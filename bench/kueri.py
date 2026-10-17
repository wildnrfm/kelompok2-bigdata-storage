# -*- coding: utf-8 -*-
"""Definisi kueri W1 sampai W6, dipakai BERSAMA oleh harness (MongoDB, PostGIS) dan
hdfs-parquet/run_sql.py (Spark), supaya ketiga penyimpanan menjawab pertanyaan yang sama.

Pertanyaan tiap beban kerja (satu "kueri" = satu titik dari bench/points.json):
  W1  ambil satu anotasi menurut ann_id (100 id tetap, tersebar di seluruh skala)
  W2  jumlah anotasi yang TITIK PUSATNYA ada di jendela persegi +-half_titik derajat
      (bawaan 0,01 derajat, sekitar 1,1 km) di sekitar titik uji
  W3  seperti W2, dan event_date antara date_from dan date_to (titik uji +-30 hari)
  W4  jumlah anotasi yang KOTAK PEMBATASNYA beririsan dengan jendela +-half_kotak derajat
      (bawaan 0,1 derajat, sekitar 22 km), dengan event_type tertentu dan event_conf >= 0,9
  W5  jumlah anotasi per event_type dan tahun kejadian (jumlah_hasil = jumlah kelompok)
  W6  jumlah patch per inventory dan split, rata-rata pixel_annotated (jumlah_hasil = kelompok)

Semua perbandingan memakai batas tertutup. Batas jendela digeser setengah langkah dari
kisi 1e-7 derajat tempat semua koordinat data berada, jadi tidak ada titik yang jatuh
tepat di tepi jendela (hasil tidak bergantung pada cara tiap mesin memperlakukan tepi).
MongoDB menghitung pada bola, PostGIS dan Spark pada bidang datar; tepi utara-selatan
jendela di MongoDB dipadatkan tiap 0,005 derajat sehingga selisih garis bolanya (< 3e-8
derajat) lebih kecil daripada jarak titik mana pun ke tepi.
"""
import json
import math
import random
from datetime import date, datetime, time

SEED = 20261023
N_DASAR_ANOTASI = 74956
N_DASAR_PATCH = 4392
FAKTOR = {"S1": 1, "S10": 10, "S100": 100}
BEBAN = ["W1", "W2", "W3", "W4", "W5", "W6"]
LANGKAH_CINCIN = 0.005
PARAMETER_BAWAAN = {"half_titik": 0.01, "half_kotak": 0.1, "hari": 30, "conf_min": 0.9}


def harapan(skala):
    """(jumlah anotasi, jumlah patch) yang seharusnya ada di satu skala."""
    return N_DASAR_ANOTASI * FAKTOR[skala], N_DASAR_PATCH * FAKTOR[skala]


def muat_titik(jalur):
    """(parameter, daftar titik) dari bench/points.json."""
    with open(jalur, encoding="utf-8") as f:
        doc = json.load(f)
    par = dict(PARAMETER_BAWAAN)
    par.update(doc.get("parameter", {}))
    return par, doc["points"]


def ids_w1(skala, n=100):
    """100 ann_id tetap yang tersebar merata di seluruh skala (kueri_id = nomor urut 1..100)."""
    total = N_DASAR_ANOTASI * FAKTOR[skala]
    rng = random.Random(SEED + 1)
    return [{"id": i + 1, "ann_id": v} for i, v in enumerate(sorted(rng.sample(range(total), n)))]


def daftar_kueri(beban, skala, titik):
    """Daftar kueri satu beban kerja: W1 dari ids_w1, W2 sampai W4 dari titik uji, W5 dan W6 satu kueri."""
    if beban == "W1":
        return ids_w1(skala)
    if beban in ("W2", "W3", "W4"):
        return titik
    return [{"id": 1}]


def jendela(lon, lat, half):
    """(x0, y0, x1, y1) jendela persegi, batasnya digeser setengah langkah kisi (5e-8)."""
    return (round(round(lon - half, 7) - 5e-8, 8), round(round(lat - half, 7) - 5e-8, 8),
            round(round(lon + half, 7) + 5e-8, 8), round(round(lat + half, 7) + 5e-8, 8))


def jendela_kueri(beban, p, par):
    half = par["half_kotak"] if beban == "W4" else par["half_titik"]
    return jendela(p["lon"], p["lat"], half)


# ------------------------------------------------------------------ MongoDB
def _antara(a, b, langkah):
    n = max(1, int(math.ceil(abs(b - a) / langkah)))
    return [round(a + (b - a) * i / n, 8) for i in range(n + 1)]


def cincin_mongo(x0, y0, x1, y1, langkah=LANGKAH_CINCIN):
    """Cincin GeoJSON berlawanan jarum jam, tertutup, tepi dipadatkan tiap 'langkah' derajat."""
    cincin = [[x, y0] for x in _antara(x0, x1, langkah)]
    cincin += [[x1, y] for y in _antara(y0, y1, langkah)[1:]]
    cincin += [[x, y1] for x in _antara(x1, x0, langkah)[1:]]
    cincin += [[x0, y] for y in _antara(y1, y0, langkah)[1:]]
    return cincin


def poligon_mongo(w):
    return {"type": "Polygon", "coordinates": [cincin_mongo(*w)]}


def tanggal_mongo(teks):
    """'2019-03-15' menjadi datetime tengah malam UTC (pymongo membaca datetime polos sebagai UTC)."""
    return datetime.combine(date.fromisoformat(teks), time())


