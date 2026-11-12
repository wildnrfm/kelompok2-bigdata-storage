#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cek_data.py  --  pemeriksa berkas data Sen12Landslides (mentah dan hasil konversi)
Kelompok 2 - Tugas 2 Big Data Storage

CARA PAKAI (dari akar repo, PowerShell; hanya Python bawaan):
  python data/cek_data.py --raw            cocokkan data/raw/ dengan data/raw/SHA256.txt
  python data/cek_data.py --raw --tulis    (Wildan, sekali) tulis data/raw/SHA256.txt
  python data/cek_data.py --skala S1       periksa data/out/s1 (juga S10, S100)
  python data/cek_data.py --skala S100 --cepat   lewati pemeriksaan NDJSON (lebih singkat)
  python data/cek_data.py --ukuran         cetak ukuran berkas semua skala (untuk KAMUS_DATA.md)

Yang diperiksa pada --skala (setiap baris berawalan OK atau GAGAL):
  * keempat berkas ada; header CSV sesuai kontrak; jumlah baris sesuai skala
    (S1 = 74.956 anotasi + 4.392 patch; S10 = 10x; S100 = 100x)
  * ann_id unik dan berurutan lengkap dari 0; patch_id unik; sim_batch 0..(faktor-1) dengan
    jumlah baris yang sama per batch
  * koordinat: bujur -180..180, lintang -90..90, kotak pembatas bermakna (min < maks), titik
    pusat di dalam kotaknya; tanggal berbentuk ISO yang sah
  * NDJSON dan CSV berisi hal yang sama baris demi baris (id, titik pusat, kotak, tanggal)
  * sebaran lokasi, pemicu, dan jenis adalah kelipatan tepat dari data asli (hanya profil laporan)
