# -*- coding: utf-8 -*-
import requests, sys, json, re
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}
session = requests.Session()
session.trust_env = False

# 1. PC 端 price 页面
r1 = session.get("https://car.autohome.com.cn/price/series-2569.html", headers=headers, timeout=6)
print("PC 2569 status:", r1.status_code, "URL:", r1.url)
print("PC 2569 title:", re.findall(r'<title>(.*?)</title>', r1.text))
print("PC 2569 breadcrumbs:", re.findall(r'class="crumbs.*?</div>', r1.text, re.DOTALL))

# 2. 真实江淮星锐的 ID
# 让我们在目录里搜江淮的所有车
