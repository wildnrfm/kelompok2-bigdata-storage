# KONTRAK TEKNIS KELOMPOK 2 (sumber tunggal)

Semua panduan, kode, dan skrip memakai nama, jalur, port, kolom, dan perintah di dokumen ini **persis**.
Perlu menyimpang? Hentikan dan tulis `[KEPUTUSAN]` atau `[BLOKIR]` di grup; jangan menyimpang diam-diam.

Dataset: **Sen12Landslides** (Höhn dkk., Scientific Data 12:1772, DOI dataset 10.57967/hf/5883, CC BY 4.0).
Versi dokumen: 2 (menggantikan seluruh panduan lama yang memakai data SEN12TP; panduan lama tidak berlaku).
Tanggal: 25 Okt 2026.

## 0. Orang, akun, lokasi

| Panggilan | Nama lengkap | NIM | GitHub | Peran | Folder |
|---|---|---|---|---|---|
| Wildan | Muhammad Wildan Arif Maulana | 23051204065 | wildnrfm | Project Lead + Documentation/QA | `docs/`, `tests/`, berkas di akar |
| Syuep | Maulana Hidayah Syaif Ali Khan | 23051204068 | Syaifalikhan | Data Collection Engineer | `data/` |
| Elsa | Elsa Claudia Putri | 23051204038 | ElsaCP | Storage A (MongoDB) memimpin; Performance Analyst membantu | `mongodb/` |
| Sofi | Marsanda Sofi Aminarti | 23051204066 | marsandasofi | Performance Analyst memimpin; Storage A (MongoDB) membantu | `bench/`, `results/` |
| Levi | Muhammad Syah Levi | 23051204051 | SyahLev | Storage B (PostgreSQL/PostGIS + baseline HDFS-Parquet) | `postgis/`, `hdfs-parquet/` |

- Nama lengkap Syuep disusun dari urutan nama; Wildan mencocokkannya dengan data resmi saat mengisi `TEAM.md`.
- Repo: https://github.com/wildnrfm/kelompok2-bigdata-storage (privat).
- Folder lokal Windows (seragam): `C:\proyek\kelompok2-bigdata-storage`. Jangan di Desktop atau Documents bila
  OneDrive aktif. Mac/Linux: `~/proyek/kelompok2-bigdata-storage`.
- Semua perintah ditulis untuk **PowerShell** (Windows Terminal). Jangan memakai Git Bash untuk perintah `docker`
  (Git Bash mengubah jalur yang diawali `/`). Mac/Linux: perintahnya sama, ganti jalur dan `python` menjadi `python3`.
- Python: **3.12** (3.11 sampai 3.13 boleh). Perintah `python`; bila gagal coba `py`.
- Skrip data dan bench hanya memakai pustaka bawaan Python. Pustaka tambahan untuk uji:
  `python -m pip install pymongo "psycopg[binary]"` (Elsa, Sofi, Levi).
- Bahasa: Indonesia, sapaan "kamu". Sinkron 1 dan Sinkron 2 = dua panggilan grup; kickoff = panggilan 30 menit di awal.

## 1. Peta langkah global (nomor tetap; dipakai di semua panduan dan di grup)

| Fase | Langkah |
|---|---|
| 1. Siapkan repo | 1 repo (sudah ada; dikosongkan lalu diisi ulang) · 2 **Wildan: pasang paket, data mentah, uji, push** · 3 pasang alat (Syuep, Elsa, Sofi, Levi) · 4 clone + latihan Git (4 anggota) · 5 spesifikasi laptop (4 anggota) · 6 Wildan cek `TEAM.md` + jam kickoff · 7 **KICKOFF** (semua) |
| 2. Data dan penyimpanan | 8 Syuep: S1 di laptopnya + cocokkan checksum · 9 Elsa + Sofi: Docker MongoDB · 10 Levi: Docker PostGIS + skema · 11 Sofi + Elsa: harness, 100 titik tetap, wasit · 12 Levi: Docker HDFS + Spark |
| 3. Muat S1 | 13 Elsa + Sofi: muat S1 MongoDB, indeks, W3 · 14 Levi: muat S1 PostGIS, indeks, W3 · 15 Levi + Syuep: Parquet S1 di HDFS, W3 Spark SQL · 16 Syuep: S10 dan S100 + `CHECKSUMS.txt` · 17 Sofi + Elsa: harness W3 di ketiganya + banding jumlah · 18 **SINKRON 1** (semua) |
| 4. Pitching | 19 baca dokumen rancangan (semua) · 20 bahan slide ke Wildan (Syuep, Elsa, Levi, Sofi) · 21 Wildan: diagram draw.io · 22 Wildan: slide (6) · 23 tinjau silang (semua) · 24 latihan pitching = **SINKRON 2** (semua) |
| 5. Skala dan uji | 25 kueri W1 sampai W6 benar di S1 di ketiganya (Elsa, Sofi, Levi) · 26 muat S10 lalu S100 (Elsa, Sofi, Levi, Syuep) · 27 jalankan W1 sampai W8 (Sofi memimpin, Elsa membantu) · 28 uji silang jumlah hasil di S100 (Sofi, Elsa) |
| 6. Analisis | 29 tabel, grafik, hipotesis H1 sampai H5 (Sofi, Elsa) · 30 laporan + slide hasil (Wildan menyusun, semua menulis bagiannya) · 31 QA akhir + kumpul di SIDIA (Wildan) |

