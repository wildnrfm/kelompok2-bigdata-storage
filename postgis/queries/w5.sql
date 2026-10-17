-- W5: jumlah anotasi per event_type dan tahun kejadian (agregasi seluruh tabel).
--   docker exec sen12ls-postgis psql -U postgres -d sen12ls -f /sql/queries/w5.sql
-- Rencana kueri: tambahkan  -v explain=1.
\timing on
SELECT event_type, EXTRACT(year FROM event_date)::int AS tahun, count(*) AS n
FROM annotations GROUP BY 1, 2 ORDER BY 1, 2;
\if :{?explain}
EXPLAIN (ANALYZE, BUFFERS) SELECT event_type, EXTRACT(year FROM event_date)::int AS tahun, count(*) AS n
FROM annotations GROUP BY 1, 2 ORDER BY 1, 2;
\endif
