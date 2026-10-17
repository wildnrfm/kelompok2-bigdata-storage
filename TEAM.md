# Tim: Kelompok 2 (Kelas B), Tugas 2 Big Data Storage

| Panggilan | Nama lengkap | NIM | GitHub | Peran | Folder |
|---|---|---|---|---|---|
| Wildan | Muhammad Wildan Arif Maulana | 23051204065 | [wildnrfm](https://github.com/wildnrfm) | Project Lead + Documentation/QA | `docs/`, `tests/`, berkas di akar repo |
| Syuep | Maulana Hidayah Syaif Ali Khan | 23051204068 | [Syaifalikhan](https://github.com/Syaifalikhan) | Data Collection Engineer | `data/` |
| Elsa | Elsa Claudia Putri | 23051204038 | [ElsaCP](https://github.com/ElsaCP) | Storage A (MongoDB) memimpin; Performance Analyst membantu | `mongodb/` |
| Sofi | Marsanda Sofi Aminarti | 23051204066 | [marsandasofi](https://github.com/marsandasofi) | Performance Analyst memimpin; Storage A (MongoDB) membantu | `bench/`, `results/` |
| Levi | Muhammad Syah Levi | 23051204051 | [SyahLev](https://github.com/SyahLev) | Storage B (PostgreSQL/PostGIS + baseline HDFS-Parquet) | `postgis/`, `hdfs-parquet/` |

> **Catatan untuk Wildan (#2.10 dan #6):** nama lengkap Syuep di atas disusun dari urutan namanya; cocokkan dengan data resmi dan perbaiki di sini bila berbeda.
> Hapus catatan ini setelah dicocokkan.

## Aturan kerja singkat

- Ubah **hanya folder milikmu**. `results/` boleh diisi siapa pun yang menjalankan uji; Sofi mengelola ringkasannya.
- Commit kecil dan sering, pesan diawali `[folder]`, misalnya `[postgis] muat S1`. Jangan `git push --force`.
- Jangan menaruh sandi pribadi, kunci akses, atau data pribadi di repo. Sandi `postgres` di berkas compose PostGIS hanya untuk database uji di laptop sendiri.
- Kabar di grup memakai tanda `[SELESAI]`, `[BLOKIR]`, `[KEPUTUSAN]`, `[Tinjau]` (lihat `baca-dulu/00_ALUR_KERJA.md`).
