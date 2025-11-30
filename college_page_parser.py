# college_page_parser.py -- heuristics to extract TPO name and phone from college website pages

from scraper_core import fetch_html, soupify
from utils import extract_phone, normalize_text
from urllib.parse import urljoin, urlparse
import re, time

CANDIDATE_PATHS = ["/placement", "/placement-cell", "/placementcell", "/placement.php",
                   "/training-and-placement", "/contact", "/contact-us", "/about-us", "/faculty"]

TPO_LABELS = ["training & placement", "training and placement", "placement officer",
              "training & placement officer", "tpo", "placement cell", "placement officer"]

def discover_and_extract_tpo(entry, max_attempts=5):
    """
    entry: dict containing at least college_name and possibly source_url or website
    Will try to find college website (from 'source_url' or 'website' key) and search common pages.
    Returns updated entry with tpo_name and tpo_phone (or '-') and updated source_url to used page.
    """

    # if source_url looks like a college site (contains domain other than vtu/aicte), use it
    src = entry.get("source_url","")
    website_candidates = []

    # If entry has explicit website field
    if entry.get("website"):
        website_candidates.append(entry.get("website"))

    if src and src.startswith("http"):
        # if src is a mirror or csv, skip; try to parse a website if present in row
        pass

    # Try common domain guesses using college name -> create slug? (last resort)
    # We won't attempt aggressive search engines; instead use website candidates when available.

    # Preferred: if entry has 'college_website' or 'website' field, try it
    for url in website_candidates:
        try:
            html = fetch_html(url)
        except Exception:
            continue
        soup = soupify(html)
        tpo = search_tpo_in_soup(soup)
        if tpo:
            entry["tpo_name"] = tpo.get("name","-")
            entry["tpo_phone"] = tpo.get("phone","-")
            entry["source_url"] = url
            return entry

    # If no explicit website, attempt searching candidate paths on source domain if it's a college url
    # If entry.source_url is a CSV path, skip
    if src and src.startswith("http") and "raw.githubusercontent" not in src and "aicte" not in src and "ugc" not in src and "vtu" not in src:
        parsed = urlparse(src)
        base = f"{parsed.scheme}://{parsed.netloc}"
        for p in CANDIDATE_PATHS:
            url = urljoin(base, p)
            try:
                html = fetch_html(url)
            except Exception:
                continue
            soup = soupify(html)
            tpo = search_tpo_in_soup(soup)
            if tpo:
                entry["tpo_name"] = tpo.get("name","-")
                entry["tpo_phone"] = tpo.get("phone","-")
                entry["source_url"] = url
                return entry

    # Not found
    entry["tpo_name"] = entry.get("tpo_name","-") or "-"
    entry["tpo_phone"] = entry.get("tpo_phone","-") or "-"
    return entry

def search_tpo_in_soup(soup):
    """
    Search the soup text for TPO patterns and phone numbers; return dict with name and phone if found.
    """
    text = soup.get_text(" ", strip=True)
    low = text.lower()
    # find a block around keywords
    idx = None
    for lbl in TPO_LABELS:
        idx = low.find(lbl)
        if idx != -1:
            break
    if idx == -1:
        return None
    # take snippet
    start = max(0, idx-300)
    snippet = text[start: idx+400]
    phone = extract_phone(snippet)
    # try to extract name via regex: look for "Placement Officer: Name"
    m = re.search(r"(Placement|TPO|Training & Placement|Training and Placement)[:\-\s]*([A-Z][A-Za-z\.\s]{2,80})", snippet, re.I)
    name = m.group(2).strip() if m else "-"
    return {"name": normalize_text(name), "phone": phone or "-"}
