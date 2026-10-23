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

test_sids = [5026, 6643, 3825, 5976, 7207]

def extract_cover(sid):
    url = f"https://car.autohome.com.cn/price/series-{sid}.html"
    try:
        r = requests.get(url, headers=headers, verify=False, timeout=6)
        r.encoding = "gb2312"
        # 匹配 cardfs 封面图 (通常在头部主视觉区域)
        matches = re.findall(r'(?:https?:)?//[^\s"\'<>]*autoimg[^\s"\'<>]*cardfs[^\s"\'<>]*\.(?:jpg|jpeg|png)', r.text, re.IGNORECASE)
        if matches:
            # 选第一个 cardfs 图片，去除缩略图尺寸限制 (如 120x90_0_q95_ 或 240x180_) 获取清晰图
            raw = matches[0]
            clean_url = re.sub(r'\d+x\d+_\d+_q\d+(_c\d+)?_', '', raw)
            if clean_url.startswith("//"):
                clean_url = "https:" + clean_url
            return clean_url
    except Exception as e:
        print(f"Error {sid}: {e}")
    return None

for sid in test_sids:
    cover = extract_cover(sid)
    print(f"Series {sid} -> {cover}")
