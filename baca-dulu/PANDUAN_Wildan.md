# Panduan Wildan (Project Lead + Dokumentasi/QA)

Folder milikmu: `docs/`, `tests/`, dan berkas di akar repo (`README.md`, `TEAM.md`, `.gitignore`, `.gitattributes`).
Hal umum (terminal, Git, Docker, VS Code) ada di [01_PERSIAPAN_UMUM.md](01_PERSIAPAN_UMUM.md); peta seluruh pekerjaan di
[00_ALUR_KERJA.md](00_ALUR_KERJA.md); nama dan perintah baku di [KONTRAK.md](KONTRAK.md).

## Peta langkahmu

| # | Langkah | Menunggu | Perkiraan waktu | Membuka |
|---|---|---|---|---|
| **2** | **Pasang paket awal, data mentah, uji, push** | - | 45 sampai 90 menit | #4 semua orang |
| 3 | Alat: Git dan Python sudah ada (Anaconda, Python 3.13); Docker tidak wajib untukmu | - | - | - |
| 5 | Tulis spesifikasi laptopmu di grup | - | 5 menit | #7 |
| 6 | Cek `TEAM.md` dan tentukan jam kickoff | #4 semua | 15 menit | #7 |
| 7 | KICKOFF (kamu memimpin) | #6 | 30 menit | #8 sampai #12, #19 |
| 18 | SINKRON 1 (kamu memimpin) | #17 | 30 sampai 45 menit | #25 |
| 19 | Baca dokumen rancangan; pastikan semua bisa membukanya | #7 | 45 menit | #20, #21 |
| 20 | Bahan slide 1 dan 6 (bagianmu) | #19 | 30 menit | #22 |
| 21 | Diagram arsitektur di draw.io | #19 | 1 sampai 2 jam | #22 |
| 22 | Susun slide pitching (6 slide) | #20 dan #21 | 2 sampai 3 jam | #23 |
| 23 | Tinjau silang: angka, istilah, nama kolom | #22 | 45 menit | #24 |
| 24 | Latihan pitching = SINKRON 2 (kamu memimpin) | #23 | 45 sampai 60 menit | - |
| 30 | Laporan dan slide hasil (kamu menyusun) | #29 | 3 sampai 4 jam | #31 |
| 31 | QA akhir dan kumpul di SIDIA | #30 | 1 sampai 2 jam | - |

Langkah #4 (clone dan latihan Git) sudah kamu lakukan lewat salinan repomu, jadi tidak perlu latihan. Untuk #3 dan #5 lihat
[01_PERSIAPAN_UMUM.md](01_PERSIAPAN_UMUM.md) bagian A2 dan A4.

---

## #2. Pasang paket awal, data mentah, uji, dan push

