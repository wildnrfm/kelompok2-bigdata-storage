#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
convert_inventory.py  --  ubah data asli Sen12Landslides menjadi berkas katalog (skala S1)
Kelompok 2 - Tugas 2 Big Data Storage

MASUKAN (di data/raw/, HANYA dibaca):
    inventories.zip        shapefile inventaris longsor (74.956 poligon, 15 atribut)
    splits_aligned.json    daftar patch citra (4.392 entri: train, val, test)

KELUARAN (di data/out/s1/, tidak di-commit; ada di .gitignore):
    annotations.ndjson     MongoDB   (satu dokumen per baris, tanggal {"$date": ...})
    annotations.csv        PostGIS dan Spark (kolom datar, tanggal ISO)
    patches.ndjson         MongoDB
    patches.csv            PostGIS dan Spark

YANG DISIMPAN: hanya metadata. Bentuk poligon TIDAK disimpan; tiap anotasi diwakili oleh
    titik pusat (centroid berbobot luas) dan kotak pembatas (dari header rekaman .shp),
    dibulatkan ke 7 desimal (sekitar 1 cm). Citra NetCDF tidak dipakai.

CARA PAKAI (dari akar repo, PowerShell; hanya Python bawaan, TIDAK perlu pip install):
    python data/convert_inventory.py

PEMERIKSAAN DIRI: pada data asli, angka hasil (jumlah baris, sebaran lokasi dan pemicu,
    rentang tanggal, luas, koordinat, patch per split dan inventaris) dicocokkan dengan
    laporan_inventaris.txt (22 Okt 2026). Bila ada yang beda, skrip berakhir dengan kode 3
    dan menulis daftar perbedaannya: JANGAN lanjut, tulis [BLOKIR] di grup.
    Untuk data uji buatan: --profil tanpa  (melewati pencocokan dengan laporan).

