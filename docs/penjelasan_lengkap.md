# PENJELASAN LENGKAP PROYEK BIG DATA STORAGE
## Benchmark Performa Spatial-Temporal: MongoDB 8 vs. PostgreSQL 17/PostGIS 3.5 vs. Apache Spark 3.5 (HDFS-Parquet) pada Dataset Sen12Landslides

**Mata Kuliah:** Big Data Storage (Kelas B)
**Tugas:** Tugas 2 & Tugas Tengah Semester (TTS)
**Kelompok:** 2

### Anggota Tim:
1. **Muhammad Wildan Arif Maulana** (23051204065) — *Project Lead, Documentation & QA, dan pemrosesan-analitik Spark (Tahap 3)*
2. **Maulana Hidayah Syaif Ali Khan** (23051204068) — *Data Collection & Conversion Engineer*
3. **Elsa Claudia Putri** (23051204038) — *Storage Engineer A (MongoDB Specialist & Benchmark Lead)*
4. **Muhammad Syah Levi** (23051204051) — *Storage Engineer B (PostGIS & HDFS-Spark Specialist)*
5. **Marsanda Sofi Aminarti** (23051204066) — *Performance Analyst & Validation Lead*

> **Catatan revisi (12 Nov 2026).** Semua angka hasil di dokumen ini diambil dari `results/banding.csv` dan `results/ringkasan.csv` yang dibuat ulang dengan `python bench/summarize.py --titik-maks 20`: 90 berkas hasil tanggal 6 dan 7 Nov (30.666 baris; 29.706 dipakai di ringkasan karena S100 hanya titik 1 sampai 20), 74 grup, 0 galat. Berkas hasil 2 Nov dipindahkan ke `results/arsip/` dan tidak ikut dihitung. Penjelasan sebab yang belum diuji ditulis sebagai **dugaan**, dan angka yang perlu diukur ulang diberi tanda.

> **Catatan revisi (21 Nov 2026).** Ditambahkan **Bagian 13** (Tahap 3: pemrosesan dan analitik dengan Spark) beserta folder `analitik/` pada Bagian 10 dan 11; jumlah uji otomatis kini 22. Angka pada Bagian 7 sampai 9 tidak berubah, dan ukuran Parquet di HDFS masih belum punya berkas ukur (lihat 7.2).

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

Dataset yang dipakai bernama **Sen12Landslides**, yaitu katalog inventaris kejadian tanah longsor (*landslide*) dari berbagai negara yang dipasangkan dengan citra satelit Sentinel-1 dan Sentinel-2. Berkas yang kami pakai berisi **74.956 anotasi** di **16 lokasi** (terbanyak Italy 47.522 dan DominicaMaria 10.172; lalu Newzealand, Chimanimani, Kyrgyzstan1, Hokkaido, Hiroshima, Indonesia, dan lainnya) dengan 5 nilai penulis anotasi (`author`), serta **4.392 patch** citra dari 11 inventaris. Artikel dataset menyebut 15 inventaris di 15 wilayah; angka kami adalah isi berkas yang kami terima (rincian di `data/KAMUS_DATA.md`).

> **Sitasi wajib:** Höhn, P., Heidler, K., Behling, R., & Zhu, X. (2025). A Spatio-Temporal Dataset for Satellite-Based Landslide Detection. *Scientific Data*, 12:1772. DOI artikel: `10.1038/s41597-025-06167-2`. DOI dataset: `10.57967/hf/5883`. Lisensi: CC BY 4.0.

**File mentah** tersimpan di folder `data/raw/`:
- `inventories.zip` — kumpulan shapefile semua inventaris longsor dunia
- `splits_aligned.json` — daftar patch citra satelit yang selaras dengan inventaris
- `SHA256.txt` — hash integritas data mentah

### 2.2 Isi Dataset

Dataset terdiri dari **dua entitas utama**:

**Entitas 1: `annotations` (Poligon Kejadian Longsor)**

| Kolom | Isi | Contoh (nilai asli bila disebut; selain itu ilustrasi bentuk) |
|---|---|---|
| `ann_id` | ID unik anotasi (0 sampai 74.955 di S1) | 0, 1, 2, ... |
| `location` | Nama lokasi kejadian (16 nilai) | Italy, DominicaMaria, Hiroshima |
| `inventory` | Nama inventaris untuk patch: nama `location` huruf kecil; kosong untuk 4 lokasi tanpa patch (DominicaMaria, LanaoDelNorte, Thrissur, Nepal) | italy, hiroshima |
| `event_type` | Penyebab kejadian (5 nilai; 3.142 anotasi kosong) | Rainfall, Hurricane, Earthquake |
| `type` | Jenis gerakan tanah (hanya 2 nilai) | Debris flow (74.853), Ice avalanche (103) |
| `velocity_c` | Kelas kecepatan; di berkas ini selalu sama | `>=5` |
| `author` | Sumber anotasi (5 nilai) | Ferrario, Höhn, Emberson |
| `reference` | Referensi pustaka (terpotong 50 karakter di berkas asli) | https://doi.org/10.57967/hf/5883 |
| `event_conf` | Keyakinan atas tanggal kejadian (0 sampai 1) | 0.95, 1.0 |
| `area` | Luas poligon; satuan tidak dinyatakan sumber (diduga m²) | 412.3 |
| `pre_date` | Tanggal citra sebelum kejadian (boleh kosong) | 2019-03-02 |
| `event_date` | Tanggal kejadian (2016-04-01 sampai 2023-05-16) | 2019-03-15 |
| `post_date` | Tanggal citra sesudah kejadian | 2019-03-20 |
| `pre_dt2`, `event_dt2`, `post_dt2` | Tanggal kedua; arti tidak dijelaskan sumber, disimpan apa adanya | - |
| `center_lon` | Bujur titik pusat poligon | 11.4548681 |
| `center_lat` | Lintang titik pusat poligon | 43.7734078 |
| `bbox_min_lon` | Batas barat kotak pembatas | 11.4547 |
| `bbox_min_lat` | Batas selatan kotak pembatas | 43.7733 |
| `bbox_max_lon` | Batas timur kotak pembatas | 11.4549 |
| `bbox_max_lat` | Batas utara kotak pembatas | 43.7735 |
| `sim_batch` | Nomor batch simulasi (0 = data asli, 1 sampai 99 = salinan) | 0 |

