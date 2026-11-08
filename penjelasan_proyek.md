# Penjelasan Proyek Kelompok 2 — Big Data Storage (Kelas B)

## Judul

**Perbandingan MongoDB dan PostgreSQL/PostGIS terhadap Baseline HDFS-Parquet sebagai Penyimpanan Katalog Metadata Anotasi Longsor dan Patch Citra Sentinel-1/2 Sen12Landslides untuk Pencarian Spasial-Temporal Kejadian Longsor**

---

## Identitas Kelompok

| Nama | NIM | Peran |
|------|-----|-------|
| Muhammad Wildan Arif Maulana | 23051204065 | Project Lead + Documentation/QA |
| Maulana Hidayah Syaif Ali Khan | 23051204068 | Data Collection Engineer |
| Elsa Claudia Putri | 23051204038 | Storage Engineer A (MongoDB) |
| Marsanda Sofi Aminarti | 23051204066 | Performance Analyst |
| Muhammad Syah Levi | 23051204051 | Storage Engineer B (PostGIS + HDFS-Parquet) |

Repo GitHub (privat): https://github.com/wildnrfm/kelompok2-bigdata-storage

---

## 1. Latar Belakang dan Kasus Penggunaan

Dataset Sen12Landslides berisi 170,5 GB citra satelit Sentinel-1/2 beserta metadata 74.956 poligon longsor dan 4.392 patch citra yang sudah dicocokkan. Data sebesar itu tidak praktis dibuka secara keseluruhan hanya untuk mencari satu kejadian longsor di lokasi dan waktu tertentu.

Proyek ini membangun **katalog metadata** — hanya menyimpan atribut kejadian longsor (lokasi, tanggal, tipe pemicu, luas, tingkat keyakinan) tanpa citranya — sehingga pengguna bisa melakukan pencarian spasial-temporal secara cepat. Contoh pertanyaan yang bisa dijawab:

- "Tampilkan semua longsor dalam radius 10 km dari Cianjur, antara 2019–2021."
- "Berapa total kejadian longsor per tipe pemicu per tahun?"
- "Di inventaris mana paling banyak patch citra untuk training?"

**Pengguna**: peneliti geosains, lembaga kebencanaan (BNPB, PVMBG), dan analis risiko bencana yang memerlukan akses cepat ke katalog longsor tanpa harus mengunduh seluruh citra.

**Kebutuhan penyimpanan**: pencarian spasial (titik, kotak), filter temporal (rentang tanggal), filter atribut (tipe pemicu, tingkat keyakinan), agregasi statistik, dan kemampuan menangani volume data yang diperbesar hingga 100 kali ukuran asli.

---

## 2. Dataset

**Sumber**: Sen12Landslides (Höhn dkk., 2025; Scientific Data 12:1772; CC BY 4.0), terdaftar di TerraMosaic Hub.

**Link**: https://huggingface.co/datasets/paulhoehn/Sen12Landslides

**Format mentah**: Shapefile/DBF (ZIP, 22 MB) dan JSON (1 MB). Kami mengonversinya menjadi CSV dan NDJSON menggunakan skrip Python murni (tanpa pustaka GIS eksternal).

### Alur file data

**Sumber (2 file mentah):**

| File | Ukuran | Isi |
|------|--------|-----|
| `inventories.zip` | 22 MB | Shapefile berisi 74.956 poligon longsor (geometri + 15 atribut). Di dalamnya ada 6 file: `.shp` (geometri), `.dbf` (tabel atribut), `.shx` (indeks), `.prj` (koordinat WGS84), `.cpg` (encoding), `.qix` (indeks kueri). |
| `splits_aligned.json` | 1 MB | 4.392 entri pembagian patch citra Sentinel-1/2 ke train, val, dan test. |

**Hasil konversi (4 file, dibuat oleh `convert_inventory.py`):**

| File | Ukuran | Untuk apa |
|------|--------|-----------|
| `annotations.ndjson` | 54 MB | Dimuat ke **MongoDB** — 1 dokumen JSON per poligon longsor, termasuk titik pusat sebagai GeoJSON. |
| `annotations.csv` | 19 MB | Dimuat ke **PostGIS** dan **Spark** — 74.956 baris × 23 kolom. |
| `patches.ndjson` | 0,9 MB | Dimuat ke **MongoDB** — 4.392 dokumen patch. |
| `patches.csv` | 0,5 MB | Dimuat ke **PostGIS** dan **Spark** — 4.392 baris × 8 kolom. |

