// W2: jumlah anotasi yang TITIK PUSATNYA ada di jendela +-0,01 derajat (sekitar 1,1 km)
// di sekitar pusat anotasi ANN_ID.
//   docker exec sen12ls-mongo mongosh --quiet --file /scripts/queries/w2.js
load("/scripts/queries/_umum.js");
const ANN_ID = 0;                       // ubah untuk titik lain
const t = titikDari(ANN_ID);
const w = jendela(t.lon, t.lat, 0.01);
const filter = { center: { $geoWithin: { $geometry: poligon(w) } } };
print("Titik uji: (" + t.lon + ", " + t.lat + "), lokasi " + t.lokasi);
print("W2: " + ANN.countDocuments(filter) + " anotasi");
print("Rencana kueri:");
ringkasPlan(ANN.find(filter).explain("executionStats"));
