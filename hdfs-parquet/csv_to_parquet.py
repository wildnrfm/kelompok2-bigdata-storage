#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Ubah CSV satu skala menjadi Parquet di HDFS. Berjalan DI DALAM kontainer spark.

Perintah (PowerShell; tulis dalam SATU baris):
  docker exec sen12ls-spark /opt/spark/bin/spark-submit --master "local[2]" --driver-memory 2g
      /hdfs-parquet/csv_to_parquet.py --scale S1
Hasil: hdfs://namenode:8020/data/sen12ls/parquet/s1/annotations  dan  .../s1/patches
(S10 dan S100 sama, ganti --scale). Parquet dikompresi ZSTD. Skrip menimpa hasil lama.

Tambah batch baru tanpa menimpa (beban kerja W8):
  ... csv_to_parquet.py --scale S100 --folder /sen12ls-data/out/batch100 --tambah

Pilihan lain:
  --kompresi snappy    bila ZSTD ditolak di mesinmu (catat di laporan)
  --base file:///tmp/pq   tulis ke disk kontainer, bukan HDFS (hanya untuk uji coba kode)
Setelah selesai skrip membaca ulang Parquet dan membandingkan jumlah baris dengan CSV.
"""
import argparse
import sys
import time
from pathlib import Path

HDFS_BASE = "hdfs://namenode:8020/data/sen12ls/parquet"
DATA = "/sen12ls-data/out"

KOLOM_ANOTASI = [
    ("ann_id", "long"), ("location", "string"), ("inventory", "string"), ("event_type", "string"),
    ("type", "string"), ("velocity_c", "string"), ("author", "string"), ("reference", "string"),
    ("event_conf", "double"), ("area", "double"),
    ("pre_date", "date"), ("event_date", "date"), ("post_date", "date"),
    ("pre_dt2", "date"), ("event_dt2", "date"), ("post_dt2", "date"),
    ("center_lon", "double"), ("center_lat", "double"),
    ("bbox_min_lon", "double"), ("bbox_min_lat", "double"),
    ("bbox_max_lon", "double"), ("bbox_max_lat", "double"), ("sim_batch", "int"),
]
KOLOM_PATCH = [
    ("patch_id", "string"), ("split", "string"), ("inventory", "string"), ("s2_path", "string"),
    ("s1asc_path", "string"), ("s1dsc_path", "string"), ("pixel_annotated", "int"), ("sim_batch", "int"),
]


def skema_ddl(kolom):
    """Skema untuk spark.read.csv, bentuk DDL: 'ann_id long, location string, ...'."""
    return ", ".join("%s %s" % (n, t) for n, t in kolom)


def baca_harapan(skala):
    """(jumlah anotasi, jumlah patch) menurut bench/kueri.py (dipasang di /bench), atau None."""
    sys.path.insert(0, "/bench")
    try:
        import kueri
        return kueri.harapan(skala)
    except Exception:
        return None


def main(argv=None):
    ap = argparse.ArgumentParser(description="CSV ke Parquet di HDFS.")
    ap.add_argument("--scale", required=True, choices=["S1", "S10", "S100"])
    ap.add_argument("--folder", help="folder CSV di kontainer (bawaan %s/<skala>)" % DATA)
    ap.add_argument("--base", default=HDFS_BASE, help="folder dasar Parquet")
    ap.add_argument("--tambah", action="store_true", help="tambahkan (append) tanpa menimpa")
    ap.add_argument("--kompresi", default="zstd", choices=["zstd", "snappy", "gzip", "none"])
    args = ap.parse_args(argv)

    folder = args.folder or "%s/%s" % (DATA, args.scale.lower())
    tujuan = "%s/%s" % (args.base.rstrip("/"), args.scale.lower())

    from pyspark.sql import SparkSession
    spark = (SparkSession.builder.appName("sen12ls-csv-ke-parquet-%s" % args.scale)
             .config("spark.sql.shuffle.partitions", "4")
             .config("spark.ui.showConsoleProgress", "false")
             .getOrCreate())
    spark.sparkContext.setLogLevel("WARN")
    try:
        mulai = time.time()
        total = {}
        for nama, kolom in (("annotations", KOLOM_ANOTASI), ("patches", KOLOM_PATCH)):
            sumber = "file://%s/%s.csv" % (folder, nama)
            df = (spark.read.schema(skema_ddl(kolom))
                  .option("header", "true").option("quote", '"').option("escape", '"')
                  .option("dateFormat", "yyyy-MM-dd").option("mode", "FAILFAST")
                  .csv(sumber))
            target = "%s/%s" % (tujuan, nama)
            t0 = time.time()
            try:
                (df.write.mode("append" if args.tambah else "overwrite")
                 .option("compression", args.kompresi).parquet(target))
            except Exception as e:  # noqa: BLE001
                pesan = str(e).strip().splitlines()[0] if str(e).strip() else repr(e)
                raise SystemExit("Gagal menulis %s\n%s\nCek: kontainer namenode dan datanode jalan "
                                 "(docker compose ps), dan tunggu 30-60 detik setelah 'up' sebelum menulis."
                                 % (target, pesan))
            n = spark.read.parquet(target).count()
            total[nama] = n
            print("%s: %d baris ditulis ke %s (%.1f detik)" % (nama, n, target, time.time() - t0), flush=True)

        h = baca_harapan(args.scale)
        if h and not args.tambah and not args.folder:
            if (total["annotations"], total["patches"]) != tuple(h):
                raise SystemExit("Jumlah baris tidak sama dengan harapan %s: annotations %d (harap %d), "
                                 "patches %d (harap %d). Jalankan python data/cek_data.py --skala %s di komputermu."
                                 % (args.scale, total["annotations"], h[0], total["patches"], h[1], args.scale))
            print("Jumlah baris cocok dengan harapan %s (annotations %d, patches %d)." % (args.scale, h[0], h[1]))
        print("Selesai dalam %.1f detik (kompresi %s)." % (time.time() - mulai, args.kompresi))
        print("Catat waktunya di komputermu:  python bench/catat.py waktu --store spark --skala %s "
              "--jenis muat --detik %.1f" % (args.scale, time.time() - mulai))
    finally:
        spark.stop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
