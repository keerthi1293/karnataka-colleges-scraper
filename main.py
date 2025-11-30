# main.py -- main orchestrator: loads sources, runs parsers, saves output

import json
import pandas as pd
from sources import SOURCES
from site_parsers import parse_vtu_affiliated, parse_dte_karnataka
from utils import save_outputs, normalize_text

PARSER_MAP = {
    "vtu_affiliated": parse_vtu_affiliated,
    "dte_karnataka": parse_dte_karnataka
}

def gather_from_sources():
    rows = []

    for key, meta in SOURCES.items():
        print(f"[+] Processing source: {meta['name']}")

        parser = PARSER_MAP.get(key)
        if parser is None:
            print(f"[-] No parser for {key}, skipping.")
            continue

        try:
            # IMPORTANT: do NOT pass the old URL,
            # the parser already knows the mirror URL internally.
            extracted = parser(None)
            print(f"    -> {len(extracted)} rows extracted (raw)")
            rows.extend(extracted)
        except Exception as e:
            print(f"    Error parsing {meta['name']}: {e}")

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    # Deduplicate
    df["college_name_norm"] = df["college_name"].apply(normalize_text)
    df = df.drop_duplicates(subset=["college_name_norm", "district"], keep="first")
    df = df.drop(columns=["college_name_norm"])

    return df


def main():
    df = gather_from_sources()

    if df.empty:
        print("No rows extracted; exiting.")
        return

    cols = ["college_name", "city_town", "district",
            "affiliating_university", "tpo_name", "tpo_phone", "source_url"]

    for c in cols:
        if c not in df.columns:
            df[c] = "-"

    df = df[cols]

    save_outputs(df)
    print("\n[+] Saved all output files inside output/")


if __name__ == "__main__":
    main()
