# -*- coding: utf-8 -*-
import json, sys
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

series_list = json.load(open("car_dimension_filter/data/series.json", encoding="utf-8"))
cache = json.load(open("car_dimension_filter/data/series_enriched_cache.json", encoding="utf-8"))

for s in series_list:
    if s.get("series_id") in [5964, 448]:
        print(f"Series in series.json: {s.get('series_id')} {s.get('series')}")
        print("  pwr_ratio_str:", s.get("pwr_ratio_str"))
        print("  pwr_ratio_min:", s.get("pwr_ratio_min"))
        print("  versions count:", len(s.get("versions", [])))
        if s.get("versions"):
            v0 = s["versions"][0]
            print("  v0:", v0.get("model_name"), "spec_id:", v0.get("spec_id"), "pwr_ratio:", v0.get("pwr_ratio"), "hp:", v0.get("horsepower"), "weight:", v0.get("weight"))

c_5964 = cache.get("5964")
if c_5964:
    print("\nCache for 5964:")
    print("  score:", c_5964.get("score"))
    print("  versions keys:", list(c_5964.get("versions", {}).keys())[:5])
    for k, v in list(c_5964.get("versions", {}).items())[:2]:
        print(f"    {k}: {v}")
