# LAPORAN AKHIR BENCHMARK BIG DATA STORAGE
## Evaluasi Performa Spatial-Temporal Big Data: MongoDB 8 vs. PostgreSQL 17/PostGIS 3.5 vs. Baseline Apache Spark 3.5 (HDFS-Parquet) pada Dataset Sen12Landslides

---

**Mata Kuliah:** Big Data Storage (Kelas B)  
**Tugas:** Tugas 2 & Tugas Tengah Semester (TTS)  
**Kelompok:** 2  

### Anggota Tim:
1. **Muhammad Wildan Romadhoni** (23051204065) — *Project Lead, Documentation & QA*
2. **Syuep** (23051204068) — *Data Collection & Conversion Engineer*
3. **Elsa Claudia Putri** (23051204038) — *Storage Engineer A (MongoDB Specialist & Benchmark Lead)*
4. **Muhammad Syarifuddin Levi** (23051204051) — *Storage Engineer B (PostGIS & HDFS-Spark Specialist)*
5. **Marsanda Sofi Salsabila** (23051204066) — *Performance Analyst & Validation Lead*

---

## 1. PENDAHULUAN

### 1.1 Latar Belakang
Ledakan data observasi bumi (*earth observation*) dan penginderaan jauh menghasilkan volume data spasial-temporal yang sangat masif. Salah satu domain kebencanaan paling kritis adalah pemantauan tanah longsor (*landslides*). Pemodelan dan mitigasi risiko tanah longsor berbasis kecerdasan buatan membutuhkan katalog metadata terpusat yang mampu mencatat poligon kejadian, bounding box citra satelit (seperti Sentinel-1 SAR dan Sentinel-2 Multispektral), tanggal kejadian, serta label inventaris dalam skala jutaan baris data.

Tantangan utama pada sistem penyimpanan big data geospasial adalah:
1. **Beban Kueri Spasial Kompleks:** Kueri interseksi poligon (*bounding box intersection*), kueri kedekatan titik pusat (*radius search*), dan filter jendela waktu kejadian (*temporal filtering*).
2. **Skalabilitas Data:** Skalabilitas komputasi dari dataset lokal puluhan ribu baris hingga jutaan baris data.
3. **Kompromi Arsitektur:** Perdebatan antara basis data dokumen terdistribusi (**MongoDB**), basis data relasional berorientasi spasial (**PostGIS**), dan arsitektur analitik kolumnar berbasis data lake (**HDFS + Apache Parquet + Apache Spark**).

### 1.2 Tujuan dan Pertanyaan Penelitian
Penelitian ini bertujuan untuk mengevaluasi performa penyimpanan, latensi kueri, dan efisiensi sumber daya pada tiga teknologi penyimpanan data besar dengan dataset metadata *Sen12Landslides*.

Pertanyaan penelitian yang dijawab secara empiris adalah:
1. Apakah indeks spasial 2D (*GiST* dan *2dsphere*) mampu mengungguli pemindaian analitik kolumnar (*Spark Parquet*) pada kueri titik dan rentang waktu?
2. Bagaimana perbandingan efisiensi pemfilteran poligon beririsan antara PostgreSQL/PostGIS dan MongoDB?
3. Bagaimana perbandingan ukuran kompresi data dan indeks di disk antara format Parquet, MongoDB WiredTiger, dan PostgreSQL TOAST?
4. Kapan pemrosesan kolumnar terdistribusi (Spark SQL) mulai mengungguli basis data transaksional operasional pada agregasi skala besar?
5. Bagaimana ketahanan latensi p95 sistem saat menerima beban kueri serentak (*high concurrency*) hingga 100 klien?

---

## 2. PROFIL DATASET & METODOLOGI SIMULASI SKALA

### 2.1 Sumber Data & Profil Asli (Skala S1)
Dataset yang digunakan berasal dari katalog inventaris **Sen12Landslides** (Höhn dkk., 2025; DOI: `10.57967/hf/5883`). Dataset ini memetakan poligon kejadian longsor di 16 lokasi global yang dipasangkan dengan patch citra satelit Sentinel-1 dan Sentinel-2.

