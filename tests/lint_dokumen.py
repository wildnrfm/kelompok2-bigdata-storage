#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Periksa dokumen .md di repo: tautan relatif dan jangkarnya, pagar kode ```, dan jalur berkas yang disebut di panduan.

Pakai (dari akar repo):  python tests/lint_dokumen.py
Keluar 0 bila bersih, 1 bila ada masalah. Tidak butuh pustaka tambahan, tidak butuh Docker.
Berkas yang memang dibuat kemudian (data/out, data/CHECKSUMS.txt, bench/points.json, bench/benar) tidak dianggap masalah.
"""
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(errors="replace")
except Exception:
    pass

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent
DIBUAT_KEMUDIAN = ("data/out", "data/raw/", "data/CHECKSUMS.txt", "bench/points.json", "bench/benar",
                   "postgis/postgis", "results/", "docs/", "latihan/")
POLA_JALUR = re.compile(r"`((?:bench|postgis|mongodb|hdfs-parquet|data|tests|baca-dulu)[/\\][A-Za-z0-9_.\-/\\]+)`")


def slug(judul):
    judul = judul.strip().lower()
    judul = re.sub(r"[^\w\s-]", "", judul, flags=re.UNICODE)
    return re.sub(r"\s", "-", judul)


def jangkar(berkas):
    hasil, dalam = set(), False
    for baris in berkas.read_text(encoding="utf-8").splitlines():
        if baris.strip().startswith("```"):
            dalam = not dalam
            continue
        if dalam:
            continue
        m = re.match(r"^(#{1,6})\s+(.*)$", baris)
        if m:
            hasil.add(slug(m.group(2)))
    return hasil


def main():
    daftar = sorted(p for p in ROOT.rglob("*.md") if "__pycache__" not in p.parts and ".git" not in p.parts)
    masalah, cache = [], {}
    for p in daftar:
        nama = p.relative_to(ROOT).as_posix()
        teks = p.read_text(encoding="utf-8")
        if teks.count("```") % 2:
            masalah.append("%s: pagar kode ``` berjumlah ganjil" % nama)
        polos = re.sub(r"```.*?```", "", teks, flags=re.S)
        polos = re.sub(r"`[^`\n]*`", "", polos)
        for m in re.finditer(r"\[[^\]]*\]\(([^)\s]+)\)", polos):
            tujuan = m.group(1)
            if re.match(r"^(https?:|mailto:)", tujuan):
                continue
            berkas, _, tanda = tujuan.partition("#")
            dest = p if not berkas else (p.parent / berkas).resolve()
            if not dest.exists():
                masalah.append("%s: tautan rusak -> %s" % (nama, tujuan))
                continue
            if tanda and dest.suffix == ".md":
                if tanda not in cache.setdefault(dest, jangkar(dest)):
                    masalah.append("%s: jangkar tidak ada -> %s" % (nama, tujuan))
        for m in POLA_JALUR.finditer(teks):
            s = m.group(1).rstrip(".,;:").replace("\\", "/")
            if "*" in s or any(s.startswith(a) for a in DIBUAT_KEMUDIAN):
                continue
            if not (ROOT / s).exists():
                masalah.append("%s: berkas yang disebut tidak ada -> %s" % (nama, s))
    for baris in masalah:
        print("MASALAH", baris)
    print("%d berkas .md diperiksa, %d masalah." % (len(daftar), len(masalah)))
    return 1 if masalah else 0


if __name__ == "__main__":
    sys.exit(main())
