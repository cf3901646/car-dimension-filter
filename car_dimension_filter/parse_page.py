import requests
import re
import sys
import urllib3

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

urllib3.disable_warnings()

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}
r = requests.get("https://car.autohome.com.cn/price/series-5026.html", headers=headers, verify=False, timeout=8)
r.encoding = "gb2312" # Autohome PC uses gb2312 or gbk!
print("Title:", re.findall(r'<title>(.*?)</title>', r.text))

# Search for any img tags
img_srcs = re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', r.text)
print("Total img tags:", len(img_srcs))
for s in img_srcs[:10]:
    print("  img:", s)

# Search for series cover or pic
covers = [s for s in img_srcs if "series" in s or "car" in s or "photo" in s or "cardfs" in s]
print("Candidate covers:", len(covers))
for c in covers[:5]:
    print("  cover:", c)
