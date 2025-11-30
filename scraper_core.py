# scraper_core.py -- Cloudflare-safe polite HTTP fetching utilities with retries + caching

import os, time, json, hashlib, requests
from tenacity import retry, wait_exponential, stop_after_attempt
from bs4 import BeautifulSoup
import urllib3

# Disable SSL warnings (because verify=False is used to bypass Cloudflare SSL challenges)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Load config
with open("config.json", "r", encoding="utf-8") as f:
    CONFIG = json.load(f)

CACHE_DIR = ".http_cache"
os.makedirs(CACHE_DIR, exist_ok=True)

def _cache_path(url: str) -> str:
    return os.path.join(CACHE_DIR, hashlib.sha256(url.encode()).hexdigest() + ".html")


@retry(wait=wait_exponential(min=1, max=12),
       stop=stop_after_attempt(8))
def fetch_html(url, use_cache=True, timeout=None):
    """
    Cloudflare-friendly fetch with:
    - full browser headers
    - keep-alive session
    - SSL verify disabled
    - disk caching
    - automatic retry with exponential backoff
    """

    timeout = timeout or CONFIG.get("timeout_seconds", 15)
    cache_file = _cache_path(url)

    # -------------- CACHE ------------------
    if use_cache and os.path.exists(cache_file):
        with open(cache_file, "r", encoding="utf-8") as f:
            return f.read()

    # -------------- HEADERS ------------------
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Referer": "https://vtu.ac.in/",
        "DNT": "1"
    }

    session = requests.Session()

    try:
        resp = session.get(
            url,
            headers=headers,
            timeout=timeout,
            verify=False      # IMPORTANT for Cloudflare SSL handling
        )
    except Exception as e:
        raise Exception(f"Network error for {url}: {e}")

    # -------------- STATUS HANDLING ------------------
    if resp.status_code == 200:
        html = resp.text
        if use_cache:
            with open(cache_file, "w", encoding="utf-8") as f:
                f.write(html)
        time.sleep(CONFIG.get("rate_limit_seconds", 2))
        return html

    # Cloudflare block (403, 409, 503)
    if resp.status_code in (403, 409, 503):
        raise Exception(f"Cloudflare challenge {resp.status_code} for {url}")

    raise Exception(f"Failed HTTP {resp.status_code} for {url}")


def soupify(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "lxml")

