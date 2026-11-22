# Tahap 3: pemrosesan dan analitik (Spark)

Pemilik: Wildan. Melanjutkan tahap penyimpanan. Setelah katalog Sen12Landslides termuat di MongoDB, PostGIS, dan HDFS + Parquet, tahap ini **memproses dan menganalisis isinya** dengan Spark SQL atas Parquet di HDFS, lalu **mengukur waktu pemrosesannya** di S1, S10, dan S100.

> Asumsi: tambahan dosen dibaca sebagai "pipeline pemrosesan dan analitik atas data yang sudah disimpan". Bila bunyi persyaratan aslinya berbeda (misalnya diminta model prediktif), cocokkan dulu dengan bagian 2 sebelum menulis laporan.

## 1. Yang dikerjakan

Satu **putaran** pipeline (`analitik/spark_pipeline.py`) terdiri dari tiga tahap, dan waktu tiap tahap dicatat:

1. **ETL.** Kueri `SQL_PERKAYA` mengubah Parquet mentah menjadi tabel turunan `ann_kaya`: jenis kejadian, tahun, bulan, belahan bumi, selang hari citra sebelum dan sesudah kejadian, dekade luas, dan sel 0,1 derajat. Tabel itu **ditulis ke HDFS** (`hdfs://namenode:8020/data/sen12ls/analitik/<skala>/annotations_kaya`) lalu dibaca lagi dan jumlah barisnya dicocokkan. Foldernya terpisah dari Parquet mentah supaya ukuran di disk pada tahap penyimpanan tidak tercemar.
2. **Analitik.** 14 kueri Spark SQL atas `ann_kaya` dan `patches` (bagian 4).
3. **Ekspor.** Tiap hasil ditulis sebagai CSV di `results/analitik/<SKALA>/`.

`--ulangan N` mengulang putaran penuh dalam satu sesi Spark: ulangan 1 berlabel **cold** (JVM baru), sisanya **warm**.

## 2. Batas yang ikut ditulis di laporan

- **Hanya metadata katalog** (74.956 anotasi dan 4.392 patch), bukan citra. Jadi ini analisis isi katalog, bukan deteksi longsor dari citra.
- **Tidak ada model prediktif.** Jumlah anotasi per lokasi mengikuti usaha pemetaan inventaris dan peristiwa pemicu tunggal (Italy 16 Mei 2023 saja 63,4% data), bukan frekuensi longsor sebenarnya. Model yang dilatih dari tabel ini akan mempelajari cara data dikumpulkan; citra, yang menjadi fitur sebenarnya untuk deteksi, juga tidak kita simpan.
- **S10 dan S100 adalah salinan simulasi** (koordinat dan tanggal digeser). Analisis isi (tabel a1 sampai a8) hanya bermakna di **S1**. Di S10 dan S100 yang diuji adalah waktu pemrosesan dan konsistensi: bagian data nyata (`sim_batch = 0`) harus menghasilkan tabel yang sama persis dengan S1 (`--hanya-asli`).
- **Satuan `area` tidak dideklarasikan oleh sumber.** Tulis "luas (satuan menurut sumber)", jangan menyebut meter persegi atau hektare.
- **Status pembuktian.** Ketiga skala sudah dijalankan di **Spark 3.5.0 sungguhan** pada laptop Wildan, sesi resmi 19 November 2026 (S1 pukul 20.02, S10 pukul 20.11, S100 pukul 20.17 WIB). Pada ketiganya 14 tabel cocok dengan acuan, toleransi relatif 1e-9: 1.130 sel pada S1, dan 1.418 sel pada S10 maupun S100. Di luar itu, kode diuji tanpa Docker: 14 kueri dijalankan di SQLite dan sama dengan acuan Python mandiri (pada S1 juga dengan perhitungan pandas), dan alur kode lewat Spark tiruan di `tests/stubs`.
- **Mesin ukur.** Waktu pemrosesan diukur pada laptop Wildan (Lenovo 20JTS1PK00, Intel i5-6200U 2 inti, WSL2 `memory=6GB processors=2`), **bukan** laptop uji Elsa yang dipakai pada tahap penyimpanan. Karena itu angkanya tidak dibandingkan langsung dengan latensi MongoDB dan PostGIS pada laporan Bab III.

## 3. Isi folder

