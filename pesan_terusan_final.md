# 🚀 PANDUAN TERUSAN LENGKAP SAMPAI SELESAI

Panduan ini dimulai langsung dari posisi laptop Elsa saat ini hingga seluruh tugas, laporan, dan pitching tuntas 100%.

---

## 💻 BAGIAN I: EKSEKUSI DI LAPTOP ELSA (BENCHMARK #27)

Salin dan jalankan blok per blok di PowerShell laptop Elsa:

### 🍃 1. MONGODB

```powershell
cd C:\Users\elsac\Downloads\bigdata\kelompok2-bigdata-storage

# 1. Push hasil yang sudah ada dulu (safety)
git add results/
git commit -m "[results] W1-W6 warm S1 S10 S100 semua database"
git pull --rebase
git push

# 2. Nyalakan MongoDB (masih berisi S1)
cd mongodb; docker compose up -d; cd ..

# --- W7: ukuran S1 ---
python bench\catat.py ukuran --store mongodb --skala S1

# --- Muat S10, ukur, lalu E1 + Cold ---
python mongodb\muat_pymongo.py --skala S10
docker exec sen12ls-mongo mongosh --quiet --file /scripts/indexes.js
python bench\catat.py ukuran --store mongodb --skala S10

# E1: tanpa indeks di S10
docker exec sen12ls-mongo mongosh --quiet --file /scripts/drop_indexes.js
foreach ($w in "W2","W3","W4") { python bench\harness.py --store mongodb --workload $w --scale S10 --note "varian=tanpa-indeks" }
python bench\catat.py ukur --store mongodb --skala S10 --jenis indeks --objek semua docker exec sen12ls-mongo mongosh --quiet --file /scripts/indexes.js

# Cold S10: W3 dan W5
foreach ($n in 1,2,3) { docker restart sen12ls-mongo; Start-Sleep -Seconds 20; python bench\harness.py --store mongodb --workload W3 --scale S10 --cold-warm cold --repeats 1 --first-run-no $n }
foreach ($n in 1,2,3) { docker restart sen12ls-mongo; Start-Sleep -Seconds 20; python bench\harness.py --store mongodb --workload W5 --scale S10 --cold-warm cold --repeats 1 --first-run-no $n }

# --- Muat S100, ukur, Cold, Multi-client ---
python mongodb\muat_pymongo.py --skala S100
docker exec sen12ls-mongo mongosh --quiet --file /scripts/indexes.js
python bench\catat.py ukuran --store mongodb --skala S100

# Cold S100: W3 dan W5
foreach ($n in 1,2,3) { docker restart sen12ls-mongo; Start-Sleep -Seconds 20; python bench\harness.py --store mongodb --workload W3 --scale S100 --cold-warm cold --repeats 1 --first-run-no $n --limit-titik 20 }
foreach ($n in 1,2,3) { docker restart sen12ls-mongo; Start-Sleep -Seconds 20; python bench\harness.py --store mongodb --workload W5 --scale S100 --cold-warm cold --repeats 1 --first-run-no $n }

# Multi-client W1 di S100
foreach ($n in 10,50,100) { python bench\harness.py --store mongodb --workload W1 --scale S100 --clients $n --limit-titik 20 }

# W8: tambah batch (PALING AKHIR!)
python data\generate_scales.py --extra-batch 100
python bench\catat.py ukur --store mongodb --skala S100 --jenis tambah_batch --objek annotations docker exec sen12ls-mongo mongoimport --db sen12ls --collection annotations --file /sen12ls-data/out/batch100/annotations.ndjson
python bench\catat.py ukur --store mongodb --skala S100 --jenis tambah_batch --objek patches docker exec sen12ls-mongo mongoimport --db sen12ls --collection patches --file /sen12ls-data/out/batch100/patches.ndjson

# Matikan MongoDB
cd mongodb; docker compose stop; cd ..
```

---

### 🐘 2. POSTGIS

