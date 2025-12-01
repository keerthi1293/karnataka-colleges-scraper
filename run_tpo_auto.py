# filename: run_tpo_auto.py
# One-line: runs high-accuracy auto TPO enrichment and saves final CSV.

import pandas as pd
from tpo_auto_enrichment import auto_enrich_dataframe

IN_FILE = "output/colleges.csv"
OUT_FILE = "output/final_karnataka_colleges_tpo_high_accuracy.csv"

print("[RUN] Loading", IN_FILE)
df = pd.read_csv(IN_FILE, dtype=str)
df.fillna("-", inplace=True)

print("[RUN] Running high-accuracy TPO enrichment. This may take time (network-bound).")
df_out = auto_enrich_dataframe(df, max_workers=6, strict=True)

# keep desired columns and order
desired_cols = [
    "college_name", "city_town", "district", "affiliating_university",
    "TPO_NAME", "TPO_EMAIL", "TPO_PHONE", "tpo_confidence_score",
    "tpo_website_used", "tpo_placement_page", "source_url"
]
for c in desired_cols:
    if c not in df_out.columns:
        df_out[c] = "-"

df_out = df_out[desired_cols]
df_out.to_csv(OUT_FILE, index=False, encoding="utf-8")
print("[RUN] Saved:", OUT_FILE)
print("[RUN] Summary: total rows:", len(df_out))
print(df_out[["college_name","TPO_NAME","TPO_EMAIL","TPO_PHONE","tpo_confidence_score"]].head(10))
