import json
import re
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

KNOWN_BRAND_RULES = [
    # 豪华与超跑
    ("劳斯莱斯", ["劳斯莱斯", "幻影", "古思特", "库里南", "魅影", "曜影", "闪灵"]),
    ("宾利", ["宾利", "飞驰", "欧陆", "添越"]),
    ("兰博基尼", ["兰博基尼", "Urus", "Huracán", "Revuelto", "Aventador"]),
    ("法拉利", ["法拉利", "Roma", "296", "SF90", "Purosangue", "F8"]),
    ("阿斯顿·马丁", ["阿斯顿·马丁", "DBX", "Vantage", "DB11", "DB12", "DBS"]),
    ("保时捷", ["保时捷", "Panamera", "Macan", "Cayenne", "Taycan", "911", "718"]),
    ("玛莎拉蒂", ["玛莎拉蒂", "Grecale", "Ghibli", "Levante", "GranTurismo"]),
    ("迈凯伦", ["迈凯伦", "Artura", "720S", "750S"]),
    ("路虎", ["路虎", "揽胜", "卫士", "发现"]),
    ("捷豹", ["捷豹", "F-PACE", "XFL", "XEL", "E-PACE"]),
    
    # 德系与美日欧豪华
    ("奔驰", ["奔驰", "梅赛德斯", "迈巴赫", "AMG"]),
    ("宝马", ["宝马", "BMW", "MINI"]),
    ("奥迪", ["奥迪", "AUDI"]),
    ("雷克萨斯", ["雷克萨斯", "LEXUS"]),
    ("沃尔沃", ["沃尔沃", "VOLVO"]),
    ("凯迪拉克", ["凯迪拉克", "CT5", "XT5", "CT6", "XT4", "XT6", "IQ锐歌", "傲歌"]),
    ("林肯", ["林肯", "航海家", "冒险家", "飞行家", "领航员"]),
    ("捷尼赛思", ["捷尼赛思", "GENESIS"]),
    ("英菲尼迪", ["英菲尼迪", "INFINITI"]),

    # 新能源大厂与新势力
    ("特斯拉", ["特斯拉", "Tesla", "Model 3", "Model Y", "Model S", "Model X", "Cybertruck"]),
    ("比亚迪", ["比亚迪", "秦PLUS", "秦L", "比亚迪汉", "比亚迪唐", "宋PLUS", "宋Pro", "宋L", "元PLUS", "元UP", "海鸥", "海豚", "海豹", "驱逐舰", "护卫舰"]),
    ("理想汽车", ["理想", "理想L6", "理想L7", "理想L8", "理想L9", "理想MEGA"]),
    ("蔚来", ["蔚来", "ET5", "ES6", "EC6", "ET7", "ES8", "EC7", "ES7", "乐道"]),
    ("小鹏汽车", ["小鹏", "MONA", "小鹏G6", "小鹏P7", "小鹏G9", "小鹏X9"]),
    ("小米汽车", ["小米", "SU7"]),
    ("鸿蒙智行", ["问界", "智界", "享界", "尊界", "AITO"]),
    ("极氪", ["极氪", "ZEEKR"]),
    ("腾势汽车", ["腾势", "DENZA"]),
    ("仰望", ["仰望"]),
    ("方程豹", ["方程豹", "豹5", "豹8"]),
    ("零跑汽车", ["零跑", "LEAPMOTOR"]),
    ("哪吒汽车", ["哪吒", "NETA"]),
    ("极越", ["极越"]),
    ("智己汽车", ["智己", "IM"]),
    ("阿维塔", ["阿维塔", "AVATR"]),
    ("岚图汽车", ["岚图", "VOYAH"]),
    ("深蓝汽车", ["深蓝"]),
    ("广汽埃安", ["埃安", "AION"]),
    ("极狐", ["极狐", "ARCFOX"]),
    ("高合汽车", ["高合", "HiPhi"]),

    # 主流合资
    ("大众", ["大众", "朗逸", "速腾", "迈腾", "帕萨特", "高尔夫", "途观", "途昂", "探岳", "宝来", "凌渡", "ID.3", "ID.4", "ID.6", "威然", "途岳", "探歌"]),
    ("丰田", ["丰田", "卡罗拉", "凯美瑞", "汉兰达", "RAV4", "荣放", "威兰达", "锐放", "锋兰达", "赛那", "格瑞维亚", "亚洲龙", "雷凌", "皇冠", "普拉多", "埃尔法", "威尔法"]),
    ("本田", ["本田", "雅阁", "思域", "CR-V", "皓影", "型格", "英仕派", "奥德赛", "艾力绅", "飞度", "缤智", "冠道", "UR-V"]),
    ("日产", ["日产", "轩逸", "天籁", "逍客", "奇骏", "骐达", "劲客", "探陆"]),
    ("别克", ["别克", "GL8", "微蓝", "君威", "君越", "昂科威", "威朗", "E5", "E4", "世纪"]),
    ("福特", ["福特", "蒙迪欧", "福克斯", "锐界", "探险者", "烈马", "撼路者", "全顺", "游骑侠"]),
    ("雪佛兰", ["雪佛兰", "科鲁泽", "迈锐宝", "探界者", "开拓者"]),
    ("现代", ["现代", "伊兰特", "索纳塔", "途胜", "胜达", "库斯途", "ix35", "沐飒"]),
    ("起亚", ["起亚", "K3", "K5", "狮铂拓界", "赛图斯", "嘉华", "EV5"]),
    ("马自达", ["马自达", "昂克赛拉", "CX-5", "CX-50", "CX-30", "EZ-6"]),
    ("斯巴鲁", ["斯巴鲁", "森林人", "傲虎", "BRZ", "旭豹"]),
    ("标致", ["标致", "408", "508", "4008", "5008"]),
    ("雪铁龙", ["雪铁龙", "凡尔赛", "天逸", "C3-XR", "C6"]),
    ("斯柯达", ["斯柯达", "明锐", "速派", "柯迪亚克", "柯珞克"]),
    ("smart", ["smart", "精灵#1", "精灵#3", "精灵#5"]),

    # 主流自主传统大厂
    ("吉利汽车", ["吉利", "银河", "星越", "星瑞", "博越", "帝豪", "缤越", "缤瑞", "几何", "熊猫"]),
    ("领克", ["领克", "LYNK&CO"]),
    ("长安汽车", ["长安", "CS75", "CS55", "CS35", "逸动", "UNI-V", "UNI-K", "UNI-T", "启源", "欧尚"]),
    ("奇瑞", ["奇瑞", "瑞虎", "艾瑞泽", "风云", "探索06"]),
    ("捷途", ["捷途", "旅行者", "山海", "大圣"]),
    ("星途", ["星途", "瑶光", "揽月", "凌云", "追风", "星纪元"]),
    ("长城汽车", ["长城", "长城炮", "金刚炮", "山海炮", "风骏"]),
    ("哈弗", ["哈弗", "H6", "大狗", "猛龙", "枭龙", "H9", "M6", "赤兔", "初恋"]),
    ("坦克", ["坦克", "TANK"]),
    ("魏牌", ["魏牌", "蓝山", "高山", "摩卡", "拿铁"]),
    ("广汽传祺", ["传祺", "M8", "M6", "GS3", "GS4", "GS8", "E8", "E9", "影豹", "影酷"]),
    ("五菱汽车", ["五菱", "五菱宏光", "宏光MINIEV", "缤果", "星光", "凯捷", "佳辰"]),
    ("宝骏", ["宝骏", "悦也", "云朵", "云海"]),
    ("荣威", ["荣威", "RX5", "D7", "i5", "i6", "eRX5"]),
    ("名爵", ["名爵", "MG", "Cyberster"]),
    ("红旗", ["红旗", "H5", "H9", "HS5", "HS3", "HS7", "E-QM5", "HQ9"]),
    ("北京汽车", ["北京汽车", "BJ40", "BJ30", "BJ60", "BJ80", "北京EU5", "北京EX5", "北京X7"]),
    ("上汽大通", ["大通", "MAXUS"]),
    ("江淮汽车", ["江淮", "思皓", "钇为", "瑞风", "悍途"]),
    ("东风汽车", ["东风", "纳米", "奕派", "风神", "风行", "风光", "小康"]),
    ("DS", ["DS", "DS 7", "DS 9", "DS 3", "DS 4", "DS 5"]),
    ("五十铃", ["五十铃", "mu-X", "D-MAX", "铃拓"]),
    ("江铃汽车", ["江铃", "驭胜", "大道", "域虎"]),
    ("凯翼汽车", ["凯翼", "炫界", "昆仑", "拾月"]),
    ("东南汽车", ["东南", "DX7", "DX3", "DX5"]),
]

