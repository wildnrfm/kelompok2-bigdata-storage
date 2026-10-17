-- W1: ambil satu anotasi menurut ann_id (contoh: ann_id 0).
-- REFERENSI: teks ini persis yang dijalankan hdfs-parquet/run_sql.py (dibuat oleh bench/kueri.py).
-- Tabel (view) annotations dibaca dari Parquet di HDFS; jendela digeser setengah langkah dari kisi data.
SELECT ann_id, location, event_type, event_date FROM annotations WHERE ann_id = 0;