Tanda grup WhatsApp: `[SELESAI]`, `[BLOKIR]` (macet lebih dari 1 jam), `[KEPUTUSAN]`, `[Tinjau]`.
Fase 4 (pitching, #19 sampai #24) tidak butuh fase 2 dan 3; boleh dimajukan bila jadwal pitching dekat.

## 2. Susunan repo

```
kelompok2-bigdata-storage/
├─ README.md  TEAM.md  .gitignore  .gitattributes
├─ baca-dulu/        panduan .md: README, 00_ALUR_KERJA, KONTRAK, 01_PERSIAPAN_UMUM, PANDUAN_<nama>, PEMECAHAN_MASALAH
├─ latihan/<panggilan-huruf-kecil>.txt        latihan Git langkah #4 (satu berkas per orang)
├─ data/
│   ├─ raw/inventories.zip, splits_aligned.json, SHA256.txt      DI-COMMIT (± 23 MB)
│   ├─ convert_inventory.py, generate_scales.py, cek_data.py
│   ├─ CHECKSUMS.txt, KAMUS_DATA.md                              di-commit
│   └─ out/s1|s10|s100|batchN/                                   TIDAK di-commit (.gitignore)
├─ mongodb/       docker-compose.yml, indexes.js, drop_indexes.js, muat_pymongo.py, queries/_umum.js w1.js ... w6.js
├─ postgis/       docker-compose.yml, schema.sql, load.sql, indexes.sql, drop_indexes.sql, queries/w1.sql ... w6.sql
├─ hdfs-parquet/  docker-compose.yml, hadoop.env, csv_to_parquet.py, run_sql.py, sql/w1.sql ... w6.sql
├─ bench/         kueri.py, make_points.py, points.json, kebenaran.py, benar/, harness.py, compare_counts.py,
│                 summarize.py, catat.py
├─ results/       CSV hasil uji (nama berisi tanggal), pengukuran_<penyimpanan>.csv, ringkasan.csv, banding.csv
├─ tests/         uji_semua.py, buat_data_uji.py, fake_db.js, stubs/ (pustaka tiruan; tanpa Docker)
└─ docs/          arsitektur, slide, laporan
```

Kode awal sudah ada setelah `git pull --rebase` (Wildan memasukkannya di #2). Bila sesuatu belum ada, tulis `[BLOKIR]`.

## 3. Kontrak data (rinci kolom ada di `data/KAMUS_DATA.md`)

- **Masukan** (di `data/raw/`, hanya dibaca): `inventories.zip` (74.956 poligon, 15 atribut) dan
  `splits_aligned.json` (4.392 entri patch: train, val, test). `SHA256.txt` memuat checksum keduanya.
- **Keluaran konversi** `python data/convert_inventory.py` → `data/out/s1/`, empat berkas dengan isi setara:

| Berkas | Dipakai oleh | Isi |
|---|---|---|
| `annotations.ndjson` | MongoDB | satu dokumen per baris; `_id` = `ann_id`; tanggal `{"$date": ...}`; `center` GeoJSON Point; `bbox` GeoJSON Polygon; field kosong tidak ditulis |
| `annotations.csv` | PostGIS dan Spark | 23 kolom: `ann_id, location, inventory, event_type, type, velocity_c, author, reference, event_conf, area, pre_date, event_date, post_date, pre_dt2, event_dt2, post_dt2, center_lon, center_lat, bbox_min_lon, bbox_min_lat, bbox_max_lon, bbox_max_lat, sim_batch` |
| `patches.ndjson` | MongoDB | `_id` = `patch_id`; `paths` {s2, s1asc, s1dsc}; `pixel_annotated`; `sim_batch` |
| `patches.csv` | PostGIS dan Spark | 8 kolom: `patch_id, split, inventory, s2_path, s1asc_path, s1dsc_path, pixel_annotated, sim_batch` |

- **Yang disimpan**: metadata, titik pusat (centroid berbobot luas), dan kotak pembatas; **bentuk poligon tidak disimpan**.
  Koordinat 7 desimal, EPSG:4326 (dugaan; `.prj` tanpa kode EPSG). Tanggal ISO `YYYY-MM-DD`.
- **Pemeriksaan diri konverter**: pada data asli, hasil dicocokkan dengan `laporan_inventaris.txt` (22 Okt 2026):
  jumlah, sebaran lokasi dan pemicu, rentang tanggal dan luas, koordinat, patch per split dan inventaris.
  Keluar kode 0 = LOLOS; 2 = masukan tidak ada atau rusak; 3 = ada angka yang beda (**jangan lanjut; `[BLOKIR]`**).
- **Skala** (bersarang; S1 awalan S10, S10 awalan S100; seed tetap **20261023**):

| Skala | Anotasi | Patch | Folder | Dibuat oleh |
|---|---|---|---|---|
| S1 | 74.956 | 4.392 | `data/out/s1` | `python data/convert_inventory.py` |
| S10 | 749.560 | 43.920 | `data/out/s10` | `python data/generate_scales.py --scale S10` |
| S100 | 7.495.600 | 439.200 | `data/out/s100` | `python data/generate_scales.py --scale S100` (3 sampai 6 menit, 7,84 GB) |

- `ann_id` = `id` asli + 74.956 × b (b = nomor batch), berurutan dari 0; `sim_batch` = b; `patch_id` untuk b ≥ 1 diberi akhiran `_r<b>`.
- Perkiraan ukuran berkas: S1 78 MB, S10 781 MB, S100 7,84 GB (diukur pada data tiruan berbentuk laporan asli).
- Checksum (SHA-256): `data/raw/SHA256.txt` (berkas asli) dan `data/CHECKSUMS.txt` (hasil S1, S10, S100).
  `python data/cek_data.py --raw` dan `python data/generate_scales.py --verify` memeriksanya; berkas yang belum dibuat dilewati.
- Pemeriksa hasil: `python data/cek_data.py --skala S1` (juga S10, S100; `--cepat` melewati NDJSON). Harus berakhir
  `SEMUA PEMERIKSAAN LULUS`.
- Batch tambahan untuk W8: `python data/generate_scales.py --extra-batch 100` → `data/out/batch100/` (74.956 anotasi,
  `ann_id` 7.495.600 sampai 7.570.555, dan 4.392 patch).

## 4. Docker (nama tetap; **satu penyimpanan aktif sekali waktu**)

Perintah umum dari folder masing-masing: `docker compose up -d`, `docker compose ps`, `docker compose logs --tail 50`,
`docker compose stop` (data tetap), `docker compose down` (hapus kontainer; MongoDB dan PostGIS: data tetap; **HDFS: data ikut hilang**),
`docker compose down -v` (hapus semua termasuk data). Berkas compose memakai sintaks modern (tanpa `version:`).
Semua kontainer memasang `../data` di `/sen12ls-data` (hanya baca).

| Penyimpanan | Folder | Kontainer | Image | Port host | Catatan |
|---|---|---|---|---|---|
| MongoDB | `mongodb/` | `sen12ls-mongo` | `mongo:8` | 27017 | DB `sen12ls`, koleksi `annotations` dan `patches`; `./` di `/scripts`; cache WiredTiger 0,5 GB; volume `mongo_data` |
| PostGIS | `postgis/` | `sen12ls-postgis` | `postgis/postgis:17-3.5` | 5433 → 5432 | DB `sen12ls`, user `postgres`, sandi uji `postgres`; `./` di `/sql`; volume `pg_data`; `shared_buffers=256MB` |
| HDFS | `hdfs-parquet/` | `sen12ls-namenode`, `sen12ls-datanode1`, `sen12ls-datanode2` | `apache/hadoop:3.5.0` | 9870 (UI) | konfigurasi di `hadoop.env`, replikasi 2 |
| Spark | `hdfs-parquet/` | `sen12ls-spark` | `spark:3.5.0-python3` | 4040 (UI saat job jalan) | `sleep infinity`, `user 0:0`; memasang `../bench:/bench:ro`, `../results:/results`, `./:/hdfs-parquet:ro`; mode `local[2]` |

- Jalur Parquet: `hdfs://namenode:8020/data/sen12ls/parquet/{s1,s10,s100}/{annotations,patches}` (ZSTD).
- Tunggu 30 sampai 60 detik setelah `up -d` sampai `docker exec sen12ls-namenode hdfs dfsadmin -report` menunjukkan 2 datanode hidup.
- Windows: batasi memori WSL lewat `C:\Users\<nama>\.wslconfig` (`[wsl2]`, `memory=6GB`, `processors=2`), lalu `wsl --shutdown`.

## 5. Perintah muat dan indeks (PowerShell, dari mana saja)

Ganti `s1` dengan `s10` atau `s100` untuk skala lain. **Tulis `python bench\catat.py ukur ...` di depan** perintah
muat atau indeks supaya waktunya tercatat otomatis (lihat bagian 6).

**MongoDB**
```
docker exec sen12ls-mongo mongoimport --db sen12ls --collection annotations --drop --file /sen12ls-data/out/s1/annotations.ndjson
docker exec sen12ls-mongo mongoimport --db sen12ls --collection patches --drop --file /sen12ls-data/out/s1/patches.ndjson
docker exec sen12ls-mongo mongosh --quiet --file /scripts/indexes.js
```
- **Jangan** memakai `--jsonArray`. Bila `mongoimport` tidak ada di kontainer, pakai cadangan:
  `python mongodb\muat_pymongo.py --skala S1` (lebih lambat; cukup untuk S1 dan S10).
- Indeks: `center` 2dsphere, `bbox` 2dsphere, `dates.event`, `{event_type, dates.event}`, `{location, dates.event}`; patches: `{inventory, split}`.
- Tanpa indeks (eksperimen E1): `docker exec sen12ls-mongo mongosh --quiet --file /scripts/drop_indexes.js`.

**PostgreSQL/PostGIS**
```
docker exec sen12ls-postgis psql -U postgres -d sen12ls -f /sql/schema.sql
docker exec sen12ls-postgis psql -U postgres -d sen12ls -v folder=/sen12ls-data/out/s1 -f /sql/load.sql
docker exec sen12ls-postgis psql -U postgres -d sen12ls -f /sql/indexes.sql
```
- `schema.sql` menghapus dan membuat ulang tabel `annotations` (`center geometry(Point,4326)`, `bbox geometry(Polygon,4326)`) dan `patches`.
- `load.sql`: `COPY` ke tabel sementara, lalu `INSERT ... ST_MakePoint`, `ST_MakeEnvelope`; mengosongkan tabel dulu kecuali ada `-v tambah=1`.
- Indeks: GiST pada `center` dan `bbox`; btree `event_date`, `(event_type, event_date)`, `(location, event_date)`; patches `(inventory, split)`; lalu `VACUUM ANALYZE`.
- Tanpa indeks (E1): `... -f /sql/drop_indexes.sql`.

**HDFS + Parquet + Spark SQL**
```
docker exec sen12ls-spark /opt/spark/bin/spark-submit --master "local[2]" --driver-memory 2g /hdfs-parquet/csv_to_parquet.py --scale S1
```
- Membaca CSV di `/sen12ls-data/out/s1`, menulis Parquet ZSTD ke HDFS, lalu membaca ulang dan mencocokkan jumlah baris.
- Bila ZSTD ditolak: tambahkan `--kompresi snappy` dan catat di laporan.

**Tambah batch (W8)**, setelah S100 termuat dan `python data\generate_scales.py --extra-batch 100`:
- MongoDB: `mongoimport` yang sama tanpa `--drop`, `--file /sen12ls-data/out/batch100/annotations.ndjson` (juga patches).
- PostGIS: `... -v folder=/sen12ls-data/out/batch100 -v tambah=1 -f /sql/load.sql`.
- Spark: `... csv_to_parquet.py --scale S100 --folder /sen12ls-data/out/batch100 --tambah`.
- Setelah itu jumlah baris S100 berubah (7.570.556); lakukan W8 **paling akhir**, atau muat ulang S100.

## 6. Beban kerja uji dan hasil (kontrak `bench/`)

Semua definisi kueri ada **satu tempat**: `bench/kueri.py` (dipakai MongoDB, PostGIS, dan Spark supaya ketiganya
menjawab pertanyaan yang sama). Satu "kueri" = satu titik dari `bench/points.json` (W2 sampai W4) atau satu `ann_id` (W1).

| Kode | Beban kerja | Penyimpanan | Status |
|---|---|---|---|
| W1 | ambil satu anotasi menurut `ann_id` (100 id tetap); konkurensi 1, 10, 50, 100 lewat `--clients` | ketiganya (klien banyak: MongoDB dan PostGIS) | ada skrip |
| W2 | jumlah anotasi yang **titik pusatnya** ada di jendela ±0,01° (sekitar 1,1 km) di sekitar titik uji | ketiganya | ada skrip |
| W3 | seperti W2 dan `event_date` dalam ±30 hari dari tanggal titik uji | ketiganya | ada skrip |
| W4 | jumlah anotasi yang **kotak pembatasnya** beririsan dengan jendela ±0,1° (sekitar 22 km), `event_type` tertentu, `event_conf` ≥ 0,9 | ketiganya | ada skrip |
| W5 | jumlah anotasi per `event_type` dan tahun kejadian (jumlah_hasil = jumlah kelompok) | ketiganya | ada skrip |
| W6 | jumlah patch per `inventory` dan `split`, plus rata-rata `pixel_annotated` (jumlah_hasil = jumlah kelompok) | ketiganya | ada skrip |
| W7 | muat massal S1, S10, S100: waktu muat, waktu bangun indeks, ukuran di disk | ketiganya | `bench/catat.py` |
| W8 | tambah satu batch baru (batch100) ke S100: waktu | ketiganya | `bench/catat.py` + perintah bagian 5 |
| W9 | beban campuran 90% baca dan 10% tulis, 5 menit, 50 klien | MongoDB, PostGIS | **belum ada skrip** (Tugas Tengah Semester) |
| W10 | uji kegagalan (matikan DataNode, dst.) | masing-masing | **belum ada skrip** (Tugas Tengah Semester, opsional) |

- Semua perbandingan memakai batas tertutup. Batas jendela **digeser setengah langkah** dari kisi 1e-7° tempat semua koordinat
  data berada, jadi tidak ada titik tepat di tepi jendela: MongoDB (bola), PostGIS dan Spark (bidang datar) **harus** memberi
  jumlah sama persis. Selisih berarti ada yang salah, bukan efek tepi.
- `bench/points.json` (dibuat `python bench/make_points.py` dari `data/out/s1/annotations.csv`, seed 20261023, **di-commit**):
  `{"seed", "parameter", "points": [{id, lon, lat, date_from, date_to, event_type, inside, ann_id, location}]}`.
  100 titik: 70 "di dalam" (titik pusat anotasi nyata yang punya `event_date`, dipilih bergilir menurut 16 lokasi,
  dijamin minimal satu hasil) dan 30 "di luar" (minimal 1° dari titik pusat mana pun, dijamin kosong).
- **Wasit jawaban benar**: `python bench/kebenaran.py --skala S1 --tulis` menghitung jumlah yang seharusnya langsung dari
  `annotations.csv` (tanpa database) dan menulis `bench/benar/W*_S1.csv` (di-commit untuk S1). `compare_counts.py`
  memakainya otomatis.
- Pagar anti salah label (jumlah baris sebelum uji): S1 74.956 anotasi dan 4.392 patch; S10 749.560 dan 43.920;
  S100 7.495.600 dan 439.200. Beda = berhenti, kecuali `--force`.
- Kolom CSV hasil (satu baris = satu eksekusi kueri; median, p95, QPS dihitung belakangan):
  `penyimpanan,beban_kerja,skala,ulangan,cold_warm,kueri_id,waktu_ms,jumlah_hasil,catatan`
  - `penyimpanan` ∈ {mongodb, postgis, spark}; `beban_kerja` ∈ {W1..W6}; `skala` ∈ {S1, S10, S100}; `ulangan` 1..N;
    `cold_warm` ∈ {cold, warm}; `kueri_id` = `id` titik (W2 sampai W4), nomor urut 1..100 (W1), atau 1 (W5, W6);
    `waktu_ms` desimal 3 angka; `jumlah_hasil` bilangan bulat (**-1 = kueri itu galat**); `catatan` teks bebas
    (W1 banyak klien: `konkurensi=N`, diisi otomatis; uji varian seperti E1: tulis `--note "varian=tanpa-indeks"` supaya
    `summarize.py` memisahkannya dari hasil biasa).
- Nama berkas: `results/YYYYMMDD_<penyimpanan>_<beban>_<skala>.csv`; bila sudah ada ditambah `_2`, `_3`.
- **Harness**: `python bench/harness.py --store {mongodb|postgis|spark} --workload {W1..W6} --scale {S1|S10|S100}`
  `[--repeats 3] [--cold-warm warm|cold] [--first-run-no 1] [--clients N] [--limit-titik N] [--note TEKS] [--force]`.
  Warm = satu putaran pemanasan (tidak dicatat) lalu N ulangan dicatat. Cold = tanpa pemanasan (nyalakan ulang kontainer dulu).
  Untuk `spark`, harness memanggil `docker exec sen12ls-spark ... run_sql.py` dengan argumen yang sama.
  Koneksi: Mongo `mongodb://localhost:27017` (db `sen12ls`); PostGIS `host=localhost port=5433 dbname=sen12ls user=postgres password=postgres`.
- **Pembanding**: `python bench/compare_counts.py results/A.csv [results/B.csv [results/C.csv]]` membandingkan `jumlah_hasil`
  per `kueri_id` antar berkas **dan** dengan wasit; satu berkas = dibandingkan dengan wasit saja (cara tiap orang memeriksa
  hasilnya sendiri); keluar 0 bila semua sama, 1 bila ada yang beda, 2 bila masukan tidak bisa dipakai.
- **Ringkasan**: `python bench/summarize.py` → `results/ringkasan.csv` dan `results/banding.csv` (median per penyimpanan berjajar).
- **Catat waktu dan ukuran (W7, W8)** (satu berkas per penyimpanan, supaya tidak bentrok di Git):
  - `python bench/catat.py ukur --store mongodb --skala S1 --jenis muat --objek annotations <perintah>` menjalankan perintah,
    mengukur, dan mencatat bila berhasil. `--jenis` ∈ {muat, indeks, tambah_batch}.
  - `python bench/catat.py ukuran --store {mongodb|postgis|spark|mentah} --skala S1` mengukur ukuran di disk otomatis lewat `docker exec`.
  - `python bench/catat.py tampil` menampilkan tabel banding semua penyimpanan (MiB dan detik).
  - Hasil: `results/pengukuran_<penyimpanan>.csv` (kolom `tanggal,penyimpanan,skala,jenis,objek,nilai,satuan,catatan`).
- Aturan uji: minimal 3 ulangan; satu penyimpanan aktif sekali waktu; memori dibatasi (bagian 4); jumlah hasil W1 sampai W6
  diuji silang dengan wasit; jangan menjalankan uji saat laptop dipakai hal berat lain.

## 7. Hipotesis dan eksperimen (dugaan awal, **belum diuji**)

| Kode | Hipotesis | Ditolak bila |
|---|---|---|
| H1 | Dengan indeks spasial, MongoDB dan PostGIS lebih cepat daripada baseline Parquet pada W2 dan W3, dan selisihnya melebar dari S1 ke S100 | selisih mengecil atau terbalik |
| H2 | Pada W4 (kotak pembatas + atribut), PostGIS lebih cepat daripada MongoDB | MongoDB sama cepat atau lebih cepat |
| H3 | Ukuran di disk dari kecil ke besar: Parquet (ZSTD), PostGIS, MongoDB (termasuk indeks) | urutannya berbeda |
| H4 | Pada W5 dan W6 di S100 (agregasi seluruh tabel), Spark SQL atas Parquet lebih cepat daripada MongoDB | MongoDB lebih cepat |
| H5 | Pada W1 dengan 50 klien di S100, p95 MongoDB dan PostGIS kurang dari 10 kali p95 satu klien | p95 10 kali lipat atau lebih |

- **E1**: ulangi W2 sampai W4 dengan dan tanpa indeks (`drop_indexes.js`, `drop_indexes.sql`).
- **E2**: kurva skala, W1 sampai W6 di S1, S10, S100 (inti Tugas Tengah Semester).
- E3 (opsional): Parquet acak versus diurutkan menurut `location`. E4 (opsional): PostGIS `geography` versus `geometry`. Belum ada skrip.

## 8. Git

- Alur: `git pull --rebase` → `git add <folder sendiri>` → `git commit -m "[folder] pesan"` → `git pull --rebase` → `git push`.
  **Jangan `--force`.**
- Awalan commit: `[data]` `[mongodb]` `[postgis]` `[hdfs-parquet]` `[bench]` `[results]` `[docs]` `[latihan]`; berkas di akar dan `tests/`: `[root]`.
- `results/` boleh diisi siapa pun yang menjalankan uji (nama berkas unik berisi tanggal dan penyimpanan); Sofi yang mengelola isinya.
- Konflik: buka berkas, putuskan isi akhirnya, hapus penanda `<<<<<<<`, `=======`, `>>>>>>>`, `git add <berkas>`,
  `git rebase --continue`, `git push`. Ragu: `git rebase --abort` lalu `[BLOKIR]`.
- Pengaturan awal sekali: `git config --global user.name "Nama"`, `git config --global user.email "email"`, `git config --global pull.rebase true`.
- Login GitHub: saat clone atau push pertama, jendela browser terbuka (Git Credential Manager); masuk dengan akun GitHub-mu.
- Latihan #4: buat `latihan/<panggilan-huruf-kecil>.txt` berisi satu kalimat; commit `[latihan] Nama: uji coba push`.
- **Tidak boleh di repo:** `data/out/` (data besar), sandi, token, data pribadi, folder `cek-sen12ls/` (alat pemeriksaan awal Wildan).
  Sandi uji `postgres` hanya untuk database di laptop sendiri.

## 9. Format kabar

- WhatsApp: `[SELESAI] <folder>: <apa>` · `[BLOKIR] <apa yang dicoba + pesan galat lengkap> @nama` · `[KEPUTUSAN] <hal yang disepakati>`
  · `[Tinjau] @nama - <bagian> - <temuan> - Saran: <perbaikan>`.
- Check-in malam: `Hari ini: ... / Besok: ... / Kendala: ...`.

## 10. Yang sudah dibuktikan dan yang belum (baca sebelum percaya angka)

**Sudah dibuktikan** (`python tests/uji_semua.py`, tanpa Docker): konverter dan pemeriksa data pada data tiruan berbentuk laporan
asli; generator S10 dan S100 deterministik dan bersarang; kode harness, pemuat, pembanding, ringkasan, dan pencatat berjalan dari
ujung ke ujung; definisi kueri W1 sampai W6 memberi jumlah yang sama di MongoDB, PostGIS, dan Spark **tiruan** dan wasit.
Selain itu skrip psql PostGIS (`schema.sql`, `load.sql`, `indexes.sql`, `drop_indexes.sql`, `queries/w1.sql` sampai `w6.sql`) dan teks SQL
`SQL_POSTGIS` di `bench/kueri.py` sudah dijalankan di **PostgreSQL 16 sungguhan** dengan tiruan fungsi spasial planar: hasil W1 sampai W6
sama dengan wasit pada 100 titik uji (data tiruan berbentuk laporan asli).

**Belum dibuktikan** (dibuktikan oleh kita saat mengerjakan langkahnya):

1. Konversi pada data asli: pemeriksaan diri konverter yang menentukan (kode 0 = cocok dengan laporan 22 Okt 2026).
2. Perintah Docker sungguhan: nama image, `mongoimport` di `mongo:8`, HDFS dan Spark (SQL dan psql PostGIS sudah diuji di PostgreSQL biasa,
   tetapi **PostGIS sendiri** (tipe `geometry`, `ST_Intersects`, indeks GiST) belum pernah dijalankan).
3. Kesamaan jumlah MongoDB (bola) dan PostGIS/Spark (bidang datar) pada W4; jendela sudah digeser dari tepi, tetapi
   hanya uji sungguhan yang memastikan (`compare_counts.py`).
4. Semua angka waktu dan ukuran di disk (belum ada yang diukur).
5. Arti kolom `*_dt2`, satuan `area`, dan EPSG:4326 (dugaan, tercatat di kamus data).
