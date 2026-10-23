# -*- coding: utf-8 -*-
import json
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

data = json.load(open("car_dimension_filter/data/series_enriched_cache.json", encoding="utf-8"))
print(f"Total Enriched in cache: {len(data)}")

scores = [v['score'] for v in data.values() if v.get('score')]
print(f"Has score: {len(scores)}, max: {max(scores) if scores else None}, min: {min(scores) if scores else None}")

drive_types = {}
for v in data.values():
    for sub in v.get('versions', {}).values():
        d = sub.get('drive_type')
        if d:
            drive_types[d] = drive_types.get(d, 0) + 1
print("Drive distribution:", drive_types)

ratios = []
for v in data.values():
    for sub in v.get('versions', {}).values():
        r = sub.get('pwr_ratio')
        if r:
            ratios.append(r)
print(f"Has power-to-weight ratio: {len(ratios)}, max: {max(ratios) if ratios else None}, avg: {round(sum(ratios)/len(ratios), 1) if ratios else None}")
