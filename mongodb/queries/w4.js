// W4: jumlah anotasi yang KOTAK PEMBATASNYA beririsan dengan jendela +-0,1 derajat (sekitar 22 km),
// event_type sama dengan anotasi ANN_ID, dan event_conf >= 0,9.
//   docker exec sen12ls-mongo mongosh --quiet --file /scripts/queries/w4.js
load("/scripts/queries/_umum.js");
const ANN_ID = 0;                       // ubah untuk titik lain
const t = titikDari(ANN_ID);
const w = jendela(t.lon, t.lat, 0.1);
const filter = {
  bbox: { $geoIntersects: { $geometry: poligon(w) } },
  event_type: t.event_type,
  event_conf: { $gte: 0.9 },
};
print("Titik uji: (" + t.lon + ", " + t.lat + "), event_type " + t.event_type);
print("W4: " + ANN.countDocuments(filter) + " anotasi");
print("Rencana kueri:");
ringkasPlan(ANN.find(filter).explain("executionStats"));
