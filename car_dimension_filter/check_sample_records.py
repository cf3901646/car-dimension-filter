import json
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

with open('car_dimension_filter/data/series.json', 'r', encoding='utf-8') as f:
    series = json.load(f)

with open('car_dimension_filter/data/series_covers.json', 'r', encoding='utf-8') as f:
    covers = json.load(f)

with open('car_dimension_filter/data/series_enriched_cache.json', 'r', encoding='utf-8') as f:
    cache = json.load(f)

s_map = {str(s['series_id']): s for s in series}

test_ids = ['6962', '2569', '634', '162', '5989', '7698']
for tid in test_ids:
    s = s_map.get(tid)
    c = covers.get(tid)
    ech = cache.get(tid, {})
    if s:
        print(f"=== ID: {tid} ===")
        print("Brand:", s.get("brand"), "| Series:", s.get("series"), "| Display:", s.get("display_series_name"))
        print("Cover in covers.json:", bool(c), "| Sample URL:", str(c)[:45] if c else None)
        print("Drive types:", s.get("drive_types"), "| Max HP:", s.get("max_horsepower"), "| Ratio:", s.get("pwr_ratio_str"))
        print("Versions count in series:", len(s.get("versions", [])))
        print("Versions count in cache:", len(ech.get("versions", {})))
        print("Score:", s.get("score") or ech.get("score"))
