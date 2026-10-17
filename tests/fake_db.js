globalThis.db = { getSiblingDB: () => ({ annotations: {}, patches: {} }) };
globalThis.print = console.log;
const fs = require("fs");
const src = fs.readFileSync(process.argv[2], "utf8");
(0, eval)(src);
const [lon, lat, half] = [Number(process.argv[3]), Number(process.argv[4]), Number(process.argv[5])];
const w = jendela(lon, lat, half);
console.log(JSON.stringify({ w, ring: cincin(w) }));
