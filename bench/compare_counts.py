#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Bandingkan jumlah hasil per kueri antara berkas hasil MongoDB, PostGIS, Spark, dan wasit.

Cara pakai (dari akar repo, PowerShell):
  python bench/compare_counts.py results/A.csv                  satu berkas: dibandingkan dengan wasit
  python bench/compare_counts.py results/A.csv results/B.csv
  python bench/compare_counts.py results/A.csv results/B.csv results/C.csv
Wasit "benar" (hasil bench/kebenaran.py --tulis) ikut dibandingkan otomatis bila berkas
bench/benar/<beban>_<skala>.csv ada. Matikan dengan --tanpa-wasit (tidak untuk satu berkas).

Syarat: semua berkas memuat beban kerja dan skala yang sama. Yang dibandingkan adalah
kolom jumlah_hasil tiap kueri_id, dari ulangan pertama di tiap berkas.

Jendela kueri sengaja digeser setengah langkah dari kisi koordinat data (lihat
bench/kueri.py), jadi MongoDB (bola), PostGIS dan Spark (bidang datar) HARUS memberi
jumlah yang sama persis. Selisih berarti ada yang salah (data yang dimuat, indeks, atau
kueri), bukan efek tepi: tulis [BLOKIR] di grup dengan daftar selisih yang tercetak.
Kode keluar 0 bila semua cocok, 1 bila ada yang beda, 2 bila berkas tidak bisa dibaca.
"""
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BENAR_DIR = ROOT / "bench" / "benar"
WAJIB = ["penyimpanan", "beban_kerja", "skala", "ulangan", "kueri_id", "jumlah_hasil"]

try:
    sys.stdout.reconfigure(errors="replace")
except Exception:
    pass


def baca(jalur):
    """Satu berkas hasil -> (info, {kueri_id: jumlah di ulangan pertama}, peringatan)."""
    try:
        with open(jalur, encoding="utf-8", newline="") as f:
            baris = list(csv.DictReader(f))
    except OSError as e:
        raise SystemExit("Tidak bisa membuka %s: %s" % (jalur, e))
    if not baris:
        raise SystemExit("%s kosong." % jalur)
    kurang = [k for k in WAJIB if k not in baris[0]]
    if kurang:
        raise SystemExit("%s: kolom ini tidak ada: %s" % (jalur, ", ".join(kurang)))
    info = {}
    for k in ("penyimpanan", "beban_kerja", "skala"):
        nilai = {b[k] for b in baris}
        if len(nilai) != 1:
            raise SystemExit("%s: kolom %s berisi lebih dari satu nilai: %s"
                             % (jalur, k, sorted(nilai)))
        info[k] = nilai.pop()
    try:
        awal = min(int(b["ulangan"]) for b in baris)
        pertama, semua = {}, {}
        for b in baris:
            q, n = int(b["kueri_id"]), int(b["jumlah_hasil"])
            semua.setdefault(q, set()).add(n)
            if int(b["ulangan"]) == awal:
                pertama[q] = n
    except ValueError as e:
        raise SystemExit("%s: ada angka yang tidak terbaca (%s)" % (jalur, e))
    peringatan = ["kueri %d: jumlah berubah antar ulangan %s" % (q, sorted(s))
                  for q, s in sorted(semua.items()) if len(s) > 1]
    galat = sorted(q for q, n in pertama.items() if n < 0)
    if galat:
        peringatan.append("%d kueri GALAT saat dijalankan (jumlah -1), contoh kueri_id %s"
                          % (len(galat), galat[:5]))
    return info, pertama, peringatan


def main(argv=None):
    arg = sys.argv[1:] if argv is None else list(argv)
    tanpa_wasit = "--tanpa-wasit" in arg
    jalur = [a for a in arg if a != "--tanpa-wasit"]
    if len(jalur) not in (1, 2, 3):
        print(__doc__)
        return 2
    data = [baca(j) for j in jalur]

    beban = {d[0]["beban_kerja"] for d in data}
    skala = {d[0]["skala"] for d in data}
    if len(beban) > 1 or len(skala) > 1:
        print("Berkas harus memuat beban kerja dan skala yang sama. "
              "Ditemukan beban %s, skala %s." % (sorted(beban), sorted(skala)))
        return 2
    b, s = beban.pop(), skala.pop()
    nama = [d[0]["penyimpanan"] for d in data]
    if len(set(nama)) < len(nama):
        print("PERINGATAN: ada dua berkas dari penyimpanan yang sama: %s" % nama)
    for j, d in zip(jalur, data):
        for p in d[2]:
            print("PERINGATAN %s: %s" % (j, p))

    ids_hasil = set().union(*[set(d[1]) for d in data])
    wasit = BENAR_DIR / ("%s_%s.csv" % (b, s))
    if len(jalur) == 1 and (tanpa_wasit or not wasit.is_file()):
        print("Dengan satu berkas hasil, pembandingnya adalah wasit. Buat dulu: "
              "python bench/kebenaran.py --skala %s --tulis" % s)
        return 2
    if not tanpa_wasit and wasit.is_file():
        info, pertama, _ = baca(wasit)
        lain = len(set(pertama) - ids_hasil)
        if lain:
            print("Catatan: wasit punya %d kueri yang tidak dijalankan di berkas hasil (diabaikan)." % lain)
        data.append((info, {q: n for q, n in pertama.items() if q in ids_hasil}, []))
        nama.append("benar")
    elif not tanpa_wasit:
        print("Catatan: wasit %s belum ada (python bench/kebenaran.py --skala %s --tulis); "
              "yang dibandingkan hanya berkas hasil." % (wasit.name, s))
    print("Perbandingan %s %s: %s" % (b, s, " vs ".join(nama)))

    semua_id = sorted(set().union(*[set(d[1]) for d in data]))
    beda = []
    for q in semua_id:
        nilai = [d[1].get(q) for d in data]
        if len(set(nilai)) > 1:
            beda.append((q, nilai))
    print("Cocok: %d dari %d kueri." % (len(semua_id) - len(beda), len(semua_id)))
    if not beda:
        print("Semua jumlah hasil sama.")
        return 0

    print()
    print("kueri_id  " + "  ".join("%9s" % n for n in nama))
    for q, nilai in beda[:40]:
        print("%8d  " % q + "  ".join("%9s" % ("-" if v is None else v) for v in nilai))
    if len(beda) > 40:
        print("... dan %d kueri lain." % (len(beda) - 40))
    print()
    print("Ada %d kueri yang beda. Ini BUKAN efek tepi (jendela sudah digeser dari tepi)." % len(beda))
    print("Cek berurutan: (1) skala yang dimuat sama di semua penyimpanan, (2) muat ulang dari")
    print("data/out yang sama, (3) indeks sudah dibuat, (4) '-' artinya kueri itu tidak ada di berkas.")
    print("Bila tetap beda: tulis [BLOKIR] di grup dan tempel tabel di atas.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
