# Pemecahan masalah (satu tempat untuk semua galat yang sering muncul)

Cari **kata dari pesan galatmu** di tabel yang sesuai. Setiap panduan pribadi juga punya tabel "Kalau macet" untuk langkahnya sendiri; tabel di sini
mengumpulkan yang paling sering dan yang berlaku untuk semua orang. Bila tidak ketemu dalam **15 menit**, tulis `[BLOKIR]` (bentuknya di bagian terakhir):
macet lebih dari satu jam tanpa kabar adalah kesalahan terbesar, bukan galatnya.

> Prinsip: **salin pesan galat utuh** (bukan hanya "error"), sebutkan perintah yang kamu jalankan, dan jangan memperbaiki dengan cara yang menghapus atau menimpa pekerjaan orang lain.
> Larangan tetap: **jangan `git push --force`**, jangan menaruh sandi atau data pribadi di repo, jangan mematikan pemeriksaan TLS/sertifikat, dan jangan mengubah definisi kueri supaya angkanya "cocok".

## 1. Git dan GitHub

| Tanda | Penyebab dan cara memperbaiki |
|---|---|
| `git` tidak dikenali (`The term 'git' is not recognized`) | Git belum terpasang atau PowerShell belum dibuka ulang. Tutup dan buka PowerShell baru; `git --version`. Pasang ulang di [01_PERSIAPAN_UMUM.md](01_PERSIAPAN_UMUM.md), A2. |
| `Repository not found` atau `Authentication failed` saat clone atau push | Kamu belum menerima undangan repo (cek email GitHub) atau login salah. Buka <https://github.com/wildnrfm/kelompok2-bigdata-storage> di browser; bila 404, undangan belum diterima. Login ulang lewat jendela yang dibuka Git. |
| `! [rejected] main -> main (fetch first)` atau `non-fast-forward` | Orang lain sudah push. `git pull --rebase` lalu `git push`. **Jangan** `--force`. |
| `CONFLICT (content): Merge conflict in <berkas>` | Dua orang mengubah baris yang sama. Buka berkas, pilih isi yang benar (hapus penanda `<<<<<<<`, `=======`, `>>>>>>>`), lalu `git add <berkas>` dan `git rebase --continue`. Tidak yakin? `git rebase --abort` dan tanya pemilik folder. Cara lengkap: 01_PERSIAPAN_UMUM, A5. |
| `You have unstaged changes` saat `git pull --rebase` | Ada perubahan yang belum di-commit. Commit dulu (`git add ...`, `git commit -m "[folder] ..."`) atau simpan sementara (`git stash`, lalu `git pull --rebase`, lalu `git stash pop`). |
| `Author identity unknown` / `Please tell me who you are` | Pengaturan Git belum dibuat: `git config --global user.name "Nama Kamu"` dan `git config --global user.email "emailmu"` (A2). |
| Berkas besar atau berkas aneh muncul di `git status` (`data/out`, `cek-sen12ls`, `__pycache__`, `.env`) | Jangan di-`add`. Semuanya ada di `.gitignore`; bila tetap muncul, `git status --ignored` dan tanyakan Wildan. **Jangan** commit dengan `git add .` sebelum membaca `git status`. |
| `warning: LF will be replaced by CRLF` | Tidak berbahaya. Repo memaksa akhir baris LF lewat `.gitattributes`; jangan mengubah pengaturan `core.autocrlf` tanpa bertanya. |
| Salah commit (pesan salah atau berkas salah) dan **belum push** | `git reset --soft HEAD~1` (membatalkan commit, perubahan tetap), perbaiki, commit ulang. Sudah push: tulis di grup; jangan menulis ulang riwayat sendirian. |
| Terlanjur menaruh sandi atau data pribadi di commit | Hentikan, **jangan push**; bila sudah push, beri tahu Wildan segera (sandi harus diganti). Untuk database uji, sandi `postgres` hanya berlaku di laptop sendiri dan memang ada di berkas compose. |

## 2. Python dan pustaka

