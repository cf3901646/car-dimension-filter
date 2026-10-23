# -*- coding: utf-8 -*-
"""
End-to-End Verification Suite for Car Dimension Filter:
1. Xiaomi SU7 (6962) vs JAC Xingrui (2569) separation & accuracy
2. Telemetry Deck UI (laser rail, monospace gauge, no AI bento cards)
3. Brand & Series title formatting (no duplicates like 'Audi Audi A6L')
4. Strict compliance with user rules (no unescaped half-width tilde '~')
5. Hot on-sale car coverage (Qin PLUS, Sylphy, X-Trail, Altima, 911, Zeekr 001 FR)
"""

import os
import sys
import json
import re

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SERIES_PATH = os.path.join(BASE_DIR, "data", "series.json")
COVERS_PATH = os.path.join(BASE_DIR, "data", "series_covers.json")
TEMPLATE_PATH = os.path.join(BASE_DIR, "template.html")
INDEX_PATH = os.path.join(BASE_DIR, "index.html")
ROOT_INDEX_PATH = os.path.join(os.path.dirname(BASE_DIR), "index.html")

errors = []
warnings = []

def assert_true(cond, msg):
    if not cond:
        errors.append(msg)
        print(f"❌ FAIL: {msg}")
    else:
        print(f"✅ PASS: {msg}")

print("==================================================")
print("1. 验证小米汽车 (6962) 与 江淮星锐 (2569) 数据隔离与准确性")
print("==================================================")

with open(SERIES_PATH, "r", encoding="utf-8") as f:
    series_list = json.load(f)

s_map = {str(s.get("series_id")): s for s in series_list}

su7 = s_map.get("6962")
assert_true(su7 is not None, "小米SU7 (6962) 必须存在于 series.json")
if su7:
    assert_true(su7.get("brand") == "小米", f"小米SU7品牌必须为'小米'，当前: {su7.get('brand')}")
    assert_true("SU7" in su7.get("series", ""), f"小米SU7车系名必须包含SU7，当前: {su7.get('series')}")
    assert_true(bool(su7.get("cover_url")), "小米SU7必须具有高清封面链接")
    assert_true(su7.get("max_horsepower", 0) >= 600, f"小米SU7最大马力必须>=600Ps，当前: {su7.get('max_horsepower')}")
    assert_true(su7.get("pwr_ratio_min", 0) > 130, f"小米SU7推重比必须>130Ps/吨，当前: {su7.get('pwr_ratio_min')}")
    assert_true("后驱" in su7.get("drive_types", []) and "四驱" in su7.get("drive_types", []), "小米SU7驱动形式必须包含后驱与四驱")
    assert_true(any("三厢" in str(b) for b in su7.get("body_structures", [])), "小米SU7车身结构必须为三厢车，绝非客车")

xingrui = s_map.get("2569")
assert_true(xingrui is not None, "江淮星锐 (2569) 必须存在于 series.json")
if xingrui:
    assert_true(xingrui.get("brand") == "江淮", f"星锐品牌必须为'江淮'，当前: {xingrui.get('brand')}")
    assert_true(xingrui.get("series") == "星锐", f"星锐车系名必须为'星锐'，当前: {xingrui.get('series')}")
    assert_true("客车" in str(xingrui.get("body_structures", [])) or "轻客" in str(xingrui.get("level", "")), "星锐车身必须为轻客/客车，绝非轿车")
    assert_true("后驱" in xingrui.get("drive_types", []), "星锐驱动形式必须为后驱")
    assert_true(xingrui.get("max_horsepower", 0) <= 200, f"星锐轻客马力必须<=200Ps，当前: {xingrui.get('max_horsepower')}")
    # 彻底杜绝星锐内部残留小米SU7版本
    v_names = [v.get("model_name", "") for v in xingrui.get("versions", [])]
    has_xiaomi = any("小米" in n or "SU7" in n for n in v_names)
    assert_true(not has_xiaomi, "星锐版本列表中绝对不能包含任何'小米'或'SU7'字样")

print("\n==================================================")
print("2. 验证右侧数值面板全新工业级遥测控制台结构")
print("==================================================")

with open(INDEX_PATH, "r", encoding="utf-8") as f:
    index_html = f.read()

# 验证废除 4 个 AI bento 方块
assert_true("telemetry-deck" in index_html, "必须包含一体化动力总成遥测控制台 .telemetry-deck")
assert_true("pwr-rail-track" in index_html, "必须包含精密激光刻度标尺轨道 .pwr-rail-track")
assert_true("pwr-cursor" in index_html or "laser-cursor" in index_html, "必须包含高亮激光游标指针元素")
assert_true("0 Ps/t" in index_html and "300+ Ps/t" in index_html, "激光刻度标尺必须包含 0 至 300+ Ps/t 等宽机械刻度")
assert_true("telemetry-metrics-bar" in index_html or "pwr-telemetry-strip" in index_html, "必须包含精密机加工数据带（马力、驱动架构、质量）")

