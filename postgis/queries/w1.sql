-- W1: ambil satu anotasi menurut ann_id (bawaan 0).
--   docker exec sen12ls-postgis psql -U postgres -d sen12ls -f /sql/queries/w1.sql
-- Anotasi lain:       tambahkan  -v ann=100  sebelum -f.
-- Rencana kueri:      tambahkan  -v explain=1  (menampilkan EXPLAIN ANALYZE setelah hasil).
\if :{?ann}
\else
  \set ann 0
\endif
SELECT ann_id, location, event_type, event_date FROM annotations WHERE ann_id = :ann;
\if :{?explain}
EXPLAIN (ANALYZE, BUFFERS) SELECT ann_id FROM annotations WHERE ann_id = :ann;
\endif
