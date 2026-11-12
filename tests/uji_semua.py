#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Uji menyeluruh TANPA Docker: konversi, generator, pemeriksa, wasit, harness, pembanding.

Cara pakai (dari akar repo, PowerShell; hanya Python bawaan):
  python tests/uji_semua.py              uji cepat (sekitar 1 menit)
  python tests/uji_semua.py --penuh      termasuk konversi data berbentuk laporan asli (75 ribu poligon)
  python tests/uji_semua.py --simpan     jangan hapus folder sementara (untuk diperiksa)
  python tests/uji_semua.py -k mongo     hanya uji yang namanya memuat 'mongo'

Yang dibuktikan: kode berjalan dari ujung ke ujung, nama kolom dan definisi kueri W1 sampai W6
konsisten, dan MongoDB/PostGIS/Spark TIRUAN memberi jumlah yang sama dengan wasit
bench/kebenaran.py. Pustaka tiruan ada di tests/stubs (lihat README di sana).
Yang TIDAK dibuktikan: perilaku MongoDB, PostGIS, HDFS, dan Spark sungguhan.
"""
import argparse
import contextlib
import csv
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import traceback
from pathlib import Path

PAKET = Path(__file__).resolve().parent.parent
STUBS = PAKET / "tests" / "stubs"
for sub in ("tests", "bench", "data", "mongodb", "hdfs-parquet"):
    sys.path.insert(0, str(PAKET / sub))

try:
    sys.stdout.reconfigure(errors="replace")
except Exception:
    pass

N_ANOTASI, N_PATCH = 600, 40
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")


class Gagal(Exception):
    pass


def harus(kondisi, pesan):
    if not kondisi:
        raise Gagal(pesan)


def sub(skrip, *arg, ok=(0,)):
    """Jalankan skrip Python di paket sebagai proses terpisah; kembalikan (kode, keluaran)."""
    h = subprocess.run([sys.executable, str(PAKET / skrip)] + [str(a) for a in arg],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", env=ENV)
    keluar = (h.stdout or "") + (h.stderr or "")
    if ok is not None and h.returncode not in ok:
        raise Gagal("%s %s -> kode %d\n%s" % (skrip, " ".join(map(str, arg)), h.returncode, keluar[-1500:]))
    return h.returncode, keluar


@contextlib.contextmanager
def diam():
    """Tangkap cetakan; tampilkan hanya bila ada pengecualian."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        try:
            yield buf
        except BaseException:
            sys.__stdout__.write(buf.getvalue()[-1500:] + "\n")
            raise


def jalankan_main(modul, argv, ok=(0, None)):
    with diam() as buf:
        try:
            kode = modul.main(argv)
        except SystemExit as e:
            kode = e.code
            if kode not in ok:
                raise Gagal("%s %s berhenti: %s\n%s" % (modul.__name__, argv, e.code, buf.getvalue()[-800:]))
    harus(kode in ok, "%s %s kode %r" % (modul.__name__, argv, kode))
    return buf.getvalue()


class L:
    """Lingkungan uji bersama (dibuat sekali)."""
    tmp = None
    siap = False


def lingkungan():
    if L.siap:
        return L
    L.tmp = Path(tempfile.mkdtemp(prefix="sen12ls_uji_"))
    L.raw, L.out, L.hasil, L.benar = (L.tmp / n for n in ("raw", "out", "results", "benar"))
    L.points = L.tmp / "points.json"
    L.s1, L.s10 = L.out / "s1", L.out / "s10"
    L.siap = True
    return L


# ------------------------------------------------------------------ data
def uji_konversi_kecil():
    import buat_data_uji
    l = lingkungan()
    buat_data_uji.buat_kecil(str(l.raw), n=N_ANOTASI, n_patch=N_PATCH)
    kode, k = sub("data/convert_inventory.py", "--raw", l.raw, "--out", l.s1, "--profil", "tanpa")
    for nama, n in (("annotations.csv", N_ANOTASI + 1), ("annotations.ndjson", N_ANOTASI),
                    ("patches.csv", N_PATCH + 1), ("patches.ndjson", N_PATCH)):
        baris = (l.s1 / nama).read_text(encoding="utf-8").count("\n")
        harus(baris == n, "%s: %d baris, harap %d" % (nama, baris, n))
    dok = [json.loads(x) for x in (l.s1 / "annotations.ndjson").read_text(encoding="utf-8").splitlines()]
    pertama = dok[0]
    harus(pertama["center"]["type"] == "Point" and pertama["bbox"]["type"] == "Polygon", "bentuk dokumen Mongo salah")
    harus("dates" not in pertama, "anotasi tanpa tanggal tidak boleh punya field dates")
    ada = next(d for d in dok if "dates" in d)
    harus("$date" in json.dumps(ada["dates"]), "tanggal belum berbentuk Extended JSON")


def uji_konversi_tolak_masukan_rusak():
    l = lingkungan()
    kode, k = sub("data/convert_inventory.py", "--raw", l.tmp / "tidak_ada", "--out", l.tmp / "x", "--profil", "tanpa",
                  ok=(2,))
    harus("inventories" in k.lower() or "tidak ada" in k.lower(), "pesan galat tidak menjelaskan: " + k[-300:])


