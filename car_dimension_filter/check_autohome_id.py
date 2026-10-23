# -*- coding: utf-8 -*-
import requests, re, sys, json
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
session = requests.Session()
session.trust_env = False

# 1. 查 2569
r = session.get('https://car.autohome.com.cn/price/series-2569.html', headers=headers, timeout=5)
title = re.findall(r'<title>(.*?)</title>', r.text)
print('Series 2569 title:', title)

# 2. 查小米汽车的所有车系
r_brand = session.get('https://car.autohome.com.cn/price/brand-384.html', headers=headers, timeout=5) # 看看小米品牌ID
print('Brand 384 title:', re.findall(r'<title>(.*?)</title>', r_brand.text))

# 搜小米汽车
r_search = session.get('https://sou.autohome.com.cn/zhaoche?entry=44&q=%E5%B0%8F%E7%B1%B3SU7', headers=headers, timeout=5)
series_ids = re.findall(r'series/(\d+)|series-(\d+)', r_search.text)
print('Search series_ids found:', series_ids[:10])

# 看看小米SU7究竟是哪个ID
for sid in [6926, 7126, 7367, 7293, 7300, 7569, 7793, 7915, 6923, 7111]:
    try:
        res = session.get(f'https://car.autohome.com.cn/price/series-{sid}.html', headers=headers, timeout=3)
        t = re.findall(r'<title>(.*?)</title>', res.text)
        if t:
            print(f'SID {sid}: {t[0]}')
    except Exception:
        pass
