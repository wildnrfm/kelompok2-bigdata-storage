# BAHAN PRESENTASI PITCHING (6 SLIDE)
## Evaluasi Performa Spatial-Temporal Big Data: MongoDB vs. PostGIS vs. Apache Spark Parquet
**Kelompok 2 - Big Data Storage (Kelas B)**

---

### ⏱️ Aturan Durasi:
* Total durasi: **≤ 10 menit** (masing-masing anggota berbicara maksimal 1,5 – 2 menit).
* Format: 6 Slide padat informasi dan berbasis data angka empiris.

---

## 📽️ SLIDE 1: JUDUL & ANGGOTA TIM
* **Pembicara:** Muhammad Wildan Arif Maulana (Project Lead)
* **Waktu:** ~1 menit

### Konten Slide:
* **Judul:** Benchmark Performa Spatial-Temporal Big Data: MongoDB 8 vs. PostgreSQL 17/PostGIS 3.5 vs. Baseline HDFS-Parquet (Apache Spark 3.5)
* **Studi Kasus:** Katalog Metadata Deteksi Tanah Longsor Global (*Sen12Landslides*)
* **Anggota Kelompok 2:**
  1. Muhammad Wildan Arif Maulana (23051204065) — *Project Lead & Documentation*
  2. Maulana Hidayah Syaif Ali Khan (23051204068) — *Data Collection & Conversion Engineer*
  3. Elsa Claudia Putri (23051204038) — *Storage Engineer A (MongoDB Specialist)*
  4. Muhammad Syah Levi (23051204051) — *Storage Engineer B (PostGIS & HDFS Specialist)*
  5. Marsanda Sofi Aminarti (23051204066) — *Performance Analyst & Validation Lead*

> 🎙️ **Naskah Wildan:**
> *"Selamat pagi/siang Bapak/Ibu Dosen dan rekan-rekan sekalian. Kami dari Kelompok 2 akan mempresentasikan hasil benchmark komprehensif sistem penyimpanan big data untuk data observasi bumi spasial-temporal, membandingkan MongoDB, PostGIS, dan arsitektur analitik HDFS-Parquet dengan Apache Spark."*

---

## 📽️ SLIDE 2: MASALAH, LATAR BELAKANG, & SKENARIO PENGGUNA
* **Pembicara:** Muhammad Wildan Arif Maulana
* **Waktu:** ~1,5 menit

### Konten Slide:
* **Tantangan Industri:**
  * Satelit observasi bumi menghasilkan jutaan citra dan poligon bencana dengan atribut koordinat, jendela tanggal, dan bounding box.
  * Kueri geospasial tradisional sering mengalami *bottleneck* saat data melonjak ke jutaan rekaman.
* **Pertanyaan Inti:**
  * Basis data mana yang paling cepat untuk pencarian radius titik dan irisan poligon citra?
  * Kapan arsitektur Big Data kolumnar (Spark + Parquet) lebih unggul dibanding basis data operasional?
  * Bagaimana kompromi antara kecepatan kueri vs efisiensi pemakaian disk?

> 🎙️ **Naskah Wildan:**
> *"Dalam mitigasi bencana tanah longsor, sistem AI membutuhkan akses metadata ribuan citra satelit Sentinel-1 dan Sentinel-2 secara real-time. Melalui riset ini, kami menguji 7,5 juta baris data untuk menjawab secara empiris: teknologi penyimpanan mana yang paling optimal untuk skenario pencarian spasial, pemrosesan analitik, dan efisiensi biaya penyimpanan."*

---

## 📽️ SLIDE 3: DATASET SEN12LANDSLIDES & SIMULASI MULTI-SKALA
* **Pembicara:** Syuep
* **Waktu:** ~1,5 menit

### Konten Slide:
* **Dataset Dasar:** *Sen12Landslides* (Höhn dkk., 2025, Nature Scientific Data).
* **Entitas Data:**
  * `annotations` (poligon kejadian, titik pusat, bounding box, tanggal kejadian, tipe longsor).
  * `patches` (metadata patch citra satelit Sentinel-1 SAR & Sentinel-2 Multispektral).
* **Skalabilitas Deterministik (Seed `20261023`):**
  * **S1 (1x):** 74.956 anotasi, 4.392 patch (~73 MB mentah).
  * **S10 (10x):** 749.560 anotasi, 43.920 patch (~730 MB mentah).
  * **S100 (100x):** 7.495.600 anotasi, 439.200 patch (~7,36 GB mentah).
* **Jaminan Konsistensi:** 100% lolos verifikasi checksum SHA-256 dan validasi wasit ground truth.

> 🎙️ **Naskah Syuep:**
> *"Dataset asli terdiri dari 74 ribu poligon longsor global. Untuk menguji skalabilitas sistem big data, kami merancang generator skala deterministik hingga 100 kali lipat, mencapai 7,5 juta anotasi. Seluruh sebaran koordinat dan tanggal digeser secara realistis tanpa menimbulkan duplikasi buatan, dan terbukti lolos uji konsistensi 100%."*

---

## 📽️ SLIDE 4: ARSITEKTUR 3 DATABASE & PIPELINE PENGUJIAN
* **Pembicara:** Elsa Claudia Putri & Muhammad Syah Levi
* **Waktu:** ~2 menit

