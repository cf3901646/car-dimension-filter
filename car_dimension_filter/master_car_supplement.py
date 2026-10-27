# -*- coding: utf-8 -*-
"""
Master Car Supplement Tool:
1. Scans missing modern and popular series (including MAEXTRO 尊界全系, 智界, 享界, 小米, 小鹏, 蔚来, 仰望, 比亚迪, 阿维塔, etc.)
2. Fetches full specifications (Dimensions, Wheelbase, Weight, Drive type, Horsepower, Power-to-weight, Range, Radius, Seats, Price).
3. Fetches official high-res cover images and clean owner review scores (strictly excluding 4.86 placeholder & <5 low sample scores).
4. Merges into series.json, cars.json, cars.db, series_covers.json, series_enriched_cache.json.
5. Rebuilds series-data.js and index.html.
"""

import os
import sys
import json
import re
import time
import sqlite3
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
import urllib3

urllib3.disable_warnings()

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
CARS_JSON_PATH = os.path.join(DATA_DIR, "cars.json")
CARS_DB_PATH = os.path.join(DATA_DIR, "cars.db")
SERIES_JSON_PATH = os.path.join(DATA_DIR, "series.json")
COVERS_PATH = os.path.join(DATA_DIR, "series_covers.json")
CACHE_PATH = os.path.join(DATA_DIR, "series_enriched_cache.json")
CATALOG_PATH = os.path.join(os.path.dirname(BASE_DIR), "scratch", "missing_series_catalog.json")
if not os.path.exists(CATALOG_PATH):
    CATALOG_PATH = r"C:\Users\320327744\.gemini\antigravity\brain\4ecbfe81-b885-4391-819a-dc33af461596\scratch\missing_series_catalog.json"

CDN_IP = "124.91.148.35"

M_HEADERS = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X)",
    "Referer": "https://car.m.autohome.com.cn/",
    "Host": "car.m.autohome.com.cn"
}

PC_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://car.autohome.com.cn/",
    "Host": "car.autohome.com.cn"
}

