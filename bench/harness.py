#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Harness uji: ukur waktu kueri W1 sampai W6 di MongoDB, PostGIS, atau Spark SQL.

Satu baris CSV = satu eksekusi kueri (satu titik dari bench/points.json, atau satu id untuk W1).
Hasil disimpan di results/YYYYMMDD_<penyimpanan>_<beban>_<skala>.csv
Definisi kueri ada di bench/kueri.py (dipakai juga oleh Spark, supaya ketiganya adil).

Contoh (dari akar repo, PowerShell):
  python bench/harness.py --store mongodb --workload W3 --scale S1
  python bench/harness.py --store postgis --workload W4 --scale S10 --repeats 3
  python bench/harness.py --store spark   --workload W2 --scale S1
  python bench/harness.py --store mongodb --workload W1 --scale S10 --clients 10

Persiapan sekali:  python -m pip install pymongo "psycopg[binary]"
Mode warm (bawaan): satu putaran pemanasan yang tidak dicatat, lalu --repeats putaran dicatat.
Mode cold: tanpa pemanasan; nyalakan ulang kontainer dulu (docker compose restart).
--clients N (hanya W1; MongoDB dan PostGIS): N klien bersamaan, tiap klien membuka koneksi
sendiri dan menjalankan seluruh daftar id; kolom catatan diisi konkurensi=N.
--limit-titik N: pakai N kueri pertama saja (dianjurkan untuk Spark di S100 yang lambat).
Pagar anti salah label: jumlah baris tabel dicocokkan dengan skala; beda = berhenti
(kecuali --force).
"""
import argparse
import csv
import math
import statistics
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
import kueri  # noqa: E402

try:
    sys.stdout.reconfigure(errors="replace")
except Exception:
    pass

POINTS = ROOT / "bench" / "points.json"
RESULTS = ROOT / "results"

KOLOM = ["penyimpanan", "beban_kerja", "skala", "ulangan", "cold_warm",
         "kueri_id", "waktu_ms", "jumlah_hasil", "catatan"]

MONGO_URI = "mongodb://localhost:27017"
MONGO_DB = "sen12ls"
PG_DSN = "host=localhost port=5433 dbname=sen12ls user=postgres password=postgres"
SPARK_CMD = ["docker", "exec", "sen12ls-spark", "/opt/spark/bin/spark-submit",
             "--master", "local[2]", "--driver-memory", "2g",
             "/hdfs-parquet/run_sql.py"]


def persentil(nilai, q):
    """Persentil metode peringkat terdekat. Contoh: q=95 -> nilai ke-95% dari urutan."""
    urut = sorted(nilai)
    k = math.ceil(q / 100 * len(urut)) - 1
    return urut[max(0, min(len(urut) - 1, k))]


def nama_berkas(store, beban, skala, folder=None):
    """Nama hasil; bila sudah ada, tambahkan _2, _3, dst. supaya tidak menimpa."""
    folder = folder or RESULTS
    tanggal = datetime.now().strftime("%Y%m%d")
    dasar = "%s_%s_%s_%s" % (tanggal, store, beban, skala)
    nama = dasar + ".csv"
    n = 2
    while (Path(folder) / nama).exists():
        nama = "%s_%d.csv" % (dasar, n)
        n += 1
    return nama


def runner_mongodb(beban, par):
    """Kembalikan (fungsi hitung, fungsi kueri, fungsi tutup) untuk MongoDB."""
    try:
        from pymongo import MongoClient
    except ImportError:
        raise SystemExit("pymongo belum terpasang. Jalankan:  python -m pip install pymongo")
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    koleksi = client[MONGO_DB][kueri.tabel_beban(beban)]

    def hitung():
        return koleksi.estimated_document_count()

    def jalankan(q):
        if beban == "W1":
            return len(list(koleksi.find({"_id": q["ann_id"]},
                                         {"location": 1, "event_type": 1, "dates.event": 1})))
        if beban in ("W2", "W3", "W4"):
            return koleksi.count_documents(kueri.filter_mongo(beban, q, par))
        return len(list(koleksi.aggregate(kueri.PIPA_W5 if beban == "W5" else kueri.PIPA_W6)))

    return hitung, jalankan, client.close


def runner_postgis(beban, par):
    """Kembalikan (fungsi hitung, fungsi kueri, fungsi tutup) untuk PostGIS."""
    try:
        import psycopg
    except ImportError:
        raise SystemExit('psycopg belum terpasang. Jalankan:  python -m pip install "psycopg[binary]"')
    conn = psycopg.connect(PG_DSN, autocommit=True)
    sql = kueri.SQL_POSTGIS[beban]
    tabel = kueri.tabel_beban(beban)

    def hitung():
        with conn.cursor() as cur:
            cur.execute("SELECT count(*) FROM " + tabel)
            return cur.fetchone()[0]

    def jalankan(q):
        with conn.cursor() as cur:
            cur.execute(sql, kueri.param_postgis(beban, q, par))
            if beban in ("W2", "W3", "W4"):
                return int(cur.fetchone()[0])
            return len(cur.fetchall())

    return hitung, jalankan, conn.close


RUNNERS = {"mongodb": runner_mongodb, "postgis": runner_postgis}


def jalankan_spark(args, nama):
    """Spark dijalankan di dalam kontainer lewat run_sql.py (format CSV sama persis)."""
    perintah = SPARK_CMD + [
        "--workload", args.workload, "--scale", args.scale,
        "--repeats", str(args.repeats), "--cold-warm", args.cold_warm,
        "--out", "/results/" + nama,
    ]
    if args.first_run_no != 1:
        perintah += ["--first-run-no", str(args.first_run_no)]
    if args.limit_titik:
        perintah += ["--limit-titik", str(args.limit_titik)]
    if args.note:
        perintah += ["--note", args.note]
    if args.force:
        perintah.append("--force")
    print("Menjalankan Spark SQL di kontainer (S10 dan S100 bisa lama):")
    print(" ".join(perintah))
    kode = subprocess.call(perintah)
    if kode != 0:
        raise SystemExit("Spark gagal (kode %d). Cek kontainer: docker compose ps "
                         "di folder hdfs-parquet" % kode)
    print("Selesai. Hasil: results/" + nama)


def tulis_csv(jalur, baris):
    Path(jalur).parent.mkdir(parents=True, exist_ok=True)
    with open(jalur, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(KOLOM)
        w.writerows(baris)


def ringkas(args, waktu, jumlah_per_kueri, jalur):
    ada = sum(1 for n in jumlah_per_kueri if n > 0)
    galat = sum(1 for n in jumlah_per_kueri if n < 0)
    print()
    print("Ringkasan %s %s %s (%s, %d ulangan x %d kueri = %d eksekusi)" % (
        args.store, args.workload, args.scale, args.cold_warm, args.repeats,
        len(jumlah_per_kueri), len(waktu)))
    print("  median : %.3f ms" % statistics.median(waktu))
    print("  p95    : %.3f ms" % persentil(waktu, 95))
    print("  p99    : %.3f ms" % persentil(waktu, 99))
    print("  rata2  : %.3f ms" % statistics.mean(waktu))
    print("  hasil  : %d per putaran; %d dari %d kueri punya hasil%s" % (
        sum(n for n in jumlah_per_kueri if n > 0), ada, len(jumlah_per_kueri),
        "; %d GALAT" % galat if galat else ""))
    print("Berkas   :", jalur)


def eksekusi(jalankan, q):
    """(milidetik, jumlah hasil, catatan galat). Galat dicatat sebagai jumlah -1, tidak menghentikan uji."""
    t0 = time.perf_counter()
    try:
        n, galat = jalankan(q), ""
    except Exception as e:  # noqa: BLE001
        n, galat = -1, "GALAT " + str(e).strip().replace("\n", " ")[:80]
    return (time.perf_counter() - t0) * 1000, n, galat


def satu_klien(args, par, daftar, jalankan):
    baris, pertama = [], {}
    awal = args.first_run_no
    for ulangan in range(awal, awal + args.repeats):
        for q in daftar:
            ms, n, galat = eksekusi(jalankan, q)
            baris.append([args.store, args.workload, args.scale, ulangan, args.cold_warm,
                          q["id"], "%.3f" % ms, n, (args.note + " " + galat).strip()])
            if ulangan == awal:
                pertama[q["id"]] = n
        print("Ulangan %d selesai (%d kueri)" % (ulangan, len(daftar)), flush=True)
    return baris, pertama


def banyak_klien(args, par, daftar):
    """N utas, tiap utas dengan koneksi sendiri; semua mulai bersamaan setelah pemanasan."""
    n_klien = args.clients
    kunci = threading.Lock()
    gerbang = threading.Barrier(n_klien)
    semua, pertama, masalah = [], {}, []
    catatan = ("konkurensi=%d %s" % (n_klien, args.note)).strip()

    def pekerja():
        try:
            _hitung, jalankan, tutup = RUNNERS[args.store](args.workload, par)
        except BaseException as e:  # noqa: BLE001
            masalah.append(e)
            gerbang.abort()
            return
        try:
            if args.cold_warm == "warm":
                for q in daftar:
                    jalankan(q)
            gerbang.wait()
            lokal, awal = [], args.first_run_no
            for ulangan in range(awal, awal + args.repeats):
                for q in daftar:
                    ms, n, galat = eksekusi(jalankan, q)
                    lokal.append([args.store, args.workload, args.scale, ulangan, args.cold_warm,
                                  q["id"], "%.3f" % ms, n, (catatan + " " + galat).strip()])
            with kunci:
                semua.extend(lokal)
                for b in lokal:
                    if b[3] == awal:
                        pertama[b[5]] = b[7]
        except threading.BrokenBarrierError:
            pass
        except BaseException as e:  # noqa: BLE001
            masalah.append(e)
        finally:
            tutup()

    utas = [threading.Thread(target=pekerja) for _ in range(n_klien)]
    awal_total = time.perf_counter()
    for u in utas:
        u.start()
    for u in utas:
        u.join()
    if masalah:
        raise SystemExit("Uji banyak klien gagal: %s" % masalah[0])
    detik = time.perf_counter() - awal_total
    print("%d klien selesai dalam %.1f detik (termasuk pemanasan dan koneksi)" % (n_klien, detik))
    return semua, pertama


def main(argv=None):
    ap = argparse.ArgumentParser(description="Harness uji W1 sampai W6.")
    ap.add_argument("--store", required=True, choices=["mongodb", "postgis", "spark"])
    ap.add_argument("--workload", required=True, choices=kueri.BEBAN)
    ap.add_argument("--scale", required=True, choices=list(kueri.FAKTOR))
    ap.add_argument("--repeats", type=int, default=3, help="jumlah ulangan (bawaan 3)")
    ap.add_argument("--cold-warm", dest="cold_warm", choices=["warm", "cold"], default="warm")
    ap.add_argument("--first-run-no", dest="first_run_no", type=int, default=1,
                    help="nomor ulangan pertama (untuk mengulang mode cold)")
    ap.add_argument("--clients", type=int, default=1, help="jumlah klien bersamaan (hanya W1)")
    ap.add_argument("--limit-titik", dest="limit_titik", type=int, default=0,
                    help="pakai N kueri pertama saja")
    ap.add_argument("--note", default="", help="catatan bebas, masuk kolom catatan")
    ap.add_argument("--force", action="store_true", help="lewati pemeriksaan jumlah data")
    ap.add_argument("--points", default=str(POINTS), help=argparse.SUPPRESS)
    ap.add_argument("--results", default=str(RESULTS), help=argparse.SUPPRESS)
    args = ap.parse_args(argv)
    if args.repeats < 1:
        raise SystemExit("--repeats minimal 1")
    if args.clients < 1:
        raise SystemExit("--clients minimal 1")
    if args.clients > 1 and args.workload != "W1":
        raise SystemExit("--clients hanya untuk W1.")
    if args.clients > 1 and args.store == "spark":
        raise SystemExit("--clients tidak berlaku untuk spark (satu klien).")

    hasil_dir = Path(args.results)
    hasil_dir.mkdir(parents=True, exist_ok=True)
    nama = nama_berkas(args.store, args.workload, args.scale, hasil_dir)
    if args.store == "spark":
        jalankan_spark(args, nama)
        return

    par, titik = dict(kueri.PARAMETER_BAWAAN), []
    if args.workload in ("W2", "W3", "W4"):
        if not Path(args.points).exists():
            raise SystemExit("Berkas bench/points.json belum ada.\n"
                             "Jalankan dulu: python bench/make_points.py")
        par, titik = kueri.muat_titik(args.points)
    daftar = kueri.daftar_kueri(args.workload, args.scale, titik)
    if args.limit_titik:
        daftar = daftar[:args.limit_titik]

    hitung, jalankan, tutup = RUNNERS[args.store](args.workload, par)
    try:
        try:
            total = hitung()
        except Exception as e:  # noqa: BLE001
            raise SystemExit("Tidak bisa terhubung ke %s: %s\nPastikan kontainer jalan: "
                             "docker compose ps" % (args.store, e))
        harap_a, harap_p = kueri.harapan(args.scale)
        harapan = harap_p if args.workload == "W6" else harap_a
        print("Jumlah data di %s (%s): %d (harapan untuk %s: %d)" % (
            args.store, kueri.tabel_beban(args.workload), total, args.scale, harapan))
        if total != harapan and not args.force:
            raise SystemExit("Jumlah data tidak cocok. Muat skala %s dulu, atau "
                             "jalankan lagi dengan --force." % args.scale)

        if args.clients > 1:
            tutup()
            tutup = lambda: None  # noqa: E731
            baris, pertama = banyak_klien(args, par, daftar)
        else:
            if args.cold_warm == "warm":
                print("Pemanasan: satu putaran %d kueri (tidak dicatat)..." % len(daftar))
                for q in daftar:
                    jalankan(q)
            else:
                print("Mode cold: tanpa pemanasan. Pastikan kontainer baru dinyalakan ulang.")
            baris, pertama = satu_klien(args, par, daftar, jalankan)

        jalur = hasil_dir / nama
        tulis_csv(jalur, baris)
        ringkas(args, [float(b[6]) for b in baris], list(pertama.values()), jalur)
    finally:
        tutup()


if __name__ == "__main__":
    main()
