"""Tiruan pyspark.sql: SparkSession dengan SQLite; 'HDFS' adalah kamus dalam memori."""
import csv
import re
import sqlite3

_HDFS = {}          # jalur Parquet -> daftar baris (kamus)


def kosongkan():
    _HDFS.clear()


class Row(dict):
    def __getitem__(self, k):
        if isinstance(k, int):
            return list(self.values())[k]
        return dict.__getitem__(self, k)


def _ddl(skema):
    return [tuple(p.split()) for p in skema.split(",")]


def _konversi(tipe, teks):
    if teks == "":
        return None
    if tipe in ("long", "int"):
        return int(teks)
    if tipe == "double":
        return float(teks)
    return teks


class _Tulis:
    def __init__(self, df):
        self.df, self.m = df, "overwrite"

    def mode(self, m):
        self.m = m
        return self

    def option(self, k, v):
        return self

    def parquet(self, jalur):
        if self.m == "append":
            _HDFS.setdefault(jalur, []).extend(self.df.baris)
        else:
            _HDFS[jalur] = list(self.df.baris)


class DataFrame:
    def __init__(self, baris):
        self.baris = baris

    @property
    def write(self):
        return _Tulis(self)

    def count(self):
        return len(self.baris)

    def createOrReplaceTempView(self, nama):
        SparkSession._aktif._daftarkan(nama, self.baris)


class _Lector:
    def __init__(self):
        self._skema = None

    def schema(self, ddl):
        self._skema = _ddl(ddl)
        return self

    def option(self, k, v):
        return self

    def csv(self, jalur):
        jalur = jalur[len("file://"):] if jalur.startswith("file://") else jalur
        with open(jalur, encoding="utf-8", newline="") as f:
            baca = csv.reader(f)
            kepala = next(baca)
            if len(kepala) != len(self._skema):
                raise ValueError("jumlah kolom %d != skema %d" % (len(kepala), len(self._skema)))
            return DataFrame([{n: _konversi(t, v) for (n, t), v in zip(self._skema, b)} for b in baca])

    def parquet(self, jalur):
        if jalur not in _HDFS:
            raise Exception("Path does not exist: %s" % jalur)
        return DataFrame(_HDFS[jalur])


class _Konteks:
    def setLogLevel(self, tingkat):
        pass


class _Pembangun:
    def appName(self, nama):
        return self

    def config(self, k, v):
        return self

    def getOrCreate(self):
        s = SparkSession()
        SparkSession._aktif = s
        return s


def _terjemah(sql):
    sql = re.sub(r"DATE '(\d{4}-\d{2}-\d{2})'", r"'\1'", sql)
    sql = re.sub(r"year\(event_date\)", "CAST(strftime('%Y', event_date) AS INTEGER)", sql)
    return sql


class SparkSession:
    builder = _Pembangun()
    _aktif = None

    def __init__(self):
        self._db = sqlite3.connect(":memory:")
        self.sparkContext = _Konteks()
        self.read = _Lector()

    def _daftarkan(self, nama, baris):
        self._db.execute("DROP TABLE IF EXISTS %s" % nama)
        if not baris:
            raise ValueError("tabel kosong: " + nama)
        kolom = list(baris[0])
        self._db.execute("CREATE TABLE %s (%s)" % (nama, ", ".join(kolom)))
        self._db.executemany("INSERT INTO %s VALUES (%s)" % (nama, ",".join("?" * len(kolom))),
                             ([b[k] for k in kolom] for b in baris))

    def table(self, nama):
        h = self._db.execute("SELECT * FROM %s" % nama).fetchall()
        return DataFrame(h)

    def sql(self, teks):
        cur = self._db.execute(_terjemah(teks))
        nama = [d[0] for d in cur.description]
        hasil = [Row(zip(nama, r)) for r in cur.fetchall()]

        class _Hasil:
            def collect(self_inner):
                return hasil
        return _Hasil()

    def stop(self):
        self._db.close()
