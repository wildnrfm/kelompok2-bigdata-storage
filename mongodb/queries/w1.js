// W1: ambil satu anotasi menurut ann_id (= _id).
//   docker exec sen12ls-mongo mongosh --quiet --file /scripts/queries/w1.js
load("/scripts/queries/_umum.js");
const ANN_ID = 0;                       // ubah untuk anotasi lain
const hasil = ANN.find({ _id: ANN_ID }, { location: 1, event_type: 1, "dates.event": 1 }).toArray();
print("W1: " + hasil.length + " dokumen");
printjson(hasil);
print("Rencana kueri:");
ringkasPlan(ANN.find({ _id: ANN_ID }).explain("executionStats"));
