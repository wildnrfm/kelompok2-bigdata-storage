# PANDUAN CARA CEK HASIL BENCHMARK
## Kelompok 2 — Big Data Storage (Kelas B)

**Anggota Tim:**
1. **Muhammad Wildan Arif Maulana** (23051204065) — *Project Lead, Documentation & QA, dan pemrosesan-analitik Spark (Tahap 3)*
2. **Maulana Hidayah Syaif Ali Khan** (23051204068) — *Data Collection & Conversion Engineer*
3. **Elsa Claudia Putri** (23051204038) — *Storage Engineer A (MongoDB Specialist & Benchmark Lead)*
4. **Muhammad Syah Levi** (23051204051) — *Storage Engineer B (PostGIS & HDFS-Spark Specialist)*
5. **Marsanda Sofi Aminarti** (23051204066) — *Performance Analyst & Validation Lead*

> Repositori: `https://github.com/wildnrfm/kelompok2-bigdata-storage`

> **Catatan revisi (12 Nov 2026).** Panduan ini disamakan dengan isi repo: nama kolom berkas mentah, jumlah berkas (90, bukan 111), perintah `compare_counts.py` dan `kebenaran.py`, dan angka kunci. Ringkasan dibuat dengan `python bench\summarize.py --titik-maks 20`. Hal yang belum terbukti ditulis sebagai **dugaan**, dan hal yang belum diukur ditulis **belum terukur**.

> **Catatan revisi (21 Nov 2026).** Ditambahkan **CARA 10** (cek hasil Tahap 3, pemrosesan dan analitik Spark di `results/analitik/`) dan jumlah uji otomatis diperbarui menjadi 22. Cara 1 sampai 9 tidak berubah.

> **Catatan revisi (26 Nov 2026).** Ditambahkan **CARA 11** (cek penelusuran rencana kueri, 25 Nov 2026). Enam berkas hasil baru (`20261125_postgis_*`) ikut dihitung: `ringkasan.csv` kini 80 grup dan `banding.csv` 34 baris, dari 96 berkas (31.026 baris; 30.066 dipakai). Angka seri utama (6 dan 7 Nov) tidak berubah; grup tambahan ditandai kolom `varian` = `bawaan` atau `custom-plan`. Waktu muat dan waktu indeks S100 kini tercatat (CARA 4).

---

## CARA 1: BUKA RINGKASAN UTAMA (PALING CEPAT)

### Berkas: `results/ringkasan.csv`

Ini **satu berkas terpenting**: tabel ringkasan semua hasil benchmark. Setiap baris mewakili satu kombinasi unik: satu penyimpanan × satu beban kerja × satu skala × satu kondisi. Isinya 80 grup, dihitung dari 96 berkas hasil (90 berkas tanggal 6 dan 7 Nov, ditambah 6 berkas 25 Nov). Berkas 2 Nov ada di `results/arsip/` dan tidak ikut dihitung. Enam grup terakhir adalah varian rencana kueri PostGIS (`varian` = `bawaan` atau `custom-plan`; CARA 11); seri utama tidak berubah.

**Cara membukanya:**
```powershell
# Di Excel / LibreOffice Calc
# Buka File → results\ringkasan.csv → Import sebagai CSV (pemisah: koma)

# Di terminal (PowerShell)
Import-Csv results\ringkasan.csv | Format-Table -AutoSize

# Di terminal (Python)
python -c "import csv; [print(r) for r in csv.DictReader(open('results/ringkasan.csv'))]"
```

**Kolom yang ada:**

| Kolom | Arti |
|---|---|
| `penyimpanan` | `mongodb`, `postgis`, atau `spark` |
| `beban_kerja` | Jenis kueri: `W1` sampai `W6` |
| `skala` | Volume data: `S1`, `S10`, atau `S100` |
| `cold_warm` | `warm` atau `cold`. Baris `cold` menggabungkan semua ulangan, padahal hanya ulangan 1 yang dingin (lihat CARA 5) |
| `konkurensi` | Jumlah klien serentak (kosong = 1 klien) |
| `varian` | `tanpa-indeks` untuk E1; `bawaan` dan `custom-plan` untuk pengulangan PostGIS 25 Nov (CARA 11); kosong = seri utama |
| `ulangan_n` | Jumlah ulangan |
| `kueri_n` | Jumlah kueri yang dihitung (titik × ulangan × klien). Di S100 hanya titik 1 sampai 20 |
| `median_ms` | **Latensi median dalam milidetik** ← angka utama |
| `median_ulangan_min` | Median ulangan yang paling cepat |
| `median_ulangan_maks` | Median ulangan yang paling lambat |
| `p95_ms` | Persentil ke-95: 95 dari 100 kueri selesai dalam waktu ini atau lebih cepat |
| `rata2_ms` | Rata-rata latensi |
| `qps_1klien` | 1000 ÷ `rata2_ms`: perkiraan kueri per detik untuk satu klien yang berjalan berurutan |
| `galat_n` | Jumlah kueri yang galat (harus 0) |
| `berkas_n` | Jumlah berkas sumber yang digabung |

