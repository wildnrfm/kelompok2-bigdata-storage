# PENJELASAN LENGKAP PROYEK BIG DATA STORAGE
## Benchmark Performa Spatial-Temporal: MongoDB 8 vs. PostgreSQL 17/PostGIS 3.5 vs. Apache Spark 3.5 (HDFS-Parquet) pada Dataset Sen12Landslides

**Mata Kuliah:** Big Data Storage (Kelas B)
**Tugas:** Tugas 2 & Tugas Tengah Semester (TTS)
**Kelompok:** 2

### Anggota Tim:
1. **Muhammad Wildan Arif Maulana** (23051204065) — *Project Lead, Documentation & QA*
2. **Maulana Hidayah Syaif Ali Khan** (23051204068) — *Data Collection & Conversion Engineer*
3. **Elsa Claudia Putri** (23051204038) — *Storage Engineer A (MongoDB Specialist & Benchmark Lead)*
4. **Muhammad Syah Levi** (23051204051) — *Storage Engineer B (PostGIS & HDFS-Spark Specialist)*
5. **Marsanda Sofi Aminarti** (23051204066) — *Performance Analyst & Validation Lead*

---

## BAGIAN 1: APA ITU PROYEK INI?

Proyek ini adalah tugas mata kuliah **Big Data Storage** yang meminta mahasiswa untuk:
1. Memilih sebuah dataset bervolume besar
2. Menyimpan dataset tersebut ke dalam **minimal dua sistem penyimpanan berbeda**
3. Mengukur dan membandingkan performa masing-masing sistem dari sisi kecepatan kueri dan efisiensi penyimpanan
4. Menarik kesimpulan berbasis data: sistem mana yang paling cocok untuk kebutuhan apa

**Kelompok 2 memilih tiga sistem penyimpanan:**
- **MongoDB 8.0** — basis data dokumen berbasis JSON
- **PostgreSQL 17 + PostGIS 3.5** — basis data relasional dengan ekstensi peta/spasial
- **Apache Spark 3.5.0 + HDFS + Apache Parquet** — platform analitik data lake berbasis file kolumnar terdistribusi (sebagai pembanding/baseline)

---

## BAGIAN 2: DATASET YANG DIPAKAI

### 2.1 Sumber Data: Sen12Landslides

Dataset yang dipakai bernama **Sen12Landslides**, yaitu katalog inventaris kejadian tanah longsor (*landslide*) dari seluruh dunia, dikumpulkan dari **11 inventaris global** di **16 lokasi** (antara lain Iburi/Jepang, Kodagu/India, Hiroshima/Jepang, Kaikoura/Selandia Baru, dll) dan dipasangkan dengan citra satelit Sentinel-1 dan Sentinel-2.

> **Sitasi wajib:** Höhn, P., Strunz, G., & Riedlinger, T. (2025). *Sen12Landslides: A multi-sensor benchmark dataset for landslide detection*. Scientific Data, 12:1772. DOI: `10.57967/hf/5883`. Lisensi: CC BY 4.0.

**File mentah** tersimpan di folder `data/raw/`:
- `inventories.zip` — kumpulan shapefile semua inventaris longsor dunia
- `splits_aligned.json` — daftar patch citra satelit yang selaras dengan inventaris
- `SHA256.txt` — hash integritas data mentah

### 2.2 Isi Dataset

Dataset terdiri dari **dua entitas utama**:

**Entitas 1: `annotations` (Poligon Kejadian Longsor)**

| Kolom | Isi | Contoh |
|---|---|---|
| `ann_id` | ID unik anotasi | 0, 1, 2, ... |
| `location` | Nama lokasi kejadian | Iburi, Kodagu, Hiroshima |
| `inventory` | Nama inventaris sumber | Emberson2022, Ferrario2023 |
| `event_type` | Penyebab longsor | earthquake, rainfall, snowmelt |
| `type` | Jenis gerakan tanah | slide, flow, fall |
| `velocity_c` | Kelas kecepatan gerakan | slow, rapid |
| `author` | Penulis anotasi | P. Strunz, T. Riedlinger |
| `reference` | Referensi pustaka | - |
| `event_conf` | Tingkat keyakinan (0–1) | 0.85, 1.0 |
| `area` | Luas poligon (m²) | 12345.67 |
| `pre_date` | Tanggal citra sebelum kejadian | 2018-08-10 |
| `event_date` | Tanggal kejadian longsor | 2018-09-06 |
| `post_date` | Tanggal citra sesudah kejadian | 2018-09-20 |
| `pre_dt2`, `event_dt2`, `post_dt2` | Tanggal cadangan kedua | - |
| `center_lon` | Bujur titik pusat poligon | 141.93 |
| `center_lat` | Lintang titik pusat poligon | 42.75 |
| `bbox_min_lon` | Batas barat kotak pembatas | 141.90 |
| `bbox_min_lat` | Batas selatan kotak pembatas | 42.72 |
| `bbox_max_lon` | Batas timur kotak pembatas | 141.96 |
| `bbox_max_lat` | Batas utara kotak pembatas | 42.78 |
| `sim_batch` | Nomor batch simulasi (0 = data asli) | 0 |

