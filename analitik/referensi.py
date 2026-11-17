#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pembanding bebas: menghitung semua tabel analitik dengan Python murni dari CSV.

Tanpa Spark, tanpa SQL, tanpa pustaka luar. Satu kali baca CSV, satu kali hitung. Hasilnya
dipakai sebagai jawaban acuan: keluaran Spark (spark_pipeline.py) harus sama dengan keluaran
berkas ini, dan kueri SQL yang sama diuji di SQLite (uji_sql.py) terhadap berkas ini.

Pemakaian (dari akar repo; hanya Python bawaan):
  python analitik/referensi.py --skala S1                  tulis analitik/referensi_S1/*.csv
  python analitik/referensi.py --skala S10 --keluar X      S10: sekitar 1 menit
  python analitik/referensi.py --folder data/out/s1 --keluar X
  python analitik/referensi.py --skala S10 --hanya-asli --keluar X    hanya baris sim_batch = 0
                                                           (hasilnya harus sama dengan S1)

Aturan yang ditiru dari Spark SQL (supaya hasilnya sebanding):
  - sel CSV kosong = NULL; fungsi agregat mengabaikan NULL; urutan menaik menaruh NULL di awal
  - TRIM hanya membuang spasi; floor(log10(luas)) = NULL bila luas kosong atau <= 0
  - persentil EKSAK: posisi (n-1)*p dengan interpolasi linear (rumus percentile() Spark/Hive)
  - count(*) - count(DISTINCT kolom) menghitung baris ber-NULL sebagai duplikat (sama seperti SQL)
"""
import argparse
import csv
import datetime
import math
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kueri_analitik as ka  # noqa: E402

AKAR = Path(__file__).resolve().parent.parent
try:
    csv.field_size_limit(10 ** 7)
except Exception:  # noqa: BLE001
    pass


# ----------------------------------------------------------------------------- alat kecil
def kunci_urut(t):
    """Kunci pengurutan menaik yang menaruh None di awal (seperti Spark dan SQLite)."""
    return tuple((x is not None, x) for x in t)


def persentil(nilai, p):
    """Persentil eksak dengan interpolasi linear atas data terurut; None bila tidak ada data."""
    v = sorted(nilai)
    n = len(v)
    if n == 0:
        return None
    pos = (n - 1) * p
    bawah = int(math.floor(pos))
    atas = int(math.ceil(pos))
    if bawah == atas or v[bawah] == v[atas]:
        return float(v[bawah])
    return (atas - pos) * v[bawah] + (pos - bawah) * v[atas]


def rata2(nilai):
    return math.fsum(nilai) / len(nilai) if nilai else None


def mn(nilai):
    return min(nilai) if nilai else None


def mx(nilai):
    return max(nilai) if nilai else None


def lantai(x):
    return None if x is None else int(math.floor(x))


def teks_kosong(v):
    """Kolom teks dianggap kosong bila kosong atau hanya berisi spasi (TRIM(...) = '')."""
    return v is None or v.strip(" ") == ""


def bersih(v, label):
    """COALESCE(NULLIF(TRIM(v), ''), label)."""
    return label if teks_kosong(v) else v.strip(" ")


def _ubah(tipe, teks):
    if teks == "":
        return None
    if tipe in ("long", "int"):
        return int(teks)
    if tipe == "double":
        return float(teks)
    if tipe == "date":
        return datetime.date(int(teks[0:4]), int(teks[5:7]), int(teks[8:10]))
    return teks


def baca_bertipe(jalur, skema):
    """Hasilkan (daftar nilai bertipe per baris, daftar teks mentah per baris) satu per satu."""
    with open(jalur, encoding="utf-8", newline="") as f:
        r = csv.reader(f)
        kepala = next(r)
        harap = [n for n, _ in skema]
        if kepala != harap:
            raise SystemExit("Kolom %s tidak sesuai skema.\n  ada  : %s\n  harap: %s" % (jalur, kepala, harap))
        tipe = [t for _, t in skema]
        for b in r:
            if len(b) != len(tipe):
                raise SystemExit("%s: baris dengan %d kolom, harap %d" % (jalur, len(b), len(tipe)))
            yield [_ubah(t, x) for t, x in zip(tipe, b)], b


def muat_bertipe(folder, hanya_asli=False):
    """Seluruh anotasi dan patch sebagai daftar kamus bertipe. Hanya untuk data kecil (uji_sql.py)."""
    folder = Path(folder)
    ann = [dict(zip([n for n, _ in ka.SKEMA_ANOTASI], v))
           for v, _ in baca_bertipe(folder / "annotations.csv", ka.SKEMA_ANOTASI)]
    pat = [dict(zip([n for n, _ in ka.SKEMA_PATCH], v))
           for v, _ in baca_bertipe(folder / "patches.csv", ka.SKEMA_PATCH)]
    if hanya_asli:
        ann = [a for a in ann if a["sim_batch"] == 0]
        pat = [p for p in pat if p["sim_batch"] == 0]
    return ann, pat


# ----------------------------------------------------------------------------- perhitungan
def hitung(folder, hanya_asli=False):
    """Kembalikan {nama_analisis: (kolom, baris)} untuk semua ANALISIS."""
    folder = Path(folder)
    ia = dict((n, i) for i, (n, _) in enumerate(ka.SKEMA_ANOTASI))
    ip = dict((n, i) for i, (n, _) in enumerate(ka.SKEMA_PATCH))

    # ---- penghitung per kolom (q1), pemeriksaan (q2), dan himpunan (q0)
    n_ann = n_asli = 0
    kosong_ann = dict((n, 0) for n, _ in ka.SKEMA_ANOTASI)
    kosong_pat = dict((n, 0) for n, _ in ka.SKEMA_PATCH)
    himp = {"inv": set(), "jenis": set(), "lokasi": set(), "penulis": set(), "ann_id": set(), "patch_id": set()}
    cek = dict((k, 0) for k in (
        "area_kosong", "area_nol_atau_negatif", "bbox_terbalik", "conf_di_luar_0_1", "jenis_kejadian_kosong",
        "koordinat_di_luar_rentang", "patch_inventaris_tanpa_anotasi", "piksel_anotasi_negatif",
        "pusat_di_luar_bbox", "tanpa_tanggal_apa_pun", "urutan_tanggal_salah"))
    inv_ann_mentah = set()
    n_per_inv = {}

    # ---- kelompok analitik
    a1, a2, a3, a3b, a4a, a4b, a5, a7, a8 = {}, {}, {}, {}, {}, {}, {}, {}, {}

    for v, mentah in baca_bertipe(folder / "annotations.csv", ka.SKEMA_ANOTASI):
        if hanya_asli and v[ia["sim_batch"]] != 0:
            continue
        n_ann += 1
        for (nama, tipe), teks in zip(ka.SKEMA_ANOTASI, mentah):
            if (tipe == "string" and teks.strip(" ") == "") or (tipe != "string" and teks == ""):
                kosong_ann[nama] += 1
        ann_id, lokasi_m = v[ia["ann_id"]], v[ia["location"]]
        inv, jenis_m, penulis = v[ia["inventory"]], v[ia["event_type"]], v[ia["author"]]
        conf, area = v[ia["event_conf"]], v[ia["area"]]
        pre, ev, post = v[ia["pre_date"]], v[ia["event_date"]], v[ia["post_date"]]
        lon, lat = v[ia["center_lon"]], v[ia["center_lat"]]
        bx0, by0, bx1, by1 = v[ia["bbox_min_lon"]], v[ia["bbox_min_lat"]], v[ia["bbox_max_lon"]], v[ia["bbox_max_lat"]]
        if v[ia["sim_batch"]] == 0:
            n_asli += 1
        if not teks_kosong(inv):
            himp["inv"].add(inv.strip(" "))
        if not teks_kosong(jenis_m):
            himp["jenis"].add(jenis_m.strip(" "))
        if lokasi_m is not None:
            himp["lokasi"].add(lokasi_m)
        if penulis is not None:
            himp["penulis"].add(penulis)
        if ann_id is not None:
            himp["ann_id"].add(ann_id)
        if inv is not None:
            inv_ann_mentah.add(inv)
            n_per_inv[inv] = n_per_inv.get(inv, 0) + 1

        # ---- pemeriksaan q2 (satu baris dihitung bila kondisinya BENAR, NULL tidak dihitung)
        if area is None:
            cek["area_kosong"] += 1
        elif area <= 0:
            cek["area_nol_atau_negatif"] += 1
        if (bx0 is not None and bx1 is not None and bx0 > bx1) or (by0 is not None and by1 is not None and by0 > by1):
            cek["bbox_terbalik"] += 1
        if conf is not None and (conf < 0 or conf > 1):
            cek["conf_di_luar_0_1"] += 1
        if teks_kosong(jenis_m):
            cek["jenis_kejadian_kosong"] += 1
        if ((lon is not None and (lon < -180 or lon > 180)) or (lat is not None and (lat < -90 or lat > 90))):
            cek["koordinat_di_luar_rentang"] += 1
        if ((lon is not None and bx0 is not None and lon < bx0) or (lon is not None and bx1 is not None and lon > bx1)
                or (lat is not None and by0 is not None and lat < by0) or (lat is not None and by1 is not None and lat > by1)):
            cek["pusat_di_luar_bbox"] += 1
        if pre is None and ev is None and post is None:
            cek["tanpa_tanggal_apa_pun"] += 1
        if (pre is not None and ev is not None and pre > ev) or (ev is not None and post is not None and ev > post):
            cek["urutan_tanggal_salah"] += 1

        # ---- kolom turunan (SQL_PERKAYA)
        lokasi = lokasi_m
        inventaris = bersih(inv, ka.TANPA_INVENTARIS)
        jenis = bersih(jenis_m, ka.KOSONG)
        tahun = ev.year if ev is not None else None
        bulan = ev.month if ev is not None else None
        hemisfer = "utara" if (lat is not None and lat >= 0) else "selatan"
        sel_pra = (ev - pre).days if (ev is not None and pre is not None) else None
        sel_pasca = (post - ev).days if (post is not None and ev is not None) else None
        dekade = lantai(math.log10(area)) if (area is not None and area > 0) else None
        gx = lantai(lon * 10) if lon is not None else None
        gy = lantai(lat * 10) if lat is not None else None

        g = a1.setdefault((tahun, jenis), [0, set()])
        g[0] += 1
        if lokasi is not None:
            g[1].add(lokasi)
        a2[(bulan, hemisfer, jenis)] = a2.get((bulan, hemisfer, jenis), 0) + 1
        g = a3.setdefault((lokasi, inventaris, jenis), [0, [], [], []])     # n, tahun, area, conf
        g[0] += 1
        if tahun is not None:
            g[1].append(tahun)
        if area is not None:
            g[2].append(area)
        if conf is not None:
            g[3].append(conf)
        if ev is not None:
            a3b[(lokasi, ev)] = a3b.get((lokasi, ev), 0) + 1
        daftar_area = a4a.setdefault(jenis, [])
        if area is not None:
            daftar_area.append(area)
        if dekade is not None:
            a4b[(dekade, jenis)] = a4b.get((dekade, jenis), 0) + 1
        g = a5.setdefault((gx, gy), [0, set(), [], []])                      # n, lokasi, lon, lat
        g[0] += 1
        if lokasi is not None:
            g[1].add(lokasi)
        if lon is not None:
            g[2].append(lon)
        if lat is not None:
            g[3].append(lat)
        g = a7.setdefault(jenis, [0, [], [], []])                            # n, pra, pasca, conf
        g[0] += 1
        if sel_pra is not None:
            g[1].append(sel_pra)
        if sel_pasca is not None:
            g[2].append(sel_pasca)
        if conf is not None:
            g[3].append(conf)
        if ev is not None:
            g = a8.setdefault(ev, [0, set()])
            g[0] += 1
            if lokasi is not None:
                g[1].add(lokasi)

    # ---- patch
    n_pat = 0
    a6 = {}
    patch_ids = 0
    for v, mentah in baca_bertipe(folder / "patches.csv", ka.SKEMA_PATCH):
        if hanya_asli and v[ip["sim_batch"]] != 0:
            continue
        n_pat += 1
        for (nama, tipe), teks in zip(ka.SKEMA_PATCH, mentah):
            if (tipe == "string" and teks.strip(" ") == "") or (tipe != "string" and teks == ""):
                kosong_pat[nama] += 1
        if v[ip["patch_id"]] is not None:
            himp["patch_id"].add(v[ip["patch_id"]])
        inv, split, piksel = v[ip["inventory"]], v[ip["split"]], v[ip["pixel_annotated"]]
        if inv is not None and inv not in inv_ann_mentah:
            cek["patch_inventaris_tanpa_anotasi"] += 1
        if piksel is not None and piksel < 0:
            cek["piksel_anotasi_negatif"] += 1
        g = a6.setdefault(inv, [0, 0, 0, 0, []])                             # n, train, val, test, piksel
        g[0] += 1
        if split == "train":
            g[1] += 1
        elif split == "val":
            g[2] += 1
        elif split == "test":
            g[3] += 1
        if piksel is not None:
            g[4].append(piksel)

    hasil = {}

    # ---- q0
    q0 = [("anotasi", n_ann), ("anotasi_asli_sim0", n_asli), ("inventaris_berbeda", len(himp["inv"])),
          ("jenis_kejadian_berbeda", len(himp["jenis"])), ("lokasi_berbeda", len(himp["lokasi"])),
          ("patch", n_pat), ("penulis_berbeda", len(himp["penulis"]))]
    hasil["q0_hitung"] = (["metrik", "nilai"], sorted(q0))

    # ---- q1
    q1 = []
    for tabel, skema, kos, n in (("annotations", ka.SKEMA_ANOTASI, kosong_ann, n_ann),
                                 ("patches", ka.SKEMA_PATCH, kosong_pat, n_pat)):
        for nama, _ in skema:
            q1.append((tabel, nama, n, kos[nama]))
    hasil["q1_kolom_kosong"] = (["tabel", "kolom", "n_total", "n_kosong"], sorted(q1))

    # ---- q2
    q2 = [("ann_id_ganda", n_ann - len(himp["ann_id"])), ("patch_id_ganda", n_pat - len(himp["patch_id"]))]
    q2 += sorted(cek.items())
    hasil["q2_pemeriksaan"] = (["pemeriksaan", "n_langgar"], sorted(q2))

    # ---- a1, a2
    hasil["a1_tahun_jenis"] = (["tahun", "jenis", "n", "n_lokasi"],
                               sorted(((k[0], k[1], g[0], len(g[1])) for k, g in a1.items()), key=kunci_urut))
    hasil["a2_bulan_hemisfer"] = (["bulan", "hemisfer", "jenis", "n"],
                                  sorted(((k[0], k[1], k[2], n) for k, n in a2.items()), key=kunci_urut))

    # ---- a3
    baris3 = [(k[0], k[1], k[2], g[0], mn(g[1]), mx(g[1]), persentil(g[2], 0.5), rata2(g[3])) for k, g in a3.items()]
    baris3.sort(key=lambda r: (-r[3], kunci_urut(r[:3])))
    hasil["a3_lokasi"] = (["lokasi", "inventaris", "jenis", "n", "tahun_min", "tahun_maks", "area_p50", "conf_rata2"], baris3)

    # ---- a3b: tanggal kejadian berbeda per lokasi (hanya baris bertanggal)
    per_lokasi = {}
    for (lok, tgl), n in a3b.items():
        g = per_lokasi.setdefault(lok, [0, 0, 0, tgl, tgl])      # n, n_tanggal, hari terpadat, tanggal awal, akhir
        g[0] += n
        g[1] += 1
        g[2] = max(g[2], n)
        g[3] = min(g[3], tgl)
        g[4] = max(g[4], tgl)
    baris3b = [(lok, g[0], g[1], g[2], g[3], g[4]) for lok, g in per_lokasi.items()]
    baris3b.sort(key=lambda r: (-r[1], kunci_urut(r[:1])))
    hasil["a3b_lokasi_tanggal"] = (["lokasi", "n_bertanggal", "n_tanggal", "n_hari_terpadat", "tanggal_awal",
                                    "tanggal_akhir"], baris3b)

    # ---- a4a, a4b
    baris4 = [(j, len(a), mn(a), persentil(a, 0.05), persentil(a, 0.25), persentil(a, 0.5),
               persentil(a, 0.75), persentil(a, 0.95), mx(a)) for j, a in a4a.items()]
    hasil["a4a_area_jenis"] = (["jenis", "n", "area_min", "p05", "p25", "p50", "p75", "p95", "area_maks"],
                               sorted(baris4, key=lambda r: kunci_urut(r[:1])))
    hasil["a4b_area_dekade"] = (["dekade_area", "jenis", "n"],
                                sorted(((k[0], k[1], n) for k, n in a4b.items()), key=kunci_urut))

    # ---- a5
    sel = [(k[0], k[1], g[0], len(g[1]), rata2(g[2]), rata2(g[3])) for k, g in a5.items()]
    sel.sort(key=lambda r: (-r[2], kunci_urut(r[:2])))
    hasil["a5a_sel_terpadat"] = (["gx", "gy", "n", "n_lokasi", "lon_rata2", "lat_rata2"], sel[:20])
    ns = [g[0] for g in a5.values()]
    hasil["a5b_sel_ringkas"] = (["n_sel", "n_sel_1", "p50_per_sel", "p95_per_sel", "maks_per_sel", "n_total"],
                                [(len(ns), sum(1 for x in ns if x == 1), persentil(ns, 0.5), persentil(ns, 0.95),
                                  mx(ns), sum(ns))])

    # ---- a6
    baris6 = []
    for inv, g in a6.items():
        baris6.append((inv, g[0], g[1], g[2], g[3], rata2(g[4]), persentil(g[4], 0.5), mx(g[4]),
                       n_per_inv.get(inv, 0) if inv is not None else 0))
    baris6.sort(key=lambda r: kunci_urut(r[:1]))
    hasil["a6_patch_inventaris"] = (["inventaris", "n_patch", "n_train", "n_val", "n_test", "piksel_rata2",
                                     "piksel_p50", "piksel_maks", "n_anotasi"], baris6)

    # ---- a7
    baris7 = []
    for j, g in a7.items():
        n, pra, pasca, conf = g
        baris7.append((j, n, len(pra), persentil(pra, 0.5), persentil(pra, 0.95), mx(pra),
                       len(pasca), persentil(pasca, 0.5), persentil(pasca, 0.95), mx(pasca),
                       rata2(conf), persentil(conf, 0.5), sum(1 for c in conf if c == 1)))
    baris7.sort(key=lambda r: kunci_urut(r[:1]))
    hasil["a7_waktu_kualitas"] = (["jenis", "n", "n_selang_pra", "selang_pra_p50", "selang_pra_p95", "selang_pra_maks",
                                   "n_selang_pasca", "selang_pasca_p50", "selang_pasca_p95", "selang_pasca_maks",
                                   "conf_rata2", "conf_p50", "n_conf_1"], baris7)

    # ---- a8
    baris8 = [(d, g[0], len(g[1])) for d, g in a8.items()]
    baris8.sort(key=lambda r: (-r[1], r[0]))
    hasil["a8_hari_terpadat"] = (["event_date", "n", "n_lokasi"], baris8[:15])

    assert set(hasil) == set(ka.NAMA_ANALISIS), sorted(set(ka.NAMA_ANALISIS) ^ set(hasil))
    return hasil


def tulis_semua(hasil, keluar):
    for nama in ka.NAMA_ANALISIS:
        kolom, baris = hasil[nama]
        ka.tulis_csv(os.path.join(keluar, nama + ".csv"), kolom, baris)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Hitung tabel analitik acuan dengan Python murni.")
    ap.add_argument("--skala", choices=["S1", "S10", "S100"], help="folder data/out/<skala> di akar repo")
    ap.add_argument("--folder", help="folder yang berisi annotations.csv dan patches.csv")
    ap.add_argument("--keluar", help="folder hasil (bawaan analitik/referensi_<SKALA>)")
    ap.add_argument("--hanya-asli", action="store_true", help="hanya baris sim_batch = 0 (bagian data nyata)")
    args = ap.parse_args(argv)
    if not args.skala and not args.folder:
        raise SystemExit("Isi --skala atau --folder.")
    folder = Path(args.folder) if args.folder else AKAR / "data" / "out" / args.skala.lower()
    for n in ("annotations.csv", "patches.csv"):
        if not (folder / n).exists():
            raise SystemExit("Tidak ada %s. Buat dulu dengan data/convert_inventory.py (dan generator untuk S10/S100)."
                             % (folder / n))
    keluar = args.keluar or str(AKAR / "analitik" / ("referensi_%s" % (args.skala or "X")))
    hasil = hitung(folder, args.hanya_asli)
    tulis_semua(hasil, keluar)
    print("Tulis %d tabel ke %s  (anotasi %s, patch %s)" % (
        len(hasil), keluar, hasil["q0_hitung"][1][0][1], dict(hasil["q0_hitung"][1])["patch"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