**Cara membaca angkanya:**
- Makin **kecil** `median_ms`, makin **cepat**
- `p95_ms` menunjukkan ekor distribusi: kueri paling lambat yang masih dianggap wajar. Satu-dua kueri sangat lambat bisa menaikkan p95 jauh di atas median (contoh: W4 S100 MongoDB, median 640 ms tetapi p95 206.458 ms)
- Kalau `galat_n > 0`, ada kueri yang galat dan perlu diperiksa

---

## CARA 2: LIHAT PERBANDINGAN LANGSUNG ANTAR PENYIMPANAN

### Berkas: `results/banding.csv`

Berkas ini menampilkan **tiga penyimpanan berdampingan** untuk skenario yang sama (34 baris; 6 di antaranya varian rencana kueri 25 Nov). Ini yang paling mudah dibaca untuk menjawab "siapa paling cepat di kondisi X?".

**Cara membukanya:**
```powershell
Import-Csv results\banding.csv | Format-Table -AutoSize
```

**Kolom yang ada:**

| Kolom | Arti |
|---|---|
| `beban_kerja` | W1 sampai W6 |
| `skala` | S1, S10, S100 |
| `cold_warm` | warm atau cold |
| `konkurensi` | Jumlah klien (kosong = 1) |
| `varian` | Kosong (normal), `tanpa-indeks`, `bawaan`, atau `custom-plan` |
| `median_ms_mongodb` | Latensi median MongoDB (ms) |
| `median_ms_postgis` | Latensi median PostGIS (ms) |
| `median_ms_spark` | Latensi median Spark (ms); kosong bila tidak diuji |
| `tercepat` | Penyimpanan yang paling cepat |
| `rasio_terlambat_vs_tercepat` | Berapa kali lebih lambat yang paling lambat dibanding yang tercepat |

**Contoh cara baca dua baris penting:**
```
W2, S100, warm → mongodb=8.829, postgis=1.202, spark=545.959 → tercepat=postgis, rasio=454.4
```
Artinya: untuk kueri jendela di 7,5 juta anotasi (warm), PostGIS **454× lebih cepat** dari Spark dan sekitar 7,3× lebih cepat dari MongoDB.

```
W5, S100, warm → mongodb=6869.304, postgis=1141.604, spark=1293.227 → tercepat=postgis, rasio=6.0
```
Artinya: untuk agregasi seluruh tabel 7,5 juta baris, PostGIS paling cepat. Spark (1.293 ms) lebih cepat dari MongoDB (6.869 ms) tetapi masih sedikit di belakang PostGIS.

**Ringkasan 18 skenario utama** (6 beban × 3 skala, warm, tanpa varian): PostGIS tercepat pada 15; MongoDB tercepat pada W3 S100, W6 S1, dan W6 S10; Spark tidak pernah tercepat. Keunggulan MongoDB di W3 S100 muncul karena PostGIS memakai rencana generik: dengan rencana kustom PostGIS 0,79 ms (CARA 11), sehingga PostGIS tercepat pada 16 dari 18.

---

## CARA 3: CEK HASIL MENTAH PER KUERI

### Folder: `results/*.csv` (96 berkas)

Setiap berkas adalah rekaman **mentah per kueri** dari satu sesi benchmark. Nama berkas mengikuti pola:
```
YYYYMMDD_[penyimpanan]_[beban_kerja]_[skala].csv
YYYYMMDD_[penyimpanan]_[beban_kerja]_[skala]_[k].csv
```

Akhiran `_k` (k = 2, 3, ...) menandai **sesi ke-k** untuk kombinasi yang sama pada hari yang sama. Itu belum tentu sama dengan nomor ulangan; nomor ulangan sebenarnya ada di kolom `ulangan` di dalam berkas.

**Contoh nama berkas:**
- `20261106_mongodb_W2_S100.csv` — MongoDB, W2, S100, warm; berisi ulangan 1 sampai 3
- `20261107_postgis_W3_S10_2.csv` — PostGIS, W3, S10, cold, ulangan 1 (sesi ke-2 hari itu)
- `20261107_mongodb_W1_S100_2.csv` — MongoDB, W1, S100, 50 klien (kolom `catatan` berisi `konkurensi=50`)

**Berkas resmi (dijalankan di laptop uji tim, mesin Elsa; CSV tidak mencatat nama mesin):**
- `20261106_` (56 berkas) → warm W1 sampai W6 untuk ketiga penyimpanan dan semua skala, ditambah E1 W2 dan W3 MongoDB
- `20261107_` (34 berkas) → cold (W3 dan W5), multi-klien (W1 S100), dan E1 lainnya
- `20261125_` (6 berkas) → pengulangan PostGIS W2, W3, dan W4 pada S100 (warm, 20 titik, 3 ulangan) dengan `varian=bawaan` dan `varian=custom-plan`, untuk penelusuran rencana kueri (CARA 11)
- Berkas `20261102_` (21 berkas, S1) ada di `results/arsip/` dan tidak dihitung

