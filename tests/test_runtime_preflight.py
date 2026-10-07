from pathlib import Path
import importlib.util
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('preflight', Path(__file__).parents[1] / 'tools/runtime_preflight.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class RuntimeReadiness(unittest.TestCase):
    def test_missing_project_is_not_ready(self):
        with tempfile.TemporaryDirectory() as directory:
            result = module.inspect_runtime(Path(directory), {'submodules': {}})
            self.assertFalse(result['source_present'])
            self.assertFalse(result['native_inputs_present'])

    def test_xcode_project_without_wow64_and_libraries_is_not_ready(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            project = root / 'app/Madeira.xcodeproj/project.pbxproj'
            project.parent.mkdir(parents=True)
            project.write_text('path = libwineserver.a; path = "../../FEX/build-ios/FEXCore/Source/libFEXCore.a";')
            result = module.inspect_runtime(root, {'submodules': {'wine': {}}})
            self.assertFalse(result['native_inputs_present'])
            self.assertIn('libwineserver.a', result['missing'])
            self.assertIn('../../FEX/build-ios/FEXCore/Source/libFEXCore.a', result['missing'])
            self.assertIn('i386-windows/d3d9.dll', result['missing'])
            self.assertIn('wine/ (submodule not initialized)', result['missing'])

if __name__ == '__main__':
    unittest.main()
