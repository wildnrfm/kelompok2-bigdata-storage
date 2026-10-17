-- W3: seperti W2, dan event_date antara date_from dan date_to (titik uji +-30 hari).
-- Contoh: 15 Feb 2019 sampai 16 Apr 2019.
-- REFERENSI: teks ini persis yang dijalankan hdfs-parquet/run_sql.py (dibuat oleh bench/kueri.py).
-- Tabel (view) annotations dibaca dari Parquet di HDFS; jendela digeser setengah langkah dari kisi data.
SELECT count(*) AS n FROM annotations WHERE center_lon BETWEEN 11.44486805 AND 11.46486815 AND center_lat BETWEEN 43.76340775 AND 43.78340785 AND event_date BETWEEN DATE '2019-02-15' AND DATE '2019-04-16';
