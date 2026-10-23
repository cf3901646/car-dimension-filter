# -*- coding: utf-8 -*-
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
COVERS_INDEX_PATH = os.path.join(DATA_DIR, "series_covers.json")

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

def scrape_sid(sid, session):
    # Channel 1: Price page
    try:
        url = f"https://car.autohome.com.cn/price/series-{sid}.html"
        r = session.get(url, headers=HEADERS, timeout=8, verify=False)
        if r.status_code == 200:
            matches = re.findall(
                r'(?:https?:)?//[^\s"\'<>]*autoimg[^\s"\'<>]*cardfs[^\s"\'<>]*\.(?:jpg|jpeg|png)',
                r.text,
                re.IGNORECASE
            )
            if matches:
                return sid, clean_autoimg_url(matches[0])
    except Exception:
        pass

    # Channel 2: Pic gallery
    try:
        url = f"https://car.autohome.com.cn/pic/series/{sid}.html"
        r = session.get(url, headers=HEADERS, timeout=8, verify=False)
        if r.status_code == 200:
            matches = re.findall(
                r'(?:https?:)?//[^\s"\'<>]*autoimg[^\s"\'<>]*cardfs[^\s"\'<>]*\.(?:jpg|jpeg|png)',
                r.text,
                re.IGNORECASE
            )
            if matches:
                return sid, clean_autoimg_url(matches[0])
    except Exception:
        pass

    return sid, None

def run_batch(limit=None):
    with open(SERIES_PATH, "r", encoding="utf-8") as f:
        all_series = json.load(f)

    if os.path.exists(COVERS_INDEX_PATH):
        try:
            with open(COVERS_INDEX_PATH, "r", encoding="utf-8") as f:
                covers = json.load(f)
        except Exception:
            covers = {}
    else:
        covers = {}

    # 优先在售、且尚未抓取到有效图片的车系
    active_todo = [s for s in all_series if not s.get("is_stopped") and (str(s["series_id"]) not in covers or not covers[str(s["series_id"])])]
    stopped_todo = [s for s in all_series if s.get("is_stopped") and (str(s["series_id"]) not in covers or not covers[str(s["series_id"])])]
    
    todo = active_todo + stopped_todo
    if limit:
        targets = todo[:limit]
    else:
        targets = todo

    valid_count = len([k for k, v in covers.items() if v])
    print(f"Total series: {len(all_series)}, already have covers: {valid_count}, remaining to fetch: {len(targets)}")
    if not targets:
        print("All covers already fetched!")
        return

    chunk_size = 80
    for chunk_start in range(0, len(targets), chunk_size):
        chunk = targets[chunk_start:chunk_start + chunk_size]
        print(f"\nProcessing chunk {chunk_start + 1} to {chunk_start + len(chunk)} of {len(targets)}...")
        t0 = time.time()
        success = 0

        def worker(s):
            session = requests.Session()
            return scrape_sid(s["series_id"], session)

        with ThreadPoolExecutor(max_workers=16) as pool:
            futures = {pool.submit(worker, s): s for s in chunk}
            for future in as_completed(futures):
                s = futures[future]
                sid, img_url = future.result()
                if img_url:
                    covers[str(sid)] = img_url
                    success += 1
                else:
                    covers[str(sid)] = None

        t1 = time.time()
        # 实时存盘
        with open(COVERS_INDEX_PATH, "w", encoding="utf-8") as f:
            json.dump(covers, f, ensure_ascii=False, indent=2)
        print(f"Chunk finished: {success}/{len(chunk)} covers scraped in {t1 - t0:.2f}s. Saved to index.")

if __name__ == "__main__":
    count = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1] != "all" else None
    run_batch(count)
