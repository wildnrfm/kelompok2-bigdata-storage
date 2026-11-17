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

    def asDict(self):
        return dict(self)


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

    @property
    def columns(self):
        return list(self.baris[0]) if self.baris and isinstance(self.baris[0], dict) else []

    def collect(self):
        return [Row(b) if isinstance(b, dict) else b for b in self.baris]

    def count(self):
        return len(self.baris)

    def createOrReplaceTempView(self, nama):
        SparkSession._aktif._daftarkan(nama, self.baris)


class _HasilSQL(DataFrame):
    """Hasil spark.sql(): baris sudah dihitung. Bila didaftarkan sebagai view, yang disimpan adalah
    kueri SQL-nya (malas, seperti Spark), bukan barisnya."""

    def __init__(self, sesi, sql, nama, baris):
        DataFrame.__init__(self, baris)
        self._sesi, self._sql, self._nama = sesi, sql, nama

    @property
    def columns(self):
        return list(self._nama)

    def collect(self):
        return self.baris

    def createOrReplaceTempView(self, nama):
        self._sesi._daftarkan_view(nama, self._sql)


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


def _pasang_fungsi_spark(db):
    """Daftarkan year, month, datediff, log10, floor, percentile (analitik/fungsi_spark.py) bila ada."""
    import os
    import sys
    akar = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
    jalur = os.path.join(akar, "analitik")
    if os.path.isdir(jalur):
        if jalur not in sys.path:
            sys.path.insert(0, jalur)
        import fungsi_spark
        fungsi_spark.pasang(db)


def _terjemah(sql):
    sql = re.sub(r"DATE '(\d{4}-\d{2}-\d{2})'", r"'\1'", sql)
    sql = re.sub(r"year\(event_date\)", "CAST(strftime('%Y', event_date) AS INTEGER)", sql)
    return sql


class SparkSession:
    builder = _Pembangun()
    _aktif = None

    def __init__(self):
        self._db = sqlite3.connect(":memory:")
        _pasang_fungsi_spark(self._db)
        self.sparkContext = _Konteks()
        self.read = _Lector()

    def _buang(self, nama):
        """Buang tabel atau view bernama itu (apa pun jenisnya)."""
        r = self._db.execute("SELECT type FROM sqlite_master WHERE name = ?", (nama,)).fetchone()
        if r:
            self._db.execute("DROP %s %s" % ("VIEW" if r[0] == "view" else "TABLE", nama))

    def _daftarkan_view(self, nama, sql):
        self._buang(nama)
        self._db.execute("CREATE VIEW %s AS %s" % (nama, sql))

    def _daftarkan(self, nama, baris):
        self._buang(nama)
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
        sql = _terjemah(teks)
        cur = self._db.execute(sql)
        nama = [d[0] for d in cur.description]
        return _HasilSQL(self, sql, nama, [Row(zip(nama, r)) for r in cur.fetchall()])

    def stop(self):
        self._db.close()
