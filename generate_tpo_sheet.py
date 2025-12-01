# generate_tpo_sheet.py
import pandas as pd
from tpo_enrichment import enrich_dataset

df = pd.read_csv("output/colleges.csv")
df = df.drop_duplicates(subset=["college_name"])

enriched = enrich_dataset(df)
enriched.to_csv("output/tpo_verification_sheet.csv", index=False)

print("Generated: output/tpo_verification_sheet.csv")
print("Please open this file and fill TPO_NAME and TPO_PHONE columns manually.")