Total: **74.956 baris** pada data dasar (Skala S1). Tipe tiap kolom di MongoDB, PostGIS, dan Parquet ada di `data/KAMUS_DATA.md`.

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
  - Titik pusat dan kotak pembatas digeser acak sampai ±0,25° (bujur dan lintang, selisih yang sama untuk keduanya)
  - Keenam kolom tanggal digeser acak sampai ±365 hari (jumlah hari yang sama untuk keenamnya)
  - `sim_batch` diisi dengan nomor batch
- Seed acak tetap `20261023` (batch b memakai pembangkit acak `seed + b`) → hasil identik di semua laptop
- Sampelnya **bersarang**: batch S10 adalah bagian dari S100

**Tiga skala data yang dihasilkan:**

| Skala | Faktor | Anotasi | Patch | Ukuran berkas CSV + NDJSON |
|---|---|---|---|---|
| **S1** (data asli) | 1× | 74.956 | 4.392 | 74,6 MiB |
| **S10** (simulasi 10×) | 10× | 749.560 | 43.920 | 747,9 MiB |
| **S100** (simulasi 100×) | 100× | 7.495.600 | 439.200 | 7.507,8 MiB (≈ 7,33 GiB) |

Sumber ukuran: `results/pengukuran_mentah.csv`. Semua file output diverifikasi dengan checksum SHA-256 yang tersimpan di `data/CHECKSUMS.txt` (`python data/generate_scales.py --verify`).

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
- `center_2dsphere` — indeks bola berbasis sel S2 Geometry pada titik pusat (W2, W3)
- `bbox_2dsphere` — indeks bola pada kotak pembatas (W4)
- `dates.event_1` — indeks tanggal kejadian
- `event_type_1_dates.event_1` — indeks gabungan tipe + tanggal
- `location_1_dates.event_1` — indeks gabungan lokasi + tanggal
- `inventory_1_split_1` (patches) — indeks gabungan inventaris + partisi

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
- `ann_center_gist` — indeks GiST (Generalized Search Tree, struktur mirip R-Tree) pada titik pusat
- `ann_bbox_gist` — indeks GiST pada kotak pembatas
- `ann_event_date` — indeks B-Tree pada tanggal kejadian
- `ann_type_date` — indeks B-Tree gabungan tipe + tanggal
- `ann_location_date` — indeks B-Tree gabungan lokasi + tanggal
- `pat_inventory_split` — indeks B-Tree gabungan inventaris + split (tabel `patches`)
- Setelah semua indeks dibuat, `VACUUM ANALYZE` dijalankan pada kedua tabel

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
**Pertanyaan:** "Tampilkan lokasi, jenis kejadian, dan tanggal kejadian anotasi nomor X."
- Paling dasar: mengambil satu rekaman berdasarkan `ann_id`
- Diuji dengan 1 klien, lalu 10, 50, dan 100 klien serentak (uji konkurensi, hanya di S100)
- **Kueri MongoDB:** `db.annotations.find({_id: X}, {location: 1, event_type: 1, "dates.event": 1})` (`ann_id` disimpan sebagai `_id`)
- **Kueri PostGIS:** `SELECT ann_id, location, event_type, event_date FROM annotations WHERE ann_id = X`
- **Kueri Spark:** `SELECT ann_id, location, event_type, event_date FROM annotations WHERE ann_id = X`

### W2 — Spatial Window (Titik dalam Jendela Persegi)
**Pertanyaan:** "Berapa banyak anotasi yang titik pusatnya berada di dalam jendela persegi ±0,01° (sekitar 1,1 km dari pusat ke tepi) di sekitar titik uji?"
- Jendela persegi, bukan lingkaran. Tepi jendela digeser 0,00000005° (setengah langkah dari kisi koordinat 1e-7°) supaya tidak ada titik data yang tepat di tepi, sehingga ketiga penyimpanan seharusnya memberi jumlah yang sama
- **Kueri MongoDB:** `{center: {$geoWithin: {$geometry: <poligon jendela>}}}`
- **Kueri PostGIS:** `WHERE ST_Intersects(center, ST_MakeEnvelope(x0, y0, x1, y1, 4326))`
- **Kueri Spark:** `WHERE center_lon BETWEEN x0 AND x1 AND center_lat BETWEEN y0 AND y1`

### W3 — Spatial-Temporal Range (Spasial + Filter Waktu)
**Pertanyaan:** "Berapa banyak anotasi dalam jendela ±0,01° di sekitar titik ini, yang tanggal kejadiannya berada dalam ±30 hari dari tanggal kejadian titik uji?"
- Menambahkan filter rentang tanggal di atas W2
- Memadukan indeks spasial (`center`) dengan indeks tanggal. Tidak ada indeks gabungan spasial + tanggal, jadi MongoDB dan PostGIS memilih sendiri indeks yang dipakai

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

**Status pencatatan (12 Nov 2026):** yang sudah ada di `results/` ialah ukuran di disk MongoDB dan PostGIS untuk S1, S10, dan S100 (`pengukuran_mongodb.csv`, `pengukuran_postgis.csv`), ukuran berkas mentah (`pengukuran_mentah.csv`), dan waktu bangun indeks hanya di S10 (MongoDB 23,9 detik; PostGIS 4,2 detik). **Belum tercatat:** waktu muat semua penyimpanan dan waktu indeks di S100. Ukuran Parquet di HDFS baru tercatat pada 22 Nov 2026 (`pengukuran_spark.csv`, lihat 7.2).

### W8 — Batch Append (Tambah Data Ke Tabel Aktif)
**Pertanyaan:** "Berapa lama waktu yang dibutuhkan untuk menambahkan 1 batch data baru (`batch100`, 74.956 baris anotasi + 4.392 patch) ke tabel S100 yang sudah berisi 7,5 juta baris dan sudah terindeks penuh?"
- Menguji kemampuan penulisan tambahan (*append write*) tanpa rekonstruksi tabel
- **Hasil:** MongoDB annotations = **42,074 detik**, MongoDB patches = **0,731 detik**; PostGIS (annotations + patches) = **4,461 detik**; Spark belum diukur
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
- **Warm:** kueri dijalankan tanpa restart container, jadi cache database sudah terisi
- **Cold:** protokolnya me-restart container lalu menjalankan satu ulangan per berkas (`--cold-warm cold --repeats 1 --first-run-no N`). Pola waktunya menunjukkan hanya **ulangan 1** yang benar-benar dingin: ulangan 2 dan 3 sering jauh lebih cepat (contoh PostGIS W3 S100: 11,6 ms, lalu 2,4 dan 2,4 ms), diduga karena restart hanya dilakukan sekali. Baris Cold di `banding.csv` dan `ringkasan.csv` menggabungkan ketiga ulangan sehingga terlihat lebih cepat dari yang sebenarnya; angka ulangan 1 ada di Bagian 7.5
- **Skala S100 memakai 20 titik pertama (`kueri_id` 1 sampai 20):** rancangannya 20 titik, tetapi berkas MongoDB W1 sampai W3 dan PostGIS W1 di S100 memuat 100 titik, sedangkan berkas lain hanya 20. Karena itu ringkasan dan perbandingan S100 dihitung dengan `--titik-maks 20` (hanya titik 1 sampai 20; 15 di antaranya titik di dalam sebaran data)

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
- `--first-run-no` : nomor ulangan pertama (untuk melanjutkan sesi; bawaan 1)
- `--clients` : jumlah klien serentak (untuk W1)
- `--repeats` : jumlah ulangan (bawaan 3)
- `--note` : catatan varian (misalnya `varian=tanpa-indeks`)
- `--limit-titik` : batasi jumlah titik uji
- `--force` : lewati pemeriksaan jumlah data