def uji_pemeriksa_data():
    l = lingkungan()
    arg = ["--skala", "S1", "--folder", l.s1, "--profil", "tanpa", "--harap-anotasi", N_ANOTASI,
           "--harap-patch", N_PATCH]
    kode, k = sub("data/cek_data.py", *arg)
    harus("SEMUA PEMERIKSAAN LULUS" in k, "tidak ada kalimat lulus:\n" + k[-500:])
    # negatif: buang satu baris dan harus ketahuan
    rusak = l.tmp / "rusak" / "s1"
    shutil.copytree(l.s1, rusak)
    baris = (rusak / "annotations.csv").read_text(encoding="utf-8").splitlines(True)
    (rusak / "annotations.csv").write_text("".join(baris[:100] + baris[101:]), encoding="utf-8", newline="")
    kode, k = sub("data/cek_data.py", "--skala", "S1", "--folder", rusak, "--profil", "tanpa",
                  "--harap-anotasi", N_ANOTASI, "--harap-patch", N_PATCH, ok=(1,))
    harus("GAGAL" in k, "pemeriksa tidak melaporkan baris yang hilang:\n" + k[-500:])
    # negatif: ubah satu nilai di CSV saja (NDJSON dan CSV harus tetap sama)
    rusak2 = l.tmp / "rusak2" / "s1"
    shutil.copytree(l.s1, rusak2)
    with open(rusak2 / "annotations.csv", encoding="utf-8", newline="") as f:
        semua = list(csv.reader(f))
    k = semua[0].index("center_lon")
    semua[4][k] = "%.7f" % (float(semua[4][k]) + 0.0001)
    with open(rusak2 / "annotations.csv", "w", encoding="utf-8", newline="") as f:
        csv.writer(f, lineterminator="\n").writerows(semua)
    kode, k = sub("data/cek_data.py", "--skala", "S1", "--folder", rusak2, "--profil", "tanpa",
                  "--harap-anotasi", N_ANOTASI, "--harap-patch", N_PATCH, ok=(1,))
    harus("GAGAL" in k, "pemeriksa tidak melihat CSV dan NDJSON yang berbeda:\n" + k[-500:])


def uji_generator():
    l = lingkungan()
    sub("data/generate_scales.py", "--scale", "S10", "--basis", l.s1, "--keluar", l.out)
    kode, k = sub("data/cek_data.py", "--skala", "S10", "--folder", l.s10, "--profil", "tanpa",
                  "--harap-anotasi", N_ANOTASI * 10, "--harap-patch", N_PATCH * 10)
    harus("SEMUA PEMERIKSAAN LULUS" in k, k[-500:])
    for nama in ("annotations.csv", "annotations.ndjson", "patches.csv", "patches.ndjson"):
        a = (l.s1 / nama).read_bytes()
        b = (l.s10 / nama)
        with open(b, "rb") as f:
            harus(f.read(len(a)) == a, "%s: S1 bukan awalan S10" % nama)
    ids = [int(r["ann_id"]) for r in csv.DictReader(open(l.s10 / "annotations.csv", encoding="utf-8", newline=""))]
    harus(ids == list(range(N_ANOTASI * 10)), "ann_id S10 tidak berurutan 0..n-1")
    # deterministik: buat ulang di folder lain, isinya sama
    l2 = l.tmp / "ulang"
    sub("data/generate_scales.py", "--scale", "S10", "--basis", l.s1, "--keluar", l2)
    for nama in ("annotations.csv", "patches.ndjson"):
        harus((l2 / "s10" / nama).read_bytes() == (l.s10 / nama).read_bytes(), "generator tidak deterministik: " + nama)


def uji_checksum():
    l = lingkungan()
    ck = l.tmp / "CHECKSUMS.txt"
    sub("data/generate_scales.py", "--write-checksums", "--keluar", l.out, "--checksums", ck)
    harus(ck.exists() and "out/s10/annotations.csv" in ck.read_text(encoding="utf-8"), "CHECKSUMS.txt tidak berisi s10")
    kode, k = sub("data/generate_scales.py", "--verify", "--keluar", l.out, "--checksums", ck, ok=(0, None))
    harus("COCOK" in k.upper() or "LULUS" in k.upper() or "OK" in k.upper(), "verifikasi tidak melaporkan cocok:\n" + k[-400:])
    # rusak satu bita di S10: --verify harus gagal (kode bukan 0) atau melaporkan beda
    p = l.s10 / "patches.csv"
    asli = p.read_bytes()
    try:
        p.write_bytes(asli[:-2] + b"X\n")
        kode, k = sub("data/generate_scales.py", "--verify", "--keluar", l.out, "--checksums", ck, ok=None)
        harus(kode != 0 or "BEDA" in k.upper() or "GAGAL" in k.upper() or "TIDAK COCOK" in k.upper(),
              "verifikasi tidak melihat berkas yang diubah:\n" + k[-400:])
    finally:
        p.write_bytes(asli)


