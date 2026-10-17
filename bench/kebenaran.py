#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""kebenaran.py  --  WASIT jawaban benar W1 sampai W6, dihitung langsung dari annotations.csv.

Tanpa database, tanpa pustaka tambahan. Hasilnya adalah jumlah yang SEHARUSNYA dikeluarkan
MongoDB, PostGIS, dan Spark untuk tiap titik uji; ketiganya dicocokkan dengan wasit ini
(lihat bench/compare_counts.py).

Cara pakai (dari akar repo, PowerShell):
  python bench/kebenaran.py                    semua titik uji, skala S1 (cepat)
  python bench/kebenaran.py --skala S10        skala lain (S100 butuh sekitar 1 GB RAM, beberapa menit)
  python bench/kebenaran.py --tulis            juga tulis bench/benar/W*_S*.csv (untuk compare_counts)
  python bench/kebenaran.py --ann 0            contoh satu anotasi: titik, jendela, dan daftar hasil
  python bench/kebenaran.py --titik 11.8 44.2  jendela W2 di satu titik (tambah --tanggal 2023-05-17
                                               untuk W3, memakai +-30 hari)
"""
import argparse
import csv
import sys
from array import array
from bisect import bisect_left, bisect_right
from collections import Counter
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "data"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import convert_inventory as ci  # noqa: E402
import kueri  # noqa: E402

try:
    sys.stdout.reconfigure(errors="replace")
except Exception:
    pass

POINTS = ROOT / "bench" / "points.json"
BENAR_DIR = ROOT / "bench" / "benar"
KOLOM = ["penyimpanan", "beban_kerja", "skala", "ulangan", "cold_warm", "kueri_id",
         "waktu_ms", "jumlah_hasil", "catatan"]


class Indeks:
    """annotations.csv dalam bentuk larik kolom, diurutkan menurut lintang titik pusat."""

    def __init__(self, folder):
        a = Path(folder) / "annotations.csv"
        if not a.is_file():
            raise SystemExit("Berkas %s belum ada.\nJalankan dulu convert_inventory.py "
                             "(dan generate_scales.py untuk S10/S100)." % a)
        self.id = array("q")
        self.lon, self.lat = array("d"), array("d")
        self.x0, self.y0, self.x1, self.y1 = array("d"), array("d"), array("d"), array("d")
        self.tgl = array("i")                  # ordinal tanggal event_date; 0 = kosong
        self.conf = array("d")                 # -1 = kosong
        self.et = array("b")
        self.kode = {None: 0}
        self.nama = [None]
        self.lokasi = []
        self.agregat5 = Counter()
        for r in ci.baca_anotasi_csv(a):
            self.id.append(r["ann_id"])
            self.lon.append(r["center_lon"])
            self.lat.append(r["center_lat"])
            self.x0.append(r["bbox_min_lon"])
            self.y0.append(r["bbox_min_lat"])
            self.x1.append(r["bbox_max_lon"])
            self.y1.append(r["bbox_max_lat"])
            d = r["event_date"]
            self.tgl.append(d.toordinal() if d else 0)
            self.conf.append(r["event_conf"] if r["event_conf"] is not None else -1.0)
            e = r["event_type"]
            if e not in self.kode:
                self.kode[e] = len(self.nama)
                self.nama.append(e)
            self.et.append(self.kode[e])
            self.lokasi.append(r["location"])
            self.agregat5[(e, d.year if d else None)] += 1
        self.n = len(self.id)
        self.urut = sorted(range(self.n), key=self.lat.__getitem__)
        self.lat_urut = array("d", (self.lat[i] for i in self.urut))
        self.tinggi = max((self.y1[i] - self.y0[i] for i in range(self.n)), default=0.0)

    def cari(self, beban, w, p=None, par=None, daftar=False):
        """Jumlah (atau daftar indeks bila daftar=True) anotasi yang cocok dengan jendela w."""
        x0, y0, x1, y1 = w
        pad = self.tinggi if beban == "W4" else 0.0
        lo = bisect_left(self.lat_urut, y0 - pad)
        hi = bisect_right(self.lat_urut, y1 + pad)
        hasil = []
        n = 0
        if beban == "W3":
            d1 = date.fromisoformat(p["date_from"]).toordinal()
            d2 = date.fromisoformat(p["date_to"]).toordinal()
        if beban == "W4":
            kode = self.kode.get(p["event_type"], -1)
            conf_min = par["conf_min"]
        for k in range(lo, hi):
            i = self.urut[k]
            if beban in ("W2", "W3"):
                if not (x0 <= self.lon[i] <= x1):
                    continue
                if beban == "W3" and not (self.tgl[i] and d1 <= self.tgl[i] <= d2):
                    continue
            else:
                if not (self.x0[i] <= x1 and self.x1[i] >= x0 and self.y0[i] <= y1 and self.y1[i] >= y0):
                    continue
                if self.et[i] != kode or self.conf[i] < conf_min:
                    continue
            n += 1
            if daftar:
                hasil.append(i)
        return hasil if daftar else n


def agregat_patch(folder):
    p = Path(folder) / "patches.csv"
    if not p.is_file():
        raise SystemExit("Berkas %s belum ada." % p)
    cnt = Counter()
    for r in ci.baca_patch_csv(p):
        cnt[(r["inventory"], r["split"])] += 1
    return cnt


def hitung_semua(idx, skala, titik, par, folder):
    """{beban: {kueri_id: jumlah}} untuk W1 sampai W6."""
    hasil = {}
    hasil["W1"] = {q["id"]: 1 if 0 <= q["ann_id"] < idx.n else 0 for q in kueri.ids_w1(skala)}
    for beban in ("W2", "W3", "W4"):
        hasil[beban] = {p["id"]: idx.cari(beban, kueri.jendela_kueri(beban, p, par), p, par)
                        for p in titik}
    hasil["W5"] = {1: len(idx.agregat5)}
    hasil["W6"] = {1: len(agregat_patch(folder))}
    return hasil


def tulis_csv(beban, skala, jumlah):
    BENAR_DIR.mkdir(parents=True, exist_ok=True)
    jalur = BENAR_DIR / ("%s_%s.csv" % (beban, skala))
    with open(jalur, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(KOLOM)
        for q in sorted(jumlah):
            w.writerow(["benar", beban, skala, 1, "warm", q, "0.000", jumlah[q], "wasit kebenaran.py"])
    return jalur


def contoh(idx, ann_id, par):
    if ann_id not in set(idx.id):
        raise SystemExit("ann_id %d tidak ada di data." % ann_id)
    i = list(idx.id).index(ann_id)
    d = date.fromordinal(idx.tgl[i]) if idx.tgl[i] else None
    p = {"lon": idx.lon[i], "lat": idx.lat[i], "event_type": idx.nama[idx.et[i]] or "Rainfall",
         "date_from": (d - timedelta(days=par["hari"])).isoformat() if d else "2016-04-01",
         "date_to": (d + timedelta(days=par["hari"])).isoformat() if d else "2016-04-01"}
    print("Anotasi %d: lokasi %s, titik pusat (%r, %r), event_date %s, event_type %s"
          % (ann_id, idx.lokasi[i], p["lon"], p["lat"], d, idx.nama[idx.et[i]]))
    for beban, ket in (("W2", "titik pusat di jendela +-%g derajat" % par["half_titik"]),
                       ("W3", "dan event_date %s sampai %s" % (p["date_from"], p["date_to"])),
                       ("W4", "kotak beririsan dengan jendela +-%g derajat, event_type %s, conf >= %g"
                        % (par["half_kotak"], p["event_type"], par["conf_min"]))):
        w = kueri.jendela_kueri(beban, p, par)
        n = idx.cari(beban, w, p, par)
        print("%s: %d anotasi (%s)" % (beban, n, ket))
        if beban != "W4":
            for j in idx.cari(beban, w, p, par, daftar=True)[:15]:
                print("    ann_id %-9d %-14s event_date %s" % (
                    idx.id[j], idx.lokasi[j], date.fromordinal(idx.tgl[j]) if idx.tgl[j] else "-"))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="Wasit jawaban benar W1 sampai W6.")
    ap.add_argument("--skala", choices=sorted(kueri.FAKTOR), default="S1")
    ap.add_argument("--folder", help="folder data (bawaan data/out/<skala>)")
    ap.add_argument("--points", default=str(POINTS))
    ap.add_argument("--tulis", action="store_true", help="tulis bench/benar/W*_S*.csv")
    ap.add_argument("--ann", type=int, help="contoh: pakai titik pusat anotasi ini")
    ap.add_argument("--titik", nargs=2, type=float, metavar=("LON", "LAT"))
    ap.add_argument("--tanggal", help="dengan --titik: tanggal pusat W3 (YYYY-MM-DD)")
    args = ap.parse_args(argv)

    folder = args.folder or str(ROOT / "data" / "out" / args.skala.lower())
    if args.skala == "S100" and not (args.ann is not None or args.titik):
        print("Catatan: S100 butuh sekitar 1 GB RAM dan beberapa menit.", flush=True)
    idx = Indeks(folder)
    try:
        par, titik = kueri.muat_titik(args.points)
    except OSError:
        par, titik = dict(kueri.PARAMETER_BAWAAN), []
        if args.ann is None and not args.titik:
            raise SystemExit("Berkas %s belum ada.\nJalankan dulu: python bench/make_points.py" % args.points)

    if args.ann is not None:
        return contoh(idx, args.ann, par)
    if args.titik:
        p = {"lon": args.titik[0], "lat": args.titik[1]}
        w = kueri.jendela_kueri("W2", p, par)
        beban = "W2"
        if args.tanggal:
            d = date.fromisoformat(args.tanggal)
            p["date_from"] = (d - timedelta(days=par["hari"])).isoformat()
            p["date_to"] = (d + timedelta(days=par["hari"])).isoformat()
            beban = "W3"
        hits = idx.cari(beban, w, p, par, daftar=True)
        print("%s di (%r, %r), jendela +-%g derajat: %d anotasi" % (
            beban, p["lon"], p["lat"], par["half_titik"], len(hits)))
        for j in hits[:30]:
            print("    ann_id %-9d %-14s event_date %s" % (
                idx.id[j], idx.lokasi[j], date.fromordinal(idx.tgl[j]) if idx.tgl[j] else "-"))
        return 0

    print("Jawaban benar dari %s: %d anotasi, %d titik uji, skala %s" % (
        Path(folder) / "annotations.csv", idx.n, len(titik), args.skala))
    hasil = hitung_semua(idx, args.skala, titik, par, folder)
    for beban in kueri.BEBAN:
        h = hasil[beban]
        ada = sum(1 for v in h.values() if v > 0)
        ket = {"W1": "id ditemukan", "W2": "titik punya hasil", "W3": "titik punya hasil",
               "W4": "titik punya hasil", "W5": "kelompok (event_type x tahun)",
               "W6": "kelompok (inventory x split)"}[beban]
        print("  %s: %d dari %d kueri: %s; jumlah seluruhnya %d" % (beban, ada, len(h), ket, sum(h.values())))
        if args.tulis:
            tulis_csv(beban, args.skala, h)
    if args.tulis:
        print("Tertulis di %s (commit bila S1)." % BENAR_DIR)
    return 0


if __name__ == "__main__":
    sys.exit(main())
