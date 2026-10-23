# -*- coding: utf-8 -*-
import requests, sys, json, re
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

headers = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148"
}
session = requests.Session()
session.trust_env = False

for sid, name in [(634, "天籁"), (162, "保时捷911"), (6962, "小米SU7"), (5964, "秦PLUS")]:
    # 尝试移动端车系主页: https://car.m.autohome.com.cn/series/{sid}.html
    m_url = f"https://car.m.autohome.com.cn/series/{sid}.html"
    try:
        r = session.get(m_url, headers=headers, timeout=6)
        print(f"\n{name} ({sid}) status: {r.status_code}")
        if r.status_code == 200:
            # 查找图片链接
            imgs = re.findall(r'(https?:)?//[^\s"\'<>]+\.(?:jpg|png|webp)', r.text)
            # 过滤汽车图库 cardfs 图片
            cardfs = [img for img in imgs if "autoimg.cn" in img and any(k in img for k in ["cardfs", "car", "product", "special"])]
            print(f"  Found {len(cardfs)} cardfs images, sample: {cardfs[:2]}")
    except Exception as e:
        print(f"  Error {sid}: {e}")

    # 尝试移动端接口: https://car.m.autohome.com.cn/ashx/car/GetSeriesPic.ashx 或类似
    # 或者 https://car.m.autohome.com.cn/ashx/car/GetModelConfigNew.ashx 里面有没有图片
