# PANDUAN CARA CEK HASIL BENCHMARK
## Kelompok 2 — Big Data Storage (Kelas B)

**Anggota Tim:**
1. **Muhammad Wildan Arif Maulana** (23051204065) — *Project Lead, Documentation & QA*
2. **Maulana Hidayah Syaif Ali Khan** (23051204068) — *Data Collection & Conversion Engineer*
3. **Elsa Claudia Putri** (23051204038) — *Storage Engineer A (MongoDB Specialist & Benchmark Lead)*
4. **Muhammad Syah Levi** (23051204051) — *Storage Engineer B (PostGIS & HDFS-Spark Specialist)*
5. **Marsanda Sofi Aminarti** (23051204066) — *Performance Analyst & Validation Lead*

> Repositori: `https://github.com/wildnrfm/kelompok2-bigdata-storage`

---

## CARA 1: BUKA RINGKASAN UTAMA (PALING CEPAT)

### File: `results/ringkasan.csv`

Ini adalah **satu file terpenting** yang merangkum semua hasil benchmark dalam satu tabel. Setiap baris mewakili satu kombinasi unik: satu database × satu workload × satu skala × satu kondisi.

**Cara membukanya:**
```
# Di Excel / LibreOffice Calc
Buka File → results/ringkasan.csv → Import sebagai CSV (delimiter: koma)

# Di terminal (PowerShell)
Import-Csv results\ringkasan.csv | Format-Table -AutoSize

# Di terminal (Python)
python -c "import csv; [print(r) for r in csv.DictReader(open('results/ringkasan.csv'))]"
```

**Kolom-kolom yang ada:**

| Kolom | Arti |
|---|---|
| `penyimpanan` | Database: `mongodb`, `postgis`, atau `spark` |
| `beban_kerja` | Jenis kueri: `W1` hingga `W6` |
| `skala` | Volume data: `S1`, `S10`, atau `S100` |
| `cold_warm` | Kondisi cache: `warm` atau `cold` |
| `konkurensi` | Jumlah klien serentak (kosong = 1 klien) |
| `varian` | Varian khusus (`tanpa-indeks` untuk E1, kosong = normal) |
| `ulangan_n` | Jumlah ulangan yang dijalankan |
| `kueri_n` | Jumlah total kueri yang dieksekusi |
| `median_ms` | **Latensi median dalam milidetik** ← angka utama |
| `median_ulangan_min` | Median terbaik dari semua ulangan |
| `median_ulangan_maks` | Median terburuk dari semua ulangan |
| `p95_ms` | Persentil ke-95 latensi (99 dari 100 kueri lebih cepat dari ini) |
| `rata2_ms` | Rata-rata latensi |
| `qps_1klien` | Throughput: kueri per detik |
| `galat_n` | Jumlah kueri yang error (harus 0) |
| `berkas_n` | Jumlah file sumber yang digabungkan |

**Cara baca angkanya:**
- Semakin **kecil** `median_ms` → semakin **cepat**
- Angka `p95_ms` menunjukkan performa terburuk yang masih "normal" (ekor distribusi)
- Kalau `galat_n > 0` → ada yang error, perlu diperiksa

---

## CARA 2: LIHAT PERBANDINGAN LANGSUNG ANTAR DATABASE

### File: `results/banding.csv`

File ini menampilkan **tiga database secara berdampingan** untuk setiap skenario yang sama. Ini yang paling mudah dibaca untuk menjawab "siapa paling cepat di kondisi X?".

**Cara membukanya:**
```
Import-Csv results\banding.csv | Format-Table -AutoSize
```

**Kolom-kolom yang ada:**

| Kolom | Arti |
|---|---|
| `beban_kerja` | W1–W6 |
| `skala` | S1, S10, S100 |
| `cold_warm` | warm atau cold |
| `konkurensi` | Jumlah klien (kosong = 1) |
| `varian` | Normal atau tanpa-indeks |
| `median_ms_mongodb` | Latensi median MongoDB (ms) |
| `median_ms_postgis` | Latensi median PostGIS (ms) |
| `median_ms_spark` | Latensi median Spark (ms), kosong jika tidak diuji |
| `tercepat` | Nama database yang paling cepat |
| `rasio_terlambat_vs_tercepat` | Berapa kali lebih lambat database terburuk vs terbaik |

**Contoh cara baca 2 baris penting:**
```
W2, S100, warm → mongodb=7.741, postgis=1.202, spark=545.959 → tercepat=postgis, rasio=454.4
```
Artinya: untuk kueri radius di 7,5 juta data dalam kondisi warm, PostGIS **454× lebih cepat** dari Spark.

```
W5, S100, warm → mongodb=6869.304, postgis=1141.604, spark=1293.227 → tercepat=postgis, rasio=6.0
```
Artinya: untuk agregasi seluruh tabel 7,5 juta baris, PostGIS paling cepat — tapi Spark (1.293 ms) lebih cepat dari MongoDB (6.869 ms).

---

## CARA 3: CEK HASIL MENTAH PER WORKLOAD

### Folder: `results/*.csv` (111 file)