Jadi: **2 file mentah → dikonversi → 4 file → masuk 3 penyimpanan** (MongoDB, PostGIS, HDFS-Parquet).

### Tabel annotations (poligon longsor)

Berisi 74.956 baris dengan 23 kolom, antara lain:

| Kolom | Keterangan |
|-------|-----------|
| `ann_id` | ID unik (0–74.955) |
| `location` | Nama lokasi (16 nilai: Iburi, Hokkaido, Kodagu,ثلجة, dst.) |
| `event_type` | Pemicu longsor (earthquake, rainfall, rapid_snowmelt, construction, unknown) |
| `event_date` | Tanggal kejadian (1920–2022); 109 anotasi tidak punya tanggal |
| `center_lon`, `center_lat` | Titik pusat poligon (WGS84) |
| `bbox_min_lon/lat`, `bbox_max_lon/lat` | Kotak pembatas poligon |
| `area` | Luas poligon |
| `event_conf` | Tingkat keyakinan kejadian (0–1) |
| `sim_batch` | Nomor batch simulasi (0 untuk data asli) |

### Tabel patches (citra Sentinel-1/2)

Berisi 4.392 baris dengan 8 kolom: `patch_id`, `split` (train/val/test), `inventory`, jalur citra S2, S1 ascending, S1 descending, `pixel_annotated`, dan `sim_batch`.

### Simulasi volume

Data asli (S1) diperbesar secara deterministik:
- **S10** (10×): 749.560 anotasi, 43.920 patch
- **S100** (100×): 7.495.600 anotasi, 439.200 patch

Simulasi mengkloning data asli dengan `sim_batch` berbeda dan `ann_id` yang di-offset, sehingga distribusi atribut tetap proporsional. Checksum dicocokkan antar laptop untuk memastikan semua anggota bekerja dengan data yang identik.

---

## 3. Pemilihan Teknologi dan Justifikasi

Kami memilih **dua teknologi dari kategori berbeda** ditambah satu **baseline**:

### A. MongoDB 8 (Document Store)

MongoDB dipilih karena model dokumen cocok dengan struktur data longsor: satu poligon = satu dokumen JSON lengkap. Keunggulan utamanya:

- **Skema fleksibel**: 109 anotasi tidak punya `event_date` dan 26 tidak punya `event_type` — di MongoDB, field yang kosong cukup tidak ditulis, tanpa perlu NULL.
- **GeoJSON native**: titik pusat disimpan sebagai `{type: "Point", coordinates: [lon, lat]}` dan kotak pembatas sebagai `Polygon`. MongoDB bisa langsung memahami format ini.
- **Indeks 2dsphere**: memungkinkan pencarian spasial seperti `$geoWithin` dan `$near` dengan performa baik.
- **CAP**: condong ke CP (consistency + partition tolerance). Pada replica set, saat terjadi partisi jaringan, MongoDB memilih konsistensi di atas ketersediaan.
- **Skalabilitas horizontal**: bisa scale-out lewat sharding, meski dalam proyek ini kami menggunakan satu node.

### B. PostgreSQL 17 + PostGIS 3.5 (Relasional + Spasial)

PostGIS dipilih karena menyediakan tipe data spasial dan indeks yang terintegrasi langsung dalam SQL:

- **Tipe `geometry`**: kolom `center` bertipe `Point` dan `bbox` bertipe `Polygon`, keduanya dalam SRID 4326 (WGS84).
- **Indeks GiST**: indeks spasial pada kolom geometry, memungkinkan operasi `ST_Intersects`, `ST_DWithin`, dan `ST_MakeEnvelope` dengan efisien.
- **SQL gabungan**: satu query bisa menggabungkan filter spasial (`ST_Intersects`), temporal (`event_date BETWEEN`), dan atribut (`event_type = 'earthquake'`) sekaligus — kemampuan yang cocok untuk kasus pencarian kompleks seperti W4.
- **ACID**: menjamin konsistensi transaksi penuh.
- **CAP**: pada deployment satu node seperti proyek ini, PostgreSQL bersifat CA. Pada deployment terdistribusi dengan streaming replication, bisa condong ke CP.
- **Row-oriented**: setiap baris disimpan utuh, efisien untuk pencarian titik dan filter WHERE, tetapi kurang optimal untuk agregasi kolom tunggal.

