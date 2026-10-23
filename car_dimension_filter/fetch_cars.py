import urllib.request
import json
import re
import os
import sys
import time
import sqlite3

# Windows 终端控制台 utf-8 编码兼容
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

POPULAR_SERIES = [
    # 特斯拉
    {"brand": "特斯拉", "series": "Model 3", "series_id": 5346},
    {"brand": "特斯拉", "series": "Model Y", "series_id": 5769},
    # 比亚迪
    {"brand": "比亚迪", "series": "秦PLUS", "series_id": 6050},
    {"brand": "比亚迪", "series": "秦L", "series_id": 7545},
    {"brand": "比亚迪", "series": "汉", "series_id": 5666},
    {"brand": "比亚迪", "series": "宋PLUS新能源", "series_id": 5970},
    {"brand": "比亚迪", "series": "海鸥", "series_id": 7183},
    {"brand": "比亚迪", "series": "元PLUS", "series_id": 6512},
    {"brand": "比亚迪", "series": "海豹", "series_id": 6649},
    # 小米
    {"brand": "小米汽车", "series": "小米SU7", "series_id": 7436},
    # 理想
    {"brand": "理想汽车", "series": "理想L6", "series_id": 7515},
    {"brand": "理想汽车", "series": "理想L7", "series_id": 6867},
    {"brand": "理想汽车", "series": "理想L8", "series_id": 6735},
    {"brand": "理想汽车", "series": "理想L9", "series_id": 6736},
    {"brand": "理想汽车", "series": "理想MEGA", "series_id": 7384},
    # 蔚来 / 小鹏
    {"brand": "蔚来", "series": "蔚来ET5", "series_id": 6598},
    {"brand": "蔚来", "series": "蔚来ES6", "series_id": 4983},
    {"brand": "小鹏汽车", "series": "小鹏MONA M03", "series_id": 7661},
    {"brand": "小鹏汽车", "series": "小鹏G6", "series_id": 7205},
    {"brand": "小鹏汽车", "series": "小鹏P7+", "series_id": 7752},
    # 极氪 / 鸿蒙智行
    {"brand": "极氪", "series": "极氪001", "series_id": 6251},
    {"brand": "极氪", "series": "极氪007", "series_id": 7453},
    {"brand": "极氪", "series": "极氪7X", "series_id": 7780},
    {"brand": "鸿蒙智行", "series": "问界M7", "series_id": 6813},
    {"brand": "鸿蒙智行", "series": "问界M9", "series_id": 7247},
    {"brand": "鸿蒙智行", "series": "智界S7", "series_id": 7393},
    # 宝马 / 奔驰 / 奥迪 (含进口)
    {"brand": "宝马", "series": "宝马3系", "series_id": 66},
    {"brand": "宝马", "series": "宝马5系", "series_id": 159},
    {"brand": "宝马", "series": "宝马X3", "series_id": 271},
    {"brand": "宝马", "series": "宝马7系", "series_id": 161},
    {"brand": "奔驰", "series": "奔驰C级", "series_id": 588},
    {"brand": "奔驰", "series": "奔驰E级", "series_id": 197},
    {"brand": "奔驰", "series": "奔驰GLC", "series_id": 3862},
    {"brand": "奔驰", "series": "奔驰S级", "series_id": 59},
    {"brand": "奥迪", "series": "奥迪A4L", "series_id": 692},
    {"brand": "奥迪", "series": "奥迪A6L", "series_id": 18},
    {"brand": "奥迪", "series": "奥迪Q5L", "series_id": 4172},
    {"brand": "奥迪", "series": "奥迪A8", "series_id": 146},
    # 保时捷 / 雷克萨斯 (纯进口代表)
    {"brand": "保时捷", "series": "Panamera", "series_id": 703},
    {"brand": "保时捷", "series": "Macan", "series_id": 3144},
    {"brand": "保时捷", "series": "Taycan", "series_id": 5041},
    {"brand": "雷克萨斯", "series": "雷克萨斯ES", "series_id": 403},
    {"brand": "雷克萨斯", "series": "雷克萨斯RX", "series_id": 404},
    # 丰田 / 本田 / 大众
    {"brand": "丰田", "series": "凯美瑞", "series_id": 110},
    {"brand": "丰田", "series": "卡罗拉", "series_id": 526},
    {"brand": "丰田", "series": "RAV4荣放", "series_id": 770},
    {"brand": "丰田", "series": "赛那", "series_id": 6296},
    {"brand": "本田", "series": "雅阁", "series_id": 78},
    {"brand": "本田", "series": "思域", "series_id": 135},
    {"brand": "本田", "series": "CR-V", "series_id": 314},
    {"brand": "大众", "series": "朗逸", "series_id": 614},
    {"brand": "大众", "series": "迈腾", "series_id": 496},
    {"brand": "大众", "series": "帕萨特", "series_id": 528},
    {"brand": "大众", "series": "高尔夫", "series_id": 871},
    # 别克 / 腾势 / 坦克 (MPV与越野)
    {"brand": "别克", "series": "别克GL8", "series_id": 166},
    {"brand": "腾势汽车", "series": "腾势D9", "series_id": 6712},
    {"brand": "坦克", "series": "坦克300", "series_id": 5833},
]

