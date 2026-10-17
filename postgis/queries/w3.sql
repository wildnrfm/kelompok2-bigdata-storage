-- W3: seperti W2, dan tanggal kejadian dalam +-30 hari dari tanggal anotasi :ann.
--   docker exec sen12ls-postgis psql -U postgres -d sen12ls -f /sql/queries/w3.sql
-- Anotasi lain:       tambahkan  -v ann=100  sebelum -f  (bawaan 0). Harus punya event_date;
--                     bila tidak, skrip berhenti dengan pesan.
-- Rencana kueri:      tambahkan  -v explain=1.
\if :{?ann}
\else
  \set ann 0
\endif
\set half 0.01
SELECT round(ST_X(center)::numeric - :half, 7) - 0.00000005 AS x0,
       round(ST_Y(center)::numeric - :half, 7) - 0.00000005 AS y0,
       round(ST_X(center)::numeric + :half, 7) + 0.00000005 AS x1,
       round(ST_Y(center)::numeric + :half, 7) + 0.00000005 AS y1,
       event_date - 30 AS d1, event_date + 30 AS d2
FROM annotations WHERE ann_id = :ann \gset
\if :{?d1}
\else
  \echo 'Anotasi tidak ditemukan atau tidak punya event_date. Pilih ann_id lain, mis. -v ann=100'
  \quit
\endif
SELECT count(*) AS w3 FROM annotations
WHERE ST_Intersects(center, ST_MakeEnvelope(:x0, :y0, :x1, :y1, 4326))
  AND event_date BETWEEN :'d1'::date AND :'d2'::date;
\if :{?explain}
EXPLAIN (ANALYZE, BUFFERS) SELECT count(*) FROM annotations
WHERE ST_Intersects(center, ST_MakeEnvelope(:x0, :y0, :x1, :y1, 4326))
  AND event_date BETWEEN :'d1'::date AND :'d2'::date;
\endif