**Kolom di dalam berkas mentah:**

| Kolom | Arti |
|---|---|
| `penyimpanan` | `mongodb`, `postgis`, atau `spark` |
| `beban_kerja` | `W1` sampai `W6` |
| `skala` | `S1`, `S10`, atau `S100` |
| `ulangan` | Nomor ulangan (1, 2, 3) |
| `cold_warm` | `warm` atau `cold` |
| `kueri_id` | Nomor urut kueri (1 sampai 100): titik ke-N di `bench/points.json` untuk W2 sampai W4, ID anotasi ke-N untuk W1. W5 dan W6 hanya satu kueri |
| `waktu_ms` | **Latensi kueri ini dalam milidetik** |
| `jumlah_hasil` | Jumlah hasil kueri; **-1 berarti galat** |
| `catatan` | Catatan sesi, misalnya `varian=tanpa-indeks` atau `konkurensi=50` |

**Perhatian di S100:** rancangannya memakai 20 titik pertama, tetapi sebagian berkas S100 (MongoDB W1 sampai W3, PostGIS W1) memuat 100 titik. Saring `kueri_id <= 20` bila membandingkan atau menghitung sendiri.

**Cara membuka dan menyaring:**
```powershell
# Lihat 10 baris pertama
Get-Content results\20261106_mongodb_W2_S100.csv | Select-Object -First 10

# 5 kueri paling lambat di S100 (titik 1 sampai 20), tanpa yang galat
Import-Csv results\20261106_mongodb_W2_S100.csv |
  Where-Object { [int]$_.kueri_id -le 20 -and $_.jumlah_hasil -ne '-1' } |
  Sort-Object { [double]$_.waktu_ms } -Descending |
  Select-Object -First 5 ulangan, kueri_id, waktu_ms, jumlah_hasil | Format-Table
```

```python
# Dengan Python + pandas (bila pandas terpasang)
import pandas as pd
df = pd.read_csv('results/20261106_mongodb_W2_S100.csv')
df = df[df['kueri_id'] <= 20]            # S100: hanya titik 1 sampai 20
print(df['waktu_ms'].describe())
```

---

## CARA 4: CEK UKURAN DISK DAN WAKTU (W7, W8)

### Berkas: `results/pengukuran_mongodb.csv`

Berisi ukuran fisik MongoDB di disk per skala, waktu indeks, waktu muat S100, dan waktu tambah batch.

**Kolom:** `tanggal`, `penyimpanan`, `skala`, `jenis`, `objek`, `nilai`, `satuan`, `catatan`

Nilai `jenis` yang ada:
- `jumlah_dokumen` — jumlah dokumen
- `ukuran_data_tak_terkompres` — ukuran data sebelum kompresi (MiB)
- `ukuran_data_di_disk` — ukuran data terkompresi di disk (MiB)
- `ukuran_indeks` — ukuran semua indeks (MiB)
- `ukuran_total` — data di disk + indeks (MiB)
- `indeks` — waktu membangun semua indeks (detik); tercatat untuk S10 dan S100 (S1 tidak tercatat)
- `muat` — waktu muat massal (detik); hanya S100, `objek` = `annotations+patches`, dicatat 25 Nov 2026
- `tambah_batch` — W8: waktu menambah satu batch ke S100 (detik)

`objek` berisi `annotations`, `patches`, atau `semua`.

**Cara baca:**
```powershell
Import-Csv results\pengukuran_mongodb.csv |
  Where-Object { $_.skala -eq 'S100' } |
  Format-Table -AutoSize
```

### Berkas: `results/pengukuran_postgis.csv`

Sama seperti di atas, untuk PostGIS. Nilai `jenis`:
- `ukuran_data_di_disk` — ukuran tabel (heap) (MiB)
- `ukuran_indeks` — ukuran indeks GiST dan B-Tree (MiB)
- `ukuran_total` — total termasuk TOAST, dari `pg_total_relation_size` (MiB)
- `indeks` — waktu membangun semua indeks (detik); tercatat untuk S10 dan S100 (S1 tidak tercatat)
- `muat` — waktu muat massal (detik); hanya S100, `objek` = `annotations+patches`, dicatat 25 Nov 2026
- `tambah_batch` — W8: waktu menambah satu batch ke S100 (detik), `annotations` + `patches`

### Berkas: `results/pengukuran_mentah.csv`

Ukuran berkas mentah (CSV dan NDJSON) per skala, sebagai referensi sebelum dimuat (`jenis` = `ukuran_total`).

### Angka total S100 (jumlahkan `annotations` dan `patches`)

| Penyimpanan | Perhitungan | Total |
|---|---|---|
| MongoDB | 1.832,418 + 29,539 MiB | 1.861,957 MiB (≈ 1,82 GiB) |
| PostGIS | 3.409,906 + 87,188 MiB | 3.497,094 MiB (≈ 3,42 GiB) |
| Parquet (HDFS) | 434,108 + 1,252 MiB (satu salinan, tanpa indeks) | 435,360 MiB (≈ 0,43 GiB) |

