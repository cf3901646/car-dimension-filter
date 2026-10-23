import requests
import json
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

session = requests.Session()
session.trust_env = False
headers = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1",
    "Referer": "https://car.m.autohome.com.cn/"
}

# 探查 car.m.autohome.com.cn 下可能包含车图的 ashx 接口
ashx_list = [
    # 车系图片相关
    "https://car.m.autohome.com.cn/ashx/car/GetSeriesPic.ashx?seriesId=5026",
    "https://car.m.autohome.com.cn/ashx/car/GetModelPicList.ashx?seriesId=5026",
    "https://car.m.autohome.com.cn/ashx/car/GetPicList.ashx?seriesId=5026",
    "https://car.m.autohome.com.cn/ashx/car/GetSeriesPicList.ashx?seriesId=5026",
    "https://car.m.autohome.com.cn/ashx/car/GetCarPicList.ashx?seriesId=5026",
    "https://car.m.autohome.com.cn/ashx/car/GetSeriesInfo.ashx?seriesId=5026",
    "https://car.m.autohome.com.cn/ashx/car/GetSeriesPrice.ashx?seriesId=5026",
    "https://car.m.autohome.com.cn/ashx/car/GetModelListBySeriesId.ashx?seriesId=5026",
    "https://car.m.autohome.com.cn/ashx/car/GetSeriesSpecList.ashx?seriesId=5026",
    "https://car.m.autohome.com.cn/ashx/car/GetSeriesSummary.ashx?seriesId=5026"
]

for url in ashx_list:
    try:
        r = session.get(url, headers=headers, timeout=4)
        name = url.split("?")[0].split("/")[-1]
        print(f"{name}: status={r.status_code}, len={len(r.text)}")
        if r.status_code == 200 and len(r.text) > 10:
            if "autoimg" in r.text or "jpg" in r.text or "png" in r.text:
                print("   *** FOUND IMAGES in", name)
                # print sample
                import re
                imgs = re.findall(r'https?://[^\s"\'\\]+\.(?:jpg|png|webp)', r.text)
                for im in imgs[:3]:
                    print("     ", im)
            else:
                print("   Preview:", r.text[:80])
    except Exception as e:
        print(f"Error {url}: {e}")
