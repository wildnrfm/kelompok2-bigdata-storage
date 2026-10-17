#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Ukur kueri W1 sampai W6 di Spark SQL atas Parquet. Berjalan DI DALAM kontainer spark.

Biasanya dipanggil lewat harness:  python bench/harness.py --store spark --workload W3 --scale S1
Panggilan langsung (PowerShell, SATU baris):
  docker exec sen12ls-spark /opt/spark/bin/spark-submit --master "local[2]" --driver-memory 2g
      /hdfs-parquet/run_sql.py --workload W3 --scale S1 --repeats 3 --cold-warm warm
      --out /results/CONTOH.csv

Definisi kueri diambil dari /bench/kueri.py (dipakai bersama MongoDB dan PostGIS). Titik uji dari
/bench/points.json. Satu baris CSV = satu eksekusi kueri; format sama dengan bench/harness.py.
Parquet dibaca dari hdfs://namenode:8020/data/sen12ls/parquet/<skala>/{annotations,patches}.
"""
import argparse
import csv
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, "/bench")
import kueri  # noqa: E402

KOLOM = ["penyimpanan", "beban_kerja", "skala", "ulangan", "cold_warm",
         "kueri_id", "waktu_ms", "jumlah_hasil", "catatan"]
HDFS_BASE = "hdfs://namenode:8020/data/sen12ls/parquet"


def persentil(nilai, q):
    import math
    urut = sorted(nilai)
    k = math.ceil(q / 100 * len(urut)) - 1
    return urut[max(0, min(len(urut) - 1, k))]


def jumlah_hasil(beban, baris):
    """W2-W4: isi kolom n. W1, W5, W6: jumlah baris (W5 dan W6: jumlah kelompok)."""
    if beban in ("W2", "W3", "W4"):
        return int(baris[0]["n"])
    return len(baris)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Uji W1 sampai W6 di Spark SQL (Parquet).")
    ap.add_argument("--workload", required=True, choices=kueri.BEBAN)
    ap.add_argument("--scale", required=True, choices=list(kueri.FAKTOR))
    ap.add_argument("--repeats", type=int, default=3)
    ap.add_argument("--cold-warm", dest="cold_warm", choices=["warm", "cold"], default="warm")
    ap.add_argument("--first-run-no", dest="first_run_no", type=int, default=1)
    ap.add_argument("--limit-titik", dest="limit_titik", type=int, default=0)
    ap.add_argument("--note", default="")
    ap.add_argument("--force", action="store_true", help="lewati pemeriksaan jumlah data")
    ap.add_argument("--out", required=True, help="berkas CSV hasil (belum boleh ada)")
    ap.add_argument("--points", default="/bench/points.json")
    ap.add_argument("--base", default=HDFS_BASE)
    args = ap.parse_args(argv)
    if args.repeats < 1:
        raise SystemExit("--repeats minimal 1")
    out = Path(args.out)
    if out.exists():
        raise SystemExit("Berkas %s sudah ada. Pakai nama lain." % out)
    par, titik = dict(kueri.PARAMETER_BAWAAN), []
    if args.workload in ("W2", "W3", "W4"):
        if not Path(args.points).exists():
            raise SystemExit("Berkas %s tidak ada. Jalankan python bench/make_points.py di komputermu, "
                             "dan nyalakan kontainer spark dari folder hdfs-parquet." % args.points)
        par, titik = kueri.muat_titik(args.points)
    daftar = kueri.daftar_kueri(args.workload, args.scale, titik)
    if args.limit_titik:
        daftar = daftar[:args.limit_titik]
    catatan = args.note
    if args.base != HDFS_BASE:
        catatan = ("sumber=%s %s" % (args.base, catatan)).strip()

    from pyspark.sql import SparkSession
    spark = (SparkSession.builder.appName("sen12ls-%s-%s" % (args.workload, args.scale))
             .config("spark.sql.shuffle.partitions", "4")
             .config("spark.ui.showConsoleProgress", "false")
             .getOrCreate())
    spark.sparkContext.setLogLevel("WARN")
    try:
        nama_tabel = kueri.tabel_beban(args.workload)
        folder = "%s/%s/%s" % (args.base.rstrip("/"), args.scale.lower(), nama_tabel)
        try:
            spark.read.parquet(folder).createOrReplaceTempView(nama_tabel)
            total = spark.table(nama_tabel).count()
        except Exception as e:  # noqa: BLE001
            pesan = str(e).strip().splitlines()[0] if str(e).strip() else repr(e)
            raise SystemExit("Tidak bisa membaca %s\n%s\nCek: kontainer namenode dan datanode jalan, "
                             "dan Parquet sudah dibuat (csv_to_parquet.py --scale %s)"
                             % (folder, pesan, args.scale))
        harap_a, harap_p = kueri.harapan(args.scale)
        harapan = harap_p if args.workload == "W6" else harap_a
        print("Jumlah data di %s: %d (harapan untuk %s: %d)" % (folder, total, args.scale, harapan), flush=True)
        if total != harapan and not args.force:
            raise SystemExit("Jumlah data tidak cocok. Buat Parquet skala %s dulu, atau jalankan "
                             "lagi dengan --force." % args.scale)

        def jalankan(q):
            t0 = time.perf_counter()
            try:
                n, galat = jumlah_hasil(args.workload,
                                        spark.sql(kueri.sql_spark(args.workload, q, par)).collect()), ""
            except Exception as e:  # noqa: BLE001
                n, galat = -1, "GALAT " + str(e).strip().splitlines()[0][:80] if str(e).strip() else "GALAT"
            return (time.perf_counter() - t0) * 1000, n, galat

        if args.cold_warm == "warm":
            print("Pemanasan: satu putaran %d kueri (tidak dicatat)..." % len(daftar), flush=True)
            for q in daftar:
                jalankan(q)
        else:
            print("Mode cold: tanpa pemanasan.", flush=True)

        baris, waktu, pertama = [], [], {}
        awal = args.first_run_no
        for ulangan in range(awal, awal + args.repeats):
            for q in daftar:
                ms, n, galat = jalankan(q)
                baris.append(["spark", args.workload, args.scale, ulangan, args.cold_warm,
                              q["id"], "%.3f" % ms, n, (catatan + " " + galat).strip()])
                waktu.append(ms)
                if ulangan == awal:
                    pertama[q["id"]] = n
            print("Ulangan %d selesai (%d kueri)" % (ulangan, len(daftar)), flush=True)

        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f, lineterminator="\n")
            w.writerow(KOLOM)
            w.writerows(baris)
        ada = sum(1 for n in pertama.values() if n > 0)
        galat_n = sum(1 for n in pertama.values() if n < 0)
        print()
        print("Ringkasan spark %s %s (%s, %d ulangan x %d kueri = %d eksekusi)"
              % (args.workload, args.scale, args.cold_warm, args.repeats, len(daftar), len(waktu)))
        print("  median : %.3f ms" % statistics.median(waktu))
        print("  p95    : %.3f ms" % persentil(waktu, 95))
        print("  p99    : %.3f ms" % persentil(waktu, 99))
        print("  rata2  : %.3f ms" % statistics.mean(waktu))
        print("  hasil  : %d per putaran; %d dari %d kueri punya hasil%s"
              % (sum(n for n in pertama.values() if n > 0), ada, len(pertama),
                 "; %d GALAT" % galat_n if galat_n else ""))
        print("Berkas   :", out)
    finally:
        spark.stop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
