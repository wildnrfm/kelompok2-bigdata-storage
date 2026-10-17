// W3: seperti W2, dan tanggal kejadian dalam +-30 hari dari tanggal anotasi ANN_ID.
//   docker exec sen12ls-mongo mongosh --quiet --file /scripts/queries/w3.js
load("/scripts/queries/_umum.js");
const ANN_ID = 0;                       // ubah untuk titik lain (harus punya tanggal kejadian)
const t = titikDari(ANN_ID);
if (!t.tanggal) throw new Error("Anotasi " + ANN_ID + " tidak punya tanggal kejadian; pilih ANN_ID lain.");
const w = jendela(t.lon, t.lat, 0.01);
const filter = {
  center: { $geoWithin: { $geometry: poligon(w) } },
  "dates.event": { $gte: hariGeser(t.tanggal, -30), $lte: hariGeser(t.tanggal, 30) },
};
print("Titik uji: (" + t.lon + ", " + t.lat + "), tanggal " + t.tanggal.toISOString().slice(0, 10));
print("W3: " + ANN.countDocuments(filter) + " anotasi");
print("Rencana kueri:");
ringkasPlan(ANN.find(filter).explain("executionStats"));