Dataset dikonversi dari format mentah ESRI Shapefile/GeoJSON ke dalam dua entitas data terstruktur:
* **`annotations`:** Berisi 74.956 rekaman poligon longsor, titik pusat (*center lon/lat*), bounding box (*min_lon, min_lat, max_lon, max_lat*), tanggal kejadian (*event_date*), tingkat keyakinan (*confidence*), dan tipe kejadian (*event_type*).
* **`patches`:** Berisi 4.392 rekaman patch citra satelit, resolusi spasial, partisi inventaris (*split: train/val/test*), dan rasio piksel teranotasi.

### 2.2 Pembangkitan Data Uji Multi-Skala (S1, S10, S100)
Untuk menguji kurva skalabilitas penyimpanan, dikembangkan generator data deterministik (`data/generate_scales.py`) dengan seed acak tetap (`20261023`):
* **Skala S1 (Data Dasar / 1x):** 74.956 anotasi; 4.392 patch (Batch 0).
* **Skala S10 (Skala Menengah / 10x):** 749.560 anotasi; 43.920 patch (Batch 0–9).
* **Skala S100 (Skala Penuh / 100x):** 7.495.600 anotasi; 439.200 patch (Batch 0–99).
* **Batch Tambahan W8 (`batch100`):** 74.956 anotasi; 4.392 patch untuk mengukur waktu penambahan data ke S100 tanpa rekondisi tabel.

Setiap replika batch $b$ menggeser koordinat geografis sebesar $\Delta \text{lon}, \Delta \text{lat} \in [-0.05^\circ, +0.05^\circ]$ dan tanggal sebesar $\pm 15$ hari secara acak berurutan, memastikan densitas dan distribusi spasial tetap realistis tanpa terjadi tumpukan duplikat identik.

---

## 3. ARSITEKTUR PENYIMPANAN & MODEL DATA

### 3.1 MongoDB 8.0 (Document Store)
* **Model Data:** Dokumen semi-terstruktur BSON di koleksi `sen12ls.annotations` dan `sen12ls.patches`. Geometri titik dan poligon disimpan dalam format GeoJSON standar (`type: "Point"`, `type: "Polygon"`).
* **Storage Engine:** WiredTiger dengan kompresi bawaan Snappy.
* **Strategi Indeks:**
  * Indeks Geospasial: `center_2dsphere` (indeks bola berbasis Google S2 Geometry cell hierarchy) dan `bbox_2dsphere`.
  * Indeks Majemuk Temporal & Atribut: `event_type_1_dates.event_1`, `location_1_dates.event_1`.
  * Indeks B-Tree Patch: `inventory_1_split_1`.

### 3.2 PostgreSQL 17 + PostGIS 3.5 (Relational Spatial Store)
* **Model Data:** Skema relasional normal dengan tipe data native geometri PostGIS (`geometry(Point, 4326)` dan `geometry(Polygon, 4326)`). Koordinat bounding box dikonstruksi menjadi geometri poligon tertutup menggunakan `ST_MakeEnvelope`.
* **Strategi Indeks:**
  * Indeks Spasial GiST: Generalized Search Tree menggunakan algoritma R-Tree bounding box (`idx_annotations_center_gist` dan `idx_annotations_bbox_gist`).
  * Indeks B-Tree: `idx_annotations_event_date`, `idx_annotations_type_date`, dan `idx_patches_inv_split`.

### 3.3 Baseline Apache Spark 3.5.0 + HDFS (Columnar Data Lake)
* **Model Data:** File kolumnar terdistribusi Apache Parquet dengan kompresi Zstandard (ZSTD) yang disimpan pada klaster Hadoop Distributed File System (HDFS, 1 NameNode + 2 DataNode, replikasi 2).
* **Karakteristik:** Tidak menggunakan indeks sekunder maupun indeks spasial (pure distributed full-table scanning). Mengandalkan pemangkasan kolom (*column projection*), pemangkasan blok (*predicate pushdown*), dan eksekusi paralel multi-core vectorization.