def uji_batch_tambahan():
    l = lingkungan()
    sub("data/generate_scales.py", "--extra-batch", 10, "--basis", l.s1, "--keluar", l.out)
    baris = list(csv.DictReader(open(l.out / "batch10" / "annotations.csv", encoding="utf-8", newline="")))
    harus(len(baris) == N_ANOTASI, "jumlah baris batch tambahan %d" % len(baris))
    harus(int(baris[0]["ann_id"]) == N_ANOTASI * 10, "ann_id batch10 harus mulai %d, dapat %s" % (N_ANOTASI * 10, baris[0]["ann_id"]))
    harus(all(r["sim_batch"] == "10" for r in baris), "sim_batch bukan 10")


# ------------------------------------------------------------------ bench
def pasang_kecil():
    import kueri
    import kebenaran
    import compare_counts
    l = lingkungan()
    kueri.N_DASAR_ANOTASI, kueri.N_DASAR_PATCH = N_ANOTASI, N_PATCH
    kebenaran.BENAR_DIR = l.benar
    compare_counts.BENAR_DIR = l.benar
    return kueri


def uji_titik():
    import make_points
    l = lingkungan()
    pasang_kecil()
    with diam():
        make_points.main(None, src=l.s1 / "annotations.csv", out=l.points)
    d = json.loads(l.points.read_text(encoding="utf-8"))
    p = d["points"]
    harus(len(p) == 100 and sum(1 for x in p if x["inside"]) == 70, "harus 100 titik (70 di dalam)")
    harus([x["id"] for x in p] == list(range(1, 101)), "id titik harus 1..100")
    h1 = hashlib.sha256(l.points.read_bytes()).hexdigest()
    with diam():
        make_points.main(None, src=l.s1 / "annotations.csv", out=l.tmp / "p2.json")
    harus(hashlib.sha256((l.tmp / "p2.json").read_bytes()).hexdigest() == h1, "titik tidak deterministik")


def uji_wasit():
    import kebenaran
    l = lingkungan()
    pasang_kecil()
    for skala, folder in (("S1", l.s1), ("S10", l.s10)):
        out = jalankan_main(kebenaran, ["--skala", skala, "--folder", str(folder), "--points", str(l.points), "--tulis"])
        harus("W2" in out and (l.benar / ("W3_%s.csv" % skala)).exists(), "wasit tidak menulis berkas " + skala)
    out = jalankan_main(kebenaran, ["--skala", "S1", "--folder", str(l.s1), "--points", str(l.points), "--ann", "0"])
    harus("Anotasi 0" in out, "contoh --ann 0 tidak tercetak")
    harus(sum(int(r["jumlah_hasil"]) for r in csv.DictReader(open(l.benar / "W2_S1.csv", encoding="utf-8"))) > 0,
          "wasit W2 S1 semua nol: titik uji dalam tidak menemukan apa pun")


def bandingkan(beban, skala, berkas):
    import compare_counts
    with diam() as buf:
        kode = compare_counts.main([str(b) for b in berkas])
    return kode, buf.getvalue()


def jalankan_harness(store, skala, beban=None, tambahan=()):
    import harness
    l = lingkungan()
    pasang_kecil()
    hasil = []
    for w in ([beban] if beban else ["W1", "W2", "W3", "W4", "W5", "W6"]):
        before = set(p.name for p in l.hasil.glob("*.csv")) if l.hasil.exists() else set()
        jalankan_main(harness, ["--store", store, "--workload", w, "--scale", skala, "--repeats", "1",
                                "--points", str(l.points), "--results", str(l.hasil)] + list(tambahan))
        baru = sorted(set(p.name for p in l.hasil.glob("*.csv")) - before)
        harus(len(baru) == 1, "harness %s %s menulis %d berkas" % (store, w, len(baru)))
        hasil.append((w, l.hasil / baru[0]))
    return hasil


def pakai_stub(nama):
    sys.path.insert(0, str(STUBS))
    for m in [m for m in sys.modules if m == nama or m.startswith(nama + ".")]:
        del sys.modules[m]
    return __import__(nama)


def cocokkan_semua(store, skala, berkas_per_beban, lainnya=None):
    """Bandingkan hasil satu penyimpanan dengan wasit (dua berkas: hasil + dirinya sendiri ditambah wasit otomatis)."""
    for w, jalur in berkas_per_beban:
        kode, k = bandingkan(w, skala, [jalur, jalur])
        harus(kode == 0, "%s %s %s berbeda dari wasit:\n%s" % (store, w, skala, k[-900:]))
        harus("benar" in k, "wasit tidak ikut dibandingkan (%s %s %s):\n%s" % (store, w, skala, k[-400:]))


