import requests
import json
import re
import sys
import sqlite3

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

POPULAR_MISSING = [
    {"series_id": 7207, "series": "问界M9", "brand": "鸿蒙智行"},
    {"series_id": 6962, "series": "小米SU7", "brand": "小米汽车"},
    {"series_id": 7915, "series": "小米SU7 Ultra", "brand": "小米汽车"},
    {"series_id": 5499, "series": "汉", "brand": "比亚迪"},
    {"series_id": 6910, "series": "理想L8", "brand": "理想汽车"},
    {"series_id": 7515, "series": "理想L6", "brand": "理想汽车"},
    {"series_id": 6736, "series": "理想L9", "brand": "理想汽车"},
    {"series_id": 7384, "series": "理想MEGA", "brand": "理想汽车"},
    {"series_id": 7698, "series": "极氪001 FR", "brand": "极氪"},
    {"series_id": 7453, "series": "极氪007", "brand": "极氪"},
    {"series_id": 7780, "series": "极氪7X", "brand": "极氪"},
    {"series_id": 5833, "series": "坦克300", "brand": "坦克"},
    {"series_id": 6393, "series": "坦克500", "brand": "坦克"},
    {"series_id": 6712, "series": "腾势D9", "brand": "腾势汽车"},
    {"series_id": 4983, "series": "蔚来ES6", "brand": "蔚来"},
    {"series_id": 6598, "series": "蔚来ET5", "brand": "蔚来"},
]

session = requests.Session()
session.trust_env = False

conn = sqlite3.connect("car_dimension_filter/data/cars.db")
cur = conn.cursor()

new_cars = []
for item in POPULAR_MISSING:
    sid = item["series_id"]
    sname = item["series"]
    brand = item["brand"]
    url = f"https://car.m.autohome.com.cn/ashx/car/GetModelConfigNew.ashx?seriesId={sid}"
    try:
        r = session.get(url, headers=HEADERS, timeout=8)
        if r.status_code != 200:
            print(f"[-] 失败 {brand} {sname} (HTTP {r.status_code})")
            continue
        data = r.json()
    except Exception as e:
        print(f"[-] 超时或异常 {brand} {sname}: {e}")
        continue

    param_map = {}
    for group in (data.get("param") or []):
        for pitem in (group.get("paramitems") or []):
            param_map[pitem.get("name")] = pitem.get("valueitems") or []

    model_names = param_map.get("车型名称") or []
    lengths = param_map.get("长度(mm)", [])
    widths = param_map.get("宽度(mm)", [])
    heights = param_map.get("高度(mm)", [])
    wheelbases = param_map.get("轴距(mm)", [])
    levels = param_map.get("级别", [])
    energies = param_map.get("能源类型", [])
    structures = param_map.get("车身结构", [])
    weights = param_map.get("整备质量(kg)", [])
    prices = param_map.get("厂商指导价(元)", [])

    count = 0
    for i, m_item in enumerate(model_names):
        spec_id = m_item.get("specid")
        m_name = m_item.get("value", "")

        def get_val(arr):
            if i < len(arr): return arr[i].get("value", "")
            return ""

        def parse_int(v):
            digits = re.findall(r"\d+", str(v))
            return int(digits[0]) if digits else None

        len_val = parse_int(get_val(lengths))
        wid_val = parse_int(get_val(widths))
        hei_val = parse_int(get_val(heights))
        wb_val = parse_int(get_val(wheelbases))
        weight_val = parse_int(get_val(weights))

        if len_val and wid_val and hei_val and wb_val:
            car_entry = (
                spec_id, sid, brand, sname, m_name,
                get_val(levels), get_val(energies), get_val(structures),
                len_val, wid_val, hei_val, wb_val,
                weight_val, get_val(prices)
            )
            cur.execute("INSERT OR REPLACE INTO vehicles VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)", car_entry)
            new_cars.append(car_entry)
            count += 1
    print(f"[+] 成功抓取补充: {brand} {sname} (SID: {sid}) 共 {count} 款配置")

conn.commit()
conn.close()
print(f"补充完毕！共成功入库 {len(new_cars)} 款热门车型。")
