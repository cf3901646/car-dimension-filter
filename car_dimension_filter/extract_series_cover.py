import requests
import re
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

url = "https://car.autohome.com.cn/price/series-5026.html"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
r = requests.get(url, headers=headers, timeout=8, verify=False)
print("Status:", r.status_code, "Len:", len(r.text))

# 匹配所有 autoimg 图片
imgs = re.findall(r'(?:https?:)?//[^\s"\'<>]*autoimg[^\s"\'<>]*\.(?:jpg|png|webp)', r.text, re.IGNORECASE)
print(f"Total autoimg URLs: {len(imgs)}")
for im in imgs[:10]:
    full_url = "https:" + im if im.startswith("//") else im
    print("  ", full_url)
