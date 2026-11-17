#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tahap pemrosesan dan analitik di Spark atas Parquet di HDFS. Berjalan DI DALAM kontainer spark.

Perintah (PowerShell; tulis dalam SATU baris):
  docker exec sen12ls-spark /opt/spark/bin/spark-submit --master "local[2]" --driver-memory 2g
      /analitik/spark_pipeline.py --skala S1 --ulangan 3

Yang dikerjakan (satu putaran):
  1. etl      kueri SQL_PERKAYA membuat tabel turunan ann_kaya (jenis, tahun, bulan, hemisfer, selang
              waktu citra, dekade luas, sel 0,1 derajat) dari Parquet mentah, lalu MENULIS-nya ke HDFS
              (hdfs://namenode:8020/data/sen12ls/analitik/<skala>/annotations_kaya) dan membacanya lagi
  2. analitik 14 kueri di kueri_analitik.ANALISIS (q0..q2 pemeriksaan data, a1..a8 analisis isi)
  3. ekspor   hasil kueri ditulis sebagai CSV di /results/analitik/<SKALA>/
Waktu tiap tahap dicatat ke /results/analitik/waktu_pemrosesan.csv (ditambahkan di akhir berkas).
Ulangan pertama dalam satu proses berlabel cold (JVM baru), sisanya warm.

Pilihan:
  --ulangan N        jumlah putaran penuh dalam satu sesi Spark (bawaan 1)
  --tanpa-etl        lewati penulisan ann_kaya ke HDFS; kueri dijalankan langsung atas Parquet mentah
  --hanya-asli       hanya baris sim_batch = 0 (bagian data nyata); hasil S10/S100 harus sama dengan S1.
                     Hasil ke folder <SKALA>_asli dan waktu TIDAK dicatat ke berkas waktu bawaan
  --keluar FOLDER    folder hasil (bawaan /results/analitik)
  --base, --base-etl folder Parquet mentah dan Parquet turunan di HDFS
  --force            lewati pemeriksaan jumlah baris terhadap harapan skala
Sesudah selesai, bandingkan dengan acuan Python di komputermu:  python analitik\\cocokkan.py
Hanya pyspark dan Python bawaan (Python 3.8 di kontainer).
"""
import argparse
import csv
import os
import statistics
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, "/bench")
import kueri_analitik as ka  # noqa: E402

HDFS_BASE = "hdfs://namenode:8020/data/sen12ls/parquet"
HDFS_ETL = "hdfs://namenode:8020/data/sen12ls/analitik"
HASIL = "/results/analitik"
KOLOM_WAKTU = ["sesi", "skala", "ulangan", "cold_warm", "tahap", "waktu_ms", "n_baris", "n_anotasi", "catatan"]


def harapan(skala):
    """(jumlah anotasi, jumlah patch) menurut bench/kueri.py (dipasang di /bench), atau None."""
    try:
        import kueri
        return kueri.harapan(skala)
    except Exception:  # noqa: BLE001
        return None


def pesan_galat(e):
    teks = str(e).strip()
    return teks.splitlines()[0] if teks else repr(e)


def baca_mentah(spark, base, skala, hanya_asli):
    """Daftarkan view annotations dan patches dari Parquet mentah; kembalikan (n_anotasi, n_patch)."""
    for tabel in ("annotations", "patches"):
        folder = "%s/%s/%s" % (base.rstrip("/"), skala.lower(), tabel)
        try:
            df = spark.read.parquet(folder)
            if hanya_asli:
                df.createOrReplaceTempView(tabel + "_semua")
                spark.sql("SELECT * FROM %s_semua WHERE sim_batch = 0" % tabel).createOrReplaceTempView(tabel)
            else:
                df.createOrReplaceTempView(tabel)
        except Exception as e:  # noqa: BLE001
            raise SystemExit("Tidak bisa membaca %s\n%s\nCek: kontainer namenode dan datanode jalan, dan Parquet "
                             "sudah dibuat (csv_to_parquet.py --scale %s)" % (folder, pesan_galat(e), skala))
    return spark.table("annotations").count(), spark.table("patches").count()


def putaran(spark, args, tujuan_etl, folder_hasil):
    """Satu putaran penuh. Kembalikan daftar (tahap, ms, n_baris) dan tabel hasil {nama: (kolom, baris)}."""
    catat, hasil = [], {}
    t_total = time.perf_counter()

    if not args.tanpa_etl:
        t0 = time.perf_counter()
        try:
            (spark.sql(ka.SQL_PERKAYA).write.mode("overwrite")
             .option("compression", args.kompresi).parquet(tujuan_etl))
            kaya = spark.read.parquet(tujuan_etl)
            kaya.createOrReplaceTempView(ka.TABEL_KAYA)
            n_kaya = kaya.count()
        except Exception as e:  # noqa: BLE001
            raise SystemExit("Gagal menulis atau membaca tabel turunan %s\n%s\nCek: namenode dan datanode jalan "
                             "(docker compose ps). Atau jalankan lagi dengan --tanpa-etl."
                             % (tujuan_etl, pesan_galat(e)))
        catat.append(("etl", (time.perf_counter() - t0) * 1000, n_kaya))
        n_ann = spark.table("annotations").count()
        if n_kaya != n_ann:
            raise SystemExit("Tabel turunan berisi %d baris, harusnya %d (sama dengan annotations)." % (n_kaya, n_ann))
    else:
        spark.sql(ka.SQL_PERKAYA).createOrReplaceTempView(ka.TABEL_KAYA)

    for nama, judul, kunci, sql in ka.ANALISIS:
        t0 = time.perf_counter()
        try:
            kolom, baris = ka.ke_tabel(spark.sql(sql))
        except Exception as e:  # noqa: BLE001
            raise SystemExit("Kueri %s gagal: %s\n(Kirim pesan ini ke Wildan; kemungkinan beda dialek Spark.)"
                             % (nama, pesan_galat(e)))
        catat.append((nama, (time.perf_counter() - t0) * 1000, len(baris)))
        hasil[nama] = (kolom, baris)

    t0 = time.perf_counter()
    for nama in ka.NAMA_ANALISIS:
        kolom, baris = hasil[nama]
        ka.tulis_csv(os.path.join(folder_hasil, nama + ".csv"), kolom, baris)
    catat.append(("ekspor", (time.perf_counter() - t0) * 1000, len(hasil)))
    catat.append(("total", (time.perf_counter() - t_total) * 1000, 0))
    return catat, hasil


def tambah_waktu(jalur, baris):
    folder = os.path.dirname(os.path.abspath(jalur))
    if not os.path.isdir(folder):
        os.makedirs(folder)
    baru = not os.path.exists(jalur)
    with open(jalur, "a", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        if baru:
            w.writerow(KOLOM_WAKTU)
        w.writerows(baris)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Pemrosesan dan analitik Sen12Landslides di Spark.")
    ap.add_argument("--skala", required=True, choices=["S1", "S10", "S100"])
    ap.add_argument("--ulangan", type=int, default=1)
    ap.add_argument("--keluar", default=HASIL)
    ap.add_argument("--base", default=HDFS_BASE)
    ap.add_argument("--base-etl", dest="base_etl", default=HDFS_ETL)
    ap.add_argument("--tanpa-etl", dest="tanpa_etl", action="store_true")
    ap.add_argument("--hanya-asli", dest="hanya_asli", action="store_true")
    ap.add_argument("--kompresi", default="zstd", choices=["zstd", "snappy", "gzip", "none"])
    ap.add_argument("--waktu", help="berkas CSV waktu (bawaan <keluar>/waktu_pemrosesan.csv)")
    ap.add_argument("--catatan", default="")
    ap.add_argument("--force", action="store_true", help="lewati pemeriksaan jumlah baris")
    args = ap.parse_args(argv)
    if args.ulangan < 1:
        raise SystemExit("--ulangan minimal 1")

    nama_skala = args.skala + ("_asli" if args.hanya_asli else "")
    folder_hasil = os.path.join(args.keluar, nama_skala)
    tujuan_etl = "%s/%s/annotations_kaya" % (args.base_etl.rstrip("/"), nama_skala.lower())
    jalur_waktu = args.waktu or (None if args.hanya_asli else os.path.join(args.keluar, "waktu_pemrosesan.csv"))
    catatan = " ".join(x for x in (("tanpa-etl" if args.tanpa_etl else ""),
                                   ("hanya-asli" if args.hanya_asli else ""), args.catatan) if x)

    from pyspark.sql import SparkSession
    spark = (SparkSession.builder.appName("sen12ls-analitik-%s" % nama_skala)
             .config("spark.sql.shuffle.partitions", "4")
             .config("spark.ui.showConsoleProgress", "false")
             .getOrCreate())
    spark.sparkContext.setLogLevel("WARN")
    try:
        n_ann, n_pat = baca_mentah(spark, args.base, args.skala, args.hanya_asli)
        h = harapan(args.skala)
        print("Data mentah %s%s: annotations %d, patches %d" % (
            args.skala, " (hanya sim_batch=0)" if args.hanya_asli else "", n_ann, n_pat), flush=True)
        if h and not args.hanya_asli and not args.force and (n_ann, n_pat) != tuple(h):
            raise SystemExit("Jumlah baris tidak sama dengan harapan %s: annotations %d (harap %d), patches %d "
                             "(harap %d). Buat Parquet skala %s dulu (csv_to_parquet.py) atau pakai --force."
                             % (args.skala, n_ann, h[0], n_pat, h[1], args.skala))

        sesi = int(time.time())
        semua, baris_waktu = {}, []
        for ul in range(1, args.ulangan + 1):
            cw = "cold" if ul == 1 else "warm"
            catat, hasil = putaran(spark, args, tujuan_etl, folder_hasil)
            for tahap, ms, n in catat:
                baris_waktu.append([sesi, args.skala, ul, cw, tahap, "%.3f" % ms, n, n_ann, catatan])
                semua.setdefault(tahap, []).append((cw, ms))
            total = [ms for t, ms, n in catat if t == "total"][0]
            print("Putaran %d/%d (%s): %.1f detik" % (ul, args.ulangan, cw, total / 1000.0), flush=True)

        if jalur_waktu:
            tambah_waktu(jalur_waktu, baris_waktu)
        print()
        print("%-22s %12s %14s" % ("tahap", "cold (ms)", "median warm (ms)"))
        urut = (["etl"] if not args.tanpa_etl else []) + ka.NAMA_ANALISIS + ["ekspor", "total"]
        for tahap in urut:
            dingin = [ms for cw, ms in semua[tahap] if cw == "cold"]
            hangat = [ms for cw, ms in semua[tahap] if cw == "warm"]
            print("%-22s %12.1f %14s" % (tahap, dingin[0], "%.1f" % statistics.median(hangat) if hangat else "-"))
        print()
        total_ms = statistics.median([ms for cw, ms in semua["total"] if cw == "warm"] or [semua["total"][0][1]])
        print("Total per putaran: %.1f detik untuk %d anotasi (%.0f anotasi/detik)"
              % (total_ms / 1000.0, n_ann, n_ann / (total_ms / 1000.0) if total_ms else 0))
        print("Tabel hasil : %s (%d berkas CSV)" % (folder_hasil, len(ka.NAMA_ANALISIS)))
        if jalur_waktu:
            print("Waktu       : %s (ditambahkan)" % jalur_waktu)
        else:
            print("Waktu       : tidak dicatat (mode --hanya-asli tanpa --waktu)")
        # jalur di Windows: /results/analitik/S1 di kontainer = results\analitik\S1 di folder repo
        jalur_win = folder_hasil[1:] if folder_hasil.startswith("/results/") else folder_hasil
        jalur_win = jalur_win.replace("/", "\\")
        print("Berikutnya  : python analitik\\cocokkan.py --hasil %s" % jalur_win)
        if not args.hanya_asli and args.skala != "S1":
            print("              (acuan %s dipilih otomatis dari nama folder; uji konsistensi bagian data nyata: "
                  "ulangi dengan --hanya-asli)" % ("referensi_" + args.skala))
    finally:
        spark.stop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