Setiap hasil disimpan ke file CSV di folder `results/` dengan nama format
`YYYYMMDD_[store]_[workload]_[scale].csv`. Sesi berikutnya untuk kombinasi yang sama pada hari yang sama diberi akhiran `_2`, `_3`, dan seterusnya (contoh: `20261107_postgis_W3_S10_2.csv` adalah sesi cold ulangan 1; `20261107_mongodb_W1_S100_2.csv` adalah sesi 50 klien). Berkas hasil 2 Nov ada di `results/arsip/`.

### 6.3 Verifikasi Kebenaran Hasil

Sebelum angka performa dipercaya, seluruh hasil kueri diverifikasi keabsahan isinya:
- Jawaban benar (*ground truth*) dihitung `bench/kebenaran.py` dan tersimpan di `bench/benar/W1_S1.csv` s.d. `W6_S1.csv`. **Wasit ini hanya ada untuk S1.**
- Skrip `bench/compare_counts.py` membandingkan **jumlah hasil** tiap kueri (bukan isi barisnya) dari ketiga penyimpanan, dan dengan wasit bila ada
- Untuk S10 dan S100 ketiga penyimpanan dibandingkan satu sama lain (`--tanpa-wasit`); hasilnya di `results/uji_silang_S10_S100.txt`. Semua jumlah hasil sama kecuali **satu kueri**: S100 W2 titik 19 (MongoDB 1.401; PostGIS dan Spark 1.400). Selisihnya satu anotasi yang berjarak sekitar 5 mm di luar tepi jendela; dugaannya toleransi sel S2 MongoDB di tepi jendela (belum dibuktikan)
- Selisih selain itu dianggap salah dan diselidiki sebelum angka dipakai di laporan

### 6.4 Mesin Uji

Laptop uji resmi tim adalah **laptop Elsa Claudia Putri** (satu mesin supaya hardware konsisten). Berkas CSV hasil tidak mencatat nama mesin, jadi kepastian mesinnya bersumber dari catatan tim, bukan dari berkas:
- **Prosesor:** Intel Core i5-13420H (Gen 13, 8 inti fisik)
- **RAM:** 16 GB
- **Penyimpanan:** NVMe SSD
- **OS:** Windows 11 + Docker Desktop

Spesifikasi di atas berlaku untuk seluruh pengukuran Bagian 7 (tahap penyimpanan). Pengukuran waktu **Tahap 3** (Bagian 13) dijalankan di laptop lain, yaitu laptop Wildan (Lenovo 20JTS1PK00, Intel Core i5-6200U 2 inti/4 utas, RAM 11,9 GB, WSL2 dibatasi `memory=6GB processors=2`), sehingga angkanya tidak dibandingkan langsung dengan latensi pada Bagian 7.

---

## BAGIAN 7: HASIL PENGUKURAN EMPIRIS

### 7.1 Perbandingan Latensi Median

Sumber data: `results/banding.csv` (**28 baris**: 25 di tabel bawah ditambah 3 baris konkurensi) dan `results/ringkasan.csv` (**74 grup**, statistik lengkap per database × workload × skala × kondisi). Keduanya dibuat dengan `python bench/summarize.py --titik-maks 20` dari 90 berkas hasil 6 dan 7 Nov. Median dihitung dari semua kueri dan semua ulangan (3) tiap grup; skala S100 memakai titik 1 sampai 20. Angka tebal = tercepat.

**Tabel semua skenario dari `banding.csv`** (milidetik, median):

| Workload | Skala | Kondisi | Varian | MongoDB (ms) | PostGIS (ms) | Spark (ms) | Tercepat | Terlambat ÷ tercepat |
|---|---|---|---|---|---|---|---|---|
| W1 | S1 | Warm | — | 1,503 | **1,200** | 92,889 | **PostGIS** | 77,4× |
| W1 | S10 | Warm | — | 1,451 | **0,724** | 84,221 | **PostGIS** | 116,4× |
| W1 | S100 | Warm | — | 0,819 | **0,681** | 205,740 | **PostGIS** | 301,9× |
| W2 | S1 | Warm | — | 2,102 | **0,958** | 114,781 | **PostGIS** | 119,9× |
| W2 | S10 | Warm | — | 2,461 | **0,909** | 155,132 | **PostGIS** | 170,7× |
| W2 | S10 | Warm | tanpa-indeks | 1.119,729 | **213,921** | — | **PostGIS** | 5,2× |
| W2 | S100 | Warm | — | 8,829 | **1,202** | 545,959 | **PostGIS** | 454,4× |
| W3 | S1 | Warm | — | 1,845 | **0,915** | 115,053 | **PostGIS** | 125,7× |
| W3 | S10 | Cold | — | 3,519 | **0,822** | — | **PostGIS** | 4,3× |
| W3 | S10 | Warm | — | 2,175 | **2,050** | 165,380 | **PostGIS** | 80,7× |
| W3 | S10 | Warm | tanpa-indeks | 440,877 | **158,250** | — | **PostGIS** | 2,8× |
| W3 | S100 | Cold | — | 12,250 | **3,094** | — | **PostGIS** | 4,0× |
| W3 | S100 | Warm | — | **11,231** | 12,956 | 636,928 | **MongoDB** | 56,7× |
| W4 | S1 | Warm | — | 9,431 | **1,136** | 113,499 | **PostGIS** | 99,9× |
| W4 | S10 | Warm | — | 22,733 | **2,011** | 187,785 | **PostGIS** | 93,4× |
| W4 | S10 | Warm | tanpa-indeks | 632,785 | **196,672** | — | **PostGIS** | 3,2× |
| W4 | S100 | Warm | — | 639,974 | **32,973** | 926,173 | **PostGIS** | 28,1× |
| W5 | S1 | Warm | — | 51,111 | **26,996** | 625,964 | **PostGIS** | 23,2× |
| W5 | S10 | Cold | — | 1.176,506 | **74,190** | — | **PostGIS** | 15,9× |
| W5 | S10 | Warm | — | 523,681 | **135,430** | 670,541 | **PostGIS** | 5,0× |
| W5 | S100 | Cold | — | 4.483,146 | **727,333** | — | **PostGIS** | 6,2× |
| W5 | S100 | Warm | — | 6.869,304 | **1.141,604** | 1.293,227 | **PostGIS** | 6,0× |
| W6 | S1 | Warm | — | **3,251** | 3,381 | 393,632 | **MongoDB** | 121,1× |
| W6 | S10 | Warm | — | **14,412** | 21,971 | 516,875 | **MongoDB** | 35,9× |
| W6 | S100 | Warm | — | 131,669 | **73,143** | 531,194 | **PostGIS** | 7,3× |

