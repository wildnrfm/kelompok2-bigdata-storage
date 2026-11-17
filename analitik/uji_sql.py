#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Uji kueri analitik TANPA Spark: jalankan kueri Spark SQL yang sama di SQLite, lalu bandingkan
dengan hitungan Python murni (referensi.py).

SQLite tidak punya year, month, datediff, log10, floor, dan percentile; fungsi_spark.py
mendaftarkan versi Python yang artinya sama dengan Spark. Jadi uji ini membuktikan LOGIKA kueri
(pengelompokan, penanganan NULL, urutan, persentil) benar. Yang tidak dibuktikan: perilaku mesin
Spark itu sendiri; itu diperiksa dengan menjalankan spark_pipeline.py lalu cocokkan.py.

Pemakaian (dari akar repo):
  python analitik/uji_sql.py --skala S1           data nyata, sekitar 1 menit
  python analitik/uji_sql.py --folder X           folder berisi annotations.csv dan patches.csv
  python analitik/uji_sql.py --skala S10 --hanya-asli
"""
import argparse
import sqlite3
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cocokkan  # noqa: E402
import fungsi_spark  # noqa: E402
import kueri_analitik as ka  # noqa: E402
import referensi  # noqa: E402

AKAR = Path(__file__).resolve().parent.parent
TIPE_SQLITE = {"long": "INTEGER", "int": "INTEGER", "double": "REAL", "string": "TEXT", "date": "TEXT"}


def _siap(v):
    """Tanggal -> teks ISO (seperti DATE di Spark jika dicetak); selain itu apa adanya."""
    return v.isoformat() if hasattr(v, "isoformat") else v


def muat_sqlite(koneksi, folder, hanya_asli=False):
    """Buat tabel annotations dan patches (tipe sesuai skema Parquet; kosong = NULL) dan isi dari CSV."""
    folder = Path(folder)
    for nama, skema in (("annotations", ka.SKEMA_ANOTASI), ("patches", ka.SKEMA_PATCH)):
        koneksi.execute("DROP TABLE IF EXISTS %s" % nama)
        koneksi.execute("CREATE TABLE %s (%s)" % (nama, ", ".join("%s %s" % (n, TIPE_SQLITE[t]) for n, t in skema)))
        i_sim = [n for n, _ in skema].index("sim_batch")

        def baris():
            for v, _ in referensi.baca_bertipe(folder / (nama + ".csv"), skema):
                if hanya_asli and v[i_sim] != 0:
                    continue
                yield [_siap(x) for x in v]
        koneksi.executemany("INSERT INTO %s VALUES (%s)" % (nama, ",".join("?" * len(skema))), baris())
    koneksi.execute("DROP VIEW IF EXISTS %s" % ka.TABEL_KAYA)
    koneksi.execute("CREATE VIEW %s AS %s" % (ka.TABEL_KAYA, ka.SQL_PERKAYA))


def jalankan_sql(koneksi, sql):
    cur = koneksi.execute(sql)
    kolom = [d[0] for d in cur.description]
    return kolom, [tuple(r) for r in cur.fetchall()]


def uji(folder, hanya_asli=False, tol=1e-9, cetak=print):
    """Kembalikan (jumlah tabel cocok, jumlah bermasalah). Mencetak laporan lewat cetak()."""
    t0 = time.time()
    acuan = referensi.hitung(folder, hanya_asli)
    cetak("Acuan Python selesai (%.1f detik)" % (time.time() - t0))
    k = sqlite3.connect(":memory:")
    fungsi_spark.pasang(k)
    t0 = time.time()
    muat_sqlite(k, folder, hanya_asli)
    cetak("Data dimuat ke SQLite (%.1f detik)" % (time.time() - t0))
    ok = buruk = sel = 0
    for nama, judul, kunci, sql in ka.ANALISIS:
        t0 = time.time()
        kolom, baris = jalankan_sql(k, sql)
        dt = time.time() - t0
        teks = [[ka.format_nilai(x) for x in b] for b in baris]
        kolom_b, baris_b = acuan[nama]
        teks_b = [[ka.format_nilai(x) for x in b] for b in baris_b]
        beda, n = cocokkan.bandingkan_tabel(nama, kolom, teks, kolom_b, teks_b, kunci, tol)
        sel += n
        if beda:
            buruk += 1
            cetak("BEDA    %s (%.1f detik)" % (nama, dt))
            for x in beda:
                cetak("        " + x)
        else:
            ok += 1
            cetak("COCOK   %-22s %4d baris, %5d sel (%.1f detik)" % (nama, len(teks), n, dt))
    k.close()
    return ok, buruk, sel


def main(argv=None):
    ap = argparse.ArgumentParser(description="Uji kueri analitik di SQLite terhadap hitungan Python.")
    ap.add_argument("--skala", choices=["S1", "S10", "S100"])
    ap.add_argument("--folder")
    ap.add_argument("--hanya-asli", action="store_true")
    ap.add_argument("--toleransi", type=float, default=1e-9)
    args = ap.parse_args(argv)
    if not args.skala and not args.folder:
        raise SystemExit("Isi --skala atau --folder.")
    folder = Path(args.folder) if args.folder else AKAR / "data" / "out" / args.skala.lower()
    ok, buruk, sel = uji(folder, args.hanya_asli, args.toleransi)
    print()
    if buruk:
        print("ADA SELISIH: %d tabel cocok, %d bermasalah." % (ok, buruk))
        return 1
    print("KUERI = ACUAN (%d tabel, %d sel dibandingkan)" % (ok, sel))
    return 0


if __name__ == "__main__":
    sys.exit(main())
