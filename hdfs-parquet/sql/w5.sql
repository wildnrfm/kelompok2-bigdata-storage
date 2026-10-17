-- W5: jumlah anotasi per event_type dan tahun kejadian (agregasi seluruh tabel).
-- REFERENSI: teks ini persis yang dijalankan hdfs-parquet/run_sql.py (dibuat oleh bench/kueri.py).
-- Tabel (view) annotations dibaca dari Parquet di HDFS; jendela digeser setengah langkah dari kisi data.
SELECT event_type, year(event_date) AS tahun, count(*) AS n FROM annotations GROUP BY event_type, year(event_date);