def fetch_series_data_with_retry(series_info, max_retries=3):
    series_id = series_info["series_id"]
    brand = series_info["brand"]
    series = series_info["series"]
    url = f"https://car.m.autohome.com.cn/ashx/car/GetModelConfigNew.ashx?seriesId={series_id}"
    
    for attempt in range(max_retries):
        try:
            timeout_sec = 8 + attempt * 5
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            })
            with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
                content = resp.read().decode("utf-8")
                data = json.loads(content)
                break
        except Exception as e:
            if attempt == max_retries - 1:
                print(f"[-] 抓取失败 (重试耗尽) {brand} {series} (ID: {series_id}): {e}")
                return []
            time.sleep(1.0)

    param_map = {}
    for group in (data.get("param") or []):
        for item in (group.get("paramitems") or []):
            param_map[item.get("name")] = item.get("valueitems") or []

    model_names = param_map.get("车型名称") or []
    if not model_names:
        return []

    lengths = param_map.get("长度(mm)", [])
    widths = param_map.get("宽度(mm)", [])
    heights = param_map.get("高度(mm)", [])
    wheelbases = param_map.get("轴距(mm)", [])
    levels = param_map.get("级别", [])
    energies = param_map.get("能源类型", [])
    structures = param_map.get("车身结构", [])
    weights = param_map.get("整备质量(kg)", [])
    prices = param_map.get("厂商指导价(元)", [])

    results = []
    for i, m_item in enumerate(model_names):
        spec_id = m_item.get("specid")
        m_name = m_item.get("value", "")

        def get_val(arr):
            if i < len(arr):
                val = arr[i].get("value", "")
                return val
            return ""

        def parse_int(v):
            digits = re.findall(r"\d+", str(v))
            if digits:
                return int(digits[0])
            return None

        len_val = parse_int(get_val(lengths))
        wid_val = parse_int(get_val(widths))
        hei_val = parse_int(get_val(heights))
        wb_val = parse_int(get_val(wheelbases))
        weight_val = parse_int(get_val(weights))

        # 只要长宽高和轴距有效，就记录
        if len_val and wid_val and hei_val and wb_val:
            results.append({
                "spec_id": spec_id,
                "series_id": series_id,
                "brand": brand,
                "series": series,
                "model_name": m_name,
                "level": get_val(levels),
                "energy_type": get_val(energies),
                "body_structure": get_val(structures),
                "length": len_val,
                "width": wid_val,
                "height": hei_val,
                "wheelbase": wb_val,
                "weight": weight_val,
                "price": get_val(prices)
            })

    print(f"[+] 抓取成功: {brand} {series}，解析到 {len(results)} 款有效车型")
    return results

def aggregate_by_series(all_cars):
    series_map = {}
    for c in all_cars:
        sid = c["series_id"]
        if sid not in series_map:
            series_map[sid] = {
                "series_id": sid,
                "brand": c["brand"],
                "series": c["series"],
                "level": c.get("level", ""),
                "energy_types": set(),
                "body_structures": set(),
                "lengths": [],
                "widths": [],
                "heights": [],
                "wheelbases": [],
                "prices": [],
                "versions": []
            }
        s = series_map[sid]
        if c.get("energy_type"):
            s["energy_types"].add(c["energy_type"])
        if c.get("body_structure"):
            s["body_structures"].add(c["body_structure"])
        s["lengths"].append(c["length"])
        s["widths"].append(c["width"])
        s["heights"].append(c["height"])
        s["wheelbases"].append(c["wheelbase"])
        if c.get("price") and c.get("price") != "-":
            s["prices"].append(c["price"])
        s["versions"].append(c)

    aggregated = []
    for sid, s in series_map.items():
        min_len, max_len = min(s["lengths"]), max(s["lengths"])
        min_wid, max_wid = min(s["widths"]), max(s["widths"])
        min_hei, max_hei = min(s["heights"]), max(s["heights"])
        min_wb, max_wb = min(s["wheelbases"]), max(s["wheelbases"])

        # 格式化尺寸展示字符串
        len_str = f"{min_len}" if min_len == max_len else f"{min_len}～{max_len}"
        wid_str = f"{min_wid}" if min_wid == max_wid else f"{min_wid}～{max_wid}"
        hei_str = f"{min_hei}" if min_hei == max_hei else f"{min_hei}～{max_hei}"
        wb_str = f"{min_wb}" if min_wb == max_wb else f"{min_wb}～{max_wb}"

        # 格式化价格范围
        price_str = "暂无报价"
        if s["prices"]:
            p_nums = []
            for p in s["prices"]:
                match = re.findall(r"[\d\.]+", p)
                if match:
                    p_nums.append(float(match[0]))
            if p_nums:
                min_p, max_p = min(p_nums), max(p_nums)
                price_str = f"{min_p}万" if min_p == max_p else f"{min_p}～{max_p}万"

        # 轴长比 (空间得房率指标，基于中位数或主尺寸)
        rep_len = min_len
        rep_wb = min_wb
        ratio = round((rep_wb / rep_len) * 100, 1) if rep_len else 0

        aggregated.append({
            "series_id": sid,
            "brand": s["brand"],
            "series": s["series"],
            "level": s["level"],
            "energy_types": sorted(list(s["energy_types"])),
            "body_structures": sorted(list(s["body_structures"])),
            "length_min": min_len,
            "length_max": max_len,
            "length_str": len_str,
            "width_min": min_wid,
            "width_max": max_wid,
            "width_str": wid_str,
            "height_min": min_hei,
            "height_max": max_hei,
            "height_str": hei_str,
            "wheelbase_min": min_wb,
            "wheelbase_max": max_wb,
            "wheelbase_str": wb_str,
            "ratio": ratio,
            "price_str": price_str,
            "version_count": len(s["versions"]),
            "versions": s["versions"]
        })
    return aggregated

