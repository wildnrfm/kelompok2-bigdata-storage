#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Muat NDJSON ke MongoDB lewat Python (CADANGAN bila mongoimport tidak ada di kontainer).

Cara biasa memakai mongoimport di kontainer (lebih cepat). Pakai skrip ini hanya bila
  docker exec sen12ls-mongo mongoimport --version
menjawab 'executable file not found'.

Contoh (dari akar repo, PowerShell):
  python mongodb/muat_pymongo.py --skala S1
  python mongodb/muat_pymongo.py --folder data/out/batch100 --tambah     (W8: tambah tanpa menghapus)
Prasyarat: python -m pip install pymongo     dan kontainer sen12ls-mongo sudah jalan.
Membaca berkas di komputermu (data/out/...), bukan di kontainer. Tanpa --tambah, koleksi
annotations dan patches dikosongkan dulu (sama seperti mongoimport --drop).
"""
import argparse
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BATCH = 2000

try:
    sys.stdout.reconfigure(errors="replace")
except Exception:
    pass


def muat_berkas(koleksi, jalur, json_util):
    n, batch, t0 = 0, [], time.time()
    with open(jalur, encoding="utf-8") as f:
        for baris in f:
            baris = baris.strip()
            if not baris:
                continue
            batch.append(json_util.loads(baris))
            if len(batch) >= BATCH:
                koleksi.insert_many(batch, ordered=False)
                n += len(batch)
                batch = []
                if n % (BATCH * 50) == 0:
                    print("  %s: %d dokumen (%.0f detik)" % (Path(jalur).name, n, time.time() - t0), flush=True)
    if batch:
        koleksi.insert_many(batch, ordered=False)
        n += len(batch)
    return n


def main(argv=None):
    ap = argparse.ArgumentParser(description="Muat NDJSON ke MongoDB lewat pymongo.")
    ap.add_argument("--skala", choices=["S1", "S10", "S100"], default="S1")
    ap.add_argument("--folder", help="folder berisi annotations.ndjson dan patches.ndjson (menggantikan --skala)")
    ap.add_argument("--tambah", action="store_true", help="tambah ke koleksi yang ada (tanpa mengosongkan)")
    ap.add_argument("--uri", default="mongodb://localhost:27017")
    args = ap.parse_args(argv)
    try:
        from bson import json_util
        from pymongo import MongoClient
    except ImportError:
        raise SystemExit("pymongo belum terpasang. Jalankan:  python -m pip install pymongo")
    folder = Path(args.folder) if args.folder else ROOT / "data" / "out" / args.skala.lower()
    ann, pat = folder / "annotations.ndjson", folder / "patches.ndjson"
    for p in (ann, pat):
        if not p.is_file():
            raise SystemExit("Berkas %s tidak ada." % p)
    db = MongoClient(args.uri, serverSelectionTimeoutMS=5000)["sen12ls"]
    try:
        db.command("ping")
    except Exception as e:  # noqa: BLE001
        raise SystemExit("Tidak bisa terhubung ke MongoDB (%s). Kontainer jalan? docker compose ps" % e)
    if not args.tambah:
        db["annotations"].drop()
        db["patches"].drop()
    t0 = time.time()
    na = muat_berkas(db["annotations"], ann, json_util)
    npat = muat_berkas(db["patches"], pat, json_util)
    detik = time.time() - t0
    print("Selesai: annotations %d, patches %d dokumen dalam %.1f detik." % (na, npat, detik))
    print("Isi koleksi sekarang: annotations %d, patches %d" % (
        db["annotations"].estimated_document_count(), db["patches"].estimated_document_count()))
    print("Catat waktunya:  python bench/catat.py waktu --store mongodb --skala %s --jenis muat --detik %.1f"
          % (args.skala if not args.folder else "S1", detik))
    return 0


if __name__ == "__main__":
    sys.exit(main())