KOUBEI_HEADERS = {
    "Host": "k.autohome.com.cn",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://www.autohome.com.cn/"
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

def fetch_single_series_specs(sid, session=None, retries=2):
    if not session:
        session = requests.Session()
        session.trust_env = False

    url = f"https://{CDN_IP}/ashx/car/GetModelConfigNew.ashx?seriesId={sid}"
    data = None
    for attempt in range(retries + 1):
        try:
            r = session.get(url, headers=M_HEADERS, timeout=8, verify=False)
            if r.status_code == 200:
                data = r.json()
                if data and (data.get("param") or data.get("result")):
                    break
        except Exception:
            pass
        time.sleep(0.2 * (attempt + 1))

    if not data:
        return sid, None

    param = data.get("param") or []
    param_map = {}
    for g in param:
        for it in (g.get("paramitems") or []):
            param_map[it.get("name")] = it.get("valueitems") or []

    model_names = param_map.get("车型名称", [])
    if not model_names:
        return sid, None

    levels = param_map.get("级别", [])
    energy_types = param_map.get("能源类型", [])
    body_types = param_map.get("车身结构", [])
    lengths = param_map.get("长度(mm)", [])
    widths = param_map.get("宽度(mm)", [])
    heights = param_map.get("高度(mm)", [])
    wheelbases = param_map.get("轴距(mm)", [])
    weights = param_map.get("整备质量(kg)", [])
    drives = param_map.get("驱动方式", [])
    awd_types = param_map.get("四驱形式", [])
    motor_counts = param_map.get("驱动电机数", [])
    motor_ps_list = param_map.get("电动机总马力(Ps)", [])
    engine_ps_list = param_map.get("最大马力(Ps)", [])
    sys_ps_list = param_map.get("系统综合马力(Ps)", [])
    sys_kw_list = param_map.get("系统综合功率(kW)", [])
    max_kw_list = param_map.get("最大功率(kW)", [])
    cltc_range = param_map.get("CLTC纯电续航里程(km)", [])
    wltc_range = param_map.get("WLTC纯电续航里程(km)", [])
    nedc_range = param_map.get("NEDC纯电续航里程(km)", [])
    turn_radii = param_map.get("最小转弯半径(m)", [])
    seats_list = param_map.get("座位数(个)", [])
    prices = param_map.get("厂商指导价(元)", [])
    factories = param_map.get("厂商", [])

    # 如果所有车型的长度都拿不到，尝试从 '长*宽*高(mm)' 解析
    dim_combos = param_map.get("长*宽*高(mm)", [])

    versions = []
    series_level = parse_val(levels[0]) if levels else "乘用车"
    series_energy_set = set()

    for i, m_item in enumerate(model_names):
        spec_id = m_item.get("specid")
        m_name = parse_val(m_item)
        if not m_name:
            continue

        energy = parse_val(energy_types[i]) if i < len(energy_types) else ""
        if energy: series_energy_set.add(energy)

        # 尺寸
        l_val = parse_first_digit(parse_val(lengths[i])) if i < len(lengths) else None
        w_val = parse_first_digit(parse_val(widths[i])) if i < len(widths) else None
        h_val = parse_first_digit(parse_val(heights[i])) if i < len(heights) else None
        wb_val = parse_first_digit(parse_val(wheelbases[i])) if i < len(wheelbases) else None

        if (not l_val or not w_val or not h_val) and i < len(dim_combos):
            dim_str = parse_val(dim_combos[i])
            nums = re.findall(r"\d+(?:\.\d+)?", dim_str)
            if len(nums) >= 3:
                l_val = l_val or float(nums[0])
                w_val = w_val or float(nums[1])
                h_val = h_val or float(nums[2])

        # 过滤尺寸严重缺失的概念车
        if not l_val or not w_val or not h_val:
            continue

        # 驱动
        drv_raw = parse_val(drives[i]) if i < len(drives) else ""
        awd_raw = parse_val(awd_types[i]) if i < len(awd_types) else ""
        m_count_raw = parse_val(motor_counts[i]) if i < len(motor_counts) else ""
        combined_drv_text = f"{drv_raw} {awd_raw} {m_count_raw} {m_name}"
        if any(w in combined_drv_text for w in ["四驱", "4WD", "AWD", "4MATIC", "xDrive", "quattro", "双电机", "三电机", "四电机"]):
            drive_type = "四驱"
        elif any(w in combined_drv_text for w in ["后驱", "后置"]):
            drive_type = "后驱"
        elif any(w in combined_drv_text for w in ["前驱", "前置"]):
            drive_type = "前驱"
        else:
            drive_type = "前驱" if "轿车" in series_level or "微型" in series_level else "未知"

        # 马力
        ps_sys = parse_first_digit(parse_val(sys_ps_list[i])) if i < len(sys_ps_list) else None
        kw_sys = parse_first_digit(parse_val(sys_kw_list[i])) if i < len(sys_kw_list) else None
        ps_engine = parse_first_digit(parse_val(engine_ps_list[i])) if i < len(engine_ps_list) else None
        ps_motor = parse_first_digit(parse_val(motor_ps_list[i])) if i < len(motor_ps_list) else None
        kw_max = parse_first_digit(parse_val(max_kw_list[i])) if i < len(max_kw_list) else None

        horsepower = None
        if ps_sys and ps_sys > 0:
            horsepower = ps_sys
        elif kw_sys and kw_sys > 0:
            horsepower = round(kw_sys * 1.36)
        else:
            if "增程" in energy:
                horsepower = ps_motor or (round(kw_max * 1.36) if kw_max else None) or ps_engine
            elif any(w in energy for w in ["轻混", "48V"]) or (ps_engine and ps_motor and ps_motor < 60):
                horsepower = ps_engine
            elif any(w in energy for w in ["插电", "油电混动", "PHEV", "HEV"]):
                if ps_engine and ps_motor:
                    horsepower = ps_engine if ps_motor < 60 else max(ps_engine, ps_motor)
                else:
                    horsepower = ps_engine or ps_motor
            elif "纯电" in energy or "EV" in energy:
                horsepower = ps_motor or (round(kw_max * 1.36) if kw_max else None)
            else:
                horsepower = ps_engine or (round(kw_max * 1.36) if kw_max else None)

        if not horsepower and kw_max:
            horsepower = round(kw_max * 1.36)

        # 重量与推重比
        weight_val = parse_first_digit(parse_val(weights[i])) if i < len(weights) else None
        pwr_ratio = None
        if horsepower and weight_val and weight_val > 500:
            pwr_ratio = round(horsepower / (weight_val / 1000.0), 1)

        # 纯电续航
        ev_range = None
        for r_arr in [cltc_range, wltc_range, nedc_range]:
            if i < len(r_arr):
                rv = parse_first_digit(parse_val(r_arr[i]))
                if rv and rv > 0:
                    ev_range = int(rv)
                    break

        # 转弯半径
        turn_radius = parse_first_digit(parse_val(turn_radii[i])) if i < len(turn_radii) else None

        # 座位数
        seats_raw = parse_val(seats_list[i]) if i < len(seats_list) else ""
        seats = parse_first_digit(seats_raw)
        if not seats:
            m_s = re.search(r'([456789]|两|三|四|五|六|七|八|九)座', m_name)
            if m_s:
                seat_map = {'两': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9}
                seats = seat_map.get(m_s.group(1), parse_first_digit(m_s.group(1)))

        # 价格
        price_raw = parse_val(prices[i]) if i < len(prices) else ""
        if price_raw and "万" not in price_raw and "-" not in price_raw:
            try:
                p_num = float(price_raw)
                if p_num > 1000:
                    price_raw = f"{p_num / 10000.0:.2f}万"
            except Exception:
                pass

        v_obj = {
            "spec_id": int(spec_id) if spec_id else None,
            "model_name": m_name,
            "energy_type": energy,
            "body_structure": parse_val(body_types[i]) if i < len(body_types) else "",
            "price": price_raw,
            "length": int(l_val),
            "width": int(w_val),
            "height": int(h_val),
            "wheelbase": int(wb_val) if wb_val else None,
            "weight": int(weight_val) if weight_val else None,
            "drive_type": drive_type,
            "horsepower": int(horsepower) if horsepower else None,
            "pwr_ratio": pwr_ratio,
            "ev_range": ev_range,
            "turn_radius": turn_radius,
            "seats": int(seats) if seats else None
        }
        versions.append(v_obj)

    if not versions:
        return sid, None

    return sid, {
        "level": series_level,
        "energy_types": sorted(list(series_energy_set)),
        "versions": versions
    }

def fetch_single_series_cover(sid, session=None):
    if not session:
        session = requests.Session()
        session.trust_env = False
    
    url = f"https://{CDN_IP}/price/series-{sid}.html"
    try:
        r = session.get(url, headers=PC_HEADERS, timeout=6, verify=False)
        if r.status_code == 200:
            matches = re.findall(
                r'(?:https?:)?//[^\s"\'<>]*autoimg[^\s"\'<>]*cardfs[^\s"\'<>]*\.(?:jpg|jpeg|png)',
                r.text,
                re.IGNORECASE
            )
            if matches:
                u = matches[0]
                cleaned = re.sub(r'\d+x\d+(_\d+)?(_q\d+)?(_c\d+)?_', '', u)
                if cleaned.startswith("//"): cleaned = "https:" + cleaned
                elif cleaned.startswith("http://"): cleaned = "https://" + cleaned[7:]
                return sid, cleaned
    except Exception:
        pass

    # 备选图库页
    try:
        url_pic = f"https://{CDN_IP}/pic/series/{sid}.html"
        r = session.get(url_pic, headers=PC_HEADERS, timeout=6, verify=False)
        if r.status_code == 200:
            matches = re.findall(
                r'(?:https?:)?//[^\s"\'<>]*autoimg[^\s"\'<>]*cardfs[^\s"\'<>]*\.(?:jpg|jpeg|png)',
                r.text,
                re.IGNORECASE
            )
            if matches:
                u = matches[0]
                cleaned = re.sub(r'\d+x\d+(_\d+)?(_q\d+)?(_c\d+)?_', '', u)
                if cleaned.startswith("//"): cleaned = "https:" + cleaned
                elif cleaned.startswith("http://"): cleaned = "https://" + cleaned[7:]
                return sid, cleaned
    except Exception:
        pass

    return sid, None

def fetch_single_series_koubei(sid, session=None):
    if not session:
        session = requests.Session()
        session.trust_env = False

    url = f"https://{CDN_IP}/{sid}/"
    try:
        r = session.get(url, headers=KOUBEI_HEADERS, timeout=6, verify=False)
        if r.status_code == 200:
            m = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', r.text)
            if m:
                d = json.loads(m.group(1))
                base = d.get("props", {}).get("pageProps", {}).get("baseData", {})
                score = base.get("seriesAverage") or base.get("average")
                averagenum = base.get("averagenum") or 0
                if averagenum < 5:
                    return sid, None, averagenum
                if score is not None:
                    s_float = round(float(score), 2)
                    if s_float == 4.86:
                        return sid, None, averagenum
                    return sid, s_float, averagenum
    except Exception:
        pass
    return sid, None, 0

def run_supplementation():
    print("=" * 60)
    print("STARTING MASTER CAR SUPPLEMENTATION")
    print("=" * 60)

    # 1. 读取基础库
    with open(SERIES_JSON_PATH, "r", encoding="utf-8") as f:
        local_series = json.load(f)
    local_sids = set(s["series_id"] for s in local_series)

    with open(CARS_JSON_PATH, "r", encoding="utf-8") as f:
        local_cars = json.load(f)

    with open(CACHE_PATH, "r", encoding="utf-8") as f:
        enrich_cache = json.load(f)

    covers = {}
    if os.path.exists(COVERS_PATH):
        try:
            with open(COVERS_PATH, "r", encoding="utf-8") as f:
                covers = json.load(f)
        except Exception:
            pass

    # 2. 读取待补全清单
    with open(CATALOG_PATH, "r", encoding="utf-8") as f:
        missing_catalog = json.load(f)

    # 优先选出：重点品牌 + 2020年至今（SID >= 5000）
    popular_brands = [
        "尊界", "智界", "享界", "AITO 问界", "问界", "小米汽车", "小鹏", "蔚来", "理想汽车",
        "零跑汽车", "极氪", "乐道", "腾势", "方程豹", "仰望", "比亚迪", "吉利汽车", "奇瑞",
        "长城", "长安", "广汽传祺", "埃安", "极越", "极石", "深蓝汽车", "阿维塔", "奔驰", "宝马", "奥迪", "保时捷"
    ]

    candidates = []
    for s in missing_catalog:
        sid = s["series_id"]
        if sid in local_sids:
            continue
        is_pop = any(pb in s["brand_name"] for pb in popular_brands)
        if is_pop or sid >= 5000:
            candidates.append(s)

    # 确保尊界全系排在最前
    def sort_key(s):
        if "尊界" in s["brand_name"] or "尊界" in s["series_name"]:
            return (0, -s["series_id"])
        if any(pb in s["brand_name"] for pb in ["智界", "享界", "问界", "小米", "仰望", "方程豹", "阿维塔"]):
            return (1, -s["series_id"])
        return (2, -s["series_id"])

    candidates.sort(key=sort_key)
    print(f"Total candidate series to probe & enrich: {len(candidates)}")
    print(f"Top 5 candidates: {[(c['brand_name'], c['series_name'], c['series_id']) for c in candidates[:5]]}")

    # 3. 批量多线程探测与抓取规格参数 (Phase 1)
    print("\n--- Phase 1: Probing & Fetching Specifications ---")
    valid_new_series = []
    t0 = time.time()
    success_count = 0

    with ThreadPoolExecutor(max_workers=10) as pool:
        futures = {pool.submit(fetch_single_series_specs, c["series_id"]): c for c in candidates}
        done = 0
        for fut in as_completed(futures):
            c = futures[fut]
            sid, res = fut.result()
            done += 1
            if res and res.get("versions"):
                success_count += 1
                valid_new_series.append({
                    "meta": c,
                    "spec": res
                })
                print(f"  [+] 成功发现有效配置: [{c['brand_name']}] {c['series_name']} (SID {sid}) - {len(res['versions'])} 款配置")
            if done % 100 == 0:
                print(f"  扫描进度: {done}/{len(candidates)} 完成，已成功抓取 {success_count} 款新车系...")

    print(f"\nPhase 1 完成：在 {len(candidates)} 个候选车系中，成功获取 {len(valid_new_series)} 款有真实配置的新车系，耗时 {time.time()-t0:.2f}s！")

    if not valid_new_series:
        print("无有效新车系需要添加。")
        return

    # 4. 批量多线程抓取新车系的封面图与口碑分 (Phase 2)
    print(f"\n--- Phase 2: Fetching Covers and Koubei for {len(valid_new_series)} Series ---")
    new_sids = [item["meta"]["series_id"] for item in valid_new_series]

    new_covers = {}
    with ThreadPoolExecutor(max_workers=12) as pool:
        futures = {pool.submit(fetch_single_series_cover, sid): sid for sid in new_sids}
        for fut in as_completed(futures):
            sid, c_url = fut.result()
            if c_url:
                new_covers[str(sid)] = c_url
                covers[str(sid)] = c_url

    print(f"获取到 {len(new_covers)}/{len(new_sids)} 款车系封面图！")

    new_koubei = {}
    with ThreadPoolExecutor(max_workers=12) as pool:
        futures = {pool.submit(fetch_single_series_koubei, sid): sid for sid in new_sids}
        for fut in as_completed(futures):
            sid, score, count = fut.result()
            new_koubei[str(sid)] = {"score": score, "score_count": count}

    # 5. 数据组装与品牌纠正 (Phase 3)
    print("\n--- Phase 3: Assembling Series & Car Records ---")
    added_series_objs = []
    added_car_records = []

    for item in valid_new_series:
        c = item["meta"]
        spec = item["spec"]
        sid = c["series_id"]
        sid_str = str(sid)
        raw_bname = c["brand_name"]
        raw_sname = c["series_name"]

        # 品牌清洗与规范
        brand = raw_bname
        if "尊界" in raw_bname or "尊界" in raw_sname: brand = "尊界"
        elif "智界" in raw_bname or "智界" in raw_sname: brand = "智界"
        elif "享界" in raw_bname or "享界" in raw_sname: brand = "享界"
        elif "问界" in raw_bname or "AITO" in raw_bname: brand = "问界"
        elif "小米" in raw_bname: brand = "小米"
        elif "方程豹" in raw_bname: brand = "方程豹"
        elif "仰望" in raw_bname: brand = "仰望"
        elif "阿维塔" in raw_bname: brand = "阿维塔"
        elif "乐道" in raw_bname: brand = "乐道"
        elif "极氪" in raw_bname: brand = "极氪"
        elif "腾势" in raw_bname: brand = "腾势"
        elif "小鹏" in raw_bname: brand = "小鹏"
        elif "蔚来" in raw_bname: brand = "蔚来"
        elif "理想" in raw_bname: brand = "理想"
        elif "零跑" in raw_bname: brand = "零跑"
        elif "比亚迪" in raw_bname: brand = "比亚迪"
        elif "吉利" in raw_bname: brand = "吉利"
        elif "奇瑞" in raw_bname: brand = "奇瑞"

        # display_series_name 去除冗余品牌前缀
        display_name = raw_sname
        pfxs = [brand, brand + "汽车", brand + "牌", "比亚迪", "吉利", "奇瑞", "长城", "长安", "东风", "大众", "丰田", "本田"]
        for pfx in pfxs:
            if display_name.startswith(pfx) and len(display_name) > len(pfx):
                sub = display_name[len(pfx):].strip()
                if sub and len(sub) >= 2:
                    display_name = sub
                    break

        vs = spec["versions"]
        ls = [v["length"] for v in vs if v.get("length")]
        ws = [v["width"] for v in vs if v.get("width")]
        hs = [v["height"] for v in vs if v.get("height")]
        wbs = [v["wheelbase"] for v in vs if v.get("wheelbase")]
        drvs = sorted(list(set(v["drive_type"] for v in vs if v.get("drive_type") and v.get("drive_type") != "未知")))
        if not drvs: drvs = ["未知"]
        main_drv = "四驱" if "四驱" in drvs else drvs[0]

        hps = [v["horsepower"] for v in vs if v.get("horsepower")]
        pwrs = [v["pwr_ratio"] for v in vs if v.get("pwr_ratio")]
        ranges = [v["ev_range"] for v in vs if v.get("ev_range")]
        radii = [v["turn_radius"] for v in vs if v.get("turn_radius")]
        seats_all = [v["seats"] for v in vs if v.get("seats")]

        # 价格区间
        prices_clean = []
        for v in vs:
            p_str = v.get("price") or ""
            nums = re.findall(r"\d+(?:\.\d+)?", p_str)
            if nums:
                prices_clean.append(float(nums[0]))

        price_min = min(prices_clean) if prices_clean else None
        price_max = max(prices_clean) if prices_clean else None
        if price_min and price_max:
            price_str = f"{price_min:.2f}万" if price_min == price_max else f"{price_min:.2f}～{price_max:.2f}万"
        else:
            price_str = "暂无报价"

        # 推重比与续航文字
        pwr_str = ""
        if pwrs:
            pwr_min, pwr_max = min(pwrs), max(pwrs)
            pwr_str = f"{pwr_min} Ps/吨" if pwr_min == pwr_max else f"{pwr_min}～{pwr_max} Ps/吨"

        range_str = ""
        if ranges:
            r_min, r_max = min(ranges), max(ranges)
            range_str = f"{r_min}km" if r_min == r_max else f"{r_min}～{r_max}km"

        seats_str = ""
        if seats_all:
            s_min, s_max = min(seats_all), max(seats_all)
            seats_str = f"{s_min}座" if s_min == s_max else f"{s_min}～{s_max}座"

        kb = new_koubei.get(sid_str, {})

        series_entry = {
            "series_id": sid,
            "brand": brand,
            "brand_name": brand,
            "series": raw_sname,
            "series_name": raw_sname,
            "clean_series_name": raw_sname,
            "display_series_name": display_name,
            "level": spec["level"],
            "energy_types": spec["energy_types"],
            "drive_types": drvs,
            "main_drive_type": main_drv,
            "price_str": price_str,
            "price_min": price_min,
            "price_max": price_max,
            "score": kb.get("score"),
            "score_count": kb.get("score_count", 0),
            "is_stopped": False,
            "cover_url": new_covers.get(sid_str, ""),
            "length_min": min(ls) if ls else 4800,
            "length_max": max(ls) if ls else 4800,
            "width_min": min(ws) if ws else 1900,
            "width_max": max(ws) if ws else 1900,
            "height_min": min(hs) if hs else 1500,
            "height_max": max(hs) if hs else 1500,
            "wheelbase_min": min(wbs) if wbs else 2900,
            "wheelbase_max": max(wbs) if wbs else 2900,
            "pwr_ratio_min": min(pwrs) if pwrs else None,
            "pwr_ratio_max": max(pwrs) if pwrs else None,
            "pwr_ratio_str": pwr_str,
            "range_min": min(ranges) if ranges else None,
            "range_max": max(ranges) if ranges else None,
            "range_str": range_str,
            "max_horsepower": max(hps) if hps else None,
            "turn_radius_min": min(radii) if radii else None,
            "turn_radius_max": max(radii) if radii else None,
            "seats_min": min(seats_all) if seats_all else None,
            "seats_max": max(seats_all) if seats_all else None,
            "seats_str": seats_str,
            "version_count": len(vs),
            "versions": vs
        }
        added_series_objs.append(series_entry)

        # 缓存记录
        enrich_cache[sid_str] = {
            "score": kb.get("score"),
            "score_count": kb.get("score_count", 0),
            "valid_prices": prices_clean,
            "versions": {str(v.get("spec_id") or v["model_name"]): v for v in vs}
        }

        # 扁平化车辆记录
        for v in vs:
            added_car_records.append({
                "spec_id": v.get("spec_id"),
                "series_id": sid,
                "brand": brand,
                "series": raw_sname,
                "model_name": v["model_name"],
                "level": spec["level"],
                "energy_type": v.get("energy_type", ""),
                "body_structure": v.get("body_structure", ""),
                "length_mm": v.get("length"),
                "width_mm": v.get("width"),
                "height_mm": v.get("height"),
                "wheelbase_mm": v.get("wheelbase"),
                "curb_weight_kg": v.get("weight"),
                "price": v.get("price")
            })

    print(f"整理完成：新增 {len(added_series_objs)} 个车系，{len(added_car_records)} 款车型配置！")

    # 6. 合并并保存文件 (Phase 4)
    print("\n--- Phase 4: Saving updated datasets ---")
    local_series.extend(added_series_objs)
    local_cars.extend(added_car_records)

    with open(SERIES_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(local_series, f, ensure_ascii=False, indent=2)

    with open(CARS_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(local_cars, f, ensure_ascii=False, indent=2)

    with open(COVERS_PATH, "w", encoding="utf-8") as f:
        json.dump(covers, f, ensure_ascii=False, indent=2)

    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(enrich_cache, f, ensure_ascii=False)

    # 写入 SQLite cars.db
    try:
        conn = sqlite3.connect(CARS_DB_PATH)
        cur = conn.cursor()
        for c in added_car_records:
            if not c.get("spec_id"): continue
            cur.execute("""
                INSERT OR REPLACE INTO vehicles (
                    spec_id, series_id, brand, series, model_name, level, energy_type,
                    body_structure, length_mm, width_mm, height_mm, wheelbase_mm,
                    curb_weight_kg, price
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                c["spec_id"], c["series_id"], c["brand"], c["series"], c["model_name"],
                c["level"], c["energy_type"], c["body_structure"], c["length_mm"],
                c["width_mm"], c["height_mm"], c["wheelbase_mm"], c["curb_weight_kg"],
                c["price"]
            ))
        conn.commit()
        conn.close()
        print("SQLite cars.db 写入成功！")
    except Exception as e:
        print(f"写入 cars.db 异常: {e}")

    # 7. 重新编译 index.html 与 series-data.js (Phase 5)
    print("\n--- Phase 5: Rebuilding series-data.js & index.html ---")
    import subprocess
    build_script = os.path.join(BASE_DIR, "build_html.py")
    subprocess.run([sys.executable, build_script], check=True)
    print("Build 成功完成！全库数据已包含尊界全系及最新补充车型。")

if __name__ == "__main__":
    run_supplementation()