| Tanda | Penyebab dan cara memperbaiki |
|---|---|
| `python` tidak dikenali, atau membuka Microsoft Store | Python belum terpasang atau jalur belum masuk PATH. Pasang dari python.org dengan **"Add python.exe to PATH"** dicentang, lalu buka PowerShell baru. Versi yang dipakai: 3.12 (3.11 sampai 3.13 boleh). |
| `ModuleNotFoundError: No module named 'pymongo'` (atau `psycopg`) | `python -m pip install pymongo "psycopg[binary]"`. Pakai `python -m pip`, bukan `pip` saja. |
| `pip` gagal mengunduh (`SSL`, `proxy`, `timeout`) | Jaringan kampus atau VPN memblokir. Coba jaringan lain (hotspot HP). **Jangan** mematikan pemeriksaan sertifikat (`--trusted-host`, `verify=False`) dan jangan mengutak-atik proxy sistem; tulis `[BLOKIR]`. |
| `UnicodeEncodeError` atau teks berubah menjadi `?` di PowerShell | Skrip proyek memakai ASCII murni dan aman. Bila terjadi di skripmu sendiri: `chcp 65001` lalu ulangi, atau `$env:PYTHONIOENCODING = "utf-8"`. |
| Anaconda: prompt `(base) PS` dan `python` menunjuk ke Anaconda | Boleh dipakai (Python 3.13 juga lulus uji). Pastikan `python --version` memberi 3.11 sampai 3.13. Pustaka dipasang di lingkungan yang sama dengan yang menjalankan skrip. |
| `python tests\uji_semua.py` gagal | Salin **nama uji yang `GAGAL`** dan pesannya ke `[BLOKIR]`. Jalankan **seluruh** uji (jangan memilih sebagian; uji saling bergantung). Pastikan `git status` bersih dan `git pull --rebase` terbaru. |

## 3. Docker Desktop (berlaku untuk MongoDB, PostGIS, HDFS, Spark)

| Tanda | Penyebab dan cara memperbaiki |
|---|---|
| `error during connect` / `docker daemon is not running` | Docker Desktop belum menyala. Buka aplikasinya; tunggu **Engine running** (ikon paus hijau). |
| `WSL 2 requires an update` / Docker tidak mau start | Jalankan `wsl --update` di PowerShell administrator, lalu mulai ulang Docker Desktop. Virtualisasi di BIOS harus aktif (lihat 01_PERSIAPAN_UMUM, Docker Desktop). |
| `port is already allocated` | Ada program atau container lain di port itu (27017 MongoDB, 5433 PostGIS, 9870 HDFS, 4040 Spark). `docker ps`; matikan yang bentrok (`docker compose stop` di foldernya). |
| `no space left on device` | Disk atau disk-image Docker penuh. Hapus `data\out\s100` bila tidak dipakai; `docker system df` untuk melihat; `docker system prune` hanya **setelah bertanya**, karena menghapus container dan image yang tidak berjalan. |
| Container `Exited (137)` | Kehabisan memori (OOM). `docker stats --no-stream`; tutup program berat; atur `memory=` di `C:\Users\<nama>\.wslconfig` (01_PERSIAPAN_UMUM) lalu `wsl --shutdown`. **Beri tahu grup** supaya semua uji memakai pengaturan yang sama. |
| Folder di dalam container kosong (`/sen12ls-data`, `/scripts`, `/sql`, `/bench`) | Pemasangan folder gagal. Repo harus di `C:\proyek` (bukan `Downloads` atau OneDrive); Docker Desktop > Settings > Resources > File sharing mengizinkan drive C; jalankan `docker compose` **dari foldernya** (jalur `../data` relatif terhadap folder itu); `docker compose down` lalu `up -d`. |
| Perintah `docker exec` berhenti dengan `No such container` | Nama container salah atau belum jalan. `docker ps -a`. Nama baku: `sen12ls-mongo`, `sen12ls-postgis`, `sen12ls-namenode`, `sen12ls-datanode1`, `sen12ls-datanode2`, `sen12ls-spark`. |
| `no matching manifest for linux/...` | Arsitektur CPU tidak cocok dengan image. `[BLOKIR]` dengan hasil `docker version`. |
| Download image sangat lama atau `TLS handshake timeout` | Jaringan. Ulangi `docker compose up -d`; gunakan jaringan lain. Jangan memakai mirror tak dikenal. |
| Dua penyimpanan menyala dan laptop lambat | Aturan emas: **satu penyimpanan sekali waktu**. `docker ps`; `docker compose stop` di folder yang tidak dipakai. |

## 4. Data (Syuep dan semua yang membuat S1)