Dari 18 skenario utama (6 beban × 3 skala, warm, tanpa varian), PostGIS tercepat pada 15; MongoDB tercepat pada W3 S100, W6 S1, dan W6 S10. Spark tidak pernah tercepat; yang terdekat adalah W5 S100 (1.293,2 ms melawan PostGIS 1.141,6 ms).

> **Catatan membaca tabel.**
> - Baris **Cold** menggabungkan semua ulangan, padahal hanya ulangan 1 yang dingin (Bagian 6.1). Angka ulangan 1 ada di Bagian 7.5.
> - **W3 S100 PostGIS Warm (12,956 ms) mencurigakan:** pada skenario yang sama, ulangan cold 2 dan 3 hanya sekitar 2,4 ms. Ukur ulang dengan `EXPLAIN (ANALYZE, BUFFERS)` sebelum angka ini dipakai untuk menyimpulkan bahwa MongoDB mengalahkan PostGIS di W3 S100.
> - Jumlah hasil MongoDB, PostGIS, dan Spark sama di semua kueri yang dibandingkan, kecuali S100 W2 titik 19 (Bagian 6.3).

**W1 S100 dengan banyak klien** (median latensi per kueri; satu klien = baris W1 S100 pada tabel di atas):

| Klien | MongoDB (ms) | PostGIS (ms) | Tercepat |
|---|---|---|---|
| 10 | 1,410 | **0,828** | PostGIS |
| 50 | 7,454 | **4,018** | PostGIS |
| 100 | 15,606 | **12,497** | PostGIS |

Latensi p95 untuk 1, 10, 50, dan 100 klien ada di Bagian 7.4.

### 7.2 Jejak Penyimpanan di Disk (Skala S100, 7,5 Juta Baris)

| Komponen | Ukuran | Sumber |
|---|---|---|
| **MongoDB** total (data + indeks; `annotations` + `patches`) | 1.861,96 MiB (≈ 1,82 GiB) | `results/pengukuran_mongodb.csv` |
| **PostGIS** total (tabel + indeks + TOAST; `annotations` + `patches`) | 3.497,09 MiB (≈ 3,42 GiB) | `results/pengukuran_postgis.csv` |
| **Parquet ZSTD** di HDFS (`annotations` + `patches`, satu salinan, tanpa indeks) | 435,36 MiB (≈ 0,43 GiB) | `results/pengukuran_spark.csv` |

Parquet diukur pada 22 Nov 2026 di laptop Wildan dengan `python bench/catat.py ukuran --store spark`: 434,108 MiB untuk `annotations` dan 1,252 MiB untuk `patches` di S100 (S1 3,964 MiB; S10 43,234 MiB). Angka lama "≈ 470 MiB" dari catatan saat konversi diganti angka terukur ini. Parquet tidak memiliki indeks, sedangkan angka MongoDB dan PostGIS sudah termasuk indeks. Kolom `ukuran_dengan_replika` bernilai 3 kali ukuran satu salinan (1.306,08 MiB di S100): faktor replikasi berkas Parquet 3, karena berkas ditulis oleh Spark yang tidak memuat `hadoop.env` (replikasi 2); angka itu tidak dibandingkan. Sebagai pembanding, berkas mentah S100 (CSV + NDJSON) berukuran 7.507,8 MiB.

### 7.3 Efek Indeks (Eksperimen E1 pada S10)

| Workload | Database | Dengan Indeks | Tanpa Indeks | Faktor Percepatan |
|---|---|---|---|---|
| W2 | PostGIS | 0,91 ms | 213,9 ms | **235×** |
| W2 | MongoDB | 2,46 ms | 1.119,7 ms | **455×** |
| W3 | PostGIS | 2,05 ms | 158,3 ms | **77×** |
| W3 | MongoDB | 2,18 ms | 440,9 ms | **203×** |
| W4 | PostGIS | 2,01 ms | 196,7 ms | **98×** |
| W4 | MongoDB | 22,7 ms | 632,8 ms | **28×** |

### 7.4 Konkurensi Multi-Client (W1 di S100, Latensi p95)

| Jumlah Klien | MongoDB p95 | PostGIS p95 |
|---|---|---|
| 1 klien | 3,474 ms | 1,013 ms |
| 10 klien | 3,024 ms | 1,487 ms |
| 50 klien | 17,831 ms | 8,346 ms |
| 100 klien | 37,158 ms | 25,754 ms |

Semua baris dihitung dari titik uji 1 sampai 20 (`--titik-maks 20`) supaya sebanding. Versi sebelumnya memakai 100 titik pada baris 1 klien (2,516 dan 1,222 ms), padahal baris klien lain hanya 20 titik. Klien adalah thread Python di laptop yang sama dengan server database, jadi sebagian antrean ada di sisi klien, bukan di database.

### 7.5 Cold Run — Efek Cache Dingin (W3 & W5)

Cold run dijalankan dengan me-restart container Docker, lalu menjalankan satu ulangan per berkas (`--cold-warm cold --repeats 1 --first-run-no N`). Diuji pada W3 (spasial-temporal) dan W5 (agregasi besar). Pola waktunya menunjukkan hanya **ulangan 1** yang benar-benar dingin: ulangan 2 dan 3 sering jauh lebih cepat, misalnya PostGIS W3 S100 11,586 ms (ulangan 1), lalu 2,414 dan 2,447 ms. Karena itu tabel di bawah memakai **ulangan 1 saja**, dibandingkan dengan median warm dari Bagian 7.1. (Baris Cold di Bagian 7.1 menggabungkan ketiga ulangan.)

