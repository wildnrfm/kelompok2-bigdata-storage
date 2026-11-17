# -*- coding: utf-8 -*-
"""Kueri tahap pemrosesan dan analitik (dialek Spark SQL) serta aturan menulis hasilnya.

Dipakai bersama oleh:
  spark_pipeline.py  menjalankan kueri ini di Spark (di dalam kontainer sen12ls-spark)
  uji_sql.py         menjalankan kueri YANG SAMA di SQLite (fungsi_spark.py meniru fungsi Spark)
  referensi.py       menghitung hasil yang sama dengan Python murni, sebagai pembanding bebas

Tabel masukan (view): annotations dan patches (Parquet hasil csv_to_parquet.py).
Tahap pemrosesan (ETL) membentuk tabel turunan ann_kaya dari annotations (SQL_PERKAYA).
Tahap analitik menjalankan ANALISIS di atas ann_kaya (dan annotations/patches).

Aturan penulisan supaya hasil Spark dan hasil pembanding bisa dibandingkan:
  - semua kueri punya ORDER BY penuh (kelompok punya kunci unik, jadi urutan pasti)
  - NULL ditulis sebagai sel kosong; bilangan desimal ditulis dengan repr() Python (bulat-balik)
  - persentil memakai rumus percentile() Spark (interpolasi linear atas data eksak, bukan percentile_approx)

Hanya Python bawaan; cocok untuk Python 3.8 di dalam kontainer Spark.
"""
import csv
import datetime
import os

TABEL_KAYA = "ann_kaya"
TANPA_INVENTARIS = "(tanpa-inventaris)"
KOSONG = "(kosong)"

# Skema Parquet (nama, tipe). tests/uji_semua.py memeriksa daftar ini SAMA dengan
# KOLOM_ANOTASI dan KOLOM_PATCH di hdfs-parquet/csv_to_parquet.py.
SKEMA_ANOTASI = [
    ("ann_id", "long"), ("location", "string"), ("inventory", "string"), ("event_type", "string"),
    ("type", "string"), ("velocity_c", "string"), ("author", "string"), ("reference", "string"),
    ("event_conf", "double"), ("area", "double"),
    ("pre_date", "date"), ("event_date", "date"), ("post_date", "date"),
    ("pre_dt2", "date"), ("event_dt2", "date"), ("post_dt2", "date"),
    ("center_lon", "double"), ("center_lat", "double"),
    ("bbox_min_lon", "double"), ("bbox_min_lat", "double"),
    ("bbox_max_lon", "double"), ("bbox_max_lat", "double"), ("sim_batch", "int"),
]
SKEMA_PATCH = [
    ("patch_id", "string"), ("split", "string"), ("inventory", "string"), ("s2_path", "string"),
    ("s1asc_path", "string"), ("s1dsc_path", "string"), ("pixel_annotated", "int"), ("sim_batch", "int"),
]
# Kolom teks dianggap kosong bila NULL atau ""; kolom lain hanya bila NULL.
KOLOM_ANOTASI_TEKS = [n for n, t in SKEMA_ANOTASI if t == "string"]
KOLOM_ANOTASI_LAIN = [n for n, t in SKEMA_ANOTASI if t != "string"]
KOLOM_PATCH_TEKS = [n for n, t in SKEMA_PATCH if t == "string"]
KOLOM_PATCH_LAIN = [n for n, t in SKEMA_PATCH if t != "string"]

# ---------------------------------------------------------------------------------------------
# Tahap pemrosesan (ETL): annotations -> ann_kaya (satu baris per anotasi, ditambah kolom turunan)
# ---------------------------------------------------------------------------------------------
SQL_PERKAYA = """
SELECT ann_id,
       location AS lokasi,
       COALESCE(NULLIF(TRIM(inventory), ''), '%(tanpa_inv)s') AS inventaris,
       COALESCE(NULLIF(TRIM(event_type), ''), '%(kosong)s') AS jenis,
       author AS penulis,
       event_conf,
       area,
       event_date,
       year(event_date) AS tahun,
       month(event_date) AS bulan,
       CASE WHEN center_lat >= 0 THEN 'utara' ELSE 'selatan' END AS hemisfer,
       datediff(event_date, pre_date) AS selang_pra,
       datediff(post_date, event_date) AS selang_pasca,
       floor(log10(area)) AS dekade_area,
       floor(center_lon * 10) AS gx,
       floor(center_lat * 10) AS gy,
       center_lon,
       center_lat,
       sim_batch
FROM annotations
""" % {"tanpa_inv": TANPA_INVENTARIS, "kosong": KOSONG}