def infer_brand(series_name, model_names_sample):
    text_to_check = series_name + " " + " ".join(model_names_sample[:3])
    
    # 优先精确查找
    for brand_canon, keywords in KNOWN_BRAND_RULES:
        for kw in keywords:
            if kw in series_name or (len(kw) >= 3 and kw in text_to_check):
                return brand_canon
    
    # 启发式清洗前缀
    clean_s = re.sub(r'\(停售\)|（停售）|\s*\(\d+\)', '', series_name).strip()
    words = clean_s.split()
    if words:
        candidate = words[0]
        if len(candidate) >= 2 and not re.match(r'^[A-Za-z0-9\-_]+$', candidate):
            return candidate
    return "其他品牌"

with open("car_dimension_filter/data/series.json", "r", encoding="utf-8") as f:
    series_list = json.load(f)

# 动力大类归一化
def normalize_energy(energy_raw_list):
    has_bev = False
    has_phev = False
    has_ice = False
    has_hev = False

    for e in energy_raw_list:
        if not e or e == "-": continue
        if "纯电" in e: has_bev = True
        elif "插电" in e or "增程" in e: has_phev = True
        elif "48V" in e or "油电混合" in e or "电驱" in e: has_hev = True
        elif "汽油" in e or "柴油" in e: has_ice = True
        else: has_ice = True

    cats = []
    if has_bev: cats.append("纯电动")
    if has_phev: cats.append("插混/增程")
    if has_ice: cats.append("燃油车")
    if has_hev: cats.append("油电混动")
    return cats if cats else ["燃油车"]

