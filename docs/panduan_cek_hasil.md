# PANDUAN CARA CEK HASIL BENCHMARK
## Kelompok 2 — Big Data Storage (Kelas B)

**Anggota Tim:**
1. **Muhammad Wildan Arif Maulana** (23051204065) — *Project Lead, Documentation & QA*
2. **Maulana Hidayah Syaif Ali Khan** (23051204068) — *Data Collection & Conversion Engineer*
3. **Elsa Claudia Putri** (23051204038) — *Storage Engineer A (MongoDB Specialist & Benchmark Lead)*
4. **Muhammad Syah Levi** (23051204051) — *Storage Engineer B (PostGIS & HDFS-Spark Specialist)*
5. **Marsanda Sofi Aminarti** (23051204066) — *Performance Analyst & Validation Lead*

> Repositori: `https://github.com/wildnrfm/kelompok2-bigdata-storage`

> **Catatan revisi (12 Nov 2026).** Panduan ini disamakan dengan isi repo: nama kolom berkas mentah, jumlah berkas (90, bukan 111), perintah `compare_counts.py` dan `kebenaran.py`, dan angka kunci. Ringkasan dibuat dengan `python bench\summarize.py --titik-maks 20`. Hal yang belum terbukti ditulis sebagai **dugaan**, dan hal yang belum diukur ditulis **belum terukur**.

---

## CARA 1: BUKA RINGKASAN UTAMA (PALING CEPAT)

### Berkas: `results/ringkasan.csv`

Ini **satu berkas terpenting**: tabel ringkasan semua hasil benchmark. Setiap baris mewakili satu kombinasi unik: satu penyimpanan × satu beban kerja × satu skala × satu kondisi. Isinya 74 grup, dihitung dari 90 berkas hasil tanggal 6 dan 7 Nov. Berkas 2 Nov ada di `results/arsip/` dan tidak ikut dihitung.

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
| `varian` | `tanpa-indeks` untuk E1; kosong = normal |
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

Berkas ini menampilkan **tiga penyimpanan berdampingan** untuk skenario yang sama (28 baris). Ini yang paling mudah dibaca untuk menjawab "siapa paling cepat di kondisi X?".

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
| `varian` | Kosong (normal) atau `tanpa-indeks` |
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

**Ringkasan 18 skenario utama** (6 beban × 3 skala, warm, tanpa varian): PostGIS tercepat pada 15; MongoDB tercepat pada W3 S100, W6 S1, dan W6 S10; Spark tidak pernah tercepat.

---

## CARA 3: CEK HASIL MENTAH PER KUERI

### Folder: `results/*.csv` (90 berkas)

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

Berisi ukuran fisik MongoDB di disk per skala, waktu indeks, dan waktu tambah batch.

**Kolom:** `tanggal`, `penyimpanan`, `skala`, `jenis`, `objek`, `nilai`, `satuan`, `catatan`

Nilai `jenis` yang ada:
- `jumlah_dokumen` — jumlah dokumen
- `ukuran_data_tak_terkompres` — ukuran data sebelum kompresi (MiB)
- `ukuran_data_di_disk` — ukuran data terkompresi di disk (MiB)
- `ukuran_indeks` — ukuran semua indeks (MiB)
- `ukuran_total` — data di disk + indeks (MiB)
- `indeks` — waktu membangun semua indeks (detik); hanya tercatat untuk S10
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
- `indeks` — waktu membangun semua indeks (detik); hanya tercatat untuk S10
- `tambah_batch` — W8: waktu menambah satu batch ke S100 (detik), `annotations` + `patches`

### Berkas: `results/pengukuran_mentah.csv`

Ukuran berkas mentah (CSV dan NDJSON) per skala, sebagai referensi sebelum dimuat (`jenis` = `ukuran_total`).

### Angka total S100 (jumlahkan `annotations` dan `patches`)

| Penyimpanan | Perhitungan | Total |
|---|---|---|
| MongoDB | 1.832,418 + 29,539 MiB | 1.861,957 MiB (≈ 1,82 GiB) |
| PostGIS | 3.409,906 + 87,188 MiB | 3.497,094 MiB (≈ 3,42 GiB) |
| Parquet (HDFS) | — | **belum terukur** |

### Yang belum ada di `results/`

- `pengukuran_spark.csv`: ukuran Parquet di HDFS dan W8 Spark. Angka "Parquet ≈ 470 MiB" yang pernah beredar **belum punya berkas ukur**. Ukur dengan `python bench\catat.py ukuran --store spark --skala S100` (butuh HDFS jalan).
- Waktu muat (`jenis` = `muat`) untuk semua penyimpanan, dan waktu indeks S100. Cara mencatat ada di docstring `bench\catat.py`.

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

Cold run disimpan satu ulangan per berkas. Pola waktunya menunjukkan **hanya ulangan 1 yang benar-benar dingin**: ulangan 2 dan 3 sering jauh lebih cepat (contoh PostGIS W3 S100: 11,586 ms lalu 2,414 dan 2,447 ms). Baris `cold` di `ringkasan.csv` dan `banding.csv` menggabungkan ketiga ulangan, jadi lihat ulangan 1 dari berkas mentah:

```python
import glob
import pandas as pd

df = pd.concat(pd.read_csv(f) for f in glob.glob('results/2026*.csv'))
df = df[(df['skala'] != 'S100') | (df['kueri_id'] <= 20)]
dingin = df[(df['cold_warm'] == 'cold') & (df['ulangan'] == 1)]
print(dingin.groupby(['penyimpanan', 'beban_kerja', 'skala'])['waktu_ms'].median())
```

Hasil yang benar (ms): MongoDB W3 S10 4,000; W3 S100 16,062; W5 S10 1.176,506; W5 S100 4.486,238. PostGIS W3 S10 0,804; W3 S100 11,586; W5 S10 74,190; W5 S100 838,717.

