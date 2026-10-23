# -*- coding: utf-8 -*-
import json
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

series = json.load(open("car_dimension_filter/data/series.json", encoding="utf-8"))
covers = json.load(open("car_dimension_filter/data/series_covers.json", encoding="utf-8")) if True else {}

print(f"Total series: {len(series)}")

for s in series:
    s_str = json.dumps(s, ensure_ascii=False)
    if "SU7" in s_str or "星锐" in s_str or "小米" in s_str:
        sid = s.get("series_id")
        brand = s.get("brand")
        brand_name = s.get("brand_name")
        ser = s.get("series")
        clean = s.get("clean_series_name")
        print(f"ID: {sid} | brand: {brand} | brand_name: {brand_name} | series: {ser} | clean: {clean}")
        print(f"  cover in covers.json: {covers.get(str(sid))}")
        if s.get("versions"):
            print(f"  version 0: {s['versions'][0].get('model_name')}")
            print(f"  version count: {len(s['versions'])}")
