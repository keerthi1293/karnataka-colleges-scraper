# site_parsers.py -- VTU parser that uses mirror URL or local snapshot

from scraper_core import fetch_html, soupify
from utils import normalize_text
import os

def parse_vtu_affiliated(_):
    """
    Try mirror URL first (raw GitHub). If that fails, look for local 'vtu_ajax_snapshot.html'.
    """
    from config import CONFIG if False else None  # no-op; keep for clarity
    mirror = None
    try:
        import json
        with open("config.json","r",encoding="utf-8") as f:
            cfg = json.load(f)
            mirror = cfg.get("vtu_mirror_url")
    except Exception:
        mirror = None

    html = None
    if mirror:
        try:
            print(f"[VTU] Trying mirror: {mirror}")
            html = fetch_html(mirror)
        except Exception as e:
            print("[VTU] Mirror fetch failed:", e)

    if html is None:
        local = "vtu_ajax_snapshot.html"
        if os.path.exists(local):
            print("[VTU] Loading local snapshot:", local)
            with open(local,"r",encoding="utf-8") as f:
                html = f.read()
        else:
            print("[VTU] No mirror or local VTU snapshot available. Please upload 'vtu_ajax_snapshot.html' or set a mirror URL in config.json.")
            return []

    soup = soupify(html)
    rows = []
    tables = soup.find_all("table")
    for table in tables:
        for tr in table.find_all("tr")[1:]:
            cols = [normalize_text(td.get_text()) for td in tr.find_all("td")]
            if len(cols) >= 3:
                rows.append({
                    "college_name": cols[0],
                    "city_town": cols[1],
                    "district": cols[2],
                    "affiliating_university": "VTU",
                    "tpo_name": "-",
                    "tpo_phone": "-",
                    "source_url": mirror or local
                })
    print(f"[VTU] Extracted {len(rows)} colleges from VTU source")
    return rows
