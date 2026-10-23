# -*- coding: utf-8 -*-
"""
Car Dimension Filter - Realtime Autohome Image Proxy & Local Web Server
Features:
- Dual-channel Autohome vehicle image scraping (Price & Pic galleries)
- Anti-hotlinking bypass with custom Referer header
- Local disk image caching (.cache/images/{sid}.jpg) for instant 0ms reload
- Persistent URL metadata mapping (data/series_covers.json)
- Background low-priority prefetcher for active series
- Fully compatible with enterprise SSL/proxies
"""

import os
import re
import sys
import json
import time
import socket
import threading
import urllib3
import requests
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

# Suppress enterprise SSL proxy warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
CACHE_DIR = os.path.join(BASE_DIR, ".cache", "images")
SERIES_PATH = os.path.join(DATA_DIR, "series.json")
COVERS_INDEX_PATH = os.path.join(DATA_DIR, "series_covers.json")

os.makedirs(CACHE_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

AUTOHOME_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://car.autohome.com.cn/"
}

# Thread-safe persistent URL cache
url_cache_lock = threading.Lock()
url_cache = {}

if os.path.exists(COVERS_INDEX_PATH):
    try:
        with open(COVERS_INDEX_PATH, "r", encoding="utf-8") as f:
            url_cache = json.load(f)
    except Exception as e:
        print(f"[Warning] Failed to load covers index: {e}")
        url_cache = {}

def save_url_cache():
    with url_cache_lock:
        try:
            with open(COVERS_INDEX_PATH, "w", encoding="utf-8") as f:
                json.dump(url_cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[Warning] Failed to save covers index: {e}")

def clean_autoimg_url(raw_url):
    """Strip thumbnail dimension markers to get original full-resolution image."""
    # Remove markers like 120x90_0_q95_c42_, 240x180_, 800x0_1_q95_, etc.
    cleaned = re.sub(r'\d+x\d+(_\d+)?(_q\d+)?(_c\d+)?_', '', raw_url)
    if cleaned.startswith("//"):
        cleaned = "https:" + cleaned
    elif cleaned.startswith("http://"):
        cleaned = "https://" + cleaned[7:]
    return cleaned

def scrape_cover_url(series_id):
    """Scrape cover image URL from Autohome using dual-channel fallback."""
    # Channel 1: Price page (Contains main hero cardfs picture for most models)
    price_url = f"https://car.autohome.com.cn/price/series-{series_id}.html"
    try:
        r = requests.get(price_url, headers=AUTOHOME_HEADERS, timeout=6, verify=False)
        if r.status_code == 200:
            matches = re.findall(
                r'(?:https?:)?//[^\s"\'<>]*autoimg[^\s"\'<>]*cardfs[^\s"\'<>]*\.(?:jpg|jpeg|png)',
                r.text,
                re.IGNORECASE
            )
            if matches:
                clean = clean_autoimg_url(matches[0])
                return clean
    except Exception:
        pass

    # Channel 2: Official Pic gallery (Contains white-background official studio shoots)
    pic_url = f"https://car.autohome.com.cn/pic/series/{series_id}.html"
    try:
        r = requests.get(pic_url, headers=AUTOHOME_HEADERS, timeout=6, verify=False)
        if r.status_code == 200:
            matches = re.findall(
                r'(?:https?:)?//[^\s"\'<>]*autoimg[^\s"\'<>]*cardfs[^\s"\'<>]*\.(?:jpg|jpeg|png)',
                r.text,
                re.IGNORECASE
            )
            if matches:
                clean = clean_autoimg_url(matches[0])
                return clean
    except Exception:
        pass

    return None

def get_cover_image_url(series_id):
    sid_str = str(series_id)
    with url_cache_lock:
        if sid_str in url_cache and url_cache[sid_str]:
            return url_cache[sid_str]

    img_url = scrape_cover_url(series_id)
    if img_url:
        with url_cache_lock:
            url_cache[sid_str] = img_url
        threading.Thread(target=save_url_cache, daemon=True).start()
    return img_url

def fetch_and_cache_image(series_id):
    """Retrieve image bytes, using local disk cache first, proxy fetch if missing."""
    cached_path = os.path.join(CACHE_DIR, f"{series_id}.jpg")
    if os.path.exists(cached_path) and os.path.getsize(cached_path) > 500:
        with open(cached_path, "rb") as f:
            return f.read(), "image/jpeg"

    img_url = get_cover_image_url(series_id)
    if not img_url:
        return None, None

    try:
        r = requests.get(img_url, headers=AUTOHOME_HEADERS, timeout=8, verify=False)
        if r.status_code == 200 and len(r.content) > 500:
            ctype = r.headers.get("Content-Type", "image/jpeg")
            with open(cached_path, "wb") as f:
                f.write(r.content)
            return r.content, ctype
    except Exception as e:
        print(f"[Proxy] Error downloading image {img_url} for series {series_id}: {e}")

    return None, None

class ProxyRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=BASE_DIR, **kwargs)

    def do_GET(self):
        parsed = urlparse(self.path)

        # 1. API route: /api/car-image?series_id=XXXX
        if parsed.path == "/api/car-image":
            qs = parse_qs(parsed.query)
            sid_raw = qs.get("series_id", [None])[0]
            if not sid_raw or not sid_raw.isdigit():
                self.send_error(400, "Missing or invalid series_id parameter")
                return

            sid = int(sid_raw)
            content, ctype = fetch_and_cache_image(sid)

            if content:
                self.send_response(200)
                self.send_header("Content-Type", ctype or "image/jpeg")
                self.send_header("Content-Length", str(len(content)))
                self.send_header("Cache-Control", "public, max-age=2592000") # 30 days browser cache
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(content)
            else:
                self.send_error(404, "Cover image not found")
            return

        # 2. Root route: serve index.html
        if parsed.path in ["", "/"]:
            self.path = "/index.html"

        return super().do_GET()

    def log_message(self, format, *args):
        # Silence routine 200/304/404 noise to keep terminal clean and readable
        msg = format % args
        if any(code in msg for code in ["200 -", "304 -", "404 -"]):
            return
        sys.stderr.write(f"[{self.log_date_time_string()}] {msg}\n")