---

## 4. METODOLOGI BENCHMARK

### 4.1 Beban Kerja Kueri (Workloads W1–W8, E1, E2)
Pengujian dieksekusi secara otomatis melalui framework uji mandiri (`bench/harness.py`):
* **W1 (Primary Key Lookup):** Mengambil 1 rekaman anotasi menurut `ann_id` (diuji pada 1, 10, 50, dan 100 klien konkuren).
* **W2 (Spatial Point Radius):** Menghitung jumlah anotasi yang titik pusatnya berada dalam jendela $\pm 0.01^\circ$ (~1,1 km) dari titik uji.
* **W3 (Spatial-Temporal Range):** Kueri W2 ditambah filter rentang tanggal kejadian $\pm 30$ hari.
* **W4 (Polygon Intersection & Attribute Filter):** Menghitung anotasi yang kotak pembatasnya beririsan dengan jendela $\pm 0.1^\circ$ (~22 km), dengan filter `event_type` spesifik dan `event_conf >= 0.9`.
* **W5 (Large-scale Aggregation):** Agregasi seluruh tabel anotasi: jumlah kejadian per `event_type` dan tahun kejadian.
* **W6 (Metadata Grouping):** Agregasi patch citra: pengelompokan menurut `inventory` dan `split`, serta rata-rata rasio piksel teranotasi.
* **W7 (Storage & Loading Measurement):** Pengukuran waktu muat bulk, waktu pembuatan indeks, dan jejak fisik di disk (MiB).
* **W8 (Batch Append):** Waktu penambahan 1 batch data baru (`batch100`, 74.956 baris) ke dalam tabel S100 yang telah terindeks penuh.
* **E1 (Eksperimen Tanpa Indeks):** Uji W2, W3, W4 pada skala S10 tanpa indeks untuk membuktikan faktor percepatan (*speedup factor*).
* **E2 (Kurva Skala):** Analisis linieritas degradasi waktu terhadap pembesaran skala data 1x $\rightarrow$ 10x $\rightarrow$ 100x.

### 4.2 Titik Uji & Prinsip Uji Adil
* Menggunakan 100 titik uji deterministik (`bench/points.json`): 70 titik di dalam klaster data aktif dan 30 titik di luar sebaran data untuk menguji respon kueri kosong (*zero-hit queries*).
* Pada skala S100, kueri spasial W2–W4 dibatasi pada 20 titik pertama (`--limit-titik 20`) secara seragam di ketiga basis data untuk menjaga perbandingan yang adil tanpa memicu komputasi berlebih.
* Pengujian diulang sebanyak **3 kali ulangan penuh** pada kondisi *Warm Cache* dan *Cold Cache* (restart kontainer Docker sebelum eksekusi).

---

## 5. HASIL BENCHMARK EMPIRIS

Seluruh pengukuran dijalankan pada perangkat keras standar laptop uji (Intel Core i5-13420H Gen 13, 16 GB RAM, NVMe SSD).

### 5.1 Tabel Perbandingan Latensi Median (ms)
Sumber data: `results/banding.csv` dan `results/ringkasan.csv`.

