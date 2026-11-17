#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Bandingkan dua folder tabel analitik (hasil Spark vs acuan Python) sel demi sel.

Pemakaian (dari akar repo, PowerShell; hanya Python bawaan):
  python analitik/cocokkan.py                              hasil Spark S1 vs acuan S1 (bawaan)
  python analitik/cocokkan.py --hasil results/analitik/S100         vs analitik/referensi_S100
  python analitik/cocokkan.py --hasil results/analitik/S100_asli    vs analitik/referensi_S1
Acuan dipilih dari nama folder hasil: S10 dan S100 memakai acuannya sendiri; S1, folder berakhiran _asli,
dan nama lain memakai acuan S1. --acuan menimpa pilihan itu.
Kode keluar 0 bila semua tabel cocok, 1 bila ada selisih atau berkas hilang.

Aturan banding: baris disejajarkan menurut kolom kunci (lihat kueri_analitik.KUNCI), bukan menurut
urutan baris. Dua sel sama bila teksnya sama, atau keduanya bilangan dengan selisih relatif
<= toleransi (bawaan 1e-9; jumlah desimal double bisa beda di digit terakhir karena urutan
penjumlahan). Sel kosong (NULL) hanya sama dengan sel kosong.
"""
import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kueri_analitik as ka  # noqa: E402

AKAR = Path(__file__).resolve().parent.parent


def skala_acuan(hasil):
    """Skala acuan untuk folder hasil: ...\\S10 -> S10, ...\\S100 -> S100; S1, ..._asli, dan lainnya -> S1."""
    nama = os.path.basename(os.path.normpath(str(hasil))).upper()
    return nama if nama in ("S10", "S100") else "S1"


def acuan_untuk(hasil):
    return str(AKAR / "analitik" / ("referensi_" + skala_acuan(hasil)))


def sama(a, b, tol):
    if a == b:
        return True
    if a == "" or b == "":
        return False
    try:
        x, y = float(a), float(b)
    except ValueError:
        return False
    return abs(x - y) <= tol * max(1.0, abs(x), abs(y))


def bandingkan_tabel(nama, kolom_a, baris_a, kolom_b, baris_b, kunci, tol=1e-9, maks_tampil=5):
    """(daftar kalimat selisih, jumlah sel yang dibandingkan). Daftar kosong berarti cocok.
    a = hasil yang diuji, b = acuan. Semua nilai harus berupa teks."""
    if list(kolom_a) != list(kolom_b):
        return ["%s: nama/urutan kolom beda\n      hasil: %s\n      acuan: %s" % (nama, list(kolom_a), list(kolom_b))], 0
    idx = [kolom_a.index(k) for k in kunci]

    def peta(baris):
        d = {}
        for n, b in enumerate(baris):
            k = tuple(b[i] for i in idx) if idx else (n,)
            m = 0
            while (k, m) in d:
                m += 1
            d[(k, m)] = b
        return d

    pa, pb = peta(baris_a), peta(baris_b)
    beda = []
    hilang_a = [k for k in pb if k not in pa]
    hilang_b = [k for k in pa if k not in pb]
    for k in hilang_a[:maks_tampil]:
        beda.append("%s: baris acuan tidak ada di hasil: %s" % (nama, list(k[0])))
    for k in hilang_b[:maks_tampil]:
        beda.append("%s: baris hasil tidak ada di acuan: %s" % (nama, list(k[0])))
    if len(hilang_a) > maks_tampil or len(hilang_b) > maks_tampil:
        beda.append("%s: ... dan %d baris lain yang tidak berpasangan" % (
            nama, max(0, len(hilang_a) - maks_tampil) + max(0, len(hilang_b) - maks_tampil)))
    n_sel = 0
    n_beda_sel = 0
    for k in pa:
        if k not in pb:
            continue
        for c, (x, y) in enumerate(zip(pa[k], pb[k])):
            n_sel += 1
            if not sama(x, y, tol):
                n_beda_sel += 1
                if n_beda_sel <= maks_tampil:
                    beda.append("%s: kunci %s kolom %s: hasil=%r acuan=%r" % (nama, list(k[0]), kolom_a[c], x, y))
    if n_beda_sel > maks_tampil:
        beda.append("%s: ... dan %d sel lain yang beda" % (nama, n_beda_sel - maks_tampil))
    return beda, n_sel


def bandingkan_folder(hasil, acuan, tol=1e-9, nama_hanya=None):
    """(laporan sebagai daftar baris teks, jumlah tabel cocok, jumlah tabel bermasalah, jumlah sel)."""
    laporan, ok, buruk, sel = [], 0, 0, 0
    for nama in ka.NAMA_ANALISIS:
        if nama_hanya and nama not in nama_hanya:
            continue
        ja, jb = os.path.join(hasil, nama + ".csv"), os.path.join(acuan, nama + ".csv")
        if not os.path.exists(ja):
            laporan.append("HILANG  %s (tidak ada di %s)" % (nama, hasil))
            buruk += 1
            continue
        if not os.path.exists(jb):
            laporan.append("HILANG  %s (tidak ada di acuan %s)" % (nama, acuan))
            buruk += 1
            continue
        ca, ba = ka.baca_csv(ja)
        cb, bb = ka.baca_csv(jb)
        beda, n = bandingkan_tabel(nama, ca, ba, cb, bb, ka.KUNCI[nama], tol)
        sel += n
        if beda:
            buruk += 1
            laporan.append("BEDA    %s" % nama)
            laporan.extend("        " + x for x in beda)
        else:
            ok += 1
            laporan.append("COCOK   %-22s %4d baris, %5d sel" % (nama, len(ba), n))
    return laporan, ok, buruk, sel


def main(argv=None):
    ap = argparse.ArgumentParser(description="Bandingkan tabel analitik hasil Spark dengan acuan Python.")
    ap.add_argument("--hasil", default=str(AKAR / "results" / "analitik" / "S1"))
    ap.add_argument("--acuan", help="folder acuan (bawaan: dipilih dari nama folder --hasil, lihat atas)")
    ap.add_argument("--toleransi", type=float, default=1e-9)
    args = ap.parse_args(argv)
    args.acuan = args.acuan or acuan_untuk(args.hasil)
    for j in (args.hasil, args.acuan):
        if not os.path.isdir(j):
            raise SystemExit("Folder %s tidak ada." % j)
    laporan, ok, buruk, sel = bandingkan_folder(args.hasil, args.acuan, args.toleransi)
    print("Hasil : %s" % args.hasil)
    print("Acuan : %s" % args.acuan)
    print("\n".join(laporan))
    print()
    if buruk:
        print("ADA SELISIH: %d tabel cocok, %d bermasalah." % (ok, buruk))
        return 1
    print("SEMUA TABEL COCOK (%d tabel, %d sel dibandingkan, toleransi relatif %g)" % (ok, sel, args.toleransi))
    return 0


if __name__ == "__main__":
    sys.exit(main())