def uji_mongo_tiruan():
    pymongo = pakai_stub("pymongo")
    pakai_stub("bson")
    import muat_pymongo as mm
    l = lingkungan()
    pasang_kecil()
    pymongo.kosongkan()
    out = jalankan_main(mm, ["--folder", str(l.s1), "--skala", "S1"])
    harus("annotations %d" % N_ANOTASI in out and "patches %d" % N_PATCH in out, "pemuat tidak melaporkan jumlah:\n" + out[-300:])
    berkas = jalankan_harness("mongodb", "S1")
    cocokkan_semua("mongodb", "S1", berkas)
    # skala yang salah harus ditolak oleh pagar jumlah baris
    import harness
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            harness.main(["--store", "mongodb", "--workload", "W2", "--scale", "S10", "--repeats", "1",
                          "--points", str(l.points), "--results", str(l.hasil)])
    except SystemExit as e:
        harus("tidak cocok" in str(e), "pagar jumlah baris memberi pesan lain: " + str(e)[-300:])
    else:
        raise Gagal("harness seharusnya menolak skala S10 saat yang dimuat S1")
    # S10 dan tambah batch
    pymongo.kosongkan()
    jalankan_main(mm, ["--folder", str(l.s10), "--skala", "S10"])
    cocokkan_semua("mongodb", "S10", jalankan_harness("mongodb", "S10", tambahan=["--limit-titik", "30"]))
    jalankan_main(mm, ["--folder", str(l.out / "batch10"), "--tambah"])
    harus(pymongo.MongoClient()["sen12ls"]["annotations"].estimated_document_count() == N_ANOTASI * 11,
          "penambahan batch10 tidak menambah jumlah")


def uji_mongo_banyak_klien_dan_cold():
    pymongo = pakai_stub("pymongo")
    pakai_stub("bson")
    import muat_pymongo as mm
    l = lingkungan()
    pasang_kecil()
    pymongo.kosongkan()
    jalankan_main(mm, ["--folder", str(l.s1), "--skala", "S1"])
    (w, jalur), = jalankan_harness("mongodb", "S1", "W1", ["--clients", "3", "--repeats", "2", "--note", "uji"])
    baris = list(csv.DictReader(open(jalur, encoding="utf-8", newline="")))
    harus(len(baris) == 3 * 2 * 100, "baris W1 3 klien x 2 ulangan x 100 = 600, dapat %d" % len(baris))
    harus(all("konkurensi=3" in b["catatan"] for b in baris), "kolom catatan tidak memuat konkurensi=3")
    (w, jalur), = jalankan_harness("mongodb", "S1", "W3", ["--cold-warm", "cold", "--first-run-no", "4", "--limit-titik", "10"])
    baris = list(csv.DictReader(open(jalur, encoding="utf-8", newline="")))
    harus(len(baris) == 10 and baris[0]["ulangan"] == "4" and baris[0]["cold_warm"] == "cold",
          "mode cold/first-run-no/limit-titik salah")


def uji_postgis_tiruan():
    psycopg = pakai_stub("psycopg")
    l = lingkungan()
    pasang_kecil()
    psycopg.kosongkan()
    psycopg.muat_csv(str(l.s1))
    cocokkan_semua("postgis", "S1", jalankan_harness("postgis", "S1"))
    psycopg.kosongkan()
    psycopg.muat_csv(str(l.s10))
    cocokkan_semua("postgis", "S10", jalankan_harness("postgis", "S10"))


def uji_spark_tiruan():
    pakai_stub("pyspark")
    import pyspark.sql as pss
    import csv_to_parquet
    import run_sql
    import harness
    l = lingkungan()
    pasang_kecil()
    pss.kosongkan()

    def ganti_subprocess(perintah):
        i = perintah.index("/hdfs-parquet/run_sql.py")
        arg = list(perintah[i + 1:])
        j = arg.index("--out")
        arg[j + 1] = str(l.hasil / Path(arg[j + 1]).name)
        arg += ["--points", str(l.points)]
        return 0 if run_sql.main(arg) in (0, None) else 1

    asli = harness.subprocess.call
    harness.subprocess.call = ganti_subprocess
    try:
        for skala, folder in (("S1", l.s1), ("S10", l.s10)):
            pss.kosongkan()
            out = jalankan_main(csv_to_parquet, ["--scale", skala, "--folder", str(folder)])
            harus("annotations: %d baris" % (N_ANOTASI * (1 if skala == "S1" else 10)) in out, "jumlah baris Parquet salah:\n" + out[-300:])
            sebelum = set(p.name for p in l.hasil.glob("*.csv")) if l.hasil.exists() else set()
            berkas = []
            for w in ["W1", "W2", "W3", "W4", "W5", "W6"]:
                s2 = set(p.name for p in l.hasil.glob("*.csv")) if l.hasil.exists() else set()
                jalankan_main(harness, ["--store", "spark", "--workload", w, "--scale", skala, "--repeats", "1",
                                        "--results", str(l.hasil)])
                baru = sorted(set(p.name for p in l.hasil.glob("*.csv")) - s2)
                harus(len(baru) == 1, "spark %s menulis %d berkas" % (w, len(baru)))
                berkas.append((w, l.hasil / baru[0]))
            cocokkan_semua("spark", skala, berkas)
    finally:
        harness.subprocess.call = asli


