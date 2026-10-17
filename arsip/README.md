# Big Data Storage · KELOMPOK 2

**Perancangan Konsep Arsitektur Penyimpanan dan Pemilihan Data** (Tugas 2)
Dataset: SEN12TP (metadata) · MongoDB dan PostgreSQL/PostGIS, dibandingkan dengan baseline HDFS + Parquet

Tim dan pembagian peran: [TEAM.md](TEAM.md). Kabar dan diskusi lewat grup WhatsApp; kode, kueri, dan hasil uji lewat repo ini.

## Gambaran singkat

Kami menyimpan katalog metadata scene citra satelit SEN12TP (2.319 scene, tiap scene berupa poligon bujur–lintang) di tiga penyimpanan, lalu membandingkan kinerjanya pada sepuluh beban kerja (W1–W10) di skala 1× sampai 1.000×.

| Penyimpanan | Bentuk data | Indeks spasial | Folder |
|---|---|---|---|
| MongoDB | dokumen GeoJSON, indeks `2dsphere` | ya | `mongodb/` |
| PostgreSQL/PostGIS | tabel `scenes`, kolom `geometry(Polygon,4326)`, indeks GiST | ya | `postgis/` |
| HDFS + Parquet (Spark SQL) | baseline: berkas kolom ZSTD dengan kolom bbox | tidak | `hdfs-parquet/` |

Ketiganya dimuat dari sampel dan seed yang sama, dan diukur oleh satu harness (`bench/harness.py`).

## Dataset

**SEN12TP - Sentinel-1 and -2 images, timely paired** (Roßberg & Schmitt, 2023), Zenodo, lisensi CC BY 4.0.
Halaman: <https://zenodo.org/records/7342060> · DOI: <https://doi.org/10.5281/zenodo.7342060>

Yang dipakai hanya berkas metadata `sen12tp-metadata.json` (1,3 MB). Citranya (± 222 GB tanpa kompresi) tidak diunduh dan tidak masuk database; katalog hanya menyimpan metadata dan penunjuk ke Zenodo. Entri di daftar dosen memuat dua dataset; kelompok kami memakai SEN12TP saja.

| Aspek | Nilai |
|---|---|
| Bentuk | GeoJSON FeatureCollection, CRS84 (bujur–lintang WGS 84); 2.319 Feature, semuanya Polygon |
| Isi | 2.319 scene unik (`scene_id`) dari 1.236 area kajian (`spatial_id`), Maret 2017 sampai Desember 2020 |
| Kualitas | 9 atribut, 0 nilai kosong |
| MD5 | `ee86bf2caa4d8ec7d2bd67163a4396e7` (cocok dengan Zenodo) |
| Lokasi di repo | `data/raw/sen12tp-metadata.json`, dan `data/raw/profil.py` untuk memprofil berkas |

Atribut inti:

| Atribut | Tipe | Keterangan |
|---|---|---|
| `scene_id` | integer | kunci utama; lookup (W1) |
| `spatial_id` | integer | area kajian (1.236 nilai unik) |
| `split` | teks | `train` 2.095, `test` 224 |
| `climate` | teks, 14 kelas | filter dan agregasi (W5, W6) |
| `landcover` | teks, 8 kelas | filter gabungan spasial dan atribut (W4), agregasi (W5) |
| `s1_timestamp_ms`, `s2_timestamp_ms` | integer, milidetik epoch | waktu Sentinel-1 dan Sentinel-2; diubah menjadi `s1_time` dan `s2_time` |
| `utm_epsg` | teks | zona UTM scene, contoh `EPSG:32719` |
| `month` | integer 1–12 | filter bulan (W3), agregasi (W6) |
| geometri | Polygon | indeks spasial (W2–W4) dan kolom bbox untuk Parquet |

