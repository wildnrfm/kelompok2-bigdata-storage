# 00. Alur kerja berurutan (peta seluruh pekerjaan)

Dokumen ini adalah **peta**: apa yang dikerjakan, oleh siapa, menunggu siapa, dan apa hasilnya. Langkah rinci (perintah,
contoh hasil, cara mengatasi galat) ada di panduan pribadi: [Wildan](PANDUAN_Wildan.md), [Syuep](PANDUAN_Syuep.md),
[Elsa](PANDUAN_Elsa.md), [Sofi](PANDUAN_Sofi.md), [Levi](PANDUAN_Levi.md). Hal yang dipakai bersama (terminal, Git,
Docker) ada di [01_PERSIAPAN_UMUM.md](01_PERSIAPAN_UMUM.md). Nama, jalur, kolom, dan perintah baku ada di
[KONTRAK.md](KONTRAK.md); bila dua dokumen berbeda, **KONTRAK yang benar**.

## Yang sedang kita kerjakan

Tugas 2 Big Data Storage: merancang arsitektur penyimpanan dan memilih penyimpanan yang tepat untuk satu dataset.
Kelompok 2 memakai **Sen12Landslides**: inventaris longsor dengan **74.956 poligon** dan **4.392 patch** citra satelit.
Kita menyimpan **katalog metadatanya** (atribut, titik pusat, dan kotak pembatas; bukan citranya) di tiga tempat:

| Penyimpanan | Peran | Indeks spasial |
|---|---|---|
| MongoDB | basis data dokumen | 2dsphere |
| PostgreSQL + PostGIS | basis data relasional spasial | GiST |
| HDFS + Parquet, dibaca Spark SQL | baseline (berkas kolumnar tanpa indeks spasial) | tidak ada |

Lalu kita **mengukur** seberapa cepat tiap tempat menjawab enam kueri (W1 sampai W6) pada tiga skala data
(**S1** = data asli, **S10**, **S100** = simulasi 10 dan 100 kali), serta waktu muat, waktu indeks, dan ukuran di disk
(W7, W8). Dari situ kita menguji hipotesis H1 sampai H5 dan menulis laporan.

Semua kode dasar (konverter data, generator skala, harness uji, wasit jawaban benar, berkas Docker, kueri) **sudah
disiapkan** dan ada di repo. Tugas kalian adalah **menjalankan, memeriksa, mengukur, dan menjelaskan**, bukan menulis
dari nol. Bagian "Yang sudah dibuktikan dan yang belum" di [KONTRAK.md](KONTRAK.md) (bagian 10) jujur tentang apa yang
sudah diuji dan apa yang baru terbukti saat kalian menjalankannya.

## Siapa mengerjakan apa

| Panggilan | Peran | Folder | Langkah utama |
|---|---|---|---|
| **Wildan** | Project Lead, Dokumentasi/QA | `docs/`, `tests/`, berkas di akar | #2, #6, #7, #18, #19, #21, #22, #23, #24, #30, #31 |
| **Syuep** | Data Collection Engineer | `data/` | #8, #15 (mendampingi), #16, #20, #26 |
| **Elsa** | Storage A (MongoDB); membantu analisis | `mongodb/` | #9, #11 (membantu), #13, #17 (membantu), #25, #26, #27 (membantu), #29 (membantu) |
| **Sofi** | Performance Analyst; membantu MongoDB | `bench/`, `results/` | #9 (membantu), #11, #13 (membantu), #17, #25 sampai #29 |
| **Levi** | Storage B (PostGIS dan HDFS-Parquet) | `postgis/`, `hdfs-parquet/` | #10, #12, #14, #15, #25, #26 |

Langkah bersama semua orang: #3, #4, #5, #7, #18, #19, #20, #23, #24 (dan #31 untuk QA).

## Enam fase dan urutan langkah

Nomor langkah **tetap** dan dipakai di grup. "Menunggu" berarti langkah itu belum bisa dimulai sebelum langkah yang disebut selesai.

### Fase 1. Siapkan repo

