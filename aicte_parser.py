# aicte_parser.py -- load AICTE institutions CSV and normalize rows for Karnataka

import os, pandas as pd
from scraper_core import fetch_html
from utils import normalize_text

EXPECTED_LOCAL = "aicte_institutes.csv"

def load_aicte_rows(url=None):
    """
    Tries to download CSV from url. If not available, tries local file EXPECTED_LOCAL.
    Returns list of dict rows mapped to required columns.
    """
    csv_path = None
    if url:
        try:
            html = fetch_html(url)
            # try to save to local temp
            csv_path = "aicte_download.csv"
            with open(csv_path,"w",encoding="utf-8") as f:
                f.write(html)
        except Exception as e:
            print("[AICTE] Could not download CSV, will try local file:", e)

    if csv_path is None or not os.path.exists(csv_path):
        if os.path.exists(EXPECTED_LOCAL):
            csv_path = EXPECTED_LOCAL
        else:
            print("[AICTE] No AICTE CSV found. Please upload 'aicte_institutes.csv' to workspace.")
            return []

    try:
        df = pd.read_csv(csv_path, dtype=str, encoding="utf-8", low_memory=False)
    except Exception:
        df = pd.read_excel(csv_path, dtype=str)

    rows = []
    # heuristics: look for Karnataka rows via column names
    df_cols = [c.lower() for c in df.columns]
    # Try to find columns for name, state, district, university, website, phone
    def find(colnames):
        for name in colnames:
            for c in df.columns:
                if name in c.lower():
                    return c
        return None

    col_name = find(["institute name","inst name","institute"])
    col_state = find(["state"])
    col_district = find(["district"])
    col_city = find(["city","place","town"])
    col_univ = find(["affiliat","university"])
    col_phone = find(["phone","telephone","contact"])
    col_website = find(["website","web"])

    for _, r in df.iterrows():
        state = str(r.get(col_state,"")).strip()
        if state.lower() != "karnataka" and "karnataka" not in state.lower():
            continue
        name = normalize_text(r.get(col_name,"-"))
        city = normalize_text(r.get(col_city,"-"))
        district = normalize_text(r.get(col_district,"-"))
        affiliating_university = normalize_text(r.get(col_univ,"-"))
        website = normalize_text(r.get(col_website,"-"))
        phone = normalize_text(r.get(col_phone,"-"))
        rows.append({
            "college_name": name or "-",
            "city_town": city or "-",
            "district": district or "-",
            "affiliating_university": affiliating_university or "-",
            "tpo_name": "-",
            "tpo_phone": phone or "-",
            "source_url": csv_path
        })
    print(f"[AICTE] Extracted {len(rows)} Karnataka rows from AICTE list")
    return rows
