import requests
import json
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

url = "https://car.m.autohome.com.cn/ashx/car/GetModelConfigNew.ashx?seriesId=5026"
session = requests.Session()
session.trust_env = False
headers = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1",
    "Referer": "https://car.m.autohome.com.cn/"
}

try:
    r = session.get(url, headers=headers, timeout=8)
    print("Status:", r.status_code)
    data = r.json()
    s_dump = json.dumps(data, ensure_ascii=False)
    import re
    imgs = re.findall(r'https?://[^\s"\'\\]+\.(?:jpg|png|webp)', s_dump)
    print("Image URLs found in entire data:", len(imgs))
    for img in imgs[:10]:
        print("  ", img)
    autoimgs = re.findall(r'[^\s"\'\\]*autoimg[^\s"\'\\]*', s_dump)
    print("Autoimg mentions:", len(autoimgs))
    for a in autoimgs[:10]:
        print("   ->", a)

except Exception as e:
    print("Error:", e)
