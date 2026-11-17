#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Ringkas waktu pemrosesan Spark per skala (dari results/analitik/waktu_pemrosesan.csv).

Pemakaian (dari akar repo, PowerShell; hanya Python bawaan):
  python analitik/ringkas_waktu.py
  python analitik/ringkas_waktu.py --waktu results/analitik/waktu_pemrosesan.csv --keluar results/analitik
Tulis dua berkas di folder --keluar (bisa dibuka di Excel atau Sheets):
  ringkasan_waktu.csv  satu baris per skala (dan mode etl / tanpa-etl): waktu etl, analitik, ekspor,
                       total (median ulangan warm; bila tidak ada ulangan warm dipakai ulangan cold),
                       total cold, anotasi per detik, dan rasio terhadap S1
  waktu_per_tahap.csv  waktu cold dan median warm tiap tahap per skala

"analitik" = jumlah waktu semua kueri analitik dalam satu putaran. Satu putaran = satu proses spark-submit
yang mengulang pipeline penuh; ulangan 1 berlabel cold (JVM baru), selanjutnya warm.
"""
import argparse
import csv
import os
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kueri_analitik as ka  # noqa: E402

AKAR = Path(__file__).resolve().parent.parent
URUT_SKALA = {"S1": 1, "S10": 2, "S100": 3}
KELUAR_RINGKAS = ["skala", "mode", "n_anotasi", "dasar", "n_putaran", "etl_ms", "analitik_ms", "ekspor_ms",
                  "total_ms", "total_cold_ms", "anotasi_per_detik", "detik_per_juta_anotasi",
                  "rasio_data_vs_S1", "rasio_waktu_vs_S1"]
KELUAR_TAHAP = ["skala", "mode", "tahap", "cold_ms", "median_warm_ms", "n_warm"]


def med(x):
    return statistics.median(x) if x else None


def baca_putaran(jalur):
    """{(skala, mode): [putaran]} dengan putaran = dict(cw, n_anotasi, tahap={nama: ms})."""
    with open(jalur, encoding="utf-8", newline="") as f:
        baris = list(csv.DictReader(f))
    if not baris:
        raise SystemExit("%s kosong" % jalur)
    wajib = set(["sesi", "skala", "ulangan", "cold_warm", "tahap", "waktu_ms", "n_anotasi", "catatan"])
    if not wajib <= set(baris[0]):
        raise SystemExit("%s: kolom tidak lengkap, butuh %s" % (jalur, sorted(wajib)))
    putaran = {}
    for b in baris:
        cat = b["catatan"] or ""
        if "hanya-asli" in cat:
            continue
        mode = "tanpa-etl" if "tanpa-etl" in cat else "etl"
        kunci = (b["skala"], mode)
        p = putaran.setdefault(kunci, {}).setdefault((b["sesi"], b["ulangan"]), {
            "cw": b["cold_warm"], "n_anotasi": int(b["n_anotasi"]), "tahap": {}})
        p["tahap"][b["tahap"]] = float(b["waktu_ms"])
    return dict((k, list(v.values())) for k, v in putaran.items())


def ringkas(putaran):
    """(baris ringkasan, baris per tahap)."""
    hasil, tahap_baris = [], []
    s1 = {}
    urut = sorted(putaran, key=lambda k: (k[1], URUT_SKALA.get(k[0], 9)))
    for skala, mode in urut:
        ps = putaran[(skala, mode)]
        hangat = [p for p in ps if p["cw"] == "warm" and "total" in p["tahap"]]
        dingin = [p for p in ps if p["cw"] == "cold" and "total" in p["tahap"]]
        pakai, dasar = (hangat, "warm") if hangat else (dingin, "cold")
        if not pakai:
            continue
        n = pakai[0]["n_anotasi"]

        def m(f):
            return med([f(p) for p in pakai if f(p) is not None])
        total = m(lambda p: p["tahap"]["total"])
        analitik = m(lambda p: sum(p["tahap"][t] for t in ka.NAMA_ANALISIS if t in p["tahap"]))
        etl = m(lambda p: p["tahap"].get("etl"))
        ekspor = m(lambda p: p["tahap"].get("ekspor"))
        total_dingin = med([p["tahap"]["total"] for p in dingin])
        if skala == "S1":
            s1[mode] = (n, total)
        rasio_d = rasio_w = ""
        if mode in s1 and s1[mode][1]:
            rasio_d, rasio_w = "%.1f" % (n / float(s1[mode][0])), "%.1f" % (total / s1[mode][1])

        def f1(x):
            return "" if x is None else "%.1f" % x
        hasil.append([skala, mode, n, dasar, len(pakai), f1(etl), f1(analitik), f1(ekspor), f1(total),
                      f1(total_dingin), "%.0f" % (n / (total / 1000.0)), "%.2f" % ((total / 1000.0) / (n / 1e6)),
                      rasio_d, rasio_w])
        nama_tahap = [t for t in (["etl"] + ka.NAMA_ANALISIS + ["ekspor", "total"])
                      if any(t in p["tahap"] for p in ps)]
        for t in nama_tahap:
            d = med([p["tahap"][t] for p in dingin if t in p["tahap"]])
            h = [p["tahap"][t] for p in hangat if t in p["tahap"]]
            tahap_baris.append([skala, mode, t, f1(d), f1(med(h)), len(h)])
    return hasil, tahap_baris


def tulis(jalur, kepala, baris):
    with open(jalur, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(kepala)
        w.writerows(baris)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Ringkas waktu pemrosesan Spark per skala.")
    ap.add_argument("--waktu", default=str(AKAR / "results" / "analitik" / "waktu_pemrosesan.csv"))
    ap.add_argument("--keluar", default=str(AKAR / "results" / "analitik"))
    args = ap.parse_args(argv)
    if not os.path.exists(args.waktu):
        raise SystemExit("Berkas %s belum ada. Jalankan spark_pipeline.py dulu (lihat analitik/README.md)." % args.waktu)
    ringkasan, per_tahap = ringkas(baca_putaran(args.waktu))
    if not ringkasan:
        raise SystemExit("Tidak ada putaran lengkap (baris 'total') di %s." % args.waktu)
    os.makedirs(args.keluar, exist_ok=True)
    tulis(os.path.join(args.keluar, "ringkasan_waktu.csv"), KELUAR_RINGKAS, ringkasan)
    tulis(os.path.join(args.keluar, "waktu_per_tahap.csv"), KELUAR_TAHAP, per_tahap)
    print("%-5s %-9s %10s %-5s %3s %10s %11s %9s %10s %11s %10s %7s %7s" % (
        "skala", "mode", "anotasi", "dasar", "n", "etl_ms", "analitik_ms", "ekspor", "total_ms", "cold_ms",
        "anot/dtk", "xdata", "xwaktu"))
    for b in ringkasan:
        print("%-5s %-9s %10d %-5s %3d %10s %11s %9s %10s %11s %10s %7s %7s" % (
            b[0], b[1], b[2], b[3], b[4], b[5] or "-", b[6], b[7] or "-", b[8], b[9] or "-", b[10],
            b[12] or "-", b[13] or "-"))
    print()
    print("Tertulis: %s dan %s" % (os.path.join(args.keluar, "ringkasan_waktu.csv"),
                                   os.path.join(args.keluar, "waktu_per_tahap.csv")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
