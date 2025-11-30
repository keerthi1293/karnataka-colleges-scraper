# scraper_core.py -- polite HTTP fetching utilities with retries and caching
import os, time, json, hashlib
import requests
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type
from bs4 import BeautifulSoup

from typing import Optional
CONFIG_PATH = "config.json"
with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    CONFIG = json.load(f)

HEADERS = {"User-Agent": CONFIG.get("user_agent", "KarnatakaCollegeScraper/1.0")}
CACHE_DIR = ".http_cache"
os.makedirs(CACHE_DIR, exist_ok=True)

def _cache_path(url: str) -> str:
    h = hashlib.sha256(url.encode("utf-8")).hexdigest()
    return os.path.join(CACHE_DIR, f"{h}.html")

@retry(wait=wait_exponential(min=1, max=10), stop=stop_after_attempt(4), retry=retry_if_exception_type(Exception))
def fetch_html(url: str, use_cache=True, timeout=None) -> Optional[str]:
    """
    Fetch HTML content politely. Uses simple file cache (in .http_cache) to avoid repeated hits.
    Retries with exponential backoff on transient errors.
    """
    timeout = timeout or CONFIG.get("timeout_seconds", 15)
    cache_file = _cache_path(url)
    if use_cache and os.path.exists(cache_file):
        with open(cache_file, "r", encoding="utf-8") as f:
            return f.read()
    resp = requests.get(url, headers=HEADERS, timeout=timeout)
    if resp.status_code == 200:
        resp.encoding = resp.apparent_encoding or "utf-8"
        html = resp.text
        if use_cache:
            with open(cache_file, "w", encoding="utf-8") as f:
                f.write(html)
        # polite rate limiting after successful fetch
        time.sleep(CONFIG.get("rate_limit_seconds", 2))
        return html
    elif resp.status_code in (429, 503):
        raise Exception(f"Server busy / rate limited: {resp.status_code} for {url}")
    else:
        raise Exception(f"Failed to fetch {url}: HTTP {resp.status_code}")

def soupify(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "lxml")
