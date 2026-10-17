// W5: jumlah anotasi per event_type dan tahun kejadian (agregasi seluruh koleksi).
//   docker exec sen12ls-mongo mongosh --quiet --file /scripts/queries/w5.js
load("/scripts/queries/_umum.js");
const pipa = [
  { $group: { _id: { event_type: "$event_type", tahun: { $year: "$dates.event" } }, n: { $sum: 1 } } },
  { $sort: { "_id.event_type": 1, "_id.tahun": 1 } },
];
const mulai = Date.now();
const hasil = ANN.aggregate(pipa).toArray();
print("W5: " + hasil.length + " kelompok (event_type x tahun), " + (Date.now() - mulai) + " ms");
hasil.slice(0, 10).forEach(r => print("  " + JSON.stringify(r)));
