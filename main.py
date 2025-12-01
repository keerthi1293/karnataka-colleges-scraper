# main.py
from aicte_parser import load_aicte_karnataka
from ugc_parser import load_ugc_karnataka
from vtu_parser import load_vtu_rows
from utils import save_outputs, normalize_text
import pandas as pd
import argparse

def gather(limit_per_source=0):
    rows = []
    rows_a = load_aicte_karnataka()
    rows_u = load_ugc_karnataka()
    rows_v = load_vtu_rows()
    if limit_per_source>0:
        rows_a = rows_a[:limit_per_source]
        rows_u = rows_u[:limit_per_source]
        rows_v = rows_v[:limit_per_source]
    rows.extend(rows_a)
    rows.extend(rows_u)
    rows.extend(rows_v)
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    df['college_name'] = df['college_name'].apply(normalize_text)
    df['district'] = df['district'].apply(lambda x: normalize_text(x) if x else "-")
    df = df.drop_duplicates(subset=['college_name','district'], keep='first')
    return df

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit-per-source", type=int, default=0)
    args = parser.parse_args()
    print("[MAIN] Starting gather")
    df = gather(limit_per_source=args.limit_per_source)
    if df.empty:
        print("[MAIN] No rows extracted; exiting.")
        return
    print(f"[MAIN] {len(df)} unique colleges collected.")
    csv_path, json_path, sqlite_path = save_outputs(df)
    print("[MAIN] Saved outputs:", csv_path, json_path, sqlite_path)

if __name__ == "__main__":
    main()
