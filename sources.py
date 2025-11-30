import json

with open("config.json", "r", encoding="utf-8") as f:
    CONFIG = json.load(f)

SOURCES = {
    "dte_karnataka": {
        "name": "DTE Karnataka - Engineering Colleges",
        "url": CONFIG["sources"]["dte_karnataka"],
        "type": "html_table",
        "priority": 1
    },
    "vtu_affiliated": {
        "name": "VTU - Affiliated Institutes",
        "url": CONFIG["sources"]["vtu_affiliated"],
        "type": "html_table",
        "priority": 1
    },
    "aicte": {
        "name": "AICTE - Approved Institutes",
        "url": CONFIG["sources"]["aicte"],
        "type": "portal",
        "priority": 2
    }
}
