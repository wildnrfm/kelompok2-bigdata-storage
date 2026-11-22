#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Grafik hasil analitik (PNG) dari tabel CSV tahap analitik. Butuh matplotlib (pip install matplotlib).

Pemakaian (dari akar repo, PowerShell):
  python analitik\\grafik.py
  python analitik\\grafik.py --sumber results\\analitik\\S1 --keluar results\\analitik\\grafik --dpi 300
Bawaan: sumber = results/analitik/S1 bila ada, selain itu analitik/referensi_S1 (isinya sama, sudah
dicocokkan dengan hasil Spark); keluaran = results/analitik/grafik. Grafik waktu pemrosesan (g6) hanya
dibuat bila results/analitik/ringkasan_waktu.csv ada (jalankan analitik/ringkas_waktu.py dulu).

Lebar gambar 14 cm (lebar teks laporan A4), jadi ukuran huruf di gambar = ukuran huruf di kertas.
Aturan rupa (dataviz): satu hue untuk besaran (biru, terang -> gelap), warna kategori hanya untuk jenis
kejadian dan SAMA di semua gambar (Hujan biru, Gempa oranye, Siklon tropis hijau-air, Tanpa jenis abu-abu),
teks memakai warna teks (bukan warna seri), garis kisi tipis dan padat, nilai ditulis langsung hanya pada
titik yang penting. Satuan kolom area tidak dinyatakan sumber data, jadi sumbu luas diberi label apa adanya.
"""
import argparse
import csv
import math
import os
import sys
from pathlib import Path

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    from matplotlib import colors as mcolors
    from matplotlib import patches as mpatches
    from matplotlib.colors import LinearSegmentedColormap
    from matplotlib.lines import Line2D
    from matplotlib.path import Path as MPath
except ImportError:
    raise SystemExit("Butuh matplotlib. Pasang dengan:  python -m pip install matplotlib")

AKAR = Path(__file__).resolve().parent.parent

# ------------------------------------------------------------------ palet (dataviz, permukaan putih)
SURF, INK, INK2, MUTED, GRID, BASE = "#ffffff", "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
BIRU = ["#cde2fb", "#b7d3f6", "#9ec5f4", "#86b6ef", "#6da7ec", "#5598e7", "#3987e5", "#2a78d6",
        "#256abf", "#1c5cab", "#184f95", "#104281", "#0d366b"]          # langkah 100..700, satu hue
CMAP = LinearSegmentedColormap.from_list("biru", BIRU)
KELUARGA = ["Hujan", "Gempa", "Siklon tropis", "Tanpa jenis"]
WARNA = {"Hujan": "#2a78d6", "Gempa": "#eb6834", "Siklon tropis": "#1baf7a", "Tanpa jenis": "#c3c2b7"}
NAMA_KELUARGA = {"Hujan": "Hujan (Rainfall)", "Gempa": "Gempa (Earthquake)",
                 "Siklon tropis": "Siklon tropis (Hurricane, Cyclone, Tropical Storm)",
                 "Tanpa jenis": "Tanpa jenis (event_type kosong)"}
KEL_JENIS = {"Rainfall": "Hujan", "Earthquake": "Gempa", "Hurricane": "Siklon tropis", "Cyclone": "Siklon tropis",
             "Tropical Storm": "Siklon tropis", "(kosong)": "Tanpa jenis"}
UNGU = "#6250d6"          # seri tunggal pada grafik waktu (bukan jenis kejadian, jadi bukan warna keluarga)
BULAN = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]
LEBAR_IN = 14.0 / 2.54    # 14 cm
ETIKET = dict(facecolor=SURF, edgecolor="none", pad=1.0)   # latar putih: garis kisi tidak menembus tulisan

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Segoe UI", "Helvetica Neue", "Arial", "DejaVu Sans"],
    "font.size": 7.5, "axes.edgecolor": BASE, "axes.labelcolor": INK2, "xtick.color": MUTED, "ytick.color": MUTED,
    "text.color": INK, "figure.facecolor": SURF, "axes.facecolor": SURF, "savefig.facecolor": SURF,
    "axes.linewidth": 0.6, "xtick.major.width": 0.6, "ytick.major.width": 0.6, "axes.unicode_minus": False,
})


# ------------------------------------------------------------------ alat kecil
def idn(x, desimal=0):
    """Angka berpola Indonesia: titik untuk ribuan, koma untuk desimal."""
    s = ("{:,.%df}" % desimal).format(x)
    return s.replace(",", "\0").replace(".", ",").replace("\0", ".")


def baca(sumber, nama):
    jalur = os.path.join(sumber, nama + ".csv")
    if not os.path.exists(jalur):
        raise SystemExit("Tidak ada %s. Jalankan spark_pipeline.py atau referensi.py dulu." % jalur)
    with open(jalur, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def angka(x):
    return None if x == "" else float(x)


def teks_di_atas(warna_isi):
    """Putih atau hampir-hitam, mana yang kontrasnya lebih tinggi di atas isi itu."""
    def lum(h):
        r, g, b = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
        f = lambda c: c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4  # noqa: E731
        return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)
    l = lum(warna_isi)
    return "#ffffff" if (1.05 / (l + 0.05)) > ((l + 0.05) / 0.0522) else INK


def gaya(ax, kisi="x", spines=("left", "bottom")):
    for s in ("top", "right", "left", "bottom"):
        ax.spines[s].set_visible(s in spines)
    ax.tick_params(length=2.5, labelsize=7)
    ax.set_axisbelow(True)
    if kisi:
        ax.grid(axis=kisi, color=GRID, linewidth=0.6, linestyle="-")


def simpan(fig, jalur, dpi):
    os.makedirs(os.path.dirname(jalur), exist_ok=True)
    fig.savefig(jalur, dpi=dpi)
    plt.close(fig)
    print("  tulis", jalur)


def tgl(s):
    """'2023-05-16' -> '16 Mei 2023'."""
    return "%d %s %s" % (int(s[8:10]), BULAN[int(s[5:7]) - 1], s[0:4])


def nama_jenis(j):
    """Nama jenis untuk tampilan: event_type kosong ditulis 'Tanpa jenis' (sama dengan legenda keluarga)."""
    return "Tanpa jenis" if j == "(kosong)" else j


def batang_h(ax, y, lebar, tinggi, warna, r_pt=2.5, min_pt=1.0):
    """Batang mendatar berupa SATU bentuk: ujung data membulat (jari-jari r_pt poin), pangkal di sumbu tegak.
    Satu bentuk saja supaya tidak ada garis sambungan; lebar minimal min_pt poin agar baris kecil tetap bertanda."""
    fig = ax.figure
    pos = ax.get_position()
    x0, x1 = ax.get_xlim()
    y0, y1 = ax.get_ylim()
    upp_x = (x1 - x0) / (pos.width * fig.get_figwidth() * 72.0)       # satuan data per poin
    upp_y = abs(y1 - y0) / (pos.height * fig.get_figheight() * 72.0)
    lebar = max(lebar, min_pt * upp_x)
    rx, ry, h2, k = r_pt * upp_x, r_pt * upp_y, tinggi / 2.0, 0.5523
    if lebar < 2 * rx:
        ax.add_patch(mpatches.Rectangle((0, y - h2), lebar, tinggi, facecolor=warna, edgecolor="none", lw=0))
        return
    titik = [(0, y - h2), (lebar - rx, y - h2), (lebar - rx + k * rx, y - h2), (lebar, y - h2 + ry - k * ry),
             (lebar, y - h2 + ry), (lebar, y + h2 - ry), (lebar, y + h2 - ry + k * ry),
             (lebar - rx + k * rx, y + h2), (lebar - rx, y + h2), (0, y + h2), (0, y - h2)]
    kode = [MPath.MOVETO, MPath.LINETO, MPath.CURVE4, MPath.CURVE4, MPath.CURVE4, MPath.LINETO, MPath.CURVE4,
            MPath.CURVE4, MPath.CURVE4, MPath.LINETO, MPath.CLOSEPOLY]
    ax.add_patch(mpatches.PathPatch(MPath(titik, kode), facecolor=warna, edgecolor="none", lw=0))


def legenda_keluarga(ax, ada, **kw):
    """Legenda jenis kejadian; latar putih menutup garis kisi yang lewat di belakangnya."""
    h = [mpatches.Patch(facecolor=WARNA[k], edgecolor="none", label=NAMA_KELUARGA[k]) for k in KELUARGA if k in ada]
    return ax.legend(handles=h, frameon=True, facecolor=SURF, edgecolor="none", framealpha=1.0, fontsize=6.8,
                     labelcolor=INK2, handlelength=1.0, handleheight=1.0, handletextpad=0.5, borderaxespad=0.0,
                     borderpad=0.3, **kw)


# ------------------------------------------------------------------ G1: tahun x jenis (peta panas)
def g1_tahun_jenis(sumber, keluar, dpi):
    baris = baca(sumber, "a1_tahun_jenis")
    jenis = sorted({r["jenis"] for r in baris}, key=lambda j: -sum(int(r["n"]) for r in baris if r["jenis"] == j))
    tahun = sorted({int(r["tahun"]) for r in baris if r["tahun"]})
    kolom = [str(t) for t in tahun] + ["tanpa\ntanggal"]
    nilai = {}
    for r in baris:
        nilai[(r["jenis"], int(r["tahun"]) if r["tahun"] else None)] = int(r["n"])
    vmax = max(nilai.values())
    fig = plt.figure(figsize=(LEBAR_IN, 3.1))
    ax = fig.add_axes([0.235, 0.27, 0.745, 0.60])
    nb, nk = len(jenis), len(kolom)
    ax.set_xlim(0, nk)
    ax.set_ylim(nb, 0)
    for i, j in enumerate(jenis):
        for k, th in enumerate(tahun + [None]):
            v = nilai.get((j, th))
            if v is None:
                continue
            c = mcolors.to_hex(CMAP(math.log10(v) / math.log10(vmax)))
            ax.add_patch(mpatches.Rectangle((k, i), 1, 1, facecolor=c, edgecolor=SURF, linewidth=1.8))
            ax.text(k + 0.5, i + 0.5, idn(v), ha="center", va="center", fontsize=7, color=teks_di_atas(c))
    ax.set_xticks([k + 0.5 for k in range(nk)])
    ax.set_xticklabels(kolom, fontsize=7, color=INK2)
    ax.xaxis.tick_top()
    ax.set_yticks([i + 0.5 for i in range(nb)])
    ax.set_yticklabels(["%s (%s)" % (nama_jenis(j), idn(sum(v for (jj, _), v in nilai.items() if jj == j))) for j in jenis],
                       fontsize=7, color=INK2)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.tick_params(length=0)
    # skala warna (logaritma): satu hue, terang = sedikit
    cb = fig.add_axes([0.235, 0.135, 0.38, 0.028])
    cb.imshow(np.linspace(0, 1, 256)[None, :], aspect="auto", cmap=CMAP, extent=[0, 1, 0, 1])
    ticks = [v for v in (1, 10, 100, 1000, 10000) if v <= vmax]
    cb.set_xticks([math.log10(v) / math.log10(vmax) for v in ticks])
    cb.set_xticklabels([idn(v) for v in ticks], fontsize=6.8, color=INK2)
    cb.set_yticks([])
    cb.tick_params(length=2, width=0.6, color=BASE)
    for s in cb.spines.values():
        s.set_visible(False)
    fig.text(0.635, 0.149, "anotasi per sel (skala log)", fontsize=6.8, color=INK2, ha="left", va="center")
    catatan = "Sel kosong = tidak ada anotasi. Angka dalam kurung = total per jenis."
    if "(kosong)" in jenis:
        catatan += " Tanpa jenis = event_type kosong."
    fig.text(0.02, 0.03, catatan, fontsize=6.8, color=MUTED, ha="left")
    simpan(fig, os.path.join(keluar, "g1_tahun_jenis.png"), dpi)


# ------------------------------------------------------------------ G2: anotasi per lokasi (batang berperingkat)
def g2_lokasi(sumber, keluar, dpi):
    mentah = baca(sumber, "a3_lokasi")
    per = {}                                   # lokasi -> [jumlah, {jenis: jumlah}]
    for r in mentah:
        g = per.setdefault(r["lokasi"], [0, {}])
        g[0] += int(r["n"])
        g[1][r["jenis"]] = g[1].get(r["jenis"], 0) + int(r["n"])
    total = sum(g[0] for g in per.values())
    baris = sorted(((lok, g[0], max(g[1], key=g[1].get)) for lok, g in per.items()), key=lambda x: (-x[1], x[0]))
    tanggal = dict((r["lokasi"], r) for r in baca(sumber, "a3b_lokasi_tanggal"))
    n = len(baris)
    fig = plt.figure(figsize=(LEBAR_IN, 4.1))
    ax = fig.add_axes([0.20, 0.10, 0.64, 0.815])
    ax.set_xlim(0, baris[0][1] * 1.34)
    ax.set_ylim(n - 0.4, -0.6)
    gaya(ax, kisi=None, spines=("bottom",))      # tiap batang sudah bertuliskan nilainya: tanpa garis kisi
    ax.set_yticks(range(n))
    ax.set_yticklabels([b[0] for b in baris], fontsize=7, color=INK2)
    ax.tick_params(axis="y", length=0)
    ax.set_xticks([0, 10000, 20000, 30000, 40000, 50000])
    ax.set_xticklabels([idn(v) for v in (0, 10000, 20000, 30000, 40000, 50000)], fontsize=7)
    ax.set_xlabel("Jumlah anotasi (poligon longsor)", fontsize=7.2, labelpad=3)
    ax.text(1.04, 1.012, "tanggal\nkejadian", transform=ax.transAxes, ha="left", va="bottom", fontsize=6.8, color=MUTED)
    for i, (lok, v, jenis) in enumerate(baris):
        batang_h(ax, i, v, 0.62, WARNA[KEL_JENIS[jenis]])
        persen = 100.0 * v / total
        ax.text(v + ax.get_xlim()[1] * 0.012, i, "%s  (%s)" % (idn(v), "<0,1%" if persen < 0.1 else idn(persen, 1) + "%"),
                va="center", ha="left", fontsize=6.8, color=INK2)
        d = tanggal.get(lok)
        if d is not None:
            teks = tgl(d["tanggal_awal"]) if int(d["n_tanggal"]) == 1 else "%s tanggal" % idn(int(d["n_tanggal"]))
            ax.text(1.04, i, teks, transform=ax.get_yaxis_transform(), ha="left", va="center", fontsize=6.8, color=INK2)
    ada = {KEL_JENIS[b[2]] for b in baris}
    legenda_keluarga(ax, ada, loc="lower right", bbox_to_anchor=(1.0, 0.02))
    dua = baris[0][1] + baris[1][1]
    tunggal = all(b[0] in tanggal and int(tanggal[b[0]]["n_tanggal"]) == 1 for b in baris[:2])
    ax.text(ax.get_xlim()[1], n * 0.50, "%s dan %s = %s%% dari semua anotasi%s" % (
        baris[0][0], baris[1][0], idn(100.0 * dua / total, 1),
        ",\nmasing-masing dari satu hari kejadian saja." if tunggal else "."),
        ha="right", va="center", fontsize=6.8, color=INK2,
        bbox=dict(facecolor=SURF, edgecolor="none", pad=2.0))
    simpan(fig, os.path.join(keluar, "g2_lokasi.png"), dpi)


# ------------------------------------------------------------------ G3: bulan per belahan bumi
def g3_bulan(sumber, keluar, dpi):
    baris = baca(sumber, "a2_bulan_hemisfer")
    hari = baca(sumber, "a8_hari_terpadat")
    fig, axs = plt.subplots(2, 1, figsize=(LEBAR_IN, 4.7), sharex=True)
    fig.subplots_adjust(left=0.115, right=0.985, top=0.86, bottom=0.07, hspace=0.30)
    ada, jumlah_bulan, panel = set(), {}, {}
    for ax, hem, judul in ((axs[0], "utara", "Belahan utara (lintang pusat >= 0)"),
                           (axs[1], "selatan", "Belahan selatan (lintang pusat < 0)")):
        tumpuk = {k: [0] * 12 for k in KELUARGA}
        for r in baris:
            if r["hemisfer"] == hem and r["bulan"]:
                tumpuk[KEL_JENIS[r["jenis"]]][int(r["bulan"]) - 1] += int(r["n"])
        tot = [sum(tumpuk[k][m] for k in KELUARGA) for m in range(12)]
        jumlah_bulan[hem], panel[hem] = tot, ax
        gaya(ax, kisi="y", spines=("left", "bottom"))
        bawah = [0] * 12
        for k in KELUARGA:
            if not any(tumpuk[k]):
                continue
            ada.add(k)
            ax.bar(range(12), tumpuk[k], bottom=bawah, width=0.58, color=WARNA[k], edgecolor=SURF, linewidth=1.0)
            bawah = [a + b for a, b in zip(bawah, tumpuk[k])]
        ymax = max(tot)
        ax.set_ylim(0, ymax * 1.18)
        ax.set_xlim(-0.6, 11.6)
        ax.set_xticks(range(12))
        ax.set_xticklabels(BULAN, fontsize=7, color=INK2)
        ax.tick_params(axis="x", length=0)
        ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: idn(v)))
        ax.set_ylabel("anotasi", fontsize=7.2)
        ax.set_title(judul, loc="left", fontsize=7.6, color=INK, pad=4)
        for m in sorted(range(12), key=lambda m: -tot[m])[:2]:
            ax.text(m, tot[m] + ymax * 0.02, idn(tot[m]), ha="center", va="bottom", fontsize=6.8, color=INK2,
                    bbox=ETIKET)
        tanpa = sum(int(r["n"]) for r in baris if r["hemisfer"] == hem and not r["bulan"])
        # catatan di baris judul panel (di luar bidang gambar), supaya tidak bertabrakan dengan garis kisi atau batang
        ax.annotate("%s anotasi tanpa tanggal tidak tampil" % idn(tanpa), xy=(1, 1), xycoords="axes fraction",
                    xytext=(0, 4), textcoords="offset points", ha="right", va="baseline", fontsize=6.5, color=MUTED)
    fig.legend(handles=[mpatches.Patch(facecolor=WARNA[k], edgecolor="none", label=NAMA_KELUARGA[k])
                        for k in KELUARGA if k in ada],
               loc="upper left", bbox_to_anchor=(0.115, 0.995), ncol=2, columnspacing=1.2, frameon=False,
               fontsize=6.8, labelcolor=INK2, handlelength=1.0, handleheight=1.0, handletextpad=0.5, borderaxespad=0.0)
    # tiga hari dengan anotasi terbanyak (tabel a8) ditandai pada bulan dan belahan buminya; belahan dipilih bila
    # hanya satu belahan yang jumlah bulannya cukup memuat hari itu
    for r in hari[:3]:
        bulan, n_hari = int(r["event_date"][5:7]) - 1, int(r["n"])
        cocok = [h for h in ("utara", "selatan") if jumlah_bulan[h][bulan] >= n_hari]
        if len(cocok) != 1:
            continue
        ax, tot = panel[cocok[0]], jumlah_bulan[cocok[0]]
        ymax = max(tot)
        teks = "%s\n%s anotasi dari %s lokasi" % (tgl(r["event_date"]), idn(n_hari), r["n_lokasi"])
        if tot[bulan] >= 0.5 * ymax:
            ax.text(bulan + 0.5, ymax * 0.80, teks, ha="left", va="center", fontsize=6.8, color=INK2, bbox=ETIKET)
        else:
            ax.text(bulan, tot[bulan] + ymax * 0.11, teks, ha="center", va="bottom", fontsize=6.8, color=INK2,
                    bbox=ETIKET)
    simpan(fig, os.path.join(keluar, "g3_bulan.png"), dpi)


# ------------------------------------------------------------------ G4: sebaran luas poligon per jenis
def g4_luas(sumber, keluar, dpi):
    baris = baca(sumber, "a4a_area_jenis")
    baris.sort(key=lambda r: float(r["p50"]))
    n = len(baris)
    fig = plt.figure(figsize=(LEBAR_IN, 2.85))
    ax = fig.add_axes([0.255, 0.238, 0.715, 0.72])
    ax.set_xscale("log")
    ax.set_xlim(10 ** 1.5, 10 ** 6.7)
    ax.set_ylim(n - 0.4, -0.6)
    gaya(ax, kisi="x", spines=("bottom",))
    ax.set_yticks(range(n))
    ax.set_yticklabels(["%s  (n = %s)" % (nama_jenis(r["jenis"]), idn(int(r["n"]))) for r in baris], fontsize=7, color=INK2)
    ax.tick_params(axis="y", length=0)
    ax.set_xticks([10 ** e for e in range(2, 7)])
    ax.set_xticklabels([idn(10 ** e) for e in range(2, 7)], fontsize=7)
    ax.xaxis.set_minor_locator(matplotlib.ticker.NullLocator())
    ax.set_xlabel("Luas poligon (satuan kolom area di sumber; skala log)", fontsize=7.2, labelpad=3)
    for i, r in enumerate(baris):
        c = WARNA[KEL_JENIS[r["jenis"]]]
        p05, p25, p50, p75, p95 = (float(r[k]) for k in ("p05", "p25", "p50", "p75", "p95"))
        ax.plot([p05, p95], [i, i], color=c, linewidth=1.6, solid_capstyle="round", zorder=3)
        ax.add_patch(mpatches.Rectangle((p25, i - 0.26), p75 - p25, 0.52, facecolor=c, edgecolor="none", zorder=4))
        ax.plot([p50, p50], [i - 0.26, i + 0.26], color=SURF, linewidth=1.8, zorder=5, solid_capstyle="butt")
        ax.text(p95 * 1.18, i, "median %s" % idn(p50), va="center", ha="left", fontsize=6.8, color=INK2, bbox=ETIKET)
    ada_kosong = any(r["jenis"] == "(kosong)" for r in baris)
    fig.text(0.02, 0.078 if ada_kosong else 0.03,
             "Garis = persentil 5 sampai 95, kotak = persentil 25 sampai 75, garis putih = median.",
             fontsize=6.8, color=MUTED, ha="left")
    if ada_kosong:
        fig.text(0.02, 0.028, "Tanpa jenis = event_type kosong.", fontsize=6.8, color=MUTED, ha="left")
    simpan(fig, os.path.join(keluar, "g4_luas.png"), dpi)


# ------------------------------------------------------------------ G5: kualitas anotasi (confidence dan selang citra)
def g5_kualitas(sumber, keluar, dpi):
    baris = baca(sumber, "a7_waktu_kualitas")
    urut = ["Rainfall", "Hurricane", "Tropical Storm", "Cyclone", "Earthquake", "(kosong)"]
    d = dict((r["jenis"], r) for r in baris)
    urut = [j for j in urut if j in d]
    n = len(urut)
    fig = plt.figure(figsize=(LEBAR_IN, 2.9))
    a = fig.add_axes([0.285, 0.21, 0.255, 0.60])
    b = fig.add_axes([0.60, 0.21, 0.225, 0.60])
    for ax in (a, b):
        ax.set_ylim(n - 0.4, -0.6)
        gaya(ax, kisi="x", spines=("bottom",))
        ax.tick_params(axis="y", length=0)
    a.set_yticks(range(n))
    a.set_yticklabels(["%s  (n = %s)" % (nama_jenis(j), idn(int(d[j]["n"]))) for j in urut], fontsize=7, color=INK2)
    b.set_yticks([])
    # (a) persentase anotasi dengan event_conf = 1
    a.set_xlim(0, 128)
    a.set_xticks([0, 50, 100])                 # tiap batang sudah bertuliskan nilainya; tiga tanda cukup dan tidak berdesakan
    a.set_xticklabels(["0%", "50%", "100%"], fontsize=6.8)
    a.set_title("Anotasi dengan\nconfidence tepat 1,0", loc="left", fontsize=7.6, pad=5)
    for i, j in enumerate(urut):
        pct = 100.0 * int(d[j]["n_conf_1"]) / int(d[j]["n"])
        batang_h(a, i, pct, 0.56, WARNA[KEL_JENIS[j]], r_pt=2.5)
        a.text(pct + 2.5, i, "%s%%" % idn(pct, 1), va="center", ha="left", fontsize=6.8, color=INK2, bbox=ETIKET)
    # (b) selang citra sebelum kejadian: median (titik), sampai persentil 95 (garis), maksimum (silang)
    b.set_xlim(0, 640)
    b.set_xticks([0, 200, 400, 600])
    b.set_xticklabels(["0", "200", "400", "600"], fontsize=6.8)
    b.set_title("Selang citra sebelum\nkejadian (hari)", loc="left", fontsize=7.6, pad=5)
    b.text(1.05, 1.012, "med / p95 / maks", transform=b.transAxes, ha="left", va="bottom", fontsize=6.5, color=MUTED)
    for i, j in enumerate(urut):
        c = WARNA[KEL_JENIS[j]]
        p50, p95, mx = float(d[j]["selang_pra_p50"]), float(d[j]["selang_pra_p95"]), float(d[j]["selang_pra_maks"])
        b.plot([p50, p95], [i, i], color=c, linewidth=1.6, solid_capstyle="round", zorder=3)
        b.plot([p50], [i], marker="o", markersize=5.0, markerfacecolor=c, markeredgecolor=SURF, markeredgewidth=1.2, zorder=4)
        b.plot([mx], [i], marker="x", markersize=4.2, color=INK2, markeredgewidth=0.9, zorder=3)
        b.text(1.05, i, "%s / %s / %s" % (idn(p50), idn(p95), idn(mx)), transform=b.get_yaxis_transform(),
               va="center", ha="left", fontsize=6.8, color=INK2)
    tetap = [j for j in urut
             if float(d[j]["selang_pra_p50"]) == float(d[j]["selang_pra_p95"]) == float(d[j]["selang_pra_maks"])]
    catatan = "Titik = median, garis = sampai persentil 95, silang = maksimum."
    if "(kosong)" in urut:
        catatan += " Tanpa jenis = event_type kosong."
    fig.text(0.02, 0.078, catatan, fontsize=6.8, color=MUTED, ha="left")
    if tetap:
        fig.text(0.02, 0.032, "%s: selangnya sama (%s hari) pada semua anotasi." % (
            ", ".join(nama_jenis(j) for j in tetap), idn(float(d[tetap[0]]["selang_pra_maks"]))),
            fontsize=6.8, color=MUTED, ha="left")
    simpan(fig, os.path.join(keluar, "g5_kualitas.png"), dpi)


# ------------------------------------------------------------------ G6: waktu pemrosesan vs ukuran data
def g6_waktu(sumber_waktu, keluar, dpi):
    jalur = os.path.join(sumber_waktu, "ringkasan_waktu.csv")
    if not os.path.exists(jalur):
        print("  lewati g6_waktu: %s belum ada (jalankan analitik/ringkas_waktu.py)" % jalur)
        return
    with open(jalur, encoding="utf-8", newline="") as f:
        baris = [r for r in csv.DictReader(f) if r["mode"] == "etl"]
    if len(baris) < 2:
        print("  lewati g6_waktu: butuh minimal dua skala (ada %d)" % len(baris))
        return
    baris.sort(key=lambda r: float(r["n_anotasi"]))
    x = [float(r["n_anotasi"]) for r in baris]
    y = [float(r["total_ms"]) / 1000.0 for r in baris]
    dingin = [float(r["total_cold_ms"]) / 1000.0 if r["total_cold_ms"] else None for r in baris]
    ada_dingin = all(v is not None for v in dingin) and any(r["dasar"] == "warm" for r in baris)
    acuan = [y[0] * xi / x[0] for xi in x]                    # bila waktu naik sebanding dengan data
    fig = plt.figure(figsize=(LEBAR_IN, 3.3))
    ax = fig.add_axes([0.115, 0.26, 0.865, 0.70])
    ax.set_xscale("log")
    ax.set_yscale("log")
    gaya(ax, kisi="both", spines=("left", "bottom"))
    semua = y + acuan + (dingin if ada_dingin else [])
    ax.set_xlim(x[0] / 1.7, x[-1] * 3.6)
    ax.set_ylim(min(y) / 2.5, max(semua) * 1.5)
    ax.xaxis.set_minor_locator(matplotlib.ticker.NullLocator())
    ax.yaxis.set_minor_locator(matplotlib.ticker.NullLocator())
    # acuan skala linier dari titik pertama (proyeksi, bukan data: garis putus-putus berlabel)
    ax.plot(x, acuan, color=MUTED, linewidth=1.0, linestyle=(0, (4, 3)), zorder=2)
    ax.text(x[-1] / 1.25, acuan[-1], "acuan: waktu naik sebanding dengan data", ha="right", va="center", fontsize=6.8,
            color=MUTED, bbox=dict(facecolor=SURF, edgecolor="none", pad=1.5))
    ax.plot(x, y, color=UNGU, linewidth=2.0, solid_capstyle="round", zorder=3)
    for xi, yi, r in zip(x, y, baris):
        ax.plot([xi], [yi], marker="o", markersize=7, markerfacecolor=UNGU, markeredgecolor=SURF, markeredgewidth=1.6, zorder=4)
        ax.annotate("%s detik" % idn(yi, 1 if yi < 100 else 0), (xi, yi), xytext=(8, -3), textcoords="offset points",
                    fontsize=7, color=INK2, ha="left", va="top", bbox=ETIKET)
    if ada_dingin:
        ax.plot(x, dingin, color=UNGU, linewidth=1.0, zorder=2, alpha=0.55)
        for xi, vi in zip(x, dingin):
            ax.plot([xi], [vi], marker="o", markersize=6, markerfacecolor=SURF, markeredgecolor=UNGU, markeredgewidth=1.4, zorder=4)
        ax.legend(handles=[Line2D([0], [0], marker="o", color=UNGU, markerfacecolor=UNGU, markeredgecolor=SURF,
                                  markersize=6, linewidth=2.0, label="putaran warm (median)"),
                           Line2D([0], [0], marker="o", color=UNGU, markerfacecolor=SURF, markeredgecolor=UNGU,
                                  markersize=5.5, linewidth=1.0, alpha=0.9, label="putaran cold (pertama)")],
                  loc="lower right", frameon=True, facecolor=SURF, edgecolor="none", framealpha=1.0, fontsize=6.8,
                  labelcolor=INK2, borderaxespad=0.4)
    ax.set_xticks(x)
    ax.set_xticklabels(["%s\n%s anotasi" % (r["skala"], idn(float(r["n_anotasi"]))) for r in baris], fontsize=7, color=INK2)
    ax.set_ylabel("Waktu satu putaran penuh (detik, skala log)", fontsize=7.2)
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: idn(v)))
    fig.text(0.02, 0.03, "Satu putaran = ETL + 14 kueri analitik + ekspor CSV. Kedua sumbu berskala log.",
             fontsize=6.8, color=MUTED, ha="left")
    simpan(fig, os.path.join(keluar, "g6_waktu.png"), dpi)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Buat grafik hasil analitik (PNG).")
    ap.add_argument("--sumber", help="folder tabel CSV (bawaan results/analitik/S1, lalu analitik/referensi_S1)")
    ap.add_argument("--keluar", default=str(AKAR / "results" / "analitik" / "grafik"))
    ap.add_argument("--waktu", default=str(AKAR / "results" / "analitik"), help="folder ringkasan_waktu.csv")
    ap.add_argument("--dpi", type=int, default=300)
    args = ap.parse_args(argv)
    sumber = args.sumber
    if not sumber:
        for kandidat in (AKAR / "results" / "analitik" / "S1", AKAR / "analitik" / "referensi_S1"):
            if (kandidat / "a1_tahun_jenis.csv").exists():
                sumber = str(kandidat)
                break
    if not sumber:
        raise SystemExit("Tabel analitik belum ada. Jalankan spark_pipeline.py (atau referensi.py --skala S1) dulu.")
    print("Sumber tabel :", sumber)
    for f in (g1_tahun_jenis, g2_lokasi, g3_bulan, g4_luas, g5_kualitas):
        f(sumber, args.keluar, args.dpi)
    g6_waktu(args.waktu, args.keluar, args.dpi)
    return 0


if __name__ == "__main__":
    sys.exit(main())
