# data/raw: berkas sumber (hanya dibaca, jangan diubah)

Folder ini berisi tiga berkas sumber untuk seluruh pekerjaan:

| Berkas | Isi |
|---|---|
| `inventories.zip` | inventaris poligon longsor Sen12Landslides (74.956 poligon, 15 atribut) |
| `splits_aligned.json` | pembagian 4.392 patch menjadi train, val, test |
| `SHA256.txt` | checksum SHA-256 kedua berkas di atas |

Berkas-berkas ini dimasukkan **sekali** oleh Wildan (langkah #2) dan **tidak boleh diubah, diganti, atau diformat ulang**: seluruh S1, S10, dan S100 dibuat dari sini,
dan checksum di `../CHECKSUMS.txt` bergantung pada byte yang persis sama. Pemeriksaan: `python data/cek_data.py --raw`.

Sumber: Höhn dkk. (2025), *Sen12Landslides*, Scientific Data 12:1772; DOI dataset 10.57967/hf/5883; lisensi CC BY 4.0.
