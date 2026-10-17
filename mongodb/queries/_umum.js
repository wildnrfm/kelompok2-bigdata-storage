// Fungsi bersama untuk contoh kueri W1-W6. Dimuat oleh w1.js ... w6.js lewat load().
// Jendela dan cincin dihitung SAMA dengan bench/kueri.py (supaya contoh = isi harness).
// Memakai var dan function (bukan const) agar tetap terlihat oleh skrip yang memanggil load().
var DB = db.getSiblingDB("sen12ls");
var ANN = DB.annotations;
var PAT = DB.patches;

var bulat = (x, d) => Number(x.toFixed(d));

// Jendela persegi +-half derajat, batas digeser setengah langkah kisi (5e-8).
function jendela(lon, lat, half) {
  return [
    bulat(bulat(lon - half, 7) - 5e-8, 8), bulat(bulat(lat - half, 7) - 5e-8, 8),
    bulat(bulat(lon + half, 7) + 5e-8, 8), bulat(bulat(lat + half, 7) + 5e-8, 8),
  ];
}

function antara(a, b, langkah) {
  const n = Math.max(1, Math.ceil(Math.abs(b - a) / langkah));
  const hasil = [];
  for (let i = 0; i <= n; i++) hasil.push(bulat(a + (b - a) * i / n, 8));
  return hasil;
}

// Cincin GeoJSON berlawanan jarum jam; tepi dipadatkan tiap 0,005 derajat.
function cincin(w, langkah = 0.005) {
  const [x0, y0, x1, y1] = w;
  const c = antara(x0, x1, langkah).map(x => [x, y0]);
  antara(y0, y1, langkah).slice(1).forEach(y => c.push([x1, y]));
  antara(x1, x0, langkah).slice(1).forEach(x => c.push([x, y1]));
  antara(y1, y0, langkah).slice(1).forEach(y => c.push([x0, y]));
  return c;
}

var poligon = w => ({ type: "Polygon", coordinates: [cincin(w)] });

// Ringkasan rencana kueri: indeks apa yang dipakai dan berapa dokumen diperiksa.
function ringkasPlan(ex) {
  const teks = JSON.stringify(ex.queryPlanner.winningPlan);
  const tahap = [...new Set([...teks.matchAll(/"stage":"([A-Z_]+)"/g)].map(m => m[1]))];
  const indeks = [...new Set([...teks.matchAll(/"indexName":"([^"]+)"/g)].map(m => m[1]))];
  const s = ex.executionStats;
  print("  tahap rencana : " + tahap.join(" > "));
  print("  indeks dipakai: " + (indeks.length ? indeks.join(", ") : "TIDAK ADA (pindai seluruh koleksi)"));
  print("  dikembalikan " + s.nReturned + ", kunci diperiksa " + s.totalKeysExamined +
        ", dokumen diperiksa " + s.totalDocsExamined + ", " + s.executionTimeMillis + " ms");
}

// Titik uji dari anotasi nomor ANN_ID (pusat, tanggal, jenis kejadian).
function titikDari(annId) {
  const a = ANN.findOne({ _id: annId });
  if (!a) throw new Error("ann_id " + annId + " tidak ada. Sudah dimuat? Skala berapa?");
  const tgl = a.dates && a.dates.event ? a.dates.event : null;
  return {
    lon: a.center.coordinates[0], lat: a.center.coordinates[1],
    tanggal: tgl, event_type: a.event_type || "Rainfall", lokasi: a.location,
  };
}

function hariGeser(tgl, hari) {
  return new Date(tgl.getTime() + hari * 86400000);
}