### Yang belum ada di `results/`

- W8 Spark (waktu tambah batch ke S100) belum tercatat. Ukuran Parquet sudah ada di `pengukuran_spark.csv` (diukur 22 Nov 2026 di laptop Wildan); angka lama "Parquet ≈ 470 MiB" diganti angka terukur 435,36 MiB.
- Waktu muat (`jenis` = `muat`) S1 dan S10, dan waktu indeks S1. Waktu muat dan waktu indeks S100 sudah tercatat 25 Nov 2026 (MongoDB 912,5 dan 242,4 detik; PostGIS 86,9 dan 46,9 detik; indeks MongoDB 5,2× lebih lama). Waktu MongoDB dicatat susulan dari keluaran terminal sesi pemuatan 7 Nov dan tidak diukur ulang; waktu PostGIS diukur ulang 25 Nov setelah S100 dimuat ulang. Waktu muat MongoDB memakai `muat_pymongo.py` (bukan `mongoimport`), jadi tidak setara dengan `COPY` pada PostGIS. Cara mencatat ada di docstring `bench\catat.py`.

---

## CARA 5: CEK HASIL EKSPERIMEN KHUSUS

### E1 — Efek Indeks (kueri tanpa indeks, S10)

Enam berkas ini berisi baris dengan `catatan` = `varian=tanpa-indeks`:
- `20261106_mongodb_W2_S10_2.csv`
- `20261106_mongodb_W3_S10_2.csv`
- `20261107_mongodb_W4_S10.csv`
- `20261107_postgis_W2_S10.csv`
- `20261107_postgis_W3_S10.csv`
- `20261107_postgis_W4_S10.csv`

Atau saring langsung dari `banding.csv`:
```powershell
Import-Csv results\banding.csv |
  Where-Object { $_.varian -eq 'tanpa-indeks' } |
  Format-Table -AutoSize
```

Bandingkan `median_ms_mongodb` di baris `tanpa-indeks` dengan baris normal (varian kosong) untuk beban dan skala yang sama.

### Cold Run — Efek Cache Dingin

Cold run disimpan satu ulangan per berkas. Pola waktunya menunjukkan **hanya ulangan 1 yang benar-benar dingin**: ulangan 2 dan 3 sering jauh lebih cepat (contoh PostGIS W3 S100: 11,586 ms lalu 2,414 dan 2,447 ms; sebabnya sebagian adalah peralihan ke rencana generik, lihat CARA 11). Baris `cold` di `ringkasan.csv` dan `banding.csv` menggabungkan ketiga ulangan, jadi lihat ulangan 1 dari berkas mentah:

```python
import glob
import pandas as pd

df = pd.concat(pd.read_csv(f) for f in glob.glob('results/2026*.csv'))
df = df[(df['skala'] != 'S100') | (df['kueri_id'] <= 20)]
dingin = df[(df['cold_warm'] == 'cold') & (df['ulangan'] == 1)]
print(dingin.groupby(['penyimpanan', 'beban_kerja', 'skala'])['waktu_ms'].median())
```

Hasil yang benar (ms): MongoDB W3 S10 4,000; W3 S100 16,062; W5 S10 1.176,506; W5 S100 4.486,238. PostGIS W3 S10 0,804; W3 S100 11,586; W5 S10 74,190; W5 S100 838,717.

Lima dari delapan rasio cold ÷ warm di bawah 1 (cold lebih cepat dari warm), termasuk keempat skenario PostGIS. Itu tidak masuk akal bila cold benar-benar dingin: **dugaan** restart container tidak mengosongkan cache sistem operasi di mesin virtual Docker, atau sesi warm terganggu. Median warm PostGIS W3 S100 (12,956 ms) paling dicurigai; penelusuran 25 Nov menunjukkan sebabnya, yaitu rencana generik (CARA 11). Untuk tiga skenario PostGIS lain dan MongoDB W5 S100 penjelasannya belum diperiksa. Rinciannya ada di `docs/penjelasan_lengkap.md` Bagian 7.5 dan 7.6.

### Multi-client — Efek Konkurensi

Median dari `banding.csv`:
```powershell
Import-Csv results\banding.csv |
  Where-Object { $_.beban_kerja -eq 'W1' -and $_.konkurensi -ne '' } |
  Format-Table -AutoSize
```

p95 dari `ringkasan.csv`:
```powershell
Import-Csv results\ringkasan.csv |
  Where-Object { $_.beban_kerja -eq 'W1' -and $_.skala -eq 'S100' -and $_.penyimpanan -ne 'spark' } |
  Select-Object penyimpanan, konkurensi, median_ms, p95_ms | Format-Table -AutoSize
```

Baris dengan `konkurensi` kosong adalah 1 klien. Klien adalah thread Python di laptop yang sama dengan server database.

