# Kelompok 2 - Tugas 2 Big Data Storage (Kelas B)

Perbandingan tiga penyimpanan untuk **katalog metadata** dataset **Sen12Landslides** (inventaris longsor): **MongoDB** (indeks 2dsphere), **PostgreSQL/PostGIS** (indeks GiST),
dan baseline **HDFS + Parquet** yang dibaca Spark SQL (tanpa indeks spasial). Kita menyimpan atribut, **titik pusat**, dan **kotak pembatas** tiap poligon (74.956 poligon, 16 lokasi) beserta 4.392 patch
citra; bukan poligon dan bukan citranya (170,5 GB). Data diperbesar secara simulasi menjadi **S1** (asli), **S10**, dan **S100** (7.495.600 anotasi), lalu diukur dengan enam kueri W1 sampai W6,
plus waktu muat, waktu indeks, dan ukuran di disk (W7, W8). Hipotesis H1 sampai H5 di [baca-dulu/KONTRAK.md](baca-dulu/KONTRAK.md) adalah **dugaan awal yang belum diuji**.

## Mulai dari sini

1. Buka [baca-dulu/README.md](baca-dulu/README.md), lalu [00_ALUR_KERJA.md](baca-dulu/00_ALUR_KERJA.md) dan panduan pribadimu (`PANDUAN_<nama>.md`).
2. Pasang alat dan clone repo ke `C:\proyek\kelompok2-bigdata-storage` ([01_PERSIAPAN_UMUM.md](baca-dulu/01_PERSIAPAN_UMUM.md)).
3. Uji kode tanpa Docker (butuh Python 3.11 sampai 3.13; tidak perlu `pip install`):

   ```powershell
   python tests\uji_semua.py
   ```

   Berakhir `SEMUA UJI LULUS` bila kode benar. (Uji ini tidak membuktikan MongoDB, PostGIS, HDFS, dan Spark sungguhan; itu dibuktikan saat mengerjakan langkahnya.)

## Status (Wildan memperbarui setelah tiap Sinkron)

- [ ] #2 Paket awal, data mentah, dan S1 terbukti cocok; di GitHub
- [ ] #3 sampai #5 Alat terpasang, clone dan latihan Git, spesifikasi laptop (semua)
- [ ] #7 Kickoff
- [ ] #8 S1 di laptop Syuep cocok dengan checksum
- [ ] #9 Docker MongoDB, #10 Docker PostGIS, #12 Docker HDFS dan Spark
- [ ] #11 Harness, 100 titik tetap, wasit jawaban benar
- [ ] #13 S1 di MongoDB, #14 S1 di PostGIS, #15 Parquet S1 di HDFS
- [ ] #16 S10 dan S100 dengan `CHECKSUMS.txt`
- [ ] #17 W3 di tiga penyimpanan: jumlah hasil sama dan cocok dengan wasit
- [ ] #18 SINKRON 1
- [ ] #19 sampai #24 Dokumen rancangan, slide pitching, tinjau silang, latihan (SINKRON 2)
- [ ] #25 W1 sampai W6 benar di S1 di ketiganya
- [ ] #26 S10 dan S100 termuat di ketiganya (laptop uji)
- [ ] #27 W1 sampai W8, E1, E2 dijalankan
- [ ] #28 Uji silang jumlah hasil di S100
- [ ] #29 Tabel, grafik, hipotesis H1 sampai H5
- [ ] #30 Laporan dan slide hasil
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
├─ results/         hasil uji (CSV) dan catatan pengukuran
├─ docs/            laporan, slide, diagram
└─ tests/           uji tanpa Docker
```

`data/out/` (berkas data besar) **tidak ada di GitHub**: tiap laptop membuatnya dari `data/raw/` dengan skrip yang sama, lalu `python data\generate_scales.py --verify` membuktikan isinya sama
(checksum di `data/CHECKSUMS.txt`).

## Tim dan pembagian folder

Lihat [TEAM.md](TEAM.md). Ubah **hanya folder milikmu**; `results/` boleh diisi siapa pun yang menjalankan uji.

## Atribusi dan lisensi data

Dataset: Höhn dkk. (2025), *Sen12Landslides*, Scientific Data 12:1772; DOI dataset 10.57967/hf/5883; lisensi **CC BY 4.0**.
Inventaris berasal dari Ferrario dkk. (2023), Emberson dkk. (2022), Belair dkk. (2022), dan Kirschbaum dkk. (2010, 2015).
Berkas hasil turunan (S10 dan S100) adalah **simulasi untuk uji beban penyimpanan**, bukan data ilmiah.