| Berkas | Fungsi |
|---|---|
| `analitik/spark_pipeline.py` | Pipeline Spark (ETL, 14 kueri, ekspor CSV, pencatat waktu). Berjalan **di dalam kontainer** `sen12ls-spark`; hanya `pyspark` dan Python bawaan. |
| `analitik/kueri_analitik.py` | Definisi SQL 14 kueri, skema kolom, dan penulis CSV. Satu sumber kebenaran: dipakai pipeline, uji, dan acuan. |
| `analitik/fungsi_spark.py` | Fungsi Spark SQL yang ditiru di SQLite untuk uji (`year`, `month`, `datediff`, `log10`, `floor`, `percentile`). |
| `analitik/referensi.py` | Penghitung acuan mandiri: Python murni, satu lintasan atas CSV, tanpa SQL. |
| `analitik/referensi_S1/`, `analitik/referensi_S10/`, `analitik/referensi_S100/` | 14 CSV jawaban benar per skala (hasil `referensi.py`, di-commit). Data S10 dan S100 identik dengan `data/CHECKSUMS.txt`. Untuk S10 dan S100 ini memeriksa **perhitungan** Spark atas data simulasi, bukan isi ilmiahnya. |
| `analitik/cocokkan.py` | Membandingkan folder hasil Spark dengan acuan (toleransi relatif 1e-9). |
| `analitik/uji_sql.py` | Menjalankan 14 SQL di SQLite lalu membandingkannya dengan acuan. |
| `analitik/ringkas_waktu.py` | Merangkum `waktu_pemrosesan.csv` per skala (median warm, cold, anotasi per detik, rasio terhadap S1). |
| `analitik/grafik.py` | Membuat grafik G1 sampai G6 (PNG). Butuh `matplotlib`. |

## 4. Empat belas tabel hasil

| Tabel (CSV) | Pertanyaan yang dijawab |
|---|---|
| `q0_hitung` | Berapa anotasi, patch, lokasi, inventaris, jenis kejadian, dan penulis? |
| `q1_kolom_kosong` | Berapa sel kosong di tiap kolom? |
| `q2_pemeriksaan` | Dari 13 pemeriksaan kualitas (ID ganda, koordinat di luar rentang, luas nol atau negatif, kotak pembatas terbalik, urutan tanggal salah, dan seterusnya), berapa baris yang melanggar? |
| `a1_tahun_jenis` | Berapa anotasi per tahun kejadian dan jenis kejadian? |
| `a2_bulan_hemisfer` | Adakah pola bulanan di tiap belahan bumi? |
| `a3_lokasi` | Ringkasan per lokasi: inventaris, jenis, rentang tahun, median luas, rata-rata confidence. |
| `a3b_lokasi_tanggal` | Berapa tanggal kejadian berbeda per lokasi, dan seberapa terpusat pada satu hari? |
| `a4a_area_jenis` | Kuantil luas per jenis kejadian. |
| `a4b_area_dekade` | Sebaran luas per dekade log10. |
| `a5a_sel_terpadat` | 20 sel 0,1 derajat dengan anotasi terbanyak. |
| `a5b_sel_ringkas` | Ringkasan kepadatan per sel (median, persentil 95, maksimum). |
| `a6_patch_inventaris` | Patch per inventaris dan pembagian train, val, test. |
| `a7_waktu_kualitas` | Selang hari citra sebelum dan sesudah kejadian, serta confidence, per jenis. |
| `a8_hari_terpadat` | 15 hari kejadian dengan anotasi terbanyak. |

## 5. Menjalankan

Pengukuran waktu resmi tahap ini dilakukan di **laptop Wildan** (lihat bagian 2); sesi resminya sudah selesai pada 19 November 2026 dan hasilnya sudah ada di `results/analitik/`. Langkah di bawah dipakai bila ingin mengulang atau memeriksa. Untuk percobaan di laptop lain, ikuti catatan di akhir bagian ini supaya hasilnya tidak bercampur dengan pengukuran resmi. Semua perintah dari akar repo (`C:\proyek\kelompok2-bigdata-storage`), PowerShell. Perintah `docker exec ... spark-submit` ditulis **dalam satu baris**.

**Langkah 1. Perbarui kode dan uji tanpa Docker.**

```powershell
git pull --rebase
python tests\uji_semua.py
```

Harus berakhir `SEMUA UJI LULUS`.

**Langkah 2. Hidupkan HDFS dan Spark, pasang folder analitik.** Matikan MongoDB dan PostGIS dulu bila menyala (`docker compose stop` di foldernya).

```powershell
cd hdfs-parquet
docker compose up -d
docker exec sen12ls-spark ls /analitik
cd ..
```

