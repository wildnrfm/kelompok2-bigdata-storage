#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pembuat data UJI BUATAN yang meniru bentuk Sen12Landslides (bukan data asli).

Dipakai hanya oleh tests/uji_semua.py. Profil "laporan" membuat 74.956 poligon dan 4.392
patch yang angka ringkasnya sengaja disamakan dengan laporan_inventaris.txt (22 Okt 2026),
supaya pemeriksaan diri convert_inventory.py bisa diuji lolos dan gagal.
Profil "kecil" membuat data kecil acak untuk uji cepat (pemeriksaan dasar saja).
"""
import io
import json
import math
import os
import random
import struct
import sys
import zipfile
from datetime import date, timedelta

AKAR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(AKAR, "data"))
import convert_inventory as ci  # noqa: E402

WKT_ESRI = ('GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984",SPHEROID["WGS_1984",6378137.0,298.257223563]],'
            'PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]]')

DBF_KOLOM = [("id", "N", 18, 0), ("pre_date", "C", 80, 0), ("event_date", "C", 80, 0),
             ("post_date", "C", 80, 0), ("event_type", "C", 80, 0), ("author", "C", 144, 0),
             ("area", "N", 24, 15), ("pre_dt2", "C", 80, 0), ("post_dt2", "C", 80, 0),
             ("event_dt2", "C", 80, 0), ("event_conf", "N", 24, 15), ("location", "C", 80, 0),
             ("type", "C", 20, 0), ("velocity_c", "C", 15, 0), ("reference", "C", 50, 0)]

PENULIS = {
    "ferrario": ("Ferrario, M. F. et al. (2023)", "https://zenodo.org/records/8102429"),
    "hohn": ("Höhn, P. et al. (2025)", "https://doi.org/10.57967/hf/5883"),
    "emberson": ("Emberson, R. et al. (2022)", "https://doi.org/10.5194/nhess-22-1129-20"),
    "belair": ("Belair, G.M et al. (2022)", "https://doi.org/10.5066/P9FZUX6N"),
    "kirschbaum": ("Kirschbaum, D. B. et al. (2010, 2015)",
                   "https://catalog.data.gov/dataset/global-"),
}
# lokasi: (bujur, lintang, sebaran derajat)
PUSAT = {
    "Italy": (11.2, 44.3, 0.35), "DominicaMaria": (-61.4, 15.4, 0.10),
    "Newzealand": (172.5, -41.0, 0.25), "Chimanimani": (33.0, -19.8, 0.20),
    "Kyrgyzstan1": (73.0, 40.7, 0.30), "Hokkaido": (142.0, 42.7, 0.25),
    "Hiroshima": (132.5, 34.4, 0.15), "Indonesia": (119.9, -0.9, 0.30),
    "LanaoDelNorte": (124.0, 8.0, 0.10), "Kyrgyzstan2": (73.5, 41.0, 0.20),
    "Thrissur": (76.2, 10.5, 0.10), "Itogon": (120.7, 16.4, 0.05),
    "USA_PuertoRico": (-66.5, 18.2, 0.10), "China": (103.5, 31.0, 0.20),
    "USA_Alaska": (-139.8, 59.7, 0.08), "Nepal": (85.3, 28.0, 0.05),
}


# ---------------------------------------------------------------- penulis SHP / DBF
def _hdr(shape_type, total_bytes, bbox):
    h = struct.pack(">i", 9994) + b"\x00" * 20 + struct.pack(">i", total_bytes // 2)
    h += struct.pack("<ii", 1000, shape_type) + struct.pack("<4d", *bbox) + struct.pack("<4d", 0, 0, 0, 0)
    assert len(h) == 100
    return h


def isi_poligon(cincin):
    """Isi rekaman poligon (tipe 5) dari daftar cincin (tiap cincin daftar (x, y), tertutup)."""
    titik = [p for r in cincin for p in r]
    xs = [p[0] for p in titik]
    ys = [p[1] for p in titik]
    bagian, idx = [], 0
    for r in cincin:
        bagian.append(idx)
        idx += len(r)
    c = struct.pack("<i", 5) + struct.pack("<4d", min(xs), min(ys), max(xs), max(ys))
    c += struct.pack("<ii", len(cincin), len(titik)) + struct.pack("<%di" % len(bagian), *bagian)
    c += struct.pack("<%dd" % (2 * len(titik)), *[v for p in titik for v in p])
    return c


def isi_null():
    return struct.pack("<i", 0)


def tulis_shp_shx(isi, bbox):
    shp, shx, off = [], [], 100
    for i, c in enumerate(isi, 1):
        rec = struct.pack(">ii", i, len(c) // 2) + c
        shp.append(rec)
        shx.append(struct.pack(">ii", off // 2, len(c) // 2))
        off += len(rec)
    a, b = b"".join(shp), b"".join(shx)
    return _hdr(5, 100 + len(a), bbox) + a, _hdr(5, 100 + len(b), bbox) + b


def tulis_dbf(kolom, baris, enc="utf-8"):
    nf = len(kolom)
    panjang_header = 32 + 32 * nf + 1
    panjang_rekaman = 1 + sum(f[2] for f in kolom)
    h = struct.pack("<BBBBIHH", 3, 26, 10, 22, len(baris), panjang_header, panjang_rekaman)
    h += b"\x00" * 17 + b"\x00" + b"\x00\x00"
    for nama, t, ln, dec in kolom:
        h += nama.encode("ascii").ljust(11, b"\x00") + t.encode("ascii") + b"\x00" * 4 + bytes([ln, dec]) + b"\x00" * 14
    h += b"\r"
    bagian = []
    for r in baris:
        rec = [b" "]
        for (nama, t, ln, dec), v in zip(kolom, r):
            if v is None:
                s = b" " * ln
            elif t == "C":
                s = str(v).encode(enc)[:ln].ljust(ln)
            else:
                txt = str(int(v)) if dec == 0 else "%.*f" % (dec, v)
                s = txt.encode("ascii").rjust(ln)
            assert len(s) == ln, (nama, s, ln)
            rec.append(s)
        bagian.append(b"".join(rec))
    return h + b"".join(bagian) + b"\x1a"


# ---------------------------------------------------------------- bentuk poligon
def cincin_cw(cx, cy, r, n, rng=None, goyang=0.0):
    """Cincin searah jarum jam (cincin luar di shapefile), tertutup."""
    pts = []
    for k in range(n):
        rr = r * (1 + (rng.uniform(-goyang, goyang) if rng else 0.0))
        a = -2 * math.pi * k / n
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    pts.append(pts[0])
    return pts


def cincin_ccw(cx, cy, r, n):
    pts = [(cx + r * math.cos(2 * math.pi * k / n), cy + r * math.sin(2 * math.pi * k / n))
           for k in range(n)]
    pts.append(pts[0])
    return pts


# ---------------------------------------------------------------- data laporan
def _daftar_lokasi(rng):
    lok = []
    for nama, n in ci.LAPORAN["location"].items():
        lok += [nama] * n
    rng.shuffle(lok)
    return lok


def _atur_rata2(nilai, target, bebas, lo, hi):
    """Geser nilai pada indeks 'bebas' agar rata-rata semua = target (tetap di [lo, hi])."""
    n = len(nilai)
    for _ in range(40):
        selisih = target * n - sum(nilai)
        if abs(selisih) < 1e-4:
            return
        langkah = selisih / len(bebas)
        for i in bebas:
            nilai[i] = min(hi, max(lo, nilai[i] + langkah))


def buat_laporan(folder):
    """Tulis inventories.zip dan splits_aligned.json di folder. Kembalikan dict kebenaran."""
    L = ci.LAPORAN
    N = L["n"]
    rng = random.Random(20261022)
    os.makedirs(folder, exist_ok=True)
    lokasi = _daftar_lokasi(rng)

    # event_type
    kolam = ["Rainfall"] * 52686 + ["Earthquake"] * 7950 + [None] * 3142
    rng.shuffle(kolam)
    it = iter(kolam)
    event_type = []
    for loc in lokasi:
        if loc == "DominicaMaria":
            event_type.append("Hurricane")
        elif loc == "LanaoDelNorte":
            event_type.append("Tropical Storm")
        elif loc == "Itogon":
            event_type.append("Cyclone")
        else:
            event_type.append(next(it))
    tipe = ["Ice avalanche" if loc == "USA_Alaska" else "Debris flow" for loc in lokasi]

    # penulis dan rujukan
    kolam_p = (["hohn"] * 16306 + ["emberson"] * 10619 + ["belair"] * 328 + ["kirschbaum"] * 181)
    rng.shuffle(kolam_p)
    ip = iter(kolam_p)
    kunci_p = ["ferrario" if loc == "Italy" else next(ip) for loc in lokasi]

    # tanggal: 550 nilai event_date unik, 109 rekaman tanpa tanggal
    awal, akhir = date(2016, 4, 1), date(2023, 5, 16)
    rentang = (akhir - awal).days
    hari = {0, rentang}
    while len(hari) < 550:
        hari.add(rng.randint(0, rentang))
    hari = sorted(hari)
    tanpa = set(rng.sample(range(N), 109))
    ada = [i for i in range(N) if i not in tanpa]
    event = [None] * N
    for k, i in enumerate(ada):
        event[i] = awal + timedelta(days=hari[k] if k < 550 else rng.choice(hari))
    fmt = lambda d: d.isoformat() if d else None
    pre = [fmt(e - timedelta(days=7)) if e else None for e in event]
    post = [fmt(e + timedelta(days=7)) if e else None for e in event]
    pre2 = [fmt(e - timedelta(days=7 + rng.randint(0, 40))) if e else None for e in event]
    post2 = [fmt(e + timedelta(days=7 + rng.randint(0, 80))) if e else None for e in event]
    event2 = [fmt(e + timedelta(days=rng.randint(0, 60))) if e else None for e in event]

    # luas dan keyakinan
    area = [min(5.0e6, max(1.0, rng.lognormvariate(math.log(150), 1.6))) for _ in range(N)]
    area[0], area[1] = L["area"][0], L["area"][1]
    conf = [1.0 if rng.random() < 0.88 else rng.uniform(0.0, 1.0) for _ in range(N)]
    bebas = [i for i in range(N) if conf[i] < 1.0][:3000]
    _atur_rata2(conf, L["event_conf_rata"], bebas, 0.0, 1.0)

    # bentuk: jumlah cincin sesuai laporan (1=74155, 2=475, 3=167, 4=69, 5+=90)
    n_cincin = [1] * N
    cadangan = rng.sample(range(2, N), 475 + 167 + 69 + 90)
    for k, i in enumerate(cadangan):
        n_cincin[i] = 2 if k < 475 else 3 if k < 642 else 4 if k < 711 else rng.randint(5, 8)
    multi_luar = set(cadangan[:9])
    # titik ekstrem agar rentang koordinat sama dengan laporan
    ekstrem = {}
    idx_nz = [i for i, l in enumerate(lokasi) if l == "Newzealand" and n_cincin[i] == 1][:2]
    idx_ak = [i for i, l in enumerate(lokasi) if l == "USA_Alaska" and n_cincin[i] == 1][:2]
    ekstrem[idx_nz[0]] = ("xmax", L["lon"][1])
    ekstrem[idx_nz[1]] = ("ymin", L["lat"][0])
    ekstrem[idx_ak[0]] = ("xmin", L["lon"][0])
    ekstrem[idx_ak[1]] = ("ymax", L["lat"][1])
    besar = next(i for i in range(2, N) if n_cincin[i] == 1 and i not in ekstrem)

    isi, baris = [], []
    gmin_x = gmin_y = 1e9
    gmax_x = gmax_y = -1e9
    for i in range(N):
        cx0, cy0, sebar = PUSAT[lokasi[i]]
        cx = cx0 + max(-3.0, min(3.0, rng.gauss(0, 1))) * sebar
        cy = cy0 + max(-3.0, min(3.0, rng.gauss(0, 1))) * sebar
        r = min(0.034, 0.00025 * math.exp(rng.gauss(0, 0.9)))
        n = max(4, int(rng.lognormvariate(math.log(10), 0.5)))
        if i == besar:
            n = 1666
        if i in ekstrem:
            jenis, nilai = ekstrem[i]
            r, n = 0.0003, 8
            if jenis == "xmax":
                cx = nilai - r
            elif jenis == "xmin":
                cx = nilai + r
            elif jenis == "ymin":
                cy = nilai + r
            else:
                cy = nilai - r
        cincin = [cincin_cw(cx, cy, r, n, rng, 0.0 if i in ekstrem else 0.25)]
        for k in range(1, n_cincin[i]):
            if i in multi_luar:
                cincin.append(cincin_cw(cx + 3 * r * k, cy, r * 0.5, 6))
            else:
                cincin.append(cincin_ccw(cx + 0.1 * r * k, cy, r * 0.3, 5))
        isi.append(isi_poligon(cincin))
        for rg in cincin:
            for x, y in rg:
                gmin_x, gmax_x = min(gmin_x, x), max(gmax_x, x)
                gmin_y, gmax_y = min(gmin_y, y), max(gmax_y, y)
        nama_p, rujuk = PENULIS[kunci_p[i]]
        baris.append([i, pre[i], fmt(event[i]), post[i], event_type[i], nama_p, area[i],
                      pre2[i], post2[i], event2[i], conf[i], lokasi[i], tipe[i], ">=5", rujuk])
    shp, shx = tulis_shp_shx(isi, (gmin_x, gmin_y, gmax_x, gmax_y))
    dbf = tulis_dbf(DBF_KOLOM, baris)
    zip_path = os.path.join(folder, "inventories.zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("inventories.shp", shp)
        z.writestr("inventories.shx", shx)
        z.writestr("inventories.dbf", dbf)
        z.writestr("inventories.prj", WKT_ESRI)
        z.writestr("inventories.cpg", "UTF-8")
        z.writestr("inventories.qix", b"\x00" * 64)

    spl = _buat_splits(rng)
    with open(os.path.join(folder, "splits_aligned.json"), "w", encoding="utf-8") as f:
        json.dump(spl, f)
    return {"n": N, "lokasi": lokasi, "event": event, "baris": baris, "besar": besar,
            "n_cincin": n_cincin, "ekstrem": ekstrem}


def _buat_splits(rng):
    P = ci.LAPORAN["patch"]
    inv = []
    for nama, n in P["inventory"].items():
        inv += [nama] * n
    rng.shuffle(inv)
    split = ["train"] * 2810 + ["val"] * 703 + ["test"] * 879
    rng.shuffle(split)
    px = [min(8911, max(50, int(rng.lognormvariate(math.log(350), 0.9)))) for _ in range(len(inv))]
    px[0], px[1] = 50, 8911
    bebas = [i for i in range(2, len(px)) if 100 < px[i] < 8000][:2500]
    float_px = [float(v) for v in px]
    _atur_rata2(float_px, P["pixel_rata"], bebas, 51, 8910)
    px = [int(v) for v in float_px]                 # dilantai, lalu sisa dibagi satu-satu
    sisa = int(round(P["pixel_rata"] * len(px))) - sum(px)
    for i in bebas[:max(0, sisa)]:
        px[i] += 1
    px[0], px[1] = 50, 8911
    hasil = {"train": [], "val": [], "test": []}
    for k, (i_nv, sp, p) in enumerate(zip(inv, split, px)):
        no = 1000 + k
        hasil[sp].append({"id": "%s_%d" % (i_nv, no),
                          "s1asc": "s1asc/%s_s1asc_%d.nc" % (i_nv, no),
                          "s1dsc": "s1dsc/%s_s1dsc_%d.nc" % (i_nv, no),
                          "s2": "s2/%s_s2_%d.nc" % (i_nv, no),
                          "pixel_annotated": p, "inventory": i_nv})
    return hasil


# ---------------------------------------------------------------- data kecil
def buat_kecil(folder, n=300, n_patch=40, seed=5):
    """Data kecil acak (bukan profil laporan). Kembalikan dict kebenaran sederhana."""
    rng = random.Random(seed)
    os.makedirs(folder, exist_ok=True)
    nama_lok = list(PUSAT)
    isi, baris, lokasi = [], [], []
    for i in range(n):
        loc = nama_lok[i % len(nama_lok)] if i % 5 else "Italy"
        lokasi.append(loc)
        cx0, cy0, sebar = PUSAT[loc]
        padat = loc == "Italy"          # gugus rapat: banyak tetangga dalam jendela, tanggal berdekatan
        cx, cy = cx0 + rng.gauss(0, 0.01 if padat else sebar), cy0 + rng.gauss(0, 0.01 if padat else sebar)
        r = 0.0004 * math.exp(rng.gauss(0, 0.5))
        isi.append(isi_poligon([cincin_cw(cx, cy, r, 5 + i % 7)]))
        d = date(2019, 1, 1) + timedelta(days=rng.randint(0, 120)) if padat \
            else date(2017, 1, 1) + timedelta(days=rng.randint(0, 2000))
        sp = i % 9 == 0
        a, ref = PENULIS[["ferrario", "hohn", "emberson"][i % 3]]
        baris.append([i, None if sp else (d - timedelta(days=7)).isoformat(),
                      None if sp else d.isoformat(), None if sp else (d + timedelta(days=7)).isoformat(),
                      None if i % 11 == 0 else ["Rainfall", "Earthquake"][i % 2], a,
                      round(rng.uniform(1, 5000), 6), None, None, None,
                      round(rng.uniform(0.5, 1), 6), loc, "Debris flow", ">=5", ref])
    shp, shx = tulis_shp_shx(isi, (-180, -90, 180, 90))
    with zipfile.ZipFile(os.path.join(folder, "inventories.zip"), "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("inventories.shp", shp)
        z.writestr("inventories.shx", shx)
        z.writestr("inventories.dbf", tulis_dbf(DBF_KOLOM, baris))
        z.writestr("inventories.prj", WKT_ESRI)
        z.writestr("inventories.cpg", "UTF-8")
    invs = ["italy", "chimanimani", "hokkaido", "usa"]
    hasil = {"train": [], "val": [], "test": []}
    for k in range(n_patch):
        iv = invs[k % 4]
        hasil[["train", "val", "test"][k % 3]].append(
            {"id": "%s_%d" % (iv, 100 + k), "s1asc": "s1asc/a%d.nc" % k,
             "s1dsc": "s1dsc/d%d.nc" % k, "s2": "s2/s%d.nc" % k,
             "pixel_annotated": 50 + k * 7, "inventory": iv})
    with open(os.path.join(folder, "splits_aligned.json"), "w", encoding="utf-8") as f:
        json.dump(hasil, f)
    return {"n": n, "n_patch": n_patch, "lokasi": lokasi, "baris": baris}


if __name__ == "__main__":
    profil, folder = sys.argv[1], sys.argv[2]
    if profil == "laporan":
        buat_laporan(folder)
    else:
        buat_kecil(folder)
    print("dibuat di", folder)
