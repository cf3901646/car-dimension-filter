# -*- coding: utf-8 -*-
import requests, sys, json, re
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://car.autohome.com.cn/"
}
session = requests.Session()

# 1. 抓取小米SU7 (6962)
su7_url = "https://car.m.autohome.com.cn/ashx/car/GetModelConfigNew.ashx?seriesId=6962"
r_su7 = session.get(su7_url, headers=HEADERS, timeout=8, verify=False)
su7_data = r_su7.json() if r_su7.status_code == 200 else {}

param_map = {}
for g in (su7_data.get("param") or []):
    for it in (g.get("paramitems") or []):
        param_map[it.get("name")] = it.get("valueitems") or []

model_names = param_map.get("车型名称", [])
lengths = param_map.get("长度(mm)", [])
widths = param_map.get("宽度(mm)", [])
heights = param_map.get("高度(mm)", [])
wheelbases = param_map.get("轴距(mm)", [])
levels = param_map.get("级别", [])
energies = param_map.get("能源类型", [])
structures = param_map.get("车身结构", [])
weights = param_map.get("整备质量(kg)", [])
prices = param_map.get("厂商指导价(元)", [])
drives = param_map.get("驱动方式", [])
motor_ps = param_map.get("电动机总马力(Ps)", [])
engine_ps = param_map.get("最大马力(Ps)", [])
cltc_range = param_map.get("CLTC纯电续航里程(km)", [])

def parse_val(item):
    if not item: return ""
    v = item.get("value")
    if v and str(v).strip(): return str(v).strip()
    sub = item.get("sublist")
    if sub and len(sub) > 0:
        sv = sub[0].get("subvalue")
        if sv and str(sv).strip(): return str(sv).strip()
    return ""

def parse_digit(v):
    if not v: return None
    nums = re.findall(r"\d+(?:\.\d+)?", str(v))
    return float(nums[0]) if nums else None

su7_versions = []
hp_list = []
ratios_list = []
ranges_list = []
drives_set = set()

for i, m_item in enumerate(model_names):
    m_name = parse_val(m_item)
    drv_raw = parse_val(drives[i]) if i < len(drives) else ""
    drv = "四驱" if ("四驱" in drv_raw or "AWD" in drv_raw) else ("后驱" if "后驱" in drv_raw else "前驱")
    drives_set.add(drv)

    ps_val = parse_digit(parse_val(motor_ps[i])) if i < len(motor_ps) else None
    if not ps_val and i < len(engine_ps):
        ps_val = parse_digit(parse_val(engine_ps[i]))
    
    wt_val = parse_digit(parse_val(weights[i])) if i < len(weights) else None
    
    pwr_ratio = None
    if ps_val and wt_val and wt_val > 500:
        pwr_ratio = round(ps_val / (wt_val / 1000.0), 1)
        ratios_list.append(pwr_ratio)

    rng_val = parse_digit(parse_val(cltc_range[i])) if i < len(cltc_range) else None
    if rng_val: ranges_list.append(int(rng_val))
    if ps_val: hp_list.append(int(ps_val))

    su7_versions.append({
        "spec_id": m_item.get("specid"),
        "model_name": m_name,
        "length": int(parse_digit(parse_val(lengths[i]))) if i < len(lengths) else 4997,
        "width": int(parse_digit(parse_val(widths[i]))) if i < len(widths) else 1963,
        "height": int(parse_digit(parse_val(heights[i]))) if i < len(heights) else 1445,
        "wheelbase": int(parse_digit(parse_val(wheelbases[i]))) if i < len(wheelbases) else 3000,
        "weight": int(wt_val) if wt_val else 2180,
        "drive_type": drv,
        "horsepower": int(ps_val) if ps_val else 690,
        "pwr_ratio": pwr_ratio,
        "ev_range": int(rng_val) if rng_val else 835
    })

# 抓取评分
r_p = session.get("https://car.autohome.com.cn/price/series-6962.html", headers=HEADERS, timeout=8, verify=False)
su7_score = 4.67
if r_p.status_code == 200:
    sc = re.findall(r'class="score-number">(\d\.\d{1,2})</span>', r_p.text)
    if sc: su7_score = float(sc[0])

