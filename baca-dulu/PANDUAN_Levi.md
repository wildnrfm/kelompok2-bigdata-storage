# Panduan Levi (Storage B: PostgreSQL/PostGIS dan baseline HDFS-Parquet)

Folder milikmu: `postgis/` dan `hdfs-parquet/`. Kamu memimpin **dua penyimpanan**:

- **PostGIS**: basis data relasional dengan tipe `geometry` dan indeks spasial GiST.
- **Baseline HDFS + Parquet**: berkas kolumnar di HDFS yang dibaca Spark SQL, **tanpa** indeks spasial. Fungsinya mengukur seberapa besar
  keuntungan indeks spasial (H1) dan seberapa kuat agregasi seluruh tabel (H4).

Hal umum (terminal, Git, Docker, VS Code) ada di [01_PERSIAPAN_UMUM.md](01_PERSIAPAN_UMUM.md); peta seluruh pekerjaan di
[00_ALUR_KERJA.md](00_ALUR_KERJA.md); nama dan perintah baku di [KONTRAK.md](KONTRAK.md) (terutama **bagian 4 sampai 6**); arti kolom di
[../data/KAMUS_DATA.md](../data/KAMUS_DATA.md).

> **Yang sudah dibuktikan dan yang belum.** Skrip PostGIS (`schema.sql`, `load.sql`, `indexes.sql`, `drop_indexes.sql`, `queries/w1.sql` sampai `w6.sql`)
> sudah dijalankan di **PostgreSQL 16 sungguhan** dengan tiruan fungsi spasial planar: muat 74.956 anotasi dan 4.392 patch berhasil, kedelapan indeks terbentuk,
> dan hasil W1 sampai W6 sama dengan wasit pada 70 titik uji. Yang **belum pernah dijalankan** adalah PostGIS-nya sendiri (tipe `geometry`, `ST_Intersects`,
> indeks GiST), semua perintah `docker`, dan seluruh sisi HDFS dan Spark (`hdfs-parquet/`). Kamulah yang pertama membuktikannya. Bila ada yang gagal,
> itu temuan berharga: tulis `[BLOKIR]` dengan pesan galat lengkap. Memperbaiki berkas di `postgis/` dan `hdfs-parquet/` adalah hakmu
> (commit `[postgis] ...` atau `[hdfs-parquet] ...`), tetapi **jangan mengubah definisi kueri atau jendela supaya "cocok"**.

## Peta langkahmu

| # | Langkah | Menunggu | Perkiraan waktu | Membuka |
|---|---|---|---|---|
| 3 | Pasang alat (Git, Python, VS Code, **Docker**) + pustaka `psycopg` | - | 30 sampai 60 menit | #4 |
| 4 | Clone repo dan latihan Git | #2 (Wildan) dan #3 | 15 sampai 20 menit | #6 |
| 5 | Tulis spesifikasi laptop di grup | - | 5 menit | #7 |
| 7 | KICKOFF | #6 | 30 menit | #10 |
| **10** | **Docker PostGIS dan skema** | #7 | 30 sampai 45 menit | #12, #14 |
| **12** | **Docker HDFS dan Spark** | #10 | 45 sampai 90 menit | #15 |
| **14** | **Muat S1 ke PostGIS, indeks, W3** | #8 (Syuep) dan #10 | 30 sampai 45 menit | #17 |
| **15** | **Parquet S1 di HDFS dan W3 Spark SQL** (kamu memimpin, Syuep mendampingi) | #8 dan #12 | 45 sampai 60 menit | #17 |
| **17** | **Kirim CSV W3 PostGIS dan Spark** (Sofi membandingkan) | #11, #14, #15 | 15 menit | #18 |
| 18 | SINKRON 1 | #17 | 30 sampai 45 menit | #25 |
| 19 | Baca dokumen rancangan | #7 | 45 menit | #20 |
| 20 | Bahan slide 4 (bagian PostGIS dan baseline) | #19 | 30 menit | #22 |
| 23 | Tinjau silang (dengan Elsa) | #22 | 45 menit | #24 |
| 24 | Latihan pitching (SINKRON 2) | #23 | 45 sampai 60 menit | - |
| **25** | **W1 sampai W6 benar di S1 di PostGIS dan Spark** | #18 | 2 sampai 3 jam | #26 |
| **26** | **Muat S10 lalu S100 di PostGIS dan HDFS-Parquet** (laptop uji) | #16 (Syuep) dan #25 | beberapa jam, sebagian besar menunggu | #27 |
| 27 | Membantu Sofi menjalankan W1 sampai W8 (sisi PostGIS dan Spark) | #26 | menyesuaikan | #28 |
| 28 | Membantu uji silang jumlah hasil di S100 | #27 | 1 jam | #29 |
| 29 | Menulis bagian PostGIS dan baseline untuk laporan | #28 | 2 sampai 3 jam | #30 |

---

## Aturan kerja di laptopmu: satu penyimpanan menyala sekali waktu

PostGIS ringan; HDFS + Spark **paling berat** (empat kontainer). Menyalakan keduanya bersamaan membuat laptop lambat dan hasil ukur tidak adil. Pindah seperti ini
(`stop` menyimpan data; **`down` pada HDFS menghapus datanya**):

| Mau bekerja di | Matikan dulu | Lalu nyalakan |
|---|---|---|
| PostGIS | `cd hdfs-parquet` lalu `docker compose stop` | `cd postgis` lalu `docker compose up -d` |
| HDFS + Spark | `cd postgis` lalu `docker compose stop` | `cd hdfs-parquet` lalu `docker compose up -d`, **tunggu 30 sampai 60 detik** |

Sebelum mulai, selalu `docker ps` dan pastikan hanya penyimpanan yang kamu pakai yang tampil. Urutan yang paling hemat pindah: **#10, lalu #14 (PostGIS tuntas), lalu #12 dan #15 (HDFS dan Spark)**;
kerjakan #12 lebih dulu hanya bila #8 (Syuep) belum selesai dan kamu menunggu.

---

## #3, #4, #5. Alat, clone, spesifikasi

- **#3 Pasang alat:** [01_PERSIAPAN_UMUM.md](01_PERSIAPAN_UMUM.md) bagian A2, **termasuk Docker Desktop dan `.wslconfig`** (memori WSL 6 GB, 2 prosesor), lalu pustaka Python:

  ```powershell
  python -m pip install "psycopg[binary]" pymongo
  ```

- **#4 Clone dan latihan Git:** setelah Wildan menulis `[SELESAI] root: paket awal sudah di GitHub`, jalankan (bagian A3):

```powershell
mkdir C:\proyek
cd C:\proyek
git clone https://github.com/wildnrfm/kelompok2-bigdata-storage.git
cd kelompok2-bigdata-storage
git pull --rebase
New-Item -ItemType Directory -Force latihan | Out-Null
Set-Content latihan\levi.txt "Halo, ini latihan Levi"
git add latihan/levi.txt
git commit -m "[latihan] Levi: uji coba push"
git pull --rebase
git push
```

Tulis di grup: `[SELESAI] latihan: clone dan push berhasil (latihan/levi.txt) - Levi`. Periksa baris namamu di `TEAM.md`
(username `SyahLev`).

- **#5 Spesifikasi:** bagian A4; tulis di grup. HDFS + Spark butuh memori; sebutkan RAM dan disk kosongmu dengan jujur supaya laptop uji S100 dipilih dengan benar.

---

## #10. Docker PostGIS dan skema

**Tujuan.** PostgreSQL 17 + PostGIS 3.5 berjalan di Docker dengan nama dan port yang tetap, dan tabel `annotations` serta `patches` sudah ada (kosong, tanpa indeks).

