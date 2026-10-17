# Tim KELOMPOK 2

Big Data Storage · SEN12TP: MongoDB + PostgreSQL/PostGIS vs HDFS–Parquet

Project Lead: Wildan. Kabar dan diskusi lewat grup WhatsApp; kode, kueri, dan hasil uji lewat repo ini. Aturan kerja ada di [README.md](README.md).

## Anggota

| No. di dokumen | Panggilan | Nama lengkap | NIM | Peran |
|---|---|---|---|---|
| 1 | Wildan | Muhammad Wildan Arif Maulana | 23051204065 | Project Lead + Documentation/QA |
| 2 | Syuep | Maulana Hidayah Syaif Ali Khan | 23051204068 | Data Collection Engineer |
| 3 dan 5 | Elsa | Elsa Claudia Putri | 23051204038 | Storage Engineer A (MongoDB), memimpin; Performance Analyst, membantu |
| 5 dan 3 | Sofi | Marsanda Sofi Aminarti | 23051204066 | Performance Analyst, memimpin; Storage Engineer A (MongoDB), membantu |
| 4 | Levi | Muhammad Syah Levi | 23051204051 | Storage Engineer B (PostgreSQL/PostGIS + baseline HDFS–Parquet) |

"No. di dokumen" mengacu pada Anggota 1–5 di bagian Pembagian tugas pada dokumen rancangan.

## Username GitHub

Isi baris namamu sendiri dengan username GitHub-mu (tanpa @), lalu commit dan push:

```
git pull --rebase
git add TEAM.md
git commit -m "[root] isi username GitHub (nama-kamu)"
git pull --rebase
git push
```

Satu orang satu baris, dan tiap baris dipisah baris kosong supaya tidak bentrok saat beberapa orang push bersamaan. Jangan ubah baris orang lain, dan jangan menghapus baris kosongnya.

- Wildan: wildnrfm

- Syuep: Syaifalikhan

- Elsa: ElsaCP

- Sofi: marsandasofi

- Levi: SyahLev

## Peran, tugas utama, dan folder

| Peran | PIC | Tugas utama | Folder |
|---|---|---|---|
| Project Lead + Documentation/QA | Wildan | Koordinasi dan jadwal, isian Sheet dosen, diagram arsitektur final, QA lintas bagian, slide pitching, laporan | `docs/` |
| Data Collection Engineer | Syuep | Konversi S1, generator S10–S1000 (seed tetap), kamus data, `CHECKSUMS.txt` | `data/` |
| Storage Engineer A (MongoDB) | Elsa, Sofi | Docker MongoDB (replica set), skema dan indeks `2dsphere`, muat massal, kueri W1–W6 | `mongodb/` |
| Storage Engineer B (PostgreSQL/PostGIS + baseline HDFS–Parquet) | Levi | DDL PostGIS dan indeks GiST, muat dengan `COPY`, HDFS + Spark, Spark SQL, kueri W2–W6 dan W8 | `postgis/`, `hdfs-parquet/` |
| Performance Analyst | Sofi, Elsa | Harness uji (Python), beban kerja W1–W10, tabel dan grafik hasil, uji silang jumlah hasil | `bench/`, `results/` |

Satu orang, satu folder: ubah hanya folder perannya sendiri. Di akar repo, `README.md` hanya diubah Wildan, dan di `TEAM.md` tiap orang hanya mengisi baris username-nya sendiri.

## Catatan pembagian

- Dua orang pada satu peran: nama pertama memimpin, yang kedua membantu dan meninjau (usulan, boleh ditukar). Elsa dan Sofi memegang dua peran sekaligus, jadi bagi per berkas agar tidak saling menimpa.
- Beban Levi paling berat: dua penyimpanan, dan HDFS + Spark paling banyak memakan memori. Usulan: begitu konversi dan generator selesai, Syuep membantu bagian HDFS–Parquet (konversi Parquet dan draf Spark SQL).
- Tinjau silang: Elsa/Sofi dan Levi saling memeriksa justifikasi dan kueri; Syuep dan Sofi/Elsa saling memeriksa profil data dan rencana uji; Wildan menutup dengan QA.
- Bila berbeda pendapat, Project Lead memutuskan. Perubahan peran disepakati di grup dengan tag `[KEPUTUSAN]`, lalu Wildan memperbarui berkas ini.