# 级别精简
def normalize_level(level_raw):
    if not level_raw or level_raw == "-": return "乘用车"
    if level_raw in ["微卡", "轻卡", "微面", "轻客"]: return "商用车/货车"
    return level_raw

for s in series_list:
    sname = s.get("series", "")
    models_sample = [v.get("model_name", "") for v in s.get("versions", [])]
    
    s["is_stopped"] = "停售" in sname
    s["clean_series_name"] = re.sub(r'\(停售\)|（停售）|\s*\(\d+\)', '', sname).strip()
    s["brand"] = infer_brand(sname, models_sample)
    s["energy_categories"] = normalize_energy(s.get("energy_types", []))
    s["clean_level"] = normalize_level(s.get("level", ""))

with open("car_dimension_filter/data/series.json", "w", encoding="utf-8") as f:
    json.dump(series_list, f, ensure_ascii=False, indent=2)

brand_counts = {}
for s in series_list:
    b = s["brand"]
    brand_counts[b] = brand_counts.get(b, 0) + 1

print("精确品牌提取与规范化完成！")
print("\nTop 30 品牌与车系数量:")
for b, cnt in sorted(brand_counts.items(), key=lambda x: x[1], reverse=True)[:30]:
    print(f"  {b}: {cnt} 个车系")
print(f"其他品牌车系总数: {brand_counts.get('其他品牌', 0)}")