Total: **74.956 baris** pada data dasar (Skala S1).

**Entitas 2: `patches` (Metadata Patch Citra Satelit)**

| Kolom | Isi |
|---|---|
| `patch_id` | ID unik patch citra |
| `split` | Partisi: train / val / test |
| `inventory` | Inventaris asal patch |
| `s2_path` | Jalur file citra Sentinel-2 |
| `s1asc_path` | Jalur file citra Sentinel-1 Ascending |
| `s1dsc_path` | Jalur file citra Sentinel-1 Descending |
| `pixel_annotated` | Jumlah piksel teranotasi sebagai longsor |
| `sim_batch` | Nomor batch simulasi |

Total: **4.392 baris** pada data dasar (Skala S1).

### 2.3 Mengapa Hanya Metadata, Bukan Citranya?

Ukuran penuh citra satelit Sen12Landslides adalah **~170 GB**. Karena tujuan proyek adalah menguji performa sistem penyimpanan pada kueri metadata spasial-temporal, hanya **katalog metadata** (atribut teks, koordinat, tanggal) yang diimpor ke dalam database — bukan file citranya.

---

## BAGIAN 3: BAGAIMANA DATA DIPERSIAPKAN

### 3.1 Konversi Data Mentah → CSV/NDJSON

Shapefile inventaris tidak bisa langsung diimpor ke MongoDB atau PostgreSQL. Oleh karena itu, file dikonversi terlebih dahulu menggunakan skrip `data/convert_inventory.py`.

Proses konversi:
1. Membaca seluruh shapefile inventaris dari `data/raw/inventories.zip`
2. Mengekstrak atribut (15 kolom asli dari DBF shapefile)
3. Menghitung koordinat titik pusat dan bounding box dari geometri poligon (.shp)
4. Menggabungkan dengan data patch dari `splits_aligned.json`
5. Menghasilkan 4 file output ke `data/out/s1/`:
   - `annotations.csv` — 74.956 baris, format tabel
   - `annotations.ndjson` — 74.956 baris, format JSON per baris (untuk MongoDB)
   - `patches.csv` — 4.392 baris
   - `patches.ndjson` — 4.392 baris

### 3.2 Simulasi Skala Data (S1 → S10 → S100)

Karena dataset asli hanya 75 ribu baris, ukuran tersebut terlalu kecil untuk menguji skalabilitas sistem big data secara bermakna. Oleh karena itu dikembangkan **generator skala deterministik** (`data/generate_scales.py`).

**Caranya:**
- Generator mengambil data S1 (Batch 0) sebagai benih
- Untuk setiap batch tambahan (Batch 1, 2, 3, ... 99), semua baris data direplikasi dengan:
  - Koordinat digeser acak ±0.05° lintang/bujur
  - Tanggal kejadian digeser acak ±15 hari
  - `sim_batch` diisi dengan nomor batch
- Seed acak tetap `20261023` → hasil identik di semua laptop

**Tiga skala data yang dihasilkan:**

| Skala | Faktor | Anotasi | Patch | Ukuran Mentah |
|---|---|---|---|---|
| **S1** (data asli) | 1× | 74.956 | 4.392 | ~73 MB |
| **S10** (simulasi 10×) | 10× | 749.560 | 43.920 | ~730 MB |
| **S100** (simulasi 100×) | 100× | 7.495.600 | 439.200 | ~7,36 GB |

Semua file output diverifikasi dengan checksum SHA-256 yang tersimpan di `data/CHECKSUMS.txt`.

---

## BAGIAN 4: TIGA SISTEM PENYIMPANAN YANG DIUJI

### 4.1 MongoDB 8.0 (Basis Data Dokumen)

**Apa itu MongoDB?**
MongoDB adalah basis data *non-relasional* yang menyimpan data dalam format dokumen BSON (mirip JSON). Tidak ada skema tabel tetap — setiap dokumen bisa punya struktur berbeda.

**Bagaimana kita memakainya?**
- Setiap anotasi dan patch disimpan sebagai satu dokumen JSON
- Koordinat disimpan dalam format GeoJSON standar (`{"type": "Point", "coordinates": [lon, lat]}`)
- Berjalan dalam container Docker (`mongodb/docker-compose.yml`)
- Diimpor menggunakan skrip Python `mongodb/muat_pymongo.py`

**Strategi Indeks yang Dibuat** (`mongodb/indexes.js`):
- `center_2dsphere` — indeks bola berbasis sel S2 Geometry untuk kueri radius
- `bbox_2dsphere` — indeks bola untuk kueri bounding box
- `event_type_1_dates.event_1` — indeks gabungan untuk filter tipe + tanggal
- `location_1_dates.event_1` — indeks gabungan untuk filter lokasi + tanggal
- `inventory_1_split_1` (patches) — indeks gabungan untuk agregasi patch

