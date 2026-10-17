#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Catat waktu muat/indeks dan ukuran penyimpanan (beban kerja W7 dan W8) ke results/.

Satu berkas per penyimpanan, supaya dua orang yang mencatat bersamaan tidak bentrok di Git:
  results/pengukuran_mongodb.csv, pengukuran_postgis.csv, pengukuran_spark.csv, pengukuran_mentah.csv
Kolom: tanggal, penyimpanan, skala, jenis, objek, nilai, satuan, catatan

Cara pakai (dari akar repo, PowerShell):
  # 1. Waktu (detik). CARA TERMUDAH: tulis 'catat.py ukur ...' di DEPAN perintahnya; perintah dijalankan
  #    seperti biasa, waktunya diukur dan dicatat otomatis bila perintah berhasil:
  python bench/catat.py ukur --store mongodb --skala S1 --jenis muat --objek annotations docker exec sen12ls-mongo mongoimport ...
  #    jenis: muat | indeks | tambah_batch      (objek bebas, mis. annotations, patches)
  #    Cara manual (bila sudah punya angkanya):
  python bench/catat.py waktu --store mongodb --skala S1 --jenis muat --detik 12.4
  # 2. Ukuran di disk, DIUKUR OTOMATIS lewat docker exec (kontainernya harus jalan):
  python bench/catat.py ukuran --store mongodb --skala S1
  python bench/catat.py ukuran --store postgis --skala S1
  python bench/catat.py ukuran --store spark   --skala S1      (ukuran Parquet di HDFS)
  python bench/catat.py ukuran --store mentah  --skala S1      (berkas CSV dan NDJSON, tanpa Docker)
  #    Bila otomatis gagal: tambahkan --mb ANGKA dan --objek NAMA untuk mengisi sendiri.
  # 3. Lihat tabel banding semua penyimpanan:
  python bench/catat.py tampil