---

## CARA 6: JALANKAN ULANG PEMBUAT RINGKASAN

Untuk membuat ulang `ringkasan.csv` dan `banding.csv` dari berkas mentah (dari akar repo):
```powershell
cd C:\proyek\kelompok2-bigdata-storage
python bench\summarize.py --titik-maks 20
```

`summarize.py` membaca berkas `results\*.csv` saja (tidak masuk ke `results\arsip\`, dan melewati `banding.csv` serta berkas berawalan `ringkasan` dan `pengukuran_`). `--titik-maks 20` membatasi S100 pada `kueri_id` 1 sampai 20; opsi `--titik-skala S100,S10` mengubah skala yang dibatasi.

Keluaran (dipotong). Tabel ringkasan dicetak lebih dulu, lalu baris penutup:
```
simpan    beban skala c/w   konk varian         ul  kueri  median_ms     ul_min    ul_maks     p95_ms galat
mongodb   W1    S1    warm     - -               3    300      1.503      0.984      2.752      3.417     0
...
Pembatasan titik: skala S100 hanya kueri_id 1 sampai 20 (--titik-maks).
Tertulis: results/ringkasan.csv (80 kelompok) dan results/banding.csv (34 baris), dari 96 berkas
```

Bila angkanya berbeda (misalnya "dari 111 berkas"), berkas 2 Nov belum dipindah ke `results\arsip\`.

---

## CARA 7: VERIFIKASI KEBENARAN ANGKA

### Langkah 1 — Bandingkan jumlah hasil antar penyimpanan

`compare_counts.py` membandingkan **jumlah hasil** tiap kueri (bukan isi barisnya), dari ulangan pertama di tiap berkas.

```powershell
# S1: tiga penyimpanan, otomatis dibandingkan juga dengan wasit (bench\benar\W2_S1.csv)
python bench\compare_counts.py results\20261106_mongodb_W2_S1.csv results\20261106_postgis_W2_S1.csv results\20261106_spark_W2_S1.csv

# S100: wasit belum ada, jadi --tanpa-wasit; titik 1 sampai 20
python bench\compare_counts.py --tanpa-wasit --titik-maks 20 results\20261106_mongodb_W2_S100.csv results\20261106_postgis_W2_S100.csv results\20261106_spark_W2_S100.csv
```

Keluaran normal (S1 W2):
```
Perbandingan W2 S1: mongodb vs postgis vs spark vs benar
Cocok: 100 dari 100 kueri.
Semua jumlah hasil sama.
```

Kode keluar 0 berarti cocok, 1 berarti ada yang beda. Satu selisih sudah diketahui: **S100 W2 titik 19** (MongoDB 1.401; PostGIS dan Spark 1.400), sehingga perintah S100 W2 di atas berakhir dengan "Cocok: 19 dari 20 kueri." dan kode keluar 1. Selisihnya satu anotasi yang berjarak sekitar 5 mm di luar tepi jendela; dugaannya toleransi sel S2 MongoDB di tepi jendela (belum dibuktikan). Selisih lain berarti ada yang salah.

Hasil perbandingan S10 dan S100 untuk W1 sampai W6 tersimpan di `results/uji_silang_S10_S100.txt`.

### Langkah 2 — Wasit jawaban benar (S1)

`bench\kebenaran.py` menghitung jawaban benar **langsung dari `data\out\s1\annotations.csv`**, tanpa database. Hasilnya dipakai `compare_counts.py` sebagai wasit. Wasit hanya ada untuk S1.

```powershell
python bench\kebenaran.py --skala S1            # hitung dan tampilkan
python bench\kebenaran.py --skala S1 --tulis    # tulis ulang bench\benar\W*_S1.csv
```

Butuh `data\out\s1\` (dibuat `python data\convert_inventory.py`).

### Langkah 3 — Jalankan uji tanpa Docker

```powershell
python tests\uji_semua.py
python tests\lint_dokumen.py
```

Harus tampil `SEMUA UJI LULUS (22 uji, 18 detik)` (jumlah detik berbeda tiap mesin) dan `18 berkas .md diperiksa, 0 masalah.` (jumlah berkas bisa bertambah).

---

## CARA 8: MEMBACA HASIL DI GITHUB

Semua hasil sudah di-push ke GitHub dan bisa dibaca di browser:

1. **Buka repositori:** `https://github.com/wildnrfm/kelompok2-bigdata-storage`

2. **Buka folder `results/`:**
   - Terlihat 96 berkas CSV hasil benchmark, ditambah `ringkasan.csv`, `banding.csv`, `ringkasan_explain.csv`, `pengukuran_*.csv`, berkas `explain_*.txt`, `uji_silang_S10_S100.txt`, dan folder `arsip/`
   - Klik `banding.csv`: GitHub menampilkannya sebagai tabel
   - Klik `ringkasan.csv`: idem

3. **Lihat riwayat commit untuk menelusuri kapan data masuk:**
   - Klik tab `Commits`
   - Commit penting: `054c609` — *"[results] tuntas seluruh benchmark resmi W1-W8 E1 E2 S1 S10 S100 Elsa"*

---

## CARA 9: ANGKA KUNCI UNTUK MENJAWAB PERTANYAAN

| Pertanyaan | Jawaban | Sumber |
|---|---|---|
| Tercepat untuk kueri jendela (W2 S100)? | **PostGIS 1,2 ms**; MongoDB 8,8 ms; Spark 546 ms (PostGIS ≈ 454× lebih cepat dari Spark) | `banding.csv` baris W2/S100/warm |
| Tercepat untuk kotak pembatas (W4 S100)? | **PostGIS 33,0 ms** vs MongoDB 640,0 ms (19,4× lebih cepat). p95 MongoDB 206 detik, hanya dari dua titik (3 dan 20); sebabnya planner memilih indeks `event_type` + tanggal, bukan `bbox_2dsphere` (CARA 11) | `banding.csv`, `ringkasan.csv` baris W4/S100 |
| Seberapa besar manfaat indeks? (E1, S10, W2) | MongoDB 1.119,7 → 2,46 ms (**455×**); PostGIS 213,9 → 0,91 ms (**235×**) | `banding.csv` baris W2/S10 |
| Paling hemat disk (S100)? | **Parquet 435,36 MiB < MongoDB 1.861,96 MiB < PostGIS 3.497,09 MiB** (Parquet 4,3× dan 8,0× lebih kecil; MongoDB 1,88× lebih kecil dari PostGIS; Parquet tanpa indeks, dua lainnya termasuk indeks) | `pengukuran_spark.csv`, `pengukuran_mongodb.csv`, `pengukuran_postgis.csv` |
| Kapan Spark lebih cepat dari MongoDB? | W5 S100: Spark 1.293 ms vs MongoDB 6.869 ms (5,3×), tetapi PostGIS (1.142 ms) lebih cepat dari Spark. Di W6 S100 MongoDB (131,7 ms) lebih cepat dari Spark (531,2 ms) | `banding.csv` baris W5/S100 dan W6/S100 |
| Stabil saat 50 klien serentak? | p95 50 klien ÷ p95 1 klien (titik 1 sampai 20): MongoDB 5,1×, PostGIS 8,2×, keduanya di bawah batas 10×. Pada 100 klien 10,7× dan 25,4×. Klien = thread Python di satu laptop | `ringkasan.csv` filter W1/S100/warm |
| Apakah jumlah hasil sama di ketiganya? | Ya, kecuali satu kueri: S100 W2 titik 19 (MongoDB 1.401; lainnya 1.400) | `results/uji_silang_S10_S100.txt` |
| Hipotesis mana yang diterima? | H1 sebagian, H2 diterima, H3 ditolak sebagian (Parquet paling kecil sesuai dugaan, tetapi urutan MongoDB dan PostGIS terbalik), H4 sebagian, H5 diterima dengan catatan | `docs/penjelasan_lengkap.md` Bagian 8 |
| Total yang diuji? | 96 berkas CSV (31.026 baris; 30.066 dipakai di ringkasan), 80 grup, 0 galat | `ringkasan.csv` kolom `galat_n` |
| Mengapa median PostGIS W3 S100 (13,0 ms) lebih lambat dari MongoDB? | Rencana generik: pada `EXPLAIN` median 13,204 ms (generik) lawan 0,356 ms (kustom), 37,1× lebih lambat; pada harness dengan rencana kustom median W3 S100 = 0,79 ms | `ringkasan_explain.csv`, `banding.csv` baris varian |
| Mengapa p95 MongoDB W4 S100 setinggi 206 detik? | Titik 3, 20, dan 19: planner memilih `event_type_1_dates.event_1` (5,3 juta kunci, titik 19: 1,0 juta); dengan `hint("bbox_2dsphere")` 170,0 → 0,94 detik (titik 3), 190,3 → 1,20 (titik 20), 22,2 → 3,6 (titik 19). Median W4 S100 tidak berubah | `ringkasan_explain.csv` |

---

## CARA 10: CEK HASIL TAHAP 3 (PEMROSESAN DAN ANALITIK)

Tahap 3 memproses katalog dengan Spark (ETL, 14 kueri, ekspor) dan mengukur waktunya di S1, S10, dan S100. Hasilnya ada di `results/analitik/`, terpisah dari hasil benchmark di Cara 1 sampai 9. Pengukurannya dijalankan di laptop Wildan (bukan laptop uji Elsa), jadi angkanya tidak dibandingkan langsung dengan latensi MongoDB dan PostGIS.

### Isi `results/analitik/`

| Yang dicari | Berkas/folder |
|---|---|
| 14 tabel hasil analitik per skala (nama berkas = nama kueri, misalnya `q0_hitung.csv`) | `results/analitik/S1/`, `S10/`, `S100/` |
| Waktu mentah tiap tahap (221 baris: 13 putaran kali 17 tahap) | `results/analitik/waktu_pemrosesan.csv` |
| Ringkasan waktu per skala (median warm, cold, anotasi per detik) | `results/analitik/ringkasan_waktu.csv` |
| Waktu per tahap (cold dan median warm) | `results/analitik/waktu_per_tahap.csv` |
| Grafik G1 sampai G6 (PNG) | `results/analitik/grafik/` |
| Jawaban benar (acuan mandiri) per skala | `analitik/referensi_S1/`, `analitik/referensi_S10/`, `analitik/referensi_S100/` |

### Langkah 1 — Lihat ringkasan waktu

```powershell
Import-Csv results\analitik\ringkasan_waktu.csv | Format-Table skala,n_anotasi,n_putaran,total_ms,total_cold_ms,anotasi_per_detik,rasio_waktu_vs_S1
```

Harus tampil tiga baris. `total_ms` adalah median putaran warm: S1 22.317,4; S10 34.535,4; S100 128.814,5 (milidetik). `total_cold_ms` adalah putaran cold: 51.986,8; 53.395,1; 181.303,9. S1 dan S10 memiliki 4 putaran warm, S100 hanya 2.

### Langkah 2 — Cocokkan hasil Spark dengan acuan (tanpa Docker)

```powershell
python analitik\cocokkan.py
python analitik\cocokkan.py --hasil results\analitik\S10
python analitik\cocokkan.py --hasil results\analitik\S100
```

Ketiganya harus berakhir `SEMUA TABEL COCOK`: 14 tabel, 1.130 sel pada S1 dan 1.418 sel pada S10 maupun S100 (toleransi relatif 1e-9). Perintah ini membandingkan CSV hasil Spark yang sudah di-commit dengan acuan di `analitik/referensi_S*`, sehingga tidak butuh Docker. Bila muncul `ADA SELISIH`, jangan mengubah angka; tanyakan ke Wildan.

### Langkah 3 — Angka kunci Tahap 3

| Pertanyaan | Jawaban | Sumber |
|---|---|---|
| Berapa lama satu putaran pipeline? (median warm) | S1 22,3 detik; S10 34,5; S100 128,8. Data bertambah 100 kali, waktu 5,8 kali | `ringkasan_waktu.csv` |
| Apakah Spark menghitung dengan benar? | Ya: 14 tabel cocok dengan acuan mandiri pada S1, S10, dan S100 | `analitik\cocokkan.py` |
| Tahap terberat di S100? | ETL 38,0 detik (29,5%); `q2_pemeriksaan` 22,8 (17,7%); `q1_kolom_kosong` 17,1 (13,3%); `a4a_area_jenis` 13,1 (10,1%) | `waktu_per_tahap.csv` |
| Seberapa terkonsentrasi isi katalog? (S1) | Italy 63,4% anotasi, seluruhnya pada 16 Mei 2023; 9 dari 16 lokasi hanya punya satu tanggal kejadian | `S1/a3_lokasi.csv`, `S1/a3b_lokasi_tanggal.csv` |
| Bagaimana kualitas data? (S1) | 11 dari 13 pemeriksaan bersih; 3.142 anotasi (4,2%) tanpa jenis pemicu; 109 (0,15%) tanpa tanggal | `S1/q2_pemeriksaan.csv`, `S1/q1_kolom_kosong.csv` |

Isi katalog hanya bermakna di S1: S10 dan S100 adalah salinan simulasi untuk menguji waktu. Penjelasan lengkap ada di `docs/penjelasan_lengkap.md` Bagian 13 dan `analitik/README.md`.

---

## CARA 11: CEK PENELUSURAN RENCANA KUERI (25 NOV 2026)

Dua angka pada seri utama tampak janggal: median W3 S100 PostGIS (12,956 ms) dan ekor p95 W4 S100 MongoDB (206.458 ms). Keduanya ditelusuri dengan `EXPLAIN` pada 25 Nov 2026 di laptop uji (laptop Elsa). Seri utama tidak diubah; hasil penelusuran ada di berkas terpisah. Penjelasan lengkap: `docs/penjelasan_lengkap.md` Bagian 7.6 dan subbab 3.2.1 laporan.

### Isi `results/` untuk penelusuran ini

| Yang dicari | Berkas |
|---|---|
| `EXPLAIN (ANALYZE, BUFFERS)` W3 S100 PostGIS, 15 titik, dua kali tiap rencana (kustom dan generik) | `results/explain_postgis_W3_S100_ann<ID>.txt` (ID = `ann_id` titik; nomor titik ada di `bench/points.json`) |
| Keadaan server saat `EXPLAIN` PostGIS dijalankan | `results/explain_postgis_W3_S100_keadaan.txt` |
| `explain("executionStats")` W4 S100 MongoDB, 7 titik (rencana bawaan, rencana dengan `hint`, `countDocuments`) | `results/explain_mongodb_W4_S100_ann<ID>.txt` |
| Putar ulang urutan harness MongoDB (titik 1, 2, 3 dan plan cache) | `results/explain_mongodb_W4_S100_urutan_harness.txt` |
| Pengulangan harness PostGIS W2, W3, W4 S100 (bawaan dan rencana kustom) | `results/20261125_postgis_W*_S100*.csv` (enam berkas; kolom `catatan` = `varian=bawaan` atau `varian=custom-plan`) |
| Ringkasan semua `EXPLAIN` dan `explain` (81 baris) | `results/ringkasan_explain.csv` (dibuat oleh `bench/ringkas_explain.py`) |

### Langkah 1 — Buat ulang ringkasan EXPLAIN

```powershell
python bench\ringkas_explain.py
```

Tidak butuh Docker. Skrip membaca `results\explain_*.txt` dan `bench\points.json`, mencetak tiga tabel (PostGIS, MongoDB, urutan harness), dan menulis `results\ringkasan_explain.csv` (81 baris). Yang harus tampil:

- PostGIS: median eksekusi kedua 0,356 ms (rencana kustom) dan 13,204 ms (rencana generik), rasio 37,1× (15 titik). Pada rencana generik indeks tanggal diperkirakan menghasilkan 37.477 baris, padahal aktualnya median 162.381 entri (8.496 sampai 439.265).
- MongoDB: titik 3, 20, dan 19 memakai `event_type_1_dates.event_1` pada rencana bawaan; dengan `hint` waktunya 0,94; 1,20; dan 3,6 detik (bawaan 170,0; 190,3; 22,2 detik).

### Langkah 2 — Lihat varian rencana di banding.csv

```powershell
Import-Csv results\banding.csv |
  Where-Object { $_.varian -in 'bawaan','custom-plan' } |
  Format-Table beban_kerja,skala,varian,median_ms_postgis
```

Harus tampil enam baris (median PostGIS, ms): W2 bawaan 1,408 dan custom-plan 0,731; W3 bawaan 9,058 dan custom-plan 0,791; W4 bawaan 11,495 dan custom-plan 17,239. Seri utama (kolom `varian` kosong): W2 1,202, W3 12,956, W4 32,973.

### Langkah 3 — Cara membaca

- Rencana kustom menurunkan W3 S100 11,5× dan W2 S100 1,9×, tetapi W4 S100 justru 1,5× lebih lambat (sebabnya belum diperiksa dengan `EXPLAIN`).
- Hasil 25 Nov berasal dari sesi dan keadaan sistem yang berbeda dari seri utama (S100 PostGIS dimuat ulang; `explain` MongoDB dijalankan pada koleksi setelah batch W8, 7.570.556 dokumen). Median W4 bawaan sesi itu 2,9× lebih rendah dari seri utama, jadi bandingkan hanya dalam orde besaran.
- `hint` MongoDB hanya diuji pada tujuh titik W4. Median W4 S100 (640 ms) tidak berubah olehnya; yang berubah hanya ekor p95.

---

## RINGKASAN LOKASI FILE HASIL

| Yang dicari | Berkas/folder | Cara buka |
|---|---|---|
| Perbandingan langsung 3 penyimpanan | `results/banding.csv` | Excel / `Import-Csv ... \| Format-Table` |
| Statistik lengkap per grup | `results/ringkasan.csv` | Excel / `Import-Csv ...` |
| Latensi per kueri (mentah) | `results/20261106_*.csv`, `results/20261107_*.csv`, dan `results/20261125_*.csv` | `Get-Content` / pandas |
| Berkas 2 Nov (tidak dihitung) | `results/arsip/` | `Get-ChildItem` |
| Ukuran disk MongoDB | `results/pengukuran_mongodb.csv` | Excel |
| Ukuran disk PostGIS | `results/pengukuran_postgis.csv` | Excel |
| Ukuran berkas mentah | `results/pengukuran_mentah.csv` | Excel |
| Ringkasan EXPLAIN dan explain (penelusuran rencana kueri) | `results/ringkasan_explain.csv` | Excel / `python bench\ringkas_explain.py` |
| Keluaran EXPLAIN dan explain mentah | `results/explain_*.txt` | Notepad |
| Uji silang jumlah hasil S10 dan S100 | `results/uji_silang_S10_S100.txt` | Notepad |
| Jawaban benar (wasit, hanya S1) | `bench/benar/W1_S1.csv` sampai `W6_S1.csv` | Excel |
| Titik koordinat uji | `bench/points.json` | Notepad / `python -c "import json; ..."` |
| Hash integritas data | `data/CHECKSUMS.txt` | Notepad |
| Hasil Tahap 3 (14 CSV per skala) | `results/analitik/S1/`, `S10/`, `S100/` | Excel |
| Waktu pemrosesan Tahap 3 | `results/analitik/ringkasan_waktu.csv` | Excel / `Import-Csv ...` |
| Grafik Tahap 3 | `results/analitik/grafik/g1_tahun_jenis.png` sampai `g6_waktu.png` | Pratinjau gambar |
