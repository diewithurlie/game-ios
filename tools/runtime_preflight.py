"""Inspect build inputs without running upstream build scripts or downloading IPAs."""
from pathlib import Path
import argparse
import json
import platform
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.request

PROJECT = Path(__file__).resolve().parents[1]

def run(args, cwd=None):
    return subprocess.run(args, cwd=cwd, check=True, capture_output=True,
                          text=True, encoding='utf-8', errors='replace', timeout=180).stdout.strip()

def inspect_runtime(root, lock):
    project = root / 'app/Madeira.xcodeproj/project.pbxproj'
    if not project.is_file():
        return {'source_present': False, 'missing': ['app/Madeira.xcodeproj/project.pbxproj'], 'native_inputs_present': False}
    text = project.read_text(encoding='utf-8')
    # The .a references live in the Madeira source group; FEX paths are relative to it.
    paths = re.findall(r'path = (?:"([^"]+\.a)"|([^;\s]+\.a));', text)
    libraries = sorted({a or b for a, b in paths})
    base = root / 'app/Madeira'
    required = list(libraries) + [
        'i386-windows/ntdll.dll', 'i386-windows/kernel32.dll',
        'i386-windows/d3d9.dll', 'aarch64-windows/xtajit.dll',
        'aarch64-windows/wow64.dll', 'prefix-template.tar.gz',
    ]
    missing = [p for p in required if not (base / p).is_file()]
    for name in lock['submodules']:
        if not (root / name / '.git').exists():
            missing.append(name + '/ (submodule not initialized)')
    if not (root / 'wine/build-macos/include/config.h').is_file():
        missing.append('wine/build-macos/include/config.h (Wine host configure output)')
    if not (root / 'toolchains/llvm-ios-build/include/llvm').is_dir():
        missing.append('toolchains/llvm-ios-build/include/llvm (iOS LLVM build)')
    # This resource folder is explicitly referenced by the upstream Xcode project.
    if not (base / 'x86_64-vcruntime').is_dir():
        missing.append('app/Madeira/x86_64-vcruntime (Xcode resource folder)')
    return {'source_present': True, 'referenced_native_libraries': libraries,
            'missing': missing, 'native_inputs_present': not missing}

def public_submodule_availability(lock):
    results = {}
    for name, item in lock['submodules'].items():
        repo = item['repository'].removeprefix('https://github.com/').removesuffix('.git')
        request = urllib.request.Request(f'https://api.github.com/repos/{repo}/commits/{item["commit"]}',
                                         headers={'User-Agent': 'FungWan-iOS-preflight', 'Accept': 'application/vnd.github+json'})
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                data = json.load(response)
            results[name] = {'available': data.get('sha') == item['commit'], 'commit': item['commit']}
        except (urllib.error.URLError, TimeoutError) as error:
            # Distinguish a failed query from proof the commit does not exist.
            results[name] = {'available': None, 'query_error': str(error), 'commit': item['commit']}
    return results

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--runtime', type=Path, default=PROJECT / 'runtime')
    parser.add_argument('--report', type=Path, default=PROJECT / 'reports/preflight.json')
    parser.add_argument('--fetch', action='store_true')
    args = parser.parse_args()
    lock = json.loads((PROJECT / 'runtime-lock.json').read_text(encoding='utf-8'))
    report = {'stage': 'preflight only - no app build, game execution or IPA produced',
              'platform': platform.system(), 'runtime_source': lock['repository'],
              'locked_commit': lock['commit'], 'game_client': 'Windows x86 32-bit, Direct3D 9 (local inspection)',
              'minimum_reliable_ios': lock['minimum_reliable_ios'], 'prebuilt_ipa': lock['prebuilt_release'],
              'game_files_uploaded': False, 'server_parameters_uploaded': False}
    fatal = None
    try:
        if args.fetch:
            if args.runtime.exists():
                raise RuntimeError('--fetch destination already exists; existing files are preserved')
            args.runtime.mkdir(parents=True)
            run(['git', 'init', str(args.runtime)])
            run(['git', 'remote', 'add', 'origin', lock['repository']], args.runtime)
            run(['git', 'fetch', '--depth', '1', 'origin', lock['commit']], args.runtime)
            run(['git', 'checkout', '--detach', 'FETCH_HEAD'], args.runtime)
        report['inputs'] = inspect_runtime(args.runtime, lock)
        if (args.runtime / '.git').exists():
            report['actual_commit'] = run(['git', 'rev-parse', 'HEAD'], args.runtime)
            if report['actual_commit'] != lock['commit']:
                raise RuntimeError('Runtime commit does not match lock')
        report['xcode_available'] = platform.system() == 'Darwin' and shutil.which('xcodebuild') is not None
        if report['xcode_available']:
            report['xcode_version'] = run(['xcodebuild', '-version'])
            report['sdk_path'] = run(['xcrun', '--sdk', 'iphoneos', '--show-sdk-path'])
        if args.fetch:
            report['public_submodule_commits'] = public_submodule_availability(lock)
        report['ready_for_native_build'] = bool(report['inputs']['native_inputs_present'] and report['xcode_available'])
        report['security_review'] = 'Unresolved quarantine of upstream release; a successful preflight is not a safety assessment.'
        report['next_stage'] = 'Rebuild missing native dependencies from their pinned source, resolve security finding, then compile and device-test Fung Wan integration.'
    except (RuntimeError, OSError, subprocess.SubprocessError) as error:
        fatal = str(error)
        report['error'] = fatal
        report['ready_for_native_build'] = False
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2), encoding='utf-8')
    text = f"Fung Wan iOS preflight: source inspected; ready for native build={report['ready_for_native_build']}. No IPA built.\n"
    if report.get('inputs', {}).get('missing'):
        text += '\nMissing build inputs:\n' + '\n'.join('- ' + p for p in report['inputs']['missing']) + '\n'
    if fatal:
        text += '\nPreflight error: ' + fatal + '\n'
    summary = __import__('os').environ.get('GITHUB_STEP_SUMMARY')
    if summary:
        with open(summary, 'a', encoding='utf-8') as stream:
            stream.write(text)
    print(text)
    return 1 if fatal else 0  # Input inspection can succeed while app readiness remains false.

if __name__ == '__main__':
    sys.exit(main())