| Beban Kerja | Skala | Kondisi | Konkurensi | Varian | MongoDB (ms) | PostGIS (ms) | Spark SQL (ms) | Database Tercepat | Rasio Kecepatan |
|---|---|---|---|---|---|---|---|---|---|
| **W1** | S1 | Warm | 1 | Normal | 1.163 | 1.356 | 113.689 | **MongoDB** | 97.8x vs Spark |
| **W1** | S10 | Warm | 1 | Normal | 1.451 | **0.724** | 84.221 | **PostGIS** | 116.4x vs Spark |
| **W1** | S100 | Warm | 1 | Normal | **0.681** | **0.681** | 205.740 | **Seri (Mongo/PG)**| 302.1x vs Spark |
| **W1** | S100 | Warm | 10 | Normal | 1.410 | **0.828** | - | **PostGIS** | 1.7x vs Mongo |
| **W1** | S100 | Warm | 50 | Normal | 7.454 | **4.018** | - | **PostGIS** | 1.9x vs Mongo |
| **W1** | S100 | Warm | 100 | Normal | 15.606 | **12.497** | - | **PostGIS** | 1.2x vs Mongo |
| **W2** | S1 | Warm | 1 | Normal | 2.066 | **1.057** | 136.850 | **PostGIS** | 129.5x vs Spark |
| **W2** | S10 | Warm | 1 | Normal | 2.461 | **0.909** | 155.132 | **PostGIS** | 170.7x vs Spark |
| **W2** | S10 | Warm | 1 | Tanpa Indeks| 1119.729 | **213.921** | - | **PostGIS** | 5.2x vs Mongo |
| **W2** | S100 | Warm | 1 | Normal | 7.741 | **1.202** | 545.959 | **PostGIS** | **454.2x vs Spark**|
| **W3** | S1 | Warm | 1 | Normal | 1.801 | **1.052** | 128.764 | **PostGIS** | 122.4x vs Spark |
| **W3** | S10 | Cold | 1 | Normal | 3.519 | **0.822** | - | **PostGIS** | 4.3x vs Mongo |
| **W3** | S10 | Warm | 1 | Normal | 2.175 | **2.050** | 165.380 | **PostGIS** | 80.7x vs Spark |
| **W3** | S10 | Warm | 1 | Tanpa Indeks| 440.877 | **158.250** | - | **PostGIS** | 2.8x vs Mongo |
| **W3** | S100 | Cold | 1 | Normal | 12.250 | **3.094** | - | **PostGIS** | 4.0x vs Mongo |
| **W3** | S100 | Warm | 1 | Normal | **9.547** | 12.956 | 636.928 | **MongoDB** | 66.7x vs Spark |
| **W4** | S1 | Warm | 1 | Normal | 8.953 | **1.473** | 126.941 | **PostGIS** | 86.2x vs Spark |
| **W4** | S10 | Warm | 1 | Normal | 22.733 | **2.011** | 187.785 | **PostGIS** | 93.4x vs Spark |
| **W4** | S10 | Warm | 1 | Tanpa Indeks| 632.785 | **196.672** | - | **PostGIS** | 3.2x vs Mongo |
| **W4** | S100 | Warm | 1 | Normal | 639.974 | **32.973** | 926.173 | **PostGIS** | **19.4x vs Mongo** |
| **W5** | S1 | Warm | 1 | Normal | 50.870 | **30.382** | 630.264 | **PostGIS** | 20.7x vs Spark |
| **W5** | S10 | Cold | 1 | Normal | 1176.506| **74.190** | - | **PostGIS** | 15.9x vs Mongo |
| **W5** | S10 | Warm | 1 | Normal | 523.681 | **135.430** | 670.541 | **PostGIS** | 5.0x vs Spark |
| **W5** | S100 | Cold | 1 | Normal | 4483.146| **727.333** | - | **PostGIS** | 6.2x vs Mongo |
| **W5** | S100 | Warm | 1 | Normal | 6869.304| **1141.604**| 1293.227 | **PostGIS** | **5.3x Spark vs Mongo**|
| **W6** | S1 | Warm | 1 | Normal | 3.771 | **3.694** | 432.323 | **PostGIS** | 117.0x vs Spark |
| **W6** | S10 | Warm | 1 | Normal | **14.412**| 21.971 | 516.875 | **MongoDB** | 35.9x vs Spark |
| **W6** | S100 | Warm | 1 | Normal | 131.669 | **73.143** | 531.194 | **PostGIS** | 7.3x vs Spark |

### 5.2 Jejak Penyimpanan & Efisiensi Disk (W7)
Sumber data: `pengukuran_mentah.csv`, `pengukuran_mongodb.csv`, `pengukuran_postgis.csv`.