**Storage Engine:** WiredTiger dengan kompresi blok Snappy secara default.

### 4.2 PostgreSQL 17 + PostGIS 3.5 (Basis Data Relasional Spasial)

**Apa itu PostgreSQL + PostGIS?**
PostgreSQL adalah basis data relasional (berbasis tabel dan SQL). PostGIS adalah ekstensi yang menambahkan kemampuan tipe data geometri dan indeks spasial ke PostgreSQL — menjadikannya standar industri untuk *Spatial Database*.

**Bagaimana kita memakainya?**
- Data anotasi dan patch diimpor ke dalam tabel relasional dengan skema tetap
- Kolom spasial menggunakan tipe `geometry(Point, 4326)` dan `geometry(Polygon, 4326)`
- Berjalan dalam container Docker (`postgis/docker-compose.yml`)
- Skema dibuat dengan `postgis/schema.sql`, data dimuat dengan `postgis/load.sql`

**Strategi Indeks yang Dibuat** (`postgis/indexes.sql`):
- `idx_annotations_center_gist` — indeks GiST (Generalized Search Tree berbasis R-Tree) pada titik pusat
- `idx_annotations_bbox_gist` — indeks GiST pada kotak pembatas
- `idx_annotations_event_date` — indeks B-Tree pada tanggal kejadian
- `idx_annotations_type_date` — indeks B-Tree gabungan tipe + tanggal
- `idx_patches_inv_split` — indeks B-Tree gabungan inventaris + split

### 4.3 Apache Spark 3.5.0 + HDFS + Apache Parquet (Data Lake Analitik)

**Apa itu Spark + HDFS + Parquet?**
- **HDFS (Hadoop Distributed File System):** sistem berkas terdistribusi yang membagi data ke beberapa node
- **Apache Parquet:** format file kolumnar yang sangat efisien untuk penyimpanan dan kompresi data analitik
- **Apache Spark:** engine komputasi terdistribusi yang membaca file Parquet dari HDFS dan menjalankan kueri SQL secara paralel

**Bagaimana kita memakainya?**
- Kluster HDFS terdiri dari 1 NameNode + 2 DataNode (replikasi faktor 2)
- File CSV dikonversi ke Parquet (kompresi Zstandard/ZSTD) menggunakan `hdfs-parquet/csv_to_parquet.py`
- Kueri dijalankan menggunakan Spark SQL melalui `hdfs-parquet/run_sql.py`
- **Tidak ada indeks sekunder** — semua kueri menggunakan pemindaian penuh terdistribusi (*distributed full scan*)

**Mengapa Spark dipakai sebagai baseline (pembanding)?**
Spark + Parquet mewakili arsitektur *Data Lake* yang paling umum dipakai di industri big data, namun tidak dirancang untuk kueri titik operasional cepat. Fungsinya sebagai tolok ukur realistis: seberapa lambat sistem tanpa indeks dibanding sistem dengan indeks.

---

## BAGIAN 5: APA YANG DIUKUR (WORKLOADS)

Semua kueri dijalankan secara otomatis oleh framework benchmark (`bench/harness.py`). Ada 6 jenis kueri utama (W1–W6) plus 2 pengukuran tambahan (W7, W8) dan 2 eksperimen khusus (E1, E2).

### W1 — Primary Key Lookup (Cari 1 Data Berdasarkan ID)
**Pertanyaan:** "Tampilkan semua atribut anotasi nomor X."
- Paling dasar: mengambil satu rekaman berdasarkan `ann_id`
- Diuji dengan 1, 10, 50, dan 100 klien serentak (uji konkurensi)
- **Kueri MongoDB:** `db.annotations.find({ann_id: X})`
- **Kueri PostGIS:** `SELECT * FROM annotations WHERE ann_id = X`
- **Kueri Spark:** `SELECT * FROM annotations WHERE ann_id = X`

### W2 — Spatial Point Radius (Cari Data Dalam Jendela Spasial)
**Pertanyaan:** "Berapa banyak anotasi yang titik pusatnya berada dalam jendela ±0.01° (~1,1 km) dari titik koordinat tertentu?"
- Menguji kemampuan kueri radius geografis
- **Kueri MongoDB:** operator `$geoWithin` dengan `$box`
- **Kueri PostGIS:** `ST_Within(center_geom, ST_MakeEnvelope(...))`

### W3 — Spatial-Temporal Range (Spasial + Filter Waktu)
**Pertanyaan:** "Berapa banyak anotasi dalam jendela ±0.01° di sekitar titik ini, yang tanggal kejadiannya antara tanggal A dan tanggal B?"
- Menambahkan filter rentang tanggal di atas W2
- Menguji indeks gabungan spasial + temporal

### W4 — Polygon Intersection + Attribute Filter (Filter Poligon + Atribut Kompleks)
**Pertanyaan:** "Berapa banyak anotasi yang kotak pembatasnya beririsan dengan area ±0.1° (~22 km), dengan tipe kejadian spesifik, dan tingkat keyakinan ≥ 0.9?"
- Kueri paling kompleks: interseksi poligon + filter atribut ganda
- Menguji indeks GiST vs 2dsphere untuk operasi bounding box