`ls` harus menampilkan `spark_pipeline.py`, `kueri_analitik.py`, dan kawan-kawannya. Tunggu 30 sampai 60 detik, lalu pastikan **kedua** DataNode sudah terdaftar di NameNode. Jawaban `Safe mode is OFF` saja belum cukup: pernah NameNode sudah siap tetapi DataNode belum mendaftar, sehingga HDFS tampak sehat padahal tidak bisa menyimpan data.

```powershell
docker exec sen12ls-namenode hdfs dfsadmin -report | Select-String "Live datanodes"
```

Harus tercetak `Live datanodes (2)`. Bila setelah dua menit masih `(0)` atau `(1)`, lihat bagian 8. **Jangan `docker compose down`** kecuali sudah siap memuat ulang semua Parquet: HDFS tidak punya volume bernama, datanya ikut hilang (`docker compose stop` aman). Cek Parquet tersedia:

```powershell
docker exec sen12ls-namenode hdfs dfs -ls /data/sen12ls/parquet
```

Harus ada `s1`, `s10`, dan `s100`. Bila ada yang belum ada (HDFS baru, atau pernah di-`down`), buat datanya lalu muat ke HDFS; skrip pemuat mencocokkan jumlah baris sendiri dan mencetak `OK`:

```powershell
python data\convert_inventory.py
python data\generate_scales.py --all
python data\generate_scales.py --verify
docker exec sen12ls-spark /opt/spark/bin/spark-submit --master "local[2]" --driver-memory 2g /hdfs-parquet/csv_to_parquet.py --scale S1
docker exec sen12ls-spark /opt/spark/bin/spark-submit --master "local[2]" --driver-memory 2g /hdfs-parquet/csv_to_parquet.py --scale S10
docker exec sen12ls-spark /opt/spark/bin/spark-submit --master "local[2]" --driver-memory 2g /hdfs-parquet/csv_to_parquet.py --scale S100
```

`generate_scales.py --all` membuat S10 dan S100 (S100 beberapa menit). Bila `data\out\s10` dan `data\out\s100` sudah ada, lewati `--all` dan cukup jalankan `--verify`; semua barisnya harus `COCOK`. Pada sesi resmi, memuat S1, S10, dan S100 ke HDFS memerlukan kira-kira 27 detik, 42 detik, dan 4 menit.

**Langkah 3. Jalankan S1 (lima putaran, sekitar 3 menit).** Satu putaran cold dan empat warm: dengan hanya dua putaran warm, median sama dengan rata-rata dua angka yang berisik.

```powershell
docker exec sen12ls-spark /opt/spark/bin/spark-submit --master "local[2]" --driver-memory 2g /analitik/spark_pipeline.py --skala S1 --ulangan 5
```

Harus tercetak `Data mentah S1: annotations 74956, patches 4392`. Hasil: 14 CSV di `results/analitik/S1/` dan baris waktu di `results/analitik/waktu_pemrosesan.csv`.

**Langkah 4. Cocokkan dengan acuan.**

```powershell
python analitik\cocokkan.py
```

Harus berakhir `SEMUA TABEL COCOK`. Bila `ADA SELISIH`, kirim seluruh keluarannya ke Wildan; jangan membetulkan angka dengan tangan.

**Langkah 5. Skala besar.** Jalankan S10 dulu (lima putaran, sekitar 3 sampai 4 menit); bila beres, lanjut S100 sebagai langkah terpisah (tiga putaran, sekitar 8 menit pada sesi resmi; bisa jauh lebih lama di mesin yang lebih lemah).

```powershell
docker exec sen12ls-spark /opt/spark/bin/spark-submit --master "local[2]" --driver-memory 2g /analitik/spark_pipeline.py --skala S10 --ulangan 5
python analitik\cocokkan.py --hasil results\analitik\S10
```

Jumlah baris yang harus tercetak: `749560` anotasi dan `43920` patch. Hasilnya harus berakhir `SEMUA TABEL COCOK`. Setelah itu S100:

```powershell
docker exec sen12ls-spark /opt/spark/bin/spark-submit --master "local[2]" --driver-memory 2g /analitik/spark_pipeline.py --skala S100 --ulangan 3
python analitik\cocokkan.py --hasil results\analitik\S100
```