```powershell
cd C:\Users\elsac\Downloads\bigdata\kelompok2-bigdata-storage

# 1. Nyalakan PostGIS (masih berisi S1)
cd postgis; docker compose up -d; cd ..

# --- W7: Ukuran S1 ---
python bench\catat.py ukuran --store postgis --skala S1

# --- Muat S10, Ukur, lalu E1 (tanpa indeks) + Cold S10 ---
docker exec sen12ls-postgis psql -U postgres -d sen12ls -v folder=/sen12ls-data/out/s10 -f /sql/load.sql
docker exec sen12ls-postgis psql -U postgres -d sen12ls -f /sql/indexes.sql
python bench\catat.py ukuran --store postgis --skala S10

# E1: Hapus indeks di S10, uji W2-W4, lalu pasang lagi
docker exec sen12ls-postgis psql -U postgres -d sen12ls -f /sql/drop_indexes.sql
foreach ($w in "W2","W3","W4") { python bench\harness.py --store postgis --workload $w --scale S10 --note "varian=tanpa-indeks" }
python bench\catat.py ukur --store postgis --skala S10 --jenis indeks --objek semua docker exec sen12ls-postgis psql -U postgres -d sen12ls -f /sql/indexes.sql

# Cold run S10 (W3 & W5)
foreach ($n in 1,2,3) { docker restart sen12ls-postgis; Start-Sleep -Seconds 20; python bench\harness.py --store postgis --workload W3 --scale S10 --cold-warm cold --repeats 1 --first-run-no $n }
foreach ($n in 1,2,3) { docker restart sen12ls-postgis; Start-Sleep -Seconds 20; python bench\harness.py --store postgis --workload W5 --scale S10 --cold-warm cold --repeats 1 --first-run-no $n }

# --- Muat S100, Ukur, Cold S100, Multi-client ---
docker exec sen12ls-postgis psql -U postgres -d sen12ls -v folder=/sen12ls-data/out/s100 -f /sql/load.sql
docker exec sen12ls-postgis psql -U postgres -d sen12ls -f /sql/indexes.sql
python bench\catat.py ukuran --store postgis --skala S100

# Cold run S100 (W3 & W5)
foreach ($n in 1,2,3) { docker restart sen12ls-postgis; Start-Sleep -Seconds 20; python bench\harness.py --store postgis --workload W3 --scale S100 --cold-warm cold --repeats 1 --first-run-no $n --limit-titik 20 }
foreach ($n in 1,2,3) { docker restart sen12ls-postgis; Start-Sleep -Seconds 20; python bench\harness.py --store postgis --workload W5 --scale S100 --cold-warm cold --repeats 1 --first-run-no $n }

# Multi-client W1 di S100 (10, 50, 100 klien)
foreach ($n in 10,50,100) { python bench\harness.py --store postgis --workload W1 --scale S100 --clients $n --limit-titik 20 }

# W8: Tambah 1 batch ke S100 (PALING AKHIR!)
python bench\catat.py ukur --store postgis --skala S100 --jenis tambah_batch --objek annotations+patches docker exec sen12ls-postgis psql -U postgres -d sen12ls -v folder=/sen12ls-data/out/batch100 -v tambah=1 -f /sql/load.sql

# Matikan PostGIS
cd postgis; docker compose stop; cd ..
```

---

### ⚡ 3. SPARK HDFS-PARQUET

```powershell
cd C:\Users\elsac\Downloads\bigdata\kelompok2-bigdata-storage

# 1. Nyalakan cluster HDFS & Spark
cd hdfs-parquet; docker compose up -d; cd ..
Start-Sleep -Seconds 45
docker exec sen12ls-namenode hdfs dfsadmin -safemode leave

# --- W7: Ukuran Parquet di HDFS ---
python bench\catat.py ukuran --store spark --skala S1
python bench\catat.py ukuran --store spark --skala S10
python bench\catat.py ukuran --store spark --skala S100

# --- Cold run Spark S10 & S100 ---
python bench\harness.py --store spark --workload W3 --scale S10 --cold-warm cold
python bench\harness.py --store spark --workload W5 --scale S10 --cold-warm cold
python bench\harness.py --store spark --workload W3 --scale S100 --cold-warm cold --limit-titik 20
python bench\harness.py --store spark --workload W5 --scale S100 --cold-warm cold

# --- W8: Tambah batch Parquet ke HDFS (PALING AKHIR!) ---
python bench\catat.py ukur --store spark --skala S100 --jenis tambah_batch --objek annotations+patches docker exec sen12ls-spark /opt/spark/bin/spark-submit --master "local[2]" --driver-memory 2g /hdfs-parquet/csv_to_parquet.py --scale S100 --folder /sen12ls-data/out/batch100 --tambah

# Matikan HDFS & Spark
cd hdfs-parquet; docker compose stop; cd ..
```

---

### 🏁 4. FINISHING ELSA & PUSH KE GITHUB

```powershell
cd C:\Users\elsac\Downloads\bigdata\kelompok2-bigdata-storage

# 1. Catat ukuran file mentah CSV/NDJSON
python bench\catat.py ukuran --store mentah --skala S1
python bench\catat.py ukuran --store mentah --skala S10
python bench\catat.py ukuran --store mentah --skala S100

# 2. Tampilkan rangkuman seluruh ukuran disk & waktu muat
python bench\catat.py tampil

# 3. Buat ringkasan dan tabel perbandingan otomatis (ringkasan.csv & banding.csv)
python bench\summarize.py

# 4. PUSH SELURUH HASIL RESMI KE GITHUB REPO
git add results/
git commit -m "[results] tuntas seluruh benchmark resmi W1-W8 E1 E2 S1 S10 S100 Elsa"
git pull --rebase
git push
```

> 🎯 **STATUS ELSA:** Begitu `git push` sukses, laptop Elsa **SELESAI 100%** dan bisa dimatikan/istirahat!

---

