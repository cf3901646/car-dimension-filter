import requests
import re
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

s = requests.Session()
s.trust_env = False
headers = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1",
    "Referer": "https://car.m.autohome.com.cn/"
}

r = s.get("https://car.m.autohome.com.cn/", headers=headers, timeout=5)
print("Status:", r.status_code, "Len:", len(r.text))
imgs = re.findall(r'https?://[^\s"\'\\]*autoimg[^\s"\'\\]*', r.text)
print("Imgs found:", len(imgs))
for im in imgs[:8]:
    print(" ", im)