Jumlah baris yang harus tercetak: `7495600` anotasi dan `439200` patch, dan hasilnya harus berakhir `SEMUA TABEL COCOK`. Kedua pembanding memilih acuannya sendiri dari nama folder (`analitik/referensi_S10`, `analitik/referensi_S100`); itu bukti Spark menghitung benar pada ukuran penuh. Bila memori atau disk Docker habis, ulangi dengan `--tanpa-etl` (melewati penulisan tabel turunan; waktu dicatat sebagai mode terpisah) dan catat alasannya.

Cadangan bila S100 penuh gagal (misalnya kehabisan memori): bagian data nyata S100 saja, tanpa mencatat waktu, harus sama dengan S1. Itu setidaknya membuktikan Parquet S100 terbaca dengan benar.

```powershell
docker exec sen12ls-spark /opt/spark/bin/spark-submit --master "local[2]" --driver-memory 2g /analitik/spark_pipeline.py --skala S100 --hanya-asli
python analitik\cocokkan.py --hasil results\analitik\S100_asli
```

**Langkah 6. Ringkas waktu dan buat grafik.**

```powershell
python analitik\ringkas_waktu.py
python -m pip install matplotlib
python analitik\grafik.py
```

Hasil: `results/analitik/ringkasan_waktu.csv`, `results/analitik/waktu_per_tahap.csv`, dan PNG di `results/analitik/grafik/` (G1 sampai G5 dari tabel S1; G6 hanya bila `ringkasan_waktu.csv` ada).

**Langkah 7. Ukur ukuran Parquet di HDFS** (dibutuhkan laporan untuk membandingkan penyimpanan; HDFS harus masih menyala dengan `Live datanodes (2)`).

```powershell
python bench\catat.py ukuran --store spark --skala S1
python bench\catat.py ukuran --store spark --skala S10
python bench\catat.py ukuran --store spark --skala S100
type results\pengukuran_spark.csv
```

Berkas `results/pengukuran_spark.csv` memuat, untuk `annotations` dan `patches` di tiap skala, dua jenis ukuran dalam MiB: `ukuran_total` (satu salinan, yang dibandingkan dengan MongoDB dan PostGIS) dan `ukuran_dengan_replika` (ruang yang benar-benar dipakai HDFS dengan replikasi 2).

**Langkah 8. Commit** (hanya folder hasil ini; jangan `git add docs`). Blok ini berhenti sendiri bila hasilnya belum lengkap.

```powershell
if ((Test-Path results\analitik\ringkasan_waktu.csv) -and (Test-Path results\analitik\grafik\g6_waktu.png)) {
  git status
  git add analitik results/analitik
  if (Test-Path results\pengukuran_spark.csv) { git add results/pengukuran_spark.csv }
  git commit -m "[analitik] hasil Spark S1, S10, S100"
  git pull --rebase
  git push
} else { "Hasil belum lengkap: ulangi langkah 3 sampai 6. Jangan commit dulu." }
```

Percobaan di laptop lain: tambahkan `--keluar /results/analitik_coba` pada perintah `spark_pipeline.py` supaya waktunya tidak bercampur dengan pengukuran resmi, dan `--hasil results\analitik_coba\S1` pada `cocokkan.py`.

## 6. Memeriksa tanpa Docker

```powershell
python tests\uji_semua.py
python analitik\uji_sql.py --skala S1
python analitik\referensi.py --skala S1 --keluar C:\temp\acuan_baru
python analitik\cocokkan.py --hasil C:\temp\acuan_baru --acuan analitik\referensi_S1
```

Baris pertama menjalankan semua uji (22 uji, termasuk lima uji tahap analitik); baris kedua menjalankan 14 SQL di SQLite; dua baris terakhir menghitung ulang acuan dari `data/out/s1` dan memastikannya sama dengan yang di-commit.

## 7. Angka S1 yang harus muncul

Dari `analitik/referensi_S1/` (tiga cara hitung berbeda memberi angka yang sama):

- 74.956 anotasi, 4.392 patch, 16 lokasi, 11 inventaris, 5 jenis kejadian.
- Italy 47.522 anotasi (63,4%), seluruhnya pada 16 Mei 2023. DominicaMaria 10.172 (13,6%), seluruhnya pada 23 Sep 2017. Keduanya 77,0% dari semua anotasi. **9 dari 16 lokasi** hanya punya satu tanggal kejadian.
- 109 anotasi tanpa tanggal apa pun, 3.142 tanpa jenis kejadian, 11.260 tanpa inventaris (DominicaMaria, LanaoDelNorte, Thrissur, Nepal).
- Confidence tepat 1,0 untuk Rainfall, Hurricane, Tropical Storm, dan Cyclone, dengan selang citra selalu 7 hari; Earthquake 42,9%.
- 368 sel 0,1 derajat terisi; median 42,5 anotasi per sel, persentil 95 sebesar 1.075, maksimum 4.255.