### C. HDFS + Parquet + Spark SQL (Baseline Kolumnar)

Kombinasi ini dipilih sebagai **baseline pembanding**, bukan sebagai solusi utama:

- **Parquet (kolumnar)**: hanya membaca kolom yang dibutuhkan — agregasi (W5, W6) yang hanya perlu `event_type` dan tahun tidak perlu membaca 23 kolom lainnya. Kompresi ZSTD sangat efisien.
- **HDFS**: penyimpanan terdistribusi (1 NameNode + 2 DataNode). Data dipecah menjadi blok dan direplikasi.
- **Spark SQL**: engine kueri yang membaca Parquet dari HDFS. Cocok untuk batch processing.
- **Keterbatasan**: tidak punya indeks spasial. Pencarian titik (W2, W3) harus memindai seluruh file — diperkirakan lebih lambat dari MongoDB dan PostGIS.
- Menjadi baseline karena tugas ini mewajibkan HDFS + Parquet sebagai pembanding.

### D. Yang Tidak Dipilih: Apache Cassandra

Cassandra dipertimbangkan tetapi tidak dipilih karena **tidak memiliki indeks spasial bawaan**. Untuk mendukung kueri spasial, Cassandra memerlukan lapisan tambahan seperti GeoMesa atau integrasi Solr, yang menambah kompleksitas signifikan tanpa keuntungan yang jelas untuk kasus penggunaan ini dibanding MongoDB (yang sudah punya 2dsphere) atau PostGIS (yang sudah punya GiST).

---

## 4. Arsitektur Sistem

Ketiga penyimpanan dijalankan sebagai container Docker di laptop yang sama, masing-masing dengan memori terbatas agar perbandingan adil:

```
data/raw/ (inventories.zip + splits_aligned.json)
        │
        ▼  convert_inventory.py
data/out/s1/ (CSV + NDJSON)
        │
   ┌────┼────────────────┐
   ▼    ▼                ▼
MongoDB    PostGIS         HDFS + Parquet
(port 27017) (port 5433)    (port 9870, Spark 4040)
   │    │                │
   └────┼────────────────┘
        ▼
   bench/harness.py → results/*.csv
   bench/compare_counts.py (cek jumlah = wasit)
   bench/summarize.py → ringkasan.csv, banding.csv
```

Setiap penyimpanan memiliki folder sendiri di repo (`mongodb/`, `postgis/`, `hdfs-parquet/`) berisi `docker-compose.yml`, skrip muat data, skrip indeks, dan kueri W1–W6. Harness (`bench/harness.py`) menjalankan kueri yang sama di ketiga penyimpanan dan mencatat waktu (cold + warm, minimal 3 ulangan).

Volume data dipasang read-only (`../data:/sen12ls-data:ro`) supaya ketiga penyimpanan membaca sumber yang sama.

---

## 5. Model Data per Penyimpanan

### MongoDB

```json
// annotations (satu dokumen per longsor)
{
  "_id": 0,
  "location": "Iburi",
  "event_type": "earthquake",
  "dates": {"event": {"$date": "2018-09-05T00:00:00Z"}},
  "center": {"type": "Point", "coordinates": [141.93, 42.75]},
  "bbox": {"type": "Polygon", "coordinates": [[[141.92, 42.74], ...]]},
  "area": 12345.6,
  "event_conf": 0.95
}
```
Indeks: `center` (2dsphere), `bbox` (2dsphere), `dates.event`, `{event_type, dates.event}`, `{location, dates.event}`.

### PostGIS

```sql
CREATE TABLE annotations (
  ann_id       INTEGER PRIMARY KEY,
  location     TEXT,
  event_type   TEXT,
  event_date   DATE,
  center       geometry(Point, 4326),
  bbox         geometry(Polygon, 4326),
  area         DOUBLE PRECISION,
  event_conf   DOUBLE PRECISION,
  ...
);
```
Indeks: GiST pada `center` dan `bbox`; B-tree pada `event_date`, `(event_type, event_date)`, `(location, event_date)`.

### Parquet (HDFS)

File Parquet dengan kompresi ZSTD, disimpan di HDFS (`/sen12ls/s1/annotations.parquet`). Schema mengikuti kolom CSV (23 kolom). Tidak ada indeks — Spark SQL membaca secara batch.

---

## 6. Rencana Pengujian

### 8 Workload

