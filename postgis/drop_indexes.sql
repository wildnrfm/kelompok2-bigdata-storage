-- Hapus indeks buatan (kunci utama tetap). Dipakai untuk eksperimen E1: ukur W2-W4 tanpa indeks.
--   docker exec sen12ls-postgis psql -U postgres -d sen12ls -f /sql/drop_indexes.sql
-- Bangun lagi dengan indexes.sql.
\set ON_ERROR_STOP on
DROP INDEX IF EXISTS ann_center_gist;
DROP INDEX IF EXISTS ann_bbox_gist;
DROP INDEX IF EXISTS ann_event_date;
DROP INDEX IF EXISTS ann_type_date;
DROP INDEX IF EXISTS ann_location_date;
DROP INDEX IF EXISTS pat_inventory_split;
SELECT tablename, indexname FROM pg_indexes WHERE schemaname = 'public' ORDER BY 1, 2;
