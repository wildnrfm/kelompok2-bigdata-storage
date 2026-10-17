#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_scales.py  --  buat data simulasi S10 dan S100 dari S1 (seed tetap, sampel bersarang)
Kelompok 2 - Tugas 2 Big Data Storage

ATURAN SIMULASI (sama dengan dokumen rancangan):
  * S1 = data asli (batch 0). Replika ke-b (b = 1, 2, ...) menyalin seluruh S1 dengan
    perubahan di bawah. S10 = batch 0..9, S100 = batch 0..99, jadi S1 ada di S10 dan
    S10 ada di S100 (berkas yang lebih kecil adalah AWALAN berkas yang lebih besar).
  * Seed tetap 20261023; batch b memakai pembangkit acak sendiri (seed + b), jadi hasilnya
    selalu sama di semua laptop. JANGAN mengubah seed: checksum tidak akan cocok.
  * Disalin apa adanya: location, inventory, event_type, type, velocity_c, author,
    reference, event_conf, area. Sebaran miring dan nilai kosong ikut terjaga.
  * Keenam tanggal digeser dengan jumlah hari acak yang SAMA (-365 sampai +365), jadi
    selisih antar tanggal tetap; tanggal kosong tetap kosong.
  * Titik pusat dan kotak pembatas digeser dengan selisih bujur dan lintang acak yang SAMA
    (maksimal 0,25 derajat), dibatasi agar kotak tetap di dalam bujur +-179 dan lintang +-85.
  * ann_id = id asli + 74.956 x b (berurutan, tanpa lubang); sim_batch = b.
    Patch: patch_id diberi akhiran _r<b> untuk b >= 1; jalur citra tidak diubah.
  * Data simulasi hanya untuk uji beban; jangan dilaporkan sebagai kejadian longsor.

CARA PAKAI (dari akar repo, PowerShell; hanya Python bawaan):
  python data/generate_scales.py --scale S10        buat S10 saja
  python data/generate_scales.py --all              buat S10 dan S100 (S100 beberapa menit)
  python data/generate_scales.py --verify           cocokkan dengan data/CHECKSUMS.txt
  python data/generate_scales.py --write-checksums  (Syuep) tulis ulang data/CHECKSUMS.txt
  python data/generate_scales.py --extra-batch 100  batch tambahan untuk uji W8 (data/out/batch100)

