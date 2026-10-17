-- Bangun indeks SETELAH data dimuat. Waktu tiap indeks tercetak (\timing). Untuk W7, jalankan DI BELAKANG
--   python bench\catat.py ukur --store postgis --skala S1 --jenis indeks --objek semua <perintah di bawah>
-- Perintah (PowerShell):
--   docker exec sen12ls-postgis psql -U postgres -d sen12ls -f /sql/indexes.sql
-- Aman diulang (IF NOT EXISTS). Untuk uji "tanpa indeks" (E1) pakai drop_indexes.sql.
\set ON_ERROR_STOP on
\timing on
-- Memori sementara lebih besar mempercepat pembangunan indeks GiST pada S100.
SET maintenance_work_mem = '256MB';
CREATE INDEX IF NOT EXISTS ann_center_gist ON annotations USING gist (center);
CREATE INDEX IF NOT EXISTS ann_bbox_gist ON annotations USING gist (bbox);
CREATE INDEX IF NOT EXISTS ann_event_date ON annotations (event_date);
CREATE INDEX IF NOT EXISTS ann_type_date ON annotations (event_type, event_date);
CREATE INDEX IF NOT EXISTS ann_location_date ON annotations (location, event_date);
CREATE INDEX IF NOT EXISTS pat_inventory_split ON patches (inventory, split);
VACUUM ANALYZE annotations;
VACUUM ANALYZE patches;

SELECT tablename, indexname, pg_size_pretty(pg_relation_size(indexname::regclass)) AS ukuran
FROM pg_indexes WHERE schemaname = 'public' ORDER BY tablename, indexname;
SELECT pg_size_pretty(pg_total_relation_size('annotations')) AS total_annotations,
       pg_size_pretty(pg_total_relation_size('patches')) AS total_patches;
