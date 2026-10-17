// W6: jumlah patch per inventory dan split, plus rata-rata pixel_annotated.
//   docker exec sen12ls-mongo mongosh --quiet --file /scripts/queries/w6.js
load("/scripts/queries/_umum.js");
const pipa = [
  { $group: { _id: { inventory: "$inventory", split: "$split" }, n: { $sum: 1 },
              rata_piksel: { $avg: "$pixel_annotated" } } },
  { $sort: { "_id.inventory": 1, "_id.split": 1 } },
];
const mulai = Date.now();
const hasil = PAT.aggregate(pipa).toArray();
print("W6: " + hasil.length + " kelompok (inventory x split), " + (Date.now() - mulai) + " ms");
hasil.slice(0, 10).forEach(r => print("  " + JSON.stringify(r)));
