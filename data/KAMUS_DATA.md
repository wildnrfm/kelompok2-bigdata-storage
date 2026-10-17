# Kamus data Sen12Landslides (katalog metadata)

Pemilik: Syuep (folder `data/`). Sumber tunggal nama dan tipe kolom: `baca-dulu/KONTRAK.md` bagian 3.
Angka profil berasal dari berkas asli yang diperiksa Wildan pada 22 Okt 2026 (`laporan_inventaris.txt`).

## 1. Apa yang disimpan

Dataset: **Sen12Landslides** (Höhn, Heidler, Behling & Zhu), Scientific Data 12:1772, DOI dataset
`10.57967/hf/5883`, lisensi **CC BY 4.0** (wajib disebut di laporan, slide, dan README).

| | Dipakai | Tidak dipakai |
|---|---|---|
| Berkas | `inventories.zip` (poligon longsor) dan `splits_aligned.json` (daftar patch citra) | citra NetCDF (170,5 GB) |
| Isi | 74.956 anotasi dan 4.392 entri patch | piksel citra |

Kami membuat **katalog metadata**: tiap anotasi diwakili atribut, **titik pusat** (centroid berbobot luas)
dan **kotak pembatas** (bbox). **Bentuk poligon tidak disimpan** (median sisi kotak hanya sekitar 54 m).
Pertanyaan katalog (di sekitar titik, di dalam kotak area, pada rentang tanggal) cukup dijawab dengan
titik dan kotak. Koordinat dibulatkan ke 7 desimal (sekitar 1 cm).

Peringatan jujur tentang sumber:

- `.prj` berisi GCS_WGS_1984 tanpa kode EPSG; kami memakai **EPSG:4326** (dugaan yang sangat wajar, bukan fakta tertulis).
- Arti `pre_dt2`, `event_dt2`, `post_dt2` tidak dijelaskan README maupun artikel; disimpan apa adanya.
- Satuan `area` tidak dinyatakan (nilai 0,88 sampai 7,46 juta; diduga m²).
- `velocity_c` selalu `>=5`; `reference` terpotong 50 karakter di berkas asli.
- JSON patch tidak memuat koordinat maupun ID anotasi, jadi hubungan anotasi dan patch hanya per
  inventaris (bukan per anotasi).

## 2. Tabel `annotations` (74.956 baris di S1)

Urutan kolom di CSV sama persis dengan tabel ini. Kosong = tidak ada nilai: sel kosong di CSV,
**field tidak ditulis** di NDJSON (MongoDB), `NULL` di PostGIS dan Parquet.

| # | Kolom CSV | Asal | PostGIS | Parquet | Di dokumen MongoDB | Catatan |
|---|---|---|---|---|---|---|
| 1 | `ann_id` | `id` asli | `bigint` PK | long | `_id` | 0 sampai 74.955 di S1; unik |
| 2 | `location` | `location` | `text` | string | `location` | 16 nilai (Italy, DominicaMaria, ...) |
| 3 | `inventory` | dari `location` | `text`, boleh kosong | string | `inventory` | nama `location` huruf kecil (`USA_*` menjadi `usa`); kosong untuk 4 lokasi tanpa patch (DominicaMaria, LanaoDelNorte, Thrissur, Nepal: 11.260 anotasi) |
| 4 | `event_type` | `event_type` | `text` | string | `event_type` | 5 nilai; 3.142 kosong |
| 5 | `type` | `type` | `text` | string | `type` | Debris flow (74.853) atau Ice avalanche (103) |
| 6 | `velocity_c` | `velocity_c` | `text` | string | `velocity_c` | selalu `>=5` |
| 7 | `author` | `author` | `text` | string | `author` | 5 nilai |
| 8 | `reference` | `reference` | `text` | string | `reference` | terpotong 50 karakter |
| 9 | `event_conf` | `event_conf` | `double precision` | double | `event_conf` | 0 sampai 1; keyakinan atas tanggal kejadian |
| 10 | `area` | `area` | `double precision` | double | `area` | satuan tidak dinyatakan |
| 11 | `pre_date` | `pre_date` | `date` | date | `dates.pre` | tanggal pra-kejadian, boleh kosong |
| 12 | `event_date` | `event_date` | `date` | date | `dates.event` | tanggal kejadian; 2016-04-01 sampai 2023-05-16 |
| 13 | `post_date` | `post_date` | `date` | date | `dates.post` | tanggal pasca-kejadian |
| 14 | `pre_dt2` | `pre_dt2` | `date` | date | `dates.pre2` | arti tidak dijelaskan sumber |
| 15 | `event_dt2` | `event_dt2` | `date` | date | `dates.event2` | idem |
| 16 | `post_dt2` | `post_dt2` | `date` | date | `dates.post2` | idem |
| 17 | `center_lon` | dihitung | `center` titik | double | `center.coordinates[0]` | bujur titik pusat, derajat |
| 18 | `center_lat` | dihitung | (bagian `center`) | double | `center.coordinates[1]` | lintang titik pusat |
| 19 | `bbox_min_lon` | header `.shp` | `bbox` poligon | double | `bbox` (Polygon) | kotak pembatas |
| 20 | `bbox_min_lat` | header `.shp` | (bagian `bbox`) | double | | |
| 21 | `bbox_max_lon` | header `.shp` | (bagian `bbox`) | double | | |
| 22 | `bbox_max_lat` | header `.shp` | (bagian `bbox`) | double | | |
| 23 | `sim_batch` | simulasi | `smallint` | int | `sim_batch` | 0 = data asli; 1 sampai 99 = salinan |