| Skala Data | Format Mentah (CSV / NDJSON) | MongoDB Data di Disk (WiredTiger) | MongoDB Indeks (2dsphere + B-Tree) | PostGIS Data di Disk (Heap Table) | PostGIS Indeks (GiST + B-Tree) | Parquet Zstandard (Estimasi) |
|---|---|---|---|---|---|---|
| **S1 (75k)** | 18.8 MiB / 54.5 MiB | 9.9 MiB | 5.4 MiB | 25.3 MiB | 10.1 MiB | ~5 MiB |
| **S10 (750k)** | 188.5 MiB / 545.3 MiB | 121.4 MiB | 66.5 MiB | 253.2 MiB | 98.0 MiB | ~48 MiB |
| **S100 (7.5M)** | 1.898.7 MiB / 5.466.9 MiB | **1.236.0 MiB** | **626.0 MiB** | **2.532.7 MiB** | **963.6 MiB** | **~470 MiB** |
| **Total S100** | **~7,36 GB** | \multicolumn{2}{c|}{**1.862,0 MiB (~1,82 GB)**} | \multicolumn{2}{c|}{**3.496,3 MiB (~3,41 GB)**} | **~470 MiB (~0,46 GB)** |

---

## 6. ANALISIS & EVALUASI HIPOTESIS (H1–H5)

### 📌 Hipotesis H1: Keunggulan Indeks Spasial terhadap Baseline Parquet (W2 & W3)
* **Pernyataan:** *Dengan indeks spasial, MongoDB dan PostGIS lebih cepat daripada baseline Parquet pada W2 dan W3, dan selisihnya melebar dari S1 ke S100.*
* **Kriteria Penolakan:** Selisih latensi mengecil atau terbalik.
* **Hasil Empiris:**
  * Pada W2 S1: PostGIS (**1,06 ms**) dan MongoDB (**2,07 ms**) unggul mutlak dibanding Spark (**136,85 ms**), selisih kecepatan $\approx 135\text{ ms}$.
  * Pada W2 S100: PostGIS (**1,20 ms**) dan MongoDB (**7,74 ms**) sangat cepat dibanding Spark (**545,96 ms**), selisih kecepatan melebar menjadi **544,76 ms** (PostGIS **454x lebih cepat**).
  * Eksperimen E1 membuktikan bahwa tanpa indeks di S10, waktu eksekusi PostGIS melonjak dari 0,91 ms ke 213,9 ms (lonjakan 235x), dan MongoDB melonjak dari 2,46 ms ke 1.119,7 ms (lonjakan 455x).
* **Kesimpulan:** **HIPOTESIS H1 DITERIMA (TERBUKTI MUTLAK)**. Indeks spasial berbasis pohon (*tree-based spatial indexing*) membatasi pemindaian hanya pada daun indeks yang relevan, menjaga latensi stabil di kisaran sub-10 ms meskipun volume data meningkat 100 kali lipat.

---

### 📌 Hipotesis H2: Efisiensi Bounding Box Intersect PostGIS vs. MongoDB (W4)
* **Pernyataan:** *Pada W4 (kotak pembatas + atribut), PostGIS lebih cepat daripada MongoDB.*
* **Kriteria Penolakan:** MongoDB sama cepat atau lebih cepat dari PostGIS.
* **Hasil Empiris:**
  * Skala S1: PostGIS **1,47 ms** vs. MongoDB **8,95 ms** (PostGIS 6,1x lebih cepat).
  * Skala S10: PostGIS **2,01 ms** vs. MongoDB **22,73 ms** (PostGIS 11,3x lebih cepat).
  * Skala S100: PostGIS **32,97 ms** vs. MongoDB **639,97 ms** (PostGIS **19,4x lebih cepat**).
  * Pada persentil ke-95 (p95) di S100: PostGIS mencatat 1.484 ms, sedangkan MongoDB melonjak ke 206.458 ms (~3,4 menit).
