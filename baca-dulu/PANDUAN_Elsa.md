# Panduan Elsa (Storage A: MongoDB; membantu analisis kinerja)

Folder milikmu: `mongodb/`. Kamu memimpin **MongoDB**: menyalakannya di Docker, memuat data, membuat indeks, menjalankan kueri, dan
menjelaskan hasilnya. Hal umum (terminal, Git, Docker, VS Code) ada di [01_PERSIAPAN_UMUM.md](01_PERSIAPAN_UMUM.md); peta seluruh
pekerjaan di [00_ALUR_KERJA.md](00_ALUR_KERJA.md); nama dan perintah baku di [KONTRAK.md](KONTRAK.md); arti kolom di
[../data/KAMUS_DATA.md](../data/KAMUS_DATA.md).

> Berkas inti sudah ada dan sudah diuji dengan MongoDB **tiruan** (tanpa Docker): `mongodb/docker-compose.yml`, `indexes.js`,
> `drop_indexes.js`, `muat_pymongo.py`, dan `queries/w1.js` sampai `w6.js`. **Yang belum pernah dijalankan pada MongoDB sungguhan**
> adalah semua perintah `docker` di bawah; kamulah yang pertama membuktikannya. Bila ada perintah yang gagal, itu temuan berharga:
> tulis `[BLOKIR]` dengan pesan galatnya, dan perbaikan berkas di `mongodb/` adalah hakmu (commit `[mongodb] ...`).

## Peta langkahmu

| # | Langkah | Menunggu | Perkiraan waktu | Membuka |
|---|---|---|---|---|
| 3 | Pasang alat (Git, Python, VS Code, **Docker**) + pustaka `pymongo` | - | 30 sampai 60 menit | #4 |
| 4 | Clone repo dan latihan Git | #2 (Wildan) dan #3 | 15 sampai 20 menit | #6 |
| 5 | Tulis spesifikasi laptop di grup | - | 5 menit | #7 |
| 7 | KICKOFF | #6 | 30 menit | #9 |
| **9** | **Docker MongoDB** (kamu memimpin, Sofi membantu) | #7 | 30 sampai 45 menit | #13 |
| 11 | Membantu Sofi: pahami kueri, uji sambungan | #7 | 30 sampai 45 menit | #17 |
| **13** | **Muat S1, indeks, W3** (kamu memimpin, Sofi membantu) | #8 (Syuep) dan #9 | 30 sampai 45 menit | #17 |
| 17 | Membantu Sofi: harness W3 di MongoDB | #11, #13, #14, #15 | 45 sampai 60 menit | #18 |
| 18 | SINKRON 1 | #17 | 30 sampai 45 menit | #25 |
| 19 | Baca dokumen rancangan | #7 | 45 menit | #20 |
| 20 | Bahan slide 3 dan 4 (bagian MongoDB) | #19 | 30 menit | #22 |
| 23 | Tinjau silang (dengan Levi) | #22 | 45 menit | #24 |
| 24 | Latihan pitching (SINKRON 2) | #23 | 45 sampai 60 menit | - |
| **25** | **W1 sampai W6 benar di S1 di MongoDB** | #18 | 1 sampai 2 jam | #26 |
| 26 | Muat S10 lalu S100 di MongoDB (laptop uji) | #16 (Syuep) dan #25 | beberapa jam, sebagian besar menunggu | #27 |
| 27 | Membantu Sofi menjalankan W1 sampai W8 | #26 | menyesuaikan | #28 |
| 28 | Membantu uji silang jumlah hasil di S100 | #27 | 1 jam | #29 |
| 29 | Membantu tabel, grafik, dan hipotesis | #28 | 2 sampai 3 jam | #30 |

---

## #3, #4, #5. Alat, clone, spesifikasi

- **#3 Pasang alat:** [01_PERSIAPAN_UMUM.md](01_PERSIAPAN_UMUM.md) bagian A2, **termasuk Docker Desktop dan `.wslconfig`**, lalu pustaka Python:

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
Set-Content latihan\elsa.txt "Halo, ini latihan Elsa"
git add latihan/elsa.txt
git commit -m "[latihan] Elsa: uji coba push"
git pull --rebase
git push
```

Tulis di grup: `[SELESAI] latihan: clone dan push berhasil (latihan/elsa.txt) - Elsa`. Periksa baris namamu di `TEAM.md`
(username `ElsaCP`).

- **#5 Spesifikasi:** bagian A4; tulis di grup.

---

## #9. Docker MongoDB (kamu memimpin, Sofi membantu)

**Tujuan.** MongoDB 8 berjalan di Docker dengan nama dan port yang tetap, dan folder `data` terpasang di dalamnya.

**Menunggu:** kickoff (#7). Docker Desktop harus sudah **Engine running**.

### 9.1 Pastikan tidak ada penyimpanan lain yang aktif

```powershell
cd C:\proyek\kelompok2-bigdata-storage
git pull --rebase
docker ps
```

Daftar harus kosong dari container `sen12ls-*` lain. Bila ada, matikan di foldernya (`docker compose stop`).

### 9.2 Nyalakan MongoDB

```powershell
cd mongodb
docker compose up -d
docker compose ps
```

Pertama kali, Docker mengunduh image `mongo:8` (sekitar 1 GB; 2 sampai 10 menit).

Contoh hasil:

```text
NAME            IMAGE     COMMAND                  SERVICE   CREATED          STATUS          PORTS
sen12ls-mongo   mongo:8   "docker-entrypoint.s..."  mongo     20 seconds ago   Up 19 seconds   0.0.0.0:27017->27017/tcp
```

### 9.3 Uji lima hal

```powershell
docker exec sen12ls-mongo mongosh --quiet --eval "db.version()"
docker exec sen12ls-mongo mongosh --quiet --eval "db.runCommand({ping: 1}).ok"
docker exec sen12ls-mongo mongosh --quiet --eval "db.serverStatus().wiredTiger.cache['maximum bytes configured']"
docker exec sen12ls-mongo ls /sen12ls-data /scripts
docker exec sen12ls-mongo mongoimport --version
```

Contoh hasil:

```text
8.0.x
1
536870912
/scripts:
docker-compose.yml  drop_indexes.js  indexes.js  muat_pymongo.py  queries

