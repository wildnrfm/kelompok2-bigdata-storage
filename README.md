# Kelompok 2 - Tugas 2 Big Data Storage (Kelas B)

Perbandingan tiga penyimpanan untuk **katalog metadata** dataset **Sen12Landslides** (inventaris longsor): **MongoDB** (indeks 2dsphere), **PostgreSQL/PostGIS** (indeks GiST),
dan baseline **HDFS + Parquet** yang dibaca Spark SQL (tanpa indeks spasial). Kita menyimpan atribut, **titik pusat**, dan **kotak pembatas** tiap poligon (74.956 poligon, 16 lokasi) beserta 4.392 patch
citra; bukan poligon dan bukan citranya (170,5 GB). Data diperbesar secara simulasi menjadi **S1** (asli), **S10**, dan **S100** (7.495.600 anotasi), lalu diukur dengan enam kueri W1 sampai W6,
plus waktu muat, waktu indeks, dan ukuran di disk (W7, W8). Hipotesis H1 sampai H5 di [baca-dulu/KONTRAK.md](baca-dulu/KONTRAK.md) sudah diuji; hasilnya di [docs/penjelasan_lengkap.md](docs/penjelasan_lengkap.md) (H1 diterima sebagian, H2 diterima, H3 ditolak sebagian, H4 diterima sebagian, H5 diterima dengan catatan).
Tahap lanjutan, **pemrosesan dan analitik** di Spark atas Parquet yang sama (ETL, 14 kueri analisis isi di S1, uji waktu di S1, S10, S100), ada di [analitik/README.md](analitik/README.md). Hasilnya: 14 tabel cocok dengan acuan mandiri pada ketiga skala, dan satu putaran penuh memerlukan 22,3, 34,5, dan 128,8 detik (median putaran warm, laptop Wildan, dua inti).

## Mulai dari sini

1. Buka [baca-dulu/README.md](baca-dulu/README.md), lalu [00_ALUR_KERJA.md](baca-dulu/00_ALUR_KERJA.md) dan panduan pribadimu (`PANDUAN_<nama>.md`).
2. Pasang alat dan clone repo ke `C:\proyek\kelompok2-bigdata-storage` ([01_PERSIAPAN_UMUM.md](baca-dulu/01_PERSIAPAN_UMUM.md)).
3. Uji kode tanpa Docker (butuh Python 3.11 sampai 3.13; tidak perlu `pip install`):

   ```powershell
   python tests\uji_semua.py
   ```

   Berakhir `SEMUA UJI LULUS` (22 uji) bila kode benar. (Uji ini tidak membuktikan MongoDB, PostGIS, HDFS, dan Spark sungguhan; itu dibuktikan saat mengerjakan langkahnya.)

## Status (Wildan memperbarui setelah tiap Sinkron)

Tanda `[x]` dipasang bila ada jejaknya di repo (hasil di `results/`, wasit di `bench/benar/`, dokumen di `docs/`). Butir tanpa jejak di repo dicentang Wildan sendiri.

