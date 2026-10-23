# -*- coding: utf-8 -*-
import sqlite3, sys, json
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

conn = sqlite3.connect('car_dimension_filter/data/cars.db')
cur = conn.cursor()
cur.execute('SELECT series_id, brand, series, model_name FROM vehicles WHERE series_id IN (2569, 6962) LIMIT 10')
for row in cur.fetchall():
    print('DB vehicle:', row)

cur.execute('SELECT series_id, brand, series FROM series WHERE series_id IN (2569, 6962)')
for row in cur.fetchall():
    print('DB series:', row)

# 查 clean_and_enrich_data.py 是怎么清洗的
with open("car_dimension_filter/clean_and_enrich_data.py", "r", encoding="utf-8") as f:
    code = f.read()
print("clean_and_enrich_data.py length:", len(code))