def uji_bandingkan_tiga_dan_beda():
    import compare_counts
    l = lingkungan()
    pasang_kecil()
    hasil = {}
    for p in sorted(l.hasil.glob("*.csv")):
        baris = list(csv.DictReader(open(p, encoding="utf-8", newline="")))
        if baris[0]["cold_warm"] != "warm" or "konkurensi" in baris[0]["catatan"] or len(baris) < 100:
            continue
        k = (baris[0]["penyimpanan"], baris[0]["beban_kerja"], baris[0]["skala"])
        if baris[0]["skala"] == "S1":
            hasil[k] = p
    harus(("mongodb", "W3", "S1") in hasil and ("postgis", "W3", "S1") in hasil and ("spark", "W3", "S1") in hasil,
          "berkas hasil tiga penyimpanan belum ada: " + str(sorted(hasil)))
    kode, k = bandingkan("W3", "S1", [hasil[("mongodb", "W3", "S1")], hasil[("postgis", "W3", "S1")],
                                       hasil[("spark", "W3", "S1")]])
    harus(kode == 0 and "Semua jumlah hasil sama" in k, "tiga penyimpanan harus sama:\n" + k[-400:])
    # sisipkan selisih satu kueri: harus terdeteksi (kode 1)
    baris = list(csv.reader(open(hasil[("postgis", "W2", "S1")], encoding="utf-8", newline="")))
    i = next(i for i, r in enumerate(baris[1:], 1) if int(r[7]) >= 0)
    baris[i][7] = str(int(baris[i][7]) + 1)
    rusak = l.tmp / "rusak_postgis_W2.csv"
    with open(rusak, "w", encoding="utf-8", newline="") as f:
        csv.writer(f, lineterminator="\n").writerows(baris)
    kode, k = bandingkan("W2", "S1", [hasil[("mongodb", "W2", "S1")], rusak])
    harus(kode == 1 and "Ada 1 kueri yang beda" in k, "selisih satu kueri tidak terdeteksi:\n" + k[-400:])
    # --titik-maks: selisih di atas batas tidak dihitung, selisih di dalam batas tetap terdeteksi
    asal2 = list(csv.reader(open(hasil[("postgis", "W2", "S1")], encoding="utf-8", newline="")))
    awal2 = min(int(r[3]) for r in asal2[1:])
    j = max((n for n, r in enumerate(asal2[1:], 1) if int(r[3]) == awal2 and int(r[7]) >= 0),
            key=lambda n: int(asal2[n][5]))
    q_akhir = int(asal2[j][5])
    asal2[j][7] = str(int(asal2[j][7]) + 1)
    rusak_akhir = l.tmp / "rusak_postgis_W2_akhir.csv"
    with open(rusak_akhir, "w", encoding="utf-8", newline="") as f:
        csv.writer(f, lineterminator="\n").writerows(asal2)
    kode, k = bandingkan("W2", "S1", [hasil[("mongodb", "W2", "S1")], rusak_akhir])
    harus(kode == 1 and "Ada 1 kueri yang beda" in k, "selisih di kueri terakhir tidak terdeteksi:\n" + k[-400:])
    kode, k = bandingkan("W2", "S1", [hasil[("mongodb", "W2", "S1")], rusak_akhir, "--titik-maks", q_akhir - 1])
    harus(kode == 0 and ("Hanya kueri_id 1 sampai %d" % (q_akhir - 1)) in k and "Semua jumlah hasil sama" in k,
          "--titik-maks harus membuang selisih di atas batas:\n" + k[-400:])
    kode, k = bandingkan("W2", "S1", [hasil[("mongodb", "W2", "S1")], rusak_akhir, "--titik-maks=%d" % q_akhir])
    harus(kode == 1 and "Ada 1 kueri yang beda" in k, "--titik-maks harus tetap mendeteksi selisih di dalam batas:\n" + k[-400:])
    # beban kerja berbeda dicampur: ditolak (kode 2)
    kode, k = bandingkan("W2", "S1", [hasil[("mongodb", "W2", "S1")], hasil[("mongodb", "W3", "S1")]])
    harus(kode == 2, "campuran beban kerja harus ditolak")
    # satu berkas dibandingkan dengan wasit: benar -> 0, rusak -> 1, wasit tidak ada -> 2
    kode, k = bandingkan("W2", "S1", [hasil[("mongodb", "W2", "S1")]])
    harus(kode == 0 and "benar" in k and "Semua jumlah hasil sama" in k, "satu berkas vs wasit harus cocok:\n" + k[-400:])
    kode, k = bandingkan("W2", "S1", [rusak])
    harus(kode == 1 and "Ada 1 kueri yang beda" in k, "satu berkas rusak vs wasit harus terdeteksi:\n" + k[-400:])
    benar_w2 = l.benar / "W2_S1.csv"
    sementara = l.benar / "W2_S1.csv.simpan"
    benar_w2.rename(sementara)
    try:
        kode, k = bandingkan("W2", "S1", [hasil[("mongodb", "W2", "S1")]])
        harus(kode == 2 and "wasit" in k, "satu berkas tanpa wasit harus ditolak:\n" + k[-300:])
    finally:
        sementara.rename(benar_w2)


