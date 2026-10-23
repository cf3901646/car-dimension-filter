# -*- coding: utf-8 -*-
import requests, sys, json
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}
session = requests.Session()
session.trust_env = False

# 1. 检查秦PLUS (5964) 的 GetModelConfigNew.ashx
url_qin = "https://car.m.autohome.com.cn/ashx/car/GetModelConfigNew.ashx?seriesId=5964"
r = session.get(url_qin, headers=headers, timeout=6)
print("Qin PLUS status:", r.status_code)
if r.status_code == 200:
    data = r.json()
    param = data.get("param") or []
    param_names = []
    for g in param:
        for it in g.get("paramitems") or []:
            param_names.append(it.get("name"))
    print("Qin PLUS available param names:", [p for p in param_names if "马力" in p or "功率" in p or "质量" in p or "驱动" in p or "续航" in p])
    
    # 打印具体的动力参数值
    for g in param:
        for it in g.get("paramitems") or []:
            name = it.get("name")
            if any(k in name for k in ["马力", "功率", "整备质量", "驱动"]):
                val_items = it.get("valueitems") or []
                vals = [v.get("value") or (v.get("sublist", [{}])[0].get("subvalue") if v.get("sublist") else "") for v in val_items[:3]]
                print(f"  {name}: {vals}")

# 2. 检查天籁 (634) 和保时捷911 (162) 的图片接口
for sid, name in [(634, "天籁"), (162, "保时捷911"), (6962, "小米SU7")]:
    pic_url = f"https://car.m.autohome.com.cn/ashx/car/GetSeriesPicInfo.ashx?seriesId={sid}"
    r_pic = session.get(pic_url, headers=headers, timeout=6)
    print(f"\nPic status for {name} ({sid}): {r_pic.status_code}")
    if r_pic.status_code == 200:
        try:
            pic_data = r_pic.json()
            print(f"  Pic data keys for {sid}:", list(pic_data.keys()) if isinstance(pic_data, dict) else len(pic_data))
            # 找找大图 url
            s_pic = json.dumps(pic_data)
            import re
            img_urls = re.findall(r'https?://[^\s"]+?\.(?:jpg|png)', s_pic)
            print(f"  Sample image urls: {img_urls[:2]}")
        except Exception as e:
            print(f"  JSON parse error: {e}")
