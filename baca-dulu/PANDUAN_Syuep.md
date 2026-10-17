# Panduan Syuep (Data Collection Engineer)

Folder milikmu: `data/`. Kamu memastikan **data benar, sama di semua laptop, dan tercatat**: konversi S1, skala S10 dan S100,
checksum, dan kamus data. Hal umum (terminal, Git, VS Code) ada di [01_PERSIAPAN_UMUM.md](01_PERSIAPAN_UMUM.md); peta seluruh
pekerjaan di [00_ALUR_KERJA.md](00_ALUR_KERJA.md); nama dan perintah baku di [KONTRAK.md](KONTRAK.md); arti tiap kolom di
[../data/KAMUS_DATA.md](../data/KAMUS_DATA.md).

> Kode dasar (`data/convert_inventory.py`, `data/generate_scales.py`, `data/cek_data.py`) **sudah ditulis dan diuji** pada data
> tiruan berbentuk laporan asli. Tugasmu: menjalankannya pada data asli di laptopmu, membuktikan hasilnya sama dengan milik
> Wildan, dan mencatat ukurannya. Kamu tidak perlu menulis ulang kode.

## Peta langkahmu

| # | Langkah | Menunggu | Perkiraan waktu | Membuka |
|---|---|---|---|---|
| 3 | Pasang alat (Git, Python, VS Code; Docker tidak wajib) | - | 30 sampai 60 menit | #4 |
| 4 | Clone repo dan latihan Git | #2 (Wildan) dan #3 | 15 sampai 20 menit | #6 |
| 5 | Tulis spesifikasi laptop di grup | - | 5 menit | #7 |
| 7 | KICKOFF | #6 | 30 menit | #8 |
| **8** | **S1 di laptopmu dan cocokkan checksum** | #7 | 30 sampai 60 menit | #13, #14, #15, #16 |
| 15 | Mendampingi Levi: periksa Parquet S1 | #8 dan #12 (Levi) | 20 sampai 30 menit | #17 |
| **16** | **S10 dan S100, `CHECKSUMS.txt`, ukuran di kamus data** | #8 | 1 sampai 2 jam (sebagian menunggu) | #26 |
| 18 | SINKRON 1 | #17 | 30 sampai 45 menit | #25 |
| 19 | Baca dokumen rancangan | #7 | 45 menit | #20 |
| 20 | Bahan slide 2 | #19 | 30 menit | #22 |
| 23 | Tinjau silang | #22 | 45 menit | #24 |
| 24 | Latihan pitching (SINKRON 2) | #23 | 45 sampai 60 menit | - |
| 26 | Mendukung pemuatan S10 dan S100 | #16 dan #25 | menyesuaikan | #27 |

---

## #3, #4, #5. Alat, clone, spesifikasi

- **#3 Pasang alat:** [01_PERSIAPAN_UMUM.md](01_PERSIAPAN_UMUM.md) bagian A2. Kamu **tidak wajib** memasang Docker (kerjamu hanya
  Python dan Git), tetapi disarankan bila laptopmu kuat supaya bisa mendampingi Levi di #15.
- **#4 Clone dan latihan Git:** setelah Wildan menulis `[SELESAI] root: paket awal sudah di GitHub`, jalankan (bagian A3):

```powershell
mkdir C:\proyek
cd C:\proyek
git clone https://github.com/wildnrfm/kelompok2-bigdata-storage.git
cd kelompok2-bigdata-storage
git pull --rebase
New-Item -ItemType Directory -Force latihan | Out-Null
Set-Content latihan\syuep.txt "Halo, ini latihan Syuep"
git add latihan/syuep.txt
git commit -m "[latihan] Syuep: uji coba push"
git pull --rebase
git push
```

Tulis di grup: `[SELESAI] latihan: clone dan push berhasil (latihan/syuep.txt) - Syuep`. Periksa juga baris namamu di `TEAM.md`
(nama lengkap dan username `Syaifalikhan`); bila ada yang salah, beri tahu Wildan.

