# -*- coding: utf-8 -*-
import requests, sys, json
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}
session = requests.Session()
session.trust_env = False

for sid in [2569, 6962]:
    url = f"https://car.m.autohome.com.cn/ashx/car/GetModelConfigNew.ashx?seriesId={sid}"
    try:
        r = session.get(url, headers=headers, timeout=6)
        print(f"Status for {sid}: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            param = data.get("param") or []
            models = []
            for g in param:
                for it in g.get("paramitems") or []:
                    if it.get("name") == "车型名称":
                        models = [v.get("value") or v.get("sublist", [{}])[0].get("subvalue") for v in it.get("valueitems") or []]
            print(f"SID {sid} models: {models[:5]}")
    except Exception as e:
        print(f"Error for {sid}: {e}")