def uji_ringkasan():
    import summarize
    l = lingkungan()
    summarize.RESULTS = l.hasil
    out = jalankan_main(summarize, [str(p) for p in sorted(l.hasil.glob("*.csv"))
                                    if p.name not in ("ringkasan.csv", "banding.csv")])
    baris = list(csv.DictReader(open(l.hasil / "banding.csv", encoding="utf-8", newline="")))
    harus(baris, "banding.csv kosong")
    w3 = [b for b in baris if b["beban_kerja"] == "W3" and b["skala"] == "S1" and b["cold_warm"] == "warm"]
    harus(w3 and all(w3[0]["median_ms_" + s] for s in ("mongodb", "postgis", "spark")),
          "banding.csv W3 S1 harus berisi tiga penyimpanan: " + str(w3))
    harus((l.hasil / "ringkasan.csv").exists() and "median_ms" in out, "ringkasan tidak ditulis")
    # varian (E1): hasil bercatatan varian=... tidak boleh bercampur dengan hasil biasa
    asal = next(p for p in sorted(l.hasil.glob("*_mongodb_W3_S1.csv")))
    baris = list(csv.reader(open(asal, encoding="utf-8", newline="")))
    for r in baris[1:]:
        r[6] = "%.3f" % (float(r[6]) * 50 + 1000)
        r[8] = (r[8] + " varian=tanpa-indeks").strip()
    varian_csv = l.tmp / "varian_mongodb_W3_S1.csv"
    with open(varian_csv, "w", encoding="utf-8", newline="") as f:
        csv.writer(f, lineterminator="\n").writerows(baris)
    jalankan_main(summarize, [str(asal), str(varian_csv)])
    rs = list(csv.DictReader(open(l.hasil / "ringkasan.csv", encoding="utf-8", newline="")))
    harus(len(rs) == 2 and {r["varian"] for r in rs} == {"", "tanpa-indeks"},
          "varian harus menjadi dua kelompok: " + str([(r["penyimpanan"], r["varian"]) for r in rs]))
    biasa = next(r for r in rs if r["varian"] == "")
    tanpa = next(r for r in rs if r["varian"] == "tanpa-indeks")
    harus(float(tanpa["median_ms"]) >= 1000 > 10 * float(biasa["median_ms"]),
          "median varian bercampur dengan median biasa: %s vs %s" % (tanpa["median_ms"], biasa["median_ms"]))
    # --titik-maks: hanya kueri_id sampai N pada skala di --titik-skala; skala lain tidak disentuh
    semua = list(csv.DictReader(open(asal, encoding="utf-8", newline="")))
    jalankan_main(summarize, [str(asal), "--titik-maks", "2", "--titik-skala", "S1"])
    rs = list(csv.DictReader(open(l.hasil / "ringkasan.csv", encoding="utf-8", newline="")))
    harus(len(rs) == 1 and int(rs[0]["kueri_n"]) == sum(
        1 for r in semua if int(r["kueri_id"]) <= 2 and r["jumlah_hasil"].strip() != "-1"),
        "--titik-maks 2 pada S1 harus membuang kueri_id > 2: " + str([r["kueri_n"] for r in rs]))
    jalankan_main(summarize, [str(asal), "--titik-maks=2"])
    rs = list(csv.DictReader(open(l.hasil / "ringkasan.csv", encoding="utf-8", newline="")))
    harus(len(rs) == 1 and int(rs[0]["kueri_n"]) == sum(1 for r in semua if r["jumlah_hasil"].strip() != "-1"),
          "bawaan --titik-skala hanya S100: S1 tidak boleh berubah: " + str([r["kueri_n"] for r in rs]))
    jalankan_main(summarize, [str(p) for p in sorted(l.hasil.glob("*.csv"))
                              if p.name not in ("ringkasan.csv", "banding.csv")])


