# college_page_parser.py -- find college placement/contact page and extract TPO details when available
from scraper_core import fetch_html, soupify
from utils import normalize_text, extract_phone
from urllib.parse import urljoin, urlparse
import re

CANDIDATE_PATHS = ["/placement", "/placement-cell", "/placementcell", "/placement.php", "/training-and-placement", "/contact", "/contact-us", "/contactus", "/about-us", "/about"]

TPO_LABELS = ["training & placement", "training and placement", "placement officer", "training & placement officer", "TPO", "placement cell", "placement officer"]

def find_college_site_from(seed_text: str) -> str:
    # attempt to pick url if seed_text contains http(s)
    import re
    m = re.search(r"https?://[^\s'\"<>]+", seed_text)
    return m.group(0) if m else "-"

def discover_and_extract_tpo(college_entry: dict) -> dict:
    """
    Given a partial record with maybe source_url or college_name, try to find college website and extract TPO name/phone
    This is best-effort. Returns updated entry with tpo_name, tpo_phone, and source_url set to the contact page if found.
    """
    source = college_entry.get("source_url","-")
    candidate_urls = []
    # If source is a college website already, use it
    if source and source.startswith("http"):
        candidate_urls.append(source)
    # Try common candidate paths if domain known
    if source and source.startswith("http"):
        parsed = urlparse(source)
        base = f"{parsed.scheme}://{parsed.netloc}"
        for p in CANDIDATE_PATHS:
            candidate_urls.append(urljoin(base, p))
    # Also try following website link from the source (if the source is a list/table page) -- handled by site-specific parsers
    # Try each candidate URL
    for url in candidate_urls:
        try:
            html = fetch_html(url)
        except Exception as e:
            continue
        soup = soupify(html)
        text = soup.get_text(separator=" ", strip=True).lower()
        # search for placement section
        for label in TPO_LABELS:
            if label in text:
                # find element containing label
                elems = soup.find_all(string=re.compile(re.escape(label), re.I))
                for el in elems:
                    container = el.parent
                    # search nearby for phone and names
                    context_text = " ".join(container.get_text(" ", strip=True).split())
                    # attempt to extract phone
                    phone = extract_phone(context_text)
                    # attempt to capture a name (heuristic: look for words with capitalized pattern preceding typical roles)
                    name = "-"
                    # pattern searching: look around for "Dr. X" or "Mr. X" etc within container
                    # fallback: look for lines with typical name patterns
                    lines = [l.strip() for l in context_text.splitlines() if l.strip()]
                    # scan tokens for candidate names (very heuristic)
                    for ln in lines:
                        # if line contains roles, remove them
                        if any(r in ln.lower() for r in ["placement", "training", "tpo", "officer"]):
                            # try to find names attached: e.g., "Placement Officer: Dr. A B"
                            parts = re.split(r":|-|–", ln)
                            if len(parts)>1:
                                candidate = parts[1].strip()
                                if len(candidate.split())>=2 and not any(c.isdigit() for c in candidate):
                                    name = candidate
                                    break
                    # if found, store and break
                    if phone == "-":
                        # try to find any phone on page
                        phone = extract_phone(text)
                    if name == "-":
                        # try to approximate name by scanning for 'Dr ' or 'Mr ' patterns
                        m = re.search(r"(Dr\.|Mr\.|Mrs\.|Ms\.)\s+[A-Z][a-zA-Z]+\s+[A-Z][a-zA-Z]+", soup.get_text())
                        if m:
                            name = m.group(0)
                    college_entry["tpo_name"] = name or "-"
                    college_entry["tpo_phone"] = phone or "-"
                    college_entry["source_url"] = url
                    return college_entry
    # if nothing found, leave defaults
    college_entry["tpo_name"] = college_entry.get("tpo_name","-") or "-"
    college_entry["tpo_phone"] = college_entry.get("tpo_phone","-") or "-"
    return college_entry
