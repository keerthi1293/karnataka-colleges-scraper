# vtu_parser.py
import os, re
from scraper_core import fetch_text, soupify
from utils import normalize_text
from sources import VTU_AJAX, VTU_PAGES

def parse_vtu_ajax():
    if not VTU_AJAX:
        return []
    try:
        print("[VTU] Trying AJAX endpoint")
        html = fetch_text(VTU_AJAX)
        return parse_html_tables(html, source=VTU_AJAX)
    except Exception as e:
        print("[VTU] AJAX failed:", e)
        return []

def parse_vtu_region_pages():
    rows = []
    for url in VTU_PAGES:
        try:
            print("[VTU] Trying region page:", url)
            html = fetch_text(url)
            rows.extend(parse_html_tables(html, source=url))
        except Exception as e:
            print("[VTU] region page failed:", e)
    return rows

def parse_local_snapshot():
    local = "vtu_ajax_snapshot.html"
    if os.path.exists(local):
        print("[VTU] Using local snapshot")
        html = open(local,"r",encoding="utf-8").read()
        return parse_html_tables(html, source=local)
    return []

def parse_html_tables(html, source):
    soup = soupify(html)
    rows = []
    tables = soup.find_all("table")
    for table in tables:
        trs = table.find_all("tr")
        if len(trs) < 2:
            continue
        for tr in trs[1:]:
            tds = tr.find_all("td")
            cols = [normalize_text(td.get_text()) for td in tds]
            if len(cols) >= 3:
                rows.append({
                    "college_name": cols[0],
                    "city_town": cols[1],
                    "district": cols[2],
                    "affiliating_university": "VTU",
                    "tpo_name": "-",
                    "tpo_phone": "-",
                    "source_url": source
                })
    print(f"[VTU] parse_html_tables found {len(rows)} rows from {source}")
    return rows

def load_vtu_rows():
    # 1: AJAX
    rows = parse_vtu_ajax()
    if rows: return rows
    # 2: region pages
    rows = parse_vtu_region_pages()
    if rows: return rows
    # 3: local snapshot
    rows = parse_local_snapshot()
    if rows: return rows
    print("[VTU] No VTU data available - please upload 'vtu_ajax_snapshot.html' or add a mirror URL to config.json")
    return []