### W5 — Large-Scale Aggregation (Statistik Seluruh Tabel)
**Pertanyaan:** "Hitung jumlah anotasi untuk setiap kombinasi `event_type` dan tahun kejadian, di seluruh tabel."
- Harus memindai **seluruh tabel** (tidak ada selektivitas spasial)
- Menguji kemampuan agregasi analitik pada data masif
- Inilah skenario di mana Spark + Parquet diharapkan unggul

### W6 — Metadata Grouping (Agregasi Patch)
**Pertanyaan:** "Untuk setiap inventaris dan setiap partisi (train/val/test), berapa rata-rata piksel teranotasi per patch?"
- Agregasi pada tabel `patches` yang lebih kecil
- Menguji performa GROUP BY pada tabel berukuran sedang

### W7 — Storage & Loading Measurement (Ukuran Disk & Waktu Muat)
Bukan kueri, tapi pengukuran:
- Waktu impor bulk data ke masing-masing database
- Waktu pembuatan indeks
- Ukuran fisik data di disk (MiB)
- Dicatat menggunakan skrip `bench/catat.py`

### W8 — Batch Append (Tambah Data Ke Tabel Aktif)
**Pertanyaan:** "Berapa lama waktu yang dibutuhkan untuk menambahkan 1 batch data baru (`batch100`, 74.956 baris anotasi + 4.392 patch) ke tabel S100 yang sudah berisi 7,5 juta baris dan sudah terindeks penuh?"
- Menguji kemampuan penulisan tambahan (*append write*) tanpa rekonstruksi tabel
- **Hasil:** MongoDB annotations = **42,074 detik**, MongoDB patches = **0,731 detik**; PostGIS (annotations + patches) = **4,461 detik**
- Sumber data: `results/pengukuran_mongodb.csv` dan `results/pengukuran_postgis.csv` (jenis = `tambah_batch`)

### E1 — Eksperimen Tanpa Indeks
Menjalankan W2, W3, W4 pada skala S10 **setelah semua indeks dihapus** (`drop_indexes.js` / `drop_indexes.sql`).
- Tujuan: membuktikan secara empiris seberapa besar kontribusi indeks terhadap kecepatan
- Dicatat dengan flag `--note "varian=tanpa-indeks"`

### E2 — Kurva Skala (Skalabilitas Volume)
Membandingkan latensi yang sama workload di S1 → S10 → S100.
- Menganalisis apakah degradasi performa bersifat linier, sub-linier, atau supra-linier terhadap pertumbuhan data 10x dan 100x

---

## BAGIAN 6: CARA PENGUJIAN DILAKUKAN

### 6.1 Prinsip Pengujian Adil

Supaya perbandingan valid, semua pengujian mengikuti prinsip berikut:
- **Titik uji yang sama:** 100 titik koordinat deterministik dari `bench/points.json` — 70 titik di dalam sebaran data aktual, 30 titik di luar (untuk menguji respon kueri yang hasilnya nol)
- **Jumlah ulangan:** Setiap kombinasi workload × database × skala diuji **3 kali ulangan penuh**
- **Warm Cache:** Kueri dijalankan tanpa restart container — cache database masih aktif
- **Cold Cache:** Container Docker di-restart sebelum pengujian → mensimulasikan kondisi database baru dinyalakan
- **Skala S100 dibatasi 20 titik:** Untuk W2–W4 pada S100, hanya 20 titik pertama yang diuji di ketiga database secara seragam (mencegah komputasi berlebih pada 7,5 juta baris)

### 6.2 Framework Benchmark

Semua pengujian dieksekusi otomatis via `bench/harness.py`:
```
python bench\harness.py --store mongodb --workload W2 --scale S10 --repeats 3
```

Parameter yang tersedia:
- `--store` : `mongodb`, `postgis`, atau `spark`
- `--workload` : `W1` hingga `W6`
- `--scale` : `S1`, `S10`, `S100`
- `--cold-warm` : `warm` (default) atau `cold`
- `--clients` : jumlah klien serentak (untuk W1)
- `--repeats` : jumlah ulangan
- `--note` : catatan varian (misalnya `varian=tanpa-indeks`)
- `--limit-titik` : batasi jumlah titik uji

Setiap hasil disimpan ke file CSV di folder `results/` dengan nama format:
`YYYYMMDD_[store]_[workload]_[scale].csv`

### 6.3 Verifikasi Kebenaran Hasil

Sebelum angka performa dipercaya, seluruh hasil kueri diverifikasi keabsahan isinya:
- Jawaban benar (*ground truth*) tersimpan di `bench/benar/W1_S1.csv` s.d. `W6_S1.csv`
- Skrip `bench/compare_counts.py` membandingkan jumlah baris hasil dari ketiga database
- Jika ada hasil yang berbeda, dicatat sebagai anomali dan diselidiki sebelum dimasukkan ke laporan

