import csv
import json
import re
import sys
import sqlite3

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

# 1. 加载权威的 catalog 映射
catalog_map = {}
with open("car_dimension_filter/data/brands_series_catalog.csv", "r", encoding="utf-8") as f:
    for r in csv.reader(f):
        if len(r) >= 2:
            match = re.search(r'series_(\d+)', r[1])
            if match:
                sid = int(match.group(1))
                raw_name = r[0].strip()
                catalog_map[sid] = raw_name

print(f"权威车系目录已加载: {len(catalog_map)} 条")

# 2. 检查并修正 series.json
with open("car_dimension_filter/data/series.json", "r", encoding="utf-8") as f:
    series_list = json.load(f)

from clean_and_enrich_data import infer_brand, normalize_energy, normalize_level

fixed_count = 0
for s in series_list:
    sid = s.get("series_id")
    if sid in catalog_map:
        cat_name_raw = catalog_map[sid]
        clean_name = re.sub(r'\s*\(\d+\)$', '', cat_name_raw).strip()
        is_stopped = "停售" in cat_name_raw
        clean_no_stop = re.sub(r'\(停售\)|（停售）|\s*\(\d+\)', '', clean_name).strip()

        if s.get("series") != clean_name:
            print(f"修正车系名 [SID {sid}]: '{s.get('series')}' -> '{clean_name}'")
            s["series"] = clean_name
            fixed_count += 1

        s["is_stopped"] = is_stopped
        s["clean_series_name"] = clean_no_stop

        # 重新推断品牌
        models_sample = [v.get("model_name", "") for v in s.get("versions", [])]
        s["brand"] = infer_brand(clean_no_stop, models_sample)
        s["energy_categories"] = normalize_energy(s.get("energy_types", []))
        s["clean_level"] = normalize_level(s.get("level", ""))

with open("car_dimension_filter/data/series.json", "w", encoding="utf-8") as f:
    json.dump(series_list, f, ensure_ascii=False, indent=2)

print(f"\n修正完成！共修正 {fixed_count} 个错误车系名称。")

# 3. 同步修复 SQLite 数据库 cars.db
conn = sqlite3.connect("car_dimension_filter/data/cars.db")
cur = conn.cursor()

# 更新 series 表
for s in series_list:
    cur.execute('''
    UPDATE series SET series = ?, brand = ? WHERE series_id = ?
    ''', (s["clean_series_name"], s["brand"], s["series_id"]))

    cur.execute('''
    UPDATE vehicles SET series = ?, brand = ? WHERE series_id = ?
    ''', (s["clean_series_name"], s["brand"], s["series_id"]))

conn.commit()
conn.close()
print("cars.db 数据库同步更新完成！")
