# ugc_parser.py -- load UGC colleges CSV and extract Karnataka degree colleges

import os, pandas as pd
from scraper_core import fetch_html
from utils import normalize_text

EXPECTED_LOCAL = "ugc_colleges.csv"

def load_ugc_rows(url=None):
    csv_path = None
    if url:
        try:
            html = fetch_html(url)
            csv_path = "ugc_download.csv"
            with open(csv_path,"w",encoding="utf-8") as f:
                f.write(html)
        except Exception as e:
            print("[UGC] Could not download CSV, will try local file:", e)

    if csv_path is None or not os.path.exists(csv_path):
        if os.path.exists(EXPECTED_LOCAL):
            csv_path = EXPECTED_LOCAL
        else:
            print("[UGC] No UGC CSV found. Please upload 'ugc_colleges.csv' to workspace.")
            return []

    try:
        df = pd.read_csv(csv_path, dtype=str, encoding="utf-8", low_memory=False)
    except Exception:
        df = pd.read_excel(csv_path, dtype=str)

    rows = []
    def find(colnames):
        for name in colnames:
            for c in df.columns:
                if name in c.lower():
                    return c
        return None

    col_name = find(["college name","name","inst"])
    col_state = find(["state","st"])
    col_district = find(["district"])
    col_city = find(["city","place","town"])
    col_univ = find(["affiliat","university"])

    for _, r in df.iterrows():
        state = str(r.get(col_state,"")).strip()
        if state.lower() != "karnataka" and "karnataka" not in state.lower():
            continue
        name = normalize_text(r.get(col_name,"-"))
        city = normalize_text(r.get(col_city,"-"))
        district = normalize_text(r.get(col_district,"-"))
        affiliating_university = normalize_text(r.get(col_univ,"-"))
        rows.append({
            "college_name": name or "-",
            "city_town": city or "-",
            "district": district or "-",
            "affiliating_university": affiliating_university or "-",
            "tpo_name": "-",
            "tpo_phone": "-",
            "source_url": csv_path
        })
    print(f"[UGC] Extracted {len(rows)} Karnataka rows from UGC list")
    return rows