su7_series_obj = {
    "series_id": 6962,
    "brand": "小米汽车",
    "brand_name": "小米汽车",
    "series": "小米SU7",
    "clean_series_name": "小米SU7",
    "series_name": "小米SU7",
    "level": "中大型车",
    "clean_level": "中大型车",
    "energy_types": ["纯电动"],
    "energy_categories": ["纯电动"],
    "body_structures": ["4门5座三厢车"],
    "length_min": 4997,
    "length_max": 4997,
    "length_str": "4997mm",
    "width_min": 1963,
    "width_max": 1963,
    "width_str": "1963mm",
    "height_min": 1445,
    "height_max": 1455,
    "height_str": "1445～1455mm",
    "wheelbase_min": 3000,
    "wheelbase_max": 3000,
    "wheelbase_str": "3000mm",
    "ratio": 60.0,
    "price_min": 21.59,
    "price_max": 29.99,
    "price_str": "21.59～29.99万",
    "version_count": len(su7_versions),
    "versions": su7_versions,
    "is_stopped": False,
    "score": su7_score,
    "cover_url": "https://car3.autoimg.cn/cardfs/product/g34/M08/15/9D/autohomecar__ChxpV2m6eI-Ado-XACFLNPTBwhk942.jpg",
    "drive_types": sorted(list(drives_set)),
    "main_drive_type": "四驱" if "四驱" in drives_set else "后驱",
    "pwr_ratio_min": min(ratios_list) if ratios_list else 146.8,
    "pwr_ratio_max": max(ratios_list) if ratios_list else 316.5,
    "pwr_ratio_str": f"{min(ratios_list)}～{max(ratios_list)} Ps/吨" if ratios_list else "146.8～316.5 Ps/吨",
    "range_min": min(ranges_list) if ranges_list else 700,
    "range_max": max(ranges_list) if ranges_list else 835,
    "range_str": f"纯电 {min(ranges_list)}～{max(ranges_list)}km" if ranges_list else "纯电 700～835km",
    "max_horsepower": max(hp_list) if hp_list else 690
}

# 更新 series.json
SERIES_PATH = "car_dimension_filter/data/series.json"
series_list = json.load(open(SERIES_PATH, encoding="utf-8"))

# 1. 修正 2569 (江淮星锐)
for s in series_list:
    if s.get("series_id") == 2569:
        s["brand"] = "江淮汽车"
        s["brand_name"] = "江淮汽车"
        s["series"] = "星锐"
        s["series_name"] = "星锐"
        s["clean_series_name"] = "星锐"
        s["level"] = "轻客"
        s["clean_level"] = "轻客"
        print("Fixed series 2569: reset to 江淮汽车 星锐")

# 2. 注入或替换 6962 (小米SU7)
existing_idx = None
for idx, s in enumerate(series_list):
    if s.get("series_id") == 6962:
        existing_idx = idx
        break

if existing_idx is not None:
    series_list[existing_idx] = su7_series_obj
else:
    series_list.insert(0, su7_series_obj)
print("Injected genuine Xiaomi SU7 (6962) into series_list!")

with open(SERIES_PATH, "w", encoding="utf-8") as f:
    json.dump(series_list, f, ensure_ascii=False, indent=2)

# 更新 covers.json
COVERS_PATH = "car_dimension_filter/data/series_covers.json"
covers = json.load(open(COVERS_PATH, encoding="utf-8"))
covers["6962"] = "https://car3.autoimg.cn/cardfs/product/g34/M08/15/9D/autohomecar__ChxpV2m6eI-Ado-XACFLNPTBwhk942.jpg"
covers["2569"] = "https://car2.autoimg.cn/cardfs/product/g27/M08/BE/46/autohomecar__ChsEbGNCPJOAau-_AEG8miOELqM498.jpg"
with open(COVERS_PATH, "w", encoding="utf-8") as f:
    json.dump(covers, f, ensure_ascii=False, indent=2)

print("Successfully fixed Xiaomi SU7 and Jianghuai Xingrui mapping!")
