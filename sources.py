import json

with open("config.json", "r", encoding="utf-8") as f:
    CONFIG = json.load(f)

# Only VTU source enabled
SOURCES = {
    "vtu_affiliated": {
        "name": "VTU - Affiliated Institutes",
        "url": CONFIG["sources"]["vtu_affiliated"],
        "type": "html_table",
        "priority": 1
    }
}

# DTE & AICTE removed because:
# - DTE blocks scripts and times out
# - AICTE requires complex scraping or PDF parsing
