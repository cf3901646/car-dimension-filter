# -*- coding: utf-8 -*-
import requests, sys, json
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}
session = requests.Session()
session.trust_env = False

url = "https://car.m.autohome.com.cn/ashx/car/GetModelConfigNew.ashx?seriesId=5964"
r = session.get(url, headers=headers, timeout=6)
data = r.json()

for g in data.get("param", []):
    for it in g.get("paramitems", []):
        if it.get("name") == "车型名称":
            print("Found 车型名称:")
            for v in it.get("valueitems", [])[:5]:
                print("  val item:", v)
