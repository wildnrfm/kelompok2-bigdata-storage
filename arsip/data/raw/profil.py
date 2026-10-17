import json, collections as C, datetime as dt

d = json.load(open('sen12tp-metadata.json', encoding='utf-8'))
f = d['features']
p = [x['properties'] for x in f]
cnt = lambda k: C.Counter(q.get(k) for q in p)

print('jumlah scene (feature):', len(f))
print('area unik (spatial_id):', len({q.get('spatial_id') for q in p}))
print('scene_id unik:', len({q.get('scene_id') for q in p}))
print('tipe geometri:', dict(C.Counter(x['geometry']['type'] for x in f)))
print('variasi susunan properti:', len({tuple(sorted(q)) for q in p}))
print('nilai kosong:', sum(v is None for q in p for v in q.values()))
print('split:', dict(cnt('split')))
print('bulan:', sorted(cnt('month').items()))
print('tutupan lahan:', cnt('landcover').most_common())
print('iklim:', cnt('climate').most_common())

ts = [q['s2_timestamp_ms'] for q in p if q.get('s2_timestamp_ms')]
u = dt.timezone.utc
print('rentang s2:', dt.datetime.fromtimestamp(min(ts) / 1000, u), 'sampai', dt.datetime.fromtimestamp(max(ts) / 1000, u))

pts = [c for x in f if x['geometry']['type'] == 'Polygon' for c in x['geometry']['coordinates'][0]]
print('lon:', min(c[0] for c in pts), max(c[0] for c in pts), '| lat:', min(c[1] for c in pts), max(c[1] for c in pts))