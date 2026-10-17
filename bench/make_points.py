#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Buat bench/points.json: 100 titik uji tetap untuk beban kerja W2, W3, dan W4.

Isi: 70 titik "di dalam" dan 30 titik "di luar".
  * Di dalam: titik pusat sebuah anotasi nyata yang punya event_date. Anotasi dipilih
    bergilir menurut lokasi (16 lokasi, urut abjad), jadi lokasi kecil seperti Nepal ikut
    teruji, bukan hanya Italy. Rentang tanggal W3 = event_date +-30 hari; event_type W4 =
    event_type anotasi itu (Rainfall bila kosong). Dijamin ada minimal satu hasil.
  * Di luar: titik acak di dalam rentang bujur-lintang data, minimal 1 derajat dari titik
    pusat anotasi mana pun, dengan rentang tanggal dan event_type acak. Dijamin kosong.
Seed tetap 20261023, jadi hasilnya selalu sama di semua laptop.

Cara pakai (dari akar repo, setelah python data/convert_inventory.py):
  python bench/make_points.py
"""
import csv
import json
import math
import random
import sys
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "out" / "s1" / "annotations.csv"
OUT = ROOT / "bench" / "points.json"
SEED = 20261023
N_DALAM = 70
N_LUAR = 30
HARI = 30
PARAMETER = {"half_titik": 0.01, "half_kotak": 0.1, "hari": HARI, "conf_min": 0.9}
TANGGAL_AWAL = date(2016, 4, 1)
TANGGAL_AKHIR = date(2023, 5, 16)


def baca_anotasi(jalur):
    if not jalur.exists():
        raise SystemExit("Berkas %s belum ada.\nJalankan dulu: python data/convert_inventory.py" % jalur)
    baris = []
    with open(jalur, encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            baris.append((int(r["ann_id"]), r["location"], r["event_type"] or None,
                          r["event_date"] or None, float(r["center_lon"]), float(r["center_lat"])))
    return baris


def main(argv=None, src=SRC, out=OUT):
    rng = random.Random(SEED)
    baris = baca_anotasi(Path(src))
    ber_tanggal = [b for b in baris if b[3]]
    per_lokasi = {}
    for b in ber_tanggal:
        per_lokasi.setdefault(b[1], []).append(b)
    lokasi = sorted(per_lokasi)
    if len(ber_tanggal) < N_DALAM or not lokasi:
        raise SystemExit("Anotasi bertanggal terlalu sedikit (%d) untuk memilih titik." % len(ber_tanggal))

    titik = []
    dipakai = set()
    i = 0
    while len(titik) < N_DALAM:
        daftar = per_lokasi[lokasi[i % len(lokasi)]]
        i += 1
        if i > 100000:
            raise SystemExit("Tidak bisa memilih %d titik unik." % N_DALAM)
        a = rng.choice(daftar)
        if a[0] in dipakai:
            continue
        dipakai.add(a[0])
        d = date.fromisoformat(a[3])
        titik.append({"lon": a[4], "lat": a[5],
                      "date_from": (d - timedelta(days=HARI)).isoformat(),
                      "date_to": (d + timedelta(days=HARI)).isoformat(),
                      "event_type": a[2] or "Rainfall", "inside": True, "ann_id": a[0],
                      "location": a[1]})

    # kisi 1 derajat untuk mencari tetangga terdekat dengan cepat
    sel = {}
    for b in baris:
        sel.setdefault((math.floor(b[4]), math.floor(b[5])), []).append(b)
    lon_min, lon_maks = min(b[4] for b in baris), max(b[4] for b in baris)
    lat_min, lat_maks = min(b[5] for b in baris), max(b[5] for b in baris)
    tipe = sorted({b[2] for b in baris if b[2]}) or ["Rainfall"]
    n_hari = (TANGGAL_AKHIR - TANGGAL_AWAL).days
    percobaan = 0
    luar = 0
    while luar < N_LUAR:
        percobaan += 1
        if percobaan > 100000:
            raise SystemExit("Tidak bisa menemukan %d titik di luar data." % N_LUAR)
        lon = round(rng.uniform(lon_min, lon_maks), 6)
        lat = round(rng.uniform(lat_min, lat_maks), 6)
        gx, gy = math.floor(lon), math.floor(lat)
        dekat = any(abs(b[4] - lon) < 1.0 and abs(b[5] - lat) < 1.0
                    for dx in (-1, 0, 1) for dy in (-1, 0, 1)
                    for b in sel.get((gx + dx, gy + dy), ()))
        if dekat:
            continue
        d = TANGGAL_AWAL + timedelta(days=rng.randint(0, n_hari))
        titik.append({"lon": lon, "lat": lat,
                      "date_from": (d - timedelta(days=HARI)).isoformat(),
                      "date_to": (d + timedelta(days=HARI)).isoformat(),
                      "event_type": rng.choice(tipe), "inside": False, "ann_id": None,
                      "location": None})
        luar += 1

    rng.shuffle(titik)
    kolom = ["id", "lon", "lat", "date_from", "date_to", "event_type", "inside", "ann_id", "location"]
    for no, p in enumerate(titik, 1):
        p["id"] = no
    titik = [{k: p[k] for k in kolom} for p in titik]

    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        json.dump({"seed": SEED, "parameter": PARAMETER, "points": titik}, f, indent=1)
        f.write("\n")
    n_in = sum(1 for p in titik if p["inside"])
    print("Titik dibuat: %d (%d di dalam, %d di luar)" % (len(titik), n_in, len(titik) - n_in))
    print("Berkas:", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
