// Hapus SEMUA indeks buatan (kecuali _id). Dipakai untuk eksperimen E1: ukur W2-W4 tanpa indeks.
//   docker exec sen12ls-mongo mongosh --quiet --file /scripts/drop_indexes.js
// Bangun lagi dengan indexes.js.
const d = db.getSiblingDB("sen12ls");
for (const nama of ["annotations", "patches"]) {
  const r = d.getCollection(nama).dropIndexes("*");
  print("Indeks " + nama + " dihapus (sisa: _id saja): " + JSON.stringify(r.ok !== undefined ? { ok: r.ok } : r));
}
