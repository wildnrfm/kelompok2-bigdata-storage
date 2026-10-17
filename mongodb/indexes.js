// Bangun indeks (jalankan SETELAH data dimuat). Waktu tiap indeks dicetak; catat total untuk W7:
//   docker exec sen12ls-mongo mongosh --quiet --file /scripts/indexes.js
// Aman diulang: indeks yang sudah ada dilewati oleh MongoDB.
const d = db.getSiblingDB("sen12ls");
const nAnn = d.annotations.estimatedDocumentCount();
const nPat = d.patches.estimatedDocumentCount();
print("Jumlah dokumen: annotations " + nAnn + ", patches " + nPat);
if (nAnn === 0) {
  print("PERINGATAN: koleksi annotations kosong. Muat data dulu (lihat panduan: mongoimport).");
}

const daftar = [
  { koleksi: "annotations", ket: "center 2dsphere (titik pusat)", kunci: { center: "2dsphere" } },
  { koleksi: "annotations", ket: "bbox 2dsphere (kotak pembatas)", kunci: { bbox: "2dsphere" } },
  { koleksi: "annotations", ket: "tanggal kejadian", kunci: { "dates.event": 1 } },
  { koleksi: "annotations", ket: "event_type + tanggal", kunci: { event_type: 1, "dates.event": 1 } },
  { koleksi: "annotations", ket: "location + tanggal", kunci: { location: 1, "dates.event": 1 } },
  { koleksi: "patches", ket: "inventory + split", kunci: { inventory: 1, split: 1 } },
];

let total = 0;
for (const item of daftar) {
  const mulai = Date.now();
  const nama = d.getCollection(item.koleksi).createIndex(item.kunci);
  const ms = Date.now() - mulai;
  total += ms;
  print("Indeks " + item.koleksi + "." + nama + " (" + item.ket + "): " + ms + " ms");
}
print("Total waktu bangun indeks: " + (total / 1000).toFixed(1) + " detik");
print("Indeks annotations:");
d.annotations.getIndexes().forEach(i => print("  " + i.name));
print("Indeks patches:");
d.patches.getIndexes().forEach(i => print("  " + i.name));