| Tanda | Penyebab dan cara memperbaiki |
|---|---|
| `Berkas ...\inventories.zip tidak ada` atau `splits_aligned.json tidak ada` | `git pull --rebase`; kedua berkas ada di `data\raw\` setelah Wildan push. Bila tetap tidak ada, `[BLOKIR]` ke Wildan. |
| `convert_inventory.py` berakhir dengan kode 3 / `[BLOKIR]` | Pemeriksaan diri konverter: hasil berbeda dari laporan inventaris 22 Okt 2026. **Jangan memakai data itu.** Salin seluruh keluaran ke `[BLOKIR]` @Wildan @Syuep. |
| `python data\generate_scales.py --verify` menampilkan `BEDA` | Isi berkasmu tidak sama dengan checksum. Hapus `data\out\sN` yang beda, buat ulang (`convert_inventory.py` untuk S1; `generate_scales.py --scale S10` untuk S10), verifikasi lagi. Tetap `BEDA`: `[BLOKIR]` @Syuep. |
| `BELUM ADA` pada `--verify` | Skala itu belum kamu buat. Tidak apa-apa bila memang belum perlu. |
| `data\cek_data.py` tidak lulus | Salin baris yang bertanda `GAGAL`. Jangan melanjutkan ke muat data. |
| Pembuatan S100 lama atau memakan disk | Normal: sekitar 5 menit dan 7,84 GB. Pastikan disk bebas 25 GB; jangan menutup jendela. |

## 5. MongoDB (Elsa, Sofi)

Rincian lengkap di [PANDUAN_Elsa.md](PANDUAN_Elsa.md) (tabel di #9, #13, #26).

| Tanda | Penyebab dan cara memperbaiki |
|---|---|
| `mongoimport: executable file not found` | Image tidak membawa `mongoimport`. Pakai cadangan `python mongodb\muat_pymongo.py --skala S1` dan catat di grup. |
| `Failed: open /sen12ls-data/out/s1/annotations.ndjson: no such file` | S1 belum dibuat atau folder tidak terpasang (bagian 3 dan 4 di atas). |
| `E11000 duplicate key` | Koleksi sudah berisi data. Tambahkan `--drop` pada `mongoimport` (hanya saat memuat ulang; bukan saat W8). |
| `Can't extract geo keys` / `Loop is not valid` saat membuat indeks | Ada geometri tidak sah. `python data\cek_data.py --skala S1` harus lulus; bila lulus, `[BLOKIR]` dengan **seluruh** pesan dan `_id` dokumen yang disebut. |
| `ServerSelectionTimeoutError` dari Python | Container belum siap atau port berbeda; `docker compose ps` harus menunjukkan `0.0.0.0:27017->27017`. |
| `w3.js`: `load(...) is not defined` | Jalankan lewat `docker exec ... mongosh --file /scripts/queries/w3.js`, bukan `mongosh` di Windows. |

## 6. PostgreSQL dan PostGIS (Levi)

