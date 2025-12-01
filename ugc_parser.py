# ugc_parser.py
import os, io, pandas as pd
from scraper_core import fetch_text
from utils import normalize_text
from sources import UGC_URLS

EXPECTED_LOCAL = "ugc_colleges.csv"

def load_ugc_karnataka():
    csv_path = None
    for url in UGC_URLS:
        if not url: continue
        try:
            print("[UGC] Trying", url)
            text = fetch_text(url)
            df = pd.read_csv(io.StringIO(text), dtype=str)
            csv_path = "ugc_download.csv"
            df.to_csv(csv_path, index=False, encoding="utf-8")
            break
        except Exception as e:
            print("[UGC] download failed:", e)
    if csv_path is None:
        if os.path.exists(EXPECTED_LOCAL):
            csv_path = EXPECTED_LOCAL
        else:
            print("[UGC] No UGC CSV available. Please upload 'ugc_colleges.csv' to the workspace.")
            return []
    try:
        df = pd.read_csv(csv_path, dtype=str, encoding="utf-8", low_memory=False)
    except Exception:
        df = pd.read_excel(csv_path, dtype=str)
    def find(cols):
        for c in df.columns:
            low = c.lower()
            for k in cols:
                if k in low:
                    return c
        return None
    name_col = find(["college name","name","inst"])
    state_col = find(["state","st"])
    city_col = find(["city","place","town"])
    district_col = find(["district"])
    univ_col = find(["affiliat","university"])
    rows = []
    if name_col is None:
        print("[UGC] Couldn't find name column; returning empty list.")
        return []
    for _, r in df.iterrows():
        state = str(r.get(state_col,"")) if state_col else ""
        if "karnataka" not in state.lower():
            continue
        name = normalize_text(r.get(name_col,"-"))
        city = normalize_text(r.get(city_col,"-") if city_col else "-")
        district = normalize_text(r.get(district_col,"-") if district_col else "-")
        affiliating_university = normalize_text(r.get(univ_col,"-") if univ_col else "-")
        rows.append({
            "college_name": name or "-",
            "city_town": city or "-",
            "district": district or "-",
            "affiliating_university": affiliating_university or "-",
            "tpo_name": "-",
            "tpo_phone": "-",
            "source_url": csv_path
        })
    print(f"[UGC] Extracted {len(rows)} Karnataka rows from UGC data")
    return rows