def filter_mongo(beban, p, par):
    """Filter MongoDB untuk W2 sampai W4 (dihitung dengan count_documents)."""
    w = jendela_kueri(beban, p, par)
    if beban == "W2":
        return {"center": {"$geoWithin": {"$geometry": poligon_mongo(w)}}}
    if beban == "W3":
        return {"center": {"$geoWithin": {"$geometry": poligon_mongo(w)}},
                "dates.event": {"$gte": tanggal_mongo(p["date_from"]),
                                "$lte": tanggal_mongo(p["date_to"])}}
    if beban == "W4":
        return {"bbox": {"$geoIntersects": {"$geometry": poligon_mongo(w)}},
                "event_type": p["event_type"], "event_conf": {"$gte": par["conf_min"]}}
    raise ValueError(beban)


PIPA_W5 = [{"$group": {"_id": {"event_type": "$event_type", "tahun": {"$year": "$dates.event"}},
                       "n": {"$sum": 1}}},
           {"$sort": {"_id.event_type": 1, "_id.tahun": 1}}]
PIPA_W6 = [{"$group": {"_id": {"inventory": "$inventory", "split": "$split"},
                       "n": {"$sum": 1}, "rata_piksel": {"$avg": "$pixel_annotated"}}},
           {"$sort": {"_id.inventory": 1, "_id.split": 1}}]


# ------------------------------------------------------------------ PostGIS
SQL_POSTGIS = {
    "W1": "SELECT ann_id, location, event_type, event_date FROM annotations WHERE ann_id = %s",
    "W2": ("SELECT count(*) FROM annotations "
           "WHERE ST_Intersects(center, ST_MakeEnvelope(%s, %s, %s, %s, 4326))"),
    "W3": ("SELECT count(*) FROM annotations "
           "WHERE ST_Intersects(center, ST_MakeEnvelope(%s, %s, %s, %s, 4326)) "
           "AND event_date BETWEEN %s::date AND %s::date"),
    "W4": ("SELECT count(*) FROM annotations "
           "WHERE ST_Intersects(bbox, ST_MakeEnvelope(%s, %s, %s, %s, 4326)) "
           "AND event_type = %s AND event_conf >= %s"),
    "W5": ("SELECT event_type, EXTRACT(year FROM event_date)::int AS tahun, count(*) AS n "
           "FROM annotations GROUP BY 1, 2 ORDER BY 1, 2"),
    "W6": ("SELECT inventory, split, count(*) AS n, round(avg(pixel_annotated), 1) AS rata_piksel "
           "FROM patches GROUP BY 1, 2 ORDER BY 1, 2"),
}


def param_postgis(beban, p, par):
    if beban == "W1":
        return [p["ann_id"]]
    if beban in ("W5", "W6"):
        return []
    w = list(jendela_kueri(beban, p, par))
    if beban == "W2":
        return w
    if beban == "W3":
        return w + [p["date_from"], p["date_to"]]
    return w + [p["event_type"], par["conf_min"]]


# ------------------------------------------------------------------ Spark SQL
def _lit(teks):
    return "'" + str(teks).replace("'", "''") + "'"


def _tgl(teks):
    """Literal tanggal Spark SQL: DATE 'YYYY-MM-DD' (jelas bertipe tanggal, tanpa tebakan Spark)."""
    date.fromisoformat(str(teks))            # tolak teks yang bukan tanggal
    return "DATE '%s'" % teks


def sql_spark(beban, p, par):
    """Teks Spark SQL satu kueri. Tabel: view annotations dan patches dari Parquet."""
    if beban == "W1":
        return ("SELECT ann_id, location, event_type, event_date FROM annotations "
                "WHERE ann_id = %d" % p["ann_id"])
    if beban == "W5":
        return ("SELECT event_type, year(event_date) AS tahun, count(*) AS n "
                "FROM annotations GROUP BY event_type, year(event_date)")
    if beban == "W6":
        return ("SELECT inventory, split, count(*) AS n, round(avg(pixel_annotated), 1) AS rata_piksel "
                "FROM patches GROUP BY inventory, split")
    x0, y0, x1, y1 = ["%.8f" % v for v in jendela_kueri(beban, p, par)]
    if beban == "W2":
        return ("SELECT count(*) AS n FROM annotations WHERE center_lon BETWEEN %s AND %s "
                "AND center_lat BETWEEN %s AND %s" % (x0, x1, y0, y1))
    if beban == "W3":
        return ("SELECT count(*) AS n FROM annotations WHERE center_lon BETWEEN %s AND %s "
                "AND center_lat BETWEEN %s AND %s AND event_date BETWEEN %s AND %s"
                % (x0, x1, y0, y1, _tgl(p["date_from"]), _tgl(p["date_to"])))
    return ("SELECT count(*) AS n FROM annotations WHERE bbox_min_lon <= %s AND bbox_max_lon >= %s "
            "AND bbox_min_lat <= %s AND bbox_max_lat >= %s AND event_type = %s AND event_conf >= %s"
            % (x1, x0, y1, y0, _lit(p["event_type"]), repr(float(par["conf_min"]))))


def tabel_beban(beban):
    """Tabel/koleksi yang jumlah barisnya dijaga: patches untuk W6, selain itu annotations."""
    return "patches" if beban == "W6" else "annotations"
