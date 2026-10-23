import hashlib
import json
import os
import re
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "series.json")
TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), "template.html")
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "index.html")

with open(DATA_PATH, "r", encoding="utf-8") as f:
    series_data = json.load(f)

# 从 price_str（如 "21.59～29.99万"、"118.0万"）解析出数值价格区间，供价格筛选与排序使用
price_filled = 0
for s in series_data:
    if s.get("price_min") is None:
        nums = [float(x) for x in re.findall(r"\d+(?:\.\d+)?", s.get("price_str") or "")]
        if nums:
            s["price_min"] = min(nums)
            s["price_max"] = max(nums)
            price_filled += 1
print(f"Parsed price range for {price_filled} series from price_str.")

# 注入官方封面图片链接
COVERS_PATH = os.path.join(os.path.dirname(__file__), "data", "series_covers.json")
cover_count = 0
if os.path.exists(COVERS_PATH):
    try:
        with open(COVERS_PATH, "r", encoding="utf-8") as f:
            covers = json.load(f)
        for s in series_data:
            s["brand_name"] = s.get("brand") or s.get("brand_name") or ""
            s["series_name"] = s.get("series") or s.get("clean_series_name") or s.get("series_name") or ""
            sid_str = str(s.get("series_id"))
            if sid_str in covers and covers[sid_str]:
                s["cover_url"] = covers[sid_str]
                cover_count += 1
    except Exception as e:
        print(f"Warning: could not inject covers: {e}")

# 注入动态爬取的规格扩展数据 (评分、驱动、推重比、续航等)
ENRICH_PATH = os.path.join(os.path.dirname(__file__), "data", "series_enriched_cache.json")
enriched_count = 0
if os.path.exists(ENRICH_PATH):
    try:
        with open(ENRICH_PATH, "r", encoding="utf-8") as f:
            enrich_cache = json.load(f)
        for s in series_data:
            sid_str = str(s.get("series_id"))
            if sid_str in enrich_cache:
                enriched_count += 1
                c_item = enrich_cache[sid_str]
                s["score"] = c_item.get("score")
                
                v_cache = c_item.get("versions", {})
                drives_set = set()
                ratios_list = []
                ranges_list = []
                hp_list = []
                
                for v in s.get("versions", []):
                    v_key = str(v.get("spec_id"))
                    if v_key not in v_cache:
                        v_key = v.get("model_name")
                    
                    v_info = v_cache.get(v_key, {})
                    drv = v_info.get("drive_type") or None  # 缓存里没有就留空，页面显示“未知”，不再默认成前驱
                    v["drive_type"] = drv
                    v["horsepower"] = v_info.get("horsepower")
                    if v_info.get("weight"):
                        v["weight"] = v_info.get("weight")
                    v["pwr_ratio"] = v_info.get("pwr_ratio")
                    v["ev_range"] = v_info.get("ev_range")
                    
                    if drv: drives_set.add(drv)
                    if v.get("pwr_ratio"): ratios_list.append(v["pwr_ratio"])
                    if v.get("ev_range"): ranges_list.append(v["ev_range"])
                    if v.get("horsepower"): hp_list.append(v["horsepower"])
                
                s["drive_types"] = sorted(list(drives_set))
                s["main_drive_type"] = "四驱" if "四驱" in s["drive_types"] else (s["drive_types"][0] if s["drive_types"] else None)
                
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
                    s["pwr_ratio_str"] = ""
                
                if ranges_list:
                    s["range_min"] = min(ranges_list)
                    s["range_max"] = max(ranges_list)
                    if s["range_min"] == s["range_max"]:
                        s["range_str"] = f"{s['range_min']}km"
                    else:
                        s["range_str"] = f"{s['range_min']}～{s['range_max']}km"
                else:
                    s["range_min"] = None
                    s["range_max"] = None
                    s["range_str"] = ""
                
                s["max_horsepower"] = max(hp_list) if hp_list else None
    except Exception as e:
        print(f"Warning: could not inject enriched specs: {e}")

# 统计总版本数与在售数
total_versions = sum(s.get("version_count", 0) for s in series_data)
active_series_count = sum(1 for s in series_data if not s.get("is_stopped"))
stopped_series_count = len(series_data) - active_series_count

print(f"Loaded {cover_count} covers, {enriched_count} enriched series from cache.")

# 285 个车系抓取时没拿到品牌，品牌名被填成了车系名，显示名又多了“车系”两个字（如“钧天勇猛者车系”）。
# 真实品牌要重新抓取才能补；这里先去掉多余的“车系”，页面在品牌与车系同名时只显示一次。
no_brand = 0
for s in series_data:
    if s.get("brand_name") and s.get("brand_name") == s.get("series_name"):
        no_brand += 1
        d = s.get("display_series_name") or ""
        if d.endswith("车系"):
            s["display_series_name"] = s["series_name"]
