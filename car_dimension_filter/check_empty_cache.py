# -*- coding: utf-8 -*-
import json, sys
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

cache = json.load(open("car_dimension_filter/data/series_enriched_cache.json", encoding="utf-8"))
series_list = json.load(open("car_dimension_filter/data/series.json", encoding="utf-8"))

empty_cache_sids = []
for sid_str, data in cache.items():
    versions = data.get("versions", {})
    if not versions:
        empty_cache_sids.append(int(sid_str))

print(f"Total in cache: {len(cache)}, Empty versions in cache: {len(empty_cache_sids)}")

# 看看这其中有哪些是目前在售的热门车型
active_sids = {s["series_id"]: s for s in series_list if not s.get("is_stopped")}
empty_active = [active_sids[sid] for sid in empty_cache_sids if sid in active_sids]
print(f"Empty versions among ON-SALE series: {len(empty_active)}")
for s in empty_active[:20]:
    print(f"  SID {s['series_id']} | {s.get('brand')} {s.get('series')}")
