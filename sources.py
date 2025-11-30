import json

with open("config.json", "r", encoding="utf-8") as f:
    CONFIG = json.load(f)

# Only VTU enabled because DTE & AICTE block cloud scraping
SOURCES = {
    "vtu_affiliated": {
        "name": "VTU - Affiliated Institutes",
        "url": CONFIG["sources"]["vtu_affiliated"],
        "type": "html_table",
        "priority": 1
    }
}