def _sql_kolom_kosong():
    bagian = []
    for tabel, teks, lain in (("annotations", KOLOM_ANOTASI_TEKS, KOLOM_ANOTASI_LAIN),
                              ("patches", KOLOM_PATCH_TEKS, KOLOM_PATCH_LAIN)):
        for k in teks:
            bagian.append("SELECT '%s' AS tabel, '%s' AS kolom, count(*) AS n_total, "
                          "sum(CASE WHEN %s IS NULL OR TRIM(%s) = '' THEN 1 ELSE 0 END) AS n_kosong FROM %s"
                          % (tabel, k, k, k, tabel))
        for k in lain:
            bagian.append("SELECT '%s' AS tabel, '%s' AS kolom, count(*) AS n_total, "
                          "sum(CASE WHEN %s IS NULL THEN 1 ELSE 0 END) AS n_kosong FROM %s"
                          % (tabel, k, k, tabel))
    return "\nUNION ALL\n".join(bagian) + "\nORDER BY tabel, kolom"


SQL_Q0 = """
SELECT 'anotasi' AS metrik, count(*) AS nilai FROM annotations
UNION ALL SELECT 'anotasi_asli_sim0', count(*) FROM annotations WHERE sim_batch = 0
UNION ALL SELECT 'inventaris_berbeda', count(DISTINCT NULLIF(TRIM(inventory), '')) FROM annotations
UNION ALL SELECT 'jenis_kejadian_berbeda', count(DISTINCT NULLIF(TRIM(event_type), '')) FROM annotations
UNION ALL SELECT 'lokasi_berbeda', count(DISTINCT location) FROM annotations
UNION ALL SELECT 'patch', count(*) FROM patches
UNION ALL SELECT 'penulis_berbeda', count(DISTINCT author) FROM annotations
ORDER BY metrik
"""

SQL_Q2 = """
SELECT 'ann_id_ganda' AS pemeriksaan, count(*) - count(DISTINCT ann_id) AS n_langgar FROM annotations
UNION ALL SELECT 'area_kosong', count(*) FROM annotations WHERE area IS NULL
UNION ALL SELECT 'area_nol_atau_negatif', count(*) FROM annotations WHERE area <= 0
UNION ALL SELECT 'bbox_terbalik', count(*) FROM annotations
          WHERE bbox_min_lon > bbox_max_lon OR bbox_min_lat > bbox_max_lat
UNION ALL SELECT 'conf_di_luar_0_1', count(*) FROM annotations WHERE event_conf < 0 OR event_conf > 1
UNION ALL SELECT 'jenis_kejadian_kosong', count(*) FROM annotations
          WHERE event_type IS NULL OR TRIM(event_type) = ''
UNION ALL SELECT 'koordinat_di_luar_rentang', count(*) FROM annotations
          WHERE center_lon < -180 OR center_lon > 180 OR center_lat < -90 OR center_lat > 90
UNION ALL SELECT 'patch_id_ganda', count(*) - count(DISTINCT patch_id) FROM patches
UNION ALL SELECT 'patch_inventaris_tanpa_anotasi', count(*) FROM patches
          WHERE inventory NOT IN (SELECT DISTINCT inventory FROM annotations WHERE inventory IS NOT NULL)
UNION ALL SELECT 'piksel_anotasi_negatif', count(*) FROM patches WHERE pixel_annotated < 0
UNION ALL SELECT 'pusat_di_luar_bbox', count(*) FROM annotations
          WHERE center_lon < bbox_min_lon OR center_lon > bbox_max_lon
             OR center_lat < bbox_min_lat OR center_lat > bbox_max_lat
UNION ALL SELECT 'tanpa_tanggal_apa_pun', count(*) FROM annotations
          WHERE pre_date IS NULL AND event_date IS NULL AND post_date IS NULL
UNION ALL SELECT 'urutan_tanggal_salah', count(*) FROM annotations
          WHERE pre_date > event_date OR event_date > post_date
ORDER BY pemeriksaan
"""