### 6.4 Mesin Uji

Seluruh pengukuran dilakukan **di satu laptop uji tunggal** (Elsa Claudia Putri) untuk memastikan konsistensi hardware:
- **Prosesor:** Intel Core i5-13420H (Gen 13, 8 inti fisik)
- **RAM:** 16 GB
- **Penyimpanan:** NVMe SSD
- **OS:** Windows 11 + Docker Desktop

---

## BAGIAN 7: HASIL PENGUKURAN EMPIRIS

### 7.1 Perbandingan Latensi Median

Sumber data: `results/banding.csv` (**28 baris data**, satu per skenario unik) dan `results/ringkasan.csv` (**74 grup**, statistik lengkap per database × workload × skala × kondisi).

**Tabel lengkap semua skenario dari `banding.csv`:**

| Workload | Skala | Kondisi | Varian | MongoDB (ms) | PostGIS (ms) | Spark (ms) | Tercepat |
|---|---|---|---|---|---|---|---|
| W1 | S1 | Warm | — | 1,163 | 1,356 | 113,689 | **MongoDB** |
| W1 | S10 | Warm | — | 1,451 | **0,724** | 84,221 | **PostGIS** |
| W1 | S100 | Warm | — | 0,681 | 0,681 | 205,740 | **Seri (identik)** |
| W2 | S1 | Warm | — | 2,066 | **1,057** | 136,850 | **PostGIS** |
| W2 | S10 | Warm | — | 2,461 | **0,909** | 155,132 | **PostGIS** |
| W2 | S10 | Warm | tanpa-indeks | 1.119,729 | **213,921** | — | **PostGIS** |
| W2 | S100 | Warm | — | 7,741 | **1,202** | 545,959 | **PostGIS (454×)** |
| W3 | S1 | Warm | — | 1,801 | **1,052** | 128,764 | **PostGIS** |
| W3 | S10 | Cold | — | 3,519 | **0,822** | — | **PostGIS** |
| W3 | S10 | Warm | — | 2,175 | **2,050** | 165,380 | **PostGIS** |
| W3 | S10 | Warm | tanpa-indeks | 440,877 | **158,250** | — | **PostGIS** |
| W3 | S100 | Cold | — | 12,250 | **3,094** | — | **PostGIS** |
| W3 | S100 | Warm | — | **9,547** | 12,956 | 636,928 | **MongoDB** |
| W4 | S1 | Warm | — | 8,953 | **1,473** | 126,941 | **PostGIS** |
| W4 | S10 | Warm | — | 22,733 | **2,011** | 187,785 | **PostGIS** |
| W4 | S10 | Warm | tanpa-indeks | 632,785 | **196,672** | — | **PostGIS** |
| W4 | S100 | Warm | — | 639,974 | **32,973** | 926,173 | **PostGIS (19,4×)** |
| W5 | S1 | Warm | — | 50,870 | **30,382** | 630,264 | **PostGIS** |
| W5 | S10 | Cold | — | 1.176,506 | **74,190** | — | **PostGIS** |
| W5 | S10 | Warm | — | 523,681 | **135,430** | 670,541 | **PostGIS** |
| W5 | S100 | Cold | — | 4.483,146 | **727,333** | — | **PostGIS** |
| W5 | S100 | Warm | — | 6.869,304 | **1.141,604** | 1.293,227 | **PostGIS** (Spark 5,3× lebih cepat dari MongoDB) |
| W6 | S1 | Warm | — | 3,771 | **3,694** | 432,323 | **PostGIS** |
| W6 | S10 | Warm | — | **14,412** | 21,971 | 516,875 | **MongoDB** |
| W6 | S100 | Warm | — | 131,669 | **73,143** | 531,194 | **PostGIS** |

> **Catatan W1 S100 konkurensi:** p95 latensi dijabarkan di Bagian 7.4. `banding.csv` juga mencatat: 10 klien PostGIS 0,828 ms; 50 klien PostGIS 4,018 ms; 100 klien PostGIS 12,497 ms.

### 7.2 Jejak Penyimpanan di Disk (Skala S100, 7,5 Juta Baris)

| Komponen | Ukuran |
|---|---|
| **Parquet Zstandard** (HDFS) | ~470 MiB |
| **MongoDB** Total (Data + Indeks) | 1.862 MiB (~1,82 GB) |
| **PostGIS** Total (Heap + Indeks) | 3.496 MiB (~3,41 GB) |

### 7.3 Efek Indeks (Eksperimen E1 pada S10)

| Workload | Database | Dengan Indeks | Tanpa Indeks | Faktor Percepatan |
|---|---|---|---|---|
| W2 | PostGIS | 0,91 ms | 213,9 ms | **235×** |
| W2 | MongoDB | 2,46 ms | 1.119,7 ms | **455×** |
| W4 | PostGIS | 2,01 ms | 196,7 ms | **98×** |
| W4 | MongoDB | 22,7 ms | 632,8 ms | **28×** |

