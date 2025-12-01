# sources.py
import json
with open("config.json","r",encoding="utf-8") as f:
    CONFIG = json.load(f)

AICTE_URLS = CONFIG.get("aicte_urls", [])
UGC_URLS = CONFIG.get("ugc_urls", [])
VTU_AJAX = CONFIG.get("vtu_ajax")
VTU_PAGES = CONFIG.get("vtu_region_pages", [])
