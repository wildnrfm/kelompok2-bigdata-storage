-- W4: jumlah anotasi yang KOTAK PEMBATASNYA beririsan dengan jendela +-0,1 derajat di sekitar titik uji,
-- event_type tertentu (contoh: Rainfall), dan event_conf >= 0,9.
-- REFERENSI: teks ini persis yang dijalankan hdfs-parquet/run_sql.py (dibuat oleh bench/kueri.py).
-- Tabel (view) annotations dibaca dari Parquet di HDFS; jendela digeser setengah langkah dari kisi data.
SELECT count(*) AS n FROM annotations WHERE bbox_min_lon <= 11.55486815 AND bbox_max_lon >= 11.35486805 AND bbox_min_lat <= 43.87340785 AND bbox_max_lat >= 43.67340775 AND event_type = 'Rainfall' AND event_conf >= 0.9;