Rincian lengkap di [PANDUAN_Levi.md](PANDUAN_Levi.md) (tabel di #10, #14, #26).

| Tanda | Penyebab dan cara memperbaiki |
|---|---|
| `password authentication failed for user "postgres"` | Volume `pg_data` dibuat saat sandinya lain. `docker compose down -v` di folder `postgis` (**menghapus data PostGIS**), lalu `up -d`. Jangan memakai `.env`; sandi uji `postgres` adalah bawaan compose dan harness. |
| `could not open file "/sen12ls-data/out/s1/annotations.csv" for reading` | S1 belum dibuat atau folder tidak terpasang (bagian 3 dan 4). |
| `Isi dulu: -v folder=...` | Perintah `load.sql` butuh `-v folder=/sen12ls-data/out/s1` (atau s10, s100, batch100). |
| `duplicate key value violates unique constraint "annotations_pkey"` | Tabel sudah berisi data. Mulai dari `schema.sql` (menghapus tabel dan indeks), atau pakai `-v tambah=1` **hanya** untuk batch baru (W8). |
| `Anotasi tidak ditemukan atau tidak punya event_date` | `-v ann=` menunjuk anotasi yang tidak ada atau tanpa tanggal. Pilih yang lain, mis. `-v ann=100`. |
| Rencana kueri menunjukkan `Seq Scan on annotations` untuk W2 | Statistik belum ada atau indeks belum dibuat. Jalankan `indexes.sql` (menjalankan `VACUUM ANALYZE`), ulangi `-v explain=1`, dan catat hasilnya. |
| `too many clients already` pada `--clients 100` | Batas koneksi bawaan PostgreSQL 100. Catat sebagai temuan di laporan; jangan mengubah pengaturan hanya untuk satu penyimpanan. |

## 7. HDFS dan Spark (Levi, Syuep)

Rincian lengkap di [PANDUAN_Levi.md](PANDUAN_Levi.md) (tabel di #12, #15, #26).

| Tanda | Penyebab dan cara memperbaiki |
|---|---|
| `Live datanodes (0)` atau `(1)` | Tunggu 30 sampai 60 detik setelah `up -d`. Tetap: `docker compose logs datanode1 --tail 30`. `Incompatible clusterIDs` → `docker compose down` lalu `up -d` (menghapus data HDFS). |
| `Name node is in safe mode` | Normal 30 sampai 60 detik setelah menyala. Tunggu; `docker exec sen12ls-namenode hdfs dfsadmin -safemode get` harus `OFF`. |
| Galat membaca konfigurasi (`NumberFormatException ... "2\r"`) | `hdfs-parquet/hadoop.env` berakhir baris CRLF. Buka di VS Code, ubah `CRLF` ke `LF` (kanan bawah), simpan, `docker compose down` lalu `up -d`. |
| `Gagal menulis hdfs://...` dari `csv_to_parquet.py` | NameNode atau DataNode belum siap (lihat dua baris di atas), atau disk Docker penuh. |
| `Compression codec zstd not supported` | Tambahkan `--kompresi snappy` pada `csv_to_parquet.py`, catat di grup dan laporan, dan pakai pilihan yang sama untuk S10 dan S100. |
| `Java heap space` atau Spark berhenti di S100 | Memori habis. Jangan menaikkan `--driver-memory` hanya untuk Spark (adil: 2 GB); tutup program lain; catat dan `[BLOKIR]` bila berulang. |
| Kueri Spark di S100 terlalu lama | Pakai `--limit-titik 20` (aturan di [PANDUAN_Sofi.md](PANDUAN_Sofi.md), #27) dan pastikan hanya Spark yang menyala. |
| `docker compose down` pada HDFS tak sengaja | Data HDFS hilang. Ulangi `csv_to_parquet.py` untuk skala yang diperlukan (menimpa); CSV di `data\out` tidak ikut terhapus. |

## 8. Harness, pembanding, dan pencatat (`bench/`)

| Tanda | Penyebab dan cara memperbaiki |
|---|---|
| `Jumlah data tidak cocok. Muat skala S1 dulu, atau jalankan lagi dengan --force.` | **Pagar anti salah label**: yang termuat di penyimpanan bukan skala yang kamu minta. Muat skala yang benar. `--force` hanya bila kamu paham alasannya (jangan untuk hasil yang masuk laporan). |
| `Tidak bisa terhubung ke mongodb` / `postgis` | Container belum jalan atau port berbeda. `docker compose ps` di foldernya. |
| `psycopg belum terpasang` / `pymongo belum terpasang` | `python -m pip install pymongo "psycopg[binary]"`. |
| `Berkas bench/points.json tidak ada` | `git pull --rebase`; berkas ini di-commit Wildan. Jangan membuatnya sendiri kecuali diminta (hasil harus identik: `git status` bersih). |
| `compare_counts`: `Cocok: n dari 100` dengan `n` kurang dari 100 | Ada kueri yang jumlahnya beda dari wasit. Lihat tabel selisih; periksa urutan: skala yang dimuat, indeks sudah ada, data COCOK dengan checksum, berkas yang dibandingkan memang W/skala yang sama. **Jangan** menyesuaikan jendela atau tanggal supaya cocok. |
| `compare_counts`: `berkas harus memuat beban kerja dan skala yang sama` | Kamu mencampur beban kerja atau skala. Pilih berkas `YYYYMMDD_<penyimpanan>_<W>_<skala>.csv` yang sama beban dan skalanya. |
| `catat.py`: `Perintah berakhir dengan kode ..., jadi waktunya TIDAK dicatat` | Perintah di dalam gagal; baca galatnya. Waktu hanya dicatat bila berhasil. |
| `summarize.py` tidak menemukan berkas | Jalankan dari akar repo; `results\*.csv` harus ada (`git pull --rebase`). |
| Hasil bergoyang antar ulangan | Tutup program lain; lihat `median_ulangan_min` dan `median_ulangan_maks` di `results/ringkasan.csv`; sebut dalam laporan. |

## 9. Cara menulis `[BLOKIR]` yang membuat orang bisa langsung membantu

Kirim **satu pesan** ke grup (bukan potongan-potongan) dengan bentuk:

```text
[BLOKIR] <langkah #> <apa yang mau dicapai>
Perintah: <perintah persis yang kamu jalankan>
Galat: <pesan galat utuh, salin tempel>
Sudah dicoba: <apa yang sudah kamu coba dan hasilnya>
Laptop: <Windows 10/11, RAM, disk kosong, Docker versi bila relevan>
@nama (pemilik langkah atau folder yang bersangkutan)
```

Contoh:

```text
[BLOKIR] #14 memuat S1 ke PostGIS
Perintah: docker exec sen12ls-postgis psql -U postgres -d sen12ls -v folder=/sen12ls-data/out/s1 -f /sql/load.sql
Galat: could not open file "/sen12ls-data/out/s1/annotations.csv" for reading: No such file or directory
Sudah dicoba: python data\generate_scales.py --verify (COCOK); docker exec sen12ls-postgis ls /sen12ls-data -> kosong
Laptop: Windows 11, RAM 16 GB, disk kosong 80 GB, Docker Desktop 4.x
@Wildan @Syuep
```

Pemilik langkah menjawab di grup dalam beberapa jam; bila tidak, Wildan menunjuk orang lain. Setelah masalah selesai, tulis `[SELESAI]` dan **apa penyebabnya**, supaya yang lain tidak mengulang.