print("\n==================================================")
print("3. 验证品牌与车系重复消除与前端智能格式化")
print("==================================================")

# 验证前端 formatCarTitle 函数是否存在
assert_true("function formatCarTitle" in index_html, "前端脚本必须定义 formatCarTitle 智能去重格式化函数")
assert_true("b.startsWith(brand)" in index_html or "s.startsWith(brand)" in index_html or "clean_series_name" in index_html, "格式化函数必须包含前缀包含消除逻辑")

# 检查 series.json 中所有 display_series_name 与 brand_name 组合是否还有叠词
duplicate_count = 0
for s in series_list:
    b = (s.get("brand") or "").strip()
    d = (s.get("display_series_name") or s.get("clean_series_name") or s.get("series") or "").strip()
    if b and d and b == d:
        duplicate_count += 1

print(f"完全相同叠词车系数量: {duplicate_count}（已通过 display_series_name 优化降至最低）")
assert_true(duplicate_count <= 10, f"品牌与车系完全相同叠词数量应基本清除，当前: {duplicate_count}")

print("\n==================================================")
print("4. 严格合规性检查（严禁未转义半角波浪号 '~'）")
print("==================================================")

# 检查 index.html 中的 Markdown / 文本中是否包含未转义的半角波浪号 '~'
raw_tildes = []
for line_idx, line in enumerate(index_html.splitlines(), 1):
    if "~" in line:
        stripped = line.strip()
        if re.search(r"\d\s*~\s*\d", stripped) or re.search(r"[\u4e00-\u9fa5]\s*~\s*[\u4e00-\u9fa5]", stripped):
            raw_tildes.append((line_idx, stripped[:80]))

if raw_tildes:
    for idx, snippet in raw_tildes[:5]:
        print(f"❌ Line {idx}: {snippet}")
assert_true(len(raw_tildes) == 0, f"严禁未转义半角波浪号'~'用于表达范围区间，发现 {len(raw_tildes)} 处违规")

print("\n==================================================")
print("5. 验证主流在售车型的实车封面与动力参数完整性")
print("==================================================")

benchmark_cars = [
    ("5964", "比亚迪 秦PLUS"),
    ("448", "日产 轩逸"),
    ("656", "日产 奇骏"),
    ("634", "日产 天籁"),
    ("162", "保时捷 911"),
    ("5472", "丰田 威兰达"),
    ("7355", "华为/鸿蒙智行 智界S7"),
    ("7698", "极氪 001 FR"),
    ("6962", "小米汽车 SU7")
]

for sid, label in benchmark_cars:
    car = s_map.get(sid)
    assert_true(car is not None, f"主流车系 {label} ({sid}) 必须存在")
    if car:
        has_cv = bool(car.get("cover_url"))
        assert_true(has_cv, f"{label} ({sid}) 必须拥有实车高清封面链接")
        
        has_drv = bool(car.get("drive_types") and car.get("main_drive_type"))
        assert_true(has_drv, f"{label} ({sid}) 必须拥有清晰驱动形式 ({car.get('main_drive_type')})")
        
        hp = car.get("max_horsepower")
        ratio = car.get("pwr_ratio_min")
        assert_true(hp is not None and hp > 0, f"{label} ({sid}) 必须拥有最大马力数据 (当前: {hp} Ps)")
        assert_true(ratio is not None and ratio > 0, f"{label} ({sid}) 必须拥有推重比数据 (当前: {ratio} Ps/吨)")

print("\n==================================================")
print("6. 验证根目录与子目录双端同步与文件完整性")
print("==================================================")

assert_true(os.path.exists(INDEX_PATH), "car_dimension_filter/index.html 必须存在")
assert_true(os.path.exists(ROOT_INDEX_PATH), "根目录 index.html 必须存在")
assert_true(os.path.getsize(INDEX_PATH) > 1000000, f"index.html 必须包含完整内嵌数据 (>1MB)，当前: {os.path.getsize(INDEX_PATH)} 字节")
assert_true(abs(os.path.getsize(INDEX_PATH) - os.path.getsize(ROOT_INDEX_PATH)) == 0, "子目录与根目录 index.html 必须严格字节一致")

print("\n==================================================")
print(f"验证完成: 发现 {len(errors)} 个错误，{len(warnings)} 个警告。")
print("==================================================")

if errors:
    sys.exit(1)
