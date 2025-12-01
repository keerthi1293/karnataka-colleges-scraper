# merge_tpo.py
import pandas as pd

main_df = pd.read_csv("output/colleges.csv")
tpo_df  = pd.read_csv("output/tpo_verification_sheet.csv")

merged = pd.merge(
    main_df,
    tpo_df[["college_name", "TPO_NAME", "TPO_PHONE", "TPO_EMAIL"]],
    on="college_name",
    how="left"
)

merged.to_csv("output/final_karnataka_colleges.csv", index=False)
print("Final dataset generated: output/final_karnataka_colleges.csv")
