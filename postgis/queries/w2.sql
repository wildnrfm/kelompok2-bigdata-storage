-- W2: jumlah anotasi yang TITIK PUSATNYA ada di jendela +-0,01 derajat (sekitar 1,1 km)
-- di sekitar pusat anotasi :ann. Jendela dihitung sama dengan bench/kueri.py.
--   docker exec sen12ls-postgis psql -U postgres -d sen12ls -f /sql/queries/w2.sql
-- Anotasi lain:       tambahkan  -v ann=100  sebelum -f  (bawaan 0).
-- Rencana kueri:      tambahkan  -v explain=1  (apakah indeks GiST dipakai? lihat baris "Index Scan" atau "Bitmap").
\if :{?ann}
\else
  \set ann 0
\endif
\set half 0.01
SELECT round(ST_X(center)::numeric - :half, 7) - 0.00000005 AS x0,
       round(ST_Y(center)::numeric - :half, 7) - 0.00000005 AS y0,
       round(ST_X(center)::numeric + :half, 7) + 0.00000005 AS x1,
       round(ST_Y(center)::numeric + :half, 7) + 0.00000005 AS y1
FROM annotations WHERE ann_id = :ann \gset
\if :{?x0}
\else
  \echo 'Anotasi tidak ditemukan. Pilih ann_id lain, mis. -v ann=100'
  \quit
\endif
SELECT count(*) AS w2 FROM annotations
WHERE ST_Intersects(center, ST_MakeEnvelope(:x0, :y0, :x1, :y1, 4326));
\if :{?explain}
EXPLAIN (ANALYZE, BUFFERS) SELECT count(*) FROM annotations
WHERE ST_Intersects(center, ST_MakeEnvelope(:x0, :y0, :x1, :y1, 4326));
\endif
