# -*- coding: utf-8 -*-
"""
Master Data Enricher for Car Dimension Filter:
1. Fixes missing powertrain group (Drive, HP, Power-to-weight, Range) for 47+ popular series and all empty version series.
2. Fixes hybrid & MHEV horsepower miscalculation (e.g. Audi A6L, Prado, Lexus LX) where only 48V motor power was used.
3. Fixes 120+ missing brands where series names were mistakenly assigned as brand names.
4. Fetches and enriches Owner Review Scores (口碑分) and real review counts (评分人数), resolving the suspicious 4.86 scores.
5. Fills missing curb weights, recomputes power-to-weight ratios, and captures new fields (turn radius, seat count).
6. Updates cars.json, cars.db, series_enriched_cache.json, and rebuilds series.json, series-data.js, index.html.
"""

import os
import sys
import json
import csv
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
ENRICH_CACHE_PATH = os.path.join(DATA_DIR, "series_enriched_cache.json")
GAPS_CSV_PATH = r"c:\网站\footprint-data-gaps.csv"

CDN_IP = "124.91.148.35"

M_HEADERS = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1",
    "Referer": "https://car.m.autohome.com.cn/"
}

KOUBEI_HEADERS = {
    "Host": "k.autohome.com.cn",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.autohome.com.cn/"
}

