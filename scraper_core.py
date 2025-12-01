# scraper_core.py
import os, time, json, hashlib, requests
from tenacity import retry, wait_exponential, stop_after_attempt
from bs4 import BeautifulSoup
from urllib.parse import urlparse

with open("config.json","r",encoding="utf-8") as f:
    CONFIG = json.load(f)

CACHE_DIR = ".http_cache"
os.makedirs(CACHE_DIR, exist_ok=True)

def _cache_path(url):
    return os.path.join(CACHE_DIR, hashlib.sha256(url.encode()).hexdigest() + ".html")

@retry(wait=wait_exponential(min=1, max=10), stop=stop_after_attempt(4))
def fetch_text(url, use_cache=True, timeout=None):
    timeout = timeout or CONFIG.get("timeout_seconds", 15)
    if use_cache:
        cache = _cache_path(url)
        if os.path.exists(cache):
            return open(cache,"r",encoding="utf-8").read()
    headers = {"User-Agent": CONFIG.get("user_agent")}
    s = requests.Session()
    resp = s.get(url, headers=headers, timeout=timeout, verify=False)
    if resp.status_code == 200:
        text = resp.text
        if use_cache:
            open(cache,"w",encoding="utf-8").write(text)
        time.sleep(CONFIG.get("rate_limit_seconds",1.5))
        return text
    raise Exception(f"HTTP {resp.status_code} for {url}")

def soupify(text):
    return BeautifulSoup(text, "lxml")
