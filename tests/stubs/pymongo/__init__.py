"""Tiruan pymongo: satu database dalam memori, hanya operasi yang dipakai bench/ dan mongodb/.

Geometri dihitung PERSEGI di bidang datar (sama seperti rancangan jendela di bench/kueri.py).
"""
import copy

_TOKO = {}          # nama koleksi -> daftar dokumen (satu database 'sen12ls' saja)


def kosongkan():
    _TOKO.clear()


def _nilai(doc, jalur):
    for k in jalur.split("."):
        if not isinstance(doc, dict) or k not in doc:
            return None
        doc = doc[k]
    return doc


def _persegi(cincin):
    xs = [p[0] for p in cincin]
    ys = [p[1] for p in cincin]
    return min(xs), min(ys), max(xs), max(ys)


def _cocok(doc, filt):
    for kunci, syarat in filt.items():
        v = _nilai(doc, kunci)
        if isinstance(syarat, dict) and "$geoWithin" in syarat:
            x0, y0, x1, y1 = _persegi(syarat["$geoWithin"]["$geometry"]["coordinates"][0])
            if v is None:
                return False
            lon, lat = v["coordinates"]
            if not (x0 <= lon <= x1 and y0 <= lat <= y1):
                return False
        elif isinstance(syarat, dict) and "$geoIntersects" in syarat:
            wx0, wy0, wx1, wy1 = _persegi(syarat["$geoIntersects"]["$geometry"]["coordinates"][0])
            if v is None:
                return False
            bx0, by0, bx1, by1 = _persegi(v["coordinates"][0])
            if not (bx0 <= wx1 and bx1 >= wx0 and by0 <= wy1 and by1 >= wy0):
                return False
        elif isinstance(syarat, dict) and ("$gte" in syarat or "$lte" in syarat):
            if v is None:
                return False
            if "$gte" in syarat and not v >= syarat["$gte"]:
                return False
            if "$lte" in syarat and not v <= syarat["$lte"]:
                return False
        else:
            if v != syarat:
                return False
    return True


def _proyeksi(doc, proj):
    if not proj:
        return copy.deepcopy(doc)
    hasil = {"_id": doc["_id"]}
    for jalur in proj:
        v = _nilai(doc, jalur)
        if v is not None:
            hasil[jalur] = v
    return hasil


class _Koleksi:
    def __init__(self, nama):
        self.nama = nama

    @property
    def _dok(self):
        return _TOKO.setdefault(self.nama, [])

    def drop(self):
        _TOKO.pop(self.nama, None)

    def insert_many(self, docs, ordered=True):
        self._dok.extend(docs)

    def estimated_document_count(self):
        return len(self._dok)

    def count_documents(self, filt):
        return sum(1 for d in self._dok if _cocok(d, filt))

    def find(self, filt=None, proyeksi=None):
        return [_proyeksi(d, proyeksi) for d in self._dok if _cocok(d, filt or {})]

    def aggregate(self, pipa):
        grup = pipa[0]["$group"]
        kunci = grup["_id"]
        cnt = {}
        for d in self._dok:
            k = []
            for nama, ekspr in kunci.items():
                if isinstance(ekspr, dict) and "$year" in ekspr:
                    t = _nilai(d, ekspr["$year"][1:])
                    k.append((nama, t.year if t is not None else None))
                else:
                    k.append((nama, _nilai(d, ekspr[1:])))
            c = cnt.setdefault(tuple(k), {"n": 0, "px": [], "n_px": 0})
            c["n"] += 1
            if "rata_piksel" in grup:
                v = _nilai(d, grup["rata_piksel"]["$avg"][1:])
                if v is not None:
                    c["px"].append(v)
        hasil = []
        for k, c in cnt.items():
            r = {"_id": dict(k), "n": c["n"]}
            if "rata_piksel" in grup:
                r["rata_piksel"] = sum(c["px"]) / len(c["px"]) if c["px"] else None
            hasil.append(r)
        return hasil


class _Db:
    def command(self, nama):
        return {"ok": 1}

    def __getitem__(self, nama):
        return _Koleksi(nama)


class MongoClient:
    def __init__(self, uri=None, **kw):
        self.uri = uri

    def __getitem__(self, nama):
        return _Db()

    def close(self):
        pass