Tanggal ditulis `YYYY-MM-DD` di CSV dan `{"$date": "YYYY-MM-DDT00:00:00.000Z"}` di NDJSON.
109 anotasi tidak punya satu pun tanggal.

Di PostGIS kolom 17 sampai 22 dipadatkan menjadi dua kolom geometri: `center geometry(Point,4326)` dan
`bbox geometry(Polygon,4326)` (`postgis/load.sql` yang membuatnya dengan `ST_MakePoint` dan `ST_MakeEnvelope`).
Di Parquet keenam kolom tetap datar supaya Spark SQL bisa menyaring dengan perbandingan biasa.

Contoh BENTUK satu dokumen MongoDB (nilai hanya ilustrasi, bukan baris asli):

```json
{"_id":12345,"location":"Italy","inventory":"italy","event_type":"Rainfall","type":"Debris flow",
 "velocity_c":">=5","author":"Ferrario","reference":"https://zenodo.org/records/8102429",
 "event_conf":0.95,"area":412.3,
 "dates":{"pre":{"$date":"2019-03-02T00:00:00.000Z"},"event":{"$date":"2019-03-15T00:00:00.000Z"},
          "post":{"$date":"2019-03-20T00:00:00.000Z"}},
 "center":{"type":"Point","coordinates":[11.4548681,43.7734078]},
 "bbox":{"type":"Polygon","coordinates":[[[11.4547,43.7733],[11.4549,43.7733],[11.4549,43.7735],[11.4547,43.7735],[11.4547,43.7733]]]},
 "sim_batch":0}
```

## 3. Tabel `patches` (4.392 baris di S1)

| # | Kolom CSV | Asal | PostGIS | Parquet | Di dokumen MongoDB | Catatan |
|---|---|---|---|---|---|---|
| 1 | `patch_id` | `id` | `text` PK | string | `_id` | contoh `chimanimani_1004`; akhiran `_r<b>` untuk salinan b >= 1 |
| 2 | `split` | kunci tingkat atas JSON | `text` | string | `split` | train (2.810), val (703), test (879) |
| 3 | `inventory` | `inventory` | `text` | string | `inventory` | 11 nilai huruf kecil |
| 4 | `s2_path` | `s2` | `text` | string | `paths.s2` | jalur relatif NetCDF; berkasnya tidak disimpan |
| 5 | `s1asc_path` | `s1asc` | `text` | string | `paths.s1asc` | idem |
| 6 | `s1dsc_path` | `s1dsc` | `text` | string | `paths.s1dsc` | idem |
| 7 | `pixel_annotated` | `pixel_annotated` | `integer` | int | `pixel_annotated` | 50 sampai 8.911, rata-rata sekitar 613 |
| 8 | `sim_batch` | simulasi | `smallint` | int | `sim_batch` | 0 = data asli |

## 4. Sebaran data asli (S1)

Sebarannya sangat miring: Italy dan DominicaMaria saja 77% dari anotasi. Simulasi mempertahankannya,
jadi kueri dengan selektivitas sangat berbeda (Italy lawan Nepal) bisa diuji.

| `location` | Anotasi | `event_type` | Anotasi | `author` | Anotasi |
|---|---|---|---|---|---|
| Italy | 47.522 | Rainfall | 52.686 | Ferrario | 47.522 |
| DominicaMaria | 10.172 | Hurricane | 10.172 | Höhn | 16.306 |
| Newzealand | 3.242 | Earthquake | 7.950 | Emberson | 10.619 |
| Chimanimani | 2.513 | Tropical Storm | 640 | Belair | 328 |
| Kyrgyzstan1 | 2.405 | Cyclone | 366 | Kirschbaum | 181 |
| Hokkaido | 2.340 | (kosong) | 3.142 | | |
| Hiroshima | 2.211 | | | | |
| Indonesia | 2.097 | | | | |
| LanaoDelNorte | 640 | | | | |
| Kyrgyzstan2 | 513 | | | | |
| Thrissur | 440 | | | | |
| Itogon | 366 | | | | |
| USA_PuertoRico | 263 | | | | |
| China | 121 | | | | |
| USA_Alaska | 103 | | | | |
| Nepal | 8 | | | | |

Patch per inventaris: italy 1.799, kyrgyzstan1 694, newzealand 508, chimanimani 345, hiroshima 322,
indonesia 253, kyrgyzstan2 170, hokkaido 144, itogon 82, china 47, usa 28 (jumlah 4.392).

