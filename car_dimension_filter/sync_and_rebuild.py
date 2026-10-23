import sqlite3
import json
import csv
import re
import os
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 1. 从权威 catalog 映射加载真实名称与停售状态
catalog_info = {}
with open("car_dimension_filter/data/brands_series_catalog.csv", "r", encoding="utf-8") as f:
    for r in csv.reader(f):
        if len(r) >= 2:
            match = re.search(r'series_(\d+)', r[1])
            if match:
                sid = int(match.group(1))
                raw_name = r[0].strip()
                is_stopped = "停售" in raw_name
                clean_name = re.sub(r'\(停售\)|（停售）|\s*\(\d+\)', '', raw_name).strip()
                catalog_info[sid] = {
                    "is_stopped": is_stopped,
                    "clean_name": clean_name
                }

# 2. 从数据库读取
conn = sqlite3.connect("car_dimension_filter/data/cars.db")
cur = conn.cursor()
cur.execute("SELECT * FROM vehicles")
cols = [d[0] for d in cur.description]
vehicles = [dict(zip(cols, r)) for r in cur.fetchall()]
conn.close()

normalized_cars = []
for v in vehicles:
    sid = v["series_id"]
    clean_series = catalog_info.get(sid, {}).get("clean_name", v["series"])
    normalized_cars.append({
        "spec_id": v["spec_id"],
        "series_id": sid,
        "brand": v["brand"],
        "series": clean_series,
        "model_name": v["model_name"],
        "level": v["level"],
        "energy_type": v["energy_type"],
        "body_structure": v["body_structure"],
        "length": v["length_mm"],
        "width": v["width_mm"],
        "height": v["height_mm"],
        "wheelbase": v["wheelbase_mm"],
        "weight": v["curb_weight_kg"],
        "price": v["price"]
    })

with open("car_dimension_filter/data/cars.json", "w", encoding="utf-8") as f:
    json.dump(normalized_cars, f, ensure_ascii=False, indent=2)

from fetch_cars import aggregate_by_series
from clean_and_enrich_data import infer_brand, normalize_energy, normalize_level

series_list = aggregate_by_series(normalized_cars)

stopped_count = 0
for s in series_list:
    sid = s["series_id"]
    info = catalog_info.get(sid, {})
    is_stopped = info.get("is_stopped", False)
    clean_name = info.get("clean_name", s["series"])
    if is_stopped:
        stopped_count += 1
    
    s["is_stopped"] = is_stopped
    s["clean_series_name"] = clean_name
    
    models_sample = [v.get("model_name", "") for v in s.get("versions", [])]
    s["brand"] = infer_brand(clean_name, models_sample)
    s["energy_categories"] = normalize_energy(s.get("energy_types", []))
    s["clean_level"] = normalize_level(s.get("level", ""))

with open("car_dimension_filter/data/series.json", "w", encoding="utf-8") as f:
    json.dump(series_list, f, ensure_ascii=False, indent=2)

print(f"数据全量权威对齐完成！总车型: {len(normalized_cars)}，总车系: {len(series_list)}（在售: {len(series_list) - stopped_count}，停售: {stopped_count}）")

# 重新编译 HTML
import subprocess
subprocess.run([sys.executable, "car_dimension_filter/build_html.py"], check=True)
print("index.html 页面已成功更新！")
