# main.py -- main orchestrator: loads sources, runs parsers, attempts TPO fetches, and writes output
import json
from sources import SOURCES
from site_parsers import parse_dte_karnataka, parse_vtu_affiliated
from college_page_parser import discover_and_extract_tpo
from utils import normalize_text, save_outputs
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse

PARSER_MAP = {
    "dte_karnataka": parse_dte_karnataka,
    "vtu_affiliated": parse_vtu_affiliated
}

def gather_from_sources(limit_per_source=0):
    rows = []
    for key, meta in SOURCES.items():
        print(f"[+] Processing source: {meta['name']} ({meta['url']})")
        parser = PARSER_MAP.get(key)
        if parser is None:
            print(f"[-] No parser for {key}, skipping. Consider adding a parser for {meta['url']}")
            continue
        try:
            extracted = parser(meta["url"])
            print(f"    -> {len(extracted)} rows extracted (raw)")
            if limit_per_source>0:
                extracted = extracted[:limit_per_source]
            rows.extend(extracted)
        except Exception as e:
            print(f"    Error parsing {meta['url']}: {e}")
    # de-duplicate by college_name + district
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    df["college_name_norm"] = df["college_name"].apply(normalize_text)
    df = df.drop_duplicates(subset=["college_name_norm","district"], keep="first")
    df = df.drop(columns=["college_name_norm"])
    return df

def fetch_tpos(df, max_workers=4):
    updated = []
    with ThreadPoolExecutor(max_workers=max_workers) as exe:
        futures = {exe.submit(discover_and_extract_tpo, row.to_dict()): idx for idx,row in df.iterrows()}
        for fut in as_completed(futures):
            try:
                res = fut.result()
                updated.append(res)
            except Exception as e:
                print("Error fetching TPO for an item:", e)
    return pd.DataFrame(updated)

def main(args):
    df = gather_from_sources(limit_per_source=args.limit_per_source)
    if df.empty:
        print("No rows extracted; exiting.")
        return
    print(f"[+] Starting to fetch TPO details for {len(df)} colleges (this may take time)...")
    df2 = fetch_tpos(df, max_workers=args.max_workers)
    # final normalization: fill missing TPOs with '-'
    for col in ["tpo_name","tpo_phone","affiliating_university"]:
        if col in df2.columns:
            df2[col] = df2[col].fillna("-").replace("", "-")
    # reorder columns
    cols = ["college_name","city_town","district","affiliating_university","tpo_name","tpo_phone","source_url"]
    for c in cols:
        if c not in df2.columns:
            df2[c] = "-"
    df_out = df2[cols]
    csv_path, json_path, sqlite_path = save_outputs(df_out)
    print("[+] Saved outputs:", csv_path, json_path, sqlite_path)
    print("[+] Done.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit-per-source", type=int, default=0, help="Limit rows per source (0 = all)")
    parser.add_argument("--max-workers", type=int, default=4, help="Concurrency for fetching college pages")
    args = parser.parse_args()
    main(args)
