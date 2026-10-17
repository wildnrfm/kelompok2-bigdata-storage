# Panduan Sofi (Performance Analyst; membantu MongoDB)

Folder milikmu: `bench/` dan `results/`. Kamu memimpin **pengukuran**: harness uji, 100 titik tetap, wasit jawaban benar, pembandingan jumlah hasil
antar penyimpanan, pelaksanaan W1 sampai W8, dan analisis hipotesis. Hal umum (terminal, Git, Docker, VS Code) ada di
[01_PERSIAPAN_UMUM.md](01_PERSIAPAN_UMUM.md); peta seluruh pekerjaan di [00_ALUR_KERJA.md](00_ALUR_KERJA.md); nama dan perintah baku di
[KONTRAK.md](KONTRAK.md) (terutama **bagian 6 dan 7**); arti kolom di [../data/KAMUS_DATA.md](../data/KAMUS_DATA.md).

> Kode di `bench/` (`kueri.py`, `make_points.py`, `kebenaran.py`, `harness.py`, `compare_counts.py`, `summarize.py`, `catat.py`) **sudah ditulis dan
> diuji dengan database tiruan** (tanpa Docker). Yang belum pernah terjadi: dijalankan pada MongoDB, PostGIS, dan Spark sungguhan. Kamulah
> yang pertama membuktikannya. Bila ada yang gagal, itu temuan: `[BLOKIR]` dengan pesan galat lengkap. Memperbaiki berkas di `bench/` adalah
> hakmu (commit `[bench] ...`), tetapi **jangan mengubah definisi kueri atau jendela supaya "cocok"**; selisih berarti ada yang salah di
> tempat lain.

## Peta langkahmu

| # | Langkah | Menunggu | Perkiraan waktu | Membuka |
|---|---|---|---|---|
| 3 | Pasang alat (Git, Python, VS Code, Docker) + `pymongo` dan `psycopg` | - | 30 sampai 60 menit | #4 |
| 4 | Clone repo dan latihan Git | #2 (Wildan) dan #3 | 15 sampai 20 menit | #6 |
| 5 | Tulis spesifikasi laptop di grup | - | 5 menit | #7 |
| 7 | KICKOFF | #6 | 30 menit | #9, #11 |
| 9 | Membantu Elsa: MongoDB di Docker (kamu mereproduksi) | #7 | 30 menit | #13 |
| **11** | **Harness, 100 titik tetap, wasit** (kamu memimpin) | #7 | 45 sampai 90 menit | #17 |
| 13 | Membantu Elsa: muat S1 ke MongoDB | #8 dan #9 | 30 menit | #17 |
| **17** | **Harness W3 di ketiganya dan banding jumlah hasil** (kamu memimpin) | #11, #13, #14, #15 | 45 sampai 60 menit | #18 |
| 18 | SINKRON 1 | #17 | 30 sampai 45 menit | #25 |
| 19 | Baca dokumen rancangan | #7 | 45 menit | #20 |
| 20 | Bahan slide 5 (rencana pengujian dan hipotesis) | #19 | 30 menit | #22 |
| 23 | Tinjau silang (dengan Syuep) | #22 | 45 menit | #24 |
| 24 | Latihan pitching (SINKRON 2) | #23 | 45 sampai 60 menit | - |
| **25** | **W1 sampai W6 benar di S1 di ketiganya** (kamu menggabungkan) | #18 | 2 sampai 3 jam | #26 |
| **26** | **Muat S10 lalu S100 di ketiganya** (laptop uji) | #16 dan #25 | beberapa jam | #27 |
| **27** | **Jalankan W1 sampai W8, E1, E2** (kamu memimpin) | #26 | beberapa jam (belum terukur) | #28 |
| **28** | **Uji silang jumlah hasil di S100** (kamu memimpin) | #27 | 1 jam | #29 |
| **29** | **Tabel, grafik, hipotesis H1 sampai H5** (kamu memimpin) | #28 | 2 sampai 3 jam | #30 |

---

## #3, #4, #5. Alat, clone, spesifikasi

- **#3 Pasang alat:** [01_PERSIAPAN_UMUM.md](01_PERSIAPAN_UMUM.md) bagian A2, **termasuk Docker Desktop, `.wslconfig`, dan pustaka**:

  ```powershell
  python -m pip install pymongo "psycopg[binary]"
  ```

- **#4 Clone dan latihan Git:** setelah Wildan menulis `[SELESAI] root: paket awal sudah di GitHub`, jalankan (bagian A3):

```powershell
mkdir C:\proyek
cd C:\proyek
git clone https://github.com/wildnrfm/kelompok2-bigdata-storage.git
cd kelompok2-bigdata-storage
git pull --rebase
New-Item -ItemType Directory -Force latihan | Out-Null
Set-Content latihan\sofi.txt "Halo, ini latihan Sofi"
git add latihan/sofi.txt
git commit -m "[latihan] Sofi: uji coba push"
git pull --rebase
git push
```

Tulis di grup: `[SELESAI] latihan: clone dan push berhasil (latihan/sofi.txt) - Sofi`. Periksa baris namamu di `TEAM.md`
(username `marsandasofi`).

- **#5 Spesifikasi:** bagian A4; tulis di grup.

---

## #9. Membantu Elsa: MongoDB di Docker