Setiap file adalah rekaman **mentah per kueri** dari satu sesi benchmark. Nama file mengikuti pola:
```
YYYYMMDD_[database]_[workload]_[skala].csv
YYYYMMDD_[database]_[workload]_[skala]_[nomor_ulangan].csv
```

**Contoh nama file:**
- `20261106_mongodb_W2_S100.csv` — MongoDB, W2, S100, ulangan pertama
- `20261107_postgis_W3_S10_2.csv` — PostGIS, W3, S10, ulangan kedua (Cold Run)
- `20261107_mongodb_W1_S100_2.csv` — MongoDB, W1, S100, ulangan ke-2 (Multi-client)

**File resmi (eksekusi di mesin Elsa) dimulai dengan:**
- `20261106_` → Warm Run W1–W6, semua database, semua skala
- `20261107_` → Cold Run (W3 & W5), Multi-client (W1), Tanpa Indeks (E1)

**Kolom di dalam file mentah:**

| Kolom | Arti |
|---|---|
| `run_id` | ID unik sesi pengujian |
| `store` | Database |
| `workload` | Jenis kueri |
| `scale` | Skala data |
| `cold_warm` | Kondisi cache |
| `point_idx` | Indeks titik uji (0–99) |
| `lon`, `lat` | Koordinat titik uji |
| `latency_ms` | **Latensi kueri ini dalam milidetik** |
| `result_count` | Jumlah baris yang dikembalikan kueri |
| `ok` | Berhasil (`True`) atau error (`False`) |
| `ts` | Timestamp eksekusi |

**Cara buka dan filter:**
```powershell
# Lihat 10 baris pertama
Get-Content results\20261106_mongodb_W2_S100.csv | Select-Object -First 10

# Filter hanya kueri yang berhasil dan sort by latensi
Import-Csv results\20261106_mongodb_W2_S100.csv |
  Where-Object { $_.ok -eq 'True' } |
  Sort-Object { [float]$_.latency_ms } |
  Select-Object point_idx, latency_ms, result_count | Format-Table
```

```python
# Dengan Python + pandas
import pandas as pd
df = pd.read_csv('results/20261106_mongodb_W2_S100.csv')
print(df[df['ok']==True]['latency_ms'].describe())
```

---

## CARA 4: CEK UKURAN DISK DAN WAKTU MUAT (W7)

### File: `results/pengukuran_mongodb.csv`

Berisi data ukuran fisik MongoDB di disk per skala.

**Kolom:** `tanggal`, `penyimpanan`, `skala`, `jenis`, `objek`, `nilai`, `satuan`, `catatan`

Nilai `jenis` yang ada:
- `jumlah_dokumen` — berapa banyak dokumen/baris
- `ukuran_data_di_disk` — ukuran data terkompresi di disk (MiB)
- `ukuran_indeks` — ukuran file indeks (MiB)
- `waktu_muat_detik` — waktu import data (detik)
- `waktu_indeks_detik` — waktu build indeks (detik)

**Cara baca:**
```powershell
Import-Csv results\pengukuran_mongodb.csv |
  Where-Object { $_.skala -eq 'S100' } |
  Format-Table -AutoSize
```

### File: `results/pengukuran_postgis.csv`

Sama seperti di atas tapi untuk PostGIS. Kolom `jenis`:
- `ukuran_data_di_disk` — ukuran heap table (MiB)
- `ukuran_indeks` — ukuran GiST + B-Tree index (MiB)
- `ukuran_total` — total termasuk TOAST (MiB)
- `waktu_muat_detik` — waktu COPY FROM CSV
- `waktu_indeks_detik` — waktu CREATE INDEX CONCURRENTLY

### File: `results/pengukuran_mentah.csv`

Ukuran file mentah (CSV dan NDJSON) per skala, sebagai referensi awal sebelum diimpor.

---

## CARA 5: CEK HASIL EKSPERIMEN KHUSUS

### E1 — Efek Indeks (Kueri Tanpa Indeks)

Cari file dengan nama mengandung tanggal 20261107 dan workload W2/W3/W4 pada skala S10:
- `20261107_mongodb_W2_S10.csv` (dengan flag varian `tanpa-indeks`)
- `20261107_postgis_W2_S10.csv`

Atau filter langsung dari `banding.csv`:
```powershell
Import-Csv results\banding.csv |
  Where-Object { $_.varian -eq 'tanpa-indeks' } |
  Format-Table -AutoSize
```

Bandingkan `median_ms_mongodb` di baris `tanpa-indeks` vs baris normal (varian kosong) untuk workload dan skala yang sama.

### Cold Run — Efek Cache Dingin

Filter dari `ringkasan.csv`:
```powershell
Import-Csv results\ringkasan.csv |
  Where-Object { $_.cold_warm -eq 'cold' } |
  Select-Object penyimpanan, beban_kerja, skala, median_ms, p95_ms |
  Format-Table -AutoSize
```

### Multi-client — Efek Konkurensi