SQL_A1 = """
SELECT tahun, jenis, count(*) AS n, count(DISTINCT lokasi) AS n_lokasi
FROM ann_kaya
GROUP BY tahun, jenis
ORDER BY tahun, jenis
"""

SQL_A2 = """
SELECT bulan, hemisfer, jenis, count(*) AS n
FROM ann_kaya
GROUP BY bulan, hemisfer, jenis
ORDER BY bulan, hemisfer, jenis
"""

SQL_A3 = """
SELECT lokasi, inventaris, jenis, count(*) AS n,
       min(tahun) AS tahun_min, max(tahun) AS tahun_maks,
       percentile(area, 0.5) AS area_p50, avg(event_conf) AS conf_rata2
FROM ann_kaya
GROUP BY lokasi, inventaris, jenis
ORDER BY n DESC, lokasi, inventaris, jenis
"""

SQL_A3B = """
SELECT lokasi, sum(n) AS n_bertanggal, count(*) AS n_tanggal, max(n) AS n_hari_terpadat,
       min(event_date) AS tanggal_awal, max(event_date) AS tanggal_akhir
FROM (SELECT lokasi, event_date, count(*) AS n
      FROM ann_kaya
      WHERE event_date IS NOT NULL
      GROUP BY lokasi, event_date) t
GROUP BY lokasi
ORDER BY n_bertanggal DESC, lokasi
"""

SQL_A4A = """
SELECT jenis, count(area) AS n, min(area) AS area_min,
       percentile(area, 0.05) AS p05, percentile(area, 0.25) AS p25, percentile(area, 0.5) AS p50,
       percentile(area, 0.75) AS p75, percentile(area, 0.95) AS p95, max(area) AS area_maks
FROM ann_kaya
GROUP BY jenis
ORDER BY jenis
"""

SQL_A4B = """
SELECT dekade_area, jenis, count(*) AS n
FROM ann_kaya
WHERE dekade_area IS NOT NULL
GROUP BY dekade_area, jenis
ORDER BY dekade_area, jenis
"""

SQL_A5A = """
SELECT gx, gy, count(*) AS n, count(DISTINCT lokasi) AS n_lokasi,
       avg(center_lon) AS lon_rata2, avg(center_lat) AS lat_rata2
FROM ann_kaya
GROUP BY gx, gy
ORDER BY n DESC, gx, gy
LIMIT 20
"""

SQL_A5B = """
SELECT count(*) AS n_sel,
       sum(CASE WHEN n = 1 THEN 1 ELSE 0 END) AS n_sel_1,
       percentile(n, 0.5) AS p50_per_sel, percentile(n, 0.95) AS p95_per_sel,
       max(n) AS maks_per_sel, sum(n) AS n_total
FROM (SELECT gx, gy, count(*) AS n FROM ann_kaya GROUP BY gx, gy) s
"""

SQL_A6 = """
SELECT p.inventory AS inventaris,
       count(*) AS n_patch,
       sum(CASE WHEN p.split = 'train' THEN 1 ELSE 0 END) AS n_train,
       sum(CASE WHEN p.split = 'val' THEN 1 ELSE 0 END) AS n_val,
       sum(CASE WHEN p.split = 'test' THEN 1 ELSE 0 END) AS n_test,
       avg(p.pixel_annotated) AS piksel_rata2,
       percentile(p.pixel_annotated, 0.5) AS piksel_p50,
       max(p.pixel_annotated) AS piksel_maks,
       COALESCE(max(a.n_anotasi), 0) AS n_anotasi
FROM patches p
LEFT JOIN (SELECT inventory, count(*) AS n_anotasi FROM annotations
           WHERE inventory IS NOT NULL GROUP BY inventory) a
       ON p.inventory = a.inventory
GROUP BY p.inventory
ORDER BY p.inventory
"""