- **#5 Spesifikasi:** bagian A4; tulis di grup.

---

## #8. S1 di laptopmu dan cocokkan checksum

**Tujuan.** Membuktikan bahwa hasil konversi di laptopmu **identik byte demi byte** dengan milik Wildan. Dari sini semua orang
bisa memakai data yang sama dengan percaya diri.

**Menunggu:** kickoff (#7). Datanya sudah ada di repo: `data/raw/inventories.zip` dan `data/raw/splits_aligned.json`.

### 8.1 Ambil versi terbaru dan periksa berkas asli

```powershell
cd C:\proyek\kelompok2-bigdata-storage
git pull --rebase
python data\cek_data.py --raw
```

Contoh hasil:

```text
COCOK     inventories.zip
COCOK     splits_aligned.json

Berkas asli COCOK dengan SHA256.txt.
```

`COCOK` = berkas di laptopmu sama dengan yang dicatat Wildan. `BEDA` = unduhan atau penyalinan rusak: `git pull --rebase`
lagi; bila tetap beda, `[BLOKIR]`.

> **Opsional, dianjurkan (30 menit):** buktikan bahwa berkas di repo sama dengan berkas **sumber aslinya**. Buka halaman dataset
> lewat DOI <https://doi.org/10.57967/hf/5883>, unduh `inventories.zip` dan `splits_aligned.json` sendiri (tab *Files and versions*),
> lalu bandingkan:
>
> ```powershell
> Get-FileHash <jalur-unduhanmu>\inventories.zip -Algorithm SHA256
> Get-Content data\raw\SHA256.txt
> ```
>
> Dua kode heksadesimal harus sama persis. Beda = tulis `[BLOKIR]` (kemungkinan Wildan memakai versi dataset yang berbeda).

### 8.2 Konversi ke S1

```powershell
python data\convert_inventory.py
```

Memerlukan sekitar 1 sampai 3 menit. Hasilnya empat berkas di `data\out\s1\` (folder ini **tidak** di-commit).

**Berhasil bila** baris terakhir: `LOLOS: 17 pemeriksaan cocok. Langkah berikut: python data/cek_data.py --skala S1`.
(Pemeriksaan ini mencocokkan hasilmu dengan `laporan_inventaris.txt` Wildan tanggal 22 Okt 2026: jumlah, sebaran lokasi dan
pemicu, rentang tanggal, luas, koordinat, patch per split dan inventaris.)

Kode keluar selain 0: berhenti dan `[BLOKIR]` dengan seluruh keluaran (2 = masukan tidak ada atau rusak; 3 = ada angka yang beda).

### 8.3 Periksa isi berkas

```powershell
python data\cek_data.py --skala S1
```

Contoh hasil (bagian akhir):

```text
  OK     header annotations.csv sesuai kontrak (23 kolom)
  OK     jumlah baris annotations.csv = 74956
  OK     ann_id berurutan lengkap 0..74955 tanpa lubang
  OK     NDJSON dan CSV berisi hal yang sama baris demi baris
  OK     sebaran location = kelipatan 1 dari data asli
  ...
SEMUA PEMERIKSAAN LULUS (18)
```

### 8.4 Cocokkan checksum dengan milik Wildan

```powershell
python data\generate_scales.py --verify
```

Contoh hasil:

```text
COCOK      out/s1/annotations.ndjson
COCOK      out/s1/annotations.csv
COCOK      out/s1/patches.ndjson
COCOK      out/s1/patches.csv

Semua 4 berkas yang ada COCOK.
```

Setelah #16 selesai, `--verify` juga mencantumkan baris S10 dan S100; yang belum kamu buat tampil sebagai `BELUM ADA` dan itu wajar.

**Bila ada `BEDA`:** hasil konversimu tidak sama dengan milik Wildan, jadi data tidak boleh dipakai untuk uji. Cek versi Python
(`python --version`: 3.11 sampai 3.13), pastikan `data\raw\` tidak berubah (8.1), hapus `data\out\s1`, ulangi 8.2. Tetap beda:
`[BLOKIR]` berisi nama berkas yang beda dan versi Python kalian berdua.

### 8.5 Kenali datanya (10 menit)

Kamu akan menjelaskan data ini di slide 2, jadi lihat bentuknya:

```powershell
Get-Content data\out\s1\annotations.csv -TotalCount 2
Get-Content data\out\s1\annotations.ndjson -TotalCount 1
Get-Content data\out\s1\patches.csv -TotalCount 2
```

Perhatikan: (1) satu baris CSV berisi 23 kolom (daftar di `data/KAMUS_DATA.md` bagian 2); (2) NDJSON memuat hal yang sama, tetapi
tanggal berbentuk `{"$date": ...}`, titik pusat berbentuk titik GeoJSON, dan **field yang kosong tidak ditulis**; (3) tidak ada
bentuk poligon, hanya titik pusat dan kotak pembatas.

### 8.6 Ukuran berkas dan kamus data

```powershell
python data\cek_data.py --ukuran
```

Contoh hasil (angka datamu bisa berbeda beberapa persen):

```text
skala    berkas                         MB
s1       annotations.ndjson          56.94
s1       annotations.csv             19.52
s1       patches.ndjson               0.95
s1       patches.csv                  0.50
s1       JUMLAH                      77.91
(MB desimal: 1 MB = 1.000.000 byte. Tulis angka ini di tabel bagian 5 KAMUS_DATA.md.)
```

Bandingkan dengan tabel di `data/KAMUS_DATA.md` bagian 5 (S1: CSV anotasi 19,5 MB; NDJSON anotasi 56,9 MB; total 77,9 MB).
Bila selisihnya lebih dari 3 persen, perbarui baris S1 di tabel itu dengan angka asli. Baris S10 dan S100 diperbarui di #16.

```powershell
git add data/KAMUS_DATA.md
git commit -m "[data] ukuran S1 asli di kamus data"
git pull --rebase
git push
```

(Lewati perintah ini bila tidak ada yang berubah.)

**Berhasil bila (#8)**

- [ ] `python data\cek_data.py --raw` menampilkan dua `COCOK`
- [ ] `python data\convert_inventory.py` berakhir `LOLOS: 17 pemeriksaan cocok`
- [ ] `python data\cek_data.py --skala S1` berakhir `SEMUA PEMERIKSAAN LULUS (18)`
- [ ] `python data\generate_scales.py --verify` menampilkan empat `COCOK`
- [ ] ukuran S1 di `KAMUS_DATA.md` sudah sesuai kenyataan

**Pesan WhatsApp**

```text
[SELESAI] data: S1 di laptop Syuep terkonversi, LOLOS 17 pemeriksaan, 18 pemeriksaan hasil lulus,
checksum 4 berkas COCOK dengan milik Wildan. Elsa/Sofi (#13) dan Levi (#14, #15) boleh memuat S1.
Cara membuatnya sendiri: python data\convert_inventory.py lalu python data\generate_scales.py --verify
```

### Kalau macet

| Tanda | Penyebab dan cara memperbaiki |
|---|---|
| `Tidak bisa menemukan inventaris` atau kode keluar 2 | `dir data\raw` harus memuat `inventories.zip` dan `splits_aligned.json`. `git pull --rebase` lalu ulangi. |
| `convert_inventory.py` kode keluar 3 | Ada angka yang beda dari laporan. `[BLOKIR]` dengan seluruh keluaran. Jangan lanjut. |
| `--verify` menampilkan `BEDA` | Lihat 8.4. Penyebab paling umum: versi Python di luar 3.11 sampai 3.13, atau `data\raw` berubah. |
| `--verify`: `data/CHECKSUMS.txt belum ada` | Wildan belum mendorongnya. `git pull --rebase`; bila tetap tidak ada, `[BLOKIR]` ke Wildan. |
| `MemoryError` atau laptop macet saat konversi | Tutup program berat (browser, Docker); S1 hanya memakai beberapa ratus MB. Tetap gagal: `[BLOKIR]` dengan RAM laptopmu. |
| `PermissionError` saat menulis `data\out` | Antivirus atau OneDrive mengunci berkas. Pastikan repo ada di `C:\proyek` (bukan Desktop/Documents), tutup berkas yang terbuka di VS Code, ulangi. |

---

## #15. Mendampingi Levi: periksa Parquet S1

**Menunggu:** #8 (kamu) dan #12 (Levi: HDFS dan Spark menyala). Levi yang memimpin (mengubah CSV S1 menjadi Parquet di HDFS dan
menjalankan W3 di Spark SQL). Peranmu: **membuktikan isi Parquet sama dengan CSV**, karena datamu yang jadi sumbernya.

Setelah Levi menjalankan `csv_to_parquet.py --scale S1` (skrip itu sendiri mencocokkan jumlah baris dan mencetak `OK`), kamu bisa
memeriksa nilainya dengan Levi lewat berbagi layar (Docker harus berjalan di laptop Levi, atau di laptopmu bila kamu juga
menyalakannya sesuai panduan Levi #12):

```powershell
docker exec sen12ls-spark /opt/spark/bin/spark-sql --master "local[2]" --driver-memory 2g -e "CREATE TEMPORARY VIEW annotations USING parquet OPTIONS (path 'hdfs://namenode:8020/data/sen12ls/parquet/s1/annotations'); SELECT count(*) AS n, sum(CASE WHEN event_date IS NULL THEN 1 ELSE 0 END) AS tanpa_tanggal, count(DISTINCT location) AS lokasi FROM annotations;"
```

**Berhasil bila** hasilnya `74956  109  16` (jumlah anotasi, jumlah tanpa `event_date`, jumlah lokasi). Pemeriksaan serupa untuk patch:
4392 baris (`.../s1/patches`). Angka lain yang boleh dicek: `Italy` 47.522 dan `Nepal` 8 anotasi (`SELECT location, count(*) ... GROUP BY location`).

Beda dari angka di atas = ada yang salah di langkah muat (bukan di data): beri tahu Levi dan `[BLOKIR]` bila tidak ketemu penyebabnya.

> Perintah `spark-sql` di atas belum pernah dijalankan pada Spark sungguhan oleh pembuat panduan; bila ia menolak, minta Levi
> menjalankan kueri yang sama lewat `pyspark` atau lewat `run_sql.py`, dan catat apa yang berhasil di grup.

**Pesan WhatsApp:** `[SELESAI] data: Parquet S1 diperiksa bersama Levi: 74956 anotasi, 109 tanpa tanggal, 16 lokasi, 4392 patch cocok dengan CSV.`

---

## #16. S10 dan S100, CHECKSUMS.txt, dan ukuran di kamus data

**Tujuan.** Menyediakan data 10 dan 100 kali, membuktikan pembuatannya selalu sama (checksum), dan mencatat ukurannya.
Semua orang kelak membuat S10 dan S100 **sendiri** di laptopnya dengan skrip yang sama, lalu memeriksa dengan checksummu.

**Menunggu:** #8. **Ruang disk:** S10 sekitar 0,8 GB; S100 sekitar **7,84 GB**. Periksa dulu:

```powershell
$d = Get-PSDrive C
"Disk C bebas: {0:N0} GB" -f ($d.Free/1GB)
```

Diperlukan minimal **12 GB bebas** untuk bagian ini (S10 + S100 + ruang kerja). Kurang dari itu: bebaskan dulu.

### 16.1 Buat S10 dan periksa

```powershell
cd C:\proyek\kelompok2-bigdata-storage
git pull --rebase
python data\generate_scales.py --scale S10
python data\cek_data.py --skala S10
```

Contoh hasil:

```text
Dasar: 74956 anotasi, 4392 patch (S1). Membuat S10.
  ... batch 9 dari 9 (32 detik)
S10 selesai: 749560 anotasi, 43920 patch, folder C:\...\data\out\s10
Langkah berikut: python data/cek_data.py --skala S10
...
  OK     jumlah baris annotations.csv = 749560
  OK     ann_id berurutan lengkap 0..749559 tanpa lubang
  OK     sim_batch 0..9, tiap batch jumlah baris sama
  OK     sebaran location = kelipatan 10 dari data asli
...
SEMUA PEMERIKSAAN LULUS (18)
```

S10 memerlukan sekitar 0,5 sampai 2 menit; pemeriksaannya sekitar 15 detik sampai 1 menit.

### 16.2 Buat S100 dan periksa

```powershell
python data\generate_scales.py --scale S100
python data\cek_data.py --skala S100
```

S100 memerlukan sekitar **3 sampai 6 menit** (pada data tiruan berbentuk laporan asli: sekitar 5 menit) dan 7,84 GB. Pemeriksaan
penuh sekitar 5 sampai 7 menit; untuk pemeriksaan lebih singkat yang melewati NDJSON: `python data\cek_data.py --skala S100 --cepat`.
Biarkan laptop bekerja dan jangan menutup jendela PowerShell.

**Berhasil bila** keduanya berakhir `SEMUA PEMERIKSAAN LULUS (18)`, dengan `jumlah baris annotations.csv = 7495600` dan
`sim_batch 0..99, tiap batch jumlah baris sama` untuk S100.

### 16.3 Tulis checksum semua skala

```powershell
python data\generate_scales.py --write-checksums
git diff data/CHECKSUMS.txt
```

Menghitung SHA-256 untuk sekitar 8,6 GB memerlukan 1 sampai 3 menit.

**Periksa hasilnya:** `git diff` harus menunjukkan hanya baris yang **ditambahkan** (hijau, diawali `+`): delapan baris untuk S10
dan S100. Empat baris `out/s1/...` milik Wildan **tidak boleh berubah**. Bila baris S1 berubah, konversi di laptopmu tidak sama
dengan milik Wildan: kembali ke 8.4 dan `[BLOKIR]`.

### 16.4 Perbarui kamus data

```powershell
python data\cek_data.py --ukuran
```

Salin angka ke tabel di `data/KAMUS_DATA.md` bagian 5:

| Skala | Anotasi | Patch | CSV anotasi | NDJSON anotasi | Total keempat berkas |
|---|---|---|---|---|---|
| S10 | 749.560 | 43.920 | (isi dari `--ukuran`) | (isi) | (isi) |
| S100 | 7.495.600 | 439.200 | (isi, dalam GB) | (isi, dalam GB) | (isi, dalam GB) |

Perubahan hanya pada kolom ukuran. Bila angkamu dalam 3 persen dari angka yang sudah tertulis (781 MB dan 7,84 GB), biarkan.

### 16.5 Simpan ke GitHub

```powershell
git add data/CHECKSUMS.txt data/KAMUS_DATA.md
git status
git commit -m "[data] CHECKSUMS S10 dan S100, ukuran berkas di kamus data"
git pull --rebase
git push
```

`git status` **tidak boleh** menampilkan `data/out` (itu data besar; sudah di `.gitignore`).

**Berhasil bila (#16)**

- [ ] `generate_scales.py --verify` menampilkan `Semua 12 berkas yang ada COCOK`
- [ ] `data/CHECKSUMS.txt` di GitHub memuat 12 baris (S1, S10, S100 masing-masing 4)
- [ ] ukuran S10 dan S100 di `KAMUS_DATA.md` sesuai kenyataan

```powershell
python data\generate_scales.py --verify
```

**Pesan WhatsApp**

```text
[SELESAI] data: S10 (749.560) dan S100 (7.495.600) dibuat dan lulus 18 pemeriksaan; CHECKSUMS.txt berisi 12 berkas.
Cara membuat sendiri: python data\generate_scales.py --scale S10 (atau S100), lalu python data\generate_scales.py --verify.
Disk bebas yang diperlukan: S10 ~0,8 GB, S100 ~7,84 GB (+ ruang database).
```

### Kalau macet

| Tanda | Penyebab dan cara memperbaiki |
|---|---|
| `No space left on device` atau `OSError: [Errno 28]` | Disk penuh. Hapus `data\out\s100` dan bebaskan ruang (Docker: `docker system prune`, tanyakan dulu). |
| Generator berjalan sangat lama (lebih dari 15 menit untuk S100) | Laptop sedang dipakai berat atau disk lambat. Tutup program lain; biarkan. Bila terhenti tanpa pesan lebih dari 10 menit: Ctrl+C, hapus `data\out\s100`, ulangi. |
| `cek_data --skala S100` GAGAL: `jumlah baris ...` | Pembuatan terhenti di tengah. Hapus `data\out\s100` lalu ulangi 16.2 sampai selesai. |
| `--write-checksums` mengubah baris S1 | Lihat 16.3. Hasil konversimu beda dari milik Wildan; jangan commit. |
| `git push` menolak (`fetch first`) | `git pull --rebase`; bila konflik di `CHECKSUMS.txt` atau `KAMUS_DATA.md`, selesaikan seperti di [A5](01_PERSIAPAN_UMUM.md#a5-git-sehari-hari-dan-cara-mengatasi-konflik) (simpan baris keduanya), lalu `git push`. |

---

## #18. SINKRON 1

Yang kamu siapkan dan tunjukkan (4 menit):

- [ ] `python data\generate_scales.py --verify`: semua `COCOK`
- [ ] `python data\cek_data.py --skala S1`: 18 pemeriksaan lulus
- [ ] tabel ukuran S1, S10, S100 di `data/KAMUS_DATA.md`
- [ ] satu kalimat tentang aturan simulasi (batch 0 = data asli; tanggal dan lokasi digeser; seed 20261023; bersarang)

Pesan setelah Sinkron 1: `[SELESAI] Sinkron 1: hasil data Syuep sudah ditunjukkan dan dicatat.`

---

## #19. Baca dokumen rancangan

Tautan ada di grup (Wildan menulis `[SELESAI] dokumen v2` saat versi final siap). Baca bagian **Profil dataset dan rencana
skala** dan **Kamus data**, dan periksa:

- [ ] angka cocok dengan hasil di laptopmu (74.956 anotasi, 4.392 patch, 16 lokasi, 11 inventaris, 109 tanpa tanggal)
- [ ] skala: S10 = 749.560 dan S100 = 7.495.600
- [ ] nama kolom cocok dengan `data/KAMUS_DATA.md`
- [ ] dokumen tidak menyebut `S1000` atau dataset lama sebagai bagian rencana

Bentuk pesan temuan: `Dokumen - <bagian> - <yang salah atau kurang> - usul: <perbaikan>`. Tidak ada temuan:
`Dokumen - bagianku sudah benar (Syuep)`.

---

## #20. Bahan slide 2 (dataset dan skala)

Kirim ke Wildan **3 sampai 5 poin** (satu kalimat pendek, paling banyak 12 kata) dan **satu gambar**.

Poin yang disarankan (ubah dengan kata-katamu, hanya tulis yang kamu pahami):

- Sumber: Sen12Landslides (Höhn dkk., 2025), CC BY 4.0: 74.956 poligon longsor dari 16 lokasi
- Yang disimpan: atribut, titik pusat, dan kotak pembatas; **bukan** poligon, bukan citra 170,5 GB
- Sebaran sangat miring: Italy dan DominicaMaria 77% dari anotasi
- Skala bersarang: S1 74.956, S10 749.560, S100 7.495.600 (seed tetap)
- Simulasi hanya untuk uji beban; bukan kejadian longsor nyata

Gambar yang disarankan: diagram kotak bersarang **S1 dalam S10 dalam S100**, dengan jumlah anotasi dan ukuran berkas tiap
skala (angka dari `KAMUS_DATA.md`); atau diagram batang lima lokasi terbesar (Italy 47.522; DominicaMaria 10.172; Newzealand
3.242; Chimanimani 2.513; Kyrgyzstan1 2.405) dan "lainnya".

Pesan WhatsApp:

```text
[SELESAI] bahan slide 2 (Syuep): 5 poin dan 1 gambar: <tempel poin atau lampirkan gambar>
```

---

## #23. Tinjau silang

Kamu meninjau **rencana uji dan hipotesis milik Sofi** (slide 5 dan bagian Rencana pengujian di dokumen); Sofi meninjau profil
dataset dan skala milikmu.

Daftar periksa untuk bagian Sofi:

- [ ] jumlah data dan skala yang disebut benar (S1, S10, S100; jumlah anotasi dan patch)
- [ ] 100 titik uji: 70 di dalam, 30 di luar; W1 sampai W6 sesuai KONTRAK bagian 6
- [ ] istilah data konsisten dengan kamus data (titik pusat, kotak pembatas, `sim_batch`)
- [ ] hipotesis ditulis sebagai dugaan awal dan punya syarat penolakan

Cara: baca sekali penuh tanpa mengomentari; baca lagi dan catat; kirim `[Tinjau] @Sofi - <bagian> - <temuan> - Saran: <perbaikan>`.

---

## #24. Latihan pitching (SINKRON 2)

Kamu menyampaikan **slide 2** (sekitar 2 menit) dan menjawab dua pertanyaan di bank pertanyaan
([PANDUAN_Wildan.md](PANDUAN_Wildan.md), #24): **"Datanya hanya 74.956 baris, cukup?"** dan **"Bagaimana data simulasi dibuat?"**.
Latih jawabanmu dengan kata-katamu sendiri.

---

## #26. Mendukung pemuatan S10 dan S100

**Menunggu:** #16 (kamu) dan #25 (kueri benar di S1).

Pengujian besar (waktu muat dan kueri) berjalan di **satu laptop uji** (dipilih saat kickoff) supaya perbandingan adil.
Peranmu di sana:

- Pemilik laptop uji membuat datanya sendiri dengan skrip yang sama, lalu membuktikan isinya identik dengan milikmu:

  ```powershell
  python data\generate_scales.py --scale S10
  python data\generate_scales.py --scale S100
  python data\generate_scales.py --verify
  ```

  Bila ada `BEDA`, kamu membantu mencari sebabnya (versi Python, berkas terputus, disk penuh).
- Untuk beban kerja W8 (menambah batch baru ke S100), siapkan batch tambahan di laptop uji **setelah S100 selesai dimuat di ketiganya**:

  ```powershell
  python data\generate_scales.py --extra-batch 100
  ```

  Hasilnya `data\out\batch100` (74.956 anotasi dengan `ann_id` 7.495.600 sampai 7.570.555, dan 4.392 patch). Skrip harus mencetak
  `Batch tambahan 100: 74956 anotasi (ann_id 7495600 sampai 7570555), 4392 patch, folder ...`; bila angkanya lain, `[BLOKIR]`.
- Setelah W8, jumlah baris S100 menjadi 7.570.556 anotasi; muat ulang S100 bila perlu menguji ulang.

Pesan WhatsApp: `[SELESAI] data: laptop uji punya S10 dan S100 yang COCOK dengan CHECKSUMS.txt (Syuep + <pemilik laptop>).`
