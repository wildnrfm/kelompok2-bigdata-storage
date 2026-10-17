-- Muat annotations.csv dan patches.csv dari satu folder lewat tabel sementara (stage).
-- Perintah (PowerShell; tulis dalam SATU baris). 'folder' = jalur DI DALAM kontainer:
--   docker exec sen12ls-postgis psql -U postgres -d sen12ls -v folder=/sen12ls-data/out/s1 -f /sql/load.sql
-- S10: -v folder=/sen12ls-data/out/s10 ; S100: -v folder=/sen12ls-data/out/s100
-- Tambah batch baru TANPA mengosongkan (beban kerja W8):
--   ... -v folder=/sen12ls-data/out/batch100 -v tambah=1 -f /sql/load.sql
-- Tanpa -v tambah=1, tabel annotations dan patches dikosongkan dulu, jadi aman diulang.
-- Waktu tiap langkah tercetak (\timing). Untuk W7, jalankan perintah ini DI BELAKANG
--   python bench\catat.py ukur --store postgis --skala S1 --jenis muat --objek annotations+patches <perintah di atas>
-- supaya total waktunya tercatat otomatis (lihat baca-dulu/KONTRAK.md bagian 6).
\set ON_ERROR_STOP on
\if :{?folder}
\else
  \echo 'Isi dulu: -v folder=/sen12ls-data/out/s1'
  \quit
\endif
\set ann_csv :folder '/annotations.csv'
\set pat_csv :folder '/patches.csv'
\timing on

DROP TABLE IF EXISTS annotations_stage;
CREATE UNLOGGED TABLE annotations_stage (
    ann_id bigint, location text, inventory text, event_type text, type text, velocity_c text,
    author text, reference text, event_conf double precision, area double precision,
    pre_date date, event_date date, post_date date, pre_dt2 date, event_dt2 date, post_dt2 date,
    center_lon double precision, center_lat double precision,
    bbox_min_lon double precision, bbox_min_lat double precision,
    bbox_max_lon double precision, bbox_max_lat double precision,
    sim_batch smallint
);
COPY annotations_stage FROM :'ann_csv' WITH (FORMAT csv, HEADER true);

DROP TABLE IF EXISTS patches_stage;
CREATE UNLOGGED TABLE patches_stage (
    patch_id text, split text, inventory text, s2_path text, s1asc_path text, s1dsc_path text,
    pixel_annotated integer, sim_batch smallint
);
COPY patches_stage FROM :'pat_csv' WITH (FORMAT csv, HEADER true);

\if :{?tambah}
\else
  TRUNCATE annotations, patches;
\endif

INSERT INTO annotations (ann_id, location, inventory, event_type, type, velocity_c, author, reference,
                         event_conf, area, pre_date, event_date, post_date, pre_dt2, event_dt2, post_dt2,
                         center, bbox, sim_batch)
SELECT ann_id, location, inventory, event_type, type, velocity_c, author, reference,
       event_conf, area, pre_date, event_date, post_date, pre_dt2, event_dt2, post_dt2,
       ST_SetSRID(ST_MakePoint(center_lon, center_lat), 4326),
       ST_MakeEnvelope(bbox_min_lon, bbox_min_lat, bbox_max_lon, bbox_max_lat, 4326),
       sim_batch
FROM annotations_stage;

INSERT INTO patches (patch_id, split, inventory, s2_path, s1asc_path, s1dsc_path, pixel_annotated, sim_batch)
SELECT patch_id, split, inventory, s2_path, s1asc_path, s1dsc_path, pixel_annotated, sim_batch
FROM patches_stage;

DROP TABLE annotations_stage;
DROP TABLE patches_stage;
SELECT (SELECT count(*) FROM annotations) AS jumlah_annotations,
       (SELECT count(*) FROM patches) AS jumlah_patches;
