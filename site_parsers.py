# site_parsers.py -- extract college rows from specific authoritative pages (DTE, VTU)
from scraper_core import fetch_html, soupify
from utils import normalize_text, extract_phone
from typing import List, Dict
from bs4 import BeautifulSoup
import re

def parse_dte_karnataka(url:str) -> List[Dict]:
    """
    Parse the DTE Karnataka engineering colleges page.
    Returns list of dicts with keys: college_name, city_town, district, affiliating_university, source_url
    """
    html = fetch_html(url)
    soup = soupify(html)
    rows = []
    # Heuristic: find table(s) with institute listing based on visible headers "Institute", "Place", "District"
    tables = soup.find_all("table")
    for table in tables:
        ths = [normalize_text(th.get_text()) for th in table.find_all("th")]
        if any("Institute" in t or "Institute Name" in t or "Institute" in t for t in ths) and any("District" in t for t in ths):
            for tr in table.find_all("tr")[1:]:
                cols = [normalize_text(td.get_text()) for td in tr.find_all(["td","th"])]
                if not cols: continue
                # best-effort mapping: assume first col institute, second place/city, third district
                college = {
                    "college_name": cols[0] if len(cols)>0 else "-",
                    "city_town": cols[1] if len(cols)>1 else "-",
                    "district": cols[2] if len(cols)>2 else "-",
                    "affiliating_university": "-",
                    "tpo_name":"-",
                    "tpo_phone":"-",
                    "source_url": url
                }
                rows.append(college)
            break
    return rows

def parse_vtu_affiliated(url:str) -> List[Dict]:
    """
    Parse the VTU affiliated-institute page and extract colleges + phone if present
    """
    html = fetch_html(url)
    soup = soupify(html)
    rows = []
    # VTU has many one-page lists and regional pages. Look for <table> with college names.
    for table in soup.find_all("table"):
        headers = [normalize_text(th.get_text()) for th in table.find_all("th")]
        # heuristics
        if any("College" in h or "Institute" in h for h in headers):
            for tr in table.find_all("tr")[1:]:
                tds = tr.find_all("td")
                if not tds: continue
                # find columns
                cols = [normalize_text(td.get_text()) for td in tds]
                # guess mapping: college, place, district, phone, website
                college_name = cols[0] if len(cols)>0 else "-"
                city_town = cols[1] if len(cols)>1 else "-"
                district = cols[2] if len(cols)>2 else "-"
                phone = cols[3] if len(cols)>3 else "-"
                # look for website link in row
                website = "-"
                link = tr.find("a", href=True)
                if link:
                    website = link["href"].strip()
                rows.append({
                    "college_name": college_name,
                    "city_town": city_town,
                    "district": district,
                    "affiliating_university": "Visvesvaraya Technological University (VTU)",
                    "tpo_name":"-",
                    "tpo_phone": extract_phone(phone),
                    "source_url": url if website=="-" else website
                })
            break
    return rows