## 5. Skala dan simulasi

Skala dibuat lewat simulasi dari data asli dan **bersarang**: S1 ada di S10, S10 ada di S100
(berkas yang lebih kecil adalah **awalan byte** berkas yang lebih besar).

| Skala | Anotasi | Patch | CSV anotasi | NDJSON anotasi | Total keempat berkas |
|---|---|---|---|---|---|
| S1 (data asli) | 74.956 | 4.392 | 19,5 MB | 56,9 MB | 77,9 MB |
| S10 | 749.560 | 43.920 | 196 MB | 570 MB | 781 MB |
| S100 | 7.495.600 | 439.200 | 1,97 GB | 5,72 GB | 7,84 GB |

Ukuran di atas diukur pada data tiruan berbentuk persis laporan asli (jumlah baris, panjang teks,
sebaran lokasi sama); pada data asli angkanya bisa berbeda beberapa persen. Ukuran di dalam MongoDB,
PostGIS, dan Parquet berbeda dan baru diketahui setelah diukur (`python bench/catat.py ukuran ...`).
Laptop yang memuat S100 perlu **minimal 25 GB disk kosong**: 7,84 GB berkas data, ditambah isi basis data
dan indeksnya (perkiraan beberapa GB per penyimpanan), ditambah ruang kerja Docker. Hapus S100 dari satu
penyimpanan (`docker compose down -v`) sebelum memuat penyimpanan berikutnya bila disk sempit.

Aturan simulasi (seed tetap **20261023**; jangan diubah, checksum tidak akan cocok):

1. **Batch 0 adalah data asli.** Batch b (b = 1 sampai 99) memakai pembangkit acak sendiri (seed + b).
2. **Disalin apa adanya:** `location`, `inventory`, `event_type`, `type`, `velocity_c`, `author`,
   `reference`, `event_conf`, `area`. Sebaran miring dan nilai kosong ikut terjaga.
3. **Tanggal digeser:** keenam tanggal digeser dengan jumlah hari acak yang **sama** (-365 sampai +365),
   jadi selisih antar tanggal tetap; anotasi tanpa tanggal tetap tanpa tanggal.
4. **Lokasi digeser:** titik pusat dan kotak digeser dengan selisih bujur dan lintang acak yang sama
   (maksimal 0,25 derajat, sekitar 28 km), dibatasi agar kotak tetap di bujur ±179 dan lintang ±85.
   Ukuran kotak tidak berubah.
5. **Kunci:** `ann_id` = `id` asli + 74.956 x b, jadi berurutan dari 0 sampai 7.495.599 di S100;
   `sim_batch` = b. Patch: `patch_id` diberi akhiran `_r<b>` untuk b >= 1; jalur citra tidak diubah.
6. **Pemeriksaan:** `python data/cek_data.py --skala S10` menghitung baris, keunikan kunci, sebaran
   (harus kelipatan tepat dari data asli), dan kesamaan NDJSON dengan CSV baris demi baris.

**Peringatan:** data simulasi hanya untuk uji beban. Jangan dilaporkan sebagai kejadian longsor.

Batch tambahan untuk beban kerja W8 (`python data/generate_scales.py --extra-batch 100`) memakai aturan
yang sama dengan b = 100; hasilnya di `data/out/batch100/` (74.956 anotasi dengan `ann_id` 7.495.600
sampai 7.570.555).

## 6. Pemeriksaan keutuhan

- Berkas asli: `data/raw/SHA256.txt` (dibuat Wildan sekali). Cek: `python data/cek_data.py --raw`.
- S10 dan S100: `data/CHECKSUMS.txt` (SHA-256 berkas hasil). Cek:
  `python data/generate_scales.py --verify`. Bila tidak cocok, buat ulang; jangan memakai data yang tidak cocok.
- Hasil tiap skala: `python data/cek_data.py --skala S1` (juga S10 dan S100; S100 sekitar 3 sampai 6 menit).

## 7. Atribusi

Sebut **Höhn dkk. (2025), Scientific Data 12:1772, dataset DOI 10.57967/hf/5883, CC BY 4.0**. Inventaris
berasal dari lima publikasi asal; lisensi masing-masing tidak kami periksa satu per satu, jadi penulis asal ikut dikutip.

| Penulis inventaris asal | Anotasi | Nilai `reference` di berkas |
|---|---|---|
| Ferrario dkk. (2023) | 47.522 | `https://zenodo.org/records/8102429` |
| Höhn dkk. (2025) | 16.306 | `https://doi.org/10.57967/hf/5883` |
| Emberson dkk. (2022) | 10.619 | `https://doi.org/10.5194/nhess-22-1129-20` (terpotong) |
| Belair dkk. (2022) | 328 | `https://doi.org/10.5066/P9FZUX6N` |
| Kirschbaum dkk. (2010, 2015) | 181 | `https://catalog.data.gov/dataset/global-` (terpotong) |
