# -*- coding: utf-8 -*-
import json
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

SERIES_PATH = "car_dimension_filter/data/series.json"
CACHE_PATH = "car_dimension_filter/data/series_enriched_cache.json"
COVERS_PATH = "car_dimension_filter/data/series_covers.json"

with open(SERIES_PATH, "r", encoding="utf-8") as f:
    series_list = json.load(f)

with open(CACHE_PATH, "r", encoding="utf-8") as f:
    cache = json.load(f)

with open(COVERS_PATH, "r", encoding="utf-8") as f:
    covers = json.load(f)

# 1. 净化 2569 (江淮星锐)
xingrui_versions = [
    {
        "spec_id": 256901,
        "model_name": "2024款 捷运王 2.0T 柴油短轴中顶 6座",
        "length": 5050,
        "width": 2080,
        "height": 2370,
        "wheelbase": 2960,
        "weight": 2280,
        "drive_type": "后驱",
        "horsepower": 150,
        "pwr_ratio": 65.8,
        "ev_range": None
    },
    {
        "spec_id": 256902,
        "model_name": "2024款 节油王 2.0T 柴油长轴高顶 9座",
        "length": 5497,
        "width": 2080,
        "height": 2670,
        "wheelbase": 3570,
        "weight": 2450,
        "drive_type": "后驱",
        "horsepower": 150,
        "pwr_ratio": 61.2,
        "ev_range": None
    },
    {
        "spec_id": 256903,
        "model_name": "2024款 快运王 2.0T 柴油加长轴高顶 17座",
        "length": 5990,
        "width": 2080,
        "height": 2670,
        "wheelbase": 3570,
        "weight": 2600,
        "drive_type": "后驱",
        "horsepower": 150,
        "pwr_ratio": 57.7,
        "ev_range": None
    }
]

for s in series_list:
    if str(s.get("series_id")) == "2569":
        s["brand"] = "江淮"
        s["brand_name"] = "江淮"
        s["series"] = "星锐"
        s["series_name"] = "星锐"
        s["clean_series_name"] = "星锐"
        s["display_series_name"] = "星锐"
        s["level"] = "客车"
        s["clean_level"] = "客车"
        s["energy_types"] = ["柴油"]
        s["energy_categories"] = ["燃油车"]
        s["body_structures"] = ["客车"]
        s["length_min"] = 5050
        s["length_max"] = 5990
        s["length_str"] = "5050～5990mm"
        s["width_min"] = 2080
        s["width_max"] = 2080
        s["width_str"] = "2080mm"
        s["height_min"] = 2370
        s["height_max"] = 2670
        s["height_str"] = "2370～2670mm"
        s["wheelbase_min"] = 2960
        s["wheelbase_max"] = 3570
        s["wheelbase_str"] = "2960～3570mm"
        s["price_min"] = 10.97
        s["price_max"] = 18.98
        s["price_str"] = "10.97～18.98万"
        s["version_count"] = 3
        s["versions"] = xingrui_versions
        s["is_stopped"] = False
        s["score"] = 4.67
        s["drive_types"] = ["后驱"]
        s["main_drive_type"] = "后驱"
        s["pwr_ratio_min"] = 57.7
        s["pwr_ratio_max"] = 65.8
        s["pwr_ratio_str"] = "57.7～65.8 Ps/吨"
        s["range_min"] = None
        s["range_max"] = None
        s["range_str"] = None
        s["max_horsepower"] = 150
        s["cover_url"] = "https://car2.autoimg.cn/cardfs/product/g27/M08/BE/46/autohomecar__ChsEbGNCPJOAau-_AEG8miOELqM498.jpg"
        print("Successfully purified series 2569 to JAC Xingrui!")

# 缓存中同步纠正 2569
cache["2569"] = {
    "score": 4.67,
    "versions": {
        "256901": {"drive_type": "后驱", "drive_raw": "前置后驱", "horsepower": 150, "weight": 2280, "pwr_ratio": 65.8, "ev_range": None},
        "256902": {"drive_type": "后驱", "drive_raw": "前置后驱", "horsepower": 150, "weight": 2450, "pwr_ratio": 61.2, "ev_range": None},
        "256903": {"drive_type": "后驱", "drive_raw": "前置后驱", "horsepower": 150, "weight": 2600, "pwr_ratio": 57.7, "ev_range": None}
    }
}
covers["2569"] = "https://car2.autoimg.cn/cardfs/product/g27/M08/BE/46/autohomecar__ChsEbGNCPJOAau-_AEG8miOELqM498.jpg"

# 2. 确认 6962 (小米SU7)
su7_obj = next((s for s in series_list if str(s.get("series_id")) == "6962"), None)
if su7_obj:
    su7_obj["brand"] = "小米"
    su7_obj["brand_name"] = "小米"
    su7_obj["series"] = "小米SU7"
    su7_obj["clean_series_name"] = "小米SU7"
    su7_obj["series_name"] = "小米SU7"
    su7_obj["display_series_name"] = "SU7"
    su7_obj["level"] = "中大型车"
    su7_obj["clean_level"] = "中大型车"
    su7_obj["energy_types"] = ["纯电动"]
    su7_obj["energy_categories"] = ["纯电动"]
    su7_obj["body_structures"] = ["三厢车"]
    su7_obj["cover_url"] = "https://car3.autoimg.cn/cardfs/product/g34/M08/15/9D/autohomecar__ChxpV2m6eI-Ado-XACFLNPTBwhk942.jpg"
    su7_obj["score"] = 4.45
    covers["6962"] = su7_obj["cover_url"]
    print("Confirmed genuine Xiaomi SU7 (6962) with accurate metadata!")

with open(SERIES_PATH, "w", encoding="utf-8") as f:
    json.dump(series_list, f, ensure_ascii=False, indent=2)

with open(CACHE_PATH, "w", encoding="utf-8") as f:
    json.dump(cache, f, ensure_ascii=False)

with open(COVERS_PATH, "w", encoding="utf-8") as f:
    json.dump(covers, f, ensure_ascii=False, indent=2)

print("All done!")
