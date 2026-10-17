# Pustaka tiruan untuk uji tanpa Docker

Folder ini berisi versi sangat sederhana dari `pymongo`, `psycopg`, dan `pyspark` yang dipakai
`tests/uji_semua.py` supaya seluruh kode (harness, pemuat, pembanding) bisa dijalankan di laptop
tanpa Docker. Mesin tiruannya Python biasa dan SQLite, jadi:

- Yang diuji: alur kode, nama kolom, parameter, definisi kueri W1 sampai W6, dan kesesuaian
  jumlah hasil dengan wasit `bench/kebenaran.py`.
- Yang TIDAK diuji: perilaku asli MongoDB, PostGIS, HDFS, dan Spark (indeks, kecepatan, bola
  versus bidang datar). Itu hanya bisa dibuktikan dengan menjalankan Docker sungguhan.

Jangan menaruh folder ini di PYTHONPATH saat uji sungguhan.