Skrip ini aman dijalankan ulang: ia menimpa isi data/out/s1/.
"""
import argparse
import codecs
import collections
import csv
import io
import json
import re
import struct
import sys
import zipfile
from datetime import date
from pathlib import Path

try:  # supaya karakter aneh di layar Windows tidak menghentikan skrip
    sys.stdout.reconfigure(errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
OUT_S1 = ROOT / "data" / "out" / "s1"

# --------------------------------------------------------------------------
# Kontrak kolom (sama persis dengan baca-dulu/KONTRAK.md bagian 3)
# --------------------------------------------------------------------------
KOLOM_ANOTASI = [
    "ann_id", "location", "inventory", "event_type", "type", "velocity_c", "author",
    "reference", "event_conf", "area", "pre_date", "event_date", "post_date", "pre_dt2",
    "event_dt2", "post_dt2", "center_lon", "center_lat", "bbox_min_lon", "bbox_min_lat",
    "bbox_max_lon", "bbox_max_lat", "sim_batch",
]
KOLOM_PATCH = [
    "patch_id", "split", "inventory", "s2_path", "s1asc_path", "s1dsc_path",
    "pixel_annotated", "sim_batch",
]
# Kolom tanggal pada anotasi: (kolom DBF/CSV, kunci di dokumen Mongo "dates")
KOLOM_TANGGAL = [("pre_date", "pre"), ("event_date", "event"), ("post_date", "post"),
                 ("pre_dt2", "pre2"), ("event_dt2", "event2"), ("post_dt2", "post2")]
KOLOM_DBF_WAJIB = ["id", "pre_date", "event_date", "post_date", "event_type", "author", "area",
                   "pre_dt2", "post_dt2", "event_dt2", "event_conf", "location", "type",
                   "velocity_c", "reference"]
INVENTARIS_PATCH = ["italy", "kyrgyzstan1", "newzealand", "chimanimani", "hiroshima",
                    "indonesia", "kyrgyzstan2", "hokkaido", "itogon", "china", "usa"]

# --------------------------------------------------------------------------
# Angka dari laporan_inventaris.txt (22 Okt 2026) dan artikel; dipakai pemeriksaan diri
# --------------------------------------------------------------------------
LAPORAN = {
    "n": 74956,
    "id": (0, 74955),
    "tanpa_event_date": 109,
    "tanpa_event_type": 3142,
    "event_type": {"Rainfall": 52686, "Hurricane": 10172, "Earthquake": 7950,
                   "Tropical Storm": 640, "Cyclone": 366},
    "type": {"Debris flow": 74853, "Ice avalanche": 103},
    "location": {"Italy": 47522, "DominicaMaria": 10172, "Newzealand": 3242,
                 "Chimanimani": 2513, "Kyrgyzstan1": 2405, "Hokkaido": 2340,
                 "Hiroshima": 2211, "Indonesia": 2097, "LanaoDelNorte": 640,
                 "Kyrgyzstan2": 513, "Thrissur": 440, "Itogon": 366, "USA_PuertoRico": 263,
                 "China": 121, "USA_Alaska": 103, "Nepal": 8},
    "author_hitungan": [47522, 16306, 10619, 328, 181],
    "event_date": ("2016-04-01", "2023-05-16", 550),
    "area": (0.876412, 7455080.0),          # maks tampil 7.45508e+06 (6 angka penting)
    "event_conf_rata": 0.947489,
    "lon": (-140.702937, 174.075937),
    "lat": (-42.630565, 60.255046),
    "patch": {
        "n": 4392,
        "split": {"train": 2810, "val": 703, "test": 879},
        "inventory": {"italy": 1799, "kyrgyzstan1": 694, "newzealand": 508, "chimanimani": 345,
                      "hiroshima": 322, "indonesia": 253, "kyrgyzstan2": 170, "hokkaido": 144,
                      "itogon": 82, "china": 47, "usa": 28},
        "pixel": (50, 8911),
        "pixel_rata": 613.4,
    },
}


# --------------------------------------------------------------------------
# Format tulisan angka dan tanggal (dipakai juga oleh generate_scales.py)
# --------------------------------------------------------------------------
def f_koord(x):
    """Koordinat: 7 desimal (sekitar 1 cm), teks pendek yang sama di NDJSON dan CSV."""
    return round(x, 7) + 0.0           # + 0.0 mengubah -0.0 menjadi 0.0


def f_desimal(x):
    """Luas dan keyakinan: 6 desimal."""
    return round(x, 6) + 0.0


def iso_mongo(d):
    return d.isoformat() + "T00:00:00.000Z"


def baca_tanggal(teks):
    """Teks tanggal DBF -> date, atau None bila kosong atau tidak sah.

    Bentuk yang diterima: 2019-03-08, 2019/03/08, 20190308 (disamakan menjadi ISO)."""
    if teks is None:
        return None
    t = teks.strip()
    m = re.fullmatch(r"(\d{4})[-/]?(\d{2})[-/]?(\d{2})", t)
    if not m:
        return None
    try:
        return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except ValueError:
        return None


def petakan_inventaris(location, daftar):
    """Nama inventaris patch untuk satu nilai location, atau None bila tidak ada patch."""
    rendah = (location or "").strip().lower()
    if rendah in daftar:
        return rendah
    if rendah.startswith("usa") and "usa" in daftar:
        return "usa"
    return None


# --------------------------------------------------------------------------
# Rekaman anotasi -> baris NDJSON / CSV
# --------------------------------------------------------------------------
def anotasi_ndjson(r):
    """Satu dokumen MongoDB (kunci berurutan; field kosong DIHILANGKAN)."""
    d = {"_id": r["ann_id"], "location": r["location"]}
    if r["inventory"] is not None:
        d["inventory"] = r["inventory"]
    if r["event_type"] is not None:
        d["event_type"] = r["event_type"]
    d["type"] = r["type"]
    for k in ("velocity_c", "author", "reference"):
        if r[k] is not None:
            d[k] = r[k]
    if r["event_conf"] is not None:
        d["event_conf"] = r["event_conf"]
    if r["area"] is not None:
        d["area"] = r["area"]
    tgl = {kunci: {"$date": iso_mongo(r[kolom])} for kolom, kunci in KOLOM_TANGGAL
           if r[kolom] is not None}
    if tgl:
        d["dates"] = tgl
    d["center"] = {"type": "Point", "coordinates": [r["center_lon"], r["center_lat"]]}
    x0, y0, x1, y1 = r["bbox_min_lon"], r["bbox_min_lat"], r["bbox_max_lon"], r["bbox_max_lat"]
    d["bbox"] = {"type": "Polygon",
                 "coordinates": [[[x0, y0], [x1, y0], [x1, y1], [x0, y1], [x0, y0]]]}
    d["sim_batch"] = r["sim_batch"]
    return json.dumps(d, ensure_ascii=False, separators=(",", ":"))


def anotasi_csv(r):
    """Satu baris CSV (None menjadi sel kosong tanpa tanda kutip)."""
    return [r["ann_id"], r["location"], r["inventory"], r["event_type"], r["type"],
            r["velocity_c"], r["author"], r["reference"], r["event_conf"], r["area"],
            r["pre_date"].isoformat() if r["pre_date"] else None,
            r["event_date"].isoformat() if r["event_date"] else None,
            r["post_date"].isoformat() if r["post_date"] else None,
            r["pre_dt2"].isoformat() if r["pre_dt2"] else None,
            r["event_dt2"].isoformat() if r["event_dt2"] else None,
            r["post_dt2"].isoformat() if r["post_dt2"] else None,
            r["center_lon"], r["center_lat"], r["bbox_min_lon"], r["bbox_min_lat"],
            r["bbox_max_lon"], r["bbox_max_lat"], r["sim_batch"]]


def patch_ndjson(r):
    d = {"_id": r["patch_id"], "split": r["split"], "inventory": r["inventory"]}
    paths = {k: r[k + "_path"] for k in ("s2", "s1asc", "s1dsc") if r[k + "_path"] is not None}
    if paths:
        d["paths"] = paths
    if r["pixel_annotated"] is not None:
        d["pixel_annotated"] = r["pixel_annotated"]
    d["sim_batch"] = r["sim_batch"]
    return json.dumps(d, ensure_ascii=False, separators=(",", ":"))


def patch_csv(r):
    return [r["patch_id"], r["split"], r["inventory"], r["s2_path"], r["s1asc_path"],
            r["s1dsc_path"], r["pixel_annotated"], r["sim_batch"]]


class PenulisSkala:
    """Menulis annotations.ndjson/csv dan patches.ndjson/csv ke satu folder, baris demi baris."""

    def __init__(self, folder):
        self.folder = Path(folder)
        self.folder.mkdir(parents=True, exist_ok=True)
        self.n_anotasi = 0
        self.n_patch = 0
        self._f = {}
        for nama in ("annotations.ndjson", "annotations.csv", "patches.ndjson", "patches.csv"):
            self._f[nama] = open(self.folder / nama, "w", encoding="utf-8", newline="\n")
        self._ca = csv.writer(self._f["annotations.csv"], lineterminator="\n")
        self._cp = csv.writer(self._f["patches.csv"], lineterminator="\n")
        self._ca.writerow(KOLOM_ANOTASI)
        self._cp.writerow(KOLOM_PATCH)

    def tambah_anotasi(self, r):
        self._f["annotations.ndjson"].write(anotasi_ndjson(r) + "\n")
        self._ca.writerow(anotasi_csv(r))
        self.n_anotasi += 1

    def tambah_patch(self, r):
        self._f["patches.ndjson"].write(patch_ndjson(r) + "\n")
        self._cp.writerow(patch_csv(r))
        self.n_patch += 1

    def tambah_banyak(self, nd_anotasi, csv_anotasi, nd_patch, csv_patch):
        """Tulis satu batch yang barisnya sudah dibentuk (dipakai generate_scales.py)."""
        self._f["annotations.ndjson"].writelines(nd_anotasi)
        self._ca.writerows(csv_anotasi)
        self._f["patches.ndjson"].writelines(nd_patch)
        self._cp.writerows(csv_patch)
        self.n_anotasi += len(nd_anotasi)
        self.n_patch += len(nd_patch)

    def tutup(self):
        for f in self._f.values():
            f.close()


# --------------------------------------------------------------------------
# Membaca CSV katalog kembali menjadi rekaman (dipakai generate_scales.py dan kebenaran.py)
# --------------------------------------------------------------------------
def _kosong(s):
    return None if s == "" else s


def baca_anotasi_csv(jalur):
    """Generator rekaman anotasi dari annotations.csv (urutan file dipertahankan)."""
    with open(jalur, encoding="utf-8", newline="") as f:
        pembaca = csv.reader(f)
        kepala = next(pembaca)
        if kepala != KOLOM_ANOTASI:
            raise ValueError("%s: kolom tidak sesuai kontrak.\n  ada     : %s\n  seharusnya: %s"
                             % (jalur, ",".join(kepala), ",".join(KOLOM_ANOTASI)))
        for b in pembaca:
            yield {
                "ann_id": int(b[0]), "location": b[1], "inventory": _kosong(b[2]),
                "event_type": _kosong(b[3]), "type": b[4], "velocity_c": _kosong(b[5]),
                "author": _kosong(b[6]), "reference": _kosong(b[7]),
                "event_conf": float(b[8]) if b[8] != "" else None,
                "area": float(b[9]) if b[9] != "" else None,
                "pre_date": date.fromisoformat(b[10]) if b[10] else None,
                "event_date": date.fromisoformat(b[11]) if b[11] else None,
                "post_date": date.fromisoformat(b[12]) if b[12] else None,
                "pre_dt2": date.fromisoformat(b[13]) if b[13] else None,
                "event_dt2": date.fromisoformat(b[14]) if b[14] else None,
                "post_dt2": date.fromisoformat(b[15]) if b[15] else None,
                "center_lon": float(b[16]), "center_lat": float(b[17]),
                "bbox_min_lon": float(b[18]), "bbox_min_lat": float(b[19]),
                "bbox_max_lon": float(b[20]), "bbox_max_lat": float(b[21]),
                "sim_batch": int(b[22]),
            }


def baca_patch_csv(jalur):
    with open(jalur, encoding="utf-8", newline="") as f:
        pembaca = csv.reader(f)
        kepala = next(pembaca)
        if kepala != KOLOM_PATCH:
            raise ValueError("%s: kolom tidak sesuai kontrak.\n  ada     : %s\n  seharusnya: %s"
                             % (jalur, ",".join(kepala), ",".join(KOLOM_PATCH)))
        for b in pembaca:
            yield {"patch_id": b[0], "split": b[1], "inventory": b[2],
                   "s2_path": _kosong(b[3]), "s1asc_path": _kosong(b[4]),
                   "s1dsc_path": _kosong(b[5]),
                   "pixel_annotated": int(b[6]) if b[6] != "" else None,
                   "sim_batch": int(b[7])}


# --------------------------------------------------------------------------
# Membaca shapefile dan DBF (logika sama dengan cek_inventaris.py)
# --------------------------------------------------------------------------
TIPE_POLIGON = (5, 15, 25)


def normalisasi_encoding(teks):
    t = (teks or "").strip().lower()
    if t.isdigit():
        t = "cp" + t
    try:
        codecs.lookup(t)
        return t
    except LookupError:
        return "utf-8"


def baca_dbf(data, enc):
    """Kembalikan (daftar nama kolom, daftar baris berupa dict; None untuk rekaman terhapus)."""
    if len(data) < 33:
        raise ValueError("berkas .dbf terlalu pendek")
    n_header = struct.unpack_from("<I", data, 4)[0]
    panjang_header, panjang_rekaman = struct.unpack_from("<HH", data, 8)
    if panjang_rekaman < 1 or panjang_header < 33:
        raise ValueError("header .dbf tidak masuk akal (panjang_header=%d, panjang_rekaman=%d)"
                         % (panjang_header, panjang_rekaman))
    fields = []
    pos = 32
    while pos + 32 <= panjang_header and data[pos] != 0x0D:
        raw = data[pos:pos + 32]
        nama = raw[:11].split(b"\x00", 1)[0].decode(enc, "replace")
        fields.append((nama, raw[16]))
        pos += 32
    n_nyata = (len(data) - panjang_header) // panjang_rekaman
    n = min(n_header, n_nyata) if n_header else n_nyata
    baris = []
    off = panjang_header
    for _ in range(n):
        rec = data[off:off + panjang_rekaman]
        off += panjang_rekaman
        if rec[:1] == b"*":                 # rekaman bertanda terhapus
            baris.append(None)
            continue
        nilai = {}
        p = 1
        for nama, lebar in fields:
            s = rec[p:p + lebar].decode(enc, "replace").strip(" \x00")
            p += lebar
            nilai[nama] = None if (s == "" or set(s) == {"*"}) else s
        baris.append(nilai)
    return [nama for nama, _ in fields], baris


def pusat_poligon(koord, bagian):
    """Titik pusat berbobot luas (centroid) dari semua cincin; None bila luasnya nol.

    koord  : tuple (x0, y0, x1, y1, ...); bagian: daftar (awal, akhir) indeks titik tiap cincin.
    Cincin luar (searah jarum jam) dan lubang (berlawanan) otomatis saling mengurangi
    karena luas bertanda dijumlahkan. Koordinat digeser ke titik pertama dulu supaya
    selisih angka besar tidak menghilangkan ketelitian."""
    ox, oy = koord[0], koord[1]
    luas2 = sx = sy = 0.0
    for a, b in bagian:
        for i in range(a, b - 1):
            x0, y0 = koord[2 * i] - ox, koord[2 * i + 1] - oy
            x1, y1 = koord[2 * i + 2] - ox, koord[2 * i + 3] - oy
            c = x0 * y1 - x1 * y0
            luas2 += c
            sx += (x0 + x1) * c
            sy += (y0 + y1) * c
    if abs(luas2) < 1e-300:
        return None
    return ox + sx / (3.0 * luas2), oy + sy / (3.0 * luas2)


def baca_shp(data):
    """Kembalikan daftar (bbox, pusat) per rekaman poligon; None untuk rekaman tanpa geometri.

    bbox = (xmin, ymin, xmax, ymax) dari header rekaman; pusat = (x, y) atau None."""
    if len(data) < 100:
        raise ValueError("berkas .shp terlalu pendek")
    kode = struct.unpack_from(">i", data, 0)[0]
    if kode != 9994:
        raise ValueError("bukan berkas .shp yang sah (kode awal %d, seharusnya 9994)" % kode)
    tipe = struct.unpack_from("<i", data, 32)[0]
    if tipe not in TIPE_POLIGON:
        raise ValueError("tipe geometri %d bukan poligon (5, 15, atau 25)" % tipe)
    hasil = []
    pos, n = 100, len(data)
    while pos + 8 <= n:
        _no, panjang = struct.unpack_from(">ii", data, pos)
        pos += 8
        isi = panjang * 2
        if isi < 4 or pos + isi > n:
            raise ValueError("berkas .shp terpotong di rekaman %d (unduhan belum selesai?)"
                             % (len(hasil) + 1))
        st = struct.unpack_from("<i", data, pos)[0]
        if st == 0:
            hasil.append(None)
        elif st in TIPE_POLIGON:
            bbox = struct.unpack_from("<4d", data, pos + 4)
            nparts, npts = struct.unpack_from("<2i", data, pos + 36)
            parts = struct.unpack_from("<%di" % nparts, data, pos + 44)
            awal = pos + 44 + 4 * nparts
            koord = struct.unpack_from("<%dd" % (2 * npts), data, awal)
            bagian = []
            for k in range(nparts):
                a = parts[k]
                b = parts[k + 1] if k + 1 < nparts else npts
                if 0 <= a < b <= npts and b - a >= 2:
                    bagian.append((a, b))
            hasil.append((bbox, pusat_poligon(koord, bagian) if bagian else None))
        else:
            raise ValueError("rekaman %d bertipe %d, bukan poligon" % (len(hasil) + 1, st))
        pos += isi
    return hasil


# --------------------------------------------------------------------------
# Mencari dan membuka berkas masukan
# --------------------------------------------------------------------------
class Masukan:
    """Isi berkas shapefile yang sudah dipilih: byte .shp, .dbf, teks .prj, encoding."""

    def __init__(self, nama, shp, dbf, prj, enc, sumber):
        self.nama, self.shp, self.dbf, self.prj, self.enc, self.sumber = \
            nama, shp, dbf, prj, enc, sumber


def _kumpulkan_zip(zf, awalan, hasil, kedalaman):
    for info in zf.infolist():
        if info.is_dir():
            continue
        nama = awalan + info.filename
        hasil[nama] = (lambda z=zf, n=info.filename: z.read(n))
        if info.filename.lower().endswith(".zip") and kedalaman < 2:
            try:
                dalam = zipfile.ZipFile(io.BytesIO(zf.read(info.filename)))
            except zipfile.BadZipFile:
                continue
            _kumpulkan_zip(dalam, nama + "!/", hasil, kedalaman + 1)


def buka_inventaris(jalur, pilih_shp=None):
    jalur = Path(jalur)
    isi = {}
    if jalur.is_dir():
        for p in sorted(jalur.rglob("*")):
            if p.is_file():
                isi[p.relative_to(jalur).as_posix()] = (lambda q=p: q.read_bytes())
    elif zipfile.is_zipfile(jalur):
        _kumpulkan_zip(zipfile.ZipFile(jalur), "", isi, 0)
    elif jalur.suffix.lower() == ".shp":
        for ext in (".shp", ".dbf", ".prj", ".cpg", ".SHP", ".DBF", ".PRJ", ".CPG"):
            q = jalur.with_suffix(ext)
            if q.is_file():
                isi[q.name] = (lambda q=q: q.read_bytes())
    else:
        raise ValueError("%s bukan zip, folder, atau .shp" % jalur)

    daftar = sorted(n for n in isi if n.lower().endswith(".shp"))
    if pilih_shp:
        daftar = [n for n in daftar if n == pilih_shp or n.endswith("/" + pilih_shp)]
    if not daftar:
        raise ValueError("tidak ada berkas .shp di %s%s. Isi: %s"
                         % (jalur, " yang bernama " + pilih_shp if pilih_shp else "",
                            ", ".join(sorted(isi)[:12]) or "(kosong)"))
    if len(daftar) > 1:
        raise ValueError("ada %d berkas .shp di %s: %s\nPilih satu dengan --shp NAMA"
                         % (len(daftar), jalur, ", ".join(daftar)))
    nama = daftar[0]
    stem = nama[:-4]
    ci = {n.lower(): n for n in isi}

    def ambil(ext):
        n = ci.get((stem + ext).lower())
        return isi[n]() if n else None

    dbf = ambil(".dbf")
    if dbf is None:
        raise ValueError("tidak ada %s.dbf pendamping: atribut tidak bisa dibaca" % stem)
    cpg = ambil(".cpg")
    prj = ambil(".prj")
    enc = normalisasi_encoding(cpg.decode("ascii", "replace")) if cpg else "utf-8"
    return Masukan(nama, isi[nama](), dbf,
                   prj.decode("utf-8", "replace") if prj else "", enc, str(jalur))


def cari_inventaris(raw):
    """Pilih berkas inventaris di folder raw: zip yang memuat .shp, atau .shp langsung."""
    raw = Path(raw)
    for nama in ("inventories.zip", "inventories.shp.zip"):
        if (raw / nama).is_file():
            return raw / nama
    for p in sorted(raw.glob("*.zip")):
        try:
            with zipfile.ZipFile(p) as z:
                if any(n.lower().endswith(".shp") for n in z.namelist()):
                    return p
        except zipfile.BadZipFile:
            continue
    shp = sorted(raw.glob("*.shp"))
    if shp:
        return shp[0]
    raise FileNotFoundError(
        "Tidak ada inventories.zip (atau .shp) di %s.\n"
        "Salin dulu dari folder unduhan (lihat panduan, bagian 'Taruh data asli')." % raw)


def cari_splits(raw):
    raw = Path(raw)
    p = raw / "splits_aligned.json"
    if p.is_file():
        return p
    for q in sorted(raw.glob("*.json")):
        try:
            with open(q, encoding="utf-8") as f:
                j = json.load(f)
        except (OSError, ValueError):
            continue
        if isinstance(j, dict) and {"train", "val", "test"} <= set(j):
            return q
    raise FileNotFoundError("Tidak ada splits_aligned.json di %s." % raw)


# --------------------------------------------------------------------------
# Konversi
# --------------------------------------------------------------------------
def angka_dbf(teks, nama, no):
    try:
        return float(teks.replace(",", "."))
    except (ValueError, AttributeError):
        raise ValueError("rekaman %d: nilai %s='%s' bukan angka" % (no, nama, teks))


class Statistik:
    """Penghitung ringkas yang dipakai pemeriksaan diri."""

    def __init__(self):
        self.n = 0
        self.id_min = self.id_maks = None
        self.id_unik = set()
        self.cnt = {k: collections.Counter() for k in ("location", "event_type", "type",
                                                      "author", "reference", "inventory")}
        self.tgl_event = collections.Counter()
        self.tanpa_event_date = 0
        self.tanpa_event_type = 0
        self.tgl_tak_sah = 0
        self.area_min = self.area_maks = None
        self.conf_jumlah = 0.0
        self.conf_n = 0
        self.lon_min = self.lon_maks = self.lat_min = self.lat_maks = None
        self.tanpa_geometri = 0
        self.pusat_cadangan = 0
        self.bbox_diperbaiki = 0
        self.dbf_terhapus = 0


def _min(a, b):
    return b if a is None or b < a else a


def _maks(a, b):
    return b if a is None or b > a else a


def konversi_inventaris(masuk, inventaris_patch, penulis, stat, verbose=True):
    """Baca .shp + .dbf, tulis anotasi ke penulis, isi stat. Kembalikan daftar peringatan."""
    peringatan = []
    kolom, baris = baca_dbf(masuk.dbf, masuk.enc)
    kurang = [k for k in KOLOM_DBF_WAJIB if k not in kolom]
    if kurang:
        raise ValueError("kolom ini tidak ada di .dbf: %s\n  kolom yang ada: %s"
                         % (", ".join(kurang), ", ".join(kolom)))
    geom = baca_shp(masuk.shp)
    if len(geom) != len(baris):
        raise ValueError("jumlah rekaman .shp (%d) berbeda dari .dbf (%d)"
                         % (len(geom), len(baris)))
    for no, (g, row) in enumerate(zip(geom, baris), 1):
        if row is None:
            stat.dbf_terhapus += 1
            continue
        if g is None:
            stat.tanpa_geometri += 1
            continue
        (xmin, ymin, xmax, ymax), pusat = g
        if xmin < -180 or xmax > 180 or ymin < -90 or ymax > 90:
            raise ValueError("rekaman %d: koordinat di luar rentang bujur/lintang. "
                             "Sistem koordinatnya bukan derajat; hentikan dan lapor." % no)
        x0, y0, x1, y1 = f_koord(xmin), f_koord(ymin), f_koord(xmax), f_koord(ymax)
        if x1 <= x0:                         # kotak tanpa lebar tidak sah untuk 2dsphere
            x1 = f_koord(x0 + 1e-7)
            stat.bbox_diperbaiki += 1
        if y1 <= y0:
            y1 = f_koord(y0 + 1e-7)
            stat.bbox_diperbaiki += 1
        if pusat is None or not (xmin - 1e-9 <= pusat[0] <= xmax + 1e-9
                                 and ymin - 1e-9 <= pusat[1] <= ymax + 1e-9):
            pusat = ((xmin + xmax) / 2.0, (ymin + ymax) / 2.0)
            stat.pusat_cadangan += 1
        cx = min(max(f_koord(pusat[0]), x0), x1)
        cy = min(max(f_koord(pusat[1]), y0), y1)

        ann_id = int(angka_dbf(row["id"], "id", no))
        tgl = {}
        for kol, _kunci in KOLOM_TANGGAL:
            t = baca_tanggal(row[kol])
            if t is None and row[kol] is not None:
                stat.tgl_tak_sah += 1
            tgl[kol] = t
        loc = row["location"] or ""
        r = {
            "ann_id": ann_id, "location": loc,
            "inventory": petakan_inventaris(loc, inventaris_patch),
            "event_type": row["event_type"], "type": row["type"] or "",
            "velocity_c": row["velocity_c"], "author": row["author"],
            "reference": row["reference"],
            "event_conf": f_desimal(angka_dbf(row["event_conf"], "event_conf", no))
            if row["event_conf"] is not None else None,
            "area": f_desimal(angka_dbf(row["area"], "area", no))
            if row["area"] is not None else None,
            "center_lon": cx, "center_lat": cy,
            "bbox_min_lon": x0, "bbox_min_lat": y0, "bbox_max_lon": x1, "bbox_max_lat": y1,
            "sim_batch": 0,
        }
        r.update(tgl)
        penulis.tambah_anotasi(r)

        stat.n += 1
        stat.id_min, stat.id_maks = _min(stat.id_min, ann_id), _maks(stat.id_maks, ann_id)
        stat.id_unik.add(ann_id)
        for k in ("location", "event_type", "type", "author", "reference", "inventory"):
            stat.cnt[k][r[k]] += 1
        if r["event_type"] is None:
            stat.tanpa_event_type += 1
        if r["event_date"] is None:
            stat.tanpa_event_date += 1
        else:
            stat.tgl_event[r["event_date"]] += 1
        if r["area"] is not None:
            stat.area_min, stat.area_maks = _min(stat.area_min, r["area"]), _maks(stat.area_maks, r["area"])
        if r["event_conf"] is not None:
            stat.conf_jumlah += r["event_conf"]
            stat.conf_n += 1
        stat.lon_min, stat.lon_maks = _min(stat.lon_min, x0), _maks(stat.lon_maks, x1)
        stat.lat_min, stat.lat_maks = _min(stat.lat_min, y0), _maks(stat.lat_maks, y1)
    if stat.dbf_terhapus:
        peringatan.append("%d rekaman bertanda terhapus di .dbf dilewati" % stat.dbf_terhapus)
    if stat.tanpa_geometri:
        peringatan.append("%d rekaman tanpa geometri dilewati" % stat.tanpa_geometri)
    if stat.tgl_tak_sah:
        peringatan.append("%d nilai tanggal tidak terbaca (dijadikan kosong)" % stat.tgl_tak_sah)
    if stat.bbox_diperbaiki:
        peringatan.append("%d sisi kotak pembatas tanpa lebar diperlebar 1e-7 derajat"
                          % stat.bbox_diperbaiki)
    if stat.pusat_cadangan:
        peringatan.append("%d titik pusat memakai tengah kotak pembatas (luas poligon nol atau "
                          "pusat di luar kotak)" % stat.pusat_cadangan)
    return peringatan


def baca_splits(jalur):
    """Daftar entri patch berurutan: (split, dict). Menerima {split: [..]} atau daftar dengan 'split'."""
    with open(jalur, encoding="utf-8-sig") as f:
        j = json.load(f)
    entri = []
    if isinstance(j, dict) and all(isinstance(v, list) for v in j.values()) and j:
        for split, daftar in j.items():
            for e in daftar:
                entri.append((str(split), e))
    elif isinstance(j, list):
        for e in j:
            if isinstance(e, dict) and "split" in e:
                entri.append((str(e["split"]), e))
    if not entri:
        kunci = list(j)[:10] if isinstance(j, dict) else type(j).__name__
        raise ValueError("bentuk %s tidak dikenali (kunci: %s). Yang diharapkan: "
                         "{\"train\": [...], \"val\": [...], \"test\": [...]}" % (jalur, kunci))
    return entri


def konversi_patch(entri, penulis):
    """Tulis semua patch; kembalikan statistik {split, inventory, pixel}."""
    st = {"split": collections.Counter(), "inventory": collections.Counter(),
          "pixel_jumlah": 0, "pixel_n": 0, "pixel_min": None, "pixel_maks": None,
          "unik": set()}
    for split, e in entri:
        if not isinstance(e, dict) or "id" not in e:
            raise ValueError("entri patch tanpa field 'id': %s" % str(e)[:80])
        pid = str(e["id"])
        if pid in st["unik"]:
            raise ValueError("patch_id kembar: %s" % pid)
        st["unik"].add(pid)
        inv = e.get("inventory")
        if inv is None:
            inv = pid.rsplit("_", 1)[0].lower()
        px = e.get("pixel_annotated")
        px = int(px) if px is not None else None
        r = {"patch_id": pid, "split": split, "inventory": str(inv).lower(),
             "s2_path": e.get("s2"), "s1asc_path": e.get("s1asc"), "s1dsc_path": e.get("s1dsc"),
             "pixel_annotated": px, "sim_batch": 0}
        penulis.tambah_patch(r)
        st["split"][split] += 1
        st["inventory"][r["inventory"]] += 1
        if px is not None:
            st["pixel_jumlah"] += px
            st["pixel_n"] += 1
            st["pixel_min"], st["pixel_maks"] = _min(st["pixel_min"], px), _maks(st["pixel_maks"], px)
    return st


# --------------------------------------------------------------------------
# Pemeriksaan diri terhadap laporan_inventaris.txt
# --------------------------------------------------------------------------
class Pemeriksa:
    def __init__(self):
        self.beda = []
        self.n_ok = 0

    def cek(self, nama, ok, ada, harap):
        if ok:
            self.n_ok += 1
            print("  OK     %s" % nama)
        else:
            self.beda.append(nama)
            print("  BEDA   %s\n         hasil kita : %s\n         laporan    : %s" % (nama, ada, harap))


def periksa_dengan_laporan(stat, pst):
    L = LAPORAN
    p = Pemeriksa()
    p.cek("jumlah anotasi", stat.n == L["n"], stat.n, L["n"])
    p.cek("id 0..74955 dan unik",
          (stat.id_min, stat.id_maks) == L["id"] and len(stat.id_unik) == stat.n,
          "%s..%s, unik %d" % (stat.id_min, stat.id_maks, len(stat.id_unik)), "0..74955, unik 74956")
    p.cek("anotasi tanpa event_date", stat.tanpa_event_date == L["tanpa_event_date"],
          stat.tanpa_event_date, L["tanpa_event_date"])
    p.cek("anotasi tanpa event_type", stat.tanpa_event_type == L["tanpa_event_type"],
          stat.tanpa_event_type, L["tanpa_event_type"])
    et = {k: v for k, v in stat.cnt["event_type"].items() if k is not None}
    p.cek("sebaran event_type", et == L["event_type"], dict(et), L["event_type"])
    p.cek("sebaran type", dict(stat.cnt["type"]) == L["type"], dict(stat.cnt["type"]), L["type"])
    p.cek("sebaran location (16 nilai)", dict(stat.cnt["location"]) == L["location"],
          dict(stat.cnt["location"]), L["location"])
    p.cek("sebaran author (5 penulis, hitungan sama)",
          sorted(stat.cnt["author"].values(), reverse=True) == L["author_hitungan"],
          sorted(stat.cnt["author"].values(), reverse=True), L["author_hitungan"])
    tmin = min(stat.tgl_event).isoformat() if stat.tgl_event else None
    tmax = max(stat.tgl_event).isoformat() if stat.tgl_event else None
    p.cek("event_date terkecil, terbesar, jumlah unik",
          (tmin, tmax, len(stat.tgl_event)) == L["event_date"],
          (tmin, tmax, len(stat.tgl_event)), L["event_date"])
    p.cek("luas (area) terkecil dan terbesar",
          stat.area_min is not None and abs(stat.area_min - L["area"][0]) <= 2e-6
          and abs(stat.area_maks - L["area"][1]) <= 10,
          (stat.area_min, stat.area_maks), L["area"])
    rata = stat.conf_jumlah / stat.conf_n if stat.conf_n else None
    p.cek("rata-rata event_conf", rata is not None and abs(rata - L["event_conf_rata"]) <= 6e-6,
          rata, L["event_conf_rata"])
    p.cek("rentang bujur kotak pembatas",
          stat.lon_min is not None and abs(stat.lon_min - L["lon"][0]) <= 2e-6
          and abs(stat.lon_maks - L["lon"][1]) <= 2e-6, (stat.lon_min, stat.lon_maks), L["lon"])
    p.cek("rentang lintang kotak pembatas",
          stat.lat_min is not None and abs(stat.lat_min - L["lat"][0]) <= 2e-6
          and abs(stat.lat_maks - L["lat"][1]) <= 2e-6, (stat.lat_min, stat.lat_maks), L["lat"])
    P = L["patch"]
    p.cek("jumlah patch", len(pst["unik"]) == P["n"], len(pst["unik"]), P["n"])
    p.cek("patch per split", dict(pst["split"]) == P["split"], dict(pst["split"]), P["split"])
    p.cek("patch per inventaris (11)", dict(pst["inventory"]) == P["inventory"],
          dict(pst["inventory"]), P["inventory"])
    prata = pst["pixel_jumlah"] / pst["pixel_n"] if pst["pixel_n"] else None
    p.cek("pixel_annotated terkecil, terbesar, rata-rata",
          (pst["pixel_min"], pst["pixel_maks"]) == P["pixel"]
          and prata is not None and abs(prata - P["pixel_rata"]) <= 0.1,
          (pst["pixel_min"], pst["pixel_maks"], prata), (P["pixel"], P["pixel_rata"]))
    return p


def periksa_dasar(stat, pst):
    """Pemeriksaan minimal untuk data selain data asli (--profil tanpa)."""
    p = Pemeriksa()
    p.cek("ada anotasi", stat.n > 0, stat.n, "> 0")
    p.cek("id anotasi unik", len(stat.id_unik) == stat.n, len(stat.id_unik), stat.n)
    p.cek("ada patch", len(pst["unik"]) > 0, len(pst["unik"]), "> 0")
    return p


# --------------------------------------------------------------------------
def ukuran_mb(p):
    return Path(p).stat().st_size / 1e6  # MB desimal, sama dengan KAMUS_DATA.md


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Ubah inventories.zip + splits_aligned.json menjadi katalog skala S1.")
    ap.add_argument("--raw", default=str(RAW_DIR), help="folder data asli (bawaan data/raw)")
    ap.add_argument("--inventaris", help="jalur inventories.zip / folder / .shp (bawaan: cari di --raw)")
    ap.add_argument("--splits", help="jalur splits_aligned.json (bawaan: cari di --raw)")
    ap.add_argument("--shp", help="nama .shp bila zip memuat lebih dari satu")
    ap.add_argument("--out", default=str(OUT_S1), help="folder keluaran (bawaan data/out/s1)")
    ap.add_argument("--profil", choices=["laporan", "tanpa"], default="laporan",
                    help="laporan = cocokkan dengan laporan_inventaris.txt (bawaan); "
                         "tanpa = hanya untuk data uji buatan")
    args = ap.parse_args(argv)

    try:
        jalur_inv = Path(args.inventaris) if args.inventaris else cari_inventaris(args.raw)
        jalur_spl = Path(args.splits) if args.splits else cari_splits(args.raw)
    except FileNotFoundError as e:
        print("GAGAL: %s" % e)
        return 2
    print("Inventaris : %s (%.1f MB)" % (jalur_inv, ukuran_mb(jalur_inv) if jalur_inv.is_file() else 0))
    print("Daftar patch: %s (%.2f MB)" % (jalur_spl, ukuran_mb(jalur_spl)))

    try:
        masuk = buka_inventaris(jalur_inv, args.shp)
        entri = baca_splits(jalur_spl)
    except (ValueError, OSError, zipfile.BadZipFile) as e:
        print("GAGAL membuka masukan: %s" % e)
        return 2

    # sistem koordinat
    prj = masuk.prj.strip()
    if not prj:
        print("Catatan: tidak ada .prj; koordinat diasumsikan bujur/lintang WGS84 (EPSG:4326).")
    elif prj.upper().startswith(("PROJCS", "PROJCRS")):
        print("GAGAL: .prj menyebut sistem koordinat proyeksi (meter), bukan derajat:\n  %s"
              % prj[:200])
        return 2
    else:
        print("Sistem koordinat (.prj): %s" % prj.replace("\n", " ")[:90])

    inventaris_patch = {str(e.get("inventory", "")).lower() for _s, e in entri
                        if isinstance(e, dict) and e.get("inventory")} or set(INVENTARIS_PATCH)

    folder = Path(args.out)
    penulis = PenulisSkala(folder)
    stat = Statistik()
    try:
        peringatan = konversi_inventaris(masuk, inventaris_patch, penulis, stat)
        pst = konversi_patch(entri, penulis)
    except ValueError as e:
        penulis.tutup()
        print("GAGAL saat konversi: %s" % e)
        return 2
    penulis.tutup()

    print()
    print("Hasil di %s" % folder)
    for nama in ("annotations.ndjson", "annotations.csv", "patches.ndjson", "patches.csv"):
        print("  %-20s %8.2f MB" % (nama, ukuran_mb(folder / nama)))
    print("  anotasi: %d baris | patch: %d baris" % (penulis.n_anotasi, penulis.n_patch))
    for w in peringatan:
        print("  catatan: " + w)

    print()
    if args.profil == "laporan":
        print("Pemeriksaan diri terhadap laporan_inventaris.txt (22 Okt 2026):")
        p = periksa_dengan_laporan(stat, pst)
    else:
        print("Pemeriksaan dasar (profil tanpa; BUKAN data asli):")
        p = periksa_dasar(stat, pst)
    print()
    if p.beda:
        print("GAGAL: %d pemeriksaan beda: %s" % (len(p.beda), "; ".join(p.beda)))
        print("Jangan lanjut dan jangan commit CHECKSUMS.txt. Tulis [BLOKIR] di grup dan "
              "tempel seluruh keluaran ini.")
        return 3
    print("LOLOS: %d pemeriksaan cocok. Langkah berikut: python data/cek_data.py --skala S1"
          % p.n_ok)
    return 0


if __name__ == "__main__":
    sys.exit(main())