**Menunggu:** kickoff (#7). Docker Desktop harus sudah **Engine running**.

### 10.1 Pastikan tidak ada penyimpanan lain yang aktif

```powershell
cd C:\proyek\kelompok2-bigdata-storage
git pull --rebase
docker ps
```

Daftar harus kosong dari container `sen12ls-*` lain. Bila ada, matikan di foldernya (`docker compose stop`).

### 10.2 Nyalakan PostGIS

```powershell
cd postgis
docker compose up -d
docker compose ps
```

Pertama kali, Docker mengunduh image `postgis/postgis:17-3.5` (ratusan MB; 2 sampai 10 menit). **Jangan membuat berkas `.env`**: sandi uji `postgres` sudah menjadi bawaan di
`docker-compose.yml` dan harness memakainya.

Contoh hasil:

```text
NAME              IMAGE                    COMMAND                  SERVICE   CREATED          STATUS          PORTS
sen12ls-postgis   postgis/postgis:17-3.5   "docker-entrypoint.s..."  postgis   30 seconds ago   Up 29 seconds   0.0.0.0:5433->5432/tcp
```

Tunggu sampai server siap (10 sampai 30 detik pada start pertama):

```powershell
docker compose logs --tail 5
```

Baris terakhir harus memuat `database system is ready to accept connections`.

### 10.3 Buat tabel

```powershell
docker exec sen12ls-postgis psql -U postgres -d sen12ls -f /sql/schema.sql
```

Contoh hasil (bentuknya; baris `NOTICE` boleh ada atau tidak, itu bukan galat):

```text
psql:/sql/schema.sql:6: NOTICE:  extension "postgis" already exists, skipping
CREATE EXTENSION
psql:/sql/schema.sql:8: NOTICE:  table "annotations" does not exist, skipping
DROP TABLE
psql:/sql/schema.sql:9: NOTICE:  table "patches" does not exist, skipping
DROP TABLE
CREATE TABLE
CREATE TABLE
```

Skrip ini **menghapus dan membuat ulang** kedua tabel (beserta indeksnya), jadi aman diulang dan dipakai tiap kali berganti skala.

### 10.4 Uji enam hal

```powershell
docker exec sen12ls-postgis psql -U postgres -d sen12ls -Atc "select version()"
docker exec sen12ls-postgis psql -U postgres -d sen12ls -Atc "select postgis_version()"
docker exec sen12ls-postgis psql -U postgres -d sen12ls -Atc "show shared_buffers"
docker exec sen12ls-postgis ls /sen12ls-data /sql
docker exec sen12ls-postgis psql -U postgres -d sen12ls -c "\dt"
docker exec sen12ls-postgis psql -U postgres -d sen12ls -c "\d annotations"
```

Contoh hasil (versi persisnya berbeda):

```text
PostgreSQL 17.x (Debian 17.x-...) on x86_64-pc-linux-gnu, compiled by gcc ..., 64-bit
3.5 USE_GEOS=1 USE_PROJ=1 USE_STATS=1
256MB
/sen12ls-data:
CHECKSUMS.txt  KAMUS_DATA.md  cek_data.py  ...  out  raw

/sql:
docker-compose.yml  drop_indexes.sql  indexes.sql  load.sql  queries  schema.sql
             List of relations
 Schema |      Name       | Type  |  Owner
--------+-----------------+-------+----------
 public | annotations     | table | postgres
 public | patches         | table | postgres
 public | spatial_ref_sys | table | postgres
```

Perintah terakhir (`\d annotations`) harus menampilkan, di antara kolom lain, `center | geometry(Point,4326) | not null` dan `bbox | geometry(Polygon,4326) | not null`,
serta `annotations_pkey` pada `ann_id`. Artinya berurutan: versi PostgreSQL; **PostGIS 3.5 aktif**; `shared_buffers` dibatasi 256 MB; folder `data/` terpasang di
`/sen12ls-data` dan folder `postgis/` di `/sql`; tabel ada dengan tipe geometri yang benar.

### 10.5 Uji sambungan dari Python (jalur yang dipakai harness)

```powershell
cd ..
python -c "import psycopg; c = psycopg.connect('host=localhost port=5433 dbname=sen12ls user=postgres password=postgres'); print(c.execute('select postgis_version()').fetchone()[0])"
docker stats --no-stream
```

Contoh hasil: `3.5 USE_GEOS=1 USE_PROJ=1 USE_STATS=1`, lalu tabel pemakaian memori (PostGIS kosong memakai sedikit).

**Berhasil bila (#10)**

- [ ] `docker compose ps` menampilkan `sen12ls-postgis` berstatus `Up` dengan port `5433->5432`
- [ ] `postgis_version()` menjawab `3.5 ...` dan `shared_buffers` = `256MB`
- [ ] `/sen12ls-data` dan `/sql` terisi (pemasangan folder berhasil)
- [ ] `\d annotations` menunjukkan `geometry(Point,4326)` dan `geometry(Polygon,4326)`
- [ ] Python berhasil terhubung dari Windows (port 5433)

**Pesan WhatsApp**

```text
[SELESAI] postgis: PostGIS 3.5 jalan di Docker (sen12ls-postgis, port 5433), shared_buffers 256MB, tabel annotations dan patches dibuat,
koneksi dari Python berhasil. Siap memuat S1 (#14) setelah Syuep selesai #8.
```

### Kalau macet

| Tanda | Penyebab dan cara memperbaiki |
|---|---|
| `Bind for 0.0.0.0:5433 failed: port is already allocated` | Ada program lain di port 5433 (container lain atau PostgreSQL Windows yang kamu atur ke 5433). `docker ps`; matikan yang bentrok. Port 5432 milik PostgreSQL Windows tidak bentrok. |
| `/sen12ls-data` atau `/sql` kosong | Pemasangan folder gagal. Pastikan repo ada di `C:\proyek` dan Docker Desktop > Settings > Resources > File sharing mengizinkan drive C. Lalu `docker compose down` dan `docker compose up -d` lagi. |
| `password authentication failed for user "postgres"` | Volume `pg_data` dibuat saat sandinya berbeda. Pakai `docker compose down -v` (**menghapus data PostGIS**; belum ada yang berharga di langkah ini), lalu `up -d` lagi dan ulangi 10.3. Jangan memakai `.env`. |
| `could not open shared memory segment` atau container `Exited` | `docker compose logs --tail 50`; salin pesannya ke `[BLOKIR]`. Penyebab umum: memori WSL terlalu kecil (`.wslconfig`, A2) atau disk penuh. |
| `extension "postgis" is not available` | Image yang terunduh salah (bukan `postgis/postgis`). `docker compose config` harus menampilkan `image: postgis/postgis:17-3.5`. |
| `Error response from daemon: ... no matching manifest` | Arsitektur CPU tidak cocok dengan image. `[BLOKIR]` dengan hasil `docker version`. |
| Python: `connection refused` atau `timeout expired` | Container belum siap (tunggu 10 detik) atau port berbeda. `docker compose ps` harus menunjukkan `0.0.0.0:5433->5432`. |

---

## #12. Docker HDFS dan Spark

**Tujuan.** Satu NameNode, dua DataNode (replikasi 2), dan satu container Spark berjalan; Spark bisa membaca dan menulis HDFS.

**Menunggu:** #10 (dan #14 bila kamu mengikuti urutan hemat pindah di atas). Ini langkah **paling berat**: mulai lebih awal dan sabar.

### 12.1 Matikan PostGIS, nyalakan HDFS dan Spark

```powershell
cd C:\proyek\kelompok2-bigdata-storage
git pull --rebase
cd postgis
docker compose stop
cd ..\hdfs-parquet
docker ps
docker compose up -d
docker compose ps
```

`docker ps` sebelum `up` harus kosong dari container `sen12ls-*`. Pertama kali, Docker mengunduh `apache/hadoop:3.5.0` dan `spark:3.5.0-python3` (beberapa GB; 5 sampai 20 menit).

Contoh hasil `docker compose ps` (empat container berstatus `Up`):

```text
NAME                IMAGE                  SERVICE     STATUS         PORTS
sen12ls-namenode    apache/hadoop:3.5.0    namenode    Up 20 seconds  0.0.0.0:9870->9870/tcp
sen12ls-datanode1   apache/hadoop:3.5.0    datanode1   Up 18 seconds
sen12ls-datanode2   apache/hadoop:3.5.0    datanode2   Up 18 seconds
sen12ls-spark       spark:3.5.0-python3    spark       Up 18 seconds  0.0.0.0:4040->4040/tcp
```

### 12.2 Tunggu sampai kedua DataNode hidup

Tunggu **30 sampai 60 detik**, lalu:

```powershell
docker exec sen12ls-namenode hdfs dfsadmin -report | Select-String "Live datanodes"
```

**Berhasil bila:** `Live datanodes (2):`. Bila `(0)` atau `(1)`, tunggu satu menit dan ulangi; bila tetap, lihat "Kalau macet". Antarmuka web NameNode: <http://localhost:9870>
(halaman Overview menyebut `Live Nodes` = 2).

Periksa juga bahwa konfigurasi dari `hadoop.env` terbaca:

```powershell
docker exec sen12ls-namenode hdfs getconf -confKey dfs.replication
docker exec sen12ls-namenode hdfs getconf -confKey dfs.permissions.enabled
```

Contoh hasil: `2` dan `false`.

### 12.3 Uji tulis dan baca HDFS

```powershell
docker exec sen12ls-namenode hdfs dfs -put /sen12ls-data/KAMUS_DATA.md /uji_kamus.md
docker exec sen12ls-namenode hdfs dfs -ls /
docker exec sen12ls-namenode hdfs dfs -stat "%r" /uji_kamus.md
```

Contoh hasil:

```text
Found 1 items
-rw-r--r--   2 root supergroup      12345 2026-11-02 10:00 /uji_kamus.md
2
```

Angka `2` pada daftar dan hasil `-stat` adalah **faktor replikasi**. (Ukuran dan tanggal di komputermu berbeda; pemilik berkas boleh `root` atau `hadoop`.)

### 12.4 Uji Spark membaca HDFS

```powershell
docker exec sen12ls-spark /opt/spark/bin/spark-submit --version
docker exec sen12ls-spark ls /bench /hdfs-parquet /results /sen12ls-data
docker exec sen12ls-spark /opt/spark/bin/spark-sql --master "local[2]" --driver-memory 2g -e "CREATE TEMPORARY VIEW uji USING text OPTIONS (path 'hdfs://namenode:8020/uji_kamus.md'); SELECT count(*) AS baris FROM uji;"
```

Contoh hasil: banner `Welcome to Spark ... version 3.5.0`; keempat folder terisi (`/bench` memuat `kueri.py`, `harness.py`, dan seterusnya; `/hdfs-parquet` memuat `csv_to_parquet.py` dan `run_sql.py`);
dan perintah ketiga mencetak satu angka (jumlah baris berkas; beberapa ratus) lalu `Time taken: ...`. Perintah ketiga memerlukan 10 sampai 40 detik karena Spark baru menyala.

Hapus berkas uji:

```powershell
docker exec sen12ls-namenode hdfs dfs -rm /uji_kamus.md
```

Contoh hasil: `Deleted /uji_kamus.md`.

> Perintah `spark-sql` belum pernah dijalankan pada Spark sungguhan oleh pembuat panduan. Bila ia menolak sedangkan `spark-submit --version` berhasil, lanjutkan ke #15
> (yang memakai `spark-submit`) dan catat pesan galatnya di grup.

**Berhasil bila (#12)**

- [ ] `docker compose ps` menampilkan empat container `Up`
- [ ] `Live datanodes (2):`; `dfs.replication` = 2; `localhost:9870` terbuka
- [ ] `hdfs dfs -put` dan `-ls` berhasil, replikasi 2
- [ ] Spark membaca berkas dari `hdfs://namenode:8020/...` dan keempat folder terpasang di container Spark

**Pesan WhatsApp**

```text
[SELESAI] hdfs-parquet: HDFS jalan (1 NameNode + 2 DataNode, replikasi 2), Spark 3.5.0 jalan (local[2]), Spark bisa membaca HDFS.
Siap mengubah S1 menjadi Parquet (#15).
```

### Kalau macet

| Tanda | Penyebab dan cara memperbaiki |
|---|---|
| `sen12ls-namenode` langsung `Exited` | `docker compose logs namenode --tail 50`. Bila ada `NameNode is not formatted` atau galat direktori: `docker compose down`, lalu `docker compose up -d` lagi (format dilakukan pada start pertama dengan folder kosong). Salin pesan ke `[BLOKIR]` bila berulang. |
| `Live datanodes (0)` setelah 2 menit | `docker compose logs datanode1 --tail 30`. Pesan `Incompatible clusterIDs`: `docker compose down` (menghapus container dan datanya) lalu `up -d` lagi. Pesan `Connection refused` ke `namenode:8020`: tunggu NameNode siap. |
| `Name node is in safe mode` | Normal selama 30 sampai 60 detik setelah menyala. Tunggu, atau `docker exec sen12ls-namenode hdfs dfsadmin -safemode get` (harus `OFF`). |
| `dfs.replication` bukan 2, atau galat membaca `hadoop.env` (mis. `NumberFormatException ... "2\r"`) | Berkas `hdfs-parquet/hadoop.env` berakhir baris CRLF. Buka di VS Code, klik `CRLF` di kanan bawah, pilih `LF`, simpan, lalu `docker compose down` dan `up -d`. Pastikan `.gitattributes` ada di repo (`git ls-files .gitattributes`). |
| Container ada yang `Exited (137)` | Memori habis (OOM). `docker stats --no-stream`; tutup program berat; naikkan `memory=` di `.wslconfig` (A2) bila RAM laptop mengizinkan, `wsl --shutdown`; **beri tahu grup** supaya semua uji memakai pengaturan yang sama. |
| `spark-submit: executable file not found` | Image Spark berbeda dari yang diharapkan. `docker exec sen12ls-spark ls /opt/spark/bin` harus memuat `spark-submit`. Bila tidak: `[BLOKIR]` dengan `docker compose config`. |
| `Permission denied` saat menulis HDFS | `dfs.permissions.enabled` harus `false` (12.2). Bila `true`, `hadoop.env` tidak terbaca: lihat baris CRLF di atas. |
| `/sen12ls-data` atau `/bench` kosong di container Spark | Pemasangan folder gagal (lihat #10). Pastikan menjalankan `docker compose` dari folder `hdfs-parquet` (jalur `../bench` relatif terhadap folder itu). |

---

## #14. Muat S1 ke PostGIS, indeks, jalankan W3

**Tujuan.** S1 (74.956 anotasi dan 4.392 patch) termuat di PostGIS, indeks dibangun, W3 dengan tangan sama dengan wasit, dan waktunya tercatat.

**Menunggu:** #8 (Syuep membuktikan S1 benar) dan #10. **Yang harus menyala:** hanya PostGIS (lihat tabel pindah di atas).

### 14.0 Buat S1 di laptopmu dan buktikan sama dengan milik Wildan

`data\out\` tidak ada di GitHub; tiap orang membuatnya sendiri (2 sampai 4 menit) dari berkas mentah di repo:

```powershell
cd C:\proyek\kelompok2-bigdata-storage
git pull --rebase
python data\convert_inventory.py
python data\generate_scales.py --verify
```

**Berhasil bila:** konversi berakhir `LOLOS: 17 pemeriksaan cocok` dan `--verify` menampilkan empat `COCOK` untuk `out/s1/...`
(baris `BELUM ADA` untuk S10 dan S100 boleh muncul). Bila `BEDA`: berhenti, tulis `[BLOKIR]` ke Syuep.

### 14.1 Nyalakan PostGIS dan buat tabel bersih

```powershell
cd postgis
docker compose up -d
cd ..
docker exec sen12ls-postgis psql -U postgres -d sen12ls -f /sql/schema.sql
```

(Bila kamu baru dari #12, matikan HDFS dahulu: `cd hdfs-parquet; docker compose stop`.) Selalu mulai dari `schema.sql`: ia menghapus tabel lama **beserta indeksnya**, jadi waktu muat tidak
tercampur pemeliharaan indeks dan waktu indeks benar-benar terukur.

### 14.2 Muat dua tabel (waktu tercatat otomatis)

`python bench\catat.py ukur ...` di depan perintah menjalankannya seperti biasa, mengukur lamanya, dan mencatat ke `results\pengukuran_postgis.csv` bila berhasil.
Tulis dalam **satu baris**:

```powershell
python bench\catat.py ukur --store postgis --skala S1 --jenis muat --objek annotations+patches docker exec sen12ls-postgis psql -U postgres -d sen12ls -v folder=/sen12ls-data/out/s1 -f /sql/load.sql
```

Contoh hasil (angka waktu ilustrasi; baris `NOTICE` dan beberapa baris `Time:` dihilangkan):

```text
Timing is on.
...
COPY 74956
Time: 1287.537 ms (00:01.288)
...
COPY 4392
Time: 15.491 ms
TRUNCATE TABLE
INSERT 0 74956
Time: 462.042 ms
INSERT 0 4392
...
 jumlah_annotations | jumlah_patches
--------------------+----------------
              74956 |           4392
(1 row)

Tercatat: postgis S1 muat (annotations+patches) = 3.4 detik  ->  C:\...\results\pengukuran_postgis.csv
```

Cara kerjanya: `COPY` memuat CSV ke tabel sementara, lalu `INSERT ... SELECT` membuat titik (`ST_MakePoint`) dan kotak (`ST_MakeEnvelope`). Tanpa `-v folder=...`, skrip berhenti dengan pesan
`Isi dulu: -v folder=/sen12ls-data/out/s1`.

### 14.3 Periksa jumlah dan bentuk data

```powershell
docker exec sen12ls-postgis psql -U postgres -d sen12ls -Atc "select count(*) from annotations" -c "select count(*) from patches"
docker exec sen12ls-postgis psql -U postgres -d sen12ls -Atc "select count(*) filter (where event_date is null) from annotations" -c "select count(*) filter (where not ST_IsValid(bbox)) from annotations" -c "select ST_SRID(center), ST_GeometryType(center) from annotations limit 1"
docker exec sen12ls-postgis psql -U postgres -d sen12ls -x -c "select ann_id, location, inventory, event_type, event_date, ST_AsText(center) as center, ST_AsText(bbox) as bbox, sim_batch from annotations where ann_id = 0"
```

Contoh hasil (nilai pada baris terakhir hanya ilustrasi; milikmu berbeda):

```text
74956
4392
109
0
4326|ST_Point
-[ RECORD 1 ]-----------------------------------------------------
ann_id     | 0
location   | Italy
inventory  | italy
event_type | Rainfall
event_date | 2016-04-01
center     | POINT(11.4548681 43.7734078)
bbox       | POLYGON((11.4541927 43.7728399,11.4541927 43.7739...))
sim_batch  | 0
```

Artinya berurutan: jumlah baris **74956 dan 4392**; **109** anotasi tanpa `event_date` (sama dengan [KAMUS_DATA](../data/KAMUS_DATA.md)); **0** kotak tidak sah (bila bukan 0, catat jumlahnya dan beri tahu Syuep dan Elsa; kotak tanpa lebar juga mengganggu indeks MongoDB); titik ber-SRID **4326**; dan satu baris
contoh. Bila jumlah barisnya lain, jangan lanjut: `[BLOKIR]` ke Syuep (data) atau periksa 14.2 (muat).

### 14.4 Bangun indeks (waktu tercatat)

```powershell
python bench\catat.py ukur --store postgis --skala S1 --jenis indeks --objek semua docker exec sen12ls-postgis psql -U postgres -d sen12ls -f /sql/indexes.sql
```

Contoh hasil (bagian akhir; ukuran ilustrasi):

```text
  tablename  |      indexname      | ukuran
-------------+---------------------+---------
 annotations | ann_bbox_gist       | 6000 kB
 annotations | ann_center_gist     | 4300 kB
 annotations | ann_event_date      | 540 kB
 annotations | ann_location_date   | 720 kB
 annotations | ann_type_date       | 620 kB
 annotations | annotations_pkey    | 1700 kB
 patches     | pat_inventory_split | 48 kB
 patches     | patches_pkey        | 192 kB
(8 rows)
...
Tercatat: postgis S1 indeks (semua) = 3.1 detik  ->  C:\...\results\pengukuran_postgis.csv
```

Harus ada **enam indeks buatan** (dua GiST: `ann_center_gist` dan `ann_bbox_gist`; empat btree) ditambah dua kunci utama. Skrip ini aman diulang (`IF NOT EXISTS`) dan menjalankan `VACUUM ANALYZE`
supaya perencana kueri tahu isi tabel.

### 14.5 Catat ukuran di disk

```powershell
python bench\catat.py ukuran --store postgis --skala S1
```

Contoh hasil: tiga baris per tabel (`ukuran_data_di_disk`, `ukuran_indeks`, `ukuran_total`, dalam MiB), lalu `Tercatat 6 baris  ->  ...pengukuran_postgis.csv`. Angka ini bahan hipotesis H3.

### 14.6 Jalankan W3 dengan tangan dan cocokkan dengan wasit

```powershell
docker exec sen12ls-postgis psql -U postgres -d sen12ls -v ann=100 -f /sql/queries/w3.sql
python bench\kebenaran.py --skala S1 --ann 100
```

Contoh hasil `w3.sql`:

```text
 w3
----
  1
(1 row)
```

Bagian `W3:` pada keluaran `kebenaran.py --ann 100` harus menyebut **jumlah yang sama**. Pilih `ann` lain dengan mengganti angkanya (harus punya `event_date`; bila tidak, skrip berhenti dengan pesan
`Anotasi tidak ditemukan atau tidak punya event_date`). Lihat juga apakah **indeks dipakai**:

```powershell
docker exec sen12ls-postgis psql -U postgres -d sen12ls -v ann=100 -v explain=1 -f /sql/queries/w2.sql
```

Setelah hasil `w2`, rencana kueri tercetak. Cari kata `ann_center_gist` (mis. `Index Scan using ann_center_gist` atau `Bitmap Index Scan on ann_center_gist`), bukan `Seq Scan on annotations`.
(Itu yang diharapkan pada PostGIS sungguhan; bila yang muncul `Seq Scan`, jalankan `VACUUM ANALYZE annotations;` lalu ulangi dan catat hasilnya.) Hal yang sama untuk W4: tambahkan `-v explain=1` pada `queries/w4.sql` dan cari `ann_bbox_gist`.

### 14.7 Jalankan harness W3 (hasilnya dikirim di #17)

```powershell
python bench\harness.py --store postgis --workload W3 --scale S1
python bench\compare_counts.py results\<nama berkas yang dicetak harness>.csv
```

Contoh hasil harness (angka waktu dan jumlah hasil ilustrasi):

```text
Jumlah data di postgis (annotations): 74956 (harapan untuk S1: 74956)
Pemanasan: satu putaran 100 kueri (tidak dicatat)...
Ulangan 1 selesai (100 kueri)
Ulangan 2 selesai (100 kueri)
Ulangan 3 selesai (100 kueri)

Ringkasan postgis W3 S1 (warm, 3 ulangan x 100 kueri = 300 eksekusi)
  median : 1.4 ms
  p95    : 3.0 ms
  ...
Berkas   : C:\...\results\20261102_postgis_W3_S1.csv
```

dan `compare_counts.py`:

```text
Perbandingan W3 S1: postgis vs benar
Cocok: 100 dari 100 kueri.
Semua jumlah hasil sama.
```

Yang harus sama di datamu: **100 kueri**, `Cocok: 100 dari 100`, dan tidak ada tulisan `GALAT`.

### 14.8 Simpan ke GitHub

```powershell
git add results/pengukuran_postgis.csv results/20261102_postgis_W3_S1.csv
git status
git commit -m "[results] PostGIS S1: muat, indeks, ukuran, W3"
git pull --rebase
git push
```

(Ganti nama berkas W3 dengan yang dicetak harness; `git status` tidak boleh memuat berkas di luar `results/`.)

**Berhasil bila (#14)**

- [ ] `74956 4392`, `109` tanpa tanggal, `0` kotak tidak sah, SRID 4326
- [ ] enam indeks buatan dan dua kunci utama terbentuk
- [ ] `results/pengukuran_postgis.csv` berisi waktu muat, waktu indeks, dan ukuran
- [ ] W3 tangan = jumlah wasit, dan rencana W2 memakai `ann_center_gist`
- [ ] harness W3: `Cocok: 100 dari 100 kueri`; perubahan sudah di-push

**Pesan WhatsApp**

```text
[SELESAI] postgis: S1 termuat (74956 anotasi, 4392 patch), 6 indeks dibuat (<detik>), W3 tangan = wasit (<jumlah>), harness W3 cocok 100 dari 100.
Waktu muat <detik>; ukuran total <MiB> (results/pengukuran_postgis.csv).
```

### Kalau macet

| Tanda | Penyebab dan cara memperbaiki |
|---|---|
| `could not open file "/sen12ls-data/out/s1/annotations.csv" for reading: No such file` | Berkas S1 belum dibuat (14.0) atau pemasangan folder gagal: `docker exec sen12ls-postgis ls /sen12ls-data/out/s1`. Kosong: ulangi 14.0, lalu cek File sharing Docker. |
| `Isi dulu: -v folder=...` | Kamu lupa `-v folder=/sen12ls-data/out/s1`. Tambahkan dan ulangi. |
| `invalid input syntax for type double precision` atau `extra data after last expected column` | CSV tidak sesuai kontrak (23 kolom). Jalankan `python data\cek_data.py --skala S1`; harus `SEMUA PEMERIKSAAN LULUS (18)`. Bila lulus, `[BLOKIR]` dengan **seluruh** pesan dan nomor baris yang disebut. |
| `permission denied for ... COPY` atau `must be superuser` | Perintah harus memakai `-U postgres` (pengguna uji). Periksa tidak ada `PGUSER` lain di lingkunganmu. |
| `duplicate key value violates unique constraint` | Tabel sudah berisi data dan kamu memakai `-v tambah=1` atau tidak menjalankan `schema.sql`. Mulai dari 14.1. |
| `The term 'docker' is not recognized` di dalam `catat.py` | Docker belum ada di PATH; buka PowerShell baru setelah memasang Docker (A2). |
| `Perintah berakhir dengan kode ..., jadi waktunya TIDAK dicatat` | Perintah di dalam gagal. Baca galatnya; waktu hanya dicatat bila berhasil. |
| `could not create GiST index` atau galat memori saat indeks | Tutup program lain; pada S1 ini tidak seharusnya terjadi. `[BLOKIR]` dengan pesan penuh dan `select ST_IsValid(...)` dari 14.3. |
| W3 tangan berbeda dari wasit | Pastikan `ann` sama di kedua perintah dan data S1 COCOK dengan checksum. Bila tetap beda: `[BLOKIR]` dengan kedua keluaran; **jangan** menyesuaikan angka supaya cocok. |
| `compare_counts`: `Cocok: n dari 100` dengan `n` kurang dari 100 | Ada kueri yang beda. Lihat tabel selisihnya: periksa indeks, skala yang dimuat, dan `schema.sql` dijalankan sebelum muat. `[BLOKIR]` bila tetap. |
| `Tidak bisa terhubung ke postgis` | Container belum jalan atau port berbeda: `docker compose ps` di folder `postgis`. |

---

## #15. Parquet S1 di HDFS dan W3 Spark SQL (kamu memimpin, Syuep mendampingi)

**Tujuan.** S1 diubah dari CSV menjadi Parquet (ZSTD) di HDFS; jumlah barisnya cocok dengan CSV; W3 dijalankan lewat Spark SQL dan jumlah hasilnya sama dengan wasit.

**Menunggu:** #8 (Syuep) dan #12 (kamu). **Yang harus menyala:** HDFS dan Spark saja (matikan PostGIS: `cd postgis; docker compose stop`; lalu `cd ..\hdfs-parquet; docker compose up -d` dan tunggu
30 sampai 60 detik bila baru dinyalakan).

### 15.1 Ubah CSV menjadi Parquet di HDFS (waktu tercatat)

Pastikan `data\out\s1\annotations.csv` ada (14.0). Tulis dalam **satu baris**:

```powershell
cd C:\proyek\kelompok2-bigdata-storage
python bench\catat.py ukur --store spark --skala S1 --jenis muat --objek annotations+patches docker exec sen12ls-spark /opt/spark/bin/spark-submit --master "local[2]" --driver-memory 2g /hdfs-parquet/csv_to_parquet.py --scale S1
```

Contoh hasil (bagian akhir; Spark mencetak banyak log `WARN` di awal, abaikan; waktu ilustrasi):

```text
annotations: 74956 baris ditulis ke hdfs://namenode:8020/data/sen12ls/parquet/s1/annotations (9.8 detik)
patches: 4392 baris ditulis ke hdfs://namenode:8020/data/sen12ls/parquet/s1/patches (1.4 detik)
Jumlah baris cocok dengan harapan S1 (annotations 74956, patches 4392).
Selesai dalam 14.2 detik (kompresi zstd).
Catat waktunya di komputermu:  python bench/catat.py waktu --store spark --skala S1 --jenis muat --detik 14.2

Tercatat: spark S1 muat (annotations+patches) = 24.6 detik  ->  C:\...\results\pengukuran_spark.csv
```

Skrip menulis, **membaca ulang**, dan mencocokkan jumlah baris dengan harapan; kegagalan mencetak pesan yang jelas. Abaikan baris `Catat waktunya ...`: waktu sudah tercatat otomatis oleh `catat.py ukur`
(jangan dicatat dua kali). Waktu yang tercatat memuat **menyalakan Spark** (JVM), sama seperti `mongoimport` dan `psql` yang diukur sebagai satu perintah utuh; sebut hal ini di laporan.

### 15.2 Periksa isi di HDFS

```powershell
docker exec sen12ls-namenode hdfs dfs -ls /data/sen12ls/parquet/s1/annotations
docker exec sen12ls-namenode hdfs dfs -du -s -h /data/sen12ls/parquet/s1/annotations /data/sen12ls/parquet/s1/patches
docker exec sen12ls-namenode hdfs fsck /data/sen12ls/parquet/s1/annotations -files -blocks
```

Contoh hasil (bentuknya):

```text
Found 2 items
-rw-r--r--   2 root supergroup          0 2026-11-02 10:05 /data/sen12ls/parquet/s1/annotations/_SUCCESS
-rw-r--r--   2 root supergroup    3412345 2026-11-02 10:05 /data/sen12ls/parquet/s1/annotations/part-00000-....zstd.parquet
...
Status: HEALTHY
 Average block replication:	2.0
```

Harus ada `_SUCCESS` dan satu atau beberapa berkas `part-...zstd.parquet`; angka `2` pada kolom kedua dan `Average block replication: 2.0` menunjukkan **replikasi 2**; `Status: HEALTHY`.

### 15.3 Periksa isi bersama Syuep

Syuep memeriksa bahwa isi Parquet sama dengan CSV (jumlah anotasi, jumlah tanpa tanggal, jumlah lokasi, dan patch); perintahnya ada di [PANDUAN_Syuep.md](PANDUAN_Syuep.md), #15.
Berbagi layar dan jalankan bersama. Hasil yang benar: `74956  109  16` dan `4392`. Beda berarti ada yang salah di langkah muat: periksa 15.1 dahulu.

### 15.4 Catat ukuran di HDFS

```powershell
python bench\catat.py ukuran --store spark --skala S1
```

Contoh hasil: baris `ukuran_total` (satu salinan) dan `ukuran_dengan_replika` (replikasi 2) untuk `annotations` dan `patches`, dalam MiB, lalu `Tercatat 4 baris  ->  ...pengukuran_spark.csv`.
Untuk H3 yang dibandingkan adalah `ukuran_total` (satu salinan); replikasi dicatat terpisah dan dijelaskan di laporan.

### 15.5 Jalankan W3 lewat harness dan cocokkan dengan wasit

```powershell
python bench\harness.py --store spark --workload W3 --scale S1
python bench\compare_counts.py results\<nama berkas yang dicetak harness>.csv
```

Contoh hasil (bagian akhir; waktu ilustrasi). Spark menyala **sekali** untuk seluruh 400 kueri, jadi kueri pertama lebih lama dari yang berikutnya:

```text
Menjalankan Spark SQL di kontainer (S10 dan S100 bisa lama):
docker exec sen12ls-spark /opt/spark/bin/spark-submit --master local[2] --driver-memory 2g /hdfs-parquet/run_sql.py --workload W3 --scale S1 --repeats 3 --cold-warm warm --out /results/20261102_spark_W3_S1.csv
...
Jumlah data di hdfs://namenode:8020/data/sen12ls/parquet/s1/annotations: 74956 (harapan untuk S1: 74956)
Pemanasan: satu putaran 100 kueri (tidak dicatat)...
Ulangan 1 selesai (100 kueri)
Ulangan 2 selesai (100 kueri)
Ulangan 3 selesai (100 kueri)

Ringkasan spark W3 S1 (warm, 3 ulangan x 100 kueri = 300 eksekusi)
  median : 85.000 ms
  p95    : 140.000 ms
  ...
Selesai. Hasil: results/20261102_spark_W3_S1.csv
```

dan

```text
Perbandingan W3 S1: spark vs benar
Cocok: 100 dari 100 kueri.
Semua jumlah hasil sama.
```

Perkiraan waktu: beberapa menit (belum terukur). Spark **lebih lambat** dari PostGIS di S1; itu wajar (biaya menjalankan job Spark lebih besar daripada membaca 74.956 baris) dan bukan masalah;
kesenjangannya yang diukur di S10 dan S100. Berkas hasil muncul di folder `results` laptopmu karena folder itu dipasang ke container.

### 15.6 Simpan ke GitHub

```powershell
git add results/pengukuran_spark.csv results/20261102_spark_W3_S1.csv
git status
git commit -m "[results] Spark S1: muat Parquet, ukuran, W3"
git pull --rebase
git push
```

**Berhasil bila (#15)**

- [ ] Parquet S1 di HDFS: `74956` anotasi dan `4392` patch (skrip mencetak `Jumlah baris cocok dengan harapan S1`), replikasi 2, `HEALTHY`
- [ ] isi Parquet cocok dengan CSV menurut pemeriksaan Syuep
- [ ] `results/pengukuran_spark.csv` berisi waktu muat dan ukuran
- [ ] harness W3 Spark: `Cocok: 100 dari 100 kueri`; perubahan sudah di-push

**Pesan WhatsApp**

```text
[SELESAI] hdfs-parquet: Parquet S1 di HDFS (74956 anotasi, 4392 patch, ZSTD, replikasi 2), waktu muat <detik>, ukuran total <MiB>.
W3 Spark SQL cocok dengan wasit (100 dari 100). Berkas: results/<nama>.csv
```

### Kalau macet

| Tanda | Penyebab dan cara memperbaiki |
|---|---|
| `Gagal menulis hdfs://...` lalu `Cek: kontainer namenode dan datanode jalan` | NameNode atau DataNode belum siap. `docker compose ps`; ulangi 12.2 (`Live datanodes (2)`); tunggu 30 sampai 60 detik lagi. |
| `Name node is in safe mode` | Tunggu satu menit setelah menyalakan, lalu ulangi. |
| `Path does not exist: file:/sen12ls-data/out/s1/annotations.csv` | CSV S1 belum dibuat (14.0) atau pemasangan folder gagal: `docker exec sen12ls-spark ls /sen12ls-data/out/s1`. |
| `Malformed CSV record` atau `NumberFormatException` | Mode `FAILFAST` menolak baris yang tidak cocok dengan skema. `python data\cek_data.py --skala S1` harus lulus; bila lulus, `[BLOKIR]` dengan pesan penuh dan nama kolom yang disebut. |
| `Compression codec zstd not supported` atau galat `zstd` | Tambahkan `--kompresi snappy` di ujung perintah `csv_to_parquet.py`, **catat di grup dan laporan** (ukuran akan lebih besar), dan gunakan pilihan yang sama untuk S10 dan S100. |
| `Jumlah baris tidak sama dengan harapan S1` | Parquet tidak sama dengan CSV. Ulangi 15.1 (skrip menimpa hasil lama); `[BLOKIR]` bila berulang. |
| `Java heap space` atau container Spark berhenti | Memori habis. Tutup program lain; lihat `Exited (137)` di #12. Jangan menaikkan `--driver-memory` hanya untuk Spark (adil: 2 GB). |
| Harness: `Tidak bisa membaca hdfs://...` | Parquet belum dibuat (15.1) atau HDFS mati. `docker exec sen12ls-namenode hdfs dfs -ls /data/sen12ls/parquet`. |
| Harness: `Berkas ... sudah ada` | Dua proses menulis nama yang sama. Jalankan satu per satu. |
| Harness: `Spark gagal (kode ...)` | Baca log Spark di atasnya (galat pertama). Cek `docker compose ps`. |
| `compare_counts` beda | Lihat tabel selisih; cek bahwa Parquet S1 benar (15.3) dan `points.json` identik dengan milik Wildan (`git status` bersih untuk `bench/`). |

---

## #17. Kirim CSV W3 PostGIS dan Spark

**Menunggu:** #11 (Sofi memastikan alat ukur benar), #14, dan #15. Sofi memimpin pembandingan tiga penyimpanan; bagianmu: **mengirim dua berkas CSV** dengan benar.

```powershell
cd C:\proyek\kelompok2-bigdata-storage
git pull --rebase
dir results\*_postgis_W3_S1*.csv, results\*_spark_W3_S1*.csv
```

Seharusnya masing-masing satu berkas dari 14.7 dan 15.5. Bila ada lebih dari satu, pakai yang **tiga ulangan** (`Ringkasan ... 3 ulangan`) dan paling baru. Periksa sekali lagi terhadap wasit:

```powershell
python bench\compare_counts.py results\<postgis W3 S1>.csv
python bench\compare_counts.py results\<spark W3 S1>.csv
```

Keduanya harus `Cocok: 100 dari 100 kueri`. Pastikan keduanya sudah di GitHub (`git status` bersih dan `git log -3` memuat commit `[results]` dari 14.8 dan 15.6). Bila belum:

```powershell
git add results/<postgis W3 S1>.csv results/<spark W3 S1>.csv
git commit -m "[results] postgis dan spark W3 S1 (3 ulangan, warm)"
git pull --rebase
git push
```

**Catatan.** Di #17 hanya **jumlah hasil** yang dibandingkan antar penyimpanan. Waktu dari laptop yang berbeda tidak dibandingkan; perbandingan waktu yang adil dilakukan di laptop uji (#26 dan #27).

**Berhasil bila:** dua berkas CSV (PostGIS dan Spark) sudah di GitHub dan masing-masing `Cocok: 100 dari 100 kueri`.

**Pesan WhatsApp:** `[SELESAI] results: postgis dan spark W3 S1 cocok dengan wasit (100 dari 100). Berkas: results/<nama1>.csv dan results/<nama2>.csv`

Bila Sofi menemukan selisih antar penyimpanan, jalankan kembali bagian yang disebut (skala yang dimuat, indeks, atau Parquet) dan kirim berkas baru; **jangan menghapus berkas lama** (beri tahu Sofi berkas mana yang berlaku).

---

## #18. SINKRON 1

Yang kamu siapkan dan tunjukkan (4 menit):

- [ ] `docker compose ps` PostGIS dan jumlah baris `74956 4392`; daftar indeks dan satu rencana kueri W2 yang memakai `ann_center_gist`
- [ ] HDFS: `Live datanodes (2)` dan `hdfs dfs -ls` isi `parquet/s1`; replikasi 2
- [ ] hasil `compare_counts.py` PostGIS dan Spark terhadap wasit: `Cocok: 100 dari 100 kueri`
- [ ] waktu muat dan ukuran dari `python bench\catat.py tampil`

Pesan setelah Sinkron 1: `[SELESAI] Sinkron 1: hasil PostGIS dan HDFS-Parquet sudah ditunjukkan dan dicatat.`

---

## #19. Baca dokumen rancangan

Tautan ada di grup (Wildan menulis `[SELESAI] dokumen v2` saat versi final siap). Baca bagian **Justifikasi pemilihan teknologi** (PostGIS dan HDFS-Parquet), **arsitektur HDFS**, dan **model data**, dan periksa:

- [ ] skema PostGIS cocok dengan `postgis/schema.sql` dan `data/KAMUS_DATA.md` (23 kolom; `center` titik, `bbox` poligon, SRID 4326)
- [ ] indeks GiST pada `center` dan `bbox`, serta indeks atribut, disebut dengan benar
- [ ] HDFS: satu NameNode, **dua** DataNode, replikasi **2**, Parquet ZSTD, Spark SQL `local[2]` dengan 2 GB; baseline dijelaskan sebagai **tanpa indeks spasial**
- [ ] klaim kinerja ditulis **hipotesis**; tidak ada klaim ketersediaan atau toleransi kegagalan yang kita **tidak uji** (W10 belum ada skripnya)
- [ ] tidak ada sisa nama dataset lama

Bentuk pesan temuan: `Dokumen - <bagian> - <yang salah atau kurang> - usul: <perbaikan>`. Tidak ada temuan: `Dokumen - bagianku sudah benar (Levi)`.

---

## #20. Bahan slide 4 (bagian PostGIS dan baseline)

Kirim ke Wildan **3 sampai 5 poin** per bagian (satu kalimat pendek, paling banyak 12 kata) dan **satu gambar**. Slide 4 dibagi dua: Elsa menyampaikan MongoDB; kamu PostGIS dan baseline.

**PostGIS**

- Skema tegas: 23 kolom bertipe jelas; titik pusat dan kotak sebagai `geometry`
- Indeks GiST pada titik pusat dan kotak pembatas; `ST_Intersects` untuk W2 sampai W4
- Satu SQL memadukan filter spasial, atribut, dan agregasi (W4, W5, W6)
- Hipotesis: PostGIS lebih cepat dari MongoDB di W4 (H2). **Belum diuji**

**Baseline HDFS + Parquet**

- HDFS: satu NameNode dan dua DataNode, replikasi 2
- Parquet kolumnar (ZSTD) dibaca Spark SQL; **tanpa** indeks spasial
- Fungsi baseline: mengukur nilai indeks spasial (H1) dan agregasi (H4); ukuran diduga terkecil (H3)
- Sedona dan GeoParquet: pengembangan lanjutan. Semua hipotesis **belum diuji**

Gambar yang disarankan: tangkapan layar antarmuka HDFS (`localhost:9870`, `Live Nodes 2`) atau `\d annotations` (tipe `geometry`) atau daftar indeks.

```text
[SELESAI] bahan slide 4 (Levi): <poin> dan gambar terlampir
```

---

## #23. Tinjau silang (dengan Elsa)

Kamu meninjau **bagian Elsa** (justifikasi MongoDB, model dokumen, dan kueri `$geoWithin` dan `$geoIntersects`); Elsa meninjau bagianmu.

Daftar periksa untuk bagian Elsa:

- [ ] W2 (titik pusat di jendela), W3 (+30 hari), W4 (kotak beririsan + `event_type` + `event_conf >= 0,9`) **berarti hal yang sama** dengan versi SQL (lihat `postgis/queries/w2.sql` sampai `w4.sql`)
- [ ] batas jendela sama (±0,01 dan ±0,1 derajat, digeser setengah langkah); batas tertutup
- [ ] model dokumen: `center` titik GeoJSON, `bbox` poligon, `dates.event`; field kosong tidak ditulis (bukan `null`)
- [ ] indeks `2dsphere`, indeks tanggal, dan indeks gabungan disebut dan dijelaskan
- [ ] klaim konsistensi dan ketersediaan tidak dibuat (satu node tanpa replica set)
- [ ] istilah dan angka konsisten dengan dokumen dan slide

Cara: baca bagiannya sekali penuh tanpa mengomentari; baca lagi dan catat; kirim `[Tinjau] @Elsa - <bagian> - <temuan> - Saran: <perbaikan>`.

---

## #24. Latihan pitching (SINKRON 2)

Kamu menyampaikan **bagian PostGIS dan baseline di slide 4** (sekitar 2 menit) dan menjawab (bank pertanyaan di [PANDUAN_Wildan.md](PANDUAN_Wildan.md), #24):

- **"Mengapa PostgreSQL/PostGIS?"**: skema tegas (23 kolom bertipe), indeks GiST pada titik dan kotak, `ST_Intersects`, dan SQL yang memadukan filter spasial, atribut, dan agregasi.
- **"Mengapa HDFS + Parquet sebagai baseline?"**: berkas kolumnar tanpa indeks spasial; mencari titik berarti memindai dengan pra-filter pada kolom koordinat. Fungsinya mengukur keunggulan indeks spasial. Sedona dan GeoParquet pengembangan lanjutan.
- **"Apa beda 2dsphere dan geometry?"** (bersama Elsa): 2dsphere memakai geometri bola; `geometry` PostGIS planar. Jendela kita digeser setengah langkah dari kisi koordinat sehingga hasilnya **harus** sama persis; diuji dengan `compare_counts.py` dan wasit.
- **"Mengapa bukan Elasticsearch, Cassandra, Redis, Neo4j, atau TimescaleDB?"** (bersama Elsa): bebannya bukan pencarian teks, bukan satu-tabel-per-kueri, bukan data di memori saja, bukan graf, dan bukan deret waktu.
- **"Bagaimana menambah data baru (W8)?"**: PostGIS: `load.sql` dengan `-v tambah=1`; Parquet: `csv_to_parquet.py --tambah` (berkas baru per batch).
- **"Mengapa Spark terlihat lambat di data kecil?"** (bersama Sofi): biaya memulai job Spark lebih besar daripada membaca 74.956 baris; baseline dinilai terutama pada S100.

Latih dengan kata-katamu sendiri; jangan menghafal.

---

## #25. W1 sampai W6 benar di S1 di PostGIS dan Spark

**Menunggu:** #18 (Sinkron 1). **Tujuan:** keenam kueri berjalan di PostGIS dan Spark dan **jumlah hasilnya sama dengan wasit**.

### 25.1 PostGIS (hanya PostGIS yang menyala)

```powershell
cd C:\proyek\kelompok2-bigdata-storage
git pull --rebase
cd hdfs-parquet
docker compose stop
cd ..\postgis
docker compose up -d
cd ..
foreach ($w in "W1","W2","W3","W4","W5","W6") { python bench\harness.py --store postgis --workload $w --scale S1 }
```

Pastikan data S1 masih ada di PostGIS (`select count(*) from annotations` = 74956); bila kamu pernah memuat skala lain, mulai dari 14.1. Lalu bandingkan **tiap berkas terbaru** dengan wasit:

```powershell
foreach ($w in "W1","W2","W3","W4","W5","W6") {
  $f = Get-ChildItem ("results\*_postgis_" + $w + "_S1.csv") | Sort-Object LastWriteTime | Select-Object -Last 1
  python bench\compare_counts.py $f.FullName
}
```

**Berhasil bila** enam kali `Semua jumlah hasil sama` (W1: `Cocok: 100 dari 100`; W5 dan W6: `Cocok: 1 dari 1`). Contoh:

```text
Perbandingan W5 S1: postgis vs benar
Cocok: 1 dari 1 kueri.
Semua jumlah hasil sama.
```

### 25.2 Spark (hanya HDFS dan Spark yang menyala)

```powershell
cd postgis
docker compose stop
cd ..\hdfs-parquet
docker compose up -d
cd ..
```

Tunggu 30 sampai 60 detik dan pastikan `Live datanodes (2)` (12.2). Parquet S1 masih ada bila kamu tidak menjalankan `docker compose down`; periksa `docker exec sen12ls-namenode hdfs dfs -ls /data/sen12ls/parquet/s1`. Lalu:

```powershell
foreach ($w in "W1","W2","W3","W4","W5","W6") { python bench\harness.py --store spark --workload $w --scale S1 }
foreach ($w in "W1","W2","W3","W4","W5","W6") {
  $f = Get-ChildItem ("results\*_spark_" + $w + "_S1.csv") | Sort-Object LastWriteTime | Select-Object -Last 1
  python bench\compare_counts.py $f.FullName
}
```

Memerlukan beberapa menit per beban kerja (tiap kueri Spark memakan puluhan sampai ratusan milidetik; W1 melakukan 100 pemindaian). **Berhasil bila** enam kali `Semua jumlah hasil sama`.

### 25.3 Bila ada yang beda

Paling mungkin W4 (kotak beririsan; bola versus bidang datar). **Jangan** mengubah jendela atau tanggal supaya cocok. Simpan tabel selisih dan tulis `[BLOKIR]`; penyebab yang mungkin: indeks belum ada (PostGIS),
Parquet tidak sama dengan CSV (Spark), atau data tidak sama dengan S1. Hanya uji sungguhan yang memastikan; **PostGIS dan Spark keduanya planar**, jadi selisih antara keduanya hampir pasti
kesalahan muat; selisih MongoDB terhadap keduanya yang menyangkut bola dan bidang datar.

### 25.4 Simpan hasilnya

```powershell
git add results
git status
git commit -m "[results] postgis dan spark W1 sampai W6 S1, cocok dengan wasit"
git pull --rebase
git push
```

Dua pemeriksaan tambahan yang berguna untuk pitching dan laporan (PostGIS menyala):

```powershell
docker exec sen12ls-postgis psql -U postgres -d sen12ls -v ann=100 -v explain=1 -f /sql/queries/w4.sql
docker exec sen12ls-postgis psql -U postgres -d sen12ls -f /sql/queries/w5.sql
```

Amati rencana W4 (apakah `ann_bbox_gist` dipakai; berapa baris dibuang oleh filter) dan jumlah kelompok W5.

**Pesan WhatsApp:** `[SELESAI] postgis dan hdfs-parquet: W1 sampai W6 di S1 cocok dengan wasit di PostGIS (6 dari 6) dan Spark (6 dari 6). Berkas di results/.`

---

## #26. Muat S10 lalu S100 di PostGIS dan HDFS-Parquet (laptop uji)

**Menunggu:** #16 (Syuep: S10 dan S100 siap dan `CHECKSUMS.txt`) dan #25.

Pengukuran waktu yang adil berjalan di **satu laptop uji** (dipilih saat kickoff). Pemilik laptop itu menjalankan perintah; kamu mendampinginya lewat berbagi layar atau bergantian memakai laptopnya.
Urutan praktis: **selesaikan satu penyimpanan sampai tuntas** (muat, indeks, ukuran, uji #27) sebelum menyalakan penyimpanan berikutnya, supaya disk dan RAM cukup. Persiapan laptop uji
(daya, tidak tidur, disk 25 GB, Docker 6 GB, checksum S10 dan S100 COCOK) ada di [PANDUAN_Sofi.md](PANDUAN_Sofi.md), #26.

### 26.1 PostGIS: S10

PostGIS menyala sendirian (`docker ps`). Rangkaian yang sama dengan #14 dengan folder `s10`:

```powershell
cd C:\proyek\kelompok2-bigdata-storage
docker exec sen12ls-postgis psql -U postgres -d sen12ls -f /sql/schema.sql
python bench\catat.py ukur --store postgis --skala S10 --jenis muat --objek annotations+patches docker exec sen12ls-postgis psql -U postgres -d sen12ls -v folder=/sen12ls-data/out/s10 -f /sql/load.sql
python bench\catat.py ukur --store postgis --skala S10 --jenis indeks --objek semua docker exec sen12ls-postgis psql -U postgres -d sen12ls -f /sql/indexes.sql
python bench\catat.py ukuran --store postgis --skala S10
docker exec sen12ls-postgis psql -U postgres -d sen12ls -Atc "select count(*) from annotations" -c "select count(*) from patches"
```

**Jangan lupa `schema.sql` paling awal**: ia menghapus tabel lama dan indeksnya. Jumlah yang benar: `749560` dan `43920`. Lalu Sofi menjalankan uji S10 (#27).

### 26.2 PostGIS: S100 (lama)

Perintahnya sama; ganti `s10` dengan `s100` dan `S10` dengan `S100`:

```powershell
docker exec sen12ls-postgis psql -U postgres -d sen12ls -f /sql/schema.sql
python bench\catat.py ukur --store postgis --skala S100 --jenis muat --objek annotations+patches docker exec sen12ls-postgis psql -U postgres -d sen12ls -v folder=/sen12ls-data/out/s100 -f /sql/load.sql
python bench\catat.py ukur --store postgis --skala S100 --jenis indeks --objek semua docker exec sen12ls-postgis psql -U postgres -d sen12ls -f /sql/indexes.sql
python bench\catat.py ukuran --store postgis --skala S100
docker exec sen12ls-postgis psql -U postgres -d sen12ls -Atc "select count(*) from annotations" -c "select count(*) from patches"
```

Waktu muat dan indeks S100 **belum terukur**; perkirakan puluhan menit (7,5 juta anotasi; CSV 1,97 GB; indeks GiST pada 7,5 juta titik dan kotak). Biarkan laptop bekerja, jangan memakainya untuk hal berat, dan jangan menutup jendela PowerShell.
Jumlah yang benar: `7495600` dan `439200`. Tabel sementara (`annotations_stage`) memakai disk sementara; pastikan disk bebas minimal 25 GB.

### 26.3 W8 untuk PostGIS: menambah satu batch baru ke S100 (paling akhir)

Setelah **semua** uji S100 untuk PostGIS selesai (#27), Syuep menyiapkan batch (`python data\generate_scales.py --extra-batch 100`):

```powershell
python bench\catat.py ukur --store postgis --skala S100 --jenis tambah_batch --objek annotations+patches docker exec sen12ls-postgis psql -U postgres -d sen12ls -v folder=/sen12ls-data/out/batch100 -v tambah=1 -f /sql/load.sql
```

(`-v tambah=1` tidak mengosongkan tabel; indeks sudah ada sehingga waktunya mencakup pembaruan indeks.) Hasil akhir: `7570556` anotasi dan `443592` patch. Setelah ini S100 berisi
data tambahan; **muat ulang S100 bila harus menguji lagi** (mulai dari `schema.sql`).

### 26.4 Ganti ke HDFS-Parquet

```powershell
cd postgis
docker compose stop
cd ..\hdfs-parquet
docker compose up -d
cd ..
```

Tunggu 30 sampai 60 detik dan pastikan `Live datanodes (2)`.

### 26.5 Parquet: S10 lalu S100

```powershell
python bench\catat.py ukur --store spark --skala S10 --jenis muat --objek annotations+patches docker exec sen12ls-spark /opt/spark/bin/spark-submit --master "local[2]" --driver-memory 2g /hdfs-parquet/csv_to_parquet.py --scale S10
python bench\catat.py ukuran --store spark --skala S10
python bench\catat.py ukur --store spark --skala S100 --jenis muat --objek annotations+patches docker exec sen12ls-spark /opt/spark/bin/spark-submit --master "local[2]" --driver-memory 2g /hdfs-parquet/csv_to_parquet.py --scale S100
python bench\catat.py ukuran --store spark --skala S100
```

Skrip mencocokkan jumlah baris dengan harapan: S10 `749560` dan `43920`; S100 `7495600` dan `439200`. Waktu S100 **belum terukur** (perkiraan: beberapa menit sampai puluhan menit). Spark tidak memiliki indeks, jadi tidak ada langkah indeks;
W7 untuk Spark berisi waktu muat dan ukuran saja. **Jangan menjalankan `docker compose down`** sebelum seluruh uji S100 selesai: itu menghapus data HDFS (Parquet bisa dibuat ulang dari CSV, tetapi memakan waktu).

### 26.6 W8 untuk Spark (paling akhir)

Setelah semua uji S100 untuk Spark selesai (#27) dan batch100 sudah dibuat Syuep:

```powershell
python bench\catat.py ukur --store spark --skala S100 --jenis tambah_batch --objek annotations+patches docker exec sen12ls-spark /opt/spark/bin/spark-submit --master "local[2]" --driver-memory 2g /hdfs-parquet/csv_to_parquet.py --scale S100 --folder /sen12ls-data/out/batch100 --tambah
```

Skrip **menambah** berkas Parquet baru ke folder S100 tanpa menimpa (tidak ada pemeriksaan harapan karena jumlahnya berubah). Setelah ini jumlah baris S100 menjadi `7570556`; kueri harness akan menolak
(`Jumlah data tidak cocok`) kecuali `--force`; karena itu W8 **paling akhir**.

### 26.7 Simpan dan bersihkan

```powershell
git add results
git commit -m "[results] pengukuran PostGIS dan Spark S10 dan S100: muat, indeks, ukuran"
git pull --rebase
git push
```

Sebelum penyimpanan berikutnya: `docker compose stop` di foldernya (data tetap). Bila disk sempit: PostGIS `docker compose down -v` (menghapus datanya) atau HDFS `docker compose down` (menghapus datanya);
hasil pengukuran di `results/` tetap aman.

**Pesan WhatsApp:** `[SELESAI] postgis dan hdfs-parquet: S10 dan S100 termuat di laptop uji (PostGIS: muat S10 <detik>, S100 <detik>; Parquet: muat S10 <detik>, S100 <detik>; ukuran di results/). Siap W1 sampai W8 (#27).`

### Kalau macet

| Tanda | Penyebab dan cara memperbaiki |
|---|---|
| `No space left on device` | Disk penuh. Hapus `data\out\s100` bila tidak dipakai, atau `docker system prune` (tanyakan dulu); muat ulang dari `schema.sql` (PostGIS) atau ulangi `csv_to_parquet.py` (menimpa). |
| PostGIS: container `Exited` di tengah muat | Memori habis. `docker compose logs --tail 50`; naikkan `memory=` di `.wslconfig` (A2) bila RAM mengizinkan, `wsl --shutdown`, lalu mulai lagi dari `schema.sql`. Beri tahu grup. |
| PostGIS: indeks GiST S100 sangat lama atau gagal memori | Tutup program lain. `shared_buffers` dibatasi sengaja (adil); `maintenance_work_mem` 256 MB sudah diatur di `indexes.sql`. Bila gagal, catat dan `[BLOKIR]`. |
| PostGIS: jumlah baris bukan `7495600` | Muat terpotong atau `schema.sql` lupa dijalankan. Ulangi dari `schema.sql`. |
| Spark S100: `Java heap space` atau `Container killed` | Memori habis. Jangan menaikkan `--driver-memory` hanya untuk Spark. Tutup program lain; lihat `Exited (137)` di #12; catat dan `[BLOKIR]` bila berulang. |
| Spark S100: `Name node is in safe mode` atau `could only be replicated to 0 nodes` | DataNode tidak siap atau disk Docker penuh. `hdfs dfsadmin -report` (`Live datanodes (2)`, `DFS Remaining`). Beri ruang disk lalu ulangi. |
| Spark: `docker compose down` tidak sengaja dijalankan | Data HDFS hilang. Ulangi `csv_to_parquet.py` untuk skala yang diperlukan (menimpa); CSV di `data\out` tidak ikut terhapus. |
| `catat.py ukuran --store spark` gagal | NameNode harus jalan: `docker compose ps`. Isi manual bila perlu: `python bench\catat.py ukuran --store spark --skala S10 --mb <angka> --objek annotations` (dan catat alasannya). |

---

## #27. Membantu Sofi menjalankan W1 sampai W8 (sisi PostGIS dan Spark)

Sofi memimpin (urutan, ulangan, hasil); semua perintah lengkapnya di [PANDUAN_Sofi.md](PANDUAN_Sofi.md), #27. Bagianmu:

- **PostGIS, cold run:** nyalakan ulang container sebelum tiap putaran dingin, tunggu 20 detik, lalu jalankan harness (PostGIS menyala sendirian):

  ```powershell
  docker restart sen12ls-postgis
  Start-Sleep -Seconds 20
  python bench\harness.py --store postgis --workload W3 --scale S10 --cold-warm cold --repeats 1 --first-run-no 1
  ```

- **PostGIS, banyak klien (W1):** `--clients 10`, `50`, `100`. Awasi RAM dan CPU (`docker stats --no-stream`); bila klien 100 menimbulkan galat koneksi (`too many clients`), catat dan sebut di laporan. Batas koneksi bawaan
  PostgreSQL 100; itu bukan kesalahan, tetapi batas yang harus dicatat.
- **PostGIS, E1 (tanpa indeks, hanya S10):** `docker exec sen12ls-postgis psql -U postgres -d sen12ls -f /sql/drop_indexes.sql`, jalankan W2 sampai W4 dengan `--note "varian=tanpa-indeks"`, lalu
  bangun lagi dengan `catat.py ukur ... indeks ... -f /sql/indexes.sql` (perintah persisnya di [PANDUAN_Sofi.md](PANDUAN_Sofi.md), 27.4). Tanpa indeks di S100 sangat lambat; jangan.
- **Rencana kueri:** simpan keluaran `-v explain=1` untuk W2 sampai W4 di S100 (indeks apa; berapa baris dibuang oleh filter; berapa lama). Itu bahan penjelasan laporan.
- **Spark:** tiap `run_sql.py` menyalakan sesi baru, jadi tidak ada `docker restart` untuk cold. Di S100 pakai `--limit-titik 20` untuk W1 sampai W4 (aturan di Sofi #27).
  Awasi `docker stats --no-stream`; bila container Spark berhenti (`Exited (137)`), catat dan `[BLOKIR]`.
- **Satu penyimpanan sekali waktu:** selesaikan semua uji PostGIS (S1, S10, S100), baru pindah ke HDFS dan Spark (tabel pindah di atas).

---

## #28. Membantu uji silang jumlah hasil di S100

Sofi memimpin. Kamu memastikan jumlah hasil PostGIS dan Spark di S100 untuk W1 sampai W6 sama dengan wasit S100 (`python bench\kebenaran.py --skala S100 --tulis`, sekitar 1 GB RAM dan beberapa menit)
dan dengan MongoDB:

```powershell
python bench\compare_counts.py results\<postgis W2 S100>.csv results\<spark W2 S100>.csv results\<mongodb W2 S100>.csv
```

Selisih berarti ada yang salah; analisis berurutan seperti pesan di keluaran perintahnya (skala yang dimuat; indeks; Parquet sama dengan CSV), lalu `[BLOKIR]` bila belum ketemu. Selama selisih belum dijelaskan,
**jangan** memakai hasil waktu kueri yang bersangkutan di laporan.

---

## #29. Menulis bagian PostGIS dan baseline untuk laporan

Bagianmu: **menjelaskan mengapa angkanya begitu**, dengan bukti dari rencana kueri dan ukuran. Tulis di `docs/laporan_levi.md` (bagian 3 PostGIS dan bagian 4 Baseline HDFS-Parquet dari kerangka laporan di
[PANDUAN_Wildan.md](PANDUAN_Wildan.md), #30), dengan angka dari `results/ringkasan.csv`, `results/banding.csv`, dan `python bench\catat.py tampil`. Klaim yang tidak diukur ditulis sebagai hipotesis.

**Bagian 3. PostGIS (5 sampai 10 kalimat, plus tabel kecil)**

- Mengapa PostGIS: skema tegas, GiST, `ST_Intersects`, SQL untuk W4 sampai W6.
- Skema dan indeks: `annotations` (23 kolom, `center` titik, `bbox` poligon, SRID 4326), `patches`; indeks GiST pada `center` dan `bbox`, btree pada tanggal dan atribut.
- Bukti: kutipan `EXPLAIN` W2 sampai W4 (indeks dipakai; baris yang dibuang oleh filter), waktu muat, waktu indeks, dan ukuran di S1, S10, S100, serta E1 (dengan dan tanpa indeks).
- Penjelasan W5 dan W6 (agregasi seluruh tabel; indeks tidak membantu) dan W1 banyak klien (batas koneksi).
- Keterbatasan jujur: `geometry` planar (bukan `geography`); E4 belum ada skrip; satu laptop.

**Bagian 4. Baseline HDFS-Parquet (5 sampai 10 kalimat, plus tabel kecil)**

- Arsitektur: satu NameNode, dua DataNode, replikasi 2, Parquet ZSTD, Spark SQL `local[2]` 2 GB; **tanpa** indeks spasial (W2 sampai W4 memindai dengan pra-filter pada kolom koordinat).
- Bukti: ukuran (`ukuran_total` dan `ukuran_dengan_replika`), waktu muat (termasuk menyalakan Spark), W2 sampai W6 di S1, S10, S100, dan bentuk kurva skalanya.
- Penjelasan H1 (selisih dengan indeks), H3 (ukuran), dan H4 (agregasi); kejujuran soal biaya menyalakan Spark di data kecil.
- Keterbatasan: Sedona dan GeoParquet tidak dipakai; E3 (Parquet diurutkan menurut `location`) opsional dan belum ada skrip; W10 (matikan DataNode) belum ada skrip.

```powershell
git add docs/laporan_levi.md
git commit -m "[docs] bagian PostGIS dan baseline untuk laporan"
git pull --rebase
git push
```

**Berhasil bila (#29):** `docs/laporan_levi.md` memuat kedua bagian dengan angka yang punya sumber berkas, dan sudah di GitHub.

**Pesan WhatsApp:** `[SELESAI] docs: bagian 3 (PostGIS) dan bagian 4 (baseline HDFS-Parquet) laporan sudah di docs/laporan_levi.md`
