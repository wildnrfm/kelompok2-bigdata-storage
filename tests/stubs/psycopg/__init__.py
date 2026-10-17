"""Tiruan psycopg: SQLite dalam memori; PostGIS diterjemahkan ke perbandingan angka biasa.

Hanya mengenali templat kueri di bench/kueri.py (SQL_POSTGIS). Basis data diisi dari CSV
lewat muat_csv(folder) (di PostgreSQL asli tugas ini dikerjakan oleh postgis/load.sql).
"""
import csv
import re
import sqlite3

_DB = {"sambungan": None}
_KOLOM_ANGKA_BULAT = {"ann_id", "sim_batch", "pixel_annotated"}
_KOLOM_DESIMAL = {"event_conf", "area", "center_lon", "center_lat", "bbox_min_lon", "bbox_min_lat",
                  "bbox_max_lon", "bbox_max_lat"}


def _sambung():
    if _DB["sambungan"] is None:
        _DB["sambungan"] = sqlite3.connect(":memory:", check_same_thread=False)
    return _DB["sambungan"]


def kosongkan():
    if _DB["sambungan"] is not None:
        _DB["sambungan"].close()
    _DB["sambungan"] = None


def _nilai(kolom, teks):
    if teks == "":
        return None
    if kolom in _KOLOM_ANGKA_BULAT:
        return int(teks)
    if kolom in _KOLOM_DESIMAL:
        return float(teks)
    return teks


def muat_csv(folder, tambah=False):
    db = _sambung()
    for nama in ("annotations", "patches"):
        with open("%s/%s.csv" % (folder, nama), encoding="utf-8", newline="") as f:
            baca = csv.reader(f)
            kolom = next(baca)
            if not tambah:
                db.execute("DROP TABLE IF EXISTS %s" % nama)
            db.execute("CREATE TABLE IF NOT EXISTS %s (%s)" % (nama, ", ".join(kolom)))
            db.executemany("INSERT INTO %s VALUES (%s)" % (nama, ",".join("?" * len(kolom))),
                           ([_nilai(k, v) for k, v in zip(kolom, baris)] for baris in baca))
    db.commit()


def _terjemah(sql):
    sql = re.sub(r"ST_Intersects\(center, ST_MakeEnvelope\(%s, %s, %s, %s, 4326\)\)",
                 "(center_lon >= ? AND center_lat >= ? AND center_lon <= ? AND center_lat <= ?)", sql)
    sql = re.sub(r"ST_Intersects\(bbox, ST_MakeEnvelope\(%s, %s, %s, %s, 4326\)\)",
                 "(bbox_max_lon >= ? AND bbox_max_lat >= ? AND bbox_min_lon <= ? AND bbox_min_lat <= ?)", sql)
    sql = sql.replace("EXTRACT(year FROM event_date)::int", "CAST(strftime('%Y', event_date) AS INTEGER)")
    sql = sql.replace("%s::date", "?").replace("%s", "?")
    if "ST_" in sql or "::" in sql:
        raise ValueError("tiruan psycopg tidak mengenali SQL ini: " + sql)
    return sql


class _Kursor:
    def __init__(self):
        self._baris = []

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, sql, params=()):
        self._baris = list(_sambung().execute(_terjemah(sql), tuple(params)))

    def fetchone(self):
        return self._baris[0] if self._baris else None

    def fetchall(self):
        return list(self._baris)


class _Sambungan:
    def cursor(self):
        return _Kursor()

    def close(self):
        pass


def connect(dsn=None, **kw):
    return _Sambungan()