* **Kesimpulan:** **HIPOTESIS H2 DITERIMA (TERBUKTI SANGAT KUAT)**. PostGIS mengimplementasikan operator kotak pembatas dua dimensi `&&` secara native di level indeks GiST dengan membandingkan nilai koordinat float langsung (*bounding box overlap*). Sebaliknya, indeks `2dsphere` MongoDB memetakan poligon ke dalam sel Geohash/S2 cell covers, yang pada kepadatan 7,5 juta poligon menimbulkan overhead pembedahan sel (*cell decomposition*) dan verifikasi dokumen yang sangat mahal.

---

### 📌 Hipotesis H3: Urutan Efisiensi Jejak Disk (W7)
* **Pernyataan:** *Ukuran di disk dari kecil ke besar: Parquet (ZSTD), PostGIS, MongoDB (termasuk indeks).*
* **Kriteria Penolakan:** Urutan fisik di disk berbeda dari dugaan awal.
* **Hasil Empiris:**
  * Parquet (Zstandard): **~470 MiB** (terkecil karena kompresi kolumnar dan *dictionary encoding*).
  * MongoDB (WiredTiger): Data 1.236 MiB + Indeks 626 MiB = **1.862 MiB (~1,82 GB)**.
  * PostGIS: Data 2.533 MiB + Indeks 964 MiB = **3.496 MiB (~3,41 GB)**.
  * **Urutan Aktual di Disk:** **Parquet < MongoDB < PostGIS**.
* **Kesimpulan:** **HIPOTESIS H3 DITOLAK (DENGAN TEMUAN ILMIAH PENTING)**. Dugaan awal menduga PostGIS lebih hemat dibanding MongoDB. Namun kenyataannya, **MongoDB 1,88x lebih hemat disk dibanding PostGIS**. Hal ini disebabkan mesin penyimpanan WiredTiger MongoDB secara default menerapkan kompresi blok Snappy pada disk, sedangkan PostgreSQL menyimpan tabel heap dalam page 8KB tak terkompresi.

---

### 📌 Hipotesis H4: Agregasi Kolumnar pada Skala Besar S100 (W5 & W6)
* **Pernyataan:** *Pada W5 dan W6 di S100 (agregasi seluruh tabel), Spark SQL atas Parquet lebih cepat daripada MongoDB.*
* **Kriteria Penolakan:** MongoDB lebih cepat daripada Spark SQL.
* **Hasil Empiris:**
  * Pada W5 S100 (Agregasi 7,5 juta baris anotasi):
    * Spark SQL: **1.293,23 ms**
    * MongoDB: **6.869,30 ms**
    * Spark SQL **5,3x lebih cepat** daripada MongoDB.
  * Pada W6 S100 (Agregasi 439 ribu baris patch):
    * PostGIS: **73,14 ms**
    * MongoDB: **131,67 ms**
    * Spark SQL: **531,19 ms**
* **Kesimpulan:** **HIPOTESIS H4 DITERIMA SEBAGIAN**. Pada dataset masif (W5, 7,5 juta baris), pemrosesan kolumnar terdistribusi Spark SQL mengungguli MongoDB secara telak karena Spark hanya membaca dua kolom yang relevan (`event_type` dan `event_date`) tanpa parsing dokumen utuh. Namun pada tabel yang lebih kecil (W6, 439 ribu baris), overhead inisialisasi eksekusi dan penjadwalan DAG task Spark membuat MongoDB dan PostGIS lebih responsif.

---

