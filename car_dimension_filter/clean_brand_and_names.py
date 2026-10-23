# -*- coding: utf-8 -*-
"""
Cleans brand names, series names, and fixes redundant prefix concatenation across series.json
"""
import json
import re
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

SERIES_PATH = "car_dimension_filter/data/series.json"
series_list = json.load(open(SERIES_PATH, encoding="utf-8"))

# 知名品牌与车系别名规范化映射
BRAND_NORM_MAP = {
    "腾势汽车": "腾势",
    "小米汽车": "小米",
    "极氪汽车": "极氪",
    "小鹏汽车": "小鹏",
    "理想汽车": "理想",
    "蔚来汽车": "蔚来",
    "智己汽车": "智己",
    "岚图汽车": "岚图",
    "深蓝汽车": "深蓝",
    "广汽埃安": "埃安",
    "吉利汽车": "吉利",
    "长安汽车": "长安",
    "长城汽车": "长城",
    "奇瑞汽车": "奇瑞",
    "广汽传祺": "传祺",
    "五菱汽车": "五菱",
    "江淮汽车": "江淮",
    "东风汽车": "东风",
    "江铃汽车": "江铃",
    "易至EV3": "易至汽车",
    "羿驰05": "江铃羿驰",
    "方程S": "方程豹",
    "车驰V系列": "车驰",
    "锐际新能源": "福特",
    "领界EV": "福特",
    "焕驰": "起亚",
    "名图新能源": "现代",
    "名图": "现代",
    "迈莎锐G级": "迈莎锐",
    "迈莎锐V级": "迈莎锐",
    "奕歌": "三菱",
    "智跑": "起亚",
    "总裁": "玛莎拉蒂",
}

for s in series_list:
    sid = s.get("series_id")
    b = (s.get("brand") or s.get("brand_name") or "").strip()
    ser = (s.get("series") or s.get("clean_series_name") or "").strip()

    # 1. 应用规范品牌映射
    if b in BRAND_NORM_MAP:
        b = BRAND_NORM_MAP[b]

    # 2. 如果 brand 和 series 一模一样
    if b == ser:
        # 尝试从具体年款提取真实车名
        versions = s.get("versions") or []
        if versions:
            vn0 = versions[0].get("model_name", "")
            # 例如 "易至EV3 2023款 青春版"
            tokens = vn0.split()
            if len(tokens) >= 2:
                # 提取年款之前的名字
                m_lead = re.split(r'\d{4}款', vn0)[0].strip()
                if m_lead and m_lead != ser:
                    ser = m_lead

    # 3. 剥离 series 里面冗余的品牌前缀
    # 比如 brand: "奥迪", series: "奥迪A6L e-tron" -> 纯净名: "A6L e-tron"
    # brand: "腾势", series: "腾势Z9S" -> "Z9S"
    # brand: "宝马", series: "宝马3系" -> "3系"
    # brand: "奔驰", series: "奔驰E级" -> "E级"
    # brand: "比亚迪", series: "比亚迪海豹07 EV" -> "海豹07 EV"
    clean_ser = ser
    prefixes_to_strip = [b, b + "汽车", b + "牌", b + "·", "比亚迪", "吉利", "长安", "奇瑞", "长城"]
    for pfx in prefixes_to_strip:
        if pfx and clean_ser.startswith(pfx) and len(clean_ser) > len(pfx):
            sub = clean_ser[len(pfx):].strip()
            if sub and len(sub) >= 2:
                clean_ser = sub
                break

    # 特殊修复：方程S -> 方程豹 豹5 / 豹8
    if "方程S" in ser:
        clean_ser = "豹5"
        b = "方程豹"

    s["brand"] = b
    s["brand_name"] = b
    s["series"] = ser
    s["series_name"] = ser
    s["display_series_name"] = clean_ser  # 纯净展示名

with open(SERIES_PATH, "w", encoding="utf-8") as f:
    json.dump(series_list, f, ensure_ascii=False, indent=2)

print("Successfully cleaned brands and series names!")