SQL_A7 = """
SELECT jenis, count(*) AS n,
       count(selang_pra) AS n_selang_pra,
       percentile(selang_pra, 0.5) AS selang_pra_p50, percentile(selang_pra, 0.95) AS selang_pra_p95,
       max(selang_pra) AS selang_pra_maks,
       count(selang_pasca) AS n_selang_pasca,
       percentile(selang_pasca, 0.5) AS selang_pasca_p50, percentile(selang_pasca, 0.95) AS selang_pasca_p95,
       max(selang_pasca) AS selang_pasca_maks,
       avg(event_conf) AS conf_rata2, percentile(event_conf, 0.5) AS conf_p50,
       sum(CASE WHEN event_conf = 1 THEN 1 ELSE 0 END) AS n_conf_1
FROM ann_kaya
GROUP BY jenis
ORDER BY jenis
"""

SQL_A8 = """
SELECT event_date, count(*) AS n, count(DISTINCT lokasi) AS n_lokasi
FROM ann_kaya
WHERE event_date IS NOT NULL
GROUP BY event_date
ORDER BY n DESC, event_date
LIMIT 15
"""

# (nama berkas tanpa .csv, judul singkat, kolom kunci untuk menyejajarkan baris, kueri)
ANALISIS = [
    ("q0_hitung", "Jumlah dasar", ["metrik"], SQL_Q0),
    ("q1_kolom_kosong", "Sel kosong per kolom", ["tabel", "kolom"], _sql_kolom_kosong()),
    ("q2_pemeriksaan", "Pemeriksaan kualitas data", ["pemeriksaan"], SQL_Q2),
    ("a1_tahun_jenis", "Anotasi per tahun dan jenis kejadian", ["tahun", "jenis"], SQL_A1),
    ("a2_bulan_hemisfer", "Anotasi per bulan, hemisfer, dan jenis", ["bulan", "hemisfer", "jenis"], SQL_A2),
    ("a3_lokasi", "Ringkasan per lokasi", ["lokasi", "inventaris", "jenis"], SQL_A3),
    ("a3b_lokasi_tanggal", "Tanggal kejadian berbeda per lokasi", ["lokasi"], SQL_A3B),
    ("a4a_area_jenis", "Kuantil luas per jenis kejadian", ["jenis"], SQL_A4A),
    ("a4b_area_dekade", "Sebaran luas per dekade (log10)", ["dekade_area", "jenis"], SQL_A4B),
    ("a5a_sel_terpadat", "20 sel 0,1 derajat terpadat", ["gx", "gy"], SQL_A5A),
    ("a5b_sel_ringkas", "Ringkasan kepadatan sel 0,1 derajat", [], SQL_A5B),
    ("a6_patch_inventaris", "Patch per inventaris dan pembagian split", ["inventaris"], SQL_A6),
    ("a7_waktu_kualitas", "Selang waktu citra dan confidence per jenis", ["jenis"], SQL_A7),
    ("a8_hari_terpadat", "15 hari kejadian dengan anotasi terbanyak", ["event_date"], SQL_A8),
]
NAMA_ANALISIS = [a[0] for a in ANALISIS]
KUNCI = dict((a[0], a[2]) for a in ANALISIS)


# ---------------------------------------------------------------------------------------------
# Penulisan dan pembacaan hasil
# ---------------------------------------------------------------------------------------------
def format_nilai(v):
    """Satu sel CSV. None -> kosong; float -> repr (bulat-balik); tanggal -> YYYY-MM-DD."""
    if v is None:
        return ""
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, float):
        return repr(v)
    if isinstance(v, (datetime.date, datetime.datetime)):
        return v.isoformat()[:10]
    return str(v)


def tulis_csv(jalur, kolom, baris):
    """Tulis satu tabel hasil. baris: daftar urutan nilai (tuple/list)."""
    folder = os.path.dirname(os.path.abspath(jalur))
    if not os.path.isdir(folder):
        os.makedirs(folder)
    with open(jalur, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(kolom)
        for b in baris:
            w.writerow([format_nilai(x) for x in b])


def baca_csv(jalur):
    """(kolom, baris) dengan semua nilai berupa teks."""
    with open(jalur, encoding="utf-8", newline="") as f:
        r = list(csv.reader(f))
    if not r:
        raise ValueError("%s kosong" % jalur)
    return r[0], r[1:]


def ke_tabel(df):
    """DataFrame Spark (atau tiruannya) -> (kolom, baris sebagai tuple). Memanggil collect()."""
    kolom = list(df.columns)
    baris = [tuple(r[i] for i in range(len(kolom))) for r in df.collect()]
    return kolom, baris