### 7.4 Konkurensi Multi-Client (W1 di S100, Latensi p95)

| Jumlah Klien | MongoDB p95 | PostGIS p95 |
|---|---|---|
| 1 klien | 2,516 ms | 1,222 ms |
| 10 klien | ~5 ms | ~3 ms |
| 50 klien | 17,831 ms | 8,346 ms |
| 100 klien | 37,160 ms | 25,750 ms |

### 7.5 Cold Run — Efek Cache Dingin (W3 & W5)

Cold run dijalankan dengan merestart container Docker sebelum setiap sesi, mensimulasikan kondisi database baru dinyalakan (page cache OS kosong). Diuji pada W3 (spasial-temporal) dan W5 (agregasi besar) untuk 3 ulangan per skenario.

| Workload | Skala | MongoDB Cold (ms) | PostGIS Cold (ms) | Rasio Cold vs Warm (PostGIS) |
|---|---|---|---|---|
| W3 | S10 | 3,519 | **0,822** | ~0,4× (PostGIS lebih cepat cold!) |
| W3 | S100 | 12,250 | **3,094** | ~0,24× |
| W5 | S10 | 1.176,506 | **74,190** | ~0,55× |
| W5 | S100 | 4.483,146 | **727,333** | ~0,64× |

Catatan: PostGIS mempertahankan keunggulan mutlak bahkan pada kondisi cold. Perbedaan cold vs warm lebih terasa di MongoDB karena WiredTiger lebih bergantung pada OS page cache untuk working set index-nya.

---

## BAGIAN 8: ANALISIS HIPOTESIS (H1–H5)

### H1 — Indeks Spasial Lebih Cepat dari Parquet pada Kueri Radius (W2 & W3)

**Pernyataan:** Database dengan indeks spasial (MongoDB dan PostGIS) lebih cepat dari Spark Parquet pada kueri radius, dan selisihnya makin besar seiring volume data naik.

**Hasil:** **DITERIMA TERBUKTI MUTLAK.**
- W2 S100: PostGIS 1,2 ms vs Spark 545,9 ms → PostGIS **454× lebih cepat**
- Eksperimen E1: tanpa indeks, MongoDB 455× lebih lambat; PostGIS 235× lebih lambat
- Indeks pohon spasial membatasi pemindaian hanya ke cabang yang relevan — latensi tetap stabil meski data naik 100×

### H2 — PostGIS Lebih Cepat dari MongoDB untuk Bounding Box (W4)

**Pernyataan:** Untuk kueri kotak pembatas beririsan dengan filter atribut, PostGIS lebih cepat dari MongoDB.

**Hasil:** **DITERIMA SANGAT KUAT.**
- W4 S100: PostGIS 32,9 ms vs MongoDB 639,9 ms → PostGIS **19,4× lebih cepat**
- Di persentil p95 S100: PostGIS 1.484 ms vs MongoDB 206.458 ms (~3,4 menit!)
- **Sebab:** Indeks GiST PostGIS melakukan perbandingan float bounding box secara native. Indeks 2dsphere MongoDB memetakan poligon ke sel-sel Geohash S2 — makin padat data, makin besar overhead dekomposisi sel

### H3 — Urutan Efisiensi Disk: Parquet < PostGIS < MongoDB

**Pernyataan (awal):** Urutan dari paling hemat disk: Parquet, PostGIS, MongoDB.

**Hasil:** **DITOLAK — temuan ilmiah baru.**
- Urutan aktual: **Parquet (470 MB) < MongoDB (1,8 GB) < PostGIS (3,5 GB)**
- MongoDB justru **1,88× lebih hemat** dibanding PostGIS
- **Sebab:** WiredTiger MongoDB mengompresi data dengan Snappy secara default. PostgreSQL menyimpan tabel dalam halaman 8KB tidak terkompresi (TOAST hanya untuk nilai sangat panjang)

### H4 — Spark Lebih Cepat untuk Agregasi Skala Besar (W5 di S100)

**Pernyataan:** Untuk agregasi seluruh tabel pada skala S100, Spark SQL lebih cepat dari MongoDB.

**Hasil:** **DITERIMA SEBAGIAN.**
- W5 S100 (7,5 juta baris): Spark 1.293 ms vs MongoDB 6.869 ms → Spark **5,3× lebih cepat** ✓
- W6 S100 (439 ribu baris): PostGIS 73 ms < MongoDB 131 ms < Spark 531 ms → Spark justru **paling lambat** ✗
- **Sebab:** Pada dataset kecil-menengah (W6), overhead inisialisasi DAG task Spark mengalahkan manfaat kolumnar. Spark unggul baru mulai terasa di atas ~1 juta baris

### H5 — Latensi Stabil Saat 50 Klien Serentak (W1 di S100)

**Pernyataan:** Latensi p95 pada 50 klien serentak tidak boleh lebih dari 10× latensi p95 klien tunggal.