## 8. Bila ada masalah

| Gejala | Tindakan |
|---|---|
| `ls: cannot access '/analitik'` | Kontainer `spark` belum dibuat ulang: `cd hdfs-parquet` lalu `docker compose up -d` (jangan `down`). |
| `Tidak bisa membaca hdfs://...` | NameNode atau DataNode belum siap (tunggu sampai `Live datanodes (2)`, lihat baris berikutnya), atau Parquet skala itu belum dibuat (`csv_to_parquet.py --scale S1`). |
| `Live datanodes (0)` atau `(1)` lebih dari dua menit setelah `docker compose up -d` | DataNode gagal mendaftar ke NameNode. Ini pernah terjadi sebelum sesi resmi; dugaan penyebabnya `clusterID` yang tidak cocok setelah klaster dibuat ulang, dan tidak diselidiki lebih lanjut. Lihat dulu `docker logs sen12ls-datanode1 --tail 30` dan `docker logs sen12ls-datanode2 --tail 30`. Bila tidak ada jalan lain, buat ulang klaster: `cd hdfs-parquet`, `docker compose down`, `docker compose up -d`, tunggu `Live datanodes (2)`, lalu muat ulang semua Parquet (Langkah 2). **Ini menghapus seluruh data HDFS.** |
| `Jumlah baris tidak sama dengan harapan` | Parquet skala itu belum lengkap atau berbeda versi; buat ulang dengan `csv_to_parquet.py`. `--force` hanya untuk percobaan. |
| `Compression codec zstd not supported` | Tambahkan `--kompresi snappy` pada perintah yang gagal (`csv_to_parquet.py` atau `spark_pipeline.py`), pakai pilihan yang sama di semua skala, dan catat di laporan. |
| `Gagal menulis atau membaca tabel turunan` | Disk Docker penuh atau HDFS bermasalah; bebaskan ruang, atau pakai `--tanpa-etl`. |
| `Kueri a5a_sel_terpadat gagal: ...` (nama kueri apa pun) | Kemungkinan beda dialek Spark. Kirim pesan galat lengkap ke Wildan; kueri hanya perlu diubah di `kueri_analitik.py`, lalu `python tests\uji_semua.py`. |
| `OutOfMemoryError` atau kontainer `Exited (137)` | Tutup program lain dan cek memori WSL di `.wslconfig` ([01_PERSIAPAN_UMUM.md](../baca-dulu/01_PERSIAPAN_UMUM.md), bagian A2). Coba `--tanpa-etl`. Bila `--driver-memory` memang harus dinaikkan, pakai nilai yang sama untuk S1, S10, dan S100 dan catat di laporan; jangan mengubahnya diam-diam. |
| `ADA SELISIH` di `cocokkan.py` | Jangan ubah angka. Kirim keluaran lengkap; selisih di S1 berarti kueri atau acuan perlu diperiksa. |

## 9. Hasil pengukuran waktu resmi (19 November 2026)

Dari `results/analitik/ringkasan_waktu.csv`. Satu putaran = ETL + 14 kueri + ekspor CSV; angka utama adalah median putaran **warm** (S1 dan S10: empat putaran warm; S100: dua putaran warm, jadi mediannya rata-rata dua angka). Mesin: laptop Wildan, dua inti, Spark `local[2]` (bagian 2).

| Skala | Anotasi | Median warm (detik) | Cold (detik) | Anotasi per detik | Waktu dibanding S1 |
|---|---:|---:|---:|---:|---:|
| S1 | 74.956 | 22,3 | 52,0 | 3.359 | 1,0 kali |
| S10 | 749.560 | 34,5 | 53,4 | 21.704 | 1,5 kali |
| S100 | 7.495.600 | 128,8 | 181,3 | 58.189 | 5,8 kali |

Data bertambah 100 kali dari S1 ke S100, tetapi waktu satu putaran hanya 5,8 kali, karena pada data kecil sebagian besar waktu tampaknya biaya tetap Spark. Hasilnya berasal dari **satu sesi per skala**, tanpa pengulangan antarsesi, sehingga dibaca sebagai orde besaran. Pembahasan lengkap ada di laporan, Bab IV.