**Tujuan.** Mengisi repo yang sudah kosong dengan: kode awal semua folder, panduan `baca-dulu/`, data mentah (`data/raw/`),
hasil konversi S1 yang terbukti cocok dengan laporan inventarismu, 100 titik uji, jawaban wasit, dan checksum, lalu
mengirimnya ke GitHub supaya empat anggota bisa clone (#4).

**Yang kamu perlukan**

- ZIP paket awal (`kelompok2-paket-awal.zip`) di folder `Downloads`.
- Salinan repomu (kosong dan bersih) dan folder `cek-sen12ls\` berisi `inventories.zip` dan `splits_aligned.json`
  (yang kamu pakai membuat `laporan_inventaris.txt`).
- PowerShell atau Anaconda Prompt. Awalan `(base)` di depan prompt tidak masalah. `python --version` harus 3.11, 3.12, atau 3.13.
  Skrip data dan uji **tidak butuh pip install** apa pun.

**Aturan keselamatan untuk langkah ini**

- Folder `cek-sen12ls\` **tidak boleh** ikut ke GitHub (`.gitignore` dari paket sudah mengecualikannya, tetapi tetap kamu periksa di 2.10).
- Bila konversi (2.5) tidak berakhir `LOLOS`, **berhenti**. Jangan push apa pun.
- Jangan `git push --force`.

### 2.1 Masuk ke folder repo dan periksa keadaannya

```powershell
cd C:\Users\wildnrfm\Downloads\kelompok2-bigdata-storage
git status
git remote -v
git pull --rebase
```

Contoh hasil:

```text
On branch main
Untracked files:
        cek-sen12ls/
nothing added to commit but untracked files present
origin  https://github.com/wildnrfm/kelompok2-bigdata-storage.git (fetch)
origin  https://github.com/wildnrfm/kelompok2-bigdata-storage.git (push)
Already up to date.
```

(`cek-sen12ls/` tampil sebagai "untracked" sebelum paket diekstrak; itu wajar.)

> **Disarankan:** lebih aman menaruh repo di `C:\proyek\kelompok2-bigdata-storage` seperti anggota lain (folder `Downloads`
> kadang ikut disinkronkan OneDrive). Bila ingin pindah: `mkdir C:\proyek`, `cd C:\proyek`,
> `git clone https://github.com/wildnrfm/kelompok2-bigdata-storage.git`, lalu salin folder `cek-sen12ls` ke dalamnya
> dan lanjutkan dari 2.2 di sana. Boleh juga tetap di `Downloads`; langkah selanjutnya sama.
>
> Bila `git clone` berkata *"You appear to have cloned an empty repository"*: repo benar-benar tanpa commit. Setelah 2.11
> pakai `git branch -M main` dan `git push -u origin main`.

### 2.2 Ekstrak ZIP ke folder repo

ZIP sengaja **tanpa folder pembungkus**: isinya langsung `README.md`, `baca-dulu\`, `data\`, dan seterusnya.

```powershell
Expand-Archive -Path "$env:USERPROFILE\Downloads\kelompok2-paket-awal.zip" -DestinationPath . -Force
dir
```

Contoh hasil:

```text
Mode   Name
----   ----
d----  baca-dulu
d----  bench
d----  cek-sen12ls
d----  data
d----  docs
d----  hdfs-parquet
d----  mongodb
d----  postgis
d----  results
d----  tests
-a---  .gitattributes
-a---  .gitignore
-a---  README.md
-a---  TEAM.md
```

Cadangan bila `Expand-Archive` bermasalah: klik kanan ZIP > Extract All, pilih folder repo; atau
`tar -xf "$env:USERPROFILE\Downloads\kelompok2-paket-awal.zip"` (dari folder repo).

### 2.3 Salin data mentah ke data\raw

```powershell
Copy-Item cek-sen12ls\inventories.zip data\raw\
Copy-Item cek-sen12ls\splits_aligned.json data\raw\
dir data\raw
```

Contoh hasil: `inventories.zip`, `splits_aligned.json`, dan `README.md` (catatan singkat dari paket).

### 2.4 Tulis checksum berkas asli

```powershell
python data\cek_data.py --raw --tulis
```

Contoh hasil:

```text
Berkas asli di C:\...\kelompok2-bigdata-storage\data\raw
  <64 karakter heksadesimal>  inventories.zip              <ukuran> byte
  <64 karakter heksadesimal>  splits_aligned.json          <ukuran> byte
Tertulis C:\...\data\raw\SHA256.txt. Commit berkas ini bersama data\raw\.
```

### 2.5 Konversi ke S1 (langkah penentu)

```powershell
python data\convert_inventory.py
```

Memerlukan sekitar 1 sampai 3 menit. Skrip membaca poligon, menghitung titik pusat dan kotak pembatas, menulis empat berkas
di `data\out\s1\`, lalu **mencocokkan hasilnya dengan `laporan_inventaris.txt` (22 Okt 2026)**.

Contoh hasil (bagian akhir):

```text
Hasil di C:\...\data\out\s1
  annotations.ndjson      56.94 MB
  annotations.csv         19.52 MB
  patches.ndjson           0.95 MB
  patches.csv              0.50 MB
  anotasi: 74956 baris | patch: 4392 baris

Pemeriksaan diri terhadap laporan_inventaris.txt (22 Okt 2026):
  OK     jumlah anotasi
  OK     id 0..74955 dan unik
  OK     anotasi tanpa event_date
  OK     anotasi tanpa event_type
  OK     sebaran event_type
  OK     sebaran type
  OK     sebaran location (16 nilai)
  OK     sebaran author (5 penulis, hitungan sama)
  OK     event_date terkecil, terbesar, jumlah unik
  OK     luas (area) terkecil dan terbesar
  OK     rata-rata event_conf
  OK     rentang bujur kotak pembatas
  OK     rentang lintang kotak pembatas
  OK     jumlah patch
  OK     patch per split
  OK     patch per inventaris (11)
  OK     pixel_annotated terkecil, terbesar, rata-rata

LOLOS: 17 pemeriksaan cocok. Langkah berikut: python data/cek_data.py --skala S1
```

Baris `catatan: ... titik pusat memakai tengah kotak pembatas ...` boleh muncul (itu hanya catatan: poligon yang luasnya nol).

**Berhasil bila** baris terakhir adalah `LOLOS: 17 pemeriksaan cocok.`

**Bila tidak LOLOS:** berhenti. Kode keluar 2 = masukan tidak ada atau rusak (`dir data\raw`); kode keluar 3 = ada angka yang
berbeda dari laporan, dan skrip mencetak daftar bedanya. Simpan seluruh keluaran ke berkas (aman, di folder yang tidak
di-commit) lalu kirim ke yang membantu:

```powershell
python data\convert_inventory.py *> cek-sen12ls\hasil_konversi.txt
```

### 2.6 Periksa berkas hasil

```powershell
python data\cek_data.py --skala S1
```

Contoh hasil (bagian akhir):

```text
  OK     header annotations.csv sesuai kontrak (23 kolom)
  OK     jumlah baris annotations.csv = 74956
  OK     ann_id berurutan lengkap 0..74955 tanpa lubang
  OK     NDJSON dan CSV berisi hal yang sama baris demi baris
  ...
SEMUA PEMERIKSAAN LULUS (18)
```

### 2.7 Buat 100 titik uji dan jawaban wasit

```powershell
python bench\make_points.py
python bench\kebenaran.py --skala S1 --tulis
```

Contoh hasil:

```text
Titik dibuat: 100 (70 di dalam, 30 di luar)
Berkas: C:\...\bench\points.json
Jawaban benar dari C:\...\data\out\s1\annotations.csv: 74956 anotasi, 100 titik uji, skala S1
  W1: 100 dari 100 kueri: id ditemukan; jumlah seluruhnya 100
  W2: 70 dari 100 kueri: titik punya hasil; jumlah seluruhnya ...
  W3: 70 dari 100 kueri: titik punya hasil; jumlah seluruhnya ...
  W4: 70 dari 100 kueri: titik punya hasil; jumlah seluruhnya ...
  W5: 1 dari 1 kueri: kelompok (event_type x tahun); jumlah seluruhnya ...
  W6: 1 dari 1 kueri: kelompok (inventory x split); jumlah seluruhnya ...
Tertulis di C:\...\bench\benar (commit bila S1).
```

(Angka `jumlah seluruhnya` di datamu akan berbeda dari contoh; yang harus sama: **70 dari 100** di W2 sampai W4 dan **100 dari 100** di W1.)

`bench\points.json` dan `bench\benar\W*_S1.csv` **di-commit**: semua orang memakai titik dan jawaban yang sama.

### 2.8 Tulis checksum hasil S1

```powershell
python data\generate_scales.py --write-checksums
```

Contoh hasil: `Tertulis ...\data\CHECKSUMS.txt (4 berkas)`. Syuep nanti menambahkan baris S10 dan S100 (#16), dan semua
orang membuktikan S1 di laptopnya identik dengan milikmu (`python data\generate_scales.py --verify`).

### 2.9 Jalankan uji menyeluruh (tanpa Docker)

```powershell
python tests\uji_semua.py
```

Memerlukan sekitar 15 sampai 60 detik. Menguji konverter, generator, pemeriksa, wasit, harness, pembanding, ringkasan, dan
pencatat memakai data kecil buatan dan pustaka database **tiruan**.

Contoh hasil:

```text
OK     konversi_kecil (0.1 detik)
OK     konversi_tolak_masukan_rusak (0.0 detik)
...
OK     compose_dan_nama (0.1 detik)

SEMUA UJI LULUS (17 uji, 15 detik)
```

Baris `(node tidak ada: pemeriksaan JavaScript dilewati)` boleh muncul bila Node.js tidak terpasang; itu tidak apa-apa.

**Penting:** uji ini membuktikan **kode** berjalan dengan benar. Ia **tidak** membuktikan MongoDB, PostGIS, HDFS, dan Spark
sungguhan berjalan; itu dibuktikan oleh Elsa, Levi, dan Sofi saat mengerjakan langkahnya.

### 2.10 Periksa TEAM.md dan isi yang akan dikirim

Buka `TEAM.md` (`code TEAM.md`) dan pastikan kelima nama dan username benar. Nama lengkap Syuep (**Maulana Hidayah Syaif
Ali Khan**) disusun dari urutan namanya; cocokkan dengan data resmi dan perbaiki bila salah.

Lalu lihat apa yang akan dikirim:

```powershell
git add .
git status --short
git diff --cached --stat | Select-String "Bin"
```

Periksa:

- [ ] **tidak ada** baris yang memuat `cek-sen12ls` dan **tidak ada** `data/out`
- [ ] baris `Bin` hanya untuk `data/raw/inventories.zip` (dan berkas biner kecil lain bila ada); tidak ada berkas lebih dari 50 MB
- [ ] ada `data/raw/SHA256.txt`, `data/CHECKSUMS.txt`, `bench/points.json`, `bench/benar/W1_S1.csv` sampai `W6_S1.csv`
- [ ] ada seluruh folder: `baca-dulu`, `bench`, `data`, `docs`, `hdfs-parquet`, `mongodb`, `postgis`, `results`, `tests`

Salah memilih? `git restore --staged <jalur>` mengeluarkan satu berkas dari daftar.

### 2.11 Commit dan push

```powershell
git commit -m "[root] paket awal Sen12Landslides: kode, data mentah, panduan"
git pull --rebase
git push
```

Contoh hasil (bagian akhir):

```text
 NNN files changed, NNNNN insertions(+)
...
To https://github.com/wildnrfm/kelompok2-bigdata-storage.git
   a1b2c3d..4d5e6f7  main -> main
```

Mengirim sekitar 25 MB; beberapa menit di jaringan lambat. (Repo tanpa commit sebelumnya: gunakan `git branch -M main`
lalu `git push -u origin main`.)

### 2.12 Periksa di GitHub

Buka <https://github.com/wildnrfm/kelompok2-bigdata-storage> dan periksa:

- [ ] folder `baca-dulu`, `bench`, `data`, `docs`, `hdfs-parquet`, `mongodb`, `postgis`, `results`, `tests` ada
- [ ] `README.md` tampil di bawah daftar berkas; klik `baca-dulu/README.md` tampil rapi
- [ ] `data/raw` berisi `inventories.zip`, `splits_aligned.json`, `SHA256.txt`
- [ ] **tidak ada** folder `cek-sen12ls` dan **tidak ada** `data/out`

### 2.13 Kabari grup

```text
[SELESAI] root: paket awal sudah di GitHub.
Langkah semua orang: (1) pasang alat, (2) git clone ke C:\proyek, (3) buka baca-dulu/README.md lalu panduanmu
(PANDUAN_<nama>.md), (4) kerjakan latihan Git (#4), (5) tulis spesifikasi laptop (#5).
Setelah semua selesai #4 aku tentukan jam kickoff.
Catatan: S1 sudah terkonversi di laptopku dan cocok dengan laporan inventaris (17 pemeriksaan). Syuep membuktikannya di #8.
```

### Kalau macet

| Tanda | Penyebab dan cara memperbaiki |
|---|---|
| `Expand-Archive : ... is not a valid Zip archive` | Unduhan ZIP terputus. Unduh ulang, lalu ulangi 2.2. |
| `python : The term 'python' is not recognized` | Buka **Anaconda Prompt** atau coba `py` sebagai pengganti `python`. |
| `convert_inventory.py` keluar dengan kode 2 | Masukan tidak ditemukan. `dir data\raw` harus memuat `inventories.zip` dan `splits_aligned.json`. |
| `convert_inventory.py` keluar dengan kode 3 | **Berhenti.** Ada angka yang berbeda dari laporan; simpan seluruh keluaran (lihat 2.5) dan tulis `[BLOKIR]` dengan daftar bedanya. Jangan push. |
| `cek_data.py --skala S1` memuat baris `GAGAL` | Baca baris `GAGAL` pertama. Biasanya konversi (2.5) belum selesai atau diulang sebagian; jalankan 2.5 lagi sampai LOLOS, lalu 2.6. |
| `uji_semua.py` gagal | Salin nama uji yang `GAGAL` dan pesan di bawahnya ke `[BLOKIR]`. Jangan push sebelum lulus. |
| `git status` menampilkan `cek-sen12ls/` sebagai berkas yang akan di-commit | `.gitignore` belum terpasang (cek 2.2). Jalankan `git rm -r --cached cek-sen12ls` dan pastikan `.gitignore` memuat `cek-sen12ls/`. |
| `! [rejected] main -> main (fetch first)` | `git pull --rebase`, lalu `git push` lagi. |
| `src refspec main does not match any` | Cabang lokal bernama lain. `git branch -M main`, lalu `git push -u origin main`. |
| `remote: Permission denied` atau `403` | Login GitHub salah. Control Panel > Credential Manager > Windows Credentials, hapus `git:https://github.com`, ulangi push dan login ulang. |
| `warning: ... LF will be replaced by CRLF` | Aman diabaikan; `.gitattributes` memastikan berkas di repo memakai LF. |

---

## #5. Spesifikasi laptop

Tulis di grup (format ada di [01_PERSIAPAN_UMUM.md](01_PERSIAPAN_UMUM.md) bagian A4). Kamu mengumpulkan spesifikasi keempat
anggota untuk memilih **laptop uji S100** di kickoff (RAM 16 GB atau lebih dan disk kosong 25 GB atau lebih).

---

## #6. Cek TEAM.md dan tentukan jam kickoff

**Menunggu:** keempat anggota menulis `[SELESAI] latihan: ...` (#4).

```powershell
cd C:\proyek\kelompok2-bigdata-storage
git pull --rebase
dir latihan
code TEAM.md
```

**Berhasil bila**

- [ ] folder `latihan` memuat empat berkas: `syuep.txt`, `elsa.txt`, `sofi.txt`, `levi.txt`
- [ ] `TEAM.md` memuat lima username GitHub yang benar
- [ ] jam kickoff sudah ditulis di grup (usulkan dua pilihan; yang terbanyak dipilih)

```text
Kickoff 30 menit, panggilan grup WhatsApp: <hari tanggal jam>. Siapkan: alat terpasang, repo ter-clone,
spesifikasi laptop sudah ditulis. Bawa pertanyaanmu.
```

Bila `latihan` belum lengkap, sebut siapa yang belum di grup dan tawarkan berbagi layar. Jangan menunda kickoff lebih dari satu hari
hanya karena satu orang; yang belum selesai bisa menyusul.

---

## #7. KICKOFF (kamu memimpin)

Panggilan grup 30 menit supaya semua orang mulai dengan pemahaman yang sama. Agenda dan tabel keputusan ada di
[00_ALUR_KERJA.md](00_ALUR_KERJA.md) bagian "Acara kelompok".

**Naskah singkat**

- Pembuka (30 detik): "Tujuan kita ada dua: pitching Tugas 2, dan kode yang sudah jalan di S1 sebagai bukti rancangannya. Kode dasar
  sudah ada di repo; tugas kita menjalankan, memeriksa, mengukur, dan menjelaskannya. Hari ini kita samakan jadwal dan siapa memegang apa."
- Giliran bicara: Syuep, Elsa, Sofi, Levi. Potong dengan sopan bila lebih dari 1 menit: "Detailnya di grup ya."
- Laptop uji S100: bila tidak ada laptop 16 GB, pilih yang RAM-nya paling besar; tugas berat dijalankan satu per satu.
- Tutup dengan membacakan keputusan dan siapa memulai apa: **Syuep #8, Elsa dan Sofi #9 dan #11, Levi #10.**

**Berhasil bila**

- [ ] tabel keputusan terisi semua baris
- [ ] tiap orang tahu langkah pertamanya dan siapa yang menunggu hasilnya
- [ ] `[KEPUTUSAN]` sudah ditulis dan di-pin

```text
[KEPUTUSAN] Kickoff selesai.
Batas kumpul: <tanggal jam>. Pitching: <hari jam>.
Sinkron 1: <hari jam>. Sinkron 2: <hari jam>. Check-in: <jam>.
Laptop uji S100: <nama>.
Mulai sekarang: Syuep #8, Elsa+Sofi #9 dan #11, Levi #10.
```

---

## #18. SINKRON 1 (kamu memimpin)

**Menunggu:** #17 selesai (Sofi menempel hasil `compare_counts.py` untuk W3 di grup).

**Sebelum**

```powershell
cd C:\proyek\kelompok2-bigdata-storage
git pull --rebase
git log --oneline -15
dir results
```

Periksa di GitHub bahwa folder tiap orang sudah berisi hasil kerjanya: `data/out` tidak ada (memang tidak di-commit), tetapi
`results/` berisi CSV W3 untuk `mongodb`, `postgis`, dan `spark`, serta `data/CHECKSUMS.txt` memuat baris S1.

**Acara** (30 sampai 45 menit): demo 4 menit per orang; banding jumlah W3 dari ketiga penyimpanan dan wasit (Sofi);
samakan istilah dan nama kolom; putuskan urutan berikutnya (lanjut #25, atau pitching dahulu).

**Sesudah**

1. Perbarui daftar **Status** di `README.md` (centang yang selesai).
2. Tulis rangkuman `[KEPUTUSAN]` di grup dan pin.
3. Simpan perubahan:

   ```powershell
   git add README.md
   git commit -m "[root] status setelah Sinkron 1"
   git pull --rebase
   git push
   ```

**Berhasil bila**

- [ ] jumlah W3 dari MongoDB, PostGIS, dan Spark SQL sudah dibandingkan, selisih (bila ada) dicatat
- [ ] nama kolom dan istilah disepakati dan tertulis di pesan yang di-pin
- [ ] urutan berikutnya diputuskan

```text
[KEPUTUSAN] Sinkron 1.
Hasil W3 S1: <cocok 100 dari 100 / selisih ... titik>.
Istilah dan kolom: <yang disepakati atau diubah>.
Urutan berikutnya: <lanjut #25 / pitching dahulu>.
```

---

## #19. Baca dokumen rancangan dan pastikan semua bisa membukanya

Dokumen rancangan adalah sumber isi pitching dan laporan: <https://claude.ai/code/artifact/61c54f54-b428-4f46-9e04-741a16d74f68>

**Sebelum meminta yang lain membaca:**

- [ ] uji dengan satu anggota bahwa tautan bisa dibuka (atau kirim versi cadangan `.md` / PDF bila tidak bisa)
- [ ] pastikan dokumen sudah berisi versi Sen12Landslides yang final; **tulis di grup `[SELESAI] dokumen v2` saat siap**. Selama itu
  belum ada, tunda #19 (dan semua langkah yang menunggunya: #20, #21, #22)

Kamu sendiri membaca **seluruh** dokumen dan memeriksa:

- [ ] angka cocok dengan [KONTRAK.md](KONTRAK.md) dan [data/KAMUS_DATA.md](../data/KAMUS_DATA.md) (lihat "Angka kunci" di akhir panduan ini)
- [ ] nama kolom dan nama berkas cocok dengan kode
- [ ] setiap klaim kinerja ditulis sebagai **hipotesis**, bukan hasil
- [ ] istilah teknis dijelaskan saat pertama muncul

Bentuk pesan temuan dari semua orang: `Dokumen - <bagian> - <yang salah atau kurang> - usul: <perbaikan>`. Kamu yang memperbarui
dokumen; setelah temuan masuk, tulis `[SELESAI] dokumen v3` (atau versi berikutnya).

---

## #20. Bahan slide untukmu (slide 1 dan 6)

Kamu menyusun semua slide, tetapi isi tiap bagian datang dari pemiliknya:

| Slide | Isi | Pemilik |
|---|---|---|
| 1 | Masalah dan pengguna | Wildan |
| 2 | Dataset dan skala 1x sampai 100x | Syuep |
| 3 | Arsitektur dan alur data | Elsa |
| 4 | Mengapa MongoDB, PostGIS, dan baseline HDFS-Parquet | Elsa (MongoDB); Levi (PostGIS dan baseline) |
| 5 | Rencana pengujian dan hipotesis | Sofi |
| 6 | Hasil yang diharapkan dan rencana Tugas Tengah Semester | Wildan |

**Poin yang disarankan untuk slide 1** (ubah dengan kata-katamu):

- Peneliti kebencanaan butuh menjawab "longsor apa yang tercatat di sekitar titik ini, pada rentang tanggal ini?"
- Sen12Landslides: 74.956 poligon longsor dan 4.392 patch citra dari 16 lokasi; citranya 170,5 GB, **katalog metadatanya yang kita simpan**
- Pertanyaan katalog bersifat spasial (titik, kotak) + waktu + atribut, sehingga penyimpanan yang tepat menentukan kecepatan
- Pertanyaan kita: MongoDB, PostGIS, atau Parquet di HDFS yang paling cocok, dan berapa selisihnya?

**Poin yang disarankan untuk slide 6**

- Yang sudah ada: kode dasar, S1 termuat di tiga penyimpanan, W3 berjalan dan jumlahnya dibandingkan dengan wasit
- Yang menyusul: S10 dan S100, W1 sampai W8, hipotesis H1 sampai H5 (dugaan awal; **belum diuji**)
- Risiko dan keterbatasan: data S10 dan S100 hasil simulasi; RAM laptop terbatas; arti beberapa kolom tidak dijelaskan sumber

**Pesan WhatsApp:** `[SELESAI] bahan slide 1 dan 6 (Wildan): 4 poin dan 1 gambar di docs/`.

---

## #21. Diagram arsitektur di draw.io

**Tujuan.** Satu halaman diagram yang menjelaskan alur data dari sumber sampai laporan. Dipakai di slide 3 dan dokumen.

1. Buka <https://app.diagrams.net>. Pilih **Device** (simpan di komputer), **Create New Diagram**, **Blank Diagram**.
2. Gambar lima kolom dari kiri ke kanan (kotak dengan sudut membulat; panah berlabel format data):

| Kolom | Isi |
|---|---|
| 1. Sumber | Hugging Face `Sen12Landslides`: `inventories.zip` (74.956 poligon) dan `splits_aligned.json` (4.392 patch). Citra NetCDF 170,5 GB: **abu-abu putus-putus, "tidak dipakai"** |
| 2. Persiapan data (`data/`, Syuep) | `convert_inventory.py` menghasilkan `data/out/s1` (NDJSON + CSV, titik pusat + kotak pembatas); `generate_scales.py` membuat S10 dan S100 (seed 20261023, bersarang); `cek_data.py` dan `CHECKSUMS.txt` |
| 3. Penyimpanan (Docker) | **MongoDB 8** (`annotations`, `patches`; indeks 2dsphere) dari NDJSON lewat `mongoimport`; **PostgreSQL 17 + PostGIS 3.5** (indeks GiST) dari CSV lewat `COPY`; **HDFS** (1 NameNode + 2 DataNode, replikasi 2) berisi **Parquet ZSTD** hasil Spark dari CSV; **Spark SQL** (`local[2]`) membaca Parquet |
| 4. Uji (`bench/`) | `kueri.py` (definisi W1 sampai W6, satu tempat untuk ketiganya); `make_points.py` menghasilkan `points.json` (100 titik); `harness.py` menulis `results/*.csv`; `kebenaran.py` (wasit) menulis `bench/benar`; `compare_counts.py`; `summarize.py`; `catat.py` (W7, W8) |
| 5. Hasil | tabel dan grafik, hipotesis H1 sampai H5, laporan |

3. **Warnai menurut pemilik**: Wildan biru, Syuep teal, Elsa ungu, Sofi oranye, Levi hijau; tambahkan legenda kecil.
4. Tulis port dan nama container di kotak penyimpanan: `sen12ls-mongo :27017`, `sen12ls-postgis :5433`, `sen12ls-namenode :9870`, `sen12ls-spark`.
5. Simpan dua berkas ke folder `docs\`:
   - **File > Save as** `docs\arsitektur.drawio`
   - **File > Export as > PNG...**, zoom 200%, centang "Include a copy of my diagram", simpan `docs\arsitektur.png`

**Berhasil bila**

- [ ] semua nama dan angka di diagram cocok dengan KONTRAK (nama container, port, jumlah baris)
- [ ] diagram terbaca di layar proyektor (huruf tidak terlalu kecil)
- [ ] `docs\arsitektur.drawio` dan `docs\arsitektur.png` ada

```powershell
git add docs
git commit -m "[docs] diagram arsitektur"
git pull --rebase
git push
```

---

## #22. Susun slide pitching (6 slide)

**Menunggu:** bahan dari Syuep, Elsa, Levi, Sofi (#20) dan diagram (#21).

1. Buat di PowerPoint atau Google Slides, **6 slide** dengan urutan di tabel #20. Satu poin = satu ide; huruf minimal 24 pt.
2. Slide 3 memakai `docs\arsitektur.png`.
3. Setiap angka punya sumber (KONTRAK, KAMUS_DATA, atau berkas hasil). Klaim kinerja selalu dengan kata **hipotesis** atau **akan diuji**.
4. Tulis **atribusi dataset** di slide terakhir atau catatan kaki: *Höhn dkk. (2025), Sen12Landslides, Scientific Data 12:1772,
   DOI dataset 10.57967/hf/5883, lisensi CC BY 4.0.*
5. Simpan `docs\slide-pitching.pptx` (atau tautan Google Slides di `docs\README.md`) lalu commit `[docs] slide pitching v1`.
6. Tulis di grup: `[SELESAI] slide v1 di docs/ - tinjau silang (#23) silakan`.

**Berhasil bila:** enam slide lengkap, semua pemilik bagian sudah melihat slidenya, dan tidak ada angka tanpa sumber.

---

## #23. Tinjau silang (bagianmu: angka, istilah, nama kolom)

| Yang meninjau | Yang ditinjau |
|---|---|
| Elsa dan Levi, saling | justifikasi teknologi, model data, dan kueri (MongoDB dan PostGIS atau baseline) |
| Syuep dan Sofi, saling | profil dataset dan skala (Syuep); rencana uji dan hipotesis (Sofi) |
| **Wildan** | **angka, istilah, dan nama kolom di seluruh dokumen dan slide** |

Daftar periksa bagianmu: semua angka cocok dengan "Angka kunci" di bawah; nama kolom sama dengan `data/KAMUS_DATA.md`;
istilah konsisten (misalnya selalu "titik pusat" dan "kotak pembatas"); klaim kinerja ditulis hipotesis; atribusi ada;
tidak ada sisa nama dataset lama.

Cara meninjau (sekitar 20 menit): baca sekali penuh tanpa mengomentari; baca lagi dan catat temuan; kirim temuan dengan bentuk
`[Tinjau] @nama - <bagian> - <temuan> - Saran: <perbaikan>`; beri tahu pemilik saat selesai.

---

## #24. Latihan pitching = SINKRON 2 (kamu memimpin)

Kamu menampilkan slide; tiap orang menyampaikan bagiannya (sekitar 2 menit per orang, total 10 menit); lainnya mencatat
temuan dengan format `[Tinjau]`. Lalu latih tanya jawab dengan bank pertanyaan di bawah (yang menjawab sudah ditentukan).

| Pertanyaan yang mungkin | Jawaban singkat | Yang menjawab |
|---|---|---|
| Mengapa hanya metadata, bukan citranya? | Citra NetCDF berukuran 170,5 GB (100 kali = 17 TB) dan bukan data tabular atau semi-terstruktur seperti syarat soal. Tempat citra adalah penyimpanan objek; katalog menyimpan metadata dan jalur ke citra. | Wildan |
| Datanya hanya 74.956 baris, cukup? | Soal meminta minimal 100 kali. Kami membesarkan lewat simulasi bersarang: S10 = 749.560 dan S100 = 7.495.600 anotasi (7,84 GB berkas), seed tetap, checksum. Keterbatasannya diakui: simulasi tidak menjaga hubungan geografis nyata; cukup untuk uji beban penyimpanan, bukan analisis ilmiah. | Syuep |
| Bagaimana data simulasi dibuat? | Tiap salinan menyalin seluruh S1, menggeser keenam tanggal dengan jumlah hari yang sama (-365 sampai +365), menggeser titik pusat dan kotak (maksimal 0,25 derajat), memberi ID baru berurutan; kolom `sim_batch` menandai asalnya (0 = data asli). | Syuep |
| Mengapa poligon tidak disimpan? | Median sisi kotak pembatas hanya sekitar 54 m. Pertanyaan katalog (di sekitar titik, di dalam kotak, pada rentang tanggal) cukup dijawab dengan titik pusat dan kotak. Konsekuensinya diakui: W2 memakai titik pusat, W4 memakai kotak pembatas. | Wildan |
| Mengapa MongoDB? | Satu anotasi = satu dokumen; field kosong tidak ditulis (skema fleksibel); indeks 2dsphere dengan `$geoWithin`; pengambilan per `_id` cepat. | Elsa |
| Mengapa PostgreSQL/PostGIS? | Skema tegas (23 kolom bertipe jelas); indeks GiST pada titik pusat dan kotak; `ST_Intersects`; SQL memadukan filter spasial, atribut, dan agregasi (W4, W5, W6). | Levi |
| Mengapa HDFS + Parquet sebagai baseline? | Berkas kolumnar tanpa indeks spasial: mencari titik berarti memindai dengan pra-filter pada kolom koordinat. Fungsinya mengukur seberapa besar keunggulan indeks spasial. Sedona dan GeoParquet dicatat sebagai pengembangan lanjutan. | Levi |
| Apa beda 2dsphere (MongoDB) dan geometry (PostGIS)? | 2dsphere memakai geometri bola; tipe `geometry` PostGIS planar. Jendela kueri kami digeser setengah langkah dari kisi koordinat data, sehingga ketiganya **harus** memberi jumlah sama persis; hal itu diuji dengan `compare_counts.py` dan wasit. Selisih berarti ada yang salah, bukan efek tepi. | Elsa dan Levi |
| Bagaimana membuat perbandingan adil? | Data dan seed sama; 100 titik uji tetap (70 di dalam, 30 di luar); memori dibatasi (cache WiredTiger 0,5 GB, `shared_buffers` 256 MB, Spark `local[2]` dengan 2 GB); satu penyimpanan aktif sekali waktu; minimal 3 ulangan; cold dan warm; satu laptop yang sama. | Sofi |
| Apa hipotesisnya dan kapan ditolak? | H1: indeks spasial mengalahkan Parquet pada W2 dan W3 dan selisihnya melebar dari S1 ke S100. H2: PostGIS lebih cepat dari MongoDB di W4. H3: ukuran Parquet < PostGIS < MongoDB. H4: Spark SQL lebih cepat dari MongoDB pada W5 dan W6 di S100. H5: p95 W1 dengan 50 klien kurang dari 10 kali p95 satu klien. Semuanya **dugaan awal, belum diuji**; syarat penolakan ada di KONTRAK bagian 7. | Sofi |
| Mengapa Spark terlihat lambat di data kecil? | Biaya memulai job Spark lebih besar daripada membaca 74.956 baris, jadi kueri diukur di dalam satu sesi yang sudah hangat dan baseline dinilai terutama pada S100. | Levi dan Sofi |
| Apa risiko terbesar? | Data S10 dan S100 hasil simulasi; RAM laptop terbatas (satu penyimpanan sekali waktu, memori dibatasi); beda bola dan bidang datar (uji silang dengan wasit); arti `*_dt2` dan satuan `area` tidak dijelaskan sumber; hubungan anotasi dan patch hanya per inventaris. | Wildan |
| Mengapa bukan Elasticsearch, Cassandra, Redis, Neo4j, atau TimescaleDB? | Elasticsearch: mesin pencari teks. Cassandra: satu tabel per pola kueri, kueri spasial bukan kekuatannya. Redis: GEO untuk titik, bukan kotak atau poligon, dan data harus muat di memori. Neo4j: bebannya bukan graf. TimescaleDB: bukan deret waktu. | Elsa dan Levi |
| Bagaimana menambah data baru (W8)? | MongoDB: `mongoimport` tanpa `--drop`. PostGIS: `load.sql` dengan `-v tambah=1`. Parquet: `csv_to_parquet.py --tambah` (berkas baru per batch). | Levi |
| Apa yang sudah jadi dan apa yang menyusul? | Tugas 2: rancangan, profil dan skala data, S1 termuat di tiga penyimpanan, W3 berjalan dan jumlahnya cocok dengan wasit. Tugas Tengah Semester: S10 dan S100, W1 sampai W8, analisis hipotesis, laporan; W9 dan W10 belum ada skripnya. | Wildan |
| Bagaimana lisensi dan atribusi? | CC BY 4.0; kami mengutip Höhn dkk. (2025), Scientific Data 12:1772, DOI dataset 10.57967/hf/5883, serta penulis inventaris asal (Ferrario, Emberson, Belair, Kirschbaum). | Wildan |

**Berhasil bila:** semua orang sudah menyampaikan bagiannya, temuan `[Tinjau]` dari latihan sudah dicatat, dan slide v2 (setelah
perbaikan) sudah di `docs/`.

```text
[KEPUTUSAN] Sinkron 2 selesai. Slide final: docs/slide-pitching.pptx (v<n>).
Perbaikan yang diputuskan: <daftar singkat>. Jadwal pitching: <hari jam>.
```

---

## #30. Laporan akhir dan slide hasil (kamu menyusun)

**Menunggu:** #29 (tabel, grafik, hipotesis dari Sofi dan Elsa).

Kerangka laporan (ikuti format dari dosen bila ada; ini kerangka isi):

| Bagian | Isi | Penulis |
|---|---|---|
| 1. Pendahuluan | masalah, pengguna, tujuan, pertanyaan penelitian | Wildan |
| 2. Dataset | sumber, apa yang disimpan dan tidak, profil, skala dan simulasi, keterbatasan (dari `data/KAMUS_DATA.md`) | Syuep |
| 3. Arsitektur dan model data | MongoDB dan PostGIS, justifikasi, indeks | Elsa (MongoDB), Levi (PostGIS) |
| 4. Baseline HDFS-Parquet | HDFS, replikasi, Parquet, Spark SQL | Levi |
| 5. Metode uji | W1 sampai W8, 100 titik, wasit, aturan adil, cold dan warm | Sofi |
| 6. Hasil | tabel dan grafik dari `results/` (median, p95, QPS), ukuran di disk, waktu muat dan indeks | Sofi |
| 7. Analisis hipotesis | H1 sampai H5: diterima atau ditolak, dengan angka; E1 dan E2 | Sofi dan Elsa |
| 8. Keterbatasan | simulasi, arti kolom yang tidak jelas, satu laptop, W9 dan W10 belum diuji, hal yang tidak terbukti | Wildan |
| 9. Kesimpulan dan saran | penyimpanan mana untuk kasus apa | Wildan |
| Lampiran | perintah, kamus data, atribusi, tautan repo | Wildan |

**Cara kerja yang aman dari konflik:** tiap orang menulis bagiannya di berkas sendiri, `docs/laporan_<nama>.md`, lalu kamu
menggabungkannya. Angka diambil dari `results/ringkasan.csv`, `results/banding.csv`, dan `python bench\catat.py tampil`.
Setiap angka punya sumber; klaim yang tidak diukur ditulis sebagai hipotesis atau dihapus.

**Atribusi wajib di laporan dan slide:** *Höhn dkk. (2025), Sen12Landslides, Scientific Data 12:1772; DOI dataset
10.57967/hf/5883; lisensi CC BY 4.0. Inventaris berasal dari Ferrario dkk. (2023), Emberson dkk. (2022), Belair dkk. (2022),
dan Kirschbaum dkk. (2010, 2015).*

---

## #31. QA akhir dan kumpul di SIDIA

Kamu memeriksa seluruh hasil sebelum dikumpulkan. Semua anggota ikut memeriksa bagiannya.

```powershell
cd C:\proyek\kelompok2-bigdata-storage
git pull --rebase
python tests\uji_semua.py
python tests\lint_dokumen.py
python bench\summarize.py
git status
git grep -n -i -E "password|token|secret" -- . ":(exclude)baca-dulu"
```

**Daftar periksa**

- [ ] `uji_semua.py` berakhir `SEMUA UJI LULUS`
- [ ] `lint_dokumen.py` berakhir `0 masalah` (tautan dan jangkar dokumen hidup; berkas yang disebut panduan ada)
- [ ] `git status` bersih; tidak ada `data/out/` dan `cek-sen12ls/` di GitHub
- [ ] `git grep` hanya menampilkan **dua** baris sandi uji `postgres` (di `postgis/docker-compose.yml` dan `bench/harness.py`; sengaja, hanya untuk database di laptop sendiri); tidak ada sandi, token, atau rahasia lain
- [ ] `results/` memuat CSV hasil, `ringkasan.csv`, `banding.csv`, dan `pengukuran_*.csv`; angka di laporan cocok dengan berkas itu
- [ ] jumlah hasil W1 sampai W6 di S100 sudah dibandingkan dengan wasit (`bench/compare_counts.py`) dan selisih (bila ada) dijelaskan
- [ ] angka kunci di laporan dan slide cocok (tabel di bawah)
- [ ] atribusi dataset ada di laporan, slide, dan `README.md`
- [ ] `README.md` bagian Status sudah dicentang dan tautan semuanya hidup
- [ ] setiap anggota sudah menulis `[SELESAI]` untuk bagiannya
- [ ] laporan dan slide final diunggah ke SIDIA **sesuai instruksi dosen** (tautan repo ikut dilampirkan bila diminta)

```text
[SELESAI] QA akhir: uji lulus, angka cocok, atribusi ada. Dikumpulkan di SIDIA: <jam>.
```

---

## Angka kunci (untuk #19, #23, #31)

| Hal | Nilai yang benar | Sumber |
|---|---|---|
| Dataset | Sen12Landslides, Höhn dkk., Scientific Data 12:1772, DOI 10.57967/hf/5883, CC BY 4.0 | KAMUS_DATA bagian 1 dan 7 |
| Data yang dipakai | 74.956 anotasi (15 atribut), 4.392 patch (train 2.810, val 703, test 879), 11 inventaris, 16 lokasi | KAMUS_DATA bagian 2 sampai 4 |
| Data yang tidak dipakai | citra NetCDF 170,5 GB | KAMUS_DATA bagian 1 |
| Yang disimpan | atribut + titik pusat (centroid berbobot luas) + kotak pembatas; **bukan** bentuk poligon | KONTRAK bagian 3 |
| `event_type` | Rainfall 52.686; Hurricane 10.172; Earthquake 7.950; Tropical Storm 640; Cyclone 366; kosong 3.142 | KAMUS_DATA bagian 4 |
| Tanpa tanggal | 109 anotasi tidak punya satu pun tanggal | KAMUS_DATA bagian 2 |
| Skala | S1 74.956 / 4.392; S10 749.560 / 43.920; S100 7.495.600 / 439.200 (anotasi / patch) | KONTRAK bagian 3 |
| Ukuran berkas data (hasil ukur pada data tiruan berbentuk laporan asli; bisa beda beberapa persen) | S1 77,9 MB; S10 781 MB; S100 7,84 GB | KAMUS_DATA bagian 5 |
| Seed | 20261023 (tetap) | KONTRAK bagian 3 |
| Titik uji | 100 titik tetap: 70 di dalam, 30 di luar (`bench/points.json`) | KONTRAK bagian 6 |
| Jendela kueri | W2 dan W3: +-0,01 derajat (sekitar 1,1 km); W3 +-30 hari; W4: +-0,1 derajat (sekitar 22 km), `event_conf` >= 0,9 | KONTRAK bagian 6 |
| Container dan port | `sen12ls-mongo` 27017; `sen12ls-postgis` 5433 menuju 5432; HDFS UI 9870; Spark UI 4040 | KONTRAK bagian 4 |
| Basis data | database `sen12ls`; MongoDB koleksi `annotations` dan `patches`; PostGIS tabel `annotations` dan `patches` | KONTRAK bagian 4 dan 5 |
| Memori dibatasi | cache WiredTiger 0,5 GB; `shared_buffers` 256 MB; Spark `local[2]` dengan 2 GB | KONTRAK bagian 4 dan 6 |
| Replikasi HDFS | 2 (dua DataNode) | `hdfs-parquet/hadoop.env` |
| Kolom CSV hasil | `penyimpanan, beban_kerja, skala, ulangan, cold_warm, kueri_id, waktu_ms, jumlah_hasil, catatan` (9 kolom) | KONTRAK bagian 6 |
| Hipotesis dan eksperimen | H1 sampai H5; E1 sampai E4; semuanya dugaan awal | KONTRAK bagian 7 |
| Beban kerja | W1 sampai W6 (ada skrip), W7 dan W8 (catat.py), W9 dan W10 (belum ada skrip) | KONTRAK bagian 6 |
| Hal yang tidak dijelaskan sumber | arti `pre_dt2`/`event_dt2`/`post_dt2`; satuan `area`; EPSG:4326 adalah dugaan | KAMUS_DATA bagian 1 |