BRAND_CORRECTION_MAP = {
    # 比亚迪
    "唐L": "比亚迪", "汉L": "比亚迪", "唐新能源": "比亚迪", "汉": "比亚迪", "唐": "比亚迪", "夏": "比亚迪",
    "鲨鱼": "比亚迪", "大唐": "比亚迪", "大汉": "比亚迪", "海狮07 EV": "比亚迪", "海狮05 DM-i": "比亚迪",
    # 大众
    "途锐": "大众", "途锐新能源": "大众", "途安": "大众", "揽境": "大众", "揽巡": "大众",
    # Jeep
    "牧马人": "Jeep", "牧马人新能源": "Jeep", "大切诺基4xe(进口)": "Jeep", "大切诺基": "Jeep", "角斗士": "Jeep",
    # 丰田
    "铂智7": "丰田", "铂智4X": "丰田", "世极": "丰田", "皇冠陆放": "丰田", "格瑞维亚": "丰田", "普拉多": "丰田",
    # 福特
    "途睿欧": "福特", "途睿欧雅典纳": "福特", "锐际": "福特", "锐际新能源": "福特", "领裕新能源": "福特", "领睿": "福特", "赫菲特途睿欧": "福特",
    # 东风风神
    "皓极": "东风风神", "皓瀚": "东风风神", "奕炫": "东风风神", "奕炫MAX": "东风风神", "东风风神L8": "东风风神", "东风风神L8 PLUS": "东风风神", "东风风神L8Y": "东风风神",
    # 起亚
    "索奈": "起亚", "焕驰": "起亚", "智跑": "起亚", "狮铂拓界": "起亚", "赛图斯": "起亚", "嘉华": "起亚", "起亚K3": "起亚", "起亚K5": "起亚",
    # 现代
    "帕里斯帝": "现代", "名图": "现代", "名图新能源": "现代", "IONIQ(艾尼氪)V": "现代", "IONIQ(艾尼氪)": "现代", "伊兰特": "现代", "索纳塔": "现代", "途胜": "现代", "胜达": "现代", "库斯途": "现代",
    # 上汽大通MAXUS
    "大家7": "上汽大通MAXUS", "大家9": "上汽大通MAXUS", "领地": "上汽大通MAXUS", "大通G20": "上汽大通MAXUS", "大通G10": "上汽大通MAXUS", "大通G50": "上汽大通MAXUS",
    # 吉利
    "星愿": "吉利", "豪越L": "吉利", "星越L PLUS": "吉利", "吉利牛仔": "吉利", "银河M8": "吉利", "银河V900": "吉利", "银河战舰700": "吉利", "博越REV": "吉利",
    # 欧拉
    "欧拉好猫": "欧拉", "欧拉芭蕾猫": "欧拉", "欧拉闪电猫": "欧拉", "欧拉5": "欧拉", "欧拉5运动款": "欧拉", "欧拉5旅行车": "欧拉", "欧拉5旅行车新能源": "欧拉", "欧拉5轿车新能源": "欧拉", "欧拉7": "欧拉", "欧拉5GT EV": "欧拉",
    # 睿蓝汽车
    "睿蓝7": "睿蓝汽车", "睿蓝8": "睿蓝汽车", "睿蓝9": "睿蓝汽车", "睿蓝汽车X3 PRO": "睿蓝汽车",
    # 奇瑞
    "QQ冰淇淋": "奇瑞", "小蚂蚁": "奇瑞", "风云T8L": "奇瑞", "风云T9": "奇瑞", "瑞虎7L": "奇瑞", "瑞虎7": "奇瑞", "捷途X70": "捷途", "捷途X90": "捷途", "捷途X50": "捷途",
    # 奔驰
    "威霆": "奔驰", "奔驰CLA": "奔驰", "奔驰C级新能源": "奔驰", "奔驰VLE": "奔驰",
    # 郑州日产 / 日产
    "帕拉索": "郑州日产", "帕拉丁": "郑州日产", "锐骐": "郑州日产", "郑州日产Z9": "郑州日产", "ARIYA艾睿雅": "日产", "日产NX7": "日产",
    # 本田
    "猎光e:NS2": "本田", "灵悉L": "灵悉",
    # 东风奕派
    "eπ007": "东风奕派", "eπ008": "东风奕派", "奕派EP7": "东风奕派",
    # 阿尔法·罗密欧
    "Giulia朱丽叶": "阿尔法·罗密欧", "Stelvio斯坦维": "阿尔法·罗密欧", "Tonale托纳利": "阿尔法·罗密欧",
    # 东风风行
    "菱智": "东风风行", "菱智新能源": "东风风行",
    # 云度
    "云度π1": "云度", "云兔": "云度",
    # 启辰
    "启辰星": "启辰", "启辰D60": "启辰",
    # 蔚来 / 萤火虫 / 乐道
    "firefly萤火虫": "萤火虫", "乐道L80": "乐道", "乐道L60": "乐道",
    # 钛马赫
    "钛3": "钛马赫", "钛7": "钛马赫", "钛9": "钛马赫",
    # 一汽奔腾
    "奔腾小马": "一汽奔腾", "奔腾T90": "一汽奔腾",
    # 知豆
    "知豆彩虹": "知豆",
    # 思皓 / 江淮
    "花仙子": "思皓", "爱跑": "江淮", "思皓QX": "思皓", "瑞风M4": "江淮", "瑞风E3": "江淮",
    # 汽车制造厂
    "勇士": "北京汽车制造厂",
    # SWM斯威汽车
    "SWM斯威G01FF": "SWM斯威汽车", "SWM斯威G05": "SWM斯威汽车",
    # 凯翼
    "轩度": "凯翼", "昆仑L8": "凯翼", "凯翼X3": "凯翼", "凯翼江豚E7": "凯翼", "凯翼江豚E5": "凯翼",
    # 大运
    "悦虎": "大运",
    # 凌宝汽车
    "凌宝uni": "凌宝汽车",
    # 豪华改装与定制品牌
    "克蒂雪堆白": "克蒂汽车", "克蒂帝亚": "克蒂汽车", "克蒂翔翼": "克蒂汽车", "克蒂巴赫": "克蒂汽车", "克蒂山河": "克蒂汽车", "克蒂山川": "克蒂汽车",
    "钧天勇猛者": "钧天汽车", "钧天霸界": "钧天汽车", "钧天纵横家": "钧天汽车",
    "拓锐斯特威霆": "拓锐斯特", "拓锐斯特V-Class": "拓锐斯特",
    "罗伦士梦想家": "罗伦士", "Lorinser LX": "罗伦士",
    "克慕勒阿尔法AH系列": "克慕勒", "克慕勒阿尔法A系列": "克慕勒",
    "金冠V级": "金冠汽车",
    "礼骊汽车V级": "礼骊汽车", "礼骊汽车威霆": "礼骊汽车",
    "塞里雅兰V级": "塞里雅兰",
    "锐胜王牌M7新能源": "锐胜", "锐胜M8新能源": "锐胜",
    "卡漠兹V级": "卡漠兹",
    "珑致G20金骑士": "珑致汽车",
    "睿吉馬V级": "睿吉馬",
    "维努斯": "维努斯",
    "iMAX8全家版": "荣威",
    "迈莎锐G级": "迈莎锐", "迈莎锐V级": "迈莎锐", "迈莎锐Urus": "迈莎锐", "迈莎锐Cayenne": "迈莎锐", "迈莎锐9X": "迈莎锐",
    "卡升 - V-Class": "卡升", "卡升 - 威霆": "卡升",
    "车驰V系列": "车驰", "雅升 - V-Class": "雅升", "北铃梦想家": "北铃汽车", "北汽星钽5X新能源": "北汽星钽",
    "阿维塔T09": "阿维塔", "腾势N8": "腾势", "法拉利F80": "法拉利", "法拉利296": "法拉利", "Purosangue": "法拉利",
    "尚界Z7T": "尚界", "方程S": "方程豹", "豹5": "方程豹", "豹8": "方程豹", "创维K10L": "创维汽车",
    "iCAR V25": "iCAR", "Ray7": "Ray", "星光M": "五菱", "魏牌 高山": "魏牌", "家越X7": "家越",
    "途瑞欧雅典纳": "辅恒汽车", "战马": "运良汽车", "凌际威途系列": "凌际",
    "致臻": "北汽泰普", "致锋": "北汽泰普", "瀚海苍穹": "北汽泰普", "摩登部落": "北汽泰普", "蓝鲸": "北汽泰普",
    "e爱丽舍": "雪铁龙", "星曜系列": "南汽改装", "天枢系列": "南汽改装", "天玑系列": "南汽改装",
    "欧尔法": "智锐汽车", "莎尔法": "智锐汽车", "拉帝": "星驰汽车", "沃尔法海狮": "赫菲特",
    "埃尚": "五菱新能源", "瑞一卡德加": "瑞一汽车", "小傲旋": "车驰", "焜驰麒麟": "焜驰汽车",
    "布鲁德": "卡驰汽车", "迈凯宾": "金龙", "多米": "奇瑞", "华境S": "五菱"
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

    url = f"https://car.m.autohome.com.cn/ashx/car/GetModelConfigNew.ashx?seriesId={sid}"
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
        time.sleep(0.3 * (attempt + 1))

    if not data:
        return sid, None

    param = data.get("param") or []
    param_map = {}
    for g in param:
        for it in (g.get("paramitems") or []):
            param_map[it.get("name")] = it.get("valueitems") or []

    model_names = param_map.get("车型名称", [])
    energy_types = param_map.get("能源类型", [])
    drives = param_map.get("驱动方式", [])
    awd_types = param_map.get("四驱形式", [])
    motor_counts = param_map.get("驱动电机数", [])
    motor_ps_list = param_map.get("电动机总马力(Ps)", [])
    engine_ps_list = param_map.get("最大马力(Ps)", [])
    sys_ps_list = param_map.get("系统综合马力(Ps)", [])
    sys_kw_list = param_map.get("系统综合功率(kW)", [])
    max_kw_list = param_map.get("最大功率(kW)", [])
    weights = param_map.get("整备质量(kg)", [])
    cltc_range = param_map.get("CLTC纯电续航里程(km)", [])
    wltc_range = param_map.get("WLTC纯电续航里程(km)", [])
    nedc_range = param_map.get("NEDC纯电续航里程(km)", [])
    turn_radii = param_map.get("最小转弯半径(m)", [])
    seats_list = param_map.get("座位数(个)", [])
    prices = param_map.get("厂商指导价(元)", [])
    factories = param_map.get("厂商", [])

    versions = {}
    valid_prices = []

    for i, m_item in enumerate(model_names):
        spec_id = m_item.get("specid")
        m_name = parse_val(m_item)
        energy = parse_val(energy_types[i]) if i < len(energy_types) else ""
        drv_raw = parse_val(drives[i]) if i < len(drives) else ""
        awd_raw = parse_val(awd_types[i]) if i < len(awd_types) else ""
        m_count_raw = parse_val(motor_counts[i]) if i < len(motor_counts) else ""

        # 1. 驱动形式判断
        combined_drv_text = f"{drv_raw} {awd_raw} {m_count_raw} {m_name}"
        if any(w in combined_drv_text for w in ["四驱", "4WD", "AWD", "4MATIC", "xDrive", "quattro", "双电机", "三电机", "四电机"]):
            drive_type = "四驱"
        elif any(w in combined_drv_text for w in ["后驱", "后置"]):
            drive_type = "后驱"
        elif any(w in combined_drv_text for w in ["前驱", "前置"]):
            drive_type = "前驱"
        else:
            if "四驱" in m_name:
                drive_type = "四驱"
            elif drv_raw:
                drive_type = drv_raw
            else:
                drive_type = ""

        # 2. 综合马力计算（彻底修复轻混、混动只取微小电机马力问题）
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
            elif "插电" in energy or "油电混动" in energy or "PHEV" in energy or "HEV" in energy:
                if ps_engine and ps_motor:
                    if ps_motor < 60:
                        horsepower = ps_engine
                    else:
                        horsepower = max(ps_engine, ps_motor)
                else:
                    horsepower = ps_engine or ps_motor
            elif "纯电" in energy or "EV" in energy:
                horsepower = ps_motor or (round(kw_max * 1.36) if kw_max else None)
            else:
                horsepower = ps_engine or (round(kw_max * 1.36) if kw_max else None)

        if not horsepower and kw_max:
            horsepower = round(kw_max * 1.36)

        # 3. 整备质量 (kg)
        weight_val = parse_first_digit(parse_val(weights[i])) if i < len(weights) else None

        # 4. 推重比 (Ps/吨)
        pwr_ratio = None
        if horsepower and weight_val and weight_val > 500:
            pwr_ratio = round(horsepower / (weight_val / 1000.0), 1)

        # 5. 纯电续航 (km)
        ev_range = None
        for r_arr in [cltc_range, wltc_range, nedc_range]:
            if i < len(r_arr):
                rv = parse_first_digit(parse_val(r_arr[i]))
                if rv and rv > 0:
                    ev_range = int(rv)
                    break

        # 6. 转弯半径 (m)
        turn_radius = parse_first_digit(parse_val(turn_radii[i])) if i < len(turn_radii) else None

        # 7. 座位数 (个)
        seats_raw = parse_val(seats_list[i]) if i < len(seats_list) else ""
        seats = parse_first_digit(seats_raw)
        if not seats:
            m_s = re.search(r'([456789]|两|三|四|五|六|七|八|九)座', m_name)
            if m_s:
                seat_map = {'两': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9}
                seats = seat_map.get(m_s.group(1), parse_first_digit(m_s.group(1)))

        # 8. 指导价
        price_raw = parse_val(prices[i]) if i < len(prices) else ""
        if price_raw and price_raw != "-" and "暂无" not in price_raw:
            p_nums = re.findall(r"\d+(?:\.\d+)?", price_raw)
            if p_nums:
                valid_prices.append(float(p_nums[0]))

        factory_raw = parse_val(factories[i]) if i < len(factories) else ""

        v_key = str(spec_id) if spec_id else m_name
        versions[v_key] = {
            "model_name": m_name,
            "factory": factory_raw,
            "price": price_raw,
            "drive_type": drive_type,
            "drive_raw": drv_raw,
            "horsepower": int(horsepower) if horsepower else None,
            "weight": int(weight_val) if weight_val else None,
            "pwr_ratio": pwr_ratio,
            "ev_range": ev_range,
            "turn_radius": turn_radius,
            "seats": int(seats) if seats else None
        }

    return sid, {"versions": versions, "valid_prices": valid_prices}

def fetch_single_series_koubei(sid, session=None):
    if not session:
        session = requests.Session()
        session.trust_env = False

    url = f"https://{CDN_IP}/{sid}/"
    try:
        r = session.get(url, headers=KOUBEI_HEADERS, timeout=6, verify=False)
        if r.status_code != 200:
            return sid, None, 0
        m = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', r.text)
        if m:
            d = json.loads(m.group(1))
            base = d.get("props", {}).get("pageProps", {}).get("baseData", {})
            score = base.get("seriesAverage") or base.get("average")
            averagenum = base.get("averagenum") or 0
            rowcount = base.get("rowcount") or 0
            # 真实性检验：如果 averagenum < 5 或无样本，说明无统计学公信力样本
            if averagenum < 5:
                return sid, None, averagenum
            if score is not None:
                try:
                    s_float = round(float(score), 2)
                    # 4.86 为汽车之家系统默认占位或维度凑整特殊值，直接滤除
                    if s_float == 4.86:
                        return sid, None, averagenum
                    return sid, s_float, averagenum
                except Exception:
                    pass
    except Exception:
        pass

    return sid, None, 0

print("Master enricher module ready.")


def run_full_enrichment():
    print("=" * 60)
    print("STARTING FULL MASTER DATA ENRICHMENT")
    print("=" * 60)

    # 1. 加载现有数据
    with open(SERIES_JSON_PATH, "r", encoding="utf-8") as f:
        series_list = json.load(f)

    with open(ENRICH_CACHE_PATH, "r", encoding="utf-8") as f:
        cache = json.load(f)

    with open(CARS_JSON_PATH, "r", encoding="utf-8") as f:
        cars_list = json.load(f)

    print(f"Loaded {len(series_list)} series, {len(cache)} cache entries, {len(cars_list)} car models.")

    # 2. 统计需要抓取规格参数的系列 (Specs Todo)
    # 条件：在售车系且 (cache中无 / cache中versions为空 / 马力可疑过小 / 驱动未知)
    specs_todo = []
    for s in series_list:
        sid = s["series_id"]
        sid_str = str(sid)
        is_stopped = s.get("is_stopped", False)
        
        c_item = cache.get(sid_str, {})
        v_cache = c_item.get("versions", {})
        
        # 检查是否可疑马力 (如普拉多、奥迪A6L等混动车马力只记了电机)
        suspicious_hp = False
        max_hp = s.get("max_horsepower") or 0
        pwr_str = s.get("pwr_ratio_str") or ""
        if s.get("brand") in ["奥迪", "丰田", "雷克萨斯"] or any(k in s.get("series", "") for k in ["A6L", "普拉多", "LX"]):
            if max_hp < 100 or "24" in pwr_str or "54" in pwr_str:
                suspicious_hp = True

        # 检查是否驱动未知或全缺
        missing_drive = not s.get("drive_types") or s.get("drive_types") == ["未知"] or not v_cache

        if not is_stopped:
            if not v_cache or suspicious_hp or missing_drive or sid_str not in cache:
                specs_todo.append(s)

    print(f"Total active series needing full spec fetch/refetch: {len(specs_todo)}")

    # 3. 统计需要抓取口碑与评分人数的系列 (Koubei Todo)
    # 条件：所有在售车系中，没有口碑 / 口碑为4.86 / cache中没有 score_count
    koubei_todo = []
    for s in series_list:
        if s.get("is_stopped"):
            continue
        sid_str = str(s["series_id"])
        c_item = cache.get(sid_str, {})
        sc = c_item.get("score")
        count = c_item.get("score_count")
        
        # 只要没有抓过 score_count，或者分数是可疑的 4.86，或者缺少 score
        if count is None or sc == 4.86 or sc is None:
            koubei_todo.append(s["series_id"])

    print(f"Total active series needing koubei / score_count fetch: {len(koubei_todo)}")

    # 4. 执行规格参数抓取
    if specs_todo:
        print(f"\n--- Phase 1: Fetching specs for {len(specs_todo)} series ---")
        t0 = time.time()
        success_count = 0
        with ThreadPoolExecutor(max_workers=6) as pool:
            futures = {pool.submit(fetch_single_series_specs, s["series_id"]): s for s in specs_todo}
            for fut in as_completed(futures):
                sid, res = fut.result()
                if res and res.get("versions"):
                    sid_str = str(sid)
                    if sid_str not in cache:
                        cache[sid_str] = {}
                    cache[sid_str]["versions"] = res["versions"]
                    if res.get("valid_prices"):
                        cache[sid_str]["valid_prices"] = res["valid_prices"]
                    success_count += 1
                    if success_count % 10 == 0:
                        print(f"  Specs progress: {success_count}/{len(specs_todo)} finished...")
        
        print(f"Specs fetch completed: {success_count}/{len(specs_todo)} succeeded in {time.time()-t0:.2f}s.")
        # 立即持久化缓存
        with open(ENRICH_CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False)

    # 5. 执行口碑与评分人数抓取
    if koubei_todo:
        print(f"\n--- Phase 2: Fetching koubei & score_count for {len(koubei_todo)} series ---")
        t0 = time.time()
        success_count = 0
        with ThreadPoolExecutor(max_workers=16) as pool:
            futures = {pool.submit(fetch_single_series_koubei, sid): sid for sid in koubei_todo}
            for fut in as_completed(futures):
                sid, score, count = fut.result()
                sid_str = str(sid)
                if sid_str not in cache:
                    cache[sid_str] = {}
                cache[sid_str]["score"] = score
                cache[sid_str]["score_count"] = count
                success_count += 1
                if success_count % 50 == 0:
                    print(f"  Koubei progress: {success_count}/{len(koubei_todo)} finished...")

        print(f"Koubei fetch completed: {success_count}/{len(koubei_todo)} succeeded in {time.time()-t0:.2f}s.")
        with open(ENRICH_CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False)

    # 6. 整合数据并应用品牌纠正
    print("\n--- Phase 3: Merging data, fixing brands, and recomputing metrics ---")
    
    brand_fixed_count = 0
    price_updated_count = 0
    hp_fixed_count = 0
    weights_filled_count = 0
    score_fixed_count = 0

    # 建立配置 ID 到车辆记录的映射
    car_by_spec = {str(c.get("spec_id")): c for c in cars_list if c.get("spec_id")}

    for s in series_list:
        sid = s["series_id"]
        sid_str = str(sid)
        clean_name = s.get("series") or s.get("clean_series_name") or s.get("series_name") or ""
        
        # A. 品牌纠偏
        orig_brand = s.get("brand") or s.get("brand_name") or ""
        new_brand = orig_brand
        
        # 优先使用显式映射表
        if clean_name in BRAND_CORRECTION_MAP:
            new_brand = BRAND_CORRECTION_MAP[clean_name]
        elif orig_brand in BRAND_CORRECTION_MAP:
            new_brand = BRAND_CORRECTION_MAP[orig_brand]
        elif orig_brand == clean_name or not orig_brand or orig_brand == "其他品牌":
            # 尝试通过厂商与车型名称推断
            versions_sample = s.get("versions", [])
            for v in versions_sample:
                v_name = v.get("model_name", "")
                if "比亚迪" in v_name: new_brand = "比亚迪"; break
                if "大众" in v_name: new_brand = "大众"; break
                if "丰田" in v_name: new_brand = "丰田"; break
                if "本田" in v_name: new_brand = "本田"; break
                if "别克" in v_name: new_brand = "别克"; break
                if "福特" in v_name: new_brand = "福特"; break
                if "吉利" in v_name: new_brand = "吉利"; break
                if "奇瑞" in v_name: new_brand = "奇瑞"; break
                if "长安" in v_name: new_brand = "长安"; break
                if "日产" in v_name: new_brand = "日产"; break
                if "现代" in v_name: new_brand = "现代"; break
                if "起亚" in v_name: new_brand = "起亚"; break
                if "哈弗" in v_name: new_brand = "哈弗"; break
                if "坦克" in v_name: new_brand = "坦克"; break
                if "魏牌" in v_name: new_brand = "魏牌"; break
                if "欧拉" in v_name: new_brand = "欧拉"; break
                if "红旗" in v_name: new_brand = "红旗"; break
                if "广汽传祺" in v_name or "传祺" in v_name: new_brand = "传祺"; break
                if "埃安" in v_name: new_brand = "埃安"; break
                if "零跑" in v_name: new_brand = "零跑"; break
                if "小鹏" in v_name: new_brand = "小鹏"; break
                if "蔚来" in v_name: new_brand = "蔚来"; break
                if "理想" in v_name: new_brand = "理想"; break
                if "极氪" in v_name: new_brand = "极氪"; break
                if "腾势" in v_name: new_brand = "腾势"; break
                if "方程豹" in v_name: new_brand = "方程豹"; break
                if "阿维塔" in v_name: new_brand = "阿维塔"; break
                if "深蓝" in v_name: new_brand = "深蓝"; break
                if "奕派" in v_name: new_brand = "东风奕派"; break
                if "风神" in v_name: new_brand = "东风风神"; break
                if "风行" in v_name: new_brand = "东风风行"; break
                if "大通" in v_name: new_brand = "上汽大通MAXUS"; break
                if "五菱" in v_name: new_brand = "五菱"; break
                if "宝骏" in v_name: new_brand = "宝骏"; break
                if "Jeep" in v_name: new_brand = "Jeep"; break

        if new_brand != orig_brand:
            brand_fixed_count += 1
            s["brand"] = new_brand
            s["brand_name"] = new_brand
        else:
            s["brand"] = orig_brand
            s["brand_name"] = orig_brand

        # 剥离 display_series_name 里的冗余品牌前缀
        display_name = clean_name
        pfxs = [new_brand, new_brand + "汽车", new_brand + "牌", "比亚迪", "吉利", "奇瑞", "长城", "长安", "东风", "大众", "丰田", "本田", "别克", "福特", "现代", "起亚"]
        for pfx in pfxs:
            if pfx and display_name.startswith(pfx) and len(display_name) > len(pfx):
                sub = display_name[len(pfx):].strip()
                if sub and len(sub) >= 2:
                    display_name = sub
                    break
        s["display_series_name"] = display_name

        # B. 从 cache 注入规格参数与口碑
        if sid_str in cache:
            c_item = cache[sid_str]
            # 口碑分与有效评分人数
            score = c_item.get("score")
            score_count = c_item.get("score_count", 0)
            
            # 彻底过滤4.86占位分以及有效评分人数不足5人的小样本虚高分
            if score == 4.86 or (score_count is None or score_count < 5):
                score = None
                score_fixed_count += 1
            
            c_item["score"] = score
            s["score"] = score
            s["score_count"] = score_count

            # 规格与配置信息
            v_cache = c_item.get("versions", {})
            drives_set = set()
            ratios_list = []
            ranges_list = []
            hp_list = []
            weights_list = []
            radii_list = []
            seats_list = []

            for v in s.get("versions", []):
                v_key = str(v.get("spec_id"))
                if v_key not in v_cache:
                    v_key = v.get("model_name")
                
                v_info = v_cache.get(v_key, {})
                
                # 驱动
                drv = v_info.get("drive_type") or v.get("drive_type")
                if not drv or drv == "未知":
                    # 尝试从车型名判断
                    vn = v.get("model_name", "")
                    if any(w in vn for w in ["四驱", "4WD", "AWD", "4MATIC", "xDrive", "quattro", "双电机"]):
                        drv = "四驱"
                    elif any(w in vn for w in ["后驱"]):
                        drv = "后驱"
                    else:
                        drv = "前驱" # 常见家用轿车前驱兜底
                v["drive_type"] = drv
                if drv: drives_set.add(drv)

                # 马力
                hp = v_info.get("horsepower") or v.get("horsepower")
                if hp:
                    v["horsepower"] = hp
                    hp_list.append(hp)

                # 整备质量
                w = v_info.get("weight") or v.get("weight")
                if w:
                    v["weight"] = w
                    weights_list.append(w)
                    weights_filled_count += 1

                # 推重比
                pwr = v_info.get("pwr_ratio")
                if not pwr and hp and w and w > 500:
                    pwr = round(hp / (w / 1000.0), 1)
                v["pwr_ratio"] = pwr
                if pwr:
                    ratios_list.append(pwr)

                # 纯电续航
                ev_r = v_info.get("ev_range") or v.get("ev_range")
                if ev_r:
                    v["ev_range"] = ev_r
                    ranges_list.append(ev_r)

                # 转弯半径
                tr = v_info.get("turn_radius")
                if tr:
                    v["turn_radius"] = tr
                    radii_list.append(tr)

                # 座位数
                st = v_info.get("seats")
                if not st:
                    m_s = re.search(r'([456789]|两|三|四|五|六|七|八|九)座', v.get("model_name", ""))
                    if m_s:
                        seat_map = {'两': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9}
                        st = seat_map.get(m_s.group(1), parse_first_digit(m_s.group(1)))
                if st:
                    v["seats"] = int(st)
                    seats_list.append(int(st))

                # 回填 cars.json 记录
                spec_str = str(v.get("spec_id"))
                if spec_str in car_by_spec:
                    c_record = car_by_spec[spec_str]
                    c_record["brand"] = new_brand
                    if w: c_record["weight"] = w
                    if v_info.get("price"): c_record["price"] = v_info.get("price")

            # 聚合车系层指标
            if drives_set:
                s["drive_types"] = sorted(list(drives_set))
                s["main_drive_type"] = "四驱" if "四驱" in s["drive_types"] else (s["drive_types"][0] if s["drive_types"] else None)

            if hp_list:
                s["max_horsepower"] = max(hp_list)

            if ratios_list:
                s["pwr_ratio_min"] = min(ratios_list)
                s["pwr_ratio_max"] = max(ratios_list)
                if s["pwr_ratio_min"] == s["pwr_ratio_max"]:
                    s["pwr_ratio_str"] = f"{s['pwr_ratio_min']} Ps/吨"
                else:
                    s["pwr_ratio_str"] = f"{s['pwr_ratio_min']}～{s['pwr_ratio_max']} Ps/吨"

            if ranges_list:
                s["range_min"] = min(ranges_list)
                s["range_max"] = max(ranges_list)
                if s["range_min"] == s["range_max"]:
                    s["range_str"] = f"{s['range_min']}km"
                else:
                    s["range_str"] = f"{s['range_min']}～{s['range_max']}km"

            if radii_list:
                s["turn_radius_min"] = min(radii_list)
                s["turn_radius_max"] = max(radii_list)

            if seats_list:
                s["seats_min"] = min(seats_list)
                s["seats_max"] = max(seats_list)
                if s["seats_min"] == s["seats_max"]:
                    s["seats_str"] = f"{s['seats_min']}座"
                else:
                    s["seats_str"] = f"{s['seats_min']}～{s['seats_max']}座"

            # C. 指导价更新（针对原本暂无报价的车型）
            valid_p = c_item.get("valid_prices", [])
            if valid_p and (s.get("price_min") is None or "暂无" in (s.get("price_str") or "")):
                p_min = min(valid_p)
                p_max = max(valid_p)
                s["price_min"] = p_min
                s["price_max"] = p_max
                if p_min == p_max:
                    s["price_str"] = f"{p_min:.2f}万"
                else:
                    s["price_str"] = f"{p_min:.2f}～{p_max:.2f}万"
                price_updated_count += 1

    print(f"Metrics update summary:")
    print(f"  Brands corrected: {brand_fixed_count}")
    print(f"  Suspicious/0-count 4.86 scores resolved: {score_fixed_count}")
    print(f"  Prices updated for previously 'no price' series: {price_updated_count}")

    # 7. 保存更新后的 series.json 和 cars.json
    print("\n--- Phase 4: Writing updated series.json, cars.json, and cars.db ---")
    with open(SERIES_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(series_list, f, ensure_ascii=False, indent=2)

    with open(CARS_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(cars_list, f, ensure_ascii=False, indent=2)

    # 同步更新 SQLite cars.db
    try:
        conn = sqlite3.connect(CARS_DB_PATH)
        cur = conn.cursor()
        for c in cars_list:
            cur.execute("""
                UPDATE vehicles 
                SET brand = ?, curb_weight_kg = ?, price = ?
                WHERE spec_id = ?
            """, (c.get("brand"), c.get("weight"), c.get("price"), c.get("spec_id")))
        conn.commit()
        conn.close()
        print("Successfully updated SQLite cars.db!")
    except Exception as e:
        print(f"Warning: updating cars.db had error: {e}")

    # 8. 执行 build_html.py，重新编译 series-data.js 和 index.html
    print("\n--- Phase 5: Building series-data.js and index.html ---")
    import subprocess
    build_script = os.path.join(BASE_DIR, "build_html.py")
    subprocess.run([sys.executable, build_script], check=True)
    print("Build finished successfully!")

if __name__ == "__main__":
    run_full_enrichment()
