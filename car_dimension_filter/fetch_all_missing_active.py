import sqlite3
import csv
import re
import os
import sys
import time
import requests
import concurrent.futures

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

CATALOG_PATH = "car_dimension_filter/data/brands_series_catalog.csv"
DB_PATH = "car_dimension_filter/data/cars.db"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1"
}

def get_missing_active_series():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT series_id FROM vehicles")
    downloaded = set(r[0] for r in cur.fetchall())
    conn.close()

    active_missing = []
    with open(CATALOG_PATH, "r", encoding="utf-8") as f:
        for r in csv.reader(f):
            if len(r) >= 2 and "停售" not in r[0]:
                m = re.search(r'series_(\d+)', r[1])
                if m:
                    sid = int(m.group(1))
                    if sid not in downloaded:
                        clean = re.sub(r'\s*\(\d+\)$', '', r[0]).strip()
                        active_missing.append({"series_id": sid, "name": clean})
    return active_missing

def fetch_single(item):
    sid = item["series_id"]
    name = item["name"]
    url = f"https://car.m.autohome.com.cn/ashx/car/GetModelConfigNew.ashx?seriesId={sid}"

    session = requests.Session()
    session.trust_env = False

    data = None
    for attempt in range(2):
        try:
            resp = session.get(url, headers=HEADERS, timeout=8)
            if resp.status_code == 200:
                data = resp.json()
                break
        except Exception:
            time.sleep(0.5)

    if not data or not isinstance(data, dict):
        return sid, []

    param_map = {}
    for group in (data.get("param") or []):
        for pitem in (group.get("paramitems") or []):
            param_map[pitem.get("name")] = pitem.get("valueitems") or []

    model_names = param_map.get("车型名称") or []
    if not model_names:
        return sid, []

    lengths = param_map.get("长度(mm)", [])
    widths = param_map.get("宽度(mm)", [])
    heights = param_map.get("高度(mm)", [])
    wheelbases = param_map.get("轴距(mm)", [])
    levels = param_map.get("级别", [])
    energies = param_map.get("能源类型", [])
    structures = param_map.get("车身结构", [])
    weights = param_map.get("整备质量(kg)", [])
    prices = param_map.get("厂商指导价(元)", [])

    brand = name.split()[0] if " " in name else name[:4]

    results = []
    for i, m_item in enumerate(model_names):
        spec_id = m_item.get("specid")
        m_name = m_item.get("value", "")

        def get_val(arr):
            return arr[i].get("value", "") if i < len(arr) else ""

        def parse_int(v):
            digits = re.findall(r"\d+", str(v))
            return int(digits[0]) if digits else None

        len_val = parse_int(get_val(lengths))
        wid_val = parse_int(get_val(widths))
        hei_val = parse_int(get_val(heights))
        wb_val = parse_int(get_val(wheelbases))
        weight_val = parse_int(get_val(weights))

        if len_val and wid_val and hei_val and wb_val:
            results.append({
                "spec_id": spec_id,
                "series_id": sid,
                "brand": brand,
                "series": name,
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
    return sid, results

def main():
    missing = get_missing_active_series()
    print(f"待抓取的在售缺失车系共: {len(missing)} 个")
    if not missing:
        print("所有在售车系已全部就绪！")
        return

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("PRAGMA journal_mode=WAL")

    total = len(missing)
    batch = []
    success_sids = 0
    total_specs = 0
    start = time.time()

    # 使用 10 线程并发抓取
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_to_item = {executor.submit(fetch_single, item): item for item in missing}

        for idx, future in enumerate(concurrent.futures.as_completed(future_to_item), 1):
            try:
                sid, cars = future.result()
                if cars:
                    batch.extend(cars)
                    success_sids += 1
                    total_specs += len(cars)
            except Exception:
                pass

            if len(batch) >= 100 or idx == total:
                cur.executemany('''
                INSERT OR REPLACE INTO vehicles VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                ''', [
                    (
                        c["spec_id"], c["series_id"], c["brand"], c["series"], c["model_name"],
                        c["level"], c["energy_type"], c["body_structure"],
                        c["length"], c["width"], c["height"], c["wheelbase"],
                        c["weight"], c["price"]
                    ) for c in batch
                ])
                conn.commit()
                batch = []

            if idx % 50 == 0 or idx == total:
                elapsed = time.time() - start
                print(f"[{idx}/{total}] 进度: {(idx/total)*100:.1f}%, 成功解析车系: {success_sids}, 新增配置: {total_specs}, 耗时: {elapsed:.0f}s")

    conn.close()
    print(f"全量在售补充抓取完毕！共耗时 {time.time()-start:.1f} 秒，新增 {success_sids} 个车系，{total_specs} 款车型配置。")

if __name__ == "__main__":
    main()