| # | Langkah | Siapa | Menunggu | Perkiraan waktu |
|---|---|---|---|---|
| 1 | Repo di GitHub (sudah ada; dikosongkan lalu diisi ulang) | Wildan | - | selesai |
| 2 | Pasang paket awal, data mentah, uji, **push** | Wildan | - | 45 sampai 90 menit |
| 3 | Pasang alat (Git, Python, VS Code, Docker) | Syuep, Elsa, Sofi, Levi | - | 30 sampai 60 menit |
| 4 | Clone repo dan latihan Git | Syuep, Elsa, Sofi, Levi | #2 dan #3 | 15 sampai 20 menit |
| 5 | Tulis spesifikasi laptop di grup | Syuep, Elsa, Sofi, Levi | - | 5 menit |
| 6 | Cek `TEAM.md`; tentukan jam kickoff | Wildan | #4 | 15 menit |
| 7 | **KICKOFF** (panggilan grup) | Semua | #6 | 30 menit |

### Fase 2. Data dan penyimpanan

| # | Langkah | Siapa | Menunggu | Perkiraan waktu |
|---|---|---|---|---|
| 8 | S1 di laptop Syuep dan cocokkan checksum | Syuep | #7 | 30 sampai 60 menit |
| 9 | Docker MongoDB | Elsa memimpin, Sofi membantu | #7 | 30 sampai 45 menit |
| 10 | Docker PostGIS dan skema | Levi | #7 | 30 sampai 45 menit |
| 11 | Harness, 100 titik tetap, wasit | Sofi memimpin, Elsa membantu | #7 | 45 sampai 90 menit |
| 12 | Docker HDFS dan Spark | Levi | #10 | 45 sampai 90 menit |

### Fase 3. Muat S1

| # | Langkah | Siapa | Menunggu | Perkiraan waktu |
|---|---|---|---|---|
| 13 | Muat S1 ke MongoDB, indeks, W3 | Elsa memimpin, Sofi membantu | #8 dan #9 | 30 sampai 45 menit |
| 14 | Muat S1 ke PostGIS, indeks, W3 | Levi | #8 dan #10 | 30 sampai 45 menit |
| 15 | Parquet S1 di HDFS dan W3 Spark SQL | Levi memimpin, Syuep mendampingi | #8 dan #12 | 45 sampai 60 menit |
| 16 | S10 dan S100, `CHECKSUMS.txt`, ukuran di kamus data | Syuep | #8 | 1 sampai 2 jam (sebagian besar menunggu) |
| 17 | Harness W3 di ketiganya dan banding jumlah hasil | Sofi memimpin, Elsa membantu; Levi mengirim CSV-nya | #11, #13, #14, #15 | 45 sampai 60 menit |
| 18 | **SINKRON 1** (panggilan grup) | Semua | #17 | 30 sampai 45 menit |

### Fase 4. Pitching

