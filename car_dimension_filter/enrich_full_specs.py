# -*- coding: utf-8 -*-
"""
High-concurrency specification enricher for all vehicle series:
- Scrapes Owner Review Score (评分)
- Scrapes Drive Type (驱动形式: 前驱/后驱/四驱)
- Scrapes Horsepower (综合马力 Ps) and Curb Weight (整备质量 kg)
- Computes Power-to-weight ratio (推重比 Ps/吨)
- Scrapes Electric Range (纯电续航 km)
- Aggregates metrics into series.json with resilient checkpointing
"""

import os
import sys
import json
import time
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
import urllib3

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

urllib3.disable_warnings()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
SERIES_PATH = os.path.join(DATA_DIR, "series.json")
ENRICH_CACHE_PATH = os.path.join(DATA_DIR, "series_enriched_cache.json")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://car.autohome.com.cn/"
}

def parse_val(item):
    if not item: return ""
    v = item.get("value")
    if v and str(v).strip():
        return str(v).strip()
    sub = item.get("sublist")
    if sub and len(sub) > 0:
        sv = sub[0].get("subvalue")
        if sv and str(sv).strip():
            return str(sv).strip()
    return ""

def parse_first_digit(v):
    if not v: return None
    nums = re.findall(r"\d+(?:\.\d+)?", str(v))
    return float(nums[0]) if nums else None

def fetch_series_full_specs(sid, session=None):
    if not session:
        session = requests.Session()

    res = {
        "score": None,
        "versions": {}
    }

    # 1. 抓取评分
    try:
        p_url = f"https://car.autohome.com.cn/price/series-{sid}.html"
        r_p = session.get(p_url, headers=HEADERS, timeout=6, verify=False)
        if r_p.status_code == 200:
            score_match = re.findall(r'class="score-number">(\d\.\d{1,2})</span>', r_p.text)
            if score_match:
                res["score"] = float(score_match[0])
    except Exception:
        pass

    # 2. 抓取具体年款的参数配置
    try:
        c_url = f"https://car.m.autohome.com.cn/ashx/car/GetModelConfigNew.ashx?seriesId={sid}"
        r_c = session.get(c_url, headers=HEADERS, timeout=8, verify=False)
        if r_c.status_code == 200:
            data = r_c.json()
            param_map = {}
            for g in (data.get("param") or []):
                for it in (g.get("paramitems") or []):
                    param_map[it.get("name")] = it.get("valueitems") or []

            model_names = param_map.get("车型名称", [])
            drives = param_map.get("驱动方式", [])
            motor_ps = param_map.get("电动机总马力(Ps)", [])
            engine_ps = param_map.get("最大马力(Ps)", [])
            weights = param_map.get("整备质量(kg)", [])
            cltc_range = param_map.get("CLTC纯电续航里程(km)", [])
            wltc_range = param_map.get("WLTC纯电续航里程(km)", [])
            nedc_range = param_map.get("NEDC纯电续航里程(km)", [])

            for i, m_item in enumerate(model_names):
                spec_id = m_item.get("specid")
                m_name = parse_val(m_item)
                drv_raw = parse_val(drives[i]) if i < len(drives) else ""
                
                # 归一化驱动形式
                if any(w in drv_raw for w in ["四驱", "4WD", "AWD"]):
                    drive_type = "四驱"
                elif any(w in drv_raw for w in ["后驱", "后置"]):
                    drive_type = "后驱"
                elif any(w in drv_raw for w in ["前驱", "前置"]):
                    drive_type = "前驱"
                else:
                    drive_type = "前驱" if drv_raw else ""

                # 提取马力：优先电机总马力，若无取发动机最大马力
                ps_val = None
                if i < len(motor_ps):
                    ps_val = parse_first_digit(parse_val(motor_ps[i]))
                if (not ps_val or ps_val == 0) and i < len(engine_ps):
                    ps_val = parse_first_digit(parse_val(engine_ps[i]))

                # 提取车重 (kg)
                weight_val = parse_first_digit(parse_val(weights[i])) if i < len(weights) else None

                # 计算推重比 (Ps/吨)
                pwr_ratio = None
                if ps_val and weight_val and weight_val > 500:
                    pwr_ratio = round(ps_val / (weight_val / 1000.0), 1)

                # 提取纯电续航 (km)
                ev_range = None
                for r_arr in [cltc_range, wltc_range, nedc_range]:
                    if i < len(r_arr):
                        rv = parse_first_digit(parse_val(r_arr[i]))
                        if rv and rv > 0:
                            ev_range = int(rv)
                            break

                res["versions"][str(spec_id) if spec_id else m_name] = {
                    "drive_type": drive_type,
                    "drive_raw": drv_raw,
                    "horsepower": int(ps_val) if ps_val else None,
                    "weight": int(weight_val) if weight_val else None,
                    "pwr_ratio": pwr_ratio,
                    "ev_range": ev_range
                }
    except Exception:
        pass

    return sid, res