**Atribusi** (cantumkan di laporan dan slide): SEN12TP - Sentinel-1 and -2 images, timely paired. Roßberg & Schmitt (2023). Zenodo. https://doi.org/10.5281/zenodo.7342060. Lisensi CC BY 4.0.

## Skala data

| Skala | Isi | Perkiraan record | Perkiraan berkas mentah | Lokasi |
|---|---|---|---|---|
| S1 | seluruh 2.319 scene asli | 2.319 | 1,3 MB | `data/s1/` (di-commit) |
| S10 | S1 + record simulasi | ± 23 ribu | ± 12,6 MB | `data/out/` (tidak di-commit) |
| S100 | S10 + record simulasi | ± 232 ribu | ± 126 MB | `data/out/` (tidak di-commit) |
| S1000 | S100 + record simulasi | ± 2,3 juta | ± 1,3 GB | `data/out/` (tidak di-commit) |

- Sampel bersarang (S1 ⊂ S10 ⊂ S100 ⊂ S1000) dengan seed tetap, jadi hasil antar skala bisa dibandingkan dan diulang.
- S10 sampai S1000 dibuat ulang dari generator dan seed di laptop masing-masing, lalu dicocokkan dengan `CHECKSUMS.txt` di folder `data/`. Data besar tidak masuk GitHub karena GitHub menolak berkas di atas 100 MB.
- Kecil dulu, besar kemudian: semuanya harus berjalan benar di S1 sebelum naik ke S10, S100, dan S1000.
- Keterbatasan: data simulasi tidak mempertahankan hubungan antara tutupan lahan atau iklim dan lokasi. Cukup untuk menguji kinerja penyimpanan, tidak untuk analisis ilmiah.

## Struktur repo

```
kelompok2-bigdata-storage/
├─ README.md        status dan cara menjalankan                  (Wildan)
├─ TEAM.md          nama, NIM, peran, username GitHub            (semua)
├─ .gitignore       data/out/, .env, __pycache__/
├─ baca-dulu/      3 PDF wajib dibaca sebelum mulai              (semua)
├─ data/            raw/ asli · s1/ siap muat · out/ S10–S1000 (tidak di-commit)
│                   · generator, CHECKSUMS.txt, kamus data       (Syuep)
├─ mongodb/         compose, indeks, muat, kueri W1–W6           (Elsa, Sofi)
├─ postgis/         schema.sql, muat, kueri W2–W6 dan W8         (Levi)
├─ hdfs-parquet/    compose HDFS + Spark, Spark SQL              (Levi, Syuep)
├─ bench/           harness.py, daftar beban kerja W1–W10        (Sofi, Elsa)
├─ results/         CSV hasil uji dan grafik                     (Sofi, Elsa)
└─ docs/            diagram, laporan, slide                      (Wildan)
```

## Cara mulai

Siapkan Git (atau GitHub Desktop), Python 3.11 atau lebih baru, dan Docker Desktop. Di Windows, Docker Desktop memakai WSL2; bila RAM laptop 12 GB atau kurang, batasi memorinya lewat `.wslconfig` (misalnya `memory=6GB`).

```
git clone https://github.com/wildnrfm/kelompok2-bigdata-storage.git
cd kelompok2-bigdata-storage
```

