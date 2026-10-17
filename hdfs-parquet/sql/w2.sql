-- W2: jumlah anotasi yang TITIK PUSATNYA ada di jendela +-0,01 derajat di sekitar titik uji
-- (contoh: titik 11.4548681, 43.7734078).
-- REFERENSI: teks ini persis yang dijalankan hdfs-parquet/run_sql.py (dibuat oleh bench/kueri.py).
-- Tabel (view) annotations dibaca dari Parquet di HDFS; jendela digeser setengah langkah dari kisi data.
SELECT count(*) AS n FROM annotations WHERE center_lon BETWEEN 11.44486805 AND 11.46486815 AND center_lat BETWEEN 43.76340775 AND 43.78340785;