def uji_catat():
    import catat
    l = lingkungan()
    catat.RESULTS, catat.OUT = l.tmp / "results_catat", l.out
    d = catat.urai_mongo('log\n{"n":600,"data":123456,"storage":100000,"idx":50000,"tot":150000}\n')
    harus(d["storage"] == 100000.0, "urai_mongo")
    harus(catat.urai_pg("1048576|524288|2097152\n") == (1048576.0, 524288.0, 2097152.0), "urai_pg")
    harus(catat.urai_hdfs("12345  24690  /data/sen12ls/parquet/s1/annotations\n") == (12345.0, 24690.0), "urai_hdfs")
    for salah, f in (("bukan json", catat.urai_mongo), ("a|b|c", catat.urai_pg), ("tidak ada", catat.urai_hdfs)):
        try:
            f(salah)
        except ValueError:
            continue
        raise Gagal("pengurai harus menolak: " + salah)
    jalankan_main(catat, ["waktu", "--store", "mongodb", "--skala", "S1", "--jenis", "muat", "--detik", "12,5"])
    jalankan_main(catat, ["ukur", "--store", "mongodb", "--skala", "S1", "--jenis", "indeks", "--objek", "uji",
                          sys.executable, "-c", "import time; time.sleep(0.05)", "--db", "x"])
    jalankan_main(catat, ["ukur", "--store", "postgis", "--skala", "S1", "--jenis", "muat",
                          sys.executable, "-c", "import sys; sys.exit(3)"], ok=(3,))
    harus(not (catat.RESULTS / "pengukuran_postgis.csv").exists(), "perintah gagal tidak boleh dicatat")
    jalankan_main(catat, ["ukuran", "--store", "mentah", "--skala", "S1"])
    jalankan_main(catat, ["ukuran", "--store", "postgis", "--skala", "S1", "--mb", "21,5", "--objek", "annotations"])
    # ukuran otomatis dengan docker palsu
    keluaran = {
        "mongosh": '{"n":600,"data":2097152,"storage":1048576,"idx":524288,"tot":1572864}',
        "psql": "1048576|524288|1572864",
        "hdfs": "1048576 2097152 /data/sen12ls/parquet/s1/annotations",
    }

    def palsu(perintah):
        for k, v in keluaran.items():
            if k in perintah:
                return v + "\n"
        raise Gagal("perintah tak terduga: %s" % perintah)

    asli = catat.jalankan
    catat.jalankan = palsu
    try:
        for store in ("mongodb", "postgis", "spark"):
            jalankan_main(catat, ["ukuran", "--store", store, "--skala", "S1"])
    finally:
        catat.jalankan = asli
    out = jalankan_main(catat, ["tampil"])
    harus("ukuran_total" in out and "annotations" in out, "tampil tidak memuat ukuran_total:\n" + out[-500:])
    rows = list(csv.DictReader(open(catat.RESULTS / "pengukuran_mongodb.csv", encoding="utf-8", newline="")))
    harus(any(r["jenis"] == "muat" and abs(float(r["nilai"]) - 12.5) < 1e-9 for r in rows), "waktu 12,5 tidak tercatat")
    harus(any(r["jenis"] == "indeks" and r["objek"] == "uji" for r in rows), "hasil 'ukur' tidak tercatat")


# ------------------------------------------------------------------ statis
def uji_js_dan_sql():
    node = shutil.which("node")
    import kueri
    ctoh = {"id": 1, "lon": 11.4548681, "lat": 43.7734078, "date_from": "2019-02-15", "date_to": "2019-04-16",
            "event_type": "Rainfall", "ann_id": 0}
    for b in kueri.BEBAN:
        teks = (PAKET / "hdfs-parquet" / "sql" / ("%s.sql" % b.lower())).read_text(encoding="utf-8")
        harus(kueri.sql_spark(b, ctoh, kueri.PARAMETER_BAWAAN) + ";" in teks,
              "hdfs-parquet/sql/%s.sql tidak sama dengan kueri.sql_spark" % b.lower())
    if not node:
        print("   (node tidak ada: pemeriksaan JavaScript dilewati)")
        return
    for js in sorted((PAKET / "mongodb").rglob("*.js")):
        h = subprocess.run([node, "--check", str(js)], capture_output=True, text=True)
        harus(h.returncode == 0, "sintaks %s: %s" % (js.name, h.stderr[-300:]))
    fake = PAKET / "tests" / "fake_db.js"
    for lon, lat, half in [(11.4548681, 43.7734078, 0.01), (-70.3012345, -34.5512345, 0.1),
                           (174.0759371, -42.6305651, 0.01), (107.8765432, -6.1234567, 0.1)]:
        h = subprocess.run([node, str(fake), str(PAKET / "mongodb" / "queries" / "_umum.js"), str(lon), str(lat), str(half)],
                           capture_output=True, text=True)
        harus(h.returncode == 0, "fake_db.js: " + h.stderr[-300:])
        js = json.loads(h.stdout)
        w = kueri.jendela(lon, lat, half)
        harus(js["w"] == list(w), "jendela JS beda dari Python di (%s, %s, %s)" % (lon, lat, half))
        harus(js["ring"] == [list(p) for p in kueri.cincin_mongo(*w)], "cincin JS beda dari Python")