| Beban | Skala | MongoDB cold ul. 1 (ms) | MongoDB warm (ms) | Cold ÷ warm | PostGIS cold ul. 1 (ms) | PostGIS warm (ms) | Cold ÷ warm |
|---|---|---|---|---|---|---|---|
| W3 | S10 | 4,000 | 2,175 | 1,84× | 0,804 | 2,050 | 0,39× |
| W3 | S100 | 16,062 | 11,231 | 1,43× | 11,586 | 12,956 | 0,89× |
| W5 | S10 | 1.176,506 | 523,681 | 2,25× | 74,190 | 135,430 | 0,55× |
| W5 | S100 | 4.486,238 | 6.869,304 | 0,65× | 838,717 | 1.141,604 | 0,73× |

**Anomali.** Rasio di atas 1 berarti cold lebih lambat dari warm, seperti yang diharapkan; hanya tiga dari delapan rasio yang begitu (MongoDB W3 S10, W3 S100, W5 S10). Lima rasio lain di bawah 1, termasuk keempat skenario PostGIS, padahal cold seharusnya lebih lambat. Dua dugaan, belum diuji: (a) restart container tidak mengosongkan cache sistem operasi di mesin virtual Docker, jadi "cold" hanya mengosongkan cache di dalam database; (b) sesi warm terganggu hal lain di laptop. Paling dicurigai adalah median warm PostGIS W3 S100 (12,956 ms), karena ulangan cold 2 dan 3 pada skenario yang sama hanya sekitar 2,4 ms.

**Yang aman disimpulkan.** Pada keempat skenario cold ulangan 1, PostGIS tetap lebih cepat dari MongoDB (0,804 vs 4,000; 11,586 vs 16,062; 74,190 vs 1.176,506; 838,717 vs 4.486,238 ms). Besar efek cold terhadap warm belum bisa dipastikan sebelum W3 dan W5 diukur ulang dengan restart sebelum setiap ulangan dan bukti bahwa cache memang kosong (di PostGIS lewat `EXPLAIN (ANALYZE, BUFFERS)`, baris `read=`).

---

## BAGIAN 8: ANALISIS HIPOTESIS (H1–H5)

### H1 — Indeks Spasial Lebih Cepat dari Parquet pada Kueri Jendela (W2 & W3)

**Pernyataan:** Database dengan indeks spasial (MongoDB dan PostGIS) lebih cepat dari Spark Parquet pada W2 dan W3, dan selisihnya makin besar dari S1 ke S100. Dianggap gugur bila selisih mengecil atau terbalik.

**Hasil:** **DITERIMA SEBAGIAN.**
- Bagian pertama terbukti: di S1, S10, dan S100, MongoDB dan PostGIS lebih cepat dari Spark pada W2 dan W3. Di S100 selisihnya 49× sampai 454×.
- Bagian kedua (selisih makin besar) hanya terbukti pada W2. Kecepatan relatif terhadap Spark, dari S1 ke S100:

| Beban | PostGIS | MongoDB |
|---|---|---|
| W2 | ≈ 120× → ≈ 454× (melebar) | ≈ 55× → ≈ 62× (melebar) |
| W3 | ≈ 126× → ≈ 49× (mengecil; angka PostGIS W3 S100 perlu diukur ulang, lihat 7.5) | ≈ 62× → ≈ 57× (mengecil) |

- Latensi W2 saat data membesar 100× (S1 ke S100): PostGIS 0,96 → 1,20 ms; MongoDB 2,10 → 8,83 ms (naik sekitar 4,2×).
- Eksperimen E1 (S10, tanpa indeks): W2 MongoDB 455× dan PostGIS 235× lebih lambat; W3 MongoDB 203× dan PostGIS 77× lebih lambat (Bagian 7.3).
- **Penjelasan:** indeks pohon spasial membatasi pemindaian ke cabang yang relevan, sedangkan Spark memindai seluruh Parquet. Itu menjelaskan kenapa PostGIS hampir datar pada W2. Kenapa selisih W3 mengecil belum diselidiki.

### H2 — PostGIS Lebih Cepat dari MongoDB untuk Bounding Box (W4)

**Pernyataan:** Untuk kueri kotak pembatas beririsan dengan filter atribut, PostGIS lebih cepat dari MongoDB.

**Hasil:** **DITERIMA.**
- Median W4: PostGIS lebih cepat di ketiga skala dan selisihnya melebar: **8,3×** (S1: 1,14 vs 9,43 ms), **11,3×** (S10: 2,01 vs 22,7 ms), **19,4×** (S100: 33,0 vs 640,0 ms)
- p95 di S100: PostGIS 1.484 ms vs MongoDB 206.458 ms (≈ 3,4 menit)
- Ekor MongoDB itu berasal dari dua titik saja: titik 3 dan titik 20 (keduanya Hiroshima, Rainfall, sekitar 33 ribu hasil), 186 sampai 218 detik per eksekusi (6 dari 60 eksekusi). Titik yang sama dijawab PostGIS dalam 75 sampai 123 ms dan Spark dalam 0,9 sampai 1,0 detik. Dua titik dengan hasil jauh lebih banyak (titik 11 Italy, 382.668 hasil; titik 19 DominicaMaria, 124.247 hasil) di MongoDB hanya 22 sampai 28 detik, jadi lambatnya bukan semata karena jumlah hasil.
- **Dugaan sebab (belum diuji):** rencana kueri yang dipilih MongoDB untuk dua titik itu berbeda dari titik lain, misalnya memakai indeks `event_type` + tanggal, bukan `bbox_2dsphere`. Cara membuktikan: jalankan `explain("executionStats")` untuk titik 3 dan 20 (`mongodb/queries/w4.js`, `ANN_ID` diambil dari `bench/points.json`). Penjelasan lama di dokumen ini (GiST membandingkan float secara native; 2dsphere memakai "sel Geohash S2" yang makin berat bila data padat) tidak terbukti, dan S2 bukan Geohash.

### H3 — Urutan Efisiensi Disk: Parquet < PostGIS < MongoDB

**Pernyataan (awal):** Urutan dari paling hemat disk: Parquet, PostGIS, MongoDB.