| Kode | Pertanyaan yang dijawab | Tipe |
|------|------------------------|------|
| W1 | "Ambil detail longsor #12345" | Point lookup |
| W2 | "Berapa longsor dalam radius 1 km dari titik ini?" | Spasial (titik pusat) |
| W3 | "Berapa longsor dalam radius 1 km dari titik ini, antara ±30 hari dari tanggal ini?" | Spasial + temporal |
| W4 | "Berapa longsor bertipe earthquake dengan keyakinan ≥ 0,9 yang kotak pembatasnya beririsan dengan jendela 22 km ini?" | Spasial + multi-atribut |
| W5 | "Berapa total longsor per tipe pemicu per tahun?" | Agregasi |
| W6 | "Berapa rata-rata pixel teranotasi per inventaris per split?" | Agregasi |
| W7 | "Berapa lama muat data S1, S10, S100 dan berapa ukuran di disk?" | Ingest |
| W8 | "Berapa lama menambahkan 1 batch baru ke S100?" | Ingest tambahan |

Setiap workload menggunakan **100 titik uji tetap** (70 di dalam wilayah data, 30 di luar) yang sama untuk ketiga penyimpanan. Hasilnya dicocokkan dengan **wasit jawaban benar** yang di-generate langsung dari CSV menggunakan Python murni, sehingga kami bisa membuktikan bahwa ketiga penyimpanan menjawab pertanyaan yang sama persis.

Pengukuran: minimal 3 ulangan per kueri, mode warm (satu putaran pemanasan lalu dicatat) dan cold (nyalakan ulang container). Dijalankan di satu laptop uji (Elsa, i5-13420H, 16 GB RAM) supaya hasilnya fair.

### 5 Hipotesis

| Kode | Dugaan |
|------|--------|
| H1 | MongoDB dan PostGIS lebih cepat dari Parquet pada pencarian spasial (W2–W3) berkat indeks, dan selisih melebar saat data membesar (S1 → S100). |
| H2 | PostGIS lebih cepat dari MongoDB pada W4 (kotak pembatas + filter atribut gabungan) karena GiST + SQL optimizer. |
| H3 | Ukuran di disk dari kecil ke besar: Parquet (ZSTD) < PostGIS < MongoDB (termasuk indeks). |
| H4 | Spark SQL atas Parquet lebih cepat dari MongoDB pada agregasi (W5–W6) di S100, karena format kolumnar hanya membaca kolom yang dibutuhkan. |
| H5 | Pada W1 dengan 50 klien konkuren di S100, latency p95 tetap kurang dari 10× latency p95 satu klien. |

### 2 Eksperimen Tambahan

- **E1**: Ulangi W2–W4 **tanpa indeks** di MongoDB dan PostGIS → buktikan bahwa indeks spasial memang signifikan.
- **E2**: Kurva skala — jalankan W1–W6 di S1, S10, S100 → amati bagaimana latensi berubah saat data membesar 10× dan 100×.

---

## 7. Progress Saat Ini

### Fase 1 — Siapkan repo ✅ (selesai)

- Repo GitHub dibuat, diisi kode lengkap (panduan, docker-compose, kueri, harness, tests), dan di-push.
- Semua 5 anggota sudah clone, uji kode (17/17 test lulus), dan latihan Git.
- Spesifikasi laptop tercatat; laptop uji utama ditetapkan (Elsa, 16 GB RAM).
- KICKOFF selesai; keputusan di-pin di grup.

### Fase 2 — Data dan penyimpanan 🔄 (sedang berjalan)

- Data S1 sudah dikonversi dan diverifikasi: 74.956 anotasi, 4.392 patch, 18 pemeriksaan lulus.
- 100 titik uji tetap dan wasit jawaban benar W1–W6 sudah di-generate.
- Docker MongoDB jalan (container `sen12ls-mongo`).
- Docker PostGIS jalan, skema tabel dibuat (container `sen12ls-postgis`).
- Docker HDFS + Spark sedang di-setup (4 container).

### Selanjutnya

- **Fase 3**: Muat S1 ke ketiga penyimpanan, jalankan W3, cocokkan jumlah hasil → SINKRON 1.
- **Fase 4**: Diagram arsitektur, slide pitching, latihan presentasi → SINKRON 2.
- **Fase 5–6** (Tugas Tengah Semester): Skala S10 dan S100, pengukuran W1–W8, eksperimen E1–E2, analisis hipotesis H1–H5, laporan akhir.