Repo ini privat. Bila clone ditolak, periksa dulu bahwa undangan collaborator sudah diterima (email, atau <https://github.com/notifications>).

Baca dulu tiga berkas ini di folder `baca-dulu/` sebelum mulai kerja:

1. Penjelasan Tugas 2 — MongoDB + PostGIS vs HDFS-Parquet
2. Panduan Kerja Kelompok — peran, alur, dan aturan
3. Alur Kerja Berurutan — langkah bernomor per orang

Laptop terbatas: jalankan satu penyimpanan pada satu waktu (`docker compose up` di satu folder, `docker compose down` sebelum pindah ke folder lain). HDFS dan Spark paling berat.

## Aturan kerja

1. **Satu orang, satu folder.** Ubah hanya folder perannya sendiri (lihat [TEAM.md](TEAM.md)). Dua orang di satu folder: bagi per berkas, atau kabari dulu sebelum mengubah berkas yang sama.
2. **Alur harian:**

   ```
   git pull --rebase                # mulai kerja: ambil perubahan terbaru
   git add mongodb/                 # selesai: tambahkan folder sendiri
   git commit -m "[mongodb] tambah indeks 2dsphere"
   git pull --rebase                # ambil lagi bila ada yang baru
   git push
   ```

3. **Pesan commit diawali nama folder** dalam kurung siku: `[mongodb] ...`, `[postgis] ...`, `[data] ...`. Untuk berkas di akar repo (`README.md`, `TEAM.md`) pakai `[root]`.
4. **Push ditolak?** Jalankan `git pull --rebase`, lalu push lagi. Jangan memakai `--force`. Masih gagal: tulis `[BLOKIR]` di grup.
5. **Konflik saat `git pull --rebase`?** Buka berkas yang disebut, simpan kedua versi, hapus baris `<<<<<<<`, `=======`, dan `>>>>>>>`, lalu `git add <berkas>`, `git rebase --continue`, dan `git push`. Ragu: tulis `[BLOKIR]` di grup, jangan menimpa pekerjaan orang lain.
6. **Tidak masuk repo:** data besar (S10 sampai S1000, Parquet hasil muat), password, dan berkas `.env`. Slide dan laporan final, juga berkas besar yang tidak bisa dibuat ulang, taruh di folder Google Drive kelompok.
7. **Belum bisa Git?** Pakai GitHub Desktop, atau kirim berkas ke Wildan lewat grup dan Wildan yang memasukkannya (tulis namamu di pesan commit).
8. **Pengumpulan ke dosen:** hanya Wildan yang mengisi Sheet dosen, supaya sel kelompok lain tidak tertimpa. Klik dua kali sel tujuan sampai kursor ada di dalam sel, baru tempel.

## Kabar di grup WhatsApp

| Tanda | Dipakai bila | Contoh |
|---|---|---|
| `[SELESAI]` | hasil siap dipakai orang lain | `[SELESAI] data/: S1 siap muat di repo. @Elsa @Sofi @Levi silakan muat.` |
| `[BLOKIR]` | macet lebih dari 1 jam | `[BLOKIR] mongoimport menolak geometri; urutan koordinat sudah dicoba. @Syuep tolong cek berkas S1.` |
| `[KEPUTUSAN]` | hal yang sudah disepakati | `[KEPUTUSAN] Uji S1000 di laptop Levi, satu penyimpanan sekali waktu.` |

Balas pesan yang menyebut namamu dalam 24 jam; cukup "oke, dilihat". Wildan merangkum semua `[KEPUTUSAN]` di pesan yang di-pin. Check-in tiap malam, tiga baris dan boleh singkat: "Hari ini: … / Besok: … / Kendala: …".

## Rencana uji

Pelaksanaan di Tugas Tengah Semester; untuk Tugas 2 baru rancangannya. Rinciannya, termasuk eksperimen E1–E4 dan hipotesis H1–H4, ada di dokumen rancangan.

| Kode | Beban kerja | Diuji pada | Metrik |
|---|---|---|---|
| W1 | Cari satu scene per `scene_id`; konkurensi 1, 10, 50, 100 | MongoDB, PostGIS, Spark SQL (satu klien) | p50, p95, p99, QPS, error |
| W2 | Scene yang menutupi satu titik (titik-dalam-poligon), 100 titik tetap | ketiganya | p50, p95, jumlah hasil |
| W3 | Scene yang menutupi satu titik pada satu bulan (spasial-temporal) | ketiganya | p50, p95, jumlah hasil |
| W4 | Scene yang beririsan dengan kotak area (kecil dan besar), difilter `landcover` (kelas jarang dan umum) | ketiganya | p50, p95, jumlah hasil |
| W5 | Jumlah scene per `landcover`, dan per `climate` × `landcover` | ketiganya | waktu kueri |
| W6 | Jumlah scene per bulan dan `climate` | ketiganya | waktu kueri |
| W7 | Muat massal S1, S10, S100, S1000, bangun indeks, dan ukuran penyimpanan | ketiganya | waktu muat, waktu bangun indeks, GB di disk |
| W8 | Tambah satu batch scene baru (inkremental) | ketiganya | waktu tambah, record per detik |
| W9 | Beban campuran: 90% baca (W1, W2, W3) dan 10% tulis, 5 menit, konkurensi 50 | MongoDB, PostGIS | p95 baca saat ada penulisan |
| W10 | Uji kegagalan: matikan primary MongoDB, satu DataNode HDFS, dan (opsional) promosikan standby PostgreSQL | masing-masing | waktu pulih, error, data hilang |

Aturan pengukuran:

- Tiap pengukuran diulang minimal 3 kali; laporkan median dan rentangnya.
- Cold = sesaat setelah container dinyalakan ulang; warm = setelah satu kali pemanasan.
- Adil: sampel dan seed sama untuk ketiga penyimpanan; W1–W4 memakai daftar tetap ID dan titik; memori tiap container dibatasi.
- Terisolasi: satu penyimpanan aktif pada satu waktu.
- Tercatat: versi perangkat lunak, spesifikasi laptop, dan konfigurasi tiap layanan.
- Uji silang: jumlah scene hasil W2–W4 dibandingkan antar penyimpanan. Selisih tipis di tepi poligon (MongoDB memakai bola, PostGIS memakai bidang datar) dicatat, bukan dianggap galat.

Format hasil: satu CSV per percobaan di `results/`, misalnya `20261020_mongodb_W3_S1000.csv` (tanggal, penyimpanan, beban, skala). Kolom (usulan; Sofi dan Elsa menetapkannya di Hari 1):

```
penyimpanan, beban_kerja, skala, ulangan, cold_warm, waktu_ms, jumlah_hasil, catatan
```

## Status

Wildan memperbarui daftar ini setelah ada `[SELESAI]` di grup.

- [ ] Repo, `README.md`, `TEAM.md`, dan `data/raw/` (Wildan)
- [ ] Semua anggota sudah clone dan mengisi username di `TEAM.md`
- [ ] Kickoff: peran, batas kumpul, jadwal pitching, jam Sinkron 1 dan 2
- [ ] S1 siap muat di `data/s1/`: NDJSON, CSV dengan WKT, Parquet dengan kolom bbox (Syuep)
- [ ] MongoDB: Docker jalan, S1 termuat, indeks dibuat, W3 jalan (Elsa, Sofi)
- [ ] PostGIS: Docker jalan, S1 termuat, indeks dibuat, W3 jalan (Levi)
- [ ] HDFS + Spark: Parquet S1 termuat, W3 jalan (Levi, Syuep)
- [ ] Generator S10–S1000 dan `CHECKSUMS.txt` (Syuep)
- [ ] `bench/harness.py` mengukur satu kueri di ketiga penyimpanan (Sofi, Elsa)
- [ ] Sinkron 1
- [ ] Diagram arsitektur final dan slide pitching (Wildan)
- [ ] Sinkron 2 (latihan pitching)
- [ ] Tugas 2 dikumpulkan sesuai batas SIDIA (Wildan)
- [ ] Tugas Tengah Semester: muat S10, S100, S1000; jalankan W1–W10; analisis dan laporan

## Rujukan

- Dataset: <https://zenodo.org/records/7342060>
- Makalah terkait menurut Zenodo: "A globally applicable method for NDVI estimation from Sentinel-1 SAR backscatter using a deep neural network and the SEN12TP dataset", PFG 2023, doi 10.1007/s41064-023-00238-y