**Hasil:** **DITOLAK sebagian: Parquet paling kecil sesuai dugaan, tetapi urutan MongoDB dan PostGIS terbalik.**
- Terukur di S100 (`results/pengukuran_*.csv`): **Parquet 435,36 MiB < MongoDB 1.861,96 MiB < PostGIS 3.497,09 MiB**. Parquet 4,3× lebih kecil dari MongoDB dan 8,0× dari PostGIS (tanpa indeks; bila indeks tidak dihitung, data anotasi Parquet 2,8× dan 5,7× lebih kecil dari data MongoDB dan PostGIS). Antara MongoDB dan PostGIS, MongoDB **1,88× lebih hemat**, dan lebih kecil di ketiga skala (2,31× di S1, 1,87× di S10, 1,88× di S100)
- Parquet paling kecil sesuai dugaan (kolumnar, ZSTD, tanpa indeks); angkanya ada di `results/pengukuran_spark.csv` (Bagian 7.2). Yang terbalik hanya urutan MongoDB dan PostGIS
- **Dugaan sebab:** selisih terbesar ada di data. `annotations` S100 memakai 1.218,80 MiB di MongoDB (WiredTiger mengompresi 4.541,66 MiB data tak terkompres; bawaannya Snappy) lawan 2.468,02 MiB di PostGIS (halaman 8 KiB tanpa kompresi tabel). Indeksnya 613,62 lawan 941,18 MiB

### H4 — Spark Lebih Cepat untuk Agregasi Skala Besar (W5 di S100)

**Pernyataan:** Untuk agregasi seluruh tabel pada skala S100, Spark SQL lebih cepat dari MongoDB.

**Hasil:** **DITERIMA SEBAGIAN.**
- W5 S100 (7,5 juta baris): Spark 1.293 ms vs MongoDB 6.869 ms → Spark **5,3× lebih cepat** ✓ (PostGIS 1.142 ms masih 1,13× lebih cepat dari Spark)
- W6 S100 (439 ribu baris): MongoDB 131,7 ms vs Spark 531,2 ms → MongoDB **4,0× lebih cepat**, jadi bagian ini gugur ✗ (PostGIS 73,1 ms tercepat)
- W5 S10 (750 ribu baris): Spark 670,5 ms masih lebih lambat dari MongoDB 523,7 ms. Titik silang Spark dan MongoDB ada di antara S10 dan S100; letak pastinya belum diuji karena tidak ada skala di antaranya
- **Dugaan sebab (belum diuji):** pada tabel kecil-menengah (W6) biaya tetap Spark (perencanaan dan penjadwalan task) mengalahkan manfaat kolumnar; pada W5 S100 waktu pemindaian yang besar menutup biaya itu

### H5 — Latensi Stabil Saat 50 Klien Serentak (W1 di S100)

**Pernyataan:** Latensi p95 pada 50 klien serentak tidak boleh lebih dari 10× latensi p95 klien tunggal.

**Hasil:** **DITERIMA, dengan catatan.**
- Pada titik yang sama (1 sampai 20): MongoDB 17,831 / 3,474 = **5,13×**; PostGIS 8,346 / 1,013 = **8,24×**. Keduanya di bawah batas 10× ✓
- Urutannya terbalik dari versi sebelumnya: pada 50 klien p95 PostGIS naik lebih banyak (8,24×) daripada MongoDB (5,13×), walau nilai absolutnya tetap lebih kecil (8,3 vs 17,8 ms)
- Pada 100 klien batas 10× terlewati: MongoDB 37,158 / 3,474 = **10,70×**; PostGIS 25,754 / 1,013 = **25,42×**
- Versi sebelumnya (7,08× dan 6,83×) membagi p95 50 klien (20 titik) dengan p95 1 klien dari 100 titik (2,516 dan 1,222 ms), jadi tidak sebanding
- Klien adalah thread Python di laptop yang sama dengan server database, jadi sebagian antrean ada di sisi klien. Hasil ini tidak membuktikan kapasitas server pada 50 klien yang sebenarnya

---

## BAGIAN 9: KESIMPULAN DAN REKOMENDASI

### Kapan Pakai MongoDB?
- Ketika skema data sering berubah-ubah (heterogen/JSON)
- Ketika kapasitas disk terbatas dan kompresi penting (1,82 GiB vs 3,42 GiB di S100, lawan PostGIS)
- Ketika membutuhkan skalabilitas horizontal (*sharding*) tanpa perubahan besar arsitektur (tidak diuji di proyek ini)
- Kueri titik tunggal W1 sub-2 ms (median 0,8 sampai 1,5 ms), walau PostGIS sama cepat atau lebih cepat (0,7 sampai 1,2 ms)

### Kapan Pakai PostgreSQL/PostGIS?
- Ketika aplikasi membutuhkan kueri spasial poligon dan bounding box yang kompleks
- Ketika akurasi SQL relasional dengan JOIN dan constraint penting
- Web GIS, peta interaktif, analisis spasial operasional
- Kueri W2, W3, dan W4 paling cepat pada 8 dari 9 skenario skala (pengecualian W3 S100, yang perlu diukur ulang); hingga 454× lebih cepat dari Spark (W2 S100) dan 19,4× lebih cepat dari MongoDB (W4 S100)