def find_available_port(start_port=8080):
    port = start_port
    while port < start_port + 50:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", port)) != 0:
                return port
            port += 1
    return start_port

def background_prefetch_worker():
    """Background low-priority daemon to smoothly preheat images for active cars."""
    time.sleep(3) # Wait for server startup
    if not os.path.exists(SERIES_PATH):
        return

    try:
        with open(SERIES_PATH, "r", encoding="utf-8") as f:
            all_series = json.load(f)
    except Exception:
        return

    # Prioritize active (in-sale) series
    active_series = [s for s in all_series if not s.get("is_stopped")]
    for s in active_series:
        sid = s.get("series_id")
        if not sid:
            continue
        cached_path = os.path.join(CACHE_DIR, f"{sid}.jpg")
        if not os.path.exists(cached_path) or os.path.getsize(cached_path) < 500:
            fetch_and_cache_image(sid)
            time.sleep(1.2) # Gentle pacing to avoid network contention

def run_server():
    port = find_available_port(8080)
    server_address = ("127.0.0.1", port)
    httpd = ThreadingHTTPServer(server_address, ProxyRequestHandler)

    # Start background gentle prefetcher
    prefetch_thread = threading.Thread(target=background_prefetch_worker, daemon=True)
    prefetch_thread.start()

    print("=" * 66)
    print(f"  汽车尺寸检索系统服务已启动 (Car Dimension Filter Proxy)")
    print(f"  本地访问网址 : http://127.0.0.1:{port}/")
    print(f"  实时图片代理 : http://127.0.0.1:{port}/api/car-image?series_id=<ID>")
    print(f"  本地持久缓存 : {CACHE_DIR}")
    print("=" * 66)
    print(f"  [提示] 保持当前窗口开启即可持续提供服务，按 Ctrl+C 可停止服务。")
    print("=" * 66)

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n正在停止服务...")
        httpd.server_close()

if __name__ == "__main__":
    run_server()