/sen12ls-data:
CHECKSUMS.txt  KAMUS_DATA.md  cek_data.py  ...  out  raw
mongoimport version: 100.x.x
```

Artinya berurutan: versi MongoDB; server menjawab; **cache WiredTiger dibatasi 0,5 GB** (536870912 byte); folder `mongodb/` terpasang di
`/scripts` dan folder `data/` terpasang di `/sen12ls-data`; alat `mongoimport` ada.

### 9.4 Uji sambungan dari Python (jalur yang dipakai harness)

```powershell
cd ..
python -c "import pymongo; print(pymongo.MongoClient('mongodb://localhost:27017', serverSelectionTimeoutMS=3000).server_info()['version'])"
```

Contoh hasil: `8.0.x`. Lihat juga pemakaian memori: `docker stats --no-stream`.

**Berhasil bila (#9)**

- [ ] `docker compose ps` menampilkan `sen12ls-mongo` berstatus `Up`
- [ ] `db.version()` dan `ping` menjawab; cache WiredTiger = 536870912
- [ ] `/sen12ls-data` dan `/scripts` terisi (pemasangan folder berhasil)
- [ ] `mongoimport --version` menjawab (bila tidak: catat, pakai cadangan di #13)
- [ ] Python berhasil terhubung dari Windows

**Pesan WhatsApp**

```text
[SELESAI] mongodb: MongoDB 8 jalan di Docker (sen12ls-mongo, port 27017), cache 0,5 GB, folder data terpasang,
mongoimport <ada / tidak ada>, koneksi dari Python berhasil. Siap memuat S1 (#13) setelah Syuep selesai #8.
```

### Kalau macet

| Tanda | Penyebab dan cara memperbaiki |
|---|---|
| `Bind for 0.0.0.0:27017 failed: port is already allocated` | Ada MongoDB lain (container atau layanan Windows) di port itu. `docker ps`; matikan yang bentrok. Layanan Windows: Services > MongoDB > Stop. |
| `/sen12ls-data` kosong | Pemasangan folder gagal. Pastikan repo ada di `C:\proyek` dan Docker Desktop > Settings > Resources > File sharing mengizinkan drive C. Lalu `docker compose down` dan `docker compose up -d` lagi. |
| `mongoimport: executable file not found` | Image tidak membawa `mongoimport`. Catat; di #13 pakai cadangan `python mongodb\muat_pymongo.py --skala S1`. Beri tahu Sofi dan Wildan (kontrak diperbarui). |
| `Error response from daemon: ... no matching manifest` | Arsitektur CPU tidak cocok dengan image. `[BLOKIR]` dengan hasil `docker version`. |
| container langsung `Exited` | `docker compose logs --tail 50`; salin pesannya ke `[BLOKIR]`. Penyebab umum: memori WSL terlalu kecil (`.wslconfig`, A2) atau disk penuh. |
| `serverSelectionTimeoutMS` / Python tidak bisa terhubung | Container belum siap (tunggu 10 detik) atau port berbeda. `docker compose ps` harus menunjukkan `0.0.0.0:27017->27017`. |

---

## #11. Membantu Sofi: pahami kueri dan uji sambungan

Sofi memimpin (harness, 100 titik tetap, wasit). Bagianmu: memastikan sisi MongoDB benar dan kamu **paham apa yang diukur**.

### 11.1 Ambil kode dan jalankan uji tanpa Docker

```powershell
cd C:\proyek\kelompok2-bigdata-storage
git pull --rebase
python tests\uji_semua.py
```

**Berhasil bila** berakhir `SEMUA UJI LULUS`. (Uji ini memakai MongoDB tiruan: membuktikan kodenya benar, bukan MongoDB sungguhan.)

### 11.2 Baca tiga berkas (30 menit)

1. `mongodb/queries/_umum.js`: fungsi `jendela` (jendela persegi), `cincin` (tepi jendela dipadatkan tiap 0,005 derajat supaya garis
   bola mendekati garis lurus), dan `ringkasPlan` (indeks apa yang dipakai kueri).
2. `mongodb/queries/w3.js` dan `w4.js`: W3 memakai `$geoWithin` pada `center` + rentang tanggal; W4 memakai `$geoIntersects`
   pada `bbox` + `event_type` + `event_conf >= 0,9`.
3. `bench/kueri.py`: **definisi tunggal** semua kueri (dipakai MongoDB, PostGIS, dan Spark). Cari fungsi `jendela`, `cincin_mongo`,
   `filter_mongo`, `PIPA_W5`, `PIPA_W6`.

Pertanyaan untuk diri sendiri (akan muncul di pitching): mengapa batas jendela **digeser setengah langkah (5e-8 derajat)** dari
kisi koordinat? Jawab: semua koordinat data berada pada kisi 1e-7 derajat, jadi tidak ada titik tepat di tepi jendela; dengan begitu
MongoDB (bola) dan PostGIS/Spark (bidang datar) **harus** memberi jumlah yang sama persis.

### 11.3 Uji sambungan harness ke MongoDB (setelah #9)

Data belum dimuat, jadi hasil yang benar justru **pesan berhenti**:

```powershell
python bench\harness.py --store mongodb --workload W1 --scale S1
```

Contoh hasil yang benar saat ini:

```text
Jumlah data di mongodb (annotations): 0 (harapan untuk S1: 74956)
Jumlah data tidak cocok. Muat skala S1 dulu, atau jalankan lagi dengan --force.
```

Artinya harness **berhasil terhubung** ke MongoDB dan menolak menguji data yang salah (pagar anti salah label). Bila yang muncul
`Tidak bisa terhubung ke mongodb: ...`: periksa #9 (container jalan) dan `pip install pymongo`.

**Berhasil bila:** pesan di atas muncul. **Pesan WhatsApp:** `[SELESAI] bench: sisi MongoDB dipahami; harness terhubung ke MongoDB (Elsa).`

---

## #13. Muat S1 ke MongoDB, buat indeks, jalankan W3 (kamu memimpin, Sofi membantu)

**Menunggu:** #8 (Syuep membuktikan S1 benar) dan #9 (MongoDB jalan).

### 13.0 Buat S1 di laptopmu dan buktikan sama dengan milik Wildan

`data\out\` tidak ada di GitHub; tiap orang membuatnya sendiri (2 sampai 4 menit) dari berkas mentah di repo:

```powershell
cd C:\proyek\kelompok2-bigdata-storage
git pull --rebase
python data\convert_inventory.py
python data\generate_scales.py --verify
```

**Berhasil bila:** konversi berakhir `LOLOS: 17 pemeriksaan cocok` dan `--verify` menampilkan empat `COCOK` untuk `out/s1/...`
(baris `BELUM ADA` untuk S10 dan S100 boleh muncul). Bila `BEDA`: berhenti, tulis `[BLOKIR]` ke Syuep.

### 13.1 Muat dua koleksi (waktu tercatat otomatis)

`python bench\catat.py ukur ...` di depan perintah menjalankan perintahnya seperti biasa, mengukur lamanya, dan mencatat ke
`results\pengukuran_mongodb.csv` bila berhasil.

```powershell
python bench\catat.py ukur --store mongodb --skala S1 --jenis muat --objek annotations docker exec sen12ls-mongo mongoimport --db sen12ls --collection annotations --drop --file /sen12ls-data/out/s1/annotations.ndjson
python bench\catat.py ukur --store mongodb --skala S1 --jenis muat --objek patches docker exec sen12ls-mongo mongoimport --db sen12ls --collection patches --drop --file /sen12ls-data/out/s1/patches.ndjson
```

Tulis tiap perintah dalam **satu baris**. **Jangan** memakai `--jsonArray` (berkasnya NDJSON, satu dokumen per baris).

Contoh hasil:

```text
2026-11-01T10:00:00.000+0000	connected to: mongodb://localhost/
2026-11-01T10:00:03.000+0000	dropping: sen12ls.annotations
2026-11-01T10:00:09.000+0000	74956 document(s) imported successfully. 0 document(s) failed to import.

Tercatat: mongodb S1 muat (annotations) = 9.8 detik  ->  C:\...\results\pengukuran_mongodb.csv
```

(Waktu di laptopmu berbeda.) Patches: `4392 document(s) imported successfully`.

Cadangan bila `mongoimport` tidak ada di container (lebih lambat; cukup untuk S1 dan S10):

```powershell
python mongodb\muat_pymongo.py --skala S1
```

### 13.2 Periksa jumlah dan bentuk dokumen

```powershell
docker exec sen12ls-mongo mongosh --quiet --eval "const d = db.getSiblingDB('sen12ls'); print(d.annotations.countDocuments({}) + ' ' + d.patches.countDocuments({}))"
docker exec sen12ls-mongo mongosh --quiet --eval "printjson(db.getSiblingDB('sen12ls').annotations.findOne({_id: 0}))"
```

Contoh hasil (nilai bentuknya ilustrasi; milikmu berbeda):

```text
74956 4392
{
  _id: 0,
  location: 'Italy',
  inventory: 'italy',
  event_type: 'Rainfall',
  ...
  dates: { pre: ISODate('2016-03-25T00:00:00.000Z'), event: ISODate('2016-04-01T00:00:00.000Z'), ... },
  center: { type: 'Point', coordinates: [ 11.4548681, 43.7734078 ] },
  bbox: { type: 'Polygon', coordinates: [ [ [ 11.4541927, 43.7728399 ], ... ] ] },
  sim_batch: 0
}
```

Perhatikan: tanggal tampil sebagai `ISODate(...)` (bukan teks); `center` adalah titik GeoJSON; **field yang kosong tidak ada** (bukan `null`).

### 13.3 Buat indeks (waktu tercatat)

```powershell
python bench\catat.py ukur --store mongodb --skala S1 --jenis indeks --objek semua docker exec sen12ls-mongo mongosh --quiet --file /scripts/indexes.js
```

Contoh hasil (bagian akhir):

```text
Jumlah dokumen: annotations 74956, patches 4392
Indeks annotations.center_2dsphere (center 2dsphere (titik pusat)): 640 ms
Indeks annotations.bbox_2dsphere (bbox 2dsphere (kotak pembatas)): 520 ms
Indeks annotations.dates.event_1 (tanggal kejadian): 90 ms
...
Total waktu bangun indeks: 1.6 detik
Indeks annotations:
  _id_
  center_2dsphere
  bbox_2dsphere
  dates.event_1
  event_type_1_dates.event_1
  location_1_dates.event_1
Indeks patches:
  _id_
  inventory_1_split_1
```

**Penting:** `mongoimport --drop` menghapus koleksinya **beserta indeksnya**, jadi indeks selalu dibangun **setelah** memuat.

### 13.4 Catat ukuran di disk

```powershell
python bench\catat.py ukuran --store mongodb --skala S1
```

Contoh hasil: beberapa baris `ukuran_data_tak_terkompres`, `ukuran_data_di_disk`, `ukuran_indeks`, `ukuran_total` (MiB) untuk `annotations` dan
`patches`, lalu `Tercatat N baris  ->  ...pengukuran_mongodb.csv`. Angka ini bahan hipotesis H3 (ukuran terkecil sampai terbesar).

### 13.5 Jalankan W3 dengan tangan dan cocokkan dengan wasit

```powershell
docker exec sen12ls-mongo mongosh --quiet --file /scripts/queries/w3.js
python bench\kebenaran.py --skala S1 --ann 0
```

Contoh hasil `w3.js`:

```text
Titik uji: (11.4548681, 43.7734078), tanggal 2016-04-01
W3: 1 anotasi
Rencana kueri:
  tahap rencana : LIMIT > ... IXSCAN > FETCH
  indeks dipakai: center_2dsphere
  dikembalikan 1, kunci diperiksa 12, dokumen diperiksa 12, 3 ms
```

(Tahap dan indeks yang dipilih MongoDB boleh berbeda; yang penting **indeks dipakai**, bukan `TIDAK ADA`.) Bagian `W3:` pada keluaran
`kebenaran.py --ann 0` harus menyebut **jumlah yang sama** dengan baris `W3:` dari MongoDB.

Bila muncul `Anotasi 0 tidak punya tanggal kejadian; pilih ANN_ID lain`: ubah baris `const ANN_ID = 0;` di `mongodb/queries/w3.js` ke angka lain
(mis. 100 atau 1000), lalu ulangi kedua perintah dengan angka itu (`--ann 100`).

### 13.6 Simpan ke GitHub

```powershell
git add results/pengukuran_mongodb.csv
git status
git commit -m "[results] pengukuran MongoDB S1: muat, indeks, ukuran"
git pull --rebase
git push
```

**Berhasil bila (#13)**

- [ ] `74956 4392` (jumlah dokumen) dan `ISODate(...)` pada tanggal
- [ ] enam indeks `annotations` dan dua indeks `patches` terbentuk (termasuk `_id_`)
- [ ] `results/pengukuran_mongodb.csv` berisi waktu muat (dua baris), waktu indeks, dan ukuran
- [ ] W3 tangan = jumlah wasit untuk anotasi yang sama, dan rencana kueri memakai indeks
- [ ] perubahan sudah di-push

**Pesan WhatsApp**

```text
[SELESAI] mongodb: S1 termuat (74956 anotasi, 4392 patch), indeks dibuat (<detik>), W3 tangan = wasit (<jumlah>).
Waktu muat <detik>; ukuran total <MiB> (results/pengukuran_mongodb.csv).
```

### Kalau macet

| Tanda | Penyebab dan cara memperbaiki |
|---|---|
| `Failed: open /sen12ls-data/out/s1/annotations.ndjson: no such file` | Berkas S1 belum dibuat (13.0) atau pemasangan folder gagal: `docker exec sen12ls-mongo ls /sen12ls-data/out/s1`. Kosong: ulangi 13.0, lalu cek File sharing Docker. |
| `Failed: error processing document #...: invalid character` | Berkas salah format. Pastikan tidak ada `--jsonArray` dan berkasnya NDJSON hasil `convert_inventory.py`. |
| `... document(s) failed to import` lebih dari 0 | Baca baris galat di atasnya. Umumnya `E11000 duplicate key`: koleksi sudah berisi data dan perintah tanpa `--drop`. Tambahkan `--drop`. |
| `The term 'docker' is not recognized` di dalam `catat.py` | Docker belum terpasang di PATH; buka PowerShell baru setelah memasang Docker (A2). |
| `Perintah berakhir dengan kode ..., jadi waktunya TIDAK dicatat` | Perintah di dalam gagal. Baca galatnya; waktu hanya dicatat bila berhasil. |
| Indeks gagal: `Can't extract geo keys` atau `Loop is not valid` | Ada geometri tidak sah (mis. kotak tanpa lebar). `python data\cek_data.py --skala S1` harus lulus 18 pemeriksaan; bila lulus, `[BLOKIR]` dengan **seluruh** pesan dan `_id` dokumen yang disebut. |
| `w3.js`: `load(...) is not defined` atau `_umum.js` tidak ditemukan | Jalankan lewat `docker exec ... mongosh --file /scripts/queries/w3.js` (bukan `mongosh` di Windows). Jalur `/scripts` hanya ada di container. |
| Hasil W3 tangan berbeda dari wasit | Pastikan `ANN_ID` sama dan indeks dibuat. Bila tetap beda: `[BLOKIR]` dengan kedua keluaran; **jangan** menyesuaikan angka supaya cocok. |
| Muat lama sekali | S1 hanya beberapa detik. Bila lebih dari 2 menit: `docker stats --no-stream` (cek memori), tutup program berat. |

---

## #17. Membantu Sofi: harness W3 di MongoDB

Sofi memimpin dan menggabungkan hasil ketiga penyimpanan; kamu menjalankan sisi MongoDB.

```powershell
cd C:\proyek\kelompok2-bigdata-storage
git pull --rebase
python bench\harness.py --store mongodb --workload W3 --scale S1
```

Contoh hasil:

```text
Jumlah data di mongodb (annotations): 74956 (harapan untuk S1: 74956)
Pemanasan: satu putaran 100 kueri (tidak dicatat)...
Ulangan 1 selesai (100 kueri)
Ulangan 2 selesai (100 kueri)
Ulangan 3 selesai (100 kueri)

Ringkasan mongodb W3 S1 (warm, 3 ulangan x 100 kueri = 300 eksekusi)
  median : 2.1 ms
  p95    : 4.8 ms
  p99    : 9.0 ms
  rata2  : 2.6 ms
  hasil  : 81 per putaran; 70 dari 100 kueri punya hasil
Berkas   : C:\...\results\20261101_mongodb_W3_S1.csv
```

(Angka waktu dan jumlah hasil di datamu berbeda; yang harus sama: **100 kueri**, **70 dari 100** punya hasil, dan tidak ada tulisan `GALAT`.)

Periksa terhadap wasit (satu berkas dibandingkan dengan jawaban benar; ganti nama berkas dengan yang dicetak harness):

```powershell
python bench\compare_counts.py results\20261101_mongodb_W3_S1.csv
```

```text
Perbandingan W3 S1: mongodb vs benar
Cocok: 100 dari 100 kueri.
Semua jumlah hasil sama.
```

Simpan hasilnya ke GitHub supaya Sofi bisa menggabungkan:

```powershell
git add results/20261101_mongodb_W3_S1.csv
git commit -m "[results] mongodb W3 S1 (3 ulangan, warm)"
git pull --rebase
git push
```

**Catatan.** Di #17 hanya **jumlah hasil** yang dibandingkan antar penyimpanan. Waktu dari laptop yang berbeda tidak dibandingkan;
perbandingan waktu yang adil dilakukan di laptop uji (#26 dan #27).

**Berhasil bila:** `Cocok: 100 dari 100 kueri`, berkas CSV sudah di GitHub. **Pesan WhatsApp:** `[SELESAI] results: mongodb W3 S1 cocok dengan wasit (100 dari 100). Berkas: results/<nama>.csv`

Bila ada kueri yang beda: lihat tabel selisihnya, lalu cek berurutan: (1) skala yang dimuat benar (74956), (2) indeks sudah ada, (3)
S1 di laptopmu COCOK dengan checksum. Tetap beda: `[BLOKIR]` dengan tabelnya.

---

## #18. SINKRON 1

Yang kamu siapkan dan tunjukkan (4 menit, bersama Sofi):

- [ ] `docker compose ps` (MongoDB jalan) dan jumlah dokumen `74956 4392`
- [ ] daftar indeks dan satu rencana kueri W3 yang memakai indeks
- [ ] hasil `compare_counts.py` MongoDB terhadap wasit: `Cocok: 100 dari 100 kueri`
- [ ] waktu muat dan ukuran dari `python bench\catat.py tampil`

Pesan setelah Sinkron 1: `[SELESAI] Sinkron 1: hasil MongoDB sudah ditunjukkan dan dicatat.`

---

## #19. Baca dokumen rancangan

Tautan ada di grup (Wildan menulis `[SELESAI] dokumen v2` saat versi final siap). Baca bagian **Justifikasi pemilihan teknologi**
(MongoDB dan perbandingannya) dan **model data**, dan periksa:

- [ ] model dokumen cocok dengan kenyataan: `center` titik GeoJSON, `bbox` poligon, `dates.event`, field kosong tidak ditulis
- [ ] nama koleksi (`annotations`, `patches`), indeks, dan jenis kueri W2 sampai W4 cocok dengan `mongodb/`
- [ ] klaim kinerja ditulis **hipotesis**; tidak ada klaim konsistensi atau ketersediaan yang kita **tidak uji** (kita memakai satu node tanpa replica set)
- [ ] tidak ada sisa nama dataset lama

Bentuk pesan temuan: `Dokumen - <bagian> - <yang salah atau kurang> - usul: <perbaikan>`. Tidak ada temuan:
`Dokumen - bagianku sudah benar (Elsa)`.

---

## #20. Bahan slide 3 dan 4 (bagian MongoDB)

Kirim ke Wildan **3 sampai 5 poin** per slide (satu kalimat pendek, paling banyak 12 kata) dan **satu gambar** per slide.

**Slide 3: arsitektur dan alur data**

- Satu sumber, tiga penyimpanan: data yang sama dimuat ke MongoDB, PostGIS, dan HDFS-Parquet
- Alur: konversi, muat, indeks, kueri, hasil CSV; semuanya berjalan di Docker
- Memori dibatasi dan satu penyimpanan aktif sekali waktu, supaya adil
- Wasit menghitung jawaban benar langsung dari CSV, tanpa database

Gambar: diagram arsitektur dari Wildan (#21), atau tangkapan layar `docker compose ps` MongoDB.

**Slide 4: mengapa MongoDB (bagianmu)**

- Satu anotasi = satu dokumen; field kosong tidak ditulis (skema fleksibel)
- Titik pusat dan kotak pembatas sebagai GeoJSON dengan indeks `2dsphere`
- W2 memakai `$geoWithin` pada titik; W4 memakai `$geoIntersects` pada kotak
- Hipotesis: indeks spasial mengalahkan Parquet (H1); PostGIS lebih cepat di W4 (H2). **Belum diuji**

Gambar: contoh satu dokumen (tangkapan layar `findOne`) atau daftar indeks.

```text
[SELESAI] bahan slide 3 dan 4 (Elsa): <poin> dan gambar terlampir
```

---

## #23. Tinjau silang (dengan Levi)

Kamu meninjau **bagian Levi** (justifikasi PostGIS dan baseline HDFS-Parquet, skema, dan kueri SQL); Levi meninjau bagianmu.

Daftar periksa untuk bagian Levi:

- [ ] W2 (titik pusat di jendela), W3 (+30 hari), W4 (kotak beririsan + `event_type` + `event_conf >= 0,9`) **berarti hal yang sama** dengan versi MongoDB
- [ ] batas jendela sama (±0,01 dan ±0,1 derajat, digeser setengah langkah); batas tertutup
- [ ] kolom dan tipe di skema sama dengan `data/KAMUS_DATA.md`
- [ ] indeks GiST pada `center` dan `bbox`, dan indeks atribut, disebut dan dijelaskan
- [ ] baseline Parquet dijelaskan sebagai **tanpa indeks spasial** (bukan "lambat karena buruk")
- [ ] istilah dan angka konsisten dengan dokumen dan slide

Cara: baca bagiannya sekali penuh tanpa mengomentari; baca lagi dan catat; kirim `[Tinjau] @Levi - <bagian> - <temuan> - Saran: <perbaikan>`.

---

## #24. Latihan pitching (SINKRON 2)

Kamu menyampaikan **slide 3 dan bagian MongoDB di slide 4** (sekitar 2 menit) dan menjawab (bank pertanyaan di
[PANDUAN_Wildan.md](PANDUAN_Wildan.md), #24): **"Mengapa MongoDB?"**, **"Apa beda 2dsphere dan geometry?"** (bersama Levi), dan
**"Mengapa bukan Elasticsearch, Cassandra, Redis, Neo4j, atau TimescaleDB?"** (bersama Levi). Latih dengan kata-katamu sendiri.

---

## #25. W1 sampai W6 benar di S1 di MongoDB

**Menunggu:** #18 (Sinkron 1). **Tujuan:** keenam kueri berjalan di MongoDB dan **jumlah hasilnya sama dengan wasit**.

```powershell
cd C:\proyek\kelompok2-bigdata-storage
git pull --rebase
foreach ($w in "W1","W2","W3","W4","W5","W6") { python bench\harness.py --store mongodb --workload $w --scale S1 }
```

Memerlukan beberapa menit. Setiap eksekusi menulis `results\YYYYMMDD_mongodb_W?_S1.csv`. Lalu bandingkan **tiap berkas terbaru** dengan wasit:

```powershell
foreach ($w in "W1","W2","W3","W4","W5","W6") {
  $f = Get-ChildItem ("results\*_mongodb_" + $w + "_S1.csv") | Sort-Object LastWriteTime | Select-Object -Last 1
  python bench\compare_counts.py $f.FullName
}
```

**Berhasil bila** enam kali `Semua jumlah hasil sama` (W5 dan W6: 1 kueri, jumlahnya = jumlah kelompok). Contoh:

```text
Perbandingan W5 S1: mongodb vs benar
Cocok: 1 dari 1 kueri.
Semua jumlah hasil sama.
```

Bila ada yang beda (paling mungkin W4): **jangan** mengubah jendela atau tanggal supaya cocok. Simpan tabel selisih
dan tulis `[BLOKIR]`; penyebab yang mungkin: indeks belum ada, data tidak sama dengan S1, atau perbedaan bola dan bidang datar
yang tidak terduga di dekat tepi jendela (hanya uji sungguhan yang memastikan).

Simpan hasilnya:

```powershell
git add results
git commit -m "[results] mongodb W1 sampai W6 S1, cocok dengan wasit"
git pull --rebase
git push
```

Dua pemeriksaan tambahan yang berguna untuk pitching:

```powershell
docker exec sen12ls-mongo mongosh --quiet --file /scripts/queries/w4.js
docker exec sen12ls-mongo mongosh --quiet --file /scripts/queries/w5.js
```

Amati rencana W4 (indeks apa yang dipilih; berapa dokumen diperiksa) dan jumlah kelompok W5.

**Pesan WhatsApp:** `[SELESAI] mongodb: W1 sampai W6 di S1 cocok dengan wasit (6 dari 6). Berkas di results/.`

---

## #26. Muat S10 lalu S100 di MongoDB (laptop uji)

**Menunggu:** #16 (Syuep: S10 dan S100 siap dan `CHECKSUMS.txt`) dan #25.

Pengukuran waktu yang adil berjalan di **satu laptop uji** (dipilih saat kickoff). Pemilik laptop itu menjalankan perintah; kamu
mendampinginya lewat berbagi layar atau bergantian memakai laptopnya. Urutan praktis: **selesaikan satu penyimpanan sampai tuntas**
(muat, indeks, ukuran, uji #27) sebelum menyalakan penyimpanan berikutnya, supaya disk dan RAM cukup.

### 26.1 Siapkan di laptop uji

```powershell
cd C:\proyek\kelompok2-bigdata-storage
git pull --rebase
python data\generate_scales.py --scale S10
python data\generate_scales.py --scale S100
python data\generate_scales.py --verify
```

**Berhasil bila:** semua berkas `COCOK` (S100 membutuhkan 7,84 GB disk dan sekitar 3 sampai 6 menit). Pastikan **tidak ada penyimpanan lain
yang jalan** (`docker ps`) dan MongoDB berjalan (`cd mongodb; docker compose up -d`).

### 26.2 Muat S10

```powershell
python bench\catat.py ukur --store mongodb --skala S10 --jenis muat --objek annotations docker exec sen12ls-mongo mongoimport --db sen12ls --collection annotations --drop --file /sen12ls-data/out/s10/annotations.ndjson
python bench\catat.py ukur --store mongodb --skala S10 --jenis muat --objek patches docker exec sen12ls-mongo mongoimport --db sen12ls --collection patches --drop --file /sen12ls-data/out/s10/patches.ndjson
python bench\catat.py ukur --store mongodb --skala S10 --jenis indeks --objek semua docker exec sen12ls-mongo mongosh --quiet --file /scripts/indexes.js
python bench\catat.py ukuran --store mongodb --skala S10
```

Periksa jumlahnya: `749560 43920` (lihat 13.2). Lalu Sofi menjalankan uji S10 (#27).

### 26.3 Muat S100 (lama)

Perintahnya sama; ganti `s10` dengan `s100` dan `--skala S10` dengan `--skala S100`:

```powershell
python bench\catat.py ukur --store mongodb --skala S100 --jenis muat --objek annotations docker exec sen12ls-mongo mongoimport --db sen12ls --collection annotations --drop --file /sen12ls-data/out/s100/annotations.ndjson
python bench\catat.py ukur --store mongodb --skala S100 --jenis muat --objek patches docker exec sen12ls-mongo mongoimport --db sen12ls --collection patches --drop --file /sen12ls-data/out/s100/patches.ndjson
python bench\catat.py ukur --store mongodb --skala S100 --jenis indeks --objek semua docker exec sen12ls-mongo mongosh --quiet --file /scripts/indexes.js
python bench\catat.py ukuran --store mongodb --skala S100
```

Waktu muat dan indeks S100 **belum terukur**; perkirakan puluhan menit (7,5 juta dokumen; 5,72 GB NDJSON). Biarkan laptop bekerja,
jangan memakainya untuk hal berat, dan jangan menutup jendela PowerShell. Bila terlalu lambat, `mongoimport` menerima
`--numInsertionWorkers 2`; **bila dipakai, pakai angka yang sama untuk semua pengukuran dan tulis di `--catatan "numInsertionWorkers=2"`**.
Periksa jumlah: `7495600 439200`.

### 26.4 W8: menambah satu batch baru ke S100 (paling akhir)

Setelah semua uji S100 untuk MongoDB selesai, Syuep menyiapkan batch (`python data\generate_scales.py --extra-batch 100`):

```powershell
python bench\catat.py ukur --store mongodb --skala S100 --jenis tambah_batch --objek annotations docker exec sen12ls-mongo mongoimport --db sen12ls --collection annotations --file /sen12ls-data/out/batch100/annotations.ndjson
python bench\catat.py ukur --store mongodb --skala S100 --jenis tambah_batch --objek patches docker exec sen12ls-mongo mongoimport --db sen12ls --collection patches --file /sen12ls-data/out/batch100/patches.ndjson
```

(Tanpa `--drop`; indeks sudah ada sehingga waktunya mencakup pembaruan indeks.) Setelah ini S100 berisi 7.570.556 anotasi; muat ulang
S100 bila harus menguji lagi.

### 26.5 Simpan dan bersihkan

```powershell
git add results
git commit -m "[results] pengukuran MongoDB S10 dan S100: muat, indeks, ukuran"
git pull --rebase
git push
```

Sebelum penyimpanan berikutnya: `cd mongodb; docker compose stop` (data tetap). Bila disk sempit: `docker compose down -v` (**menghapus** datanya;
hasil pengukuran di `results/` tetap aman).

**Pesan WhatsApp:** `[SELESAI] mongodb: S10 dan S100 termuat di laptop uji (waktu muat S10 <detik>, S100 <detik>; ukuran <MiB>). Siap W1 sampai W8 (#27).`

### Kalau macet

| Tanda | Penyebab dan cara memperbaiki |
|---|---|
| `no space left on device` | Disk penuh. Hapus `data\out\s100` bila tidak dipakai, atau `docker system prune` (tanyakan dulu), lalu muat ulang dengan `--drop`. |
| `mongoimport` berhenti di tengah atau container `Exited` | Memori habis. `docker compose logs --tail 50`; naikkan `memory=` di `.wslconfig` (A2) bila RAM laptop mengizinkan, `wsl --shutdown`, ulangi dengan `--drop`. |
| Indeks S100 sangat lama atau gagal memori | Tutup program lain. Cache dibatasi 0,5 GB sengaja (adil); bila gagal, catat dan `[BLOKIR]`. Jangan menaikkan cache hanya untuk MongoDB. |
| Jumlah dokumen tidak sama dengan 7495600 | Muat terpotong. Ulangi dengan `--drop`. |

---

## #27. Membantu Sofi menjalankan W1 sampai W8

Sofi memimpin (urutan, ulangan, hasil). Bagianmu di sisi MongoDB:

- **Cold run:** nyalakan ulang container sebelum tiap putaran dingin, tunggu 20 detik, lalu jalankan harness (perintah lengkapnya di
  [PANDUAN_Sofi.md](PANDUAN_Sofi.md), #27):

  ```powershell
  cd mongodb
  docker compose restart
  cd ..
  ```

- **W1 banyak klien** (`--clients 1`, `10`, `50`, `100`): pastikan RAM dan CPU laptop tidak habis (`docker stats --no-stream`);
  bila klien 100 membuat galat koneksi, catat dan turunkan.
- **E1 (tanpa indeks):** `docker exec sen12ls-mongo mongosh --quiet --file /scripts/drop_indexes.js`, jalankan W2 sampai W4, lalu bangun lagi dengan
  `indexes.js`. Pakai skala S10 untuk E1 (tanpa indeks di S100 sangat lambat).
- **Rencana kueri:** untuk tiap beban kerja yang menarik, simpan keluaran `queries/w2.js` sampai `w4.js` (indeks dipakai atau tidak, dokumen
  diperiksa berapa); itu bahan penjelasan di laporan.

---

## #28. Membantu uji silang jumlah hasil di S100

Sofi memimpin. Kamu memastikan jumlah hasil MongoDB di S100 untuk W1 sampai W6 sama dengan wasit S100
(`python bench\kebenaran.py --skala S100 --tulis`, sekitar 1 GB RAM dan beberapa menit) dan dengan PostGIS dan Spark:

```powershell
python bench\compare_counts.py results\<mongodb W2 S100>.csv results\<postgis W2 S100>.csv results\<spark W2 S100>.csv
```

Selisih berarti ada yang salah; analisis berurutan seperti pesan di keluaran perintahnya, lalu `[BLOKIR]` bila belum ketemu.

---

## #29. Membantu tabel, grafik, dan hipotesis

Bagianmu: **menjelaskan mengapa angkanya begitu** untuk MongoDB, dengan bukti dari rencana kueri dan ukuran:

- W2, W3, W4: indeks apa yang dipakai, berapa dokumen diperiksa; selisih dengan dan tanpa indeks (E1).
- W5, W6: agregasi seluruh koleksi; tidak ada indeks yang membantu; waktu naik sebanding skala?
- W1: pengambilan per `_id`; apa efek banyak klien (H5)?
- Ukuran (H3): data, indeks, dan total MongoDB; mengapa indeks 2dsphere besar?
- Tulis penjelasan 5 sampai 10 kalimat di `docs/laporan_elsa.md` (bagian 3 dan 7 laporan), dengan angka dari `results/ringkasan.csv` dan
  `results/banding.csv`. Klaim yang tidak diukur ditulis sebagai hipotesis.

```powershell
git add docs/laporan_elsa.md
git commit -m "[docs] bagian MongoDB untuk laporan"
git pull --rebase
git push
```
