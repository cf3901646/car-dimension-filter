import requests
import json
import csv
import re
import os
import sys
import time
import sqlite3
import concurrent.futures

# Windows 终端控制台 utf-8 编码兼容
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

CATALOG_PATH = "car_dimension_filter/data/brands_series_catalog.csv"
DB_PATH = "car_dimension_filter/data/cars.db"
CARS_JSON_PATH = "car_dimension_filter/data/cars.json"
SERIES_JSON_PATH = "car_dimension_filter/data/series.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def init_db(db_path):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("PRAGMA journal_mode=WAL")
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
    cur.execute('CREATE INDEX IF NOT EXISTS idx_series_id ON vehicles(series_id)')

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
    conn.commit()
    return conn

def get_already_downloaded_series(conn):
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT series_id FROM vehicles")
    return set(row[0] for row in cur.fetchall())

def parse_catalog():
    if not os.path.exists(CATALOG_PATH):
        raise FileNotFoundError(f"找不到目录文件: {CATALOG_PATH}")

    with open(CATALOG_PATH, "r", encoding="utf-8") as f:
        rows = list(csv.reader(f))

    series_list = []
    for r in rows:
        if len(r) >= 2:
            name_raw = r[0].strip()
            id_part = r[1].strip()
            match = re.search(r'series_(\d+)', id_part)
            if match:
                sid = int(match.group(1))
                # 清洗名称：去除尾部的在售数量标识如 (44)
                clean_name = re.sub(r'\s*\(\d+\)$', '', name_raw).strip()
                is_stopped = "停售" in name_raw
                series_list.append({
                    "series_id": sid,
                    "name": clean_name,
                    "is_stopped": is_stopped
                })
    return series_list

def fetch_single_series(series_item, max_retries=2):
    sid = series_item["series_id"]
    series_name = series_item["name"]
    url = f"https://car.m.autohome.com.cn/ashx/car/GetModelConfigNew.ashx?seriesId={sid}"
    
    session = requests.Session()
    session.trust_env = False  # 绕过环境变量代理直连

    data = None
    for attempt in range(max_retries):
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
        for item in (group.get("paramitems") or []):
            param_map[item.get("name")] = item.get("valueitems") or []

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

    # 推断品牌（从车系名称前缀或基本信息）
    brand = series_name.split()[0] if " " in series_name else series_name[:4]

    results = []
    for i, m_item in enumerate(model_names):
        spec_id = m_item.get("specid")
        m_name = m_item.get("value", "")

        def get_val(arr):
            if i < len(arr):
                return arr[i].get("value", "")
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
            results.append({
                "spec_id": spec_id,
                "series_id": sid,
                "brand": brand,
                "series": series_name,
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

def save_batch_to_db(conn, batch_cars):
    if not batch_cars:
        return
    cur = conn.cursor()
    cur.executemany('''
    INSERT OR REPLACE INTO vehicles VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    ''', [
        (
            c["spec_id"], c["series_id"], c["brand"], c["series"], c["model_name"],
            c["level"], c["energy_type"], c["body_structure"],
            c["length"], c["width"], c["height"], c["wheelbase"],
            c["weight"], c["price"]
        ) for c in batch_cars
    ])
    conn.commit()

def dump_all_data(conn):
    cur = conn.cursor()
    cur.execute("SELECT * FROM vehicles")
    cols = [desc[0] for desc in cur.description]
    all_vehicles = [dict(zip(cols, row)) for row in cur.fetchall()]

    # 规范化键名
    normalized_cars = []
    for v in all_vehicles:
        normalized_cars.append({
            "spec_id": v["spec_id"],
            "series_id": v["series_id"],
            "brand": v["brand"],
            "series": v["series"],
            "model_name": v["model_name"],
            "level": v["level"],
            "energy_type": v["energy_type"],
            "body_structure": v["body_structure"],
            "length": v["length_mm"],
            "width": v["width_mm"],
            "height": v["height_mm"],
            "wheelbase": v["wheelbase_mm"],
            "weight": v["curb_weight_kg"],
            "price": v["price"]
        })

    with open(CARS_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(normalized_cars, f, ensure_ascii=False, indent=2)

    # 聚合车系
    from fetch_cars import aggregate_by_series
    aggregated = aggregate_by_series(normalized_cars)
    with open(SERIES_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(aggregated, f, ensure_ascii=False, indent=2)

    # 更新 series 表
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
    for s in aggregated:
        cur.execute('''
        INSERT OR REPLACE INTO series VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        ''', (
            s["series_id"], s["brand"], s["series"], s["level"],
            s["length_min"], s["length_max"], s["width_min"], s["width_max"],
            s["height_min"], s["height_max"], s["wheelbase_min"], s["wheelbase_max"],
            s["version_count"], s["price_str"]
        ))
    conn.commit()
    print(f"[Dump] 已导出全量车型 JSON: {len(normalized_cars)} 款，车系: {len(aggregated)} 个")

def main():
    conn = init_db(DB_PATH)
    already_downloaded = get_already_downloaded_series(conn)
    catalog = parse_catalog()

    # 优先下载在售车系（去除停售），然后再下载历史车系
    active_series = [s for s in catalog if not s["is_stopped"]]
    stopped_series = [s for s in catalog if s["is_stopped"]]
    ordered_series = active_series + stopped_series

    to_download = [s for s in ordered_series if s["series_id"] not in already_downloaded]
    total_to_download = len(to_download)

    print(f"=== 全量车型规格数据批量下载引擎启动 ===")
    print(f"车系总目录数: {len(catalog)}")
    print(f"其中在售车系: {len(active_series)}，停售车系: {len(stopped_series)}")
    print(f"已入库车系: {len(already_downloaded)}")
    print(f"本次待下载车系: {total_to_download}")
    print(f"并发线程数: 6\n")

    batch_cars = []
    success_count = 0
    start_time = time.time()

    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
        # 分批提交
        future_to_series = {executor.submit(fetch_single_series, s): s for s in to_download}
        
        for idx, future in enumerate(concurrent.futures.as_completed(future_to_series), 1):
            s_item = future_to_series[future]
            try:
                sid, cars = future.result()
                if cars:
                    batch_cars.extend(cars)
                    success_count += 1
            except Exception as e:
                pass

            # 每 20 个车系写一次数据库
            if len(batch_cars) >= 100 or idx == total_to_download:
                save_batch_to_db(conn, batch_cars)
                batch_cars = []

            # 打印进度
            if idx % 50 == 0 or idx == total_to_download:
                elapsed = time.time() - start_time
                speed = idx / elapsed if elapsed > 0 else 0
                remain = (total_to_download - idx) / speed if speed > 0 else 0
                print(f"[{idx}/{total_to_download}] 进度: {(idx/total_to_download)*100:.1f}%, 成功解析车系: {success_count}, 耗时: {elapsed:.0f}s, 预计剩余: {remain:.0f}s")

            # 每 200 个车系做一次完整 Dump
            if idx % 200 == 0:
                dump_all_data(conn)

    # 最终保存与重建
    dump_all_data(conn)
    conn.close()

    # 重新构建前端静态页面
    print("\n[Build] 正在重新编译前端 index.html 页面...")
    import subprocess
    subprocess.run([sys.executable, "car_dimension_filter/build_html.py"], check=True)
    print("[Build] 前端页面重新构建完成！")
    print(f"=== 全量数据下载与打包圆满完成！总耗时: {time.time() - start_time:.1f}s ===")

if __name__ == "__main__":
    main()
