# utils.py -- helpers: normalize names, extract phone numbers, save outputs
import re, json, os, sqlite3, pandas as pd
from typing import Tuple

PHONE_RE = re.compile(r"(?:(?:\+?91[\-\s]?)?(?:\(?\d{3}\)?[\-\s]?\d{3}[\-\s]?\d{4}|\d{10}))")

def normalize_text(s: str) -> str:
    if not s: return ""
    return " ".join(s.replace("\xa0"," ").strip().split())

def extract_phone(s: str) -> str:
    if not s: return "-"
    m = PHONE_RE.search(s)
    return m.group(0) if m else "-"

def save_outputs(df, folder="output"):
    os.makedirs(folder, exist_ok=True)
    csv_path = os.path.join(folder, "colleges.csv")
    json_path = os.path.join(folder, "colleges.json")
    sqlite_path = os.path.join(folder, "colleges.sqlite")
    df.to_csv(csv_path, index=False, encoding="utf-8")
    df.to_json(json_path, orient="records", force_ascii=False)
    conn = sqlite3.connect(sqlite_path)
    df.to_sql("colleges", conn, if_exists="replace", index=False)
    conn.close()
    return csv_path, json_path, sqlite_path
