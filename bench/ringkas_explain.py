#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Ringkas keluaran EXPLAIN (PostGIS) dan explain (MongoDB) dari penelusuran rencana kueri 25 Nov 2026.

Cara pakai (dari akar repo, PowerShell):
  python bench/ringkas_explain.py

Membaca (semuanya di results/):
  explain_postgis_W3_S100_ann<ID>.txt        EXPLAIN (ANALYZE, BUFFERS) untuk kueri W3 S100, dua kali
                                             dengan plan_cache_mode = force_custom_plan (rencana kustom)
                                             dan dua kali dengan force_generic_plan (rencana generik)
  explain_mongodb_W4_S100_ann<ID>.txt        explain("executionStats") untuk kueri W4 S100: rencana bawaan
                                             (plan cache dikosongkan), rencana dipaksa bbox_2dsphere (hint),
                                             dan countDocuments seperti harness
  explain_mongodb_W4_S100_urutan_harness.txt putar ulang titik 1, 2, 3 dengan isi plan cache
Menulis results/ringkasan_explain.csv (satu baris per pengamatan) dan mencetak tabel ringkasnya.
Angka di laporan (subbab 3.2.1) dan di slide berasal dari keluaran skrip ini.

Catatan: ID di nama berkas adalah ann_id; nomor titik uji diambil dari bench/points.json.
"""
import csv
import glob
import json
import os
import re
import statistics as st
import sys
from decimal import Decimal, ROUND_HALF_UP

try:
    sys.stdout.reconfigure(errors="replace")
except Exception:
    pass

AKAR =os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HASIL = os.path.join(AKAR, "results")


def detik(ms, desimal=2):
    """ms -> teks detik, dibulatkan setengah ke atas (seperti Excel dan laporan), bukan pembulatan biner Python
    (190,325 detik menjadi 190.33, bukan 190.32)."""
    nilai = (Decimal(str(ms)) / 1000).quantize(Decimal(1).scaleb(-desimal), rounding=ROUND_HALF_UP)
    return format(nilai, "f")


def baca(path):
    # PowerShell menulis UTF-8 dengan BOM dan CRLF; keduanya dibuang di sini.
    with open(path, encoding="utf-8-sig") as f:
        return f.read().replace("\r", "")


def peta_titik():
    with open(os.path.join(AKAR, "bench", "points.json"), encoding="utf-8") as f:
        data = json.load(f)
    return {p["ann_id"]: p for p in data["points"]}


def ann_dari(path):
    return int(re.search(r"_ann(\d+)\.txt$", path).group(1))


def ringkas_postgis(titik):
    """Satu baris per (titik, rencana, eksekusi ke-1 atau ke-2)."""
    baris = []
    berkas = sorted(glob.glob(os.path.join(HASIL, "explain_postgis_W3_S100_ann*.txt")), key=ann_dari)
    for path in berkas:
        ann = ann_dari(path)
        bagian = re.split(r"=== (force_\w+), eksekusi ke-(\d) ===", baca(path))
        for i in range(1, len(bagian), 3):
            mode, ke, isi = bagian[i], int(bagian[i + 1]), bagian[i + 2]
            waktu = re.search(r"Execution Time: ([\d.]+) ms", isi)
            simpul = re.search(
                r"->\s+(Index Scan|Index Only Scan|Bitmap Heap Scan|Seq Scan)(?: using (\w+))? on annotations", isi)
            bitmap = re.findall(r"Bitmap Index Scan on (\w+)", isi)
            indeks = "+".join(bitmap) if bitmap else (simpul.group(2) if simpul and simpul.group(2) else "")
            tgl = re.search(
                r"Bitmap Index Scan on ann_event_date\s+\(cost=[\d.]+\.\.[\d.]+ rows=(\d+) width=\d+\) "
                r"\(actual time=[\d.]+\.\.[\d.]+ rows=(\d+)", isi)
            baris.append({
                "penyimpanan": "postgis", "beban_kerja": "W3", "skala": "S100",
                "titik": titik.get(ann, {}).get("id", ""), "ann_id": ann,
                "kondisi": ("rencana kustom" if mode == "force_custom_plan" else "rencana generik") + f" ke-{ke}",
                "rencana": simpul.group(1) if simpul else "",
                "indeks": indeks,
                "diperiksa_estimasi": tgl.group(1) if tgl else "",
                "diperiksa_aktual": tgl.group(2) if tgl else "",
                "waktu_ms": float(waktu.group(1)) if waktu else "",
            })
    return baris


def ringkas_mongodb(titik):
    """Satu baris per (titik, kondisi): bawaan, hint bbox_2dsphere, countDocuments."""
    baris = []
    berkas = sorted(glob.glob(os.path.join(HASIL, "explain_mongodb_W4_S100_ann*.txt")), key=ann_dari)
    for path in berkas:
        ann = ann_dari(path)
        teks = baca(path)
        judul = re.search(r"Titik uji ann_id \d+: (.+?), (.+?) \(", teks)
        for blok in re.split(r"\n== ", teks)[1:]:
            nama = blok.split("\n", 1)[0]
            if nama.startswith("1."):
                kondisi = "bawaan (plan cache kosong)"
            elif nama.startswith("2."):
                kondisi = "hint bbox_2dsphere"
            else:
                kondisi = "countDocuments (plan cache kosong)"
            ix = re.search(r"indeks dipakai: (.+)", blok)
            ang = re.search(r"dikembalikan (\d+), kunci diperiksa (\d+), dokumen diperiksa (\d+), (\d+) ms", blok)
            cnt = re.search(r"countDocuments: (\d+) hasil, (\d+) ms", blok)
            tolak = re.search(r"rencana ditolak: (.+)", blok)
            baris.append({
                "penyimpanan": "mongodb", "beban_kerja": "W4", "skala": "S100",
                "titik": titik.get(ann, {}).get("id", ""), "ann_id": ann,
                "kondisi": kondisi,
                "rencana": "FETCH > IXSCAN" if ix else "",
                "indeks": ix.group(1).strip() if ix else "",
                "diperiksa_estimasi": tolak.group(1).strip() if tolak else "",  # rencana yang ditolak
                "diperiksa_aktual": ang.group(2) if ang else "",               # kunci diperiksa
                "waktu_ms": float(ang.group(4)) if ang else (float(cnt.group(2)) if cnt else ""),
                "lokasi_jenis": f"{judul.group(1)}, {judul.group(2)}" if judul else "",
            })
    return baris


def cetak_postgis(baris):
    print("PostGIS W3 S100: EXPLAIN (ANALYZE, BUFFERS), eksekusi ke-2 (cache hangat)")
    print(f"{'titik':>5} {'ann_id':>7} | {'kustom ms':>9} {'generik ms':>10} {'rasio':>7} | rencana kustom -> rencana generik")
    per = {}
    for b in baris:
        per.setdefault(b["ann_id"], {})[b["kondisi"]] = b
    kus, gen = [], []
    for ann, d in sorted(per.items(), key=lambda kv: kv[1]["rencana kustom ke-2"]["titik"]):
        c, g = d["rencana kustom ke-2"], d["rencana generik ke-2"]
        kus.append(c["waktu_ms"])
        gen.append(g["waktu_ms"])
        print(f"{c['titik']:>5} {ann:>7} | {c['waktu_ms']:>9.3f} {g['waktu_ms']:>10.3f} {g['waktu_ms'] / c['waktu_ms']:>6.1f}x | "
              f"{c['rencana']} {c['indeks']} -> {g['rencana']} {g['indeks']}")
    if kus:
        print(f"median: kustom {st.median(kus):.3f} ms, generik {st.median(gen):.3f} ms, "
              f"rasio {st.median(gen) / st.median(kus):.1f}x (n = {len(kus)} titik)")
        gen_baris = [b for b in baris if b["kondisi"] == "rencana generik ke-2" and b["diperiksa_aktual"] != ""]
        if gen_baris:
            est = sorted({int(b["diperiksa_estimasi"]) for b in gen_baris})
            akt = [int(b["diperiksa_aktual"]) for b in gen_baris]
            print(f"indeks tanggal pada rencana generik: estimasi planner {est}, entri dipindai aktual "
                  f"min {min(akt)}, median {int(st.median(akt))}, maks {max(akt)}")
    print()


def cetak_mongodb(baris):
    print("MongoDB W4 S100: explain(\"executionStats\"), rencana bawaan dibanding hint bbox_2dsphere")
    print(f"{'titik':>5} {'ann_id':>7} {'lokasi, jenis':<30} | {'indeks bawaan':<27} {'kunci bawaan':>12} {'detik':>8} | "
          f"{'kunci hint':>10} {'detik':>7} {'rasio':>6}")
    per = {}
    for b in baris:
        per.setdefault(b["ann_id"], {})[b["kondisi"]] = b
    for ann, d in sorted(per.items(), key=lambda kv: kv[1]["bawaan (plan cache kosong)"]["titik"]):
        a, h = d["bawaan (plan cache kosong)"], d["hint bbox_2dsphere"]
        print(f"{a['titik']:>5} {ann:>7} {a['lokasi_jenis']:<30} | {a['indeks']:<27} {int(a['diperiksa_aktual']):>12} "
              f"{detik(a['waktu_ms']):>8} | {int(h['diperiksa_aktual']):>10} {detik(h['waktu_ms']):>7} "
              f"{a['waktu_ms'] / h['waktu_ms']:>5.1f}x")
    print()


def cetak_urutan():
    path = os.path.join(HASIL, "explain_mongodb_W4_S100_urutan_harness.txt")
    if not os.path.exists(path):
        return
    print("MongoDB W4 S100: putar ulang urutan harness (titik 1, 2, 3; plan cache kosong di awal)")
    for blok in re.split(r"\n== ", baca(path))[1:]:
        judul = blok.split("\n", 1)[0]
        cnt = re.search(r"countDocuments: (\d+) hasil, (\d+) ms", blok)
        isi = re.findall(r"- indeks (.+?); aktif=(\w+); works=(\d+)", blok)
        sisa = "; ".join(f"cache: {i} aktif={a} works={w}" for i, a, w in isi)
        print(f"  {judul}: {cnt.group(1)} hasil, {detik(int(cnt.group(2)))} detik; {sisa}")
    print()


def main():
    titik = peta_titik()
    pg, mg = ringkas_postgis(titik), ringkas_mongodb(titik)
    if not pg and not mg:
        raise SystemExit("Tidak ada berkas explain_*.txt di results/.")
    if pg:
        cetak_postgis(pg)
    if mg:
        cetak_mongodb(mg)
        cetak_urutan()
    kolom = ["penyimpanan", "beban_kerja", "skala", "titik", "ann_id", "kondisi", "rencana", "indeks",
             "diperiksa_estimasi", "diperiksa_aktual", "waktu_ms", "lokasi_jenis"]
    keluar = os.path.join(HASIL, "ringkasan_explain.csv")
    with open(keluar, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=kolom, extrasaction="ignore", lineterminator="\n")
        w.writeheader()
        for b in pg + mg:
            w.writerow(b)
    print(f"Tertulis: {os.path.relpath(keluar, AKAR)} ({len(pg) + len(mg)} baris)")


if __name__ == "__main__":
    main()