Kode keluar 0 bila semua lulus, 1 bila ada yang gagal.
"""
import argparse
import collections
import csv
import hashlib
import json
import sys
from datetime import date
from pathlib import Path

import convert_inventory as ci

try:
    sys.stdout.reconfigure(errors="replace")
except Exception:
    pass

ROOT = ci.ROOT
RAW_DIR = ci.RAW_DIR
OUT_DIR = ROOT / "data" / "out"
FAKTOR = {"S1": 1, "S10": 10, "S100": 100}
HASIL = {"gagal": 0, "lulus": 0}


def lapor(nama, ok, rinci=""):
    if ok:
        HASIL["lulus"] += 1
        print("  OK     " + nama)
    else:
        HASIL["gagal"] += 1
        print("  GAGAL  " + nama)
        if rinci:
            print("         " + str(rinci).replace("\n", "\n         ")[:900])


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for blok in iter(lambda: f.read(1 << 20), b""):
            h.update(blok)
    return h.hexdigest()


# --------------------------------------------------------------------------
# Berkas asli
# --------------------------------------------------------------------------
def periksa_raw(tulis, raw=RAW_DIR):
    raw = Path(raw)
    try:
        inv = ci.cari_inventaris(raw)
        spl = ci.cari_splits(raw)
    except FileNotFoundError as e:
        print("GAGAL: %s" % e)
        return 1
    berkas = [inv, spl]
    cs = raw / "SHA256.txt"
    print("Berkas asli di %s" % raw)
    hasil = [(sha256_file(p), p.name, p.stat().st_size) for p in berkas]
    for h, nama, ukuran in hasil:
        print("  %s  %-24s %12d byte" % (h, nama, ukuran))
    if tulis:
        cs.write_text("".join("%s  %s\n" % (h, nama) for h, nama, _u in hasil),
                      encoding="utf-8", newline="\n")
        print("Tertulis %s. Commit berkas ini bersama data/raw/." % cs)
        return 0
    if not cs.exists():
        print("Belum ada %s. (Wildan menulisnya sekali dengan: python data/cek_data.py --raw --tulis)" % cs)
        return 1
    harap = {}
    for baris in cs.read_text(encoding="utf-8-sig").splitlines():
        if baris.strip():
            h, nama = baris.split(None, 1)
            harap[nama.strip()] = h
    beda = 0
    for h, nama, _u in hasil:
        ok = harap.get(nama) == h
        print("%-9s %s" % ("COCOK" if ok else "BEDA", nama))
        beda += 0 if ok else 1
    if beda:
        print("\n%d berkas BEDA dari SHA256.txt. Ambil ulang: git pull --rebase; bila tetap beda, "
              "tulis [BLOKIR]." % beda)
        return 1
    print("\nBerkas asli COCOK dengan SHA256.txt.")
    return 0


# --------------------------------------------------------------------------
# Hasil konversi
# --------------------------------------------------------------------------
def hitung_baris_csv(p):
    with open(p, encoding="utf-8", newline="") as f:
        return sum(1 for _ in csv.reader(f)) - 1


def harapan_jumlah(skala, profil, folder_s1):
    """(anotasi, patch) yang diharapkan untuk skala ini; None bila tidak bisa dipastikan."""
    f = FAKTOR[skala]
    if profil == "laporan":
        return ci.LAPORAN["n"] * f, ci.LAPORAN["patch"]["n"] * f
    s1 = Path(folder_s1)
    if skala == "S1":
        return None, None
    if (s1 / "annotations.csv").is_file() and (s1 / "patches.csv").is_file():
        return hitung_baris_csv(s1 / "annotations.csv") * f, hitung_baris_csv(s1 / "patches.csv") * f
    return None, None


def periksa_skala(skala, folder, profil, cepat, harap_a=None, harap_p=None, folder_s1=None):
    folder = Path(folder)
    f = FAKTOR[skala]
    print("Memeriksa %s (skala %s, profil %s)" % (folder, skala, profil))
    nama_berkas = ["annotations.ndjson", "annotations.csv", "patches.ndjson", "patches.csv"]
    ada = {n: (folder / n).is_file() for n in nama_berkas}
    for n in nama_berkas:
        lapor("%s ada" % n, ada[n], "tidak ditemukan di %s" % folder)
    if not all(ada.values()):
        return
    if harap_a is None:
        harap_a, harap_p = harapan_jumlah(skala, profil, folder_s1 or (OUT_DIR / "s1"))

    # ---- anotasi: CSV (dibaca penuh), NDJSON berdampingan
    nd = None if cepat else open(folder / "annotations.ndjson", encoding="utf-8")
    kunci_tgl = dict(ci.KOLOM_TANGGAL)
    tgl_ok = {}
    n = 0
    visit = None
    sim = collections.Counter()
    cnt = {"location": collections.Counter(), "event_type": collections.Counter(),
           "type": collections.Counter()}
    tanpa_event_date = 0
    salah = collections.defaultdict(list)       # nama pemeriksaan -> contoh kegagalan

    def catat(nama, rinci):
        if len(salah[nama]) < 3:
            salah[nama].append(rinci)

    try:
        with open(folder / "annotations.csv", encoding="utf-8", newline="") as fc:
            pembaca = csv.reader(fc)
            kepala = next(pembaca)
            lapor("header annotations.csv sesuai kontrak (23 kolom)", kepala == ci.KOLOM_ANOTASI,
                  "ada: %s" % ",".join(kepala))
            if kepala != ci.KOLOM_ANOTASI:
                return
            for b in pembaca:
                n += 1
                if len(b) != 23:
                    catat("jumlah kolom tiap baris 23", "baris %d berisi %d kolom" % (n, len(b)))
                    continue
                aid = int(b[0])
                if visit is None:
                    visit = bytearray(1)
                if aid >= len(visit):
                    visit.extend(bytearray(max(aid + 1 - len(visit), len(visit))))
                if visit[aid]:
                    catat("ann_id unik", "ann_id %d kembar (baris %d)" % (aid, n))
                visit[aid] = 1
                sim[b[22]] += 1
                cnt["location"][b[1]] += 1
                cnt["event_type"][b[3] or None] += 1
                cnt["type"][b[4]] += 1
                lon, lat = float(b[16]), float(b[17])
                x0, y0, x1, y1 = float(b[18]), float(b[19]), float(b[20]), float(b[21])
                if not (-180 <= x0 < x1 <= 180 and -90 <= y0 < y1 <= 90):
                    catat("kotak pembatas sah (min < maks, di dalam bujur/lintang)",
                          "ann_id %d: %s,%s,%s,%s" % (aid, x0, y0, x1, y1))
                if not (x0 <= lon <= x1 and y0 <= lat <= y1):
                    catat("titik pusat di dalam kotaknya", "ann_id %d" % aid)
                for k in range(10, 16):
                    t = b[k]
                    if t:
                        ok = tgl_ok.get(t)
                        if ok is None:
                            try:
                                date.fromisoformat(t)
                                ok = len(t) == 10
                            except ValueError:
                                ok = False
                            tgl_ok[t] = ok
                        if not ok:
                            catat("tanggal ISO sah", "ann_id %d: '%s'" % (aid, t))
                if not b[11]:
                    tanpa_event_date += 1
                if nd is not None:
                    baris = nd.readline()
                    if not baris:
                        catat("NDJSON sepanjang CSV", "NDJSON habis di baris %d" % n)
                        nd = None
                        continue
                    d = json.loads(baris)
                    if d["_id"] != aid:
                        catat("NDJSON dan CSV: ann_id sama", "baris %d: %s vs %s" % (n, d["_id"], aid))
                    if d["center"]["coordinates"] != [lon, lat]:
                        catat("NDJSON dan CSV: titik pusat sama", "ann_id %d" % aid)
                    if d["bbox"]["coordinates"][0] != [[x0, y0], [x1, y0], [x1, y1], [x0, y1], [x0, y0]]:
                        catat("NDJSON dan CSV: kotak pembatas sama", "ann_id %d" % aid)
                    tg = d.get("dates", {})
                    for kol, kunci in ci.KOLOM_TANGGAL:
                        teks = b[ci.KOLOM_ANOTASI.index(kol)]
                        v = tg.get(kunci)
                        if (v["$date"][:10] if v else "") != teks:
                            catat("NDJSON dan CSV: tanggal sama", "ann_id %d kolom %s" % (aid, kol))
                    if (d.get("event_type") or "") != b[3]:
                        catat("NDJSON dan CSV: event_type sama", "ann_id %d" % aid)
                    if d["sim_batch"] != int(b[22]):
                        catat("NDJSON dan CSV: sim_batch sama", "ann_id %d" % aid)
            if nd is not None and nd.readline():
                catat("NDJSON sepanjang CSV", "NDJSON memiliki baris lebih banyak dari CSV")
    finally:
        if nd is not None:
            nd.close()

    lapor("jumlah baris annotations.csv = %s" % (harap_a if harap_a is not None else "(> 0)"),
          n == harap_a if harap_a is not None else n > 0, "ada %d" % n)
    if visit is not None:
        lengkap = sum(visit[:n]) == n and len(visit) >= n and all(visit[:n])
        lapor("ann_id berurutan lengkap 0..%d tanpa lubang" % (n - 1), lengkap,
              "ada lubang atau ann_id di luar 0..%d" % (n - 1))
    for nama, contoh in salah.items():
        lapor(nama, False, "\n".join(contoh))
    if not cepat and not any(k.startswith("NDJSON") for k in salah):
        lapor("NDJSON dan CSV berisi hal yang sama baris demi baris", True)
    per_batch = set(sim.values())
    lapor("sim_batch 0..%d, tiap batch jumlah baris sama" % (f - 1),
          set(sim) == {str(i) for i in range(f)} and len(per_batch) == 1,
          dict(list(sim.items())[:6]))
    if profil == "laporan":
        L = ci.LAPORAN
        lapor("sebaran location = kelipatan %d dari data asli" % f,
              dict(cnt["location"]) == {k: v * f for k, v in L["location"].items()},
              dict(cnt["location"]))
        et = {k: v for k, v in cnt["event_type"].items() if k}
        lapor("sebaran event_type = kelipatan %d dari data asli" % f,
              et == {k: v * f for k, v in L["event_type"].items()}, et)
        lapor("sebaran type = kelipatan %d dari data asli" % f,
              dict(cnt["type"]) == {k: v * f for k, v in L["type"].items()}, dict(cnt["type"]))
        lapor("anotasi tanpa event_date = %d" % (L["tanpa_event_date"] * f),
              tanpa_event_date == L["tanpa_event_date"] * f, tanpa_event_date)

    # ---- patch
    kolom_p = None
    ids = set()
    n_p = 0
    sim_p = collections.Counter()
    split_ok = True
    salah_p = []
    ndp = open(folder / "patches.ndjson", encoding="utf-8")
    try:
        with open(folder / "patches.csv", encoding="utf-8", newline="") as fc:
            pembaca = csv.reader(fc)
            kolom_p = next(pembaca)
            lapor("header patches.csv sesuai kontrak (8 kolom)", kolom_p == ci.KOLOM_PATCH,
                  "ada: %s" % ",".join(kolom_p))
            for b in pembaca:
                n_p += 1
                if b[0] in ids:
                    salah_p.append("patch_id kembar: %s" % b[0])
                ids.add(b[0])
                sim_p[b[7]] += 1
                if b[1] not in ("train", "val", "test"):
                    split_ok = False
                d = json.loads(ndp.readline() or "{}")
                if d.get("_id") != b[0] or d.get("split") != b[1]:
                    salah_p.append("NDJSON dan CSV beda di baris %d" % n_p)
            if ndp.readline():
                salah_p.append("patches.ndjson punya baris lebih banyak dari CSV")
    finally:
        ndp.close()
    lapor("jumlah baris patches.csv = %s" % (harap_p if harap_p is not None else "(> 0)"),
          n_p == harap_p if harap_p is not None else n_p > 0, "ada %d" % n_p)
    lapor("patch_id unik; NDJSON dan CSV sama", not salah_p, "; ".join(salah_p[:3]))
    lapor("split hanya train, val, test", split_ok)
    lapor("sim_batch patch 0..%d, tiap batch jumlah baris sama" % (f - 1),
          set(sim_p) == {str(i) for i in range(f)} and len(set(sim_p.values())) == 1,
          dict(list(sim_p.items())[:6]))


def cetak_ukuran(keluar=OUT_DIR):
    """Ukuran berkas data dalam MB desimal (1 MB = 1.000.000 byte), sama dengan KAMUS_DATA.md."""
    print("%-8s %-20s %12s" % ("skala", "berkas", "MB"))
    total = {}
    ada = False
    for s in ("s1", "s10", "s100"):
        for nama in ("annotations.ndjson", "annotations.csv", "patches.ndjson", "patches.csv"):
            p = Path(keluar) / s / nama
            if p.is_file():
                mb = p.stat().st_size / 1e6
                total[s] = total.get(s, 0.0) + mb
                ada = True
                print("%-8s %-20s %12.2f" % (s, nama, mb))
    for s, mb in total.items():
        print("%-8s %-20s %12.2f%s" % (s, "JUMLAH", mb, "   (= %.2f GB)" % (mb / 1000.0) if mb >= 1000 else ""))
    print("(MB desimal: 1 MB = 1.000.000 byte. Tulis angka ini di tabel bagian 5 KAMUS_DATA.md.)")
    return 0 if ada else 1


def main(argv=None):
    ap = argparse.ArgumentParser(description="Pemeriksa data Sen12Landslides.")
    ap.add_argument("--raw", action="store_true", help="periksa berkas asli di data/raw")
    ap.add_argument("--tulis", action="store_true", help="dengan --raw: tulis SHA256.txt")
    ap.add_argument("--skala", choices=sorted(FAKTOR), help="periksa hasil konversi satu skala")
    ap.add_argument("--folder", help="folder yang diperiksa (bawaan data/out/<skala>)")
    ap.add_argument("--profil", choices=["laporan", "tanpa"], default="laporan",
                    help="laporan = data asli (bawaan); tanpa = data uji buatan")
    ap.add_argument("--harap-anotasi", type=int, help="jumlah anotasi yang diharapkan")
    ap.add_argument("--harap-patch", type=int, help="jumlah patch yang diharapkan")
    ap.add_argument("--cepat", action="store_true", help="lewati pemeriksaan NDJSON")
    ap.add_argument("--ukuran", action="store_true", help="cetak ukuran berkas semua skala")
    ap.add_argument("--raw-folder", default=str(RAW_DIR), help=argparse.SUPPRESS)
    ap.add_argument("--s1-folder", default=str(OUT_DIR / "s1"), help=argparse.SUPPRESS)
    ap.add_argument("--out-folder", default=str(OUT_DIR), help=argparse.SUPPRESS)
    args = ap.parse_args(argv)

    if args.raw:
        return periksa_raw(args.tulis, args.raw_folder)
    if args.ukuran:
        return cetak_ukuran(args.out_folder)
    if args.skala:
        folder = args.folder or str(Path(args.out_folder) / args.skala.lower())
        periksa_skala(args.skala, folder, args.profil, args.cepat,
                      args.harap_anotasi, args.harap_patch, args.s1_folder)
        print()
        if HASIL["gagal"]:
            print("ADA %d PEMERIKSAAN GAGAL (%d lulus). Baca baris GAGAL di atas." % (HASIL["gagal"], HASIL["lulus"]))
            return 1
        print("SEMUA PEMERIKSAAN LULUS (%d)" % HASIL["lulus"])
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
