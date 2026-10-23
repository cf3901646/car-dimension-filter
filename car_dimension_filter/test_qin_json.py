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
print("Top-level keys:", list(data.keys()))
for g in data.get("param", []):
    print("Group name:", g.get("groupname"))
    items = [it.get("name") for it in g.get("paramitems", [])]
    print("  items:", items[:5])
