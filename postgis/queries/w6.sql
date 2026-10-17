-- W6: jumlah patch per inventory dan split, plus rata-rata pixel_annotated.
--   docker exec sen12ls-postgis psql -U postgres -d sen12ls -f /sql/queries/w6.sql
-- Rencana kueri: tambahkan  -v explain=1.
\timing on
SELECT inventory, split, count(*) AS n, round(avg(pixel_annotated), 1) AS rata_piksel
FROM patches GROUP BY 1, 2 ORDER BY 1, 2;
\if :{?explain}
EXPLAIN (ANALYZE, BUFFERS) SELECT inventory, split, count(*) AS n, round(avg(pixel_annotated), 1) AS rata_piksel
FROM patches GROUP BY 1, 2 ORDER BY 1, 2;
\endif