Lima dari delapan rasio cold ÷ warm di bawah 1 (cold lebih cepat dari warm), termasuk keempat skenario PostGIS. Itu tidak masuk akal bila cold benar-benar dingin: **dugaan** restart container tidak mengosongkan cache sistem operasi di mesin virtual Docker, atau sesi warm terganggu. Median warm PostGIS W3 S100 (12,956 ms) paling dicurigai dan perlu diukur ulang. Rinciannya ada di `docs/penjelasan_lengkap.md` Bagian 7.5.

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

`summarize.py` membaca berkas `results\*.csv` saja (tidak masuk ke `results\arsip\`). `--titik-maks 20` membatasi S100 pada `kueri_id` 1 sampai 20; opsi `--titik-skala S100,S10` mengubah skala yang dibatasi.

Keluaran (dipotong). Tabel ringkasan dicetak lebih dulu, lalu baris penutup:
```
simpan    beban skala c/w   konk varian         ul  kueri  median_ms     ul_min    ul_maks     p95_ms galat
mongodb   W1    S1    warm     - -               3    300      1.503      0.984      2.752      3.417     0
...
Pembatasan titik: skala S100 hanya kueri_id 1 sampai 20 (--titik-maks).
Tertulis: results/ringkasan.csv (74 kelompok) dan results/banding.csv (28 baris), dari 90 berkas
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

Harus tampil `SEMUA UJI LULUS (17 uji, 13 detik)` (jumlah detik berbeda tiap mesin) dan `17 berkas .md diperiksa, 0 masalah.` (jumlah berkas bisa bertambah).

---

## CARA 8: MEMBACA HASIL DI GITHUB

Semua hasil sudah di-push ke GitHub dan bisa dibaca di browser:

1. **Buka repositori:** `https://github.com/wildnrfm/kelompok2-bigdata-storage`

2. **Buka folder `results/`:**
   - Terlihat 90 berkas CSV hasil benchmark, ditambah `ringkasan.csv`, `banding.csv`, `pengukuran_*.csv`, `uji_silang_S10_S100.txt`, dan folder `arsip/`
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
| Tercepat untuk kotak pembatas (W4 S100)? | **PostGIS 33,0 ms** vs MongoDB 640,0 ms (19,4× lebih cepat). p95 MongoDB 206 detik, hanya dari dua titik (3 dan 20) | `banding.csv`, `ringkasan.csv` baris W4/S100 |
| Seberapa besar manfaat indeks? (E1, S10, W2) | MongoDB 1.119,7 → 2,46 ms (**455×**); PostGIS 213,9 → 0,91 ms (**235×**) | `banding.csv` baris W2/S10 |
| Paling hemat disk (S100)? | **MongoDB 1.861,96 MiB < PostGIS 3.497,09 MiB** (1,88×). Parquet ≈ 470 MiB **belum terukur** | `pengukuran_mongodb.csv`, `pengukuran_postgis.csv` |
| Kapan Spark lebih cepat dari MongoDB? | W5 S100: Spark 1.293 ms vs MongoDB 6.869 ms (5,3×), tetapi PostGIS (1.142 ms) lebih cepat dari Spark. Di W6 S100 MongoDB (131,7 ms) lebih cepat dari Spark (531,2 ms) | `banding.csv` baris W5/S100 dan W6/S100 |
| Stabil saat 50 klien serentak? | p95 50 klien ÷ p95 1 klien (titik 1 sampai 20): MongoDB 5,1×, PostGIS 8,2×, keduanya di bawah batas 10×. Pada 100 klien 10,7× dan 25,4×. Klien = thread Python di satu laptop | `ringkasan.csv` filter W1/S100/warm |
| Apakah jumlah hasil sama di ketiganya? | Ya, kecuali satu kueri: S100 W2 titik 19 (MongoDB 1.401; lainnya 1.400) | `results/uji_silang_S10_S100.txt` |
| Hipotesis mana yang diterima? | H1 sebagian, H2 diterima, H3 ditolak sebagian (urutan MongoDB dan PostGIS terbalik; Parquet belum terukur), H4 sebagian, H5 diterima dengan catatan | `docs/penjelasan_lengkap.md` Bagian 8 |
| Total yang diuji? | 90 berkas CSV (30.666 baris; 29.706 dipakai di ringkasan), 74 grup, 0 galat | `ringkasan.csv` kolom `galat_n` |

---

## RINGKASAN LOKASI FILE HASIL

| Yang dicari | Berkas/folder | Cara buka |
|---|---|---|
| Perbandingan langsung 3 penyimpanan | `results/banding.csv` | Excel / `Import-Csv ... \| Format-Table` |
| Statistik lengkap per grup | `results/ringkasan.csv` | Excel / `Import-Csv ...` |
| Latensi per kueri (mentah) | `results/20261106_*.csv` dan `results/20261107_*.csv` | `Get-Content` / pandas |
| Berkas 2 Nov (tidak dihitung) | `results/arsip/` | `Get-ChildItem` |
| Ukuran disk MongoDB | `results/pengukuran_mongodb.csv` | Excel |
| Ukuran disk PostGIS | `results/pengukuran_postgis.csv` | Excel |
| Ukuran berkas mentah | `results/pengukuran_mentah.csv` | Excel |
| Uji silang jumlah hasil S10 dan S100 | `results/uji_silang_S10_S100.txt` | Notepad |
| Jawaban benar (wasit, hanya S1) | `bench/benar/W1_S1.csv` sampai `W6_S1.csv` | Excel |
| Titik koordinat uji | `bench/points.json` | Notepad / `python -c "import json; ..."` |
| Hash integritas data | `data/CHECKSUMS.txt` | Notepad |