### Konten Slide:
* **MongoDB 8.0 (Elsa):**
  * Format GeoJSON, Storage Engine WiredTiger (kompresi Snappy).
  * Indeks: `center_2dsphere` (Google S2 geometry), B-Tree compound index.
  * Ukuran disk S100: **1,82 GB** (Data 1,2 GB + Indeks 626 MB).
* **PostgreSQL 17 + PostGIS 3.5 (Levi):**
  * Tipe native `geometry(Point/Polygon, 4326)`.
  * Indeks: GiST spatial index (R-Tree based bounding box overlap) + B-Tree.
  * Ukuran disk S100: **3,41 GB** (Data 2,5 GB + Indeks 964 MB).
* **Apache Spark 3.5.0 + HDFS (Levi):**
  * Cluster HDFS (1 NameNode + 2 DataNode, replikasi 2), format Parquet ZSTD.
  * Tanpa indeks; pemindaian penuh terdistribusi multi-core.
  * Ukuran Parquet S100: **~470 MB** (kompresi kolumnar terekstrem).

> 🎙️ **Naskah Elsa:**
> *"Di sisi MongoDB, kami mengimplementasikan model dokumen GeoJSON dengan indeks 2dsphere. Keunggulan utama MongoDB terletak pada storage engine WiredTiger yang memadatkan data S100 menjadi hanya 1,8 GB, menghemat ruang penyimpanan hingga 47% dibanding basis data relasional."*

> 🎙️ **Naskah Levi:**
> *"Untuk PostGIS, kami mengandalkan indeks spasial GiST berbasis R-Tree yang secara native mengoptimalkan kalkulasi geometri bidang 2D. Sebagai pembanding analitik, kami membangun cluster HDFS 3 node dengan Apache Spark dan Parquet Zstandard yang menghasilkan jejak penyimpanan paling ringkas di bawah 500 MB."*

---

## 📽️ SLIDE 5: METODOLOGI UJI & TEMUAN UTAMA (H1–H5)
* **Pembicara:** Marsanda Sofi Aminarti
* **Waktu:** ~2 menit

### Konten Slide:
* **6 Beban Kerja Utama (W1–W6) × 3 Ulangan (Warm & Cold Cache):**
* **Temuan Hipotesis Empiris:**
  * **H1 (Indeks Spasial):** **DITERIMA**. PostGIS (1,2 ms) dan MongoDB (7,7 ms) mengungguli Spark (545 ms) hingga **454x lebih cepat** di W2 S100.
  * **H2 (Irisan Bbox W4):** **DITERIMA**. PostGIS (**32,9 ms**) unggul **19,4x lebih cepat** dibanding MongoDB (**639,9 ms**) pada 7,5 juta poligon.
  * **H3 (Ukuran Disk):** **DITOLAK DENGAN TEMUAN BARU**. Urutan aktual: **Parquet (<0,5 GB) < MongoDB (1,8 GB) < PostGIS (3,5 GB)**.
  * **H4 (Agregasi Tabel Besar W5):** **DITERIMA**. Spark SQL (**1.293 ms**) mengalahkan MongoDB (**6.869 ms**) sebesar **5,3x lipat**.
  * **H5 (Ketahanan 50–100 Klien W1):** **DITERIMA**. Latensi p95 pada 50 klien hanya naik 6,8x–7,1x (< batas toleransi 10x).

> 🎙️ **Naskah Sofi:**
> *"Dari 111 file pengujian dan 2.200 baris log eksekusi, kami membuktikan 4 dari 5 hipotesis secara telak. Indeks GiST PostGIS adalah raja untuk interseksi poligon bounding box (19x lebih cepat dari MongoDB). Namun pada agregasi data analitik 7,5 juta baris, Spark kolumnar 5,3x lebih cepat daripada MongoDB. Sementara itu, kompresi WiredTiger membalikkan dugaan awal dengan mengalahkan efisiensi disk PostGIS."*

---

## 📽️ SLIDE 6: KESIMPULAN & REKOMENDASI ARSITEKTUR
* **Pembicara:** Muhammad Wildan Arif Maulana
* **Waktu:** ~1,5 menit

### Konten Slide:
* **Panduan Pemilihan Teknologi Berdasarkan Hasil Riset:**
  1. **Pilih PostGIS:** Jika sistem Anda adalah Web GIS interaktif, visualisasi peta satelit, atau membutuhkan operasi spasial poligon tingkat lanjut.
  2. **Pilih MongoDB:** Jika arsitektur memerlukan fleksibilitas skema JSON, efisiensi kapasitas disk penyimpanan operasional, dan skalabilitas horizontal instan.
  3. **Pilih Spark + Parquet:** Jika fokus sistem adalah *Data Lakehouse*, ekstraksi fitur machine learning, dan kueri analitik agregasi berkala.
* **Penutup & Sesi Tanya Jawab (Q&A).**

> 🎙️ **Naskah Wildan:**
> *"Kesimpulannya, tidak ada satu teknologi tunggal yang sempurna untuk semua kebutuhan. Untuk kueri spasial poligon operasional, PostGIS adalah pilihan mutlak. Untuk efisiensi biaya penyimpanan dokumen, MongoDB unggul. Dan untuk analitik data lake skala masif, kombinasi HDFS-Parquet-Spark adalah standar emas. Terima kasih, kami siap menerima pertanyaan."*

