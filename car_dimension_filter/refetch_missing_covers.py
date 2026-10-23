# -*- coding: utf-8 -*-
"""
Refetches missing car covers for on-sale vehicles with robust retry and error handling.
"""

import os
import sys
import json
import time
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
import urllib3

urllib3.disable_warnings()

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
SERIES_PATH = os.path.join(DATA_DIR, "series.json")
COVERS_PATH = os.path.join(DATA_DIR, "series_covers.json")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://car.autohome.com.cn/"
}

def clean_autoimg_url(raw_url):
    cleaned = re.sub(r'\d+x\d+(_\d+)?(_q\d+)?(_c\d+)?_', '', raw_url)
    if cleaned.startswith("//"):
        cleaned = "https:" + cleaned
    elif cleaned.startswith("http://"):
        cleaned = "https://" + cleaned[7:]
    return cleaned

def fetch_cover_for_sid(sid, max_retries=3):
    session = requests.Session()
    
    # 渠道 1: price 页面
    for _ in range(max_retries):
        try:
            url = f"https://car.autohome.com.cn/price/series-{sid}.html"
            r = session.get(url, headers=HEADERS, timeout=7, verify=False)
            if r.status_code == 200:
                matches = re.findall(
                    r'(?:https?:)?//[^\s"\'<>]*autoimg[^\s"\'<>]*cardfs[^\s"\'<>]*\.(?:jpg|jpeg|png)',
                    r.text,
                    re.IGNORECASE
                )
                if matches:
                    return sid, clean_autoimg_url(matches[0])
        except Exception:
            time.sleep(0.3)

    # 渠道 2: pic 图库
    for _ in range(max_retries):
        try:
            url = f"https://car.autohome.com.cn/pic/series/{sid}.html"
            r = session.get(url, headers=HEADERS, timeout=7, verify=False)
            if r.status_code == 200:
                matches = re.findall(
                    r'(?:https?:)?//[^\s"\'<>]*autoimg[^\s"\'<>]*cardfs[^\s"\'<>]*\.(?:jpg|jpeg|png)',
                    r.text,
                    re.IGNORECASE
                )
                if matches:
                    return sid, clean_autoimg_url(matches[0])
        except Exception:
            time.sleep(0.3)

    return sid, None

def run():
    with open(SERIES_PATH, "r", encoding="utf-8") as f:
        series_list = json.load(f)

    if os.path.exists(COVERS_PATH):
        with open(COVERS_PATH, "r", encoding="utf-8") as f:
            covers = json.load(f)
    else:
        covers = {}

    # 找出所有在售但缺少封面的车型
    missing_targets = []
    for s in series_list:
        if s.get("is_stopped"): continue
        sid_str = str(s["series_id"])
        if sid_str not in covers or not covers[sid_str]:
            missing_targets.append(s["series_id"])

    print(f"Total on-sale series missing covers: {len(missing_targets)}")
    if not missing_targets:
        print("All on-sale series already have covers!")
        return

    chunk_size = 30
    for chunk_start in range(0, len(missing_targets), chunk_size):
        chunk = missing_targets[chunk_start:chunk_start + chunk_size]
        print(f"\nFetching covers for chunk {chunk_start + 1} to {chunk_start + len(chunk)} of {len(missing_targets)}...")
        t0 = time.time()
        
        with ThreadPoolExecutor(max_workers=6) as pool:
            futures = [pool.submit(fetch_cover_for_sid, sid) for sid in chunk]
            for future in as_completed(futures):
                sid, img_url = future.result()
                if img_url:
                    covers[str(sid)] = img_url

        with open(COVERS_PATH, "w", encoding="utf-8") as f:
            json.dump(covers, f, ensure_ascii=False, indent=2)
        print(f"Chunk finished in {time.time() - t0:.2f}s. Saved covers checkpoint.")

    print("All missing covers fetched successfully!")

if __name__ == "__main__":
    run()
