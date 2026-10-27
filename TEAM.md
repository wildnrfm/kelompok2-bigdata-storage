# Tim: Kelompok 2 (Kelas B), Tugas 2 Big Data Storage

| Panggilan | Nama lengkap | NIM | GitHub | Peran | Folder |
|---|---|---|---|---|---|
| Wildan | Muhammad Wildan Arif Maulana | 23051204065 | [wildnrfm](https://github.com/wildnrfm) | Project Lead + Documentation/QA | `docs/`, `tests/`, berkas di akar repo |
| Syuep | Maulana Hidayah Syaif Ali Khan | 23051204068 | [Syaifalikhan](https://github.com/Syaifalikhan) | Data Collection Engineer | `data/` |
| Elsa | Elsa Claudia Putri | 23051204038 | [ElsaCP](https://github.com/ElsaCP) | Storage A (MongoDB) memimpin; Performance Analyst membantu | `mongodb/` |
| Sofi | Marsanda Sofi Aminarti | 23051204066 | [marsandasofi](https://github.com/marsandasofi) | Performance Analyst memimpin; Storage A (MongoDB) membantu | `bench/`, `results/` |
| Levi | Muhammad Syah Levi | 23051204051 | [SyahLev](https://github.com/SyahLev) | Storage B (PostgreSQL/PostGIS + baseline HDFS-Parquet) | `postgis/`, `hdfs-parquet/` |

> **Catatan untuk Wildan (#6):** cocokkan nama lengkap Syuep dengan data resmi; perbaiki di sini bila berbeda. Hapus catatan ini setelah dicocokkan.

## Spesifikasi laptop (27 Okt 2026)

Semua pengukuran waktu yang masuk laporan diukur di **satu laptop uji** (Elsa).

| Panggilan | Prosesor | RAM | Disk kosong | OS | WSL memory | Catatan |
|---|---|---|---|---|---|---|
| Wildan | Intel i5-6200U @ 2.30 GHz | 12 GB | 42 GB | Windows | 6 GB | Docs/QA, tidak menjalankan Docker |
| Syuep | AMD Ryzen 5 5500U | 6 GB | 54 GB | Windows | 3 GB | Data scripts saja (Python, tanpa Docker) |
| Elsa | Intel i5-13420H (Gen 13) | 16 GB | 290 GB | Windows | — | **Laptop uji utama** 🏆 |
| Sofi | Intel i3-1215U (Gen 12) | 8 GB | 58 GB | Windows | 4 GB | |
| Levi | Intel i5-8250U @ 1.60 GHz | 8 GB | 18 GB | Windows | 4 GB | Disk terbatas; satu penyimpanan sekali waktu |

## Aturan kerja singkat

- Ubah **hanya folder milikmu**. `results/` boleh diisi siapa pun yang menjalankan uji; Sofi mengelola ringkasannya.
- Commit kecil dan sering, pesan diawali `[folder]`, misalnya `[postgis] muat S1`. Jangan `git push --force`.
- Jangan menaruh sandi pribadi, kunci akses, atau data pribadi di repo. Sandi `postgres` di berkas compose PostGIS hanya untuk database uji di laptop sendiri.
- Kabar di grup memakai tanda `[SELESAI]`, `[BLOKIR]`, `[KEPUTUSAN]`, `[Tinjau]` (lihat `baca-dulu/00_ALUR_KERJA.md`).