**Hasil:** **DITERIMA.**
- MongoDB: 17,831 / 2,516 = **7,08×** (< batas 10×) ✓
- PostGIS: 8,346 / 1,222 = **6,83×** (< batas 10×) ✓
- Kedua sistem terbukti stabil dan tidak mengalami *queue collapse* pada beban tinggi

---

## BAGIAN 9: KESIMPULAN DAN REKOMENDASI

### Kapan Pakai MongoDB?
- Ketika skema data sering berubah-ubah (heterogen/JSON)
- Ketika kapasitas disk terbatas dan kompresi penting (1,8 GB vs 3,5 GB)
- Ketika membutuhkan skalabilitas horizontal (*sharding*) tanpa perubahan besar arsitektur
- Kueri titik tunggal W1 latensi sub-2ms

### Kapan Pakai PostgreSQL/PostGIS?
- Ketika aplikasi membutuhkan kueri spasial poligon dan bounding box yang kompleks
- Ketika akurasi SQL relasional dengan JOIN dan constraint penting
- Web GIS, peta interaktif, analisis spasial operasional
- Kueri W2/W3/W4 paling cepat — hingga 454× lebih cepat dari Spark

### Kapan Pakai Spark + Parquet?
- Ketika kebutuhan utama adalah agregasi analitik pada dataset sangat besar (>5 juta baris)
- Data warehouse, pelatihan model AI/ML, batch processing
- Ketika biaya penyimpanan menjadi pertimbangan utama (Parquet ~470 MB, 4× lebih hemat dari PostGIS)
- Bukan untuk kueri titik real-time (latensi >100 ms per kueri)

---

## BAGIAN 10: STRUKTUR REPOSITORI KODE

```
kelompok2-bigdata-storage/
│
├── baca-dulu/              ← Panduan per anggota dan alur kerja
│   ├── 00_ALUR_KERJA.md
│   ├── PANDUAN_Wildan.md
│   ├── PANDUAN_Elsa.md
│   ├── PANDUAN_Levi.md
│   ├── PANDUAN_Syuep.md
│   ├── PANDUAN_Sofi.md
│   └── KONTRAK.md
│
├── data/                   ← Semua hal terkait data
│   ├── raw/                ← Data mentah (shapefile, splits)
│   ├── out/                ← Hasil konversi (GITIGNORED — dibuat lokal)
│   │   ├── s1/             ← annotations.csv, patches.csv, .ndjson
│   │   ├── s10/
│   │   └── s100/
│   ├── convert_inventory.py    ← Konversi shapefile → CSV/NDJSON
│   ├── generate_scales.py      ← Generator S10, S100
│   ├── cek_data.py             ← Verifikasi integritas data
│   ├── CHECKSUMS.txt           ← Hash SHA-256 semua file output
│   └── KAMUS_DATA.md           ← Definisi tiap kolom
│
├── mongodb/                ← Semua hal terkait MongoDB
│   ├── docker-compose.yml      ← Definisi container Docker
│   ├── muat_pymongo.py         ← Skrip impor data Python
│   ├── indexes.js              ← Perintah buat indeks
│   ├── drop_indexes.js         ← Perintah hapus indeks (untuk E1)
│   └── queries/                ← File kueri W1–W6 dalam .js
│
├── postgis/                ← Semua hal terkait PostgreSQL/PostGIS
│   ├── docker-compose.yml
│   ├── schema.sql              ← Definisi tabel
│   ├── load.sql                ← Perintah impor data dari CSV
│   ├── indexes.sql             ← Perintah buat indeks GiST
│   ├── drop_indexes.sql        ← Perintah hapus indeks (untuk E1)
│   └── queries/                ← File kueri W1–W6 dalam .sql
│
├── hdfs-parquet/           ← Semua hal terkait HDFS + Spark
│   ├── docker-compose.yml
│   ├── csv_to_parquet.py       ← Konversi CSV → Parquet di HDFS
│   ├── run_sql.py              ← Jalankan kueri Spark SQL
│   └── sql/                    ← File kueri W1–W6 dalam .sql (Spark)
│
├── bench/                  ← Framework benchmark dan verifikasi
│   ├── harness.py              ← Runner utama benchmark
│   ├── kueri.py                ← Dispatcher kueri ke tiap database
│   ├── kebenaran.py            ← Validasi keabsahan hasil
│   ├── compare_counts.py       ← Bandingkan hasil antar database
│   ├── summarize.py            ← Generate ringkasan dan banding CSV
│   ├── catat.py                ← Catat ukuran disk dan metrik W7/W8
│   ├── make_points.py          ← Generator titik uji deterministik
│   ├── points.json             ← 100 titik uji koordinat
│   └── benar/                  ← Ground truth jawaban benar W1–W6 S1
│
├── results/                ← Semua hasil pengukuran (di-commit)
│   ├── ringkasan.csv           ← Ringkasan 74 grup (median, p95, dll)
│   ├── banding.csv             ← Perbandingan langsung 28 skenario
│   ├── pengukuran_mentah.csv   ← Ukuran file mentah
│   ├── pengukuran_mongodb.csv  ← Ukuran disk MongoDB per skala
│   ├── pengukuran_postgis.csv  ← Ukuran disk PostGIS per skala
│   └── 20261106_*.csv          ← 111 file hasil benchmark mentah
│
├── docs/                   ← Dokumen deliverable
│   ├── penjelasan_lengkap.md   ← Dokumen ini
│   └── panduan_cek_hasil.md    ← Cara melihat dan memahami hasil
│
├── tests/                  ← Test suite otomatis
│   ├── uji_semua.py            ← Jalankan 17 uji sekaligus
│   └── lint_dokumen.py         ← Periksa dokumen .md
│
├── TEAM.md                 ← Daftar anggota dan spesifikasi laptop
├── README.md               ← Pengantar repositori
└── data/CHECKSUMS.txt      ← Verifikasi integritas semua data output
```

