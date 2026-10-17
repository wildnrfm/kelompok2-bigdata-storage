# 01. Persiapan umum (dibaca semua anggota)

Bagian ini berisi hal-hal yang dipakai **semua orang**: terminal, pasang alat, ambil repo (clone), Git sehari-hari,
Docker, dan VS Code. Panduan pribadimu (`PANDUAN_<nama>.md`) memanggil bagian-bagian di sini dengan kode **A1 sampai A8**.
Nama, jalur, dan perintah di sini mengikuti [KONTRAK.md](KONTRAK.md).

**Isi**

- [A1. Dasar terminal (PowerShell)](#a1-dasar-terminal-powershell)
- [A2. Pasang alat (langkah #3)](#a2-pasang-alat-langkah-3)
- [A3. Ambil repo ke laptopmu dan latihan Git (langkah #4)](#a3-ambil-repo-ke-laptopmu-dan-latihan-git-langkah-4)
- [A4. Spesifikasi laptop (langkah #5)](#a4-spesifikasi-laptop-langkah-5)
- [A5. Git sehari-hari dan cara mengatasi konflik](#a5-git-sehari-hari-dan-cara-mengatasi-konflik)
- [A6. Docker dalam lima menit](#a6-docker-dalam-lima-menit)
- [A7. Visual Studio Code dalam dua menit](#a7-visual-studio-code-dalam-dua-menit)
- [A8. Kamus istilah](#a8-kamus-istilah)

---

## Cara membaca panduan ini

- Kerjakan **berurutan**, satu langkah, baca hasilnya, baru lanjut. Jangan menempel banyak perintah sekaligus.
- Blok kode berisi **perintah**: salin persis, tempel di PowerShell, tekan Enter. Baris yang diawali `#` di dalam blok
  adalah catatan, bukan perintah.
- Blok berjudul **Contoh hasil** menunjukkan apa yang kira-kira muncul. Angka waktu, tanggal, dan nomor versi boleh
  berbeda; kata kuncinya yang harus sama.
- **Berhasil bila** = tanda langkahnya benar. **Kalau macet** = galat yang sering muncul dan cara memperbaikinya.
- Nomor langkah (#8, #16, ...) sama di semua dokumen dan di grup WhatsApp. Cukup menulis "aku di #9".

### Lima aturan emas

1. Satu langkah, baca hasilnya, baru lanjut.
2. Macet lebih dari **1 jam**: tulis `[BLOKIR]` di grup berisi apa yang kamu coba dan **pesan galat lengkapnya**.
   Teman sering tahu jawabannya dalam 2 menit.
3. Ubah hanya **folder milikmu** (lihat tabel di [README](README.md)). Berkas orang lain: minta pemiliknya.
4. Jangan pernah `git push --force`. Jangan menaruh sandi, token, atau data pribadi di repo.
5. Simpan ke GitHub (commit dan push) setiap selesai satu bagian, jangan menumpuk sampai akhir.

---

## A1. Dasar terminal (PowerShell)

Terminal adalah jendela tempat kamu **mengetik perintah**. Di Windows kita memakai **PowerShell** (bukan CMD dan **bukan
Git Bash**, karena Git Bash mengubah jalur yang diawali `/` sehingga perintah `docker` bisa salah).

- **Membuka**: tekan tombol Windows, ketik `PowerShell`, Enter. (Windows 11: boleh mengetik `Terminal`.)
- Tampilan awal seperti `PS C:\Users\kamu>`. Itu **bukan untuk diketik**; itu tanda "kamu sedang berada di folder ini".
- **Menempel**: salin perintah (Ctrl+C), lalu klik kanan di jendela PowerShell atau tekan Ctrl+V, lalu Enter.
- **Panah atas** = perintah sebelumnya. **Tab** = melengkapi nama berkas. **Ctrl+C** = menghentikan perintah yang berjalan.
- Tulisan **merah** = galat. Baca baris paling atas dan salin **seluruh pesan** bila bertanya di grup.
- Memotret pesan galat untuk `[BLOKIR]`: Win+Shift+S, tarik kotak di sekitar pesan, lalu tempel (Ctrl+V) di WhatsApp.

| Perintah | Artinya |
|---|---|
| `cd C:\proyek` | pindah ke folder itu |
| `cd ..` | naik satu tingkat |
| `dir` | lihat isi folder yang sedang dibuka |
| `mkdir nama` | buat folder baru bernama `nama` |
| `cls` | bersihkan layar |
| `code .` | buka folder sekarang di Visual Studio Code (setelah VS Code terpasang) |

> **Mac atau Linux.** Buka aplikasi Terminal. Perintah `git` dan `docker` sama; ganti `C:\proyek\...` dengan
> `~/proyek/...` dan `python` dengan `python3`. Perintah khusus PowerShell (`Get-Content`, `Select-String`,
> `Expand-Archive`, `Get-CimInstance`) punya padanan `cat`, `grep`, `unzip`; tanyakan di grup bila perlu.

---

## A2. Pasang alat (langkah #3)

Alat dipasang **sekali saja**. Setelah semuanya terpasang, **tutup lalu buka lagi PowerShell** supaya alat barunya dikenali.
Siapkan 30 sampai 60 menit; Docker yang paling lama.

| Alat | Untuk apa | Siapa memerlukan |
|---|---|---|
| Git | mengambil dan mengirim kode ke GitHub | semua |
| Python 3.12 (3.11 sampai 3.13 boleh) | menjalankan skrip data dan uji | semua |
| Visual Studio Code | editor berkas | semua |
| Docker Desktop | menjalankan database di dalam "kotak" (container) | Elsa, Sofi, Levi (Syuep dan Wildan: tidak wajib) |

### Cara A (disarankan): lewat winget

`winget` bawaan Windows 10 (versi terbaru) dan Windows 11. Tempel satu per satu. Bila ditanya setuju syarat, ketik `Y`
lalu Enter; bila muncul jendela izin (UAC), klik Ya.

```powershell
winget install -e --id Git.Git
winget install -e --id Python.Python.3.12
winget install -e --id Microsoft.VisualStudioCode
winget install -e --id Docker.DockerDesktop
```

### Cara B: unduh manual (bila winget tidak ada)

- Git: <https://git-scm.com/download/win>. Klik Next terus (pengaturan bawaan sudah benar).
- Python: <https://www.python.org/downloads/> (pilih 3.12.x). Di jendela pertama **centang "Add python.exe to PATH"**, lalu Install Now.
- Visual Studio Code: <https://code.visualstudio.com/> (Next terus).
- Docker Desktop: <https://www.docker.com/products/docker-desktop/> (lihat langkah Docker di bawah).

### Periksa hasilnya

**Tutup PowerShell, buka lagi**, lalu:

```powershell
git --version
python --version
code --version
```

Contoh hasil (nomor versi boleh berbeda):

```text
git version 2.47.0.windows.1
Python 3.12.7
1.95.0
```

**Berhasil bila**

- [ ] `git --version` menampilkan nomor versi Git
- [ ] `python --version` menampilkan Python 3.11, 3.12, atau 3.13
- [ ] `code --version` menampilkan nomor versi VS Code

### Docker Desktop: pasang dan nyalakan (Elsa, Sofi, Levi)

1. Pasang Docker Desktop (Cara A atau B). Bila ditanya, pilih **Use WSL 2** (bukan Hyper-V) dan izinkan restart laptop.
2. Buka **Docker Desktop** dari menu Start. Setujui syarat. Akun Docker tidak wajib: pilih Skip atau Continue without signing in.
3. Tunggu sampai kiri bawah jendela menunjukkan **Engine running** (hijau). Pertama kali bisa 2 sampai 5 menit.
4. Uji di PowerShell:

   ```powershell
   docker --version
   docker run --rm hello-world
   ```

   ```text
   Docker version 27.3.1, build ce12230

   Hello from Docker!
   This message shows that your installation appears to be working correctly.
   ```

5. **Batasi memori Docker** supaya laptop tidak macet. Buka berkas pengaturan:

   ```powershell
   notepad $env:USERPROFILE\.wslconfig
   ```

   Bila Notepad bertanya "buat berkas baru?", pilih Ya. Isi tiga baris ini lalu simpan (Ctrl+S). Pakai `memory=4GB` bila RAM
   laptopmu 8 GB; `memory=6GB` bila 16 GB atau lebih.

   ```ini
   [wsl2]
   memory=6GB
   processors=2
   ```

6. Terapkan: tutup Docker Desktop, lalu di PowerShell:

   ```powershell
   wsl --shutdown
   ```

   Buka Docker Desktop lagi dan tunggu **Engine running**.

**Docker berhasil bila**

- [ ] `docker run --rm hello-world` menampilkan "Hello from Docker!"
- [ ] Docker Desktop menunjukkan Engine running

### Pengaturan Git (sekali saja)

Ganti nama dan email dengan milikmu (email yang dipakai di akun GitHub). Tanda kutipnya tetap ditulis.

```powershell
git config --global user.name "Nama Lengkapmu"
git config --global user.email "emailmu@contoh.com"
git config --global pull.rebase true
git config --global --list
```

- [ ] Daftar terakhir memuat `user.name`, `user.email`, dan `pull.rebase=true`.

### Pustaka Python untuk uji (Elsa, Sofi, Levi)

Skrip `data/` dan `bench/` (kecuali harness) hanya memakai pustaka bawaan Python. Harness uji butuh dua pustaka untuk
berbicara dengan database. Pasang sekali:

```powershell
python -m pip install pymongo "psycopg[binary]"
```

Contoh hasil (bagian akhir): `Successfully installed pymongo-4.x.x psycopg-3.x.x psycopg-binary-3.x.x`

### Kalau macet

| Tanda | Penyebab dan cara memperbaiki |
|---|---|
| `'winget' is not recognized` | Windows-mu belum punya winget. Pakai Cara B (unduh manual). |
| `'git' is not recognized` (atau `python`, `code`) | PowerShell dibuka sebelum alatnya dipasang. Tutup **semua** jendela PowerShell lalu buka lagi. Masih gagal: restart laptop. |
| `python` membuka Microsoft Store | Matikan alias: Settings > Apps > Advanced app settings > App execution aliases, matikan `python.exe` dan `python3.exe`. Atau pakai `py` sebagai pengganti `python`. |
| pip: `SSLError`, `ProxyError`, atau time out | Masalah jaringan. Ganti jaringan (hotspot HP) lalu ulangi perintahnya. |
| Docker: `WSL 2 installation is incomplete` | Buka PowerShell sebagai **Administrator** (klik kanan, Run as administrator), ketik `wsl --install`, restart laptop, buka Docker Desktop lagi. |
| Docker: virtualisasi dinonaktifkan | Aktifkan virtualisasi di BIOS (Intel VT-x atau AMD SVM). Cek: Task Manager > Performance > CPU > Virtualization: Enabled. Bingung: `[BLOKIR]` beserta tipe laptopmu. |
| Docker Desktop terus "Starting..." | Restart laptop, jalankan `wsl --update`, buka Docker Desktop lagi. |
| `error during connect ... dockerDesktopLinuxEngine` | Docker Desktop belum menyala. Buka aplikasinya dan tunggu Engine running. |

**Pesan WhatsApp**

```text
[SELESAI] alat: Git, Python, VS Code, Docker terpasang (<namamu>).
git <versi>, python <versi>, docker run hello-world berhasil
```

---

## A3. Ambil repo ke laptopmu dan latihan Git (langkah #4)

Repo ada di GitHub dan bersifat **privat**: hanya anggota yang diundang yang bisa melihatnya.
Alamat: <https://github.com/wildnrfm/kelompok2-bigdata-storage>

**Tunggu dulu** sampai Wildan menulis `[SELESAI] root: paket awal sudah di GitHub` di grup (langkah #2). Sebelum itu repo
masih kosong atau belum lengkap.

### Langkah 1. Terima undangan

1. Buka email (cek juga folder Spam) dari GitHub berjudul seperti "wildnrfm invited you to collaborate on
   wildnrfm/kelompok2-bigdata-storage", klik **View invitation**, lalu **Accept invitation**.
2. Tidak ada emailnya? Masuk ke GitHub dengan akunmu, lalu buka
   <https://github.com/wildnrfm/kelompok2-bigdata-storage/invitations>.
3. Cek: membuka alamat repo menampilkan isi repo (bukan halaman 404).

### Langkah 2. Clone ke folder C:\proyek

> **Taruh repo di `C:\proyek`, bukan di Desktop atau Documents.** Bila OneDrive aktif, folder itu disinkronkan otomatis dan
> bisa merusak repo atau memperlambat Docker.

```powershell
mkdir C:\proyek
cd C:\proyek
git clone https://github.com/wildnrfm/kelompok2-bigdata-storage.git
cd kelompok2-bigdata-storage
dir
```

(Bila `mkdir` bilang folder sudah ada, abaikan.) **Pertama kali**, jendela browser terbuka meminta login GitHub: masuk dengan
akunmu lalu klik Authorize. Setelah itu PowerShell melanjutkan sendiri.

Contoh hasil (daftar folder):

```text
Mode   Name
----   ----
d----  baca-dulu
d----  bench
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

### Langkah 3. Cek TEAM.md

Buka `TEAM.md` (`code TEAM.md`). Baris namamu harus berisi **username GitHub-mu**. Bila salah atau kosong, **jangan mengubah
baris orang lain**; beri tahu Wildan di grup.

### Langkah 4. Latihan Git (commit dan push pertamamu)

Latihan ini memastikan alur kirim-terima kodemu berfungsi. Kamu membuat satu berkas kecil di folder `latihan`. Perintah
lengkap dengan namamu ada di panduan pribadimu (bagian "#4"); bentuknya:

```powershell
git pull --rebase
New-Item -ItemType Directory -Force latihan | Out-Null
Set-Content latihan\<panggilan>.txt "Halo, ini latihan <Panggilan>"
git add latihan/<panggilan>.txt
git commit -m "[latihan] <Panggilan>: uji coba push"
git pull --rebase
git push
```

(`<panggilan>` = huruf kecil: `syuep`, `elsa`, `sofi`, atau `levi`.)

Contoh hasil:

```text
[main 3f2a1bc] [latihan] Elsa: uji coba push
 1 file changed, 1 insertion(+)
...
To https://github.com/wildnrfm/kelompok2-bigdata-storage.git
   a1b2c3d..3f2a1bc  main -> main
```

Penjelasan singkat: `git add` memilih berkas yang akan disimpan; `git commit` menyimpannya sebagai satu catatan perubahan
(dengan pesan); `git push` mengirimnya ke GitHub; `git pull --rebase` mengambil kiriman teman lebih dulu.

**Berhasil bila**

- [ ] `git push` berakhir dengan baris `main -> main` tanpa tulisan error
- [ ] di GitHub, folder `latihan` memuat berkas `<panggilan>.txt` milikmu

### Kalau macet

| Tanda | Penyebab dan cara memperbaiki |
|---|---|
| `Please tell me who you are` | Pengaturan Git belum dibuat. Jalankan tiga perintah `git config --global` di A2, lalu ulangi `git commit`. |
| `remote: Repository not found` atau `fatal: repository ... not found` | Undangan belum diterima, atau kamu login dengan akun GitHub lain. Terima undangan (Langkah 1). Bila masih: Control Panel > Credential Manager > Windows Credentials, hapus entri `git:https://github.com`, lalu clone ulang dan login dengan akun yang benar. |
| `! [rejected] main -> main (fetch first)` | Ada kiriman teman yang belum kamu ambil. `git pull --rebase`, lalu `git push`. |
| `fatal: not a git repository` | Kamu belum berada di folder repo. Jalankan `cd C:\proyek\kelompok2-bigdata-storage`. |
| `Authentication failed` | Login salah. Hapus kredensial lama seperti di atas lalu coba lagi. |
| `error: cannot pull with rebase: You have unstaged changes` | Ada perubahan yang belum di-commit. Commit dulu, atau bila itu berkas yang tak sengaja berubah: `git restore namaberkas`. |
| Repo masih kosong setelah clone | Wildan belum selesai #2. Tunggu `[SELESAI] root: ...` di grup, lalu `git pull --rebase`. |

**Pesan WhatsApp**

```text
[SELESAI] latihan: clone dan push berhasil (latihan/<panggilan>.txt) - <Panggilan>
```

---

## A4. Spesifikasi laptop (langkah #5)

Kelompok perlu tahu kekuatan laptop tiap orang untuk memilih **laptop uji S100** (yang menjalankan uji besar). Cukup tiga
angka: RAM, ruang disk kosong, dan prosesor.

**Cara klik**

- RAM dan prosesor: Settings > System > About (Pengaturan > Sistem > Tentang).
- Disk kosong: File Explorer > This PC; lihat "free of" di bawah Local Disk (C:).

**Cara perintah** (hasilnya sama):

```powershell
$cs = Get-CimInstance Win32_ComputerSystem
"{0} {1}: RAM {2:N1} GB" -f $cs.Manufacturer, $cs.Model, ($cs.TotalPhysicalMemory/1GB)
$cpu = Get-CimInstance Win32_Processor
"$($cpu.Name): $($cpu.NumberOfCores) inti, $($cpu.NumberOfLogicalProcessors) thread"
$d = Get-PSDrive C
"Disk C: bebas {0:N0} GB dari {1:N0} GB" -f ($d.Free/1GB), (($d.Free+$d.Used)/1GB)
```

```text
ASUSTeK COMPUTER INC. VivoBook: RAM 15.8 GB
Intel(R) Core(TM) i5-1135G7: 4 inti, 8 thread
Disk C: bebas 142 GB dari 476 GB
```

> **Ambang.** Untuk S1 dan S10 cukup **disk bebas 15 GB**. Laptop yang memuat **S100** (7,84 GB berkas data, ditambah isi
> database dan indeksnya) sebaiknya punya **RAM minimal 16 GB dan disk bebas minimal 25 GB**.

**Pesan WhatsApp**

```text
Spesifikasi <Panggilan>:
OS: Windows <10/11>
CPU: <nama CPU>, <n> inti
RAM: <n> GB
Disk C bebas: <n> GB
Docker Desktop: <sudah / belum / tidak perlu>
```

---

## A5. Git sehari-hari dan cara mengatasi konflik

Setiap selesai mengerjakan satu bagian, simpan dan kirim hasilnya ke GitHub dengan **pola enam baris** ini (ganti folder
dan pesannya):

```powershell
cd C:\proyek\kelompok2-bigdata-storage
git pull --rebase
git add mongodb
git commit -m "[mongodb] contoh pesan: indeks dan kueri W3 selesai"
git pull --rebase
git push
```

- `git pull --rebase` mengambil kiriman teman lebih dulu (dua kali: sebelum dan sesudah commit, supaya `git push` tidak ditolak).
- `git add <folder>` hanya memilih **foldermu**. Cek dulu dengan `git status`: merah = belum dipilih, hijau = siap di-commit.
- Pesan commit diawali **[folder]**: `[data]`, `[mongodb]`, `[postgis]`, `[hdfs-parquet]`, `[bench]`, `[results]`, `[docs]`,
  `[latihan]`; berkas di akar repo dan `tests/` memakai `[root]`.

| Boleh dan dianjurkan | Jangan |
|---|---|
| commit kecil dan sering, dengan pesan jelas | `git push --force` (bisa menghapus kerja teman) |
| `git pull --rebase` sebelum mulai bekerja | mengubah folder orang lain |
| `git status` sebelum `git add` | menaruh sandi atau token di repo |
| `git log --oneline -5` untuk melihat riwayat | meng-commit `data/out/` (data besar, sudah di `.gitignore`) |

### Kalau muncul konflik

**Konflik** terjadi saat dua orang mengubah baris yang sama. Git berhenti dan meminta kamu memilih. Ini normal dan bisa
diselesaikan:

1. `git status` menampilkan berkas bertanda **both modified**. Buka berkas itu (`code namaberkas`). Kamu akan melihat penanda:

   ```text
   <<<<<<< HEAD
   versi dari GitHub (kiriman teman)
   =======
   versi milikmu
   >>>>>>> a1b2c3d pesan commitmu
   ```

2. Putuskan isi akhirnya (sering kali **simpan keduanya**), lalu **hapus tiga baris penanda** (`<<<<<<<`, `=======`, `>>>>>>>`).
   VS Code menyediakan tombol Accept Current, Incoming, atau Both di atas penanda; boleh dipakai, lalu cek hasilnya.
3. Simpan berkas (Ctrl+S), lalu lanjutkan:

   ```powershell
   git add namaberkas
   git rebase --continue
   git push
   ```

4. Ragu atau berantakan? Batalkan semuanya dengan `git rebase --abort` (kembali ke keadaan sebelum `git pull`), lalu tulis
   `[BLOKIR]` di grup.

| Tanda | Penyebab dan cara memperbaiki |
|---|---|
| `cannot pull with rebase: You have unstaged changes` | Ada perubahan yang belum di-commit. Commit dulu, lalu `git pull --rebase`. Atau simpan sementara: `git stash`, `git pull --rebase`, `git stash pop`. |
| `! [rejected] ... (fetch first)` atau `non-fast-forward` | Ada kiriman teman yang belum kamu ambil: `git pull --rebase`, lalu `git push` lagi. |
| `You are in the middle of a rebase` | Konflik belum selesai. Selesaikan (`git add` lalu `git rebase --continue`) atau batalkan (`git rebase --abort`). |
| `File ... exceeds GitHub's file size limit of 100.00 MB` | Berkas besar ikut ter-commit (biasanya `data/out/`). Belum berhasil push? `git reset --soft HEAD~1`, lalu `git restore --staged data/out`, pastikan `.gitignore` memuat `data/out/`, commit ulang. Ragu: `[BLOKIR]`. |
| `nothing to commit, working tree clean` | Git tidak melihat perubahan. Pastikan berkas sudah disimpan (Ctrl+S) dan kamu berada di folder repo. |
| `fatal: not a git repository` | Kamu belum berada di folder repo: `cd C:\proyek\kelompok2-bigdata-storage`. |

---

## A6. Docker dalam lima menit

**Docker** menjalankan program (MongoDB, PostgreSQL, Spark) di dalam "kotak" terisolasi, jadi kamu tidak perlu memasangnya
langsung di Windows. Istilah penting:

| Istilah | Artinya |
|---|---|
| image | cetakan program yang diunduh sekali (misalnya `mongo:8`) |
| container | kotak yang sedang berjalan, dibuat dari image. Nama tetap kita: `sen12ls-mongo`, `sen12ls-postgis`, `sen12ls-namenode`, `sen12ls-datanode1`, `sen12ls-datanode2`, `sen12ls-spark` |
| volume | penyimpanan data milik container supaya data tidak hilang saat container dimatikan (`mongo_data`, `pg_data`) |
| compose | berkas `docker-compose.yml` yang menjelaskan container, port, dan volume sekaligus. Satu perintah menyalakan semuanya |
| port | pintu masuk. `5433:5432` berarti pintu 5433 di laptopmu tersambung ke pintu 5432 di dalam container |

| Perintah (jalankan di folder yang berisi `docker-compose.yml`) | Artinya |
|---|---|
| `docker compose up -d` | nyalakan di latar belakang (pertama kali mengunduh image) |
| `docker compose ps` | lihat container yang berjalan (STATUS harus Up) |
| `docker compose logs --tail 50` | 50 baris log terakhir; berguna saat ada galat |
| `docker compose stop` / `docker compose start` | matikan / nyalakan lagi; **data tetap ada** |
| `docker compose down` | hapus container; MongoDB dan PostGIS: data tetap ada; **HDFS: data ikut hilang** |
| `docker compose down -v` | hapus container **dan semua datanya**. Hati-hati! |
| `docker exec <nama> <perintah>` | jalankan perintah di dalam container (dari folder mana pun) |
| `docker stats --no-stream` | lihat pemakaian CPU dan RAM tiap container |

Hal yang perlu diingat:

- **Satu penyimpanan aktif sekali waktu.** Sebelum menyalakan yang lain, matikan yang sedang jalan (`docker compose stop`
  di foldernya). RAM laptop terbatas dan hasil uji jadi tidak adil bila dua database berebut memori.
- Di semua container, folder `data` repo terpasang (hanya baca) di `/sen12ls-data`. Berkas `data/out/s1/annotations.csv`
  di laptopmu terlihat di dalam container sebagai `/sen12ls-data/out/s1/annotations.csv`.
- Folder penyimpanan terpasang juga: `mongodb/` di `/scripts`, `postgis/` di `/sql`, `hdfs-parquet/` di `/hdfs-parquet`
  (dan `bench/` di `/bench`, `results/` di `/results` pada container Spark).
- Kontainer dan portnya (tetap, jangan diubah):

| Penyimpanan | Container | Port di laptop |
|---|---|---|
| MongoDB | `sen12ls-mongo` | 27017 |
| PostGIS | `sen12ls-postgis` | 5433 (menuju 5432 di dalam) |
| HDFS | `sen12ls-namenode`, `sen12ls-datanode1`, `sen12ls-datanode2` | 9870 (halaman web NameNode) |
| Spark | `sen12ls-spark` | 4040 (halaman web, hanya saat job berjalan) |

| Tanda | Penyebab dan cara memperbaiki |
|---|---|
| `error during connect` atau `cannot connect to the Docker daemon` | Docker Desktop belum menyala. Buka aplikasinya, tunggu Engine running. |
| `no configuration file provided: not found` | Kamu tidak berada di folder yang berisi `docker-compose.yml`. `cd` ke foldernya (mis. `cd mongodb`). |
| `Bind for 0.0.0.0:27017 failed: port is already allocated` | Ada program lain memakai port itu (container lain atau program terpasang). `docker ps` untuk mencari, lalu matikan yang bentrok. |
| `no space left on device` | Disk penuh. `docker system prune` menghapus sisa yang tak terpakai (tanyakan dulu bila ragu); kosongkan juga disk Windows. |
| unduhan image gagal atau lambat | Masalah jaringan. Ulangi `docker compose up -d`; unduhan akan melanjutkan. |

---

## A7. Visual Studio Code dalam dua menit

**VS Code** adalah editor tempat kamu membuka dan mengubah berkas teks: kode, Markdown, SQL, catatan. Enam hal cukup:

1. **Membuka folder repo**: di PowerShell ketik `cd C:\proyek\kelompok2-bigdata-storage` lalu `code .` (titik berarti
   folder ini). VS Code terbuka dengan daftar berkas di panel kiri (Explorer).
2. **Membuka berkas**: klik namanya di panel kiri. Berkas baru: klik kanan di folder, pilih New File.
3. **Menyimpan**: Ctrl+S. Titik di samping nama berkas berarti belum disimpan. Git hanya melihat yang sudah disimpan.
4. **Terminal di dalam VS Code**: menu Terminal > New Terminal (atau Ctrl+`). Pastikan namanya **powershell** (bukan Git Bash;
   ganti lewat tanda panah di sebelah +). Terminal ini langsung berada di folder repo.
5. **Mencari**: Ctrl+F mencari di berkas yang terbuka; Ctrl+Shift+F mencari di seluruh repo; Ctrl+Z membatalkan.
6. **Membaca panduan berwarna**: buka berkas `.md` lalu tekan **Ctrl+Shift+V** untuk tampilan rapi (preview).

> Ekstensi **Python** (Microsoft) dari ikon kotak di panel paling kiri membuat kode Python berwarna dan rapi. Tidak wajib.

---

## A8. Kamus istilah

| Istilah | Artinya |
|---|---|
| **Sen12Landslides** | dataset kita: inventaris longsor dengan citra satelit Sentinel-1 dan Sentinel-2 (Höhn dkk., Scientific Data 12:1772, CC BY 4.0). Kita memakai **metadatanya**, bukan citranya |
| **anotasi** | satu poligon longsor di inventaris (74.956 poligon). Disimpan sebagai atribut + titik pusat + kotak pembatas |
| **patch** | satu potongan citra yang terdaftar di `splits_aligned.json` (4.392 patch; split train, val, test) |
| **titik pusat (center)** | titik tengah poligon (centroid berbobot luas), disimpan sebagai titik GeoJSON atau `geometry(Point,4326)` |
| **kotak pembatas (bbox)** | persegi terkecil yang membungkus poligon; disimpan sebagai poligon persegi |
| **S1, S10, S100** | skala data: S1 = data asli (74.956 anotasi); S10 = 10 kali; S100 = 100 kali (7.495.600). Simulasi bersarang dengan seed tetap 20261023 |
| **batch** | satu salinan S1 dalam simulasi; `sim_batch` menandai batch asal (0 = data asli) |
| **NDJSON** | satu dokumen JSON per baris; format muat MongoDB (`mongoimport`) |
| **CSV** | tabel teks dengan kolom dipisah koma; format muat PostGIS (`COPY`) dan Spark |
| **Parquet** | format berkas kolumnar terkompresi; kita menyimpannya di HDFS |
| **HDFS** | sistem berkas terdistribusi Hadoop: NameNode (catatan letak blok) dan DataNode (penyimpan blok); replikasi 2 |
| **Spark SQL** | mesin yang menjalankan SQL di atas berkas Parquet (tanpa indeks spasial) |
| **MongoDB 2dsphere** | indeks spasial pada bola bumi; kueri memakai `$geoWithin` dan `$geoIntersects` |
| **PostGIS GiST** | indeks spasial pada kotak pembatas; kueri memakai `ST_Intersects` |
| **EPSG:4326** | sistem koordinat bujur dan lintang (derajat). Dugaan untuk data ini; tercatat di kamus data |
| **W1 sampai W10** | beban kerja uji (lihat [KONTRAK.md](KONTRAK.md) bagian 6) |
| **H1 sampai H5, E1 sampai E4** | hipotesis dan eksperimen (KONTRAK bagian 7); dugaan awal, belum diuji |
| **cold dan warm** | cold = kueri pertama setelah container dinyalakan ulang (cache dingin); warm = setelah satu putaran pemanasan |
| **median dan p95** | median = nilai tengah waktu; p95 = 95% eksekusi lebih cepat dari angka ini |
| **harness** | skrip yang menjalankan kueri berulang dan mencatat waktunya ke CSV (`bench/harness.py`) |
| **wasit** | skrip yang menghitung jawaban benar langsung dari CSV tanpa database (`bench/kebenaran.py`) |
| **checksum SHA-256** | sidik jari berkas; dua berkas yang isinya sama persis memberi checksum yang sama |
| **commit, push, pull, rebase** | simpan perubahan di laptop; kirim ke GitHub; ambil dari GitHub; susun ulang perubahanmu di atas kiriman teman |
| **konflik** | dua orang mengubah baris yang sama; harus dipilih manual (lihat A5) |
