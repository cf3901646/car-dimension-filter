# -*- coding: utf-8 -*-
"""
Fix Audited Issues:
1. Fix brand mismatches (Hongguang MINIEV -> Wuling, Hongqi H6/H9 -> Hongqi, Trumpchi M6 -> GAC, HIMA series).
2. Persist price_min & price_max for all series with valid price_str into series.json.
3. Fill 100% cover images for remaining 6 active series.
4. Fill missing drive types for remaining 3 active series.
5. Rebuild series-data.js and index.html.
"""

import os
import sys
import json
import re
import sqlite3

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

def clean_autoimg_url(raw_url):
    cleaned = re.sub(r'\d+x\d+(_\d+)?(_q\d+)?(_c\d+)?_', '', raw_url)
    if cleaned.startswith("//"): cleaned = "https:" + cleaned
    elif cleaned.startswith("http://"): cleaned = "https://" + cleaned[7:]
    return cleaned

def run_fix():
    print("=" * 60)
    print("FIXING AUDITED ISSUES")
    print("=" * 60)

    with open(SERIES_JSON_PATH, "r", encoding="utf-8") as f:
        series_list = json.load(f)

    with open(CARS_JSON_PATH, "r", encoding="utf-8") as f:
        cars_list = json.load(f)

    covers = {}
    if os.path.exists(COVERS_PATH):
        try:
            with open(COVERS_PATH, "r", encoding="utf-8") as f:
                covers = json.load(f)
        except Exception:
            pass

    # 1. 品牌纠错映射表
    explicit_brand_fix = {
        5714: ("五菱", "MINIEV"),          # 宏光MINIEV
        6703: ("奇瑞", "无界Pro"),          # 奇瑞无界Pro
        4662: ("广汽传祺", "M6"),          # 传祺M6
        6460: ("红旗", "H6"),              # 红旗H6
        5566: ("红旗", "H9"),              # 红旗H9
        7723: ("五菱", "E5"),              # 五菱E5
        5708: ("五菱", "EV50"),            # 五菱EV50
        8124: ("长安", "猎手 K50"),         # 长安猎手 K50
        8003: ("问界", "M8"),              # 问界M8
        6388: ("问界", "M5"),              # 问界M5
        6643: ("问界", "M7"),              # 问界M7
        7207: ("问界", "M9"),              # 问界M9
        8529: ("问界", "M6"),              # 问界M6
        7355: ("智界", "S7"),              # 智界S7
        7824: ("智界", "V9"),              # 智界V9
        8684: ("智界", "RX"),              # 智界RX
        7630: ("享界", "S9"),              # 享界S9
        8207: ("享界", "S9T"),             # 享界S9T
        8537: ("享界", "G9"),              # 享界G9
        5372: ("丰田", "iA5"),             # 广汽丰田iA5
    }

    # 驱动纠正
    explicit_drive_fix = {
        8530: ["四驱"],     # 北京81VJ 越野车
        8193: ["后驱"],     # 成功汽车 星马T3E 微卡
        5444: ["后驱"],     # 长安跨越 跨越者D5 卡车
    }

    # 封面图补齐
    explicit_cover_fix = {
        "5696": "https://car2.autoimg.cn/cardfs/series/g26/M05/D9/88/autohomecar__CjIFVmQbrymADU0pAAvQI7wHSUU610.png", # 奕炫GS
        "5511": "https://car2.autoimg.cn/cardfs/series/g34/M01/2A/DD/autohomecar__ChxpV2iDTGGAKBNzADZW79RTcQ0140.png", # ID.4 X
        "4418": "https://car3.autoimg.cn/cardfs/series/g26/M01/72/F1/autohomecar__CjIFVmgtqKSAUWsXAAmEMEALsWY872.png", # 菱智新能源
        "8091": "https://car3.autoimg.cn/cardfs/series/g34/M02/C6/EA/autohomecar__ChtpWGo_eSuAccUWAEAlDziqn4c433.png", # 猛士M817
        "4176": "https://car2.autoimg.cn/cardfs/series/g25/M04/10/64/autohomecar__CjIFV2Sel0qAf1yBAAnVb6Uy7EI358.png", # 捷尼赛思G80
        "7398": "https://car2.autoimg.cn/cardfs/series/g33/M07/AE/DD/autohomecar__ChxpVmkRrlmAINlrAC6d1Swt3Pk953.png", # eπ007
    }

    for sid_str, img_url in explicit_cover_fix.items():
        covers[sid_str] = clean_autoimg_url(img_url)

    brand_fixed = 0
    price_persisted = 0
    drive_fixed = 0
    cover_fixed = 0

    car_by_spec = {c.get("spec_id"): c for c in cars_list if c.get("spec_id")}

    for s in series_list:
        sid = s["series_id"]
        sid_str = str(sid)

        # 1. 品牌修复
        if sid in explicit_brand_fix:
            new_brand, new_disp = explicit_brand_fix[sid]
            s["brand"] = new_brand
            s["brand_name"] = new_brand
            s["display_series_name"] = new_disp
            brand_fixed += 1
            for v in s.get("versions", []):
                spec_id = v.get("spec_id")
                if spec_id in car_by_spec:
                    car_by_spec[spec_id]["brand"] = new_brand

        # 2. 价格持久化解析 (解决 1300+ 款车系 price_min 缺失导致无法参与价格筛选/排序的问题)
        if s.get("price_min") is None and s.get("price_str"):
            nums = [float(x) for x in re.findall(r"\d+(?:\.\d+)?", s["price_str"])]
            if nums:
                s["price_min"] = min(nums)
                s["price_max"] = max(nums)
                price_persisted += 1

        # 3. 驱动修复
        if sid in explicit_drive_fix:
            s["drive_types"] = explicit_drive_fix[sid]
            s["main_drive_type"] = explicit_drive_fix[sid][0]
            drive_fixed += 1
            for v in s.get("versions", []):
                v["drive_type"] = explicit_drive_fix[sid][0]

        # 4. 封面图填充
        if not s.get("cover_url") and sid_str in covers:
            s["cover_url"] = covers[sid_str]
            cover_fixed += 1

    print(f"Fix summary:")
    print(f"  Brands corrected: {brand_fixed}")
    print(f"  Price min/max persisted to series.json: {price_persisted}")
    print(f"  Drive types filled: {drive_fixed}")
    print(f"  Cover URLs filled: {cover_fixed}")

    # 保存文件
    with open(SERIES_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(series_list, f, ensure_ascii=False, indent=2)

    with open(CARS_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(cars_list, f, ensure_ascii=False, indent=2)

    with open(COVERS_PATH, "w", encoding="utf-8") as f:
        json.dump(covers, f, ensure_ascii=False, indent=2)

    # 同步 SQLite
    try:
        conn = sqlite3.connect(CARS_DB_PATH)
        cur = conn.cursor()
        for sid, (new_b, _) in explicit_brand_fix.items():
            cur.execute("UPDATE vehicles SET brand = ? WHERE series_id = ?", (new_b, sid))
        conn.commit()
        conn.close()
        print("SQLite cars.db brand updates committed!")
    except Exception as e:
        print(f"cars.db error: {e}")

    # 重新构建前端
    import subprocess
    build_script = os.path.join(BASE_DIR, "build_html.py")
    subprocess.run([sys.executable, build_script], check=True)
    print("Rebuild completed successfully!")

if __name__ == "__main__":
    run_fix()
