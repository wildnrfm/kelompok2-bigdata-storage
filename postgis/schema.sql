-- Tabel annotations dan patches (tanpa indeks spasial; indeks dibangun SETELAH muat di indexes.sql).
-- Perintah (PowerShell, dari mana saja):
--   docker exec sen12ls-postgis psql -U postgres -d sen12ls -f /sql/schema.sql
-- PERHATIAN: tabel lama beserta isinya dihapus dulu. Aman diulang.
-- Bentuk poligon TIDAK disimpan: tiap anotasi diwakili titik pusat (center) dan kotak pembatas (bbox).
CREATE EXTENSION IF NOT EXISTS postgis;

DROP TABLE IF EXISTS annotations;
DROP TABLE IF EXISTS patches;

CREATE TABLE annotations (
    ann_id      bigint PRIMARY KEY,
    location    text NOT NULL,
    inventory   text,
    event_type  text,
    type        text,
    velocity_c  text,
    author      text,
    reference   text,
    event_conf  double precision,
    area        double precision,
    pre_date    date,
    event_date  date,
    post_date   date,
    pre_dt2     date,
    event_dt2   date,
    post_dt2    date,
    center      geometry(Point, 4326) NOT NULL,
    bbox        geometry(Polygon, 4326) NOT NULL,
    sim_batch   smallint NOT NULL DEFAULT 0
);

CREATE TABLE patches (
    patch_id        text PRIMARY KEY,
    split           text NOT NULL,
    inventory       text NOT NULL,
    s2_path         text,
    s1asc_path      text,
    s1dsc_path      text,
    pixel_annotated integer,
    sim_batch       smallint NOT NULL DEFAULT 0
);
