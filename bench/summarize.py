#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Ringkas berkas hasil uji: median, p95, rata-rata, rentang antar ulangan, dan tabel banding.

Cara pakai (dari akar repo, PowerShell):
  python bench/summarize.py                      semua results/*.csv (kecuali ringkasan)
  python bench/summarize.py results/A.csv ...    hanya berkas yang disebut
  python bench/summarize.py --titik-maks 20      S100 hanya kueri_id 1 sampai 20 (lihat di bawah)
Hasil dicetak dan ditulis ke results/ringkasan.csv dan results/banding.csv
(keduanya bisa dibuka di Excel atau Sheets).

--titik-maks N membuang baris dengan kueri_id > N pada skala di --titik-skala (bawaan S100;
bisa lebih dari satu, pisahkan dengan koma). Rancangan S100 memakai 20 titik pertama, tetapi
sebagian berkas S100 memuat 100 titik; tanpa opsi ini median S100 bercampur dua himpunan titik
yang berbeda. Skala lain tidak disentuh. Bisa dipadukan dengan daftar berkas.

Satu baris ringkasan = satu kelompok: penyimpanan, beban_kerja, skala, cold_warm, konkurensi, varian.
  konkurensi : dari kolom catatan bila berbentuk konkurensi=N (W1 banyak klien), selain itu kosong
  varian     : dari kolom catatan bila berbentuk varian=NAMA (mis. varian=tanpa-indeks untuk E1, lewat
               harness --note "varian=tanpa-indeks"), selain itu kosong. Varian TIDAK dicampur dengan
               hasil biasa, supaya median uji tanpa indeks tidak merusak median uji berindeks.
  median_ms  : median semua eksekusi kueri di kelompok itu
  median_ulangan_min / _maks : median terkecil dan terbesar antar ulangan (rentang)
  qps_1klien : 1000 / rata2_ms, perkiraan untuk satu klien yang berjalan berurutan
  galat_n    : jumlah eksekusi yang gagal (jumlah_hasil = -1); waktunya TIDAK ikut dihitung
Tabel banding (banding.csv): median_ms per beban kerja dan skala, penyimpanan berjajar
(mongodb, postgis, spark), plus rasio terhadap yang tercepat.
"""
import csv
import math
import re
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"
URUT_SKALA = {"S1": 1, "S10": 2, "S100": 3}
URUT_SIMPAN = ["mongodb", "postgis", "spark"]
WAJIB = ["penyimpanan", "beban_kerja", "skala", "ulangan", "cold_warm", "waktu_ms"]
KELUAR = ["penyimpanan", "beban_kerja", "skala", "cold_warm", "konkurensi", "varian", "ulangan_n",
          "kueri_n", "median_ms", "median_ulangan_min", "median_ulangan_maks", "p95_ms",
          "rata2_ms", "qps_1klien", "galat_n", "berkas_n"]

try:
    sys.stdout.reconfigure(errors="replace")
except Exception:
    pass


def persentil(nilai, q):
    urut = sorted(nilai)
    k = math.ceil(q / 100 * len(urut)) - 1
    return urut[max(0, min(len(urut) - 1, k))]


def konkurensi(catatan):
    m = re.search(r"konkurensi=(\d+)", catatan or "")
    return m.group(1) if m else ""


def varian(catatan):
    m = re.search(r"varian=(\S+)", catatan or "")
    return m.group(1) if m else ""


def ambil_opsi(arg, nama):
    """Ambil '--nama N' atau '--nama=N' dari arg -> (nilai atau None, sisa arg)."""
    sisa, nilai, i = [], None, 0
    while i < len(arg):
        a = arg[i]
        if a == nama:
            if i + 1 >= len(arg):
                raise SystemExit("%s butuh nilai." % nama)
            nilai, i = arg[i + 1], i + 2
        elif a.startswith(nama + "="):
            nilai, i = a.split("=", 1)[1], i + 1
        else:
            sisa.append(a)
            i += 1
    return nilai, sisa


def baca(jalur, grup, batas=None):
    """batas: (titik_maks, {skala}) atau None. Baris pada skala itu dengan kueri_id > titik_maks dilewati."""
    with open(jalur, encoding="utf-8", newline="") as f:
        baris = list(csv.DictReader(f))
    if not baris:
        print("LEWAT %s: kosong" % jalur)
        return
    kurang = [k for k in WAJIB if k not in baris[0]]
    if batas and "kueri_id" not in baris[0]:
        kurang.append("kueri_id")
    if kurang:
        print("LEWAT %s: kolom tidak ada: %s" % (jalur, ", ".join(kurang)))
        return
    for b in baris:
        if batas and b["skala"] in batas[1] and int(b["kueri_id"]) > batas[0]:
            continue
        kunci = (b["penyimpanan"], b["beban_kerja"], b["skala"], b["cold_warm"],
                 konkurensi(b.get("catatan")), varian(b.get("catatan")))
        g = grup.setdefault(kunci, {"waktu": [], "ulangan": {}, "berkas": set(), "galat": 0})
        if str(b.get("jumlah_hasil", "0")).strip() == "-1":
            g["galat"] += 1
            continue
        ms = float(b["waktu_ms"])
        g["waktu"].append(ms)
        g["ulangan"].setdefault(b["ulangan"], []).append(ms)
        g["berkas"].add(str(jalur))


def tulis(jalur, kepala, baris):
    with open(jalur, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(kepala)
        w.writerows(baris)


def banding(grup):
    """Tabel median per (beban, skala, cold_warm, konkurensi, varian) dengan penyimpanan berjajar."""
    sel = {}
    for (simpan, beban, skala, cw, konk, var), g in grup.items():
        if g["waktu"]:
            sel.setdefault((beban, skala, cw, konk, var), {})[simpan] = statistics.median(g["waktu"])
    kepala = ["beban_kerja", "skala", "cold_warm", "konkurensi", "varian"] + \
             ["median_ms_" + s for s in URUT_SIMPAN] + ["tercepat", "rasio_terlambat_vs_tercepat"]
    baris = []
    for kunci in sorted(sel, key=lambda k: (k[0], URUT_SKALA.get(k[1], 9), k[2], k[3], k[4])):
        nilai = sel[kunci]
        tercepat = min(nilai, key=nilai.get)
        terlambat = max(nilai.values())
        rasio = terlambat / nilai[tercepat] if nilai[tercepat] > 0 and len(nilai) > 1 else ""
        baris.append(list(kunci) + [("%.3f" % nilai[s]) if s in nilai else "" for s in URUT_SIMPAN]
                     + [tercepat if len(nilai) > 1 else "", ("%.1f" % rasio) if rasio != "" else ""])
    return kepala, baris


def main(argv=None):
    arg = sys.argv[1:] if argv is None else list(argv)
    maks, arg = ambil_opsi(arg, "--titik-maks")
    skala_batas, arg = ambil_opsi(arg, "--titik-skala")
    batas = None
    if maks is not None:
        try:
            n = int(maks)
        except ValueError:
            n = 0
        if n < 1:
            raise SystemExit("--titik-maks butuh bilangan bulat >= 1, misalnya --titik-maks 20")
        batas = (n, {s.strip() for s in (skala_batas or "S100").split(",") if s.strip()})
    elif skala_batas is not None:
        raise SystemExit("--titik-skala hanya dipakai bersama --titik-maks.")
    folder = RESULTS
    if arg:
        berkas = [Path(a) for a in arg]
    else:
        berkas = sorted(p for p in folder.glob("*.csv")
                        if p.name not in ("ringkasan.csv", "banding.csv")
                        and not p.name.startswith("pengukuran_"))
    if not berkas:
        raise SystemExit("Tidak ada berkas hasil di %s" % folder)
    grup = {}
    for jalur in berkas:
        baca(jalur, grup, batas)
    grup = {k: g for k, g in grup.items() if g["waktu"] or g["galat"]}
    if not grup:
        raise SystemExit("Tidak ada data yang bisa diringkas.")

    baris = []

    def urut(k):
        return (k[1], URUT_SKALA.get(k[2], 9), URUT_SIMPAN.index(k[0]) if k[0] in URUT_SIMPAN else 9,
                k[3], k[4], k[5])

    for kunci in sorted(grup, key=urut):
        g = grup[kunci]
        w = g["waktu"]
        if not w:
            baris.append(list(kunci) + [0, 0, "", "", "", "", "", "", g["galat"], 0])
            continue
        per = [statistics.median(v) for v in g["ulangan"].values()]
        rata = statistics.mean(w)
        baris.append(list(kunci) + [
            len(g["ulangan"]), len(w), "%.3f" % statistics.median(w), "%.3f" % min(per),
            "%.3f" % max(per), "%.3f" % persentil(w, 95), "%.3f" % rata,
            "%.1f" % (1000 / rata if rata > 0 else 0), g["galat"], len(g["berkas"])])

    RESULTS.mkdir(parents=True, exist_ok=True)
    tulis(RESULTS / "ringkasan.csv", KELUAR, baris)
    kb, bb = banding(grup)
    tulis(RESULTS / "banding.csv", kb, bb)

    print("%-9s %-5s %-5s %-5s %4s %-12s %4s %6s %10s %10s %10s %10s %5s" % (
        "simpan", "beban", "skala", "c/w", "konk", "varian", "ul", "kueri", "median_ms", "ul_min",
        "ul_maks", "p95_ms", "galat"))
    for b in baris:
        print("%-9s %-5s %-5s %-5s %4s %-12s %4s %6s %10s %10s %10s %10s %5s" % (
            b[0], b[1], b[2], b[3], b[4] or "-", b[5] or "-", b[6], b[7], b[8], b[9], b[10], b[11], b[14]))
    print()
    print("Banding median (ms):")
    print("%-5s %-5s %-5s %4s %-12s  %10s %10s %10s  %-8s %6s" % (
        "beban", "skala", "c/w", "konk", "varian", "mongodb", "postgis", "spark", "tercepat", "rasio"))
    for b in bb:
        print("%-5s %-5s %-5s %4s %-12s  %10s %10s %10s  %-8s %6s" % (
            b[0], b[1], b[2], b[3] or "-", b[4] or "-", b[5] or "-", b[6] or "-", b[7] or "-", b[8] or "-", b[9] or "-"))
    print()
    if batas:
        print("Pembatasan titik: skala %s hanya kueri_id 1 sampai %d (--titik-maks)."
              % (",".join(sorted(batas[1])), batas[0]))
    print("Tertulis: results/ringkasan.csv (%d kelompok) dan results/banding.csv (%d baris), dari %d berkas"
          % (len(baris), len(bb), len(berkas)))
    if any(g["galat"] for g in grup.values()):
        print("PERINGATAN: ada eksekusi yang GALAT (kolom galat). Periksa berkas hasilnya sebelum dipakai.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