Prasyarat: python data/convert_inventory.py sudah dijalankan (ada data/out/s1/).
Hasil: data/out/s10/, data/out/s100/ (tidak di-commit; ada di .gitignore).
"""
import argparse
import hashlib
import random
import sys
import time
from datetime import timedelta
from pathlib import Path

import convert_inventory as ci

try:
    sys.stdout.reconfigure(errors="replace")
except Exception:
    pass

SEED = 20261023                   # seed tetap: jangan diubah
FAKTOR = {"S10": 10, "S100": 100}
URUT_SKALA = ["s1", "s10", "s100"]
BERKAS = ("annotations.ndjson", "annotations.csv", "patches.ndjson", "patches.csv")
GESER_HARI = 365                  # tanggal digeser -365..+365 hari
GESER_DERAJAT = 0.25              # pusat dan kotak digeser sampai 0,25 derajat
BATAS_LON = 179.0
BATAS_LAT = 85.0
OUT_DIR = ci.ROOT / "data" / "out"
CHECKSUM_FILE = ci.ROOT / "data" / "CHECKSUMS.txt"


def geser_anotasi(r, b, stride, u_hari, u_lon, u_lat):
    """Salinan anotasi r untuk batch b dengan tanggal dan lokasi digeser (tiga angka acak u)."""
    hari = int(u_hari * (2 * GESER_HARI + 1)) - GESER_HARI          # -365 .. +365
    lo = max(-GESER_DERAJAT, -BATAS_LON - r["bbox_min_lon"])
    hi = min(GESER_DERAJAT, BATAS_LON - r["bbox_max_lon"])
    dlon = lo + (hi - lo) * u_lon if lo <= hi else 0.0
    lo = max(-GESER_DERAJAT, -BATAS_LAT - r["bbox_min_lat"])
    hi = min(GESER_DERAJAT, BATAS_LAT - r["bbox_max_lat"])
    dlat = lo + (hi - lo) * u_lat if lo <= hi else 0.0

    n = dict(r)
    n["ann_id"] = r["ann_id"] + stride * b
    n["sim_batch"] = b
    if hari:
        d = timedelta(days=hari)
        for kolom, _kunci in ci.KOLOM_TANGGAL:
            if r[kolom] is not None:
                n[kolom] = r[kolom] + d
    x0 = ci.f_koord(r["bbox_min_lon"] + dlon)
    x1 = ci.f_koord(r["bbox_max_lon"] + dlon)
    y0 = ci.f_koord(r["bbox_min_lat"] + dlat)
    y1 = ci.f_koord(r["bbox_max_lat"] + dlat)
    n["bbox_min_lon"], n["bbox_max_lon"], n["bbox_min_lat"], n["bbox_max_lat"] = x0, x1, y0, y1
    n["center_lon"] = min(max(ci.f_koord(r["center_lon"] + dlon), x0), x1)
    n["center_lat"] = min(max(ci.f_koord(r["center_lat"] + dlat), y0), y1)
    return n


def batch_anotasi(dasar, b, stride):
    """Semua anotasi batch b (b >= 1). Tiga angka acak per rekaman, urutan tetap."""
    rng = random.Random(SEED + b)
    acak = rng.random
    return [geser_anotasi(r, b, stride, acak(), acak(), acak()) for r in dasar]


def batch_patch(dasar_patch, b):
    hasil = []
    for p in dasar_patch:
        n = dict(p)
        n["patch_id"] = "%s_r%d" % (p["patch_id"], b)
        n["sim_batch"] = b
        hasil.append(n)
    return hasil


def muat_dasar(basis):
    basis = Path(basis)
    for nama in ("annotations.csv", "patches.csv"):
        if not (basis / nama).is_file():
            raise SystemExit("Belum ada %s.\nJalankan dulu: python data/convert_inventory.py"
                             % (basis / nama))
    dasar = list(ci.baca_anotasi_csv(basis / "annotations.csv"))
    patch = list(ci.baca_patch_csv(basis / "patches.csv"))
    if not dasar:
        raise SystemExit("%s kosong." % (basis / "annotations.csv"))
    stride = max(r["ann_id"] for r in dasar) + 1
    return dasar, patch, stride


def tulis_batch(penulis_list, anotasi, patch):
    """Tulis satu batch ke semua penulis (teks dibuat sekali, ditulis ke tiap penulis)."""
    baris_nd = [ci.anotasi_ndjson(r) + "\n" for r in anotasi]
    baris_csv = [ci.anotasi_csv(r) for r in anotasi]
    patch_nd = [ci.patch_ndjson(r) + "\n" for r in patch]
    patch_csv = [ci.patch_csv(r) for r in patch]
    for w in penulis_list:
        w.tambah_banyak(baris_nd, baris_csv, patch_nd, patch_csv)


def buat(skala, basis, keluar):
    awal = time.time()
    dasar, patch, stride = muat_dasar(basis)
    maks = max(FAKTOR[s] for s in skala)
    penulis = {s: ci.PenulisSkala(Path(keluar) / s.lower()) for s in skala}
    print("Dasar: %d anotasi, %d patch (S1). Membuat %s." % (len(dasar), len(patch),
                                                           ", ".join(skala)))
    try:
        for b in range(maks):
            if b == 0:
                ann, pat = dasar, patch
            else:
                ann, pat = batch_anotasi(dasar, b, stride), batch_patch(patch, b)
            tulis_batch([penulis[s] for s in skala if b < FAKTOR[s]], ann, pat)
            if b and (b % 10 == 0 or b == maks - 1):
                print("  ... batch %d dari %d (%.0f detik)" % (b, maks - 1, time.time() - awal),
                      flush=True)
    finally:
        for w in penulis.values():
            w.tutup()
    for s in skala:
        w = penulis[s]
        print("%s selesai: %d anotasi, %d patch, folder %s" % (s, w.n_anotasi, w.n_patch, w.folder))
    print("Langkah berikut: python data/cek_data.py --skala %s" % skala[-1])


def buat_batch_tambahan(n, basis, keluar):
    if n < 1:
        raise SystemExit("--extra-batch harus >= 1 (batch 0 adalah data asli).")
    dasar, patch, stride = muat_dasar(basis)
    w = ci.PenulisSkala(Path(keluar) / ("batch%d" % n))
    try:
        tulis_batch([w], batch_anotasi(dasar, n, stride), batch_patch(patch, n))
    finally:
        w.tutup()
    print("Batch tambahan %d: %d anotasi (ann_id %d sampai %d), %d patch, folder %s"
          % (n, w.n_anotasi, dasar[0]["ann_id"] + stride * n,
             max(r["ann_id"] for r in dasar) + stride * n, w.n_patch, w.folder))


# --------------------------------------------------------------------------
# Checksum (SHA-256 isi berkas apa adanya; berkas data dibuat dengan akhir baris LF)
# --------------------------------------------------------------------------
def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for blok in iter(lambda: f.read(1 << 20), b""):
            h.update(blok)
    return h.hexdigest()


def berkas_terlacak(keluar):
    """(nama relatif terhadap folder data, jalur) untuk S1, S10, S100 yang sudah ada."""
    keluar = Path(keluar)
    data_dir = keluar.parent
    hasil = []
    for s in URUT_SKALA:
        for nama in BERKAS:
            p = keluar / s / nama
            if p.exists():
                hasil.append((p.relative_to(data_dir).as_posix(), p))
    return hasil


def tulis_checksum(keluar, berkas_cs):
    item = berkas_terlacak(keluar)
    if not item:
        raise SystemExit("Belum ada berkas. Jalankan convert_inventory.py dan "
                         "generate_scales.py dulu.")
    baris = ["%s  %s" % (sha256_of(p), rel) for rel, p in item]
    Path(berkas_cs).write_text("\n".join(baris) + "\n", encoding="utf-8", newline="\n")
    print("Tertulis %s (%d berkas)" % (berkas_cs, len(baris)))


def verifikasi(keluar, berkas_cs):
    berkas_cs = Path(berkas_cs)
    if not berkas_cs.exists():
        raise SystemExit("%s belum ada. Ambil dulu: git pull --rebase" % berkas_cs)
    data_dir = Path(keluar).parent
    beda = ada = 0
    for baris in berkas_cs.read_text(encoding="utf-8").splitlines():
        if not baris.strip():
            continue
        harap, rel = baris.split(None, 1)
        p = data_dir / rel.strip()
        if not p.exists():
            print("BELUM ADA  %s" % rel.strip())
            continue
        ok = sha256_of(p) == harap
        ada += 1
        print("%-9s  %s" % ("COCOK" if ok else "BEDA", rel.strip()))
        beda += 0 if ok else 1
    if beda:
        print("\n%d berkas BEDA. Pastikan versi Python 3.11 sampai 3.13 dan berkas tidak diubah "
              "tangan; hapus folder skala yang beda lalu buat ulang. Masih beda: [BLOKIR]." % beda)
        sys.exit(1)
    if ada == 0:
        print("\nTidak ada berkas yang bisa dicocokkan. Jalankan convert_inventory.py dulu.")
        sys.exit(1)
    print("\nSemua %d berkas yang ada COCOK." % ada)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Generator data simulasi Sen12Landslides (S10, S100).")
    ap.add_argument("--scale", action="append", choices=sorted(FAKTOR, key=FAKTOR.get),
                    help="skala yang dibuat (boleh diulang)")
    ap.add_argument("--all", action="store_true", help="buat S10 dan S100")
    ap.add_argument("--verify", action="store_true", help="cocokkan dengan data/CHECKSUMS.txt")
    ap.add_argument("--write-checksums", action="store_true",
                    help="tulis ulang data/CHECKSUMS.txt")
    ap.add_argument("--extra-batch", type=int, metavar="N",
                    help="buat satu batch tambahan bernomor N di data/out/batchN (untuk W8)")
    ap.add_argument("--basis", default=str(OUT_DIR / "s1"), help="folder S1 (bawaan data/out/s1)")
    ap.add_argument("--keluar", default=str(OUT_DIR), help="folder keluaran (bawaan data/out)")
    ap.add_argument("--checksums", default=str(CHECKSUM_FILE), help="berkas checksum")
    args = ap.parse_args(argv)

    if args.verify:
        verifikasi(args.keluar, args.checksums)
    elif args.write_checksums:
        tulis_checksum(args.keluar, args.checksums)
    elif args.extra_batch is not None:
        buat_batch_tambahan(args.extra_batch, args.basis, args.keluar)
    elif args.all or args.scale:
        skala = sorted(FAKTOR, key=FAKTOR.get) if args.all else sorted(set(args.scale), key=FAKTOR.get)
        buat(skala, args.basis, args.keluar)
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