### Kapan Pakai Spark + Parquet?
- Ketika kebutuhan utama adalah agregasi analitik pada dataset sangat besar (>5 juta baris): di S100 Spark 5,3× lebih cepat dari MongoDB pada W5, tetapi PostGIS masih 1,13× lebih cepat (1.141,6 vs 1.293,2 ms)
- Data warehouse, pelatihan model AI/ML, batch processing
- Ketika biaya penyimpanan menjadi pertimbangan utama: Parquet 435,36 MiB, sekitar 8,0× lebih kecil dari PostGIS dan 4,3× lebih kecil dari MongoDB (S100, satu salinan, tanpa indeks; lihat 7.2)
- Bukan untuk kueri titik real-time (median W1 84 sampai 206 ms per kueri)
- Untuk analitik batch atas katalog ini (ETL dan 14 kueri), Spark pada HDFS dan Parquet menghasilkan angka yang cocok dengan acuan mandiri pada S1, S10, dan S100, dan memproses 7.495.600 anotasi dalam sekitar 129 detik (median putaran warm, laptop dua inti); lihat Bagian 13

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
├── analitik/               ← Tahap 3: pemrosesan dan analitik Spark (Wildan)
│   ├── spark_pipeline.py       ← Pipeline: ETL, 14 kueri, ekspor CSV, pencatat waktu
│   ├── kueri_analitik.py       ← Definisi SQL 14 kueri dan skema kolom
│   ├── fungsi_spark.py         ← Fungsi Spark yang ditiru di SQLite untuk uji
│   ├── referensi.py            ← Penghitung acuan mandiri (Python murni)
│   ├── referensi_S1/, referensi_S10/, referensi_S100/  ← 14 CSV jawaban benar per skala
│   ├── cocokkan.py             ← Bandingkan hasil Spark dengan acuan
│   ├── uji_sql.py              ← Jalankan 14 SQL di SQLite, bandingkan dengan acuan
│   ├── ringkas_waktu.py        ← Ringkas waktu pemrosesan per skala
│   ├── grafik.py               ← Grafik G1 sampai G6 (PNG)
│   └── README.md               ← Cara menjalankan dan memeriksa Tahap 3
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
│   ├── banding.csv             ← Perbandingan langsung 28 baris
│   ├── pengukuran_mentah.csv   ← Ukuran file mentah
│   ├── pengukuran_mongodb.csv  ← Ukuran disk, waktu indeks S10, W8 MongoDB
│   ├── pengukuran_postgis.csv  ← Ukuran disk, waktu indeks S10, W8 PostGIS
│   ├── uji_silang_S10_S100.txt ← Hasil compare_counts untuk S10 dan S100
│   ├── analitik/               ← Hasil Tahap 3: S1/, S10/, S100/ (14 CSV tiap skala), waktu, grafik/
│   ├── 20261106_*.csv, 20261107_*.csv  ← 90 file hasil benchmark mentah
│   └── arsip/                  ← 21 file 2 Nov (tidak dihitung)
│
├── docs/                   ← Dokumen deliverable
│   ├── Laporan_Big_Data_Kelompok2.docx  ← Laporan (Bab I sampai V)
│   ├── penjelasan_lengkap.md   ← Dokumen ini
│   └── panduan_cek_hasil.md    ← Cara melihat dan memahami hasil
│
├── tests/                  ← Test suite otomatis
│   ├── uji_semua.py            ← Jalankan 22 uji sekaligus
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
| **Muhammad Wildan Arif Maulana** | Project Lead, Dokumentasi & QA, pemrosesan-analitik Spark | `docs/`, `tests/`, `analitik/`, file di root repo |
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
> Höhn, P., Heidler, K., Behling, R., & Zhu, X. (2025). A Spatio-Temporal Dataset for Satellite-Based Landslide Detection. *Scientific Data*, 12:1772. DOI artikel: `10.1038/s41597-025-06167-2`. DOI dataset: `10.57967/hf/5883`. Lisensi: CC BY 4.0.

### Sumber Inventaris Asli yang Digunakan dalam Dataset
Jumlah anotasi per penulis (kolom `author`, S1):
- Ferrario dkk. (2023): 47.522
- Höhn dkk. (2025): 16.306
- Emberson dkk. (2022): 10.619
- Belair dkk. (2022): 328
- Kirschbaum dkk. (2010, 2015): 181

### Repositori Kode & Hasil
`https://github.com/wildnrfm/kelompok2-bigdata-storage`

### Reprodusibilitas
Siapa pun dapat mereproduksi seluruh benchmark dengan:
1. `git clone https://github.com/wildnrfm/kelompok2-bigdata-storage.git`
2. `python data/convert_inventory.py` (membutuhkan `data/raw/inventories.zip`)
3. `python data/generate_scales.py --all`, lalu `python data/generate_scales.py --verify` (mencocokkan checksum di `data/CHECKSUMS.txt`)
4. Jalankan Docker untuk masing-masing database
5. `python bench/harness.py --store [mongodb|postgis|spark] --workload [W1–W6] --scale [S1|S10|S100]`
6. `python bench/summarize.py --titik-maks 20` (S100 hanya titik 1 sampai 20)
7. `python bench/compare_counts.py --tanpa-wasit --titik-maks 20 <tiga berkas hasil W2 S100>`, lalu `python tests/uji_semua.py` untuk uji tanpa Docker
8. Tahap 3 (pemrosesan dan analitik): ikuti [analitik/README.md](../analitik/README.md), lalu `python analitik/cocokkan.py` untuk S1 (dan `--hasil results/analitik/S10`, `--hasil results/analitik/S100`)

Seed acak tetap `20261023` menjamin hasil generator identik di semua mesin.

---

## BAGIAN 13: TAHAP 3, PEMROSESAN DAN ANALITIK DENGAN SPARK

Tahap ini ditambahkan setelah tahap penyimpanan (Bagian 1 sampai 12). Data yang sudah tersimpan di HDFS dalam format Parquet diolah dengan Apache Spark menjadi tabel turunan, dianalisis dengan 14 kueri SQL, dan hasilnya diekspor sebagai CSV dan grafik. Tahap ini menjawab dua pertanyaan: (1) apa yang dapat diketahui dari isi katalog Sen12Landslides dan seberapa dapat diandalkan metadatanya, dan (2) bagaimana waktu pemrosesan Spark berubah ketika data bertambah dari S1 ke S10 dan S100. Kode dan cara menjalankannya ada di `analitik/` ([analitik/README.md](../analitik/README.md)); laporan membahasnya di Bab IV.

### 13.1 Rancangan Pipeline

Satu putaran pipeline (`analitik/spark_pipeline.py`) terdiri dari tiga tahap yang waktunya dicatat satu per satu:

1. **ETL.** Satu kueri SQL membuat tabel turunan `ann_kaya` (jenis pemicu, tahun dan bulan kejadian, belahan bumi, selang hari citra sebelum dan sesudah kejadian, dekade luas, dan sel 0,1 derajat). Tabel ditulis ke HDFS sebagai Parquet ZSTD, dibaca ulang, dan jumlah barisnya dicocokkan.
2. **Analitik.** 14 kueri Spark SQL: `q0` sampai `q2` untuk jumlah dan kualitas data, `a1` sampai `a8` untuk isi katalog.
3. **Ekspor.** Tiap hasil ditulis sebagai CSV di `results/analitik/<skala>/`.

Setiap sesi Spark mengulang putaran penuh: putaran pertama berlabel *cold* (JVM baru), sisanya *warm*. S1 dan S10 dijalankan 5 putaran (1 cold dan 4 warm), S100 3 putaran (1 cold dan 2 warm) karena satu putaran S100 memerlukan 2 sampai 3 menit. Angka utama adalah median putaran *warm*. Seluruhnya 13 putaran kali 17 tahap (ETL, 14 kueri, ekspor, dan total) menjadi 221 baris di `results/analitik/waktu_pemrosesan.csv`.

### 13.2 Verifikasi Kebenaran

