# -*- coding: utf-8 -*-
import json
import sys
import re

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

series_list = json.load(open("car_dimension_filter/data/series.json", encoding="utf-8"))
covers = json.load(open("car_dimension_filter/data/series_covers.json", encoding="utf-8")) if True else {}

print(f"Total series in series.json: {len(series_list)}")

# 1. 检查车系名与配置名严重不符的车型
name_mismatches = []
# 2. 检查车名/品牌重复 (如 "易至EV3 易至EV3")
brand_series_repeats = []
# 3. 检查主流在售无封面
active_no_cover = []
# 4. 检查主流在售无动力推重比
active_no_pwr = []

# 知名品牌列表，用于识别“不冷门车型”
POPULAR_BRANDS = [
    "小米汽车", "特斯拉", "比亚迪", "理想汽车", "蔚来", "小鹏汽车", "极氪", "鸿蒙智行", "问界", "智界",
    "方程豹", "仰望", "腾势汽车", "宝马", "奔驰", "奥迪", "保时捷", "大众", "丰田", "本田",
    "吉利汽车", "领克", "长城汽车", "哈弗", "坦克", "长安汽车", "奇瑞", "红旗", "别克", "日产", "沃尔沃"
]

for s in series_list:
    sid = s.get("series_id")
    b = s.get("brand") or s.get("brand_name") or ""
    ser = s.get("series") or s.get("clean_series_name") or ""
    is_stopped = s.get("is_stopped", False)
    has_cover = bool(s.get("cover_url") or covers.get(str(sid)))
    has_pwr = bool(s.get("pwr_ratio_min") or s.get("pwr_ratio_max"))
    versions = s.get("versions") or []

    # 1. 检查配置与车系名冲突
    if versions:
        v_names = [v.get("model_name", "") for v in versions if v.get("model_name")]
        if v_names:
            first_v = v_names[0]
            # 如果车系名比较短且不在任何配置名中，但配置名中有一个共同的强标识
            clean_ser = re.sub(r'[^\w]', '', ser)
            match_any = any(clean_ser in re.sub(r'[^\w]', '', vn) for vn in v_names)
            if not match_any and len(clean_ser) >= 2:
                name_mismatches.append({
                    "series_id": sid,
                    "brand": b,
                    "series": ser,
                    "sample_version": first_v
                })

    # 2. 检查品牌和车名重复
    if b and ser and (b.strip() == ser.strip() or b.lower() == ser.lower()):
        brand_series_repeats.append({"series_id": sid, "brand": b, "series": ser})

    # 3. 检查热门品牌却缺图或缺动力
    is_pop = any(pb in b or pb in ser for pb in POPULAR_BRANDS)
    if not is_stopped and is_pop:
        if not has_cover:
            active_no_cover.append({"series_id": sid, "brand": b, "series": ser})
        if not has_pwr:
            active_no_pwr.append({"series_id": sid, "brand": b, "series": ser})

print("\n--- 1. 车系名称与配置名称不匹配 (可能存在车系错乱) ---")
print(f"Count: {len(name_mismatches)}")
for it in name_mismatches[:15]:
    print(f"  SID {it['series_id']} | 品牌: {it['brand']} | 车系: {it['series']} | 配置款: {it['sample_version']}")

print("\n--- 2. 品牌与车名完全重复 ---")
print(f"Count: {len(brand_series_repeats)}")
for it in brand_series_repeats[:10]:
    print(f"  SID {it['series_id']} | 品牌: {it['brand']} | 车系: {it['series']}")

print("\n--- 3. 热门在售车型 无封面图 ---")
print(f"Count: {len(active_no_cover)}")
for it in active_no_cover[:15]:
    print(f"  SID {it['series_id']} | {it['brand']} {it['series']}")

print("\n--- 4. 热门在售车型 无动力推重比参数 ---")
print(f"Count: {len(active_no_pwr)}")
for it in active_no_pwr[:15]:
    print(f"  SID {it['series_id']} | {it['brand']} {it['series']}")
