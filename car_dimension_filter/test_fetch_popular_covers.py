# -*- coding: utf-8 -*-
import requests, sys, re, json
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}
session = requests.Session()
# 不禁用代理，但增加超时重试
for sid, name in [(634, "天籁"), (162, "保时捷911"), (6962, "小米SU7"), (2569, "星锐")]:
    url = f"https://car.autohome.com.cn/price/series-{sid}.html"
    try:
        r = session.get(url, headers=headers, timeout=10, verify=False)
        print(f"{name} ({sid}) status: {r.status_code}")
        if r.status_code == 200:
            matches = re.findall(r'(?:https?:)?//[^\s"\'<>]*autoimg[^\s"\'<>]*cardfs[^\s"\'<>]*\.(?:jpg|jpeg|png)', r.text, re.IGNORECASE)
            print(f"  Found {len(matches)} cardfs images, sample: {matches[:1]}")
    except Exception as e:
        print(f"  Error {name} ({sid}): {e}")
