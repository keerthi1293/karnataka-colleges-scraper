# site_parsers.py -- VTU parser that uses mirror URL or local snapshot

from scraper_core import fetch_html, soupify
from utils import normalize_text
import os, json

def parse_vtu_affiliated(_unused):
    """
    Try mirror URL first (raw GitHub). If that fails, look for local 'vtu_ajax_snapshot.html'.
    Returns list of college dicts.
    """

    # Load config.json
    mirror = None
    try:
        with open("config.json", "r", encoding="utf-8") as f:
            cfg = json.load(f)
            mirror = cfg.get("vtu_mirror_url")
    except Exception:
        mirror = None

    html = None

    # 1) Try mirror URL
    if mirror:
        print(f"[VTU] Trying mirror: {mirror}")
        try:
            html = fetch_html(mirror)
        except Exception as e:
            print("[VTU] Mirror fetch failed:", e)

    # 2) If mirror failed → try local snapshot
    if html is None:
        local = "vtu_ajax_snapshot.html"
        if os.path.exists(local):
            print("[VTU] Using local snapshot:", local)
            try:
                with open(local, "r", encoding="utf-8") as f:
                    html = f.read()
            except Exception as e:
                print("[VTU] Local snapshot error:", e)
                return []
        else:
            print("[VTU] No mirror or local snapshot available.")
            print("      Please upload 'vtu_ajax_snapshot.html' into the folder.")
            return []

    # 3) Parse HTML
    rows = []
    soup = soupify(html)
    tables = soup.find_all("table")
    if not tables:
        print("[VTU] No tables found in VTU HTML.")
        return []

    for table in tables:
        trs = table.find_all("tr")
        for tr in trs[1:]:  # skip header
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

    print(f"[VTU] Extracted {len(rows)} colleges.")
    return rows
