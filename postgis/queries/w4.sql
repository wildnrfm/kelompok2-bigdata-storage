-- W4: jumlah anotasi yang KOTAK PEMBATASNYA beririsan dengan jendela +-0,1 derajat (sekitar 22 km),
-- event_type sama dengan anotasi :ann (Rainfall bila kosong), dan event_conf >= 0,9.
--   docker exec sen12ls-postgis psql -U postgres -d sen12ls -f /sql/queries/w4.sql
-- Anotasi lain:       tambahkan  -v ann=100  sebelum -f  (bawaan 0).
-- Rencana kueri:      tambahkan  -v explain=1.
\if :{?ann}
\else
  \set ann 0
\endif
\set half 0.1
SELECT round(ST_X(center)::numeric - :half, 7) - 0.00000005 AS x0,
       round(ST_Y(center)::numeric - :half, 7) - 0.00000005 AS y0,
       round(ST_X(center)::numeric + :half, 7) + 0.00000005 AS x1,
       round(ST_Y(center)::numeric + :half, 7) + 0.00000005 AS y1,
       coalesce(event_type, 'Rainfall') AS et
FROM annotations WHERE ann_id = :ann \gset
\if :{?x0}
\else
  \echo 'Anotasi tidak ditemukan. Pilih ann_id lain, mis. -v ann=100'
  \quit
\endif
SELECT count(*) AS w4 FROM annotations
WHERE ST_Intersects(bbox, ST_MakeEnvelope(:x0, :y0, :x1, :y1, 4326))
  AND event_type = :'et' AND event_conf >= 0.9;
\if :{?explain}
EXPLAIN (ANALYZE, BUFFERS) SELECT count(*) FROM annotations
WHERE ST_Intersects(bbox, ST_MakeEnvelope(:x0, :y0, :x1, :y1, 4326))
  AND event_type = :'et' AND event_conf >= 0.9;
\endif