"""
import argparse
import csv
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"
OUT = ROOT / "data" / "out"
KOLOM = ["tanggal", "penyimpanan", "skala", "jenis", "objek", "nilai", "satuan", "catatan"]
STORES = ["mongodb", "postgis", "spark", "mentah"]
SKALA = ["S1", "S10", "S100"]
MIB = 1024 * 1024

try:
    sys.stdout.reconfigure(errors="replace")
except Exception:
    pass


def angka(teks):
    """Terima '12,5' dan '12.5'."""
    try:
        return float(str(teks).strip().replace(",", "."))
    except ValueError:
        raise SystemExit("'%s' bukan angka." % teks)


def tambah(store, baris):
    """Tambahkan baris ke results/pengukuran_<store>.csv (buat bila belum ada)."""
    RESULTS.mkdir(parents=True, exist_ok=True)
    jalur = RESULTS / ("pengukuran_%s.csv" % store)
    baru = not jalur.exists()
    with open(jalur, "a", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        if baru:
            w.writerow(KOLOM)
        w.writerows(baris)
    return jalur


def baris_baru(store, skala, jenis, objek, nilai, satuan, catatan=""):
    return [datetime.now().strftime("%Y-%m-%d %H:%M"), store, skala, jenis, objek,
            ("%.3f" % nilai), satuan, catatan]


# ------------------------------------------------------------------ pengurai keluaran perintah
def urai_mongo(teks):
    """Keluaran mongosh: baris JSON {"n":..,"data":..,"storage":..,"idx":..,"tot":..} (byte)."""
    for baris in reversed(teks.strip().splitlines()):
        baris = baris.strip()
        if baris.startswith("{") and baris.endswith("}"):
            d = json.loads(baris)
            return {k: float(d[k]) for k in ("n", "data", "storage", "idx", "tot")}
    raise ValueError("keluaran mongosh tidak berisi JSON: %r" % teks[:200])


def urai_pg(teks):
    """Keluaran psql -At: 'relasi|indeks|total' (byte)."""
    for baris in reversed(teks.strip().splitlines()):
        bagian = baris.strip().split("|")
        if len(bagian) == 3 and all(b.strip().isdigit() for b in bagian):
            return tuple(float(b) for b in bagian)
    raise ValueError("keluaran psql tidak berisi tiga angka: %r" % teks[:200])


def urai_hdfs(teks):
    """Keluaran 'hdfs dfs -du -s PATH': 'ukuran ukuran_dengan_replika PATH' (byte)."""
    for baris in teks.strip().splitlines():
        bagian = baris.split()
        if len(bagian) >= 3 and bagian[0].isdigit() and bagian[1].isdigit():
            return float(bagian[0]), float(bagian[1])
    raise ValueError("keluaran hdfs tidak berisi ukuran: %r" % teks[:200])


def jalankan(perintah):
    try:
        h = subprocess.run(perintah, capture_output=True, text=True, timeout=180)
    except FileNotFoundError:
        raise SystemExit("Perintah 'docker' tidak ditemukan. Buka Docker Desktop dulu.")
    except subprocess.TimeoutExpired:
        raise SystemExit("Perintah terlalu lama: " + " ".join(perintah))
    if h.returncode != 0:
        raise SystemExit("Perintah gagal (kode %d): %s\n%s\nKontainer jalan? docker compose ps"
                         % (h.returncode, " ".join(perintah), (h.stderr or h.stdout).strip()[:400]))
    return h.stdout


# ------------------------------------------------------------------ pengukuran otomatis
def ukur_mongo(skala):
    baris = []
    for koleksi in ("annotations", "patches"):
        js = ("const s=db.getSiblingDB('sen12ls').%s.stats();"
              "print(JSON.stringify({n:Number(s.count),data:Number(s.size),"
              "storage:Number(s.storageSize),idx:Number(s.totalIndexSize),tot:Number(s.totalSize)}))"
              % koleksi)
        d = urai_mongo(jalankan(["docker", "exec", "sen12ls-mongo", "mongosh", "--quiet", "--eval", js]))
        baris += [baris_baru("mongodb", skala, "jumlah_dokumen", koleksi, d["n"], "dokumen"),
                  baris_baru("mongodb", skala, "ukuran_data_tak_terkompres", koleksi, d["data"] / MIB, "MiB"),
                  baris_baru("mongodb", skala, "ukuran_data_di_disk", koleksi, d["storage"] / MIB, "MiB"),
                  baris_baru("mongodb", skala, "ukuran_indeks", koleksi, d["idx"] / MIB, "MiB"),
                  baris_baru("mongodb", skala, "ukuran_total", koleksi, d["tot"] / MIB, "MiB",
                             "storageSize + totalIndexSize")]
    return baris


def ukur_pg(skala):
    baris = []
    for tabel in ("annotations", "patches"):
        sql = ("SELECT pg_relation_size('%s'), pg_indexes_size('%s'), pg_total_relation_size('%s')"
               % (tabel, tabel, tabel))
        r, i, t = urai_pg(jalankan(["docker", "exec", "sen12ls-postgis", "psql", "-U", "postgres",
                                    "-d", "sen12ls", "-At", "-c", sql]))
        baris += [baris_baru("postgis", skala, "ukuran_data_di_disk", tabel, r / MIB, "MiB"),
                  baris_baru("postgis", skala, "ukuran_indeks", tabel, i / MIB, "MiB"),
                  baris_baru("postgis", skala, "ukuran_total", tabel, t / MIB, "MiB",
                             "pg_total_relation_size (termasuk TOAST)")]
    return baris


def ukur_hdfs(skala):
    baris = []
    for nama in ("annotations", "patches"):
        jalur = "/data/sen12ls/parquet/%s/%s" % (skala.lower(), nama)
        s, sr = urai_hdfs(jalankan(["docker", "exec", "sen12ls-namenode", "hdfs", "dfs", "-du", "-s", jalur]))
        baris += [baris_baru("spark", skala, "ukuran_total", nama, s / MIB, "MiB", "satu salinan, tanpa replikasi"),
                  baris_baru("spark", skala, "ukuran_dengan_replika", nama, sr / MIB, "MiB", "replikasi 2")]
    return baris


def ukur_mentah(skala):
    folder = OUT / skala.lower()
    baris = []
    for nama in ("annotations.csv", "annotations.ndjson", "patches.csv", "patches.ndjson"):
        p = folder / nama
        if not p.is_file():
            raise SystemExit("Berkas %s belum ada. Jalankan dulu converter/generator." % p)
        baris.append(baris_baru("mentah", skala, "ukuran_total", nama, p.stat().st_size / MIB, "MiB"))
    return baris


UKUR = {"mongodb": ukur_mongo, "postgis": ukur_pg, "spark": ukur_hdfs, "mentah": ukur_mentah}


# ------------------------------------------------------------------ ukur waktu perintah
def ukur_perintah(args):
    perintah = list(args.perintah)
    if perintah and perintah[0] == "--":
        perintah = perintah[1:]
    if not perintah:
        raise SystemExit("Tulis perintah yang mau diukur setelah pilihan, "
                         "mis.: ... --jenis muat docker exec sen12ls-mongo mongoimport ...")
    t0 = time.perf_counter()
    try:
        kode = subprocess.call(perintah)
    except FileNotFoundError:
        raise SystemExit("Perintah '%s' tidak ditemukan." % perintah[0])
    detik = time.perf_counter() - t0
    if kode != 0:
        print("\nPerintah berakhir dengan kode %d, jadi waktunya TIDAK dicatat." % kode)
        return kode
    jalur = tambah(args.store, [baris_baru(args.store, args.skala, args.jenis, args.objek, detik, "detik",
                                           args.catatan)])
    print("\nTercatat: %s %s %s (%s) = %.1f detik  ->  %s" % (args.store, args.skala, args.jenis,
                                                            args.objek, detik, jalur))
    return 0


# ------------------------------------------------------------------ tampil
def tampil():
    semua = []
    for store in STORES:
        p = RESULTS / ("pengukuran_%s.csv" % store)
        if p.is_file():
            with open(p, encoding="utf-8", newline="") as f:
                semua += list(csv.DictReader(f))
    if not semua:
        print("Belum ada pencatatan di results/pengukuran_*.csv")
        return 0
    terbaru = {}
    for r in semua:                       # catatan paling akhir menang
        terbaru[(r["jenis"], r["objek"], r["skala"], r["penyimpanan"])] = r
    kunci = sorted({(j, o, s) for (j, o, s, _) in terbaru},
                   key=lambda k: (k[0], k[1], SKALA.index(k[2]) if k[2] in SKALA else 9))
    print("%-28s %-20s %-5s " % ("jenis", "objek", "skala") + " ".join("%10s" % s for s in STORES))
    for j, o, s in kunci:
        sel = []
        for st in STORES:
            r = terbaru.get((j, o, s, st))
            sel.append("%10s" % (("%.1f" % float(r["nilai"])) if r else "-"))
        print("%-28s %-20s %-5s " % (j, o, s) + " ".join(sel))
    print("(MiB, detik, atau jumlah menurut jenisnya; '-' = belum dicatat)")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="Catat waktu muat/indeks dan ukuran penyimpanan.")
    sub = ap.add_subparsers(dest="aksi", required=True)
    w = sub.add_parser("waktu", help="catat satu waktu (detik)")
    w.add_argument("--store", required=True, choices=STORES[:3])
    w.add_argument("--skala", required=True, choices=SKALA)
    w.add_argument("--jenis", required=True, choices=["muat", "indeks", "tambah_batch"])
    w.add_argument("--detik", required=True)
    w.add_argument("--objek", default="annotations+patches")
    w.add_argument("--catatan", default="")
    k = sub.add_parser("ukur", help="jalankan perintah, ukur waktunya, catat otomatis")
    k.add_argument("--store", required=True, choices=STORES[:3])
    k.add_argument("--skala", required=True, choices=SKALA)
    k.add_argument("--jenis", required=True, choices=["muat", "indeks", "tambah_batch"])
    k.add_argument("--objek", default="annotations+patches")
    k.add_argument("--catatan", default="")
    k.add_argument("perintah", nargs=argparse.REMAINDER, help="perintah yang diukur")
    u = sub.add_parser("ukuran", help="catat ukuran di disk (otomatis atau manual)")
    u.add_argument("--store", required=True, choices=STORES)
    u.add_argument("--skala", required=True, choices=SKALA)
    u.add_argument("--mb", help="isi manual (MiB); wajib bersama --objek")
    u.add_argument("--objek", help="nama objek untuk isian manual")
    u.add_argument("--catatan", default="")
    sub.add_parser("tampil", help="tampilkan tabel banding semua penyimpanan")
    args = ap.parse_args(argv)

    if args.aksi == "tampil":
        return tampil()
    if args.aksi == "ukur":
        return ukur_perintah(args)
    if args.aksi == "waktu":
        detik = angka(args.detik)
        if detik < 0:
            raise SystemExit("Waktu tidak boleh negatif.")
        jalur = tambah(args.store, [baris_baru(args.store, args.skala, args.jenis, args.objek,
                                               detik, "detik", args.catatan)])
        print("Tercatat: %s %s %s = %.1f detik  ->  %s" % (args.store, args.skala, args.jenis, detik, jalur))
        return 0
    if args.mb is not None:
        if not args.objek:
            raise SystemExit("Isian manual perlu --objek (mis. annotations).")
        baris = [baris_baru(args.store, args.skala, "ukuran_total", args.objek, angka(args.mb), "MiB",
                            ("manual " + args.catatan).strip())]
    else:
        baris = UKUR[args.store](args.skala)
        if args.catatan:
            for b in baris:
                b[7] = (b[7] + " " + args.catatan).strip()
    jalur = tambah(args.store, baris)
    for b in baris:
        print("  %-28s %-12s %12s %s" % (b[3], b[4], b[5], b[6]))
    print("Tercatat %d baris  ->  %s" % (len(baris), jalur))
    return 0


if __name__ == "__main__":
    sys.exit(main())
