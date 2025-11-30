# sources.py -- list of data sources; parser selection uses keys here

import json
with open("config.json","r",encoding="utf-8") as f:
    CONFIG=json.load(f)

SOURCES = {
    "aicte": {
        "name": "AICTE - official institutes CSV",
        "url": CONFIG.get("aicte_csv_url"),
        "type": "csv"
    },
    "ugc": {
        "name": "UGC - colleges CSV",
        "url": CONFIG.get("ugc_csv_url"),
        "type": "csv"
    },
    "vtu": {
        "name": "VTU - snapshot/mirror (HTML)",
        "url": CONFIG.get("vtu_mirror_url"),
        "type": "html"
    }
}