print(f"{no_brand} series have no real brand (brand_name == series_name)")

# 同一品牌下车系重名（清洗名字时出错，例如方程S 被写成了豹5）：改用配置数据里的车系名。
# 必须放在封面注入之后，因为那一步会用原始字段重写 series_name。
from collections import Counter
name_count = Counter((s.get("brand_name"), s.get("series_name")) for s in series_data)
for s in series_data:
    if name_count[(s.get("brand_name"), s.get("series_name"))] < 2:
        continue
    v_names = {v.get("series") for v in s.get("versions", []) if v.get("series")}
    if len(v_names) == 1:
        real = v_names.pop()
        if real != s.get("series_name"):
            print(f"Renamed duplicate series {s['series_id']}: {s.get('series_name')} -> {real}")
            s["series_name"] = s["display_series_name"] = real

with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
    template_content = f.read()

# 内嵌构建期编译的 Tailwind CSS（不再依赖 cdn.tailwindcss.com）
# 生成方式：在仓库根目录执行 npm install && npm run build:css
CSS_PATH = os.path.join(os.path.dirname(__file__), "tailwind.generated.css")
CSS_PLACEHOLDER = "<!-- __INLINE_TAILWIND_CSS__ -->"
if CSS_PLACEHOLDER in template_content:
    if not os.path.exists(CSS_PATH):
        sys.exit("缺少 tailwind.generated.css，请先在仓库根目录执行 npm install && npm run build:css")
    with open(CSS_PATH, "r", encoding="utf-8") as f:
        template_content = template_content.replace(CSS_PLACEHOLDER, "<style>" + f.read() + "</style>")

# 注入数据与统计
html_content = template_content
html_content = html_content.replace("__TOTAL_SERIES__", str(len(series_data)))
html_content = html_content.replace("__ACTIVE_SERIES__", str(active_series_count))
html_content = html_content.replace("__STOPPED_SERIES__", str(stopped_series_count))
html_content = html_content.replace("__TOTAL_VERSIONS__", str(total_versions))

# 车型数据单独输出为 series-data.js：页面先显示骨架，再用 <script defer> 加载数据。
# 用 script 而不用 fetch，是为了本地双击打开 index.html（file://）时仍然可用。
# 只保留页面实际读取的字段，体积约为完整数据的一半。
SERIES_KEYS = (
    "series_id", "brand_name", "series_name", "display_series_name", "level", "energy_types",
    "drive_types", "main_drive_type", "price_str", "price_min", "price_max", "score", "is_stopped",
    "cover_url", "length_min", "length_max", "width_min", "width_max", "height_min", "height_max",
    "wheelbase_min", "wheelbase_max", "pwr_ratio_min", "pwr_ratio_max", "pwr_ratio_str",
    "range_min", "range_max", "range_str", "max_horsepower",
)
VERSION_KEYS = ("model_name", "price", "length", "width", "height", "wheelbase", "weight",
                "drive_type", "horsepower", "pwr_ratio", "ev_range")

def slim(s):
    out = {k: s[k] for k in SERIES_KEYS if s.get(k) not in (None, "", [])}
    out["is_stopped"] = bool(s.get("is_stopped"))
    out["versions"] = [{k: v[k] for k in VERSION_KEYS if v.get(k) not in (None, "")} for v in s.get("versions", [])]
    return out

data_js = "window.ALL_SERIES=" + json.dumps([slim(s) for s in series_data], ensure_ascii=False, separators=(",", ":")) + ";\n"
data_hash = hashlib.sha256(data_js.encode("utf-8")).hexdigest()[:10]
html_content = html_content.replace("__SERIES_DATA_SRC__", f"series-data.js?v={data_hash}")

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
for out_dir in (os.path.dirname(__file__), ROOT_DIR):
    with open(os.path.join(out_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(html_content)
    with open(os.path.join(out_dir, "series-data.js"), "w", encoding="utf-8") as f:
        f.write(data_js)

kb = lambda n: f"{n / 1024:.0f} KB"
print(f"index.html {kb(len(html_content.encode('utf-8')))} + series-data.js {kb(len(data_js.encode('utf-8')))}（v={data_hash}），已写入 car_dimension_filter/ 与仓库根目录")
print(f"共 {len(series_data)} 个车系（在售 {active_series_count} / 历史 {stopped_series_count}），{total_versions} 款具体配置。")