def run_enrichment(limit=None):
    with open(SERIES_PATH, "r", encoding="utf-8") as f:
        series_list = json.load(f)

    # 加载已缓存的数据
    if os.path.exists(ENRICH_CACHE_PATH):
        try:
            with open(ENRICH_CACHE_PATH, "r", encoding="utf-8") as f:
                cache = json.load(f)
        except Exception:
            cache = {}
    else:
        cache = {}

    # 优先处理在售车型
    active_todo = [s for s in series_list if not s.get("is_stopped") and str(s["series_id"]) not in cache]
    stopped_todo = [s for s in series_list if s.get("is_stopped") and str(s["series_id"]) not in cache]
    todo = active_todo + stopped_todo

    if limit:
        targets = todo[:limit]
    else:
        targets = todo

    print(f"Total series: {len(series_list)}, already enriched: {len(cache)}, todo: {len(targets)}")
    if not targets:
        print("All targets enriched already!")
    else:
        chunk_size = 60
        for chunk_start in range(0, len(targets), chunk_size):
            chunk = targets[chunk_start:chunk_start + chunk_size]
            print(f"\nProcessing chunk {chunk_start + 1} to {chunk_start + len(chunk)} of {len(targets)}...")
            t0 = time.time()
            
            def worker(s):
                session = requests.Session()
                return fetch_series_full_specs(s["series_id"], session)

            with ThreadPoolExecutor(max_workers=14) as pool:
                futures = {pool.submit(worker, s): s for s in chunk}
                for future in as_completed(futures):
                    sid, data = future.result()
                    cache[str(sid)] = data

            t1 = time.time()
            # 存盘缓存
            with open(ENRICH_CACHE_PATH, "w", encoding="utf-8") as f:
                json.dump(cache, f, ensure_ascii=False)
            print(f"Chunk finished in {t1 - t0:.2f}s. Checkpoint saved.")

    # 最终合并写入 series.json
    print("\nMerging enriched specs into series.json...")
    for s in series_list:
        sid_str = str(s.get("series_id"))
        if sid_str in cache:
            item = cache[sid_str]
            s["score"] = item.get("score") # 口碑评分 (如 4.47 或 None)
            
            v_cache = item.get("versions", {})
            drives_set = set()
            ratios_list = []
            ranges_list = []
            hp_list = []

            for v in s.get("versions", []):
                v_key = str(v.get("spec_id"))
                if v_key not in v_cache:
                    v_key = v.get("model_name")
                
                v_info = v_cache.get(v_key, {})
                drv = v_info.get("drive_type") or "前驱"
                v["drive_type"] = drv
                v["horsepower"] = v_info.get("horsepower")
                if v_info.get("weight"):
                    v["weight"] = v_info.get("weight")
                v["pwr_ratio"] = v_info.get("pwr_ratio")
                v["ev_range"] = v_info.get("ev_range")

                if drv: drives_set.add(drv)
                if v["pwr_ratio"]: ratios_list.append(v["pwr_ratio"])
                if v["ev_range"]: ranges_list.append(v["ev_range"])
                if v["horsepower"]: hp_list.append(v["horsepower"])

            # 聚合车系层级数据
            s["drive_types"] = sorted(list(drives_set)) if drives_set else ["前驱"]
            s["main_drive_type"] = "四驱" if "四驱" in s["drive_types"] else (s["drive_types"][0] if s["drive_types"] else "前驱")

            if ratios_list:
                s["pwr_ratio_min"] = min(ratios_list)
                s["pwr_ratio_max"] = max(ratios_list)
                if s["pwr_ratio_min"] == s["pwr_ratio_max"]:
                    s["pwr_ratio_str"] = f"{s['pwr_ratio_min']} Ps/吨"
                else:
                    s["pwr_ratio_str"] = f"{s['pwr_ratio_min']}～{s['pwr_ratio_max']} Ps/吨"
            else:
                s["pwr_ratio_min"] = None
                s["pwr_ratio_max"] = None
                s["pwr_ratio_str"] = "待查"

            if ranges_list:
                s["range_min"] = min(ranges_list)
                s["range_max"] = max(ranges_list)
                if s["range_min"] == s["range_max"]:
                    s["range_str"] = f"纯电 {s['range_min']}km"
                else:
                    s["range_str"] = f"纯电 {s['range_min']}～{s['range_max']}km"
            else:
                s["range_min"] = None
                s["range_max"] = None
                s["range_str"] = ""

            s["max_horsepower"] = max(hp_list) if hp_list else None

    with open(SERIES_PATH, "w", encoding="utf-8") as f:
        json.dump(series_list, f, ensure_ascii=False, indent=2)

    print("Successfully enriched and updated series.json!")

if __name__ == "__main__":
    count = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1] != "all" else None
    run_enrichment(count)
