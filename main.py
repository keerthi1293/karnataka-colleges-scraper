# main.py -- orchestrator: loads AICTE + UGC + VTU, merges, attempts TPO extraction and saves outputs

import argparse, time
from sources import SOURCES
from aicte_parser import load_aicte_rows
from ugc_parser import load_ugc_rows
from site_parsers import parse_vtu_affiliated
from college_page_parser import discover_and_extract_tpo
from utils import save_outputs, normalize_text
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed

def gather(limit_per_source=0):
    rows = []
    # AICTE
    aicte_meta = SOURCES.get("aicte")
    if aicte_meta:
        try:
            rows_a = load_aicte_rows(aicte_meta.get("url"))
            if limit_per_source>0: rows_a = rows_a[:limit_per_source]
            rows.extend(rows_a)
        except Exception as e:
            print("[MAIN] AICTE error:", e)
    # UGC
    ugc_meta = SOURCES.get("ugc")
    if ugc_meta:
        try:
            rows_u = load_ugc_rows(ugc_meta.get("url"))
            if limit_per_source>0: rows_u = rows_u[:limit_per_source]
            rows.extend(rows_u)
        except Exception as e:
            print("[MAIN] UGC error:", e)
    # VTU
    vtu_meta = SOURCES.get("vtu")
    try:
        rows_v = parse_vtu_affiliated(None)
        if limit_per_source>0: rows_v = rows_v[:limit_per_source]
        rows.extend(rows_v)
    except Exception as e:
        print("[MAIN] VTU error:", e)

    # normalize and dedupe by (college_name + district)
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    df['college_name'] = df['college_name'].apply(normalize_text)
    df['district'] = df['district'].apply(lambda x: normalize_text(x) if x else "-")
    df = df.drop_duplicates(subset=['college_name','district'], keep='first')
    return df

def enrich_tpos(df, max_workers=6):
    df = df.copy().reset_index(drop=True)
    rows = []
    with ThreadPoolExecutor(max_workers=max_workers) as exe:
        futures = {exe.submit(discover_and_extract_tpo, row.to_dict()): idx for idx,row in df.iterrows()}
        for fut in as_completed(futures):
            try:
                res = fut.result()
                rows.append(res)
            except Exception as e:
                print("TPO fetch error:", e)
    return pd.DataFrame(rows)

def main(args):
    print("[MAIN] Starting gather")
    df = gather(limit_per_source=args.limit_per_source)
    if df.empty:
        print("[MAIN] No rows extracted; exiting.")
        return
    print(f"[MAIN] {len(df)} unique colleges collected. Starting TPO enrichment (this may take time).")
    df_enriched = enrich_tpos(df, max_workers=args.max_workers)
    # finalize columns
    cols = ["college_name","city_town","district","affiliating_university","tpo_name","tpo_phone","source_url"]
    for c in cols:
        if c not in df_enriched.columns:
            df_enriched[c] = "-"
    df_out = df_enriched[cols]
    csv_path, json_path, sqlite_path = save_outputs(df_out)
    print("[MAIN] Saved outputs:", csv_path, json_path, sqlite_path)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit-per-source", type=int, default=0)
    parser.add_argument("--max-workers", type=int, default=4)
    args = parser.parse_args()
    main(args)