Angka analitik hanya berguna bila benar, sehingga setiap tabel dibandingkan dengan perhitungan yang tidak memakai Spark:
- `analitik/referensi.py` menghitung ke-14 hasil dengan Python murni; hasilnya disimpan di `analitik/referensi_S1/`, `analitik/referensi_S10/`, dan `analitik/referensi_S100/`.
- Ke-14 SQL yang sama dijalankan di SQLite dengan fungsi Spark yang ditiru (`analitik/uji_sql.py`) dan hasilnya sama dengan acuan; pada S1 juga sama dengan perhitungan pandas.
- Hasil Spark 3.5.0 sungguhan dibandingkan dengan acuan oleh `analitik/cocokkan.py` dengan toleransi relatif 1e-9: S1 14 tabel (1.130 sel), S10 dan S100 masing-masing 14 tabel (1.418 sel); semuanya cocok.
- `tests/uji_semua.py` kini memuat 22 uji, 5 di antaranya untuk tahap ini.

Persentil dihitung eksak dengan `percentile()` (interpolasi linear), bukan `percentile_approx`, agar dapat dicocokkan angka demi angka.

### 13.3 Hasil Pengukuran Waktu

Pengukuran resmi dijalankan pada 19 November 2026 di **laptop Wildan** (Lenovo 20JTS1PK00, Intel Core i5-6200U 2 inti/4 utas, RAM 11,9 GB, WSL2 `memory=6GB processors=2`, Docker 2 CPU dan 5,79 GiB). Spark 3.5.0 berjalan dalam mode `local[2]` dengan `--driver-memory 2g`; HDFS terdiri dari 1 NameNode dan 2 DataNode (replikasi 2) pada satu mesin virtual; MongoDB, PostGIS, dan Grafana dimatikan. Mesin ini bukan laptop uji Bagian 7, sehingga angkanya tidak dibandingkan langsung dengan latensi di sana.

| Skala | Anotasi | Median warm (detik) | Cold (detik) | Anotasi per detik | Waktu dibanding S1 |
|---|---:|---:|---:|---:|---:|
| S1 | 74.956 | 22,3 | 52,0 | 3.359 | 1,0× |
| S10 | 749.560 | 34,5 | 53,4 | 21.704 | 1,5× |
| S100 | 7.495.600 | 128,8 | 181,3 | 58.189 | 5,8× |

Data bertambah 100 kali, sedangkan waktu satu putaran hanya 5,8 kali. Bila waktu dimodelkan sebanding dengan n^b (n = jumlah anotasi), eksponen b adalah 0,38 dari S1 ke S100, 0,19 dari S1 ke S10, dan 0,57 dari S10 ke S100. Eksponen yang naik mengindikasikan bahwa pada data kecil sebagian besar waktu adalah biaya tetap Spark, dan baru pada S100 data mulai menentukan. Pada S100 empat tahap terberat adalah ETL (38,0 detik; 29,5%), `q2_pemeriksaan` (22,8 detik; 17,7%), `q1_kolom_kosong` (17,1 detik; 13,3%), dan `a4a_area_jenis` (13,1 detik; 10,1%). Hasil berasal dari satu sesi per skala tanpa pengulangan antarsesi, sehingga dibaca sebagai orde besaran.

### 13.4 Temuan tentang Isi Katalog (S1)

Analisis isi hanya bermakna pada S1, karena S10 dan S100 adalah salinan simulasi.
- **Terkonsentrasi.** Rainfall 52.686 anotasi (70,3%); lokasi Italy 47.522 anotasi (63,4%), seluruhnya pada satu hari (16 Mei 2023). Tiga lokasi teratas 60.936 anotasi (81,3%), dan 9 dari 16 lokasi hanya memiliki satu tanggal kejadian (66.467 anotasi, 88,7%). Pola tahunan karenanya lebih mencerminkan inventaris mana yang masuk dataset daripada kecenderungan longsor di dunia.
- **Kualitas.** 11 dari 13 pemeriksaan kualitas tidak menemukan pelanggaran, termasuk seluruh pemeriksaan geometri dan identitas. Dua temuan: 3.142 anotasi (4,2%) tanpa jenis pemicu, dan 109 anotasi (0,15%) tanpa satu pun tanggal kejadian. Sebanyak 23 dari 31 kolom lengkap; `inventory` kosong pada 11.260 baris (15,0%), seluruhnya dari empat lokasi yang tidak memiliki inventaris.
- **Luas anotasi.** Median luas berbeda jauh antarjenis pemicu (474 untuk Rainfall, 11.182 untuk Earthquake; satuan tidak dinyatakan sumber data), tetapi 90,2% anotasi Rainfall berasal dari Italy, sehingga pemicu, lokasi, dan cara anotasi tercampur. Perbedaan itu tidak boleh dibaca sebagai sifat pemicunya.
- **Kepadatan spasial.** 368 sel 0,1 derajat terisi; median 42,5 anotasi per sel, persentil ke-95 sekitar 1.075, dan maksimum 4.255 pada sel sekitar 11,85° BT dan 44,15° LU (Italy). Dua puluh sel terpadat memuat 53,5% anotasi.
- **Keandalan atribut.** `event_conf` bernilai tepat 1,0 pada 85,2% anotasi (seluruh Rainfall, Hurricane, Tropical Storm, dan Cyclone), sehingga kolom ini hanya informatif untuk Earthquake dan anotasi tanpa jenis.

Katalog dapat dipakai untuk pencarian dan agregasi seperti pada tahap penyimpanan, tetapi kurang memadai sebagai dasar model prediktif tanpa data tambahan. Karena itu model prediktif tidak dibuat.

### 13.5 Keterbatasan

1. S10 dan S100 adalah salinan simulasi S1 (seed 20261023): waktunya sah untuk menguji skala, tetapi isinya tidak bermakna ilmiah.
2. Pengukuran dilakukan pada satu laptop dua inti dalam satu sesi per skala, tanpa pengulangan antarsesi, dan kemungkinan pelambatan akibat suhu tidak diukur. HDFS berupa dua DataNode pada satu mesin virtual dan Spark berjalan `local[2]`, sehingga tidak ada transfer jaringan antarnode dan hasilnya tidak mewakili klaster terdistribusi.
3. Jumlah putaran sedikit (S1 dan S10 lima putaran; S100 tiga putaran, sehingga median *warm* S100 adalah rata-rata dua angka). Waktu memuat Parquet ke HDFS (26,8; 41,8; dan 235,5 detik untuk S1, S10, dan S100) hanya tercatat dari keluaran terminal, tidak dari berkas di `results/`.
4. Satuan kolom `area` tidak dinyatakan sumber data. MongoDB dan PostGIS tidak diberi analitik yang sama, sehingga tahap ini tidak membandingkan ketiganya pada beban analitik.
