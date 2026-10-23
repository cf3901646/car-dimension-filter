import requests
import re
import json

session = requests.Session()
session.trust_env = False

headers = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1",
    "Referer": "https://car.m.autohome.com.cn/"
}

# 探索汽车之家的图片和车系接口
apis = [
    # 1. 汽车之家 M 端图片接口
    "https://car.m.autohome.com.cn/ashx/car/GetModelColorPicList.ashx?seriesId=5026",
    # 2. 车型列表/参数页，通常含有封面图
    "https://car.m.autohome.com.cn/ashx/car/GetSeriesInfoNew.ashx?seriesId=5026",
    # 3. 车系综述
    "https://car.m.autohome.com.cn/dealer/carseries/getseriesinfo?seriesid=5026",
    # 4. 汽车之家图片中心轻量接口
    "https://car.m.autohome.com.cn/ashx/car/GetPicIndex.ashx?seriesId=5026",
    # 5. 车系搜索 API (传关键词或车系ID)
    "https://api.mall.autohome.com.cn/api/car/getSeriesInfo?seriesId=5026",
    # 6. App 端车系摘要 (包含白底外观大图)
    "https://cars.app.autohome.com.cn/car/series_summary?seriesid=5026",
    # 7. 车系首页 HTML
    "https://m.autohome.com.cn/5026/",
    # 8. M 端新版 API
    "https://m.autohome.com.cn/api/series/summary?seriesId=5026",
    # 9. 汽车之家搜索建议/联想
    "https://sou.m.autohome.com.cn/suggest?q=AION%20S"
]

for url in apis:
    try:
        r = session.get(url, headers=headers, timeout=4)
        print(f"URL: {url.split('?')[0]}")
        print(f"  Status: {r.status_code}, Length: {len(r.text)}")
        imgs = re.findall(r'https?://[^\s"\'\\]*autoimg[^\s"\'\\]*\.(?:jpg|png|webp)', r.text)
        if imgs:
            print(f"  Found {len(imgs)} autoimg URLs! Sample: {imgs[0]}")
        elif r.status_code == 200:
            print("  Response preview:", r.text[:120].strip())
    except Exception as e:
        print(f"URL: {url.split('?')[0]} -> Error: {e}")