## 🔍 BAGIAN II: VERIFIKASI WASIT S100 (#28)

Dijalankan oleh **Sofi** (atau Wildan) di laptop masing-masing setelah menarik data Elsa:

```powershell
cd <folder-repo>

# 1. Tarik hasil lengkap dari Elsa
git pull --rebase

# 2. Buat wasit jawaban benar untuk S100
python bench\kebenaran.py --skala S100 --tulis

# 3. Cocokkan seluruh berkas hasil kueri S100 antara 3 database dan wasit
1..6 | ForEach-Object { python bench/compare_counts.py (Get-ChildItem "results/*_W$($_)_S100.csv").FullName }

# 4. Push konfirmasi hasil
git add results/
git commit -m "[bench] hasil uji silang S100 cocok dengan wasit"
git pull --rebase
git push
```

---

## 📊 BAGIAN III: ANALISIS & LAPORAN (#29–#31)

### 👩 SOFI — #29: Tabel, Grafik, & Hipotesis H1–H5
1. Jalankan `python bench\summarize.py` untuk melihat `results/ringkasan.csv` dan `results/banding.csv`.
2. Buat tabel perbandingan latensi median & p95 antar ketiga database.
3. Buat grafik kurva skala (S1 → S10 → S100) per workload W1–W6.
4. Tulis kesimpulan pengujian 5 hipotesis:
   - **H1 (Indeks Spasial):** MongoDB & PostGIS vs Spark pada W2–W3.
   - **H2 (PostGIS GiST vs MongoDB 2dsphere):** Perbandingan W4 (poligon bboxes).
   - **H3 (Ukuran Penyimpanan W7):** Parquet vs PostGIS vs MongoDB.
   - **H4 (Agregasi Kolumnar):** Spark vs MongoDB pada W5–W6 skala S100.
   - **H5 (Skalabilitas Konkurensi):** Latensi W1 pada 1 vs 50 klien di S100.

### 📝 SEMUA ANGGOTA — #30: Kompilasi Laporan Akhir
Tiap anggota menulis bagiannya sesuai pembagian tugas:
- **Wildan**: Pendahuluan, latar belakang masalah, kesimpulan & rekomendasi akhir.
- **Syuep**: Profil dataset Sen12Landslides & proses konversi/skalasi.
- **Elsa**: Desain arsitektur MongoDB, indeks `2dsphere`, dan evaluasi kinerjanya.
- **Levi**: Desain arsitektur PostgreSQL/PostGIS, HDFS Parquet, dan evaluasi kinerjanya.
- **Sofi**: Sajian data benchmark, grafik, tabel, dan analisis hipotesis H1–H5.

Wildan menggabungkan semua teks ke folder `docs/laporan_akhir.md` dan push ke GitHub:
```powershell
git add docs/
git commit -m "[docs] laporan akhir big data storage kelompok 2"
git pull --rebase
git push
```

### 🏁 SEMUA — #31: QA Akhir & Pengumpulan ke SIDIA
- Periksa konsistensi angka di laporan dengan berkas CSV di `results/`.
- Cek kelengkapan identitas: Nama, NIM, Kelas (Kelas B).
- Submit berkas laporan ke portal **SIDIA**.

---

## 🎤 BAGIAN IV: PITCHING & SLIDE (#19–#24)

### 1. Persiapan Bahan (#20)
Masing-masing anggota mengirimkan 1 paragraf poin inti pembicaraan ke Wildan:
- **Syuep**: Dataset & volume (7,5 juta data).
- **Elsa**: MongoDB & indeks spasial.
- **Levi**: PostGIS & Spark Parquet baseline.
- **Sofi**: Hasil pengujian kueri & 5 hipotesis.

### 2. Diagram Arsitektur Draw.io (#21)
Wildan menggambar diagram alur pipeline:
`Data Mentah → Konversi (NDJSON/CSV) → 3 Database (MongoDB, PostGIS, Spark) → Harness Benchmark → Hasil CSV`
Ekspor PNG dan masukkan ke Slide 4.

### 3. Pembuatan Slide (#22)
Wildan menyusun 6 slide pitching:
- **Slide 1**: Judul Proyek & Anggota Kelompok 2.
- **Slide 2**: Latar Belakang & Masalah Spasial-Temporal Citra Satelit.
- **Slide 3**: Profil Dataset Sen12Landslides (S1, S10, S100).
- **Slide 4**: Arsitektur 3 Database & Diagram Pipeline.
- **Slide 5**: Metodologi Pengujian & Pembuktian Hipotesis H1–H5.
- **Slide 6**: Kesimpulan, Rekomendasi Pemilihan Storage, & Q&A.

### 4. Latihan Bersama (#24 - SINKRON 2)
Google Meet 30–45 menit:
- Masing-masing anggota presentasi maksimal 1,5 – 2 menit.
- Simulasi tanya-jawab kemungkinan pertanyaan dosen (waktu total presentasi ≤ 10 menit).

