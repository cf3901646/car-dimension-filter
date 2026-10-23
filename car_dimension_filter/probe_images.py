import requests
import re
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

session = requests.Session()
session.trust_env = False
headers = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1",
    "Referer": "https://car.m.autohome.com.cn/"
}

test_urls = [
    # M 端车系页面 HTML
    "https://car.m.autohome.com.cn/series/5026.html",
    # M 端选车接口
    "https://car.m.autohome.com.cn/ashx/car/GetSeriesPic.ashx?seriesId=5026",
    # M 端找车列表
    "https://car.m.autohome.com.cn/ashx/car/GetSeriesByBrand.ashx?brandId=209",
    # 车系概要
    "https://car.m.autohome.com.cn/ashx/car/GetSeriesSummary.ashx?seriesId=5026",
    # 汽车之家轻量图片页
    "https://car.m.autohome.com.cn/pic/series/5026.html",
    # PC 端
    "https://car.autohome.com.cn/price/series-5026.html"
]

for u in test_urls:
    try:
        r = session.get(u, headers=headers, timeout=6)
        print(f"URL: {u}")
        print(f"  Status: {r.status_code}, Length: {len(r.text)}")
        imgs = re.findall(r'(https?:)?//[^\s"\'<>]*(?:autoimg|autohomecar)[^\s"\'<>]*(?:jpg|png|webp)', r.text, re.IGNORECASE)
        print(f"  Images count: {len(imgs)}")
        for img in imgs[:3]:
            print(f"    Sample: {img}")
    except Exception as e:
        print(f"URL: {u} -> Error: {e}")