Filter dari `banding.csv`:
```powershell
Import-Csv results\banding.csv |
  Where-Object { $_.beban_kerja -eq 'W1' -and $_.konkurensi -ne '' } |
  Format-Table -AutoSize
```

---

## CARA 6: JALANKAN ULANG PEMBUAT RINGKASAN

Jika ingin regenerasi `ringkasan.csv` dan `banding.csv` dari file mentah:
```powershell
cd C:\Users\elsac\Downloads\bigdata\kelompok2-bigdata-storage
python bench\summarize.py
```

Output:
```
ringkasan.csv : 74 grup
banding.csv   : 28 baris
galat         : 0
```

---

## CARA 7: VERIFIKASI KEBENARAN ANGKA

### Langkah 1 — Bandingkan Jumlah Hasil Kueri Antar Database

```powershell
python bench\compare_counts.py --scale S10
python bench\compare_counts.py --scale S100 --workload W4
```

Output normal: `Semua NNN kueri cocok` — artinya ketiga database mengembalikan jumlah baris yang sama untuk setiap titik uji.

### Langkah 2 — Verifikasi Ground Truth (Jawaban Benar S1)

```powershell
python bench\kebenaran.py --store mongodb --scale S1
python bench\kebenaran.py --store postgis --scale S1
```

Membandingkan hasil kueri aktual dengan jawaban baku di `bench/benar/*.csv`.

### Langkah 3 — Jalankan Test Suite Lengkap

```powershell
python tests\uji_semua.py
```

Harus tampil: `SEMUA UJI LULUS (17 uji, ...)`

---

## CARA 8: MEMBACA HASIL DI GITHUB

Semua hasil sudah di-push ke GitHub dan bisa dibaca langsung di browser:

1. **Buka repositori:** `https://github.com/wildnrfm/kelompok2-bigdata-storage`

2. **Navigasi ke `results/`:**
   - Klik folder `results` → terlihat semua 111 file CSV
   - Klik `banding.csv` → GitHub langsung menampilkan sebagai tabel di browser
   - Klik `ringkasan.csv` → idem

3. **Lihat commit history untuk menelusuri kapan data masuk:**
   - Klik tab `Commits`
   - Commit penting: `054c609` — *"[results] tuntas seluruh benchmark resmi W1-W8 E1 E2 S1 S10 S100 Elsa"*

---

## CARA 9: ANGKA-ANGKA KUNCI YANG PERLU DIINGAT

Ini ringkasan angka paling penting untuk menjawab pertanyaan dosen:

| Pertanyaan | Jawaban | Sumber |
|---|---|---|
| Database tercepat untuk kueri radius (W2 S100)? | **PostGIS: 1,2 ms** (454× lebih cepat dari Spark 546 ms) | `banding.csv` baris W2/S100/warm |
| Database tercepat untuk bounding box (W4 S100)? | **PostGIS: 32,9 ms** vs MongoDB 639,9 ms (19,4× lebih cepat) | `banding.csv` baris W4/S100/warm |
| Seberapa besar manfaat indeks? (E1 W2 S10) | Tanpa indeks: MongoDB 1.120 ms → dengan indeks: 2,5 ms (**455× lebih cepat**) | `banding.csv` baris W2/S10/tanpa-indeks |
| Database paling hemat disk (S100)? | **Parquet ~470 MB**, MongoDB 1,8 GB, PostGIS 3,5 GB | `pengukuran_mongodb.csv` + `pengukuran_postgis.csv` |
| Kapan Spark lebih cepat dari MongoDB? | W5 (agregasi 7,5 juta baris): Spark 1.293 ms vs MongoDB 6.869 ms (**5,3× lebih cepat**) | `banding.csv` baris W5/S100/warm |
| Stabil saat 50 klien serentak? | Ya: MongoDB p95 naik hanya 7,1× (< batas 10×), PostGIS 6,8× | `ringkasan.csv` filter W1/S100/warm/klien=50 |
| Total kueri yang diuji? | 111 file CSV, 74 grup di ringkasan, 0 galat kueri | `ringkasan.csv` kolom `galat_n` |

---

## RINGKASAN LOKASI FILE HASIL

| Yang Dicari | File/Folder | Cara Buka |
|---|---|---|
| Perbandingan langsung 3 database | `results/banding.csv` | Excel / `Import-Csv ... \| Format-Table` |
| Statistik lengkap per grup | `results/ringkasan.csv` | Excel / `Import-Csv ...` |
| Data latensi per kueri mentah | `results/20261106_*.csv` s.d. `20261107_*.csv` | `Get-Content` / pandas |
| Ukuran disk MongoDB | `results/pengukuran_mongodb.csv` | Excel |
| Ukuran disk PostGIS | `results/pengukuran_postgis.csv` | Excel |
| Ukuran file mentah | `results/pengukuran_mentah.csv` | Excel |
| Jawaban benar (ground truth) | `bench/benar/W1_S1.csv` s.d. `W6_S1.csv` | Excel |
| Titik koordinat uji | `bench/points.json` | Notepad / `python -c "import json; ..."` |
| Hash integritas data | `data/CHECKSUMS.txt` | Notepad |
