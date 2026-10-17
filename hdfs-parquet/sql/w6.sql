-- W6: jumlah patch per inventory dan split, plus rata-rata pixel_annotated.
-- REFERENSI: teks ini persis yang dijalankan hdfs-parquet/run_sql.py (dibuat oleh bench/kueri.py).
-- Tabel (view) patches dibaca dari Parquet di HDFS; jendela digeser setengah langkah dari kisi data.
SELECT inventory, split, count(*) AS n, round(avg(pixel_annotated), 1) AS rata_piksel FROM patches GROUP BY inventory, split;