Elsa memimpin. Bagianmu: **mereproduksi di laptopmu** supaya masalah yang hanya muncul di satu laptop ketahuan lebih awal, dan paham
berkas yang kamu uji nanti. Jalankan langkah 9.1 sampai 9.4 di [PANDUAN_Elsa.md](PANDUAN_Elsa.md) (`docker compose up -d`, lima uji, uji sambungan Python), lalu:

- [ ] baca `mongodb/docker-compose.yml` dan jelaskan dengan kata-katamu: port, volume, `/sen12ls-data`, `/scripts`, cache 0,5 GB
- [ ] `docker compose stop` di folder `mongodb` setelah selesai (satu penyimpanan aktif sekali waktu)

---

## #11. Harness, 100 titik tetap, dan wasit (kamu memimpin, Elsa membantu)

**Tujuan.** Memastikan alat ukur kita **benar dan deterministik** sebelum dipakai: 100 titik uji yang sama di semua laptop, jawaban
benar dari wasit, dan harness yang menolak data yang salah skala.

**Menunggu:** kickoff (#7). Data S1 harus ada di laptopmu (11.1).

### 11.1 Buat S1 di laptopmu dan buktikan sama dengan milik Wildan

```powershell
cd C:\proyek\kelompok2-bigdata-storage
git pull --rebase
python data\convert_inventory.py
python data\generate_scales.py --verify
```

**Berhasil bila:** `LOLOS: 17 pemeriksaan cocok` dan empat baris `COCOK` untuk `out/s1/...`. `BEDA` berarti data tidak boleh dipakai:
`[BLOKIR]` ke Syuep.

### 11.2 Buat ulang 100 titik uji dan wasit: hasilnya harus **identik** dengan yang di GitHub

```powershell
python bench\make_points.py
python bench\kebenaran.py --skala S1 --tulis
git status
```

**Berhasil bila** `git status` **tidak menampilkan perubahan** pada `bench/points.json` maupun `bench/benar/` (kedua folder itu sudah
di-commit Wildan; skripnya deterministik dengan seed 20261023). Keluaran pertama harus berbunyi `Titik dibuat: 100 (70 di dalam, 30 di luar)`.

Bila `git status` menampilkan `modified: bench/points.json`, hasil konversi atau versi Python-mu berbeda dari milik Wildan: **jangan commit**;
`git restore bench/points.json bench/benar`, ulangi 11.1 (`--verify`), dan `[BLOKIR]` bila tetap beda.

### 11.3 Pahami alat ukurnya (30 menit)

Baca docstring di awal tiap berkas, lalu cocokkan dengan [KONTRAK.md](KONTRAK.md) bagian 6:

1. `bench/kueri.py`: definisi W1 sampai W6 yang dipakai **semua** penyimpanan. Perhatikan `PARAMETER_BAWAAN` (±0,01 derajat untuk W2 dan W3; ±0,1 derajat
   untuk W4; ±30 hari; `event_conf` ≥ 0,9) dan penjelasan mengapa jendela **digeser setengah langkah** (5e-8 derajat) dari kisi koordinat.
2. `bench/kebenaran.py` (wasit): menghitung jumlah yang seharusnya langsung dari `annotations.csv`, tanpa database.
3. `bench/harness.py`: lihat semua pilihan.

   ```powershell
   python bench\harness.py --help
   ```

   Pilihan penting: `--store {mongodb|postgis|spark}`, `--workload {W1..W6}`, `--scale {S1|S10|S100}`, `--repeats 3`, `--cold-warm {warm|cold}`,
   `--first-run-no`, `--clients N` (hanya W1), `--limit-titik N`, `--note`, `--force`.

Cobalah satu contoh wasit supaya kamu tahu apa yang ia keluarkan:

```powershell
python bench\kebenaran.py --skala S1 --ann 100
```

Contoh hasil (bentuknya; angka di datamu berbeda):

```text
Anotasi 100: lokasi Italy, titik pusat (11.644376, 43.902886), event_date 2017-09-30, event_type Earthquake
W2: 8 anotasi (titik pusat di jendela +-0.01 derajat)
    ann_id 100       Italy          event_date 2017-09-30
    ...
W3: 1 anotasi (dan event_date 2017-08-31 sampai 2017-10-30)
W4: 60 anotasi (kotak beririsan dengan jendela +-0.1 derajat, event_type Earthquake, conf >= 0.9)
```

### 11.4 Jalankan seluruh uji tanpa Docker

```powershell
python tests\uji_semua.py
```

**Berhasil bila** berakhir `SEMUA UJI LULUS`.

### 11.5 Tulis rencana uji (bahan slide 5 dan laporan)

Buat `docs\rencana_uji.md` berisi tabel ringkas dengan kata-katamu sendiri. Kerangka:

| Kode | Apa yang diukur | Parameter | Skala | Ulangan | Penyimpanan | Hipotesis terkait |
|---|---|---|---|---|---|---|
| W1 | ambil satu anotasi menurut `ann_id` | 100 id tetap; klien 1, 10, 50, 100 | S1, S10, S100 | 3 | ketiganya (klien banyak: MongoDB dan PostGIS) | H5 |
| W2 | jumlah anotasi yang titik pusatnya di jendela | ±0,01° | S1, S10, S100 | 3 | ketiganya | H1 |
| W3 | W2 + `event_date` ±30 hari | ±0,01°, ±30 hari | S1, S10, S100 | 3 | ketiganya | H1 |
| W4 | kotak pembatas beririsan + `event_type` + `event_conf` ≥ 0,9 | ±0,1° | S1, S10, S100 | 3 | ketiganya | H2 |
| W5 | jumlah per `event_type` dan tahun | seluruh data | S1, S10, S100 | 3 | ketiganya | H4 |
| W6 | patch per `inventory` dan `split` | seluruh data | S1, S10, S100 | 3 | ketiganya | H4 |
| W7 | waktu muat, waktu indeks, ukuran di disk | `catat.py` | S1, S10, S100 | 1 (catat) | ketiganya | H3 |
| W8 | tambah satu batch (74.956) ke S100 | `catat.py` | S100 | 1 (catat) | ketiganya | - |

Tambahkan tiga paragraf pendek: (1) **aturan adil** (data dan seed sama, 100 titik tetap, memori dibatasi, satu penyimpanan aktif, minimal 3 ulangan, cold dan
warm, satu laptop); (2) **kriteria benar** (jumlah hasil sama dengan wasit; selisih = ada yang salah, bukan efek tepi); (3) **hipotesis dan syarat penolakannya**
(salin tabel H1 sampai H5 dari KONTRAK bagian 7; semuanya **dugaan awal, belum diuji**).

```powershell
git add docs/rencana_uji.md
git commit -m "[docs] rencana uji W1 sampai W8 dan aturan adil"
git pull --rebase
git push
```

**Berhasil bila (#11)**

- [ ] `git status` tidak menunjukkan perubahan pada `bench/points.json` dan `bench/benar/` setelah dibuat ulang
- [ ] `python tests\uji_semua.py`: `SEMUA UJI LULUS`
- [ ] kamu bisa menjelaskan tanpa membaca: apa itu W1 sampai W6, mengapa jendela digeser setengah langkah, dan apa tugas wasit
- [ ] `docs/rencana_uji.md` sudah di GitHub

**Pesan WhatsApp**

```text
[SELESAI] bench: points.json (100 titik: 70 dalam, 30 luar) dan wasit S1 identik dengan milik Wildan; uji tanpa Docker lulus.
Harness siap dipakai: python bench\harness.py --store <mongodb|postgis|spark> --workload W3 --scale S1. Rencana uji: docs/rencana_uji.md
```

### Kalau macet

| Tanda | Penyebab dan cara memperbaiki |
|---|---|
| `git status` memuat perubahan `bench/points.json` | Hasil konversimu beda dari Wildan. Jangan commit. `git restore bench/points.json bench/benar`; ulangi 11.1; `[BLOKIR]` bila tetap beda. |
| `Berkas ...\annotations.csv belum ada` | Jalankan `python data\convert_inventory.py` (11.1). |
| `psycopg belum terpasang` atau `pymongo belum terpasang` | `python -m pip install pymongo "psycopg[binary]"`. |
| `uji_semua.py` gagal | Salin nama uji yang `GAGAL` dan pesannya ke `[BLOKIR]`. Jangan lanjut sebelum lulus. |
| Teks aneh (`?`) di PowerShell | Tidak berbahaya; skrip memakai ASCII murni. Bila berkas hasil tampak rusak, jalankan `chcp 65001` lalu ulangi. |

---

## #13. Membantu Elsa: muat S1 ke MongoDB

Elsa memimpin. Bagianmu: periksa hasilnya **dengan mata segar**.

- [ ] `results/pengukuran_mongodb.csv` memuat baris `muat` untuk `annotations` dan `patches`, baris `indeks`, dan baris ukuran, dengan satuan benar (detik atau MiB)
- [ ] jumlah dokumen `74956 4392` dan tanggal tampil sebagai `ISODate(...)` (lihat [PANDUAN_Elsa.md](PANDUAN_Elsa.md), 13.2)
- [ ] hasil W3 dengan tangan sama dengan `python bench\kebenaran.py --skala S1 --ann <angka yang sama>`

---

## #17. Harness W3 di ketiganya dan banding jumlah hasil (kamu memimpin)

**Tujuan.** Membuktikan bahwa MongoDB, PostGIS, dan Spark SQL memberi **jumlah hasil W3 yang sama** (dan sama dengan wasit) untuk 100 titik uji di S1.
Waktu dari laptop berbeda **tidak** dibandingkan di langkah ini.

**Menunggu:** Elsa (#13: MongoDB termuat), Levi (#14: PostGIS termuat, #15: Parquet dan Spark), dan #11 (kamu).

Tiap orang menjalankan harness di penyimpanannya dan mendorong CSV-nya (`[results]`):

| Siapa | Perintah |
|---|---|
| Elsa | `python bench\harness.py --store mongodb --workload W3 --scale S1` |
| Levi | `python bench\harness.py --store postgis --workload W3 --scale S1` dan `python bench\harness.py --store spark --workload W3 --scale S1` |

Setelah ketiganya mendorong hasilnya:

```powershell
cd C:\proyek\kelompok2-bigdata-storage
git pull --rebase
dir results\*_W3_S1*.csv
```

Contoh hasil: tiga berkas, mis. `20261101_mongodb_W3_S1.csv`, `20261101_postgis_W3_S1.csv`, `20261101_spark_W3_S1.csv`. Bandingkan (ganti dengan nama berkasmu):

```powershell
python bench\compare_counts.py results\20261101_mongodb_W3_S1.csv results\20261101_postgis_W3_S1.csv results\20261101_spark_W3_S1.csv
```

**Berhasil bila**:

```text
Perbandingan W3 S1: mongodb vs postgis vs spark vs benar
Cocok: 100 dari 100 kueri.
Semua jumlah hasil sama.
```

Lalu ringkas semua waktu (hanya untuk dilihat; waktu antar laptop belum adil):

```powershell
python bench\summarize.py
```

Contoh hasil (bagian akhir):

```text
Tertulis: results/ringkasan.csv (3 kelompok) dan results/banding.csv (1 baris), dari 3 berkas
```

Simpan dan kabari grup:

```powershell
git add results/ringkasan.csv results/banding.csv
git commit -m "[results] banding W3 S1 dari tiga penyimpanan"
git pull --rebase
git push
```

```text
[SELESAI] results: W3 S1 mongodb, postgis, spark: jumlah hasil sama pada 100 dari 100 kueri dan cocok dengan wasit.
```

**Bila ada selisih:** keluaran mencetak tabel `kueri_id` dan jumlah tiap penyimpanan. Selisih **bukan efek tepi** (jendela sudah digeser dari tepi). Cek berurutan
(sama seperti pesan di keluaran): (1) skala yang dimuat sama di semua penyimpanan (74956), (2) data dimuat ulang dari `data/out` yang sama (`--verify` COCOK), (3) indeks sudah dibuat,
(4) tanda `-` berarti kueri itu tidak ada di berkas. Lalu bandingkan **tiap penyimpanan dengan wasit sendiri-sendiri** (`compare_counts.py <satu berkas>`) untuk melihat siapa yang salah.
Tetap beda: `[BLOKIR]` dengan tabelnya dan nama kedua orang pemilik penyimpanan.

### Kalau macet

| Tanda | Penyebab dan cara memperbaiki |
|---|---|
| `Tidak bisa terhubung ke mongodb` / `postgis` | Container belum jalan di laptop pemilik penyimpanannya. `docker compose ps` di foldernya. Hanya satu penyimpanan aktif sekali waktu. |
| `Jumlah data tidak cocok. Muat skala S1 dulu` | Data belum atau salah dimuat. Lihat [PANDUAN_Elsa.md](PANDUAN_Elsa.md) #13 atau [PANDUAN_Levi.md](PANDUAN_Levi.md) #14. |
| `psycopg.OperationalError: password authentication failed` | Sandi uji harus `postgres` (default compose). Bila Levi mengubahnya lewat `.env`, harness harus disesuaikan: tanyakan Levi. |
| `Berkas hasil sama sekali tidak ada untuk Spark` | Spark menulis ke `results/` lewat container; periksa `docker compose ps` di `hdfs-parquet` dan apakah folder `results/` terpasang (`docker exec sen12ls-spark ls /results`). |
| `compare_counts`: `kolom ini tidak ada` | Berkas yang dibandingkan bukan hasil harness (mis. `pengukuran_*.csv`). Pilih berkas `YYYYMMDD_<penyimpanan>_W3_S1.csv`. |
| `compare_counts`: `berkas harus memuat beban kerja dan skala yang sama` | Kamu mencampur beban kerja atau skala. Pilih tiga berkas dengan `W3` dan `S1` yang sama. |

---

## #18. SINKRON 1

Yang kamu siapkan dan tunjukkan (demo 4 menit bersama Elsa, lalu 8 menit sesi banding):

- [ ] keluaran `compare_counts.py` tiga penyimpanan + wasit (`Cocok: 100 dari 100 kueri`)
- [ ] `bench/points.json` dan wasit identik di semua laptop (hasil #11)
- [ ] `results/ringkasan.csv` dan `results/banding.csv` untuk W3 S1
- [ ] daftar istilah dan nama kolom yang perlu disamakan (kolom CSV hasil: `penyimpanan, beban_kerja, skala, ulangan, cold_warm, kueri_id, waktu_ms, jumlah_hasil, catatan`)

Pesan setelah Sinkron 1: `[SELESAI] Sinkron 1: hasil W3 dari tiga penyimpanan sudah dibandingkan dan dicatat.`

---

## #19. Baca dokumen rancangan

Tautan ada di grup (Wildan menulis `[SELESAI] dokumen v2` saat versi final siap). Baca bagian **Rencana pengujian dan hipotesis** dan periksa:

- [ ] W1 sampai W8 dan parameternya cocok dengan [KONTRAK.md](KONTRAK.md) bagian 6 (W9 dan W10 belum ada skrip; ditulis sebagai rencana)
- [ ] H1 sampai H5 dan syarat penolakannya cocok dengan KONTRAK bagian 7; semuanya ditulis **dugaan awal, belum diuji**
- [ ] aturan adil: memori dibatasi, satu penyimpanan aktif, minimal 3 ulangan, cold dan warm, 100 titik tetap, wasit
- [ ] tidak ada klaim hasil yang belum kita ukur; tidak ada sisa nama dataset lama

Bentuk pesan temuan: `Dokumen - <bagian> - <yang salah atau kurang> - usul: <perbaikan>`. Tidak ada temuan: `Dokumen - bagianku sudah benar (Sofi)`.

---

## #20. Bahan slide 5 (rencana pengujian dan hipotesis)

Kirim ke Wildan **3 sampai 5 poin** (satu kalimat pendek, paling banyak 12 kata) dan **satu gambar**.

Poin yang disarankan (ubah dengan kata-katamu):

- Enam kueri W1 sampai W6, plus waktu muat, indeks, dan ukuran (W7, W8)
- Skala S1, S10, S100; 100 titik uji tetap (70 di dalam, 30 di luar)
- Adil: memori dibatasi, satu penyimpanan aktif, minimal 3 ulangan, cold dan warm
- Jawaban benar dihitung wasit dari CSV; selisih jumlah berarti ada yang salah
- Hipotesis H1 sampai H5: dugaan awal, **belum diuji**, dengan syarat penolakan

Gambar yang disarankan: tabel H1 sampai H5 (hipotesis dan "ditolak bila") atau tabel W1 sampai W6 satu kalimat per baris.

```text
[SELESAI] bahan slide 5 (Sofi): 5 poin dan 1 gambar: <tempel atau lampirkan>
```

---

## #23. Tinjau silang (dengan Syuep)

Kamu meninjau **profil dataset dan skala milik Syuep**; Syuep meninjau rencana uji dan hipotesismu.

Daftar periksa untuk bagian Syuep:

- [ ] angka cocok dengan `data/KAMUS_DATA.md`: 74.956 anotasi, 4.392 patch, 16 lokasi, 109 tanpa tanggal; S10 749.560; S100 7.495.600
- [ ] aturan simulasi jelas (batch 0 = data asli; tanggal dan lokasi digeser; seed 20261023; bersarang) dan ada peringatan "hanya untuk uji beban"
- [ ] apa yang disimpan dan tidak (titik pusat + kotak pembatas, bukan poligon, bukan citra) dijelaskan
- [ ] keterbatasan jujur: arti `*_dt2`, satuan `area`, EPSG:4326 dugaan, hubungan anotasi-patch hanya per inventaris
- [ ] ukuran berkas ditulis sebagai "diukur pada data tiruan berbentuk laporan asli" bila belum diukur pada data asli

Cara: baca bagiannya sekali penuh tanpa mengomentari; baca lagi dan catat; kirim `[Tinjau] @Syuep - <bagian> - <temuan> - Saran: <perbaikan>`.

---

## #24. Latihan pitching (SINKRON 2)

Kamu menyampaikan **slide 5** (sekitar 2 menit) dan menjawab (bank pertanyaan di [PANDUAN_Wildan.md](PANDUAN_Wildan.md), #24):
**"Bagaimana membuat perbandingan adil?"**, **"Apa hipotesisnya dan kapan ditolak?"**, dan **"Mengapa Spark terlihat lambat di data kecil?"** (bersama Levi).

---

## #25. W1 sampai W6 benar di S1 di ketiganya (kamu menggabungkan)

**Menunggu:** #18. Elsa, Levi, dan kamu masing-masing menjalankan **keenam kueri di S1** di penyimpanannya dan mendorong CSV-nya:

```powershell
foreach ($w in "W1","W2","W3","W4","W5","W6") { python bench\harness.py --store <penyimpanan> --workload $w --scale S1 }
```

(Elsa: `mongodb`; Levi: `postgis` dan `spark`; langkah rincinya di panduan masing-masing, #25.) Bila kamu juga menjalankan satu penyimpanan di laptopmu,
lakukan hal yang sama.

Setelah semuanya masuk, gabungkan per beban kerja:

```powershell
git pull --rebase
foreach ($w in "W1","W2","W3","W4","W5","W6") {
  $m = Get-ChildItem ("results\*_mongodb_" + $w + "_S1.csv") | Sort-Object LastWriteTime | Select-Object -Last 1
  $p = Get-ChildItem ("results\*_postgis_" + $w + "_S1.csv") | Sort-Object LastWriteTime | Select-Object -Last 1
  $s = Get-ChildItem ("results\*_spark_" + $w + "_S1.csv") | Sort-Object LastWriteTime | Select-Object -Last 1
  python bench\compare_counts.py $m.FullName $p.FullName $s.FullName
}
```

**Berhasil bila** enam kali `Semua jumlah hasil sama` (W1: `Cocok: 100 dari 100`; W5 dan W6: `Cocok: 1 dari 1`). Lalu:

```powershell
python bench\summarize.py
git add results/ringkasan.csv results/banding.csv
git commit -m "[results] banding W1 sampai W6 S1"
git pull --rebase
git push
```

Selisih: lihat panduan #17 di atas. **Jangan** melanjutkan ke #26 sebelum W1 sampai W6 di S1 cocok.

**Pesan WhatsApp:** `[SELESAI] results: W1 sampai W6 di S1 cocok di ketiga penyimpanan dan dengan wasit (6 dari 6).`

---

## #26. Muat S10 lalu S100 di ketiganya (laptop uji)

**Menunggu:** #16 (Syuep) dan #25. Semua **pengukuran waktu** (W1 sampai W8) berjalan di **satu laptop uji** supaya adil; pemilik laptop itu menjalankan
perintah, Elsa dan Levi mendampingi (berbagi layar) dan memastikan langkah penyimpanan mereka benar. Pemuatan tiap penyimpanan ada di panduan pemiliknya:
[Elsa #26](PANDUAN_Elsa.md) (MongoDB) dan [Levi #26](PANDUAN_Levi.md) (PostGIS dan HDFS-Parquet).

### 26.1 Persiapan laptop uji

- [ ] colok pengisi daya; atur laptop **tidak tidur** (Settings > System > Power); tutup browser dan program berat; tunda Windows Update
- [ ] disk bebas minimal **25 GB**; RAM 16 GB atau lebih; Docker memakai `memory=6GB` (A2)
- [ ] `git pull --rebase` dan data S1, S10, S100 di laptop itu **COCOK** dengan checksum:

  ```powershell
  python data\generate_scales.py --scale S10
  python data\generate_scales.py --scale S100
  python data\generate_scales.py --verify
  ```

### 26.2 Catat kondisi uji (sekali; masuk laporan)

Buat `results\kondisi_uji.md` berisi keluaran perintah-perintah ini (setelah penyimpanan yang bersangkutan berjalan):

```powershell
docker --version
python --version
docker exec sen12ls-mongo mongosh --quiet --eval "db.version()"
docker exec sen12ls-postgis psql -U postgres -d sen12ls -Atc "select version()" -c "select postgis_full_version()"
docker exec sen12ls-spark /opt/spark/bin/spark-submit --version
```

ditambah spesifikasi laptop (CPU, RAM, disk; A4) dan pengaturan memori: cache WiredTiger 0,5 GB, `shared_buffers` 256 MB, Spark `local[2]` dengan 2 GB, Docker `memory=6GB`.

### 26.3 Urutan praktis

**Satu penyimpanan sampai tuntas, lalu berikutnya** (satu penyimpanan aktif sekali waktu): MongoDB, lalu PostGIS, lalu HDFS-Parquet-Spark. Untuk tiap penyimpanan:

1. nyalakan; muat S1 lagi di laptop uji (agar kurva skala S1, S10, S100 diukur di mesin yang sama) dan ukur: W7 dan W1 sampai W6 di S1
2. muat S10; W7; W1 sampai W6 di S10; E1 (tanpa indeks) di S10
3. muat S100; W7; W1 sampai W6 di S100; W8 **paling akhir**
4. `docker compose stop` (atau `down -v` bila disk sempit; `results/` tetap aman)

---

## #27. Jalankan W1 sampai W8, E1, dan E2 (kamu memimpin)

**Menunggu:** #26. Semua perintah dari akar repo, PowerShell, **di laptop uji**. Sebelum tiap sesi: `docker ps` (hanya penyimpanan yang diuji yang jalan),
tidak ada program berat lain.

Ganti `<store>` dengan `mongodb`, `postgis`, atau `spark`; `<S>` dengan `S1`, `S10`, atau `S100`.

### 27.1 Warm: W1 sampai W6 (3 ulangan, bawaan)

```powershell
foreach ($w in "W1","W2","W3","W4","W5","W6") { python bench\harness.py --store <store> --workload $w --scale <S> }
```

- Harness lebih dulu menghitung jumlah baris dan **menolak** bila tidak sama dengan skala (`Jumlah data tidak cocok`): itu perlindungan dari salah label, jangan dilewati dengan `--force`
  kecuali kamu paham alasannya.
- **S100, W2 sampai W4:** pakai `--limit-titik 20` untuk **ketiga** penyimpanan (agar himpunan kueri sama dan Spark tidak terlalu lama):
  `python bench\harness.py --store <store> --workload W3 --scale S100 --limit-titik 20`. Tulis di laporan bahwa S100 memakai 20 titik pertama.
- **S100, W1 untuk Spark:** pakai `--limit-titik 20` juga (tiap id = pemindaian penuh).

Contoh keluaran akhir satu run:

```text
Ringkasan mongodb W3 S100 (warm, 3 ulangan x 20 kueri = 60 eksekusi)
  median : ... ms
  p95    : ... ms
  ...
Berkas   : C:\...\results\20261105_mongodb_W3_S100.csv
```

### 27.2 W1 banyak klien (hanya MongoDB dan PostGIS)

```powershell
foreach ($n in 10,50,100) { python bench\harness.py --store <store> --workload W1 --scale <S> --clients $n }
```

Tiap klien membuka koneksi sendiri; kolom `catatan` terisi `konkurensi=N` otomatis. Bila klien 100 menimbulkan galat koneksi (`GALAT` di berkas), catat dan sebut di laporan.
Untuk H5 yang dibandingkan adalah p95 dengan 1 klien (hasil 27.1) dan 50 klien di **S100**.

### 27.3 Cold (cache dingin)

Nyalakan ulang penyimpanan sebelum **tiap** putaran dingin, tunggu 20 detik, lalu jalankan satu putaran tanpa pemanasan dengan nomor ulangan berbeda:

```powershell
foreach ($n in 1,2,3) {
  docker restart <container>      # sen12ls-mongo atau sen12ls-postgis
  Start-Sleep -Seconds 20
  python bench\harness.py --store <store> --workload W3 --scale <S> --cold-warm cold --repeats 1 --first-run-no $n
}
```

Lakukan untuk W3 (kueri spasial + tanggal) dan W5 (agregasi) di S10 dan S100. Untuk Spark, setiap `run_sql.py` memulai sesi Spark baru, jadi cukup menjalankan perintah yang sama tanpa `docker restart`
(HDFS dan Spark container tetap menyala).

### 27.4 E1: tanpa indeks (hanya S10; MongoDB dan PostGIS)

MongoDB:

```powershell
docker exec sen12ls-mongo mongosh --quiet --file /scripts/drop_indexes.js
foreach ($w in "W2","W3","W4") { python bench\harness.py --store mongodb --workload $w --scale S10 --note "varian=tanpa-indeks" }
python bench\catat.py ukur --store mongodb --skala S10 --jenis indeks --objek semua docker exec sen12ls-mongo mongosh --quiet --file /scripts/indexes.js
```

PostGIS:

```powershell
docker exec sen12ls-postgis psql -U postgres -d sen12ls -f /sql/drop_indexes.sql
foreach ($w in "W2","W3","W4") { python bench\harness.py --store postgis --workload $w --scale S10 --note "varian=tanpa-indeks" }
python bench\catat.py ukur --store postgis --skala S10 --jenis indeks --objek semua docker exec sen12ls-postgis psql -U postgres -d sen12ls -f /sql/indexes.sql
```

`varian=tanpa-indeks` di kolom `catatan` membuat `summarize.py` **memisahkan** hasil ini dari hasil berindeks (kolom `varian`). Tanpa indeks di S100 sangat lambat; jangan lakukan.
Setelah E1, **bangun indeks lagi** (perintah terakhir di atas) sebelum menguji yang lain.

### 27.5 W7 dan W8 (dicatat, bukan harness)

Waktu muat, waktu indeks, dan ukuran dicatat oleh `bench\catat.py` saat memuat (lihat panduan Elsa dan Levi, #26). W8 (tambah batch100 ke S100) dilakukan **paling akhir** untuk tiap penyimpanan.

### 27.6 Simpan hasil setelah tiap penyimpanan selesai

```powershell
git add results
git status
git commit -m "[results] <store>: W1 sampai W6 di <S>, cold, E1"
git pull --rebase
git push
```

Bila `git status` menampilkan berkas besar atau di luar `results/`, berhenti dan periksa.

### 27.7 Lihat ringkasan

```powershell
python bench\summarize.py
python bench\catat.py tampil
```

`summarize.py` menampilkan satu baris per kelompok (penyimpanan, beban kerja, skala, cold/warm, konkurensi, varian) dengan median, rentang antar ulangan, dan p95,
lalu tabel banding antar penyimpanan. **Periksa kolom `galat`**: nol artinya tidak ada kueri yang gagal; angka lain berarti ada `jumlah_hasil = -1` yang harus dilihat di berkas hasilnya.

**Berhasil bila (#27)**

- [ ] untuk tiap penyimpanan dan tiap skala: W1 sampai W6 warm (3 ulangan), W3 dan W5 cold (3 ulangan), W1 dengan 10, 50, 100 klien (MongoDB dan PostGIS)
- [ ] E1 di S10 untuk MongoDB dan PostGIS (`varian=tanpa-indeks`)
- [ ] W7 dan W8 tercatat di `results/pengukuran_*.csv`
- [ ] tidak ada kolom `galat` bernilai lebih dari nol yang belum dijelaskan
- [ ] semua hasil sudah di GitHub

```text
[SELESAI] results: W1 sampai W8 di <store> untuk S1, S10, S100 (laptop uji <nama>); E1 di S10. Berkas di results/.
```

### Kalau macet

| Tanda | Penyebab dan cara memperbaiki |
|---|---|
| `Berkas ... sudah ada. Pakai nama lain.` (Spark) | Harness memberi akhiran `_2`, `_3` otomatis; pesan ini muncul bila dua proses menulis bersamaan. Jalankan satu per satu. |
| Spark sangat lambat di S100 | Pakai `--limit-titik 20` (27.1) dan pastikan hanya Spark yang aktif. Wajar bila lebih lambat dari indeks; itulah hipotesis H1. |
| Hasil bergoyang antar ulangan | Lihat `median_ulangan_min` dan `median_ulangan_maks` di `ringkasan.csv`. Rentang besar: tutup program lain dan ulangi; sebut dalam laporan. |
| `GALAT ...` di kolom catatan | Satu kueri gagal. Lihat pesannya; bila berulang pada kueri yang sama, `[BLOKIR]`. |
| Laptop macet atau container berhenti | Memori habis. `docker stats --no-stream`; turunkan klien (27.2); naikkan `memory=` di `.wslconfig` bila RAM mengizinkan; jangan mengubah batas memori database. |
| Disk penuh | Hapus penyimpanan yang selesai (`docker compose down -v` di foldernya) dan `data\out\s100` bila tidak dipakai lagi. |

---

## #28. Uji silang jumlah hasil di S100 (kamu memimpin, Elsa membantu)

**Tujuan.** Membuktikan tiap penyimpanan memberi jumlah hasil yang **benar** di S100 (bukan hanya cepat).

### 28.1 Wasit S100 (sekali)

```powershell
python bench\kebenaran.py --skala S100 --tulis
```

Memerlukan sekitar 1 GB RAM dan beberapa menit. Menulis `bench\benar\W*_S100.csv` (kecil; **di-commit**).

### 28.2 Bandingkan tiap penyimpanan dengan wasit

Untuk tiap penyimpanan dan beban kerja di S100, ambil berkas hasil warm terbaru dan bandingkan:

```powershell
foreach ($s in "mongodb","postgis","spark") {
  foreach ($w in "W1","W2","W3","W4","W5","W6") {
    $f = Get-ChildItem ("results\*_" + $s + "_" + $w + "_S100.csv") -ErrorAction SilentlyContinue | Sort-Object LastWriteTime | Select-Object -First 1
    if ($f) { python bench\compare_counts.py $f.FullName }
  }
}
```

(`-First 1` mengambil berkas **pertama** hari itu, yaitu hasil warm; berkas bersyarat seperti cold atau `--clients` ditandai di kolom `catatan` dan berisi kueri yang sama.)

**Berhasil bila** tiap perbandingan berakhir `Semua jumlah hasil sama` (W2 sampai W4 pada 20 titik pertama bila kamu memakai `--limit-titik 20`; kueri wasit yang tidak
dijalankan diabaikan dengan catatan). Tiga penyimpanan sekaligus (bila himpunan kuerinya sama):
`python bench\compare_counts.py <mongodb.csv> <postgis.csv> <spark.csv>`.

Simpan:

```powershell
git add bench/benar results
git commit -m "[bench] wasit S100 dan hasil uji silang"
git pull --rebase
git push
```

**Bila ada selisih:** itu temuan penting, bukan untuk "dibenarkan". Catat tabelnya, periksa berurutan (skala yang dimuat; indeks; S100 COCOK dengan checksum;
dimuat ulang tanpa terpotong), lalu `[BLOKIR]`. Selama selisih belum dijelaskan, **jangan** memakai hasil waktu kueri yang bersangkutan di laporan.

**Pesan WhatsApp:** `[SELESAI] results: uji silang S100: <n> dari <n> perbandingan cocok dengan wasit (mongodb, postgis, spark).`

---

## #29. Tabel, grafik, dan hipotesis H1 sampai H5 (kamu memimpin, Elsa membantu)

**Menunggu:** #28. Semua angka diambil dari `results/ringkasan.csv`, `results/banding.csv`, dan `python bench\catat.py tampil`.

```powershell
git pull --rebase
python bench\summarize.py
python bench\catat.py tampil
```

Buka `results\banding.csv` dan `results\ringkasan.csv` di Excel atau Google Sheets (File > Open; pemisah koma).

### 29.1 Grafik (tiga jenis cukup)

1. **Kurva skala (E2):** sumbu x = S1, S10, S100; sumbu y = median (ms), **skala logaritmik**; satu garis per penyimpanan; satu grafik per beban kerja (W2, W3, W4 paling penting).
2. **Perbandingan di S100:** diagram batang median (ms, skala log) per beban kerja W1 sampai W6, tiga penyimpanan berdampingan.
3. **Ukuran di disk (H3):** diagram batang `ukuran_total` (MiB) per penyimpanan di S1, S10, S100 dari `catat.py tampil`.

Tiap grafik: judul, satuan, **legenda**, dan sumber (nama berkas). Jangan membedakan penyimpanan hanya dengan warna; beri penanda atau label langsung.

### 29.2 Evaluasi hipotesis (tulis di `docs\hipotesis.md`)

Untuk tiap hipotesis tulis: **angka yang dipakai (berkas dan kolom)**, **aturan** (dari tabel di bawah), dan **keputusan** (diterima, ditolak, atau tidak bisa disimpulkan, dengan alasan). Hipotesis
yang datanya tidak ada ditulis "belum diuji", bukan ditebak.

| Kode | Angka yang dilihat | Ditolak bila |
|---|---|---|
| H1 | W2 dan W3: median Spark dibagi median MongoDB dan PostGIS di S1, S10, S100 | selisih mengecil atau terbalik dari S1 ke S100 |
| H2 | W4: median PostGIS dan MongoDB (warm) di S1, S10, S100 | MongoDB sama cepat atau lebih cepat |
| H3 | `ukuran_total`: Parquet (satu salinan), PostGIS, MongoDB di S100 (dan S1, S10) | urutan dari kecil ke besar berbeda dari Parquet < PostGIS < MongoDB |
| H4 | W5 dan W6 di S100: median Spark dan MongoDB | MongoDB lebih cepat |
| H5 | W1 di S100: `p95_ms` dengan 50 klien dibagi `p95_ms` 1 klien, untuk MongoDB dan PostGIS | rasio 10 kali atau lebih |
| E1 | W2 sampai W4 di S10: median dengan dan tanpa indeks (`varian`) | (tidak ada syarat; laporkan selisihnya) |
| E2 | kurva skala W1 sampai W6 | (tidak ada syarat; laporkan bentuk kurvanya) |

### 29.3 Bagian laporan

Tulis `docs\laporan_sofi.md` (bagian 5 Metode uji, 6 Hasil, dan 7 Analisis hipotesis dari kerangka laporan di [PANDUAN_Wildan.md](PANDUAN_Wildan.md), #30): metode (dari
`docs/rencana_uji.md`), tabel dan grafik, hipotesis, dan keterbatasan jujur: satu laptop; S100 memakai 20 titik pertama untuk W2 sampai W4; data S10 dan S100 hasil simulasi;
W9 dan W10 belum ada skripnya.

```powershell
git add docs results
git commit -m "[docs] hasil, grafik, dan evaluasi hipotesis"
git pull --rebase
git push
```

**Berhasil bila (#29)**

- [ ] tiga jenis grafik ada dan dapat dibaca; tiap angka punya sumber berkas
- [ ] H1 sampai H5 masing-masing memiliki keputusan yang beralasan atau "belum diuji"
- [ ] `docs/hipotesis.md` dan `docs/laporan_sofi.md` sudah di GitHub

**Pesan WhatsApp:** `[SELESAI] docs: evaluasi H1 sampai H5 selesai: H1 <diterima/ditolak>, H2 <...>, H3 <...>, H4 <...>, H5 <...>. Grafik dan tabel di docs/ dan results/.`
