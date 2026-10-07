# Fung Wan iOS lab

Projek persediaan untuk jalankan Fung Wan terus dalam iPhone menggunakan runtime Windows iOS. Ini **belum app Fung Wan yang boleh dipasang**.

Workflow manual `Fung Wan - semak persediaan iOS` menggunakan mesin Mac GitHub untuk mengesahkan Xcode, sumber runtime dan kebergantungan binaan. Hasilnya laporan `fungwan-ios-preflight`, bukan IPA. Status workflow berjaya bermaksud pemeriksaan selesai; lihat `ready_for_native_build` untuk kesediaan app.

Sumber dipinkan kepada commit dalam `runtime-lock.json`. Workflow tidak menjalankan skrip upstream, memuat turun IPA prabina, memasukkan fail game, parameter akses server atau sijil Apple. Ia mempunyai akses baca kod sahaja dan berjalan apabila dimulakan secara manual.

## Status sebenar

- Client Fung Wan yang tersedia ialah Windows x86 32-bit dan mengimport Direct3D 9.
- Madeira menyediakan laluan Wine WoW64/FEX dan Direct3D 9 melalui Metal, tetapi Fung Wan belum diuji padanya.
- Upstream menyatakan iOS 26+ sebagai versi yang berjalan dengan boleh dipercayai. Sokongan semua iPhone lama tidak dijanjikan.
- IPA upstream 0.1.3 telah dikuarantin Windows Defender sebagai `Trojan:Win32/Suschil!rfn`. Sama ada salah pengesanan belum disahkan. Fail itu tidak dibungkus atau dipulihkan.
- Sumber bersih memerlukan pustaka FEX, Wine, DXMT, LLVM iOS, FFmpeg dan beberapa output lain. Dokumentasi upstream mengakui sebahagian langkah belum diuji dari checkout bersih.
- Akaun GitHub, Xcode dan pemeriksaan persediaan sahaja belum menyelesaikan kebergantungan runtime, tandatangan Apple, JIT atau ujian pada iPhone sebenar.

## Langkah penggunaan

1. Sambungkan akaun GitHub dalam Codex. Gunakan repositori **private** untuk projek ini.
2. Semak kandungan projek sebelum diterbitkan ke akaun GitHub.
3. Di tab Actions, jalankan workflow manual. Ia mempunyai had 20 minit. Untuk repositori private, penggunaan mengikut minit/kuota akaun GitHub; semak baki dan had perbelanjaan akaun dahulu.
4. Baca `preflight.json`. Kebergantungan yang belum ada perlu dibina dahulu sebelum workflow untuk IPA boleh ditambah.

Semakan tempatan:

```text
python -m unittest discover -s tests -v
python tools/runtime_preflight.py --runtime <folder sumber Madeira> --report reports/preflight.json
```

Rujukan:

- https://github.com/willfaust/Madeira
- https://github.com/willfaust/Madeira/blob/48f976429c189f8396e23d251d8a82f43c705922/docs/BUILDING.md
- https://docs.github.com/en/actions/reference/runners/github-hosted-runners