---

## BAGIAN 11: ALUR KERJA TIM DAN GIT WORKFLOW

### Pembagian Tugas dan Penanggung Jawab Folder

| Anggota | Peran | Folder yang Dikerjakan |
|---|---|---|
| **Muhammad Wildan Arif Maulana** | Project Lead, Dokumentasi & QA | `docs/`, `tests/`, file di root repo |
| **Maulana Hidayah Syaif Ali Khan** | Data Collection Engineer | `data/` |
| **Elsa Claudia Putri** | Storage Engineer A (MongoDB) + Benchmark Lead | `mongodb/`, `results/` |
| **Muhammad Syah Levi** | Storage Engineer B (PostGIS + HDFS) | `postgis/`, `hdfs-parquet/` |
| **Marsanda Sofi Aminarti** | Performance Analyst + Validation Lead | `bench/`, `results/` |

### Alur Git yang Dipakai Tim

Setiap anggota bekerja di laptop masing-masing dengan alur berikut:

```powershell
# Ambil update terbaru dari GitHub
git pull --rebase

# ... kerjakan tugas lokal ...

# Simpan perubahan dengan pesan yang bermakna
git add [folder-milikmu]/
git commit -m "[folder] deskripsi singkat apa yang dilakukan"

# Ambil update terbaru lagi (kalau ada orang lain yang push duluan)
git pull --rebase

# Kirim ke GitHub
git push
```

**Aturan Git tim:**
- Pesan commit diawali `[nama-folder]`, contoh: `[mongodb] muat S100 dan buat indeks`, `[results] tambah benchmark W3 cold S10`
- Jangan pernah `git push --force`
- Folder `data/out/` tidak di-commit (ada di `.gitignore`) — setiap anggota generate sendiri dari `data/raw/` menggunakan skrip yang sama
- File `results/` boleh diisi siapa saja yang menjalankan benchmark
- Konflik diselesaikan lewat pesan `[BLOKIR]` di grup WhatsApp

### Konvensi Pesan di Grup WhatsApp

| Tag | Kapan Dipakai | Contoh |
|---|---|---|
| `[SELESAI]` | Langkah selesai | `[SELESAI] #13 mongodb: S1 termuat, 74956 dokumen` |
| `[BLOKIR]` | Macet lebih dari 1 jam | `[BLOKIR] docker compose up gagal port conflict @Wildan` |
| `[KEPUTUSAN]` | Hal yang disepakati bersama | `[KEPUTUSAN] S100 W2–W4 dibatasi 20 titik` |
| `[Tinjau]` | Temuan saat tinjau silang | `[Tinjau] @Sofi - ringkasan.csv - galat_n ≠ 0 di W5 S10` |

---

## BAGIAN 12: ATRIBUSI DAN REPRODUSIBILITAS

### Sitasi Dataset Wajib
> Höhn, P., Strunz, G., & Riedlinger, T. (2025). *Sen12Landslides: A multi-sensor benchmark dataset for landslide detection.* Scientific Data, 12:1772. DOI: `10.57967/hf/5883`. Lisensi: CC BY 4.0.

### Sumber Inventaris Asli yang Digunakan dalam Dataset
- Ferrario dkk. (2023)
- Emberson dkk. (2022)
- Belair dkk. (2022)
- Kirschbaum dkk. (2010, 2015)

### Repositori Kode & Hasil
`https://github.com/wildnrfm/kelompok2-bigdata-storage`

### Reprodusibilitas
Siapa pun dapat mereproduksi seluruh benchmark dengan:
1. `git clone https://github.com/wildnrfm/kelompok2-bigdata-storage.git`
2. `python data/convert_inventory.py` (membutuhkan `data/raw/inventories.zip`)
3. `python data/generate_scales.py --verify`
4. Jalankan Docker untuk masing-masing database
5. `python bench/harness.py --store [mongodb|postgis|spark] --workload [W1–W6] --scale [S1|S10|S100]`
6. `python bench/summarize.py`

Seed acak tetap `20261023` menjamin hasil generator identik di semua mesin.