- [x] #2 Paket awal, data mentah, dan S1 terbukti cocok; di GitHub
- [ ] #3 sampai #5 Alat terpasang, clone dan latihan Git, spesifikasi laptop (semua)
- [ ] #7 Kickoff
- [ ] #8 S1 di laptop Syuep cocok dengan checksum
- [x] #9 Docker MongoDB, #10 Docker PostGIS, #12 Docker HDFS dan Spark
- [x] #11 Harness, 100 titik tetap, wasit jawaban benar
- [x] #13 S1 di MongoDB, #14 S1 di PostGIS, #15 Parquet S1 di HDFS
- [x] #16 S10 dan S100 dengan `CHECKSUMS.txt`
- [x] #17 W3 di tiga penyimpanan: jumlah hasil sama dan cocok dengan wasit (S1)
- [ ] #18 SINKRON 1
- [ ] #19 sampai #24 Dokumen rancangan, slide pitching, tinjau silang, latihan (SINKRON 2)
- [x] #25 W1 sampai W6 benar di S1 di ketiganya (`compare_counts.py` dengan wasit: semua cocok)
- [x] #26 S10 dan S100 termuat di ketiganya (laptop uji)
- [ ] #27 W1 sampai W8, E1, E2 dijalankan (W7 belum lengkap: waktu muat dan waktu indeks S100 belum tercatat; ukuran Parquet belum ada berkas ukurnya)
- [x] #28 Uji silang jumlah hasil di S10 dan S100 (`results/uji_silang_S10_S100.txt`; satu selisih diketahui: S100 W2 titik 19)
- [x] #29 Tabel, grafik, hipotesis H1 sampai H5 (`docs/penjelasan_lengkap.md`)
- [x] Tahap 3 (pemrosesan dan analitik): kode, 14 kueri, acuan S1, S10, S100, dan uji tanpa Docker selesai (`analitik/`)
- [x] Tahap 3: S1, S10, dan S100 dijalankan di Spark 3.5.0 sungguhan (laptop Wildan, sesi resmi 19 Nov 2026) dan `analitik\cocokkan.py` menjawab `SEMUA TABEL COCOK` pada ketiganya (14 tabel; 1.130 sel pada S1, 1.418 sel pada S10 dan S100)
- [x] Tahap 3: waktu pemrosesan S1, S10, S100 tercatat di laptop Wildan (`results/analitik/ringkasan_waktu.csv`): median putaran warm 22,3, 34,5, dan 128,8 detik
- [ ] #30 Laporan dan slide hasil (laporan Bab I sampai V sudah ditulis, termasuk Bab IV untuk Tahap 3; menunggu pemeriksaan akhir, dan slide belum dibuat)
- [ ] #31 QA akhir dan kumpul di SIDIA

## Susunan repo

```text
kelompok2-bigdata-storage/
├─ README.md  TEAM.md  .gitignore  .gitattributes
├─ baca-dulu/       panduan: alur kerja, persiapan umum, kontrak teknis, panduan per orang, pemecahan masalah
├─ data/            konverter, generator skala S10/S100, pemeriksa, kamus data; raw/ = berkas sumber (di-commit)
├─ bench/           definisi kueri, harness, 100 titik uji, wasit jawaban benar, pembanding, ringkasan, pencatat
├─ mongodb/         Docker, indeks, pemuat cadangan, kueri W1 sampai W6
├─ postgis/         Docker, skema, muat, indeks, kueri W1 sampai W6
├─ hdfs-parquet/    Docker (HDFS + Spark), CSV ke Parquet, penjalan Spark SQL
├─ analitik/        pemrosesan dan analitik Spark: ETL, 14 kueri, acuan S1, S10, S100, pencocok, grafik (Wildan)
├─ results/         hasil uji (CSV) dan catatan pengukuran
├─ docs/            laporan, slide, diagram
└─ tests/           uji tanpa Docker
```

`data/out/` (berkas data besar) **tidak ada di GitHub**: tiap laptop membuatnya dari `data/raw/` dengan skrip yang sama, lalu `python data\generate_scales.py --verify` membuktikan isinya sama
(checksum di `data/CHECKSUMS.txt`).

## Tim dan pembagian folder

Lihat [TEAM.md](TEAM.md). Ubah **hanya folder milikmu**; `results/` boleh diisi siapa pun yang menjalankan uji.

## Atribusi dan lisensi data

Dataset: Höhn, Heidler, Behling, dan Zhu (2025), *A Spatio-Temporal Dataset for Satellite-Based Landslide Detection* (Sen12Landslides), Scientific Data 12:1772; DOI artikel 10.1038/s41597-025-06167-2; DOI dataset 10.57967/hf/5883; lisensi **CC BY 4.0**.
Anotasi berasal dari Ferrario dkk. (2023), Höhn dkk. (2025), Emberson dkk. (2022), Belair dkk. (2022), dan Kirschbaum dkk. (2010, 2015).
Berkas hasil turunan (S10 dan S100) adalah **simulasi untuk uji beban penyimpanan**, bukan data ilmiah.