### 📌 Hipotesis H5: Skalabilitas Konkurensi Kueri Titik (W1 di S100)
* **Pernyataan:** *Pada W1 dengan 50 klien di S100, p95 MongoDB dan PostGIS kurang dari 10 kali p95 satu klien.*
* **Kriteria Penolakan:** Latensi p95 meningkat 10 kali lipat atau lebih saat beban dinaikkan ke 50 klien.
* **Hasil Empiris:**
  * MongoDB:
    * 1 klien: $p95 = \mathbf{2,516\text{ ms}}$
    * 50 klien: $p95 = \mathbf{17,831\text{ ms}}$
    * Rasio peningkatan: $17,831 / 2,516 = \mathbf{7,08\times}$ ($< 10\times$).
  * PostGIS:
    * 1 klien: $p95 = \mathbf{1,222\text{ ms}}$
    * 50 klien: $p95 = \mathbf{8,346\text{ ms}}$
    * Rasio peningkatan: $8,346 / 1,222 = \mathbf{6,83\times}$ ($< 10\times$).
  * Pada pengujian ekstrem 100 klien: PostGIS mempertahankan p95 di **25,75 ms** dan MongoDB di **37,16 ms**.
* **Kesimpulan:** **HIPOTESIS H5 DITERIMA (TERBUKTI SANGAT BAIK)**. Kedua sistem basis data operasional membuktikan ketahanan *connection pool* dan efisiensi algoritma B-Tree index lookup pada beban multi-threading tinggi.

---

## 7. KESIMPULAN & REKOMENDASI ARSITEKTUR

### 7.1 Ringkasan Temuan
1. **PostgreSQL/PostGIS adalah raja kueri geospasial relasional dan poligon:** Unggul mutlak pada kueri kotak pembatas W4 (hingga 19,4x lebih cepat dibanding MongoDB) dan memiliki performa kueri konkurensi paling stabil.
2. **MongoDB WiredTiger sangat efisien dalam kompresi penyimpanan dan kueri titik sederhana:** Jejak penyimpanan hampir setengah dari PostGIS (1,8 GB vs 3,5 GB pada 7,5 juta data) dan sangat mudah diskalakan secara horizontal (*sharding*).
3. **Apache Spark + Parquet adalah fondasi terbaik untuk Data Lake Analitik:** Tidak cocok untuk kueri operasional titik tunggal (*latency >100 ms*), namun sangat superior dalam kueri pemindaian analitik agregasi pada skala masif.

### 7.2 Rekomendasi Pemilihan Storage (*Architectural Decision Guide*)

| Skenario Penggunaan | Teknologi yang Direkomendasikan | Alasan Berdasarkan Hasil Benchmark |
|---|---|---|
| **Katalog Geospasial Interaktif & Web GIS** (Pencarian peta, buffer titik, irisan poligon citra satelit) | **PostgreSQL / PostGIS** | Indeks GiST native memberikan latensi terendah (1–32 ms) untuk kueri spasial murni dan interseksi poligon (W2, W3, W4). |
| **Penyimpanan Operasional & API Metadata Dokumen** (Penyimpanan metadata JSON heterogen, kendala kapasitas disk) | **MongoDB** | Kompresi WiredTiger menghemat 47% ruang disk dibanding PostGIS, penulisan batch W8 sangat cepat (42 detik), dan latensi W1 sangat responsif. |
| **Data Lakehouse & Pelatihan Model AI/ML Skala Besar** (Ekstraksi fitur citra, batch training tanah longsor, OLAP) | **HDFS + Apache Parquet + Spark** | Format Parquet Zstandard meminimalkan biaya penyimpanan cold data (<500 MiB per 7,5M baris) dan kecepatan agregasi W5 mencapai 1,2 detik. |

---

## 8. ATRIBUSI DATA & REPRODUSIBILITAS

* **Sitasi Dataset Wajib:**  
  *Höhn, P., Strunz, G., & Riedlinger, T. (2025). Sen12Landslides: A multi-sensor benchmark dataset for landslide detection. Scientific Data, 12:1772. DOI: 10.57967/hf/5883. Lisensi: CC BY 4.0.*
* **Sumber Inventaris Asli:**  
  *Ferrario dkk. (2023), Emberson dkk. (2022), Belair dkk. (2022), Kirschbaum dkk. (2010, 2015).*
* **Tautan Repositori Kode & Hasil:**  
  `https://github.com/wildnrfm/kelompok2-bigdata-storage`

