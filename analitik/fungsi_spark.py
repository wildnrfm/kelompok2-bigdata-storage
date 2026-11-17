# -*- coding: utf-8 -*-
"""Fungsi tiruan Spark SQL untuk SQLite. HANYA untuk uji di komputer tanpa Spark.

Kueri analitik ditulis dalam dialek Spark SQL (year, month, datediff, log10, floor, percentile).
SQLite tidak punya fungsi-fungsi itu, jadi di sini dibuat versi Python yang artinya sama:

  year(d), month(d)   tahun dan bulan dari teks tanggal YYYY-MM-DD (NULL bila d NULL)
  datediff(a, b)      selisih hari a dikurangi b, seperti datediff(akhir, awal) di Spark
  log10(x), floor(x)  log10(x <= 0) = NULL; floor mengembalikan bilangan bulat, seperti Spark (BIGINT)
  percentile(x, p)    persentil EKSAK dengan interpolasi linear (rumus percentile() Spark/Hive):
                      posisi = (n - 1) * p; bila posisi tidak bulat,
                      (atas - posisi) * nilai[bawah] + (posisi - bawah) * nilai[atas]

Hanya Python bawaan.
"""
import math
from datetime import date


def _tgl(teks):
    return date(int(teks[0:4]), int(teks[5:7]), int(teks[8:10]))


def year(teks):
    return None if teks is None else int(teks[0:4])


def month(teks):
    return None if teks is None else int(teks[5:7])


def datediff(akhir, awal):
    if akhir is None or awal is None:
        return None
    return (_tgl(akhir) - _tgl(awal)).days


def log10(x):
    """Seperti Spark: NULL untuk masukan NULL atau tidak positif (Spark tidak melempar galat)."""
    if x is None or x <= 0:
        return None
    return math.log10(x)


def floor(x):
    return None if x is None else int(math.floor(x))


def persentil_eksak(nilai_terurut, p):
    """Rumus percentile() Spark. nilai_terurut: daftar angka urut naik (tanpa NULL)."""
    n = len(nilai_terurut)
    if n == 0:
        return None
    posisi = (n - 1) * p
    bawah = int(math.floor(posisi))
    atas = int(math.ceil(posisi))
    if bawah == atas:
        return float(nilai_terurut[bawah])
    if nilai_terurut[bawah] == nilai_terurut[atas]:
        return float(nilai_terurut[bawah])      # Spark tidak menginterpolasi dua nilai yang sama
    return (atas - posisi) * nilai_terurut[bawah] + (posisi - bawah) * nilai_terurut[atas]


class Percentile(object):
    """Agregat SQLite: percentile(kolom, p). NULL diabaikan."""

    def __init__(self):
        self.nilai = []
        self.p = None

    def step(self, x, p):
        if x is not None:
            self.nilai.append(x)
        self.p = p

    def finalize(self):
        return persentil_eksak(sorted(self.nilai), self.p)


def pasang(koneksi):
    """Daftarkan semua fungsi tiruan ke koneksi sqlite3."""
    koneksi.create_function("year", 1, year)
    koneksi.create_function("month", 1, month)
    koneksi.create_function("datediff", 2, datediff)
    koneksi.create_function("log10", 1, log10)
    koneksi.create_function("floor", 1, floor)
    koneksi.create_aggregate("percentile", 2, Percentile)
