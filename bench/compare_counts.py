#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Bandingkan jumlah hasil per kueri antara berkas hasil MongoDB, PostGIS, Spark, dan wasit.

Cara pakai (dari akar repo, PowerShell):
  python bench/compare_counts.py results/A.csv                  satu berkas: dibandingkan dengan wasit
  python bench/compare_counts.py results/A.csv results/B.csv
  python bench/compare_counts.py results/A.csv results/B.csv results/C.csv
  python bench/compare_counts.py --titik-maks 20 results/A.csv results/B.csv results/C.csv
Wasit "benar" (hasil bench/kebenaran.py --tulis) ikut dibandingkan otomatis bila berkas
bench/benar/<beban>_<skala>.csv ada. Matikan dengan --tanpa-wasit (tidak untuk satu berkas).
--titik-maks N membandingkan hanya kueri_id 1 sampai N. Pakai untuk S100: rancangannya 20 titik
pertama, tetapi sebagian berkas S100 memuat 100 titik sedangkan berkas lain hanya 20. Tanpa opsi
ini, titik 21 sampai 100 ikut terhitung "beda" karena tidak ada di berkas yang lebih pendek.

Syarat: semua berkas memuat beban kerja dan skala yang sama. Yang dibandingkan adalah
kolom jumlah_hasil tiap kueri_id, dari ulangan pertama di tiap berkas.

Jendela kueri sengaja digeser setengah langkah dari kisi koordinat data (lihat
bench/kueri.py), jadi MongoDB (bola), PostGIS dan Spark (bidang datar) seharusnya memberi
jumlah yang sama persis. Selisih biasanya berarti ada yang salah (data yang dimuat, indeks,
atau kueri): tulis [BLOKIR] di grup dengan daftar selisih yang tercetak.
Satu pengecualian pernah teramati: S100 W2 titik 19, MongoDB 1401 dan PostGIS/Spark 1400.
Selisihnya satu anotasi yang berjarak sekitar 5 mm di luar tepi jendela; dugaannya toleransi
sel S2 MongoDB di tepi jendela (belum dibuktikan). Selisih selain itu tetap dianggap salah.
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


def baca(jalur, titik_maks=None):
    """Satu berkas hasil -> (info, {kueri_id: jumlah di ulangan pertama}, peringatan).

    titik_maks: bila diisi, hanya baris dengan kueri_id <= titik_maks yang dipakai."""
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
    if titik_maks is not None:
        try:
            baris = [b for b in baris if int(b["kueri_id"]) <= titik_maks]
        except ValueError as e:
            raise SystemExit("%s: ada kueri_id yang tidak terbaca (%s)" % (jalur, e))
        if not baris:
            raise SystemExit("%s: tidak ada baris dengan kueri_id sampai %d." % (jalur, titik_maks))
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


def urai(arg):
    """Pisahkan opsi dari daftar berkas -> (berkas, tanpa_wasit, titik_maks)."""
    berkas, tanpa_wasit, titik_maks, i = [], False, None, 0
    while i < len(arg):
        a = arg[i]
        if a == "--tanpa-wasit":
            tanpa_wasit = True
        elif a == "--titik-maks" or a.startswith("--titik-maks="):
            if "=" in a:
                nilai = a.split("=", 1)[1]
            else:
                i += 1
                nilai = arg[i] if i < len(arg) else ""
            try:
                titik_maks = int(nilai)
            except ValueError:
                titik_maks = 0
            if titik_maks < 1:
                raise SystemExit("--titik-maks butuh bilangan bulat >= 1, misalnya --titik-maks 20")
        else:
            berkas.append(a)
        i += 1
    return berkas, tanpa_wasit, titik_maks


def main(argv=None):
    arg = sys.argv[1:] if argv is None else list(argv)
    jalur, tanpa_wasit, titik_maks = urai(arg)
    if len(jalur) not in (1, 2, 3):
        print(__doc__)
        return 2
    data = [baca(j, titik_maks) for j in jalur]

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
        info, pertama, _ = baca(wasit, titik_maks)
        lain = len(set(pertama) - ids_hasil)
        if lain:
            print("Catatan: wasit punya %d kueri yang tidak dijalankan di berkas hasil (diabaikan)." % lain)
        data.append((info, {q: n for q, n in pertama.items() if q in ids_hasil}, []))
        nama.append("benar")
    elif not tanpa_wasit:
        print("Catatan: wasit %s belum ada (python bench/kebenaran.py --skala %s --tulis); "
              "yang dibandingkan hanya berkas hasil." % (wasit.name, s))
    print("Perbandingan %s %s: %s" % (b, s, " vs ".join(nama)))
    if titik_maks is not None:
        print("Hanya kueri_id 1 sampai %d yang dibandingkan (--titik-maks)." % titik_maks)

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
    print("Ada %d kueri yang beda. Jendela sudah digeser dari tepi, jadi selisih biasanya berarti ada yang salah."
          % len(beda))
    print("Cek berurutan: (1) skala yang dimuat sama di semua penyimpanan, (2) muat ulang dari")
    print("data/out yang sama, (3) indeks sudah dibuat, (4) '-' artinya kueri itu tidak ada di berkas%s,"
          % ("" if titik_maks is not None else " (di S100 coba --titik-maks 20)"))
    print("(5) satu-satunya selisih tepi yang pernah teramati: MongoDB lebih banyak 1 pada S100 W2")
    print("titik 19 (dugaan toleransi sel S2); selisih lain dianggap salah.")
    print("Bila tetap beda: tulis [BLOKIR] di grup dan tempel tabel di atas.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