def uji_compose_dan_nama():
    teks = {}
    for f in ("mongodb", "postgis", "hdfs-parquet"):
        teks[f] = (PAKET / f / "docker-compose.yml").read_text(encoding="utf-8")
    harus("container_name: sen12ls-mongo" in teks["mongodb"] and "27017:27017" in teks["mongodb"], "compose mongodb")
    harus("container_name: sen12ls-postgis" in teks["postgis"] and "5433:5432" in teks["postgis"], "compose postgis")
    for n in ("sen12ls-namenode", "sen12ls-datanode1", "sen12ls-datanode2", "sen12ls-spark"):
        harus("container_name: " + n in teks["hdfs-parquet"], "compose hdfs: " + n)
    for f, t in teks.items():
        harus("../data:/sen12ls-data:ro" in t, "%s: data harus dipasang read-only di /sen12ls-data" % f)
        harus("\t" not in t, "%s: ada tab di YAML" % f)
        harus("version:" not in t, "%s: jangan pakai 'version:'" % f)
    try:
        import yaml
    except ImportError:
        return
    for f, t in teks.items():
        d = yaml.safe_load(t)
        harus("services" in d, "%s: YAML tanpa services" % f)
    # tidak boleh ada sisa nama proyek lama
    sisa = []
    for p in PAKET.rglob("*"):
        if p.is_file() and p.suffix in (".py", ".js", ".sql", ".yml", ".env", ".md", ".txt") and "tests/uji_semua.py" not in p.as_posix() and "arsip" not in p.relative_to(PAKET).parts:
            t = p.read_text(encoding="utf-8", errors="replace")
            for kata in ("sen12tp-", "scenes.ndjson", "scenes.csv", "scene_id"):
                if kata in t:
                    sisa.append("%s: %s" % (p.relative_to(PAKET), kata))
    harus(not sisa, "sisa nama proyek lama: " + "; ".join(sisa[:8]))


def uji_konversi_laporan():
    """Konversi data berbentuk laporan asli (75 ribu poligon): self-check harus LOLOS (butuh sekitar 30 detik)."""
    import buat_data_uji
    l = lingkungan()
    folder = l.tmp / "raw_laporan"
    buat_data_uji.buat_laporan(str(folder))
    kode, k = sub("data/convert_inventory.py", "--raw", folder, "--out", l.tmp / "out_laporan")
    harus("LOLOS" in k.upper() or kode == 0, k[-600:])
    kode, k = sub("data/cek_data.py", "--skala", "S1", "--folder", l.tmp / "out_laporan")
    harus("SEMUA PEMERIKSAAN LULUS" in k, k[-600:])


UJI = [
    ("konversi_kecil", uji_konversi_kecil), ("konversi_tolak_masukan_rusak", uji_konversi_tolak_masukan_rusak),
    ("pemeriksa_data", uji_pemeriksa_data), ("generator", uji_generator), ("checksum", uji_checksum),
    ("batch_tambahan", uji_batch_tambahan), ("titik_uji", uji_titik), ("wasit", uji_wasit),
    ("mongo_tiruan", uji_mongo_tiruan), ("mongo_banyak_klien_cold", uji_mongo_banyak_klien_dan_cold),
    ("postgis_tiruan", uji_postgis_tiruan), ("spark_tiruan", uji_spark_tiruan),
    ("bandingkan", uji_bandingkan_tiga_dan_beda), ("ringkasan", uji_ringkasan), ("catat", uji_catat),
    ("js_dan_sql_referensi", uji_js_dan_sql), ("compose_dan_nama", uji_compose_dan_nama),
]
PENUH = [("konversi_laporan", uji_konversi_laporan)]
KUNCI_DATA = {"konversi_kecil"}


def main(argv=None):
    ap = argparse.ArgumentParser(description="Uji menyeluruh tanpa Docker.")
    ap.add_argument("--penuh", action="store_true", help="tambah uji konversi berbentuk laporan asli")
    ap.add_argument("--simpan", action="store_true", help="jangan hapus folder sementara")
    ap.add_argument("-k", dest="filter", help="jalankan uji yang namanya memuat teks ini")
    args = ap.parse_args(argv)
    daftar = UJI + (PENUH if args.penuh else [])
    lulus = gagal = lewat = 0
    prasyarat_ok = True
    t_awal = time.time()
    try:
        for nama, f in daftar:
            if args.filter and args.filter not in nama:
                continue
            if not prasyarat_ok and nama != "compose_dan_nama" and nama != "js_dan_sql_referensi":
                print("LEWAT  %s (data uji dasar gagal dibuat)" % nama)
                lewat += 1
                continue
            t0 = time.time()
            try:
                f()
            except Exception as e:  # noqa: BLE001
                gagal += 1
                print("GAGAL  %s (%.1f detik)" % (nama, time.time() - t0))
                msg = str(e) if isinstance(e, Gagal) else traceback.format_exc()
                print("       " + msg.replace("\n", "\n       "))
                if nama in ("konversi_kecil", "generator", "titik_uji"):
                    prasyarat_ok = False
            else:
                lulus += 1
                print("OK     %s (%.1f detik)" % (nama, time.time() - t0))
    finally:
        if L.tmp and not args.simpan:
            shutil.rmtree(L.tmp, ignore_errors=True)
        elif L.tmp:
            print("Folder sementara disimpan di", L.tmp)
    print()
    if gagal or lewat:
        print("ADA YANG GAGAL: %d lulus, %d gagal, %d dilewati (%.0f detik)" % (lulus, gagal, lewat, time.time() - t_awal))
        return 1
    print("SEMUA UJI LULUS (%d uji, %.0f detik)" % (lulus, time.time() - t_awal))
    return 0


if __name__ == "__main__":
    sys.exit(main())
