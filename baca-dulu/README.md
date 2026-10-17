# baca-dulu: panduan kerja Kelompok 2

Folder ini berisi semua panduan untuk mengerjakan **Tugas 2 Big Data Storage** (kelompok 2, kelas B): membandingkan **MongoDB**, **PostgreSQL/PostGIS**, dan
**HDFS + Parquet (Spark SQL)** untuk katalog metadata dataset **Sen12Landslides** (74.956 poligon longsor dan 4.392 patch citra satelit; hanya metadata dan titik/kotak yang kita simpan, bukan citranya).
Semua panduan berupa berkas `.md` biasa: buka di GitHub, atau di VS Code (tekan `Ctrl+Shift+V` untuk tampilan rapi).

## Mulai dari sini

1. Baca [00_ALUR_KERJA.md](00_ALUR_KERJA.md) (10 menit): peta seluruh pekerjaan, siapa menunggu siapa.
2. Kerjakan [01_PERSIAPAN_UMUM.md](01_PERSIAPAN_UMUM.md): pasang alat dan clone repo (langkah #3 sampai #5).
3. Buka **panduan pribadimu** dan ikuti berurutan:

| Siapa | Peran | Panduan | Folder milikmu |
|---|---|---|---|
| **Wildan** (Muhammad Wildan Arif Maulana) | Project Lead, Dokumentasi/QA | [PANDUAN_Wildan.md](PANDUAN_Wildan.md) | `docs/`, `tests/`, berkas di akar repo |
| **Syuep** (Maulana Hidayah Syaif Ali Khan) | Data Collection Engineer | [PANDUAN_Syuep.md](PANDUAN_Syuep.md) | `data/` |
| **Elsa** (Elsa Claudia Putri) | Storage A (MongoDB); membantu analisis | [PANDUAN_Elsa.md](PANDUAN_Elsa.md) | `mongodb/` |
| **Sofi** (Marsanda Sofi Aminarti) | Performance Analyst; membantu MongoDB | [PANDUAN_Sofi.md](PANDUAN_Sofi.md) | `bench/`, `results/` |
| **Levi** (Muhammad Syah Levi) | Storage B (PostGIS dan HDFS-Parquet) | [PANDUAN_Levi.md](PANDUAN_Levi.md) | `postgis/`, `hdfs-parquet/` |

4. Macet? Cari galatmu di [PEMECAHAN_MASALAH.md](PEMECAHAN_MASALAH.md); bila tidak ketemu dalam 15 menit, tulis `[BLOKIR]` di grup.
5. Bingung nama berkas, perintah, atau arti kolom? [KONTRAK.md](KONTRAK.md) adalah **sumber kebenaran**; bila dua dokumen berbeda, KONTRAK yang benar.
   Arti kolom data ada di [../data/KAMUS_DATA.md](../data/KAMUS_DATA.md).

## Isi folder

| Berkas | Isi | Dibaca |
|---|---|---|
| [README.md](README.md) | halaman ini | semua |
| [00_ALUR_KERJA.md](00_ALUR_KERJA.md) | peta enam fase, urutan langkah #1 sampai #31, ketergantungan, acara kelompok, aturan komunikasi | semua |
| [01_PERSIAPAN_UMUM.md](01_PERSIAPAN_UMUM.md) | terminal, pasang alat, Docker Desktop, clone, Git sehari-hari, VS Code, kamus istilah | semua |
| [KONTRAK.md](KONTRAK.md) | nama, jalur, kolom, perintah baku, beban kerja W1 sampai W10, hipotesis H1 sampai H5, apa yang sudah dan belum terbukti | semua (rujukan) |
| `PANDUAN_<nama>.md` | langkah demi langkah per orang: perintah, contoh hasil, tanda berhasil, kalau macet, pesan WhatsApp | pemiliknya |
| [PEMECAHAN_MASALAH.md](PEMECAHAN_MASALAH.md) | galat yang sering muncul (Git, Python, Docker, data, MongoDB, PostGIS, HDFS-Spark, harness) dan cara menulis `[BLOKIR]` | semua |

## Peta singkat repo

```text
kelompok2-bigdata-storage/
├─ README.md  TEAM.md  .gitignore  .gitattributes
├─ baca-dulu/       panduan (folder ini)
├─ data/            konverter, generator skala S10/S100, pemeriksa, kamus data; raw/ = tiga berkas sumber
├─ bench/           definisi kueri, harness, 100 titik uji, wasit jawaban benar, pembanding, ringkasan, pencatat
├─ mongodb/         Docker, indeks, pemuat cadangan, kueri W1 sampai W6
├─ postgis/         Docker, skema, muat, indeks, kueri W1 sampai W6
├─ hdfs-parquet/    Docker (HDFS + Spark), CSV ke Parquet, penjalan Spark SQL
├─ results/         hasil uji (CSV) dan catatan pengukuran
├─ docs/            laporan, slide, diagram
└─ tests/           uji tanpa Docker (python tests/uji_semua.py)
```

## Tiga hal yang perlu diingat

1. **Ubah hanya folder milikmu** (tabel di atas). `results/` boleh diisi siapa pun yang menjalankan uji; Sofi yang mengelola ringkasannya.
2. **Satu penyimpanan menyala sekali waktu** di satu laptop (`docker compose stop` yang lain), dan semua waktu yang masuk laporan diukur di **satu laptop uji**.
3. **Jangan `git push --force`**; jangan menaruh sandi atau data pribadi di repo; `git pull --rebase` sebelum `git push`; pesan commit diawali `[folder]`.

## Atribusi dataset

Höhn dkk. (2025), *Sen12Landslides*, Scientific Data 12:1772; DOI dataset 10.57967/hf/5883; lisensi **CC BY 4.0**.
Inventaris berasal dari Ferrario dkk. (2023), Emberson dkk. (2022), Belair dkk. (2022), dan Kirschbaum dkk. (2010, 2015).