Fase ini **tidak butuh** fase 2 dan 3. Bila jadwal pitching dekat, kerjakan fase 4 lebih dulu (setelah #7), lalu kembali ke fase 2 dan 3.

| # | Langkah | Siapa | Menunggu | Perkiraan waktu |
|---|---|---|---|---|
| 19 | Baca dokumen rancangan | Semua | #7 | 45 menit |
| 20 | Kirim bahan slide ke Wildan | Syuep, Elsa, Levi, Sofi | #19 | 30 menit |
| 21 | Diagram arsitektur di draw.io | Wildan | #19 | 1 sampai 2 jam |
| 22 | Susun slide pitching (6 slide) | Wildan | #20 dan #21 | 2 sampai 3 jam |
| 23 | Tinjau silang | Semua | #22 | 45 menit |
| 24 | Latihan pitching (**SINKRON 2**) | Semua | #23 | 45 sampai 60 menit |

### Fase 5. Skala dan uji

| # | Langkah | Siapa | Menunggu | Perkiraan waktu |
|---|---|---|---|---|
| 25 | Kueri W1 sampai W6 benar di S1 di ketiganya | Elsa, Sofi, Levi | #18 | 2 sampai 3 jam |
| 26 | Muat S10, lalu S100, di ketiganya | Elsa, Sofi, Levi, Syuep | #16 dan #25 | 3 sampai 6 jam (belum terukur) |
| 27 | Jalankan W1 sampai W8 (dan E1, E2) | Sofi memimpin, Elsa membantu | #26 | 3 sampai 6 jam (belum terukur) |
| 28 | Uji silang jumlah hasil di S100 | Sofi memimpin, Elsa membantu | #27 | 1 jam |

### Fase 6. Analisis

| # | Langkah | Siapa | Menunggu | Perkiraan waktu |
|---|---|---|---|---|
| 29 | Tabel, grafik, hipotesis H1 sampai H5 | Sofi memimpin, Elsa membantu | #28 | 2 sampai 3 jam |
| 30 | Laporan dan slide hasil | Wildan menyusun; semua menulis bagiannya | #29 | 3 sampai 4 jam |
| 31 | QA akhir dan kumpul di SIDIA | Semua; Wildan mengumpulkan | #30 | 1 sampai 2 jam |

> Perkiraan waktu untuk #26 dan #27 sengaja diberi tanda "belum terukur": waktu muat dan kueri pada S10 dan S100 baru
> kita ketahui saat menjalankannya (itulah isi pengukuran W7). Mulailah lebih awal dan biarkan laptop bekerja.

## Diagram ketergantungan (jalur kritis)

```text
#2 Wildan push ──┐
#3 alat ─────────┼─► #4 clone ─► #6 ─► #7 KICKOFF ─┬─► #8 Syuep: S1 ──┬─► #13 Elsa+Sofi: Mongo S1 ──┐
#5 spesifikasi ──┘                                  │                  ├─► #14 Levi: PostGIS S1 ─────┤
                                                    │                  ├─► #15 Levi+Syuep: Parquet ──┤
                                                    │                  └─► #16 Syuep: S10, S100      │
                                                    ├─► #9 Elsa+Sofi: Docker Mongo ──► #13           │
                                                    ├─► #10 Levi: Docker PostGIS ─┬─► #14            │
                                                    │                             └─► #12 ─► #15     │
                                                    ├─► #11 Sofi+Elsa: harness, titik, wasit ────────┤
                                                    │                                                ▼
                                                    │                          #17 banding W3 ─► #18 SINKRON 1 ─► #25 ─► #26 ─► #27 ─► #28 ─► #29 ─► #30 ─► #31
                                                    └─► #19 baca dokumen ─► #20 bahan + #21 diagram ─► #22 slide ─► #23 ─► #24 SINKRON 2
```

**Jalur kritis** (yang paling menentukan jadwal): #2 → #4 → #7 → #8 → #13/#14/#15 → #17 → #18 → #25 → #26 → #27.
Bila kamu terlambat di salah satunya, **beri tahu grup sekarang**, jangan menunggu sampai ditanya.

## Alur Wildan: dari mengunduh ZIP sampai push (ringkasan)

Perintah lengkap dan contoh hasilnya ada di [PANDUAN_Wildan.md](PANDUAN_Wildan.md), bagian #2. Garis besarnya:

1. Unduh ZIP paket, taruh di `Downloads`.
2. Buka PowerShell di salinan repo (`git pull --rebase`; pastikan repo sudah kosong dan bersih).
3. Ekstrak ZIP ke folder repo (`Expand-Archive`).
4. Salin dua berkas data mentah (`inventories.zip`, `splits_aligned.json`) ke `data\raw\`.
5. `python data\cek_data.py --raw --tulis` (menulis `SHA256.txt`).
6. `python data\convert_inventory.py`, harus berakhir **`LOLOS: 17 pemeriksaan cocok`**. Kode lain = berhenti, `[BLOKIR]`.
7. `python data\cek_data.py --skala S1`, harus berakhir `SEMUA PEMERIKSAAN LULUS (18)`.
8. `python bench\make_points.py`, lalu `python bench\kebenaran.py --skala S1 --tulis`.
9. `python data\generate_scales.py --write-checksums` (menulis baris S1 di `CHECKSUMS.txt`).
10. `python tests\uji_semua.py`, harus berakhir `SEMUA UJI LULUS`.
11. `git status` (pastikan tidak ada `cek-sen12ls` dan tidak ada `data/out`), `git add .`, `git commit`, `git pull --rebase`, `git push`.
12. Periksa di GitHub, lalu tulis `[SELESAI] root: paket awal sudah di GitHub` di grup. Setelah itu semua orang bisa clone (#4).

## Acara kelompok

### Kickoff (#7), 30 menit, dipimpin Wildan

| Menit | Acara | Siapa |
|---|---|---|
| 0 sampai 3 | Pembukaan; pastikan semua bisa membuka repo | Wildan |
| 3 sampai 8 | Perkenalan peran: tiap orang menyebut peran, folder, dan tugas pertamanya (satu kalimat) | Semua bergantian |
| 8 sampai 13 | Laptop: tiap orang membacakan RAM dan disk kosong; pilih **laptop uji S100** | Semua; Wildan mencatat |
| 13 sampai 20 | Alur: urutan #8 sampai #17 dan siapa menunggu siapa | Wildan |
| 20 sampai 25 | Jadwal: batas kumpul SIDIA, jadwal pitching, jam Sinkron 1 dan 2, jam check-in malam | Wildan |
| 25 sampai 30 | Aturan komunikasi, tanya jawab, langkah pertama masing-masing | Semua |

Keputusan yang dicatat (Wildan menulisnya sebagai `[KEPUTUSAN]` dan men-pin pesannya):

| Keputusan | Catatan (isi saat kickoff) |
|---|---|
| Batas kumpul Tugas 2 di SIDIA | ................ |
| Jadwal pitching | ................ |
| Sinkron 1 (setelah #17) | ................ |
| Sinkron 2 = latihan pitching (#24) | ................ |
| Laptop uji S100 (RAM 16 GB atau lebih, disk kosong 25 GB atau lebih) | ................ |
| Jam check-in malam | ................ |

### Sinkron 1 (#18), 30 sampai 45 menit

| Menit | Acara | Siapa |
|---|---|---|
| 0 sampai 20 | Demo singkat (4 menit per orang): tunjukkan layar dan hasilnya | Syuep, Elsa dan Sofi, Levi |
| 20 sampai 28 | Banding jumlah hasil W3 dari ketiga penyimpanan dan wasit (hasil #17) | Sofi |
| 28 sampai 36 | Samakan istilah dan nama kolom; catat yang berubah | Wildan |
| 36 sampai 45 | Putuskan urutan berikutnya: lanjut #25, atau pitching (#19 sampai #24) dahulu bila jadwal pitching dekat | Wildan memutuskan |

### Sinkron 2 (#24), latihan pitching, 45 sampai 60 menit

Wildan menampilkan slide; tiap orang menyampaikan bagiannya (sekitar 2 menit); lainnya mencatat temuan dengan format
`[Tinjau]`. Latih juga jawaban untuk pertanyaan yang mungkin muncul (bank pertanyaan ada di [PANDUAN_Wildan.md](PANDUAN_Wildan.md), #24).

## Aturan komunikasi

Semua kabar di grup WhatsApp memakai tanda di awal pesan:

| Tanda | Kapan | Bentuk |
|---|---|---|
| `[SELESAI]` | langkah selesai | `[SELESAI] <folder>: <apa yang jadi>` |
| `[BLOKIR]` | macet lebih dari 1 jam | `[BLOKIR] <apa yang dicoba + pesan galat lengkap> @nama` |
| `[KEPUTUSAN]` | hal yang disepakati | `[KEPUTUSAN] <keputusan>` (Wildan men-pin) |
| `[Tinjau]` | temuan saat tinjau silang | `[Tinjau] @nama - <bagian> - <temuan> - Saran: <perbaikan>` |

**Check-in malam** (satu pesan singkat per orang): `Hari ini: ... / Besok: ... / Kendala: ...`

## Aturan kerja bersama

1. **Satu penyimpanan aktif sekali waktu** di satu laptop (matikan yang lain dengan `docker compose stop`).
2. Ubah **hanya foldermu**. `results/` boleh diisi siapa pun yang menjalankan uji; Sofi yang mengelola isinya.
3. Commit kecil dan sering, pesan diawali `[folder]`. Jangan `--force`. Jangan menaruh sandi atau data pribadi di repo.
4. `data/out/` (berkas data besar) **tidak di-commit**; tiap orang membuat sendiri dari `data/raw/` dengan skrip yang sama,
   lalu `python data\generate_scales.py --verify` membuktikan isinya sama (checksum).
5. Setiap angka di laporan harus punya sumber: berkas hasil di `results/` atau `data/`. Klaim kinerja yang belum diukur
   ditulis sebagai **hipotesis**.
6. Menyimpang dari KONTRAK? Berhenti dan tulis `[KEPUTUSAN]` atau `[BLOKIR]`; jangan menyimpang diam-diam.

## Hasil per tugas

| Tugas | Isi | Bukti |
|---|---|---|
| **Tugas 2** (pitching) | rancangan, profil dan skala data, S1 termuat di tiga penyimpanan, W3 berjalan dan jumlahnya cocok antar penyimpanan, slide | #17 dan #18 selesai; slide dari #22; latihan #24 |
| **Tugas Tengah Semester** | S10 dan S100, W1 sampai W8 (dan E1, E2), analisis H1 sampai H5, laporan | `results/*.csv`, `results/ringkasan.csv`, `results/banding.csv`, laporan di `docs/` |

W9 (beban campuran baca-tulis) dan W10 (uji kegagalan) **belum ada skripnya**; keduanya termasuk Tugas Tengah Semester dan
ditulis sebagai rencana di laporan sampai skripnya dibuat.
