# -*- coding: utf-8 -*-
import sys
import json
import re

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

with open("car_dimension_filter/data/series.json", "r", encoding="utf-8") as f:
    series_list = json.load(f)

def parse_price(s):
    p_str = s.get("price_str") or ""
    nums = re.findall(r"\d+(?:\.\d+)?", p_str)
    if nums:
        p_min = float(nums[0])
        p_max = float(nums[1]) if len(nums) > 1 else p_min
        return p_min, p_max, (p_min + p_max) / 2
    return 0, 0, 0

s_map = {str(s["series_id"]): s for s in series_list}

def get_body_type(s):
    lvl = (s.get("level") or "") + " " + " ".join(s.get("body_structures") or [])
    if "SUV" in lvl: return "suv"
    if "MPV" in lvl: return "mpv"
    if "跑车" in lvl: return "sports"
    return "sedan"

def find_competitors(target_id):
    target = s_map.get(str(target_id))
    if not target:
        return []
    
    t_min, t_max, avg_p = parse_price(target)
    wb = target.get("wheelbase_max") or target.get("wheelbase_min") or 2800
    b_type = get_body_type(target)
    
    candidates = []
    for s in series_list:
        if s.get("is_stopped"):
            continue
        if s.get("series_id") == target.get("series_id"):
            continue
        
        # 车型类别优先对齐
        if get_body_type(s) != b_type:
            continue
            
        sp_min, sp_max, sp_avg = parse_price(s)
        if avg_p > 0 and sp_avg > 0:
            p_diff = abs(sp_avg - avg_p)
            if p_diff > max(avg_p * 0.35, 6):
                continue
        
        # 轴距容差 ±140mm
        s_wb = s.get("wheelbase_max") or s.get("wheelbase_min") or 0
        if abs(s_wb - wb) > 150:
            continue
            
        candidates.append(s)
        
    candidates.sort(key=lambda x: (x.get("score") or 0, -(abs((x.get("wheelbase_max") or 0) - wb))), reverse=True)
    return candidates[:3]

benchmarks = [
    (5769, "特斯拉 Model Y (中型纯电SUV)"),
    (6962, "小米 SU7 (C级性能纯电轿车)"),
    (5964, "比亚迪 秦PLUS (10万级主力家轿)"),
    (66, "宝马 3系 (30万级豪华运动轿车)"),
    (6091, "极氪 001 (中大型猎装轿跑)")
]

for sid, label in benchmarks:
    comps = find_competitors(sid)
    print(f"\n🎯 {label} 核心同级同价位竞品推荐:")
    for c in comps:
        p_min, p_max, avg = parse_price(c)
        print(f"   -> [{c.get('series_id')}] {c.get('brand')} {c.get('series')} ({c.get('level')}) | 指导价: {c.get('price_str')} | 轴距: {c.get('wheelbase_max')}mm | 车主口碑: {c.get('score')} ★")