if __name__ == "__main__":
    all_cars = []
    seen_specs = set()
    for s in POPULAR_SERIES:
        items = fetch_series_data_with_retry(s)
        for item in items:
            if item["spec_id"] not in seen_specs:
                seen_specs.add(item["spec_id"])
                all_cars.append(item)
        time.sleep(0.3)
    
    os.makedirs("car_dimension_filter/data", exist_ok=True)
    out_json = "car_dimension_filter/data/cars.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(all_cars, f, ensure_ascii=False, indent=2)

    # 生成车系聚合数据
    aggregated_series = aggregate_by_series(all_cars)
    out_series_json = "car_dimension_filter/data/series.json"
    with open(out_series_json, "w", encoding="utf-8") as f:
        json.dump(aggregated_series, f, ensure_ascii=False, indent=2)

    # 导出 SQLite
    out_db = "car_dimension_filter/data/cars.db"
    conn = sqlite3.connect(out_db)
    cur = conn.cursor()
    cur.execute('''
    CREATE TABLE IF NOT EXISTS vehicles (
        spec_id INTEGER PRIMARY KEY,
        series_id INTEGER,
        brand TEXT,
        series TEXT,
        model_name TEXT,
        level TEXT,
        energy_type TEXT,
        body_structure TEXT,
        length_mm INTEGER,
        width_mm INTEGER,
        height_mm INTEGER,
        wheelbase_mm INTEGER,
        curb_weight_kg INTEGER,
        price TEXT
    )
    ''')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_dims ON vehicles(length_mm, width_mm, height_mm, wheelbase_mm)')

    for c in all_cars:
        cur.execute('''
        INSERT OR REPLACE INTO vehicles VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        ''', (
            c["spec_id"], c["series_id"], c["brand"], c["series"], c["model_name"],
            c["level"], c["energy_type"], c["body_structure"],
            c["length"], c["width"], c["height"], c["wheelbase"],
            c["weight"], c["price"]
        ))
        
    cur.execute('''
    CREATE TABLE IF NOT EXISTS series (
        series_id INTEGER PRIMARY KEY,
        brand TEXT,
        series TEXT,
        level TEXT,
        length_min INTEGER,
        length_max INTEGER,
        width_min INTEGER,
        width_max INTEGER,
        height_min INTEGER,
        height_max INTEGER,
        wheelbase_min INTEGER,
        wheelbase_max INTEGER,
        version_count INTEGER,
        price_str TEXT
    )
    ''')
    for s in aggregated_series:
        cur.execute('''
        INSERT OR REPLACE INTO series VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        ''', (
            s["series_id"], s["brand"], s["series"], s["level"],
            s["length_min"], s["length_max"], s["width_min"], s["width_max"],
            s["height_min"], s["height_max"], s["wheelbase_min"], s["wheelbase_max"],
            s["version_count"], s["price_str"]
        ))

    conn.commit()
    conn.close()
    
    print(f"\n==========================================")
    print(f"全量抓取与聚合完成！")
    print(f"总车款规格: {len(all_cars)} 款")
    print(f"车系聚合数: {len(aggregated_series)} 个热门车系")
    print(f"规格详情已保存: {out_json}")
    print(f"车系聚合已保存: {out_series_json}")
    print(f"SQLite 数据库已更新: {out_db}")
