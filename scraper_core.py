# scraper_core.py -- polite HTTP fetcher with retry, simple robots check and caching

import os, time, json, hashlib, requests
from tenacity import retry, wait_exponential, stop_after_attempt
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
with open("config.json", "r", encoding="utf-8") as f:
    CONFIG = json.load(f)

CACHE_DIR = ".http_cache"
os.makedirs(CACHE_DIR, exist_ok=True)

def _cache_path(url: str) -> str:
    return os.path.join(CACHE_DIR, hashlib.sha256(url.encode()).hexdigest() + ".html")

def is_allowed_by_robots(url: str, user_agent: str = "*") -> bool:
    """
    Very simple robots.txt check: returns False if disallowed explicitly.
    (Does not implement crawl-delay parsing beyond default.)
    """
    try:
        parsed = urlparse(url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        r = requests.get(robots_url, timeout=5)
        if r.status_code != 200:
            return True
        txt = r.text.lower()
        ua = user_agent.lower()
        # naive: if "disallow: /" anywhere, assume blocked
        if "disallow: /" in txt:
            return False
        return True
    except Exception:
        return True

@retry(wait=wait_exponential(min=1, max=10), stop=stop_after_attempt(5))
def fetch_html(url: str, use_cache: bool = True, timeout: int = None) -> str:
    """
    Fetch HTML with retries. Respects a minimal robots.txt check; caches to .http_cache.
    If site blocks programmatic access, raise Exception and caller should fallback to manual source.
    """
    timeout = timeout or CONFIG.get("timeout_seconds", 15)
    if use_cache:
        cache = _cache_path(url)
        if os.path.exists(cache):
            with open(cache, "r", encoding="utf-8") as f:
                return f.read()

    # robots check
    if not is_allowed_by_robots(url):
        raise Exception(f"Blocked by robots.txt: {url}")

    headers = {
        "User-Agent": CONFIG.get("user_agent"),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Connection": "keep-alive",
        "Referer": url
    }
    s = requests.Session()
    resp = s.get(url, headers=headers, timeout=timeout, verify=False)
    if resp.status_code == 200:
        html = resp.text
        if use_cache:
            with open(_cache_path(url), "w", encoding="utf-8") as f:
                f.write(html)
        time.sleep(CONFIG.get("rate_limit_seconds", 1.5))
        return html
    raise Exception(f"Failed fetch {url}: HTTP {resp.status_code}")

def soupify(html: str):
    return BeautifulSoup(html, "lxml")
