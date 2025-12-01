# filename: tpo_auto_enrichment.py
# One-line: Automatic high-accuracy TPO extractor (strict mode).
#
# Usage: import and call auto_enrich_dataframe(df, workers=4, strict=True)
# Output: DataFrame with columns TPO_NAME, TPO_EMAIL, TPO_PHONE, tpo_confidence_score

import re, time, math
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed

# Polite headers
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36"
}

# Regexes
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", re.I)
PHONE_RE = re.compile(r"(?:\+91[\-\s]?)?(?:\d{10}|\d{3}[\-\s]\d{3}[\-\s]\d{4})")
NAME_CANDIDATE_RE = re.compile(r"(?:Mr\.|Mrs\.|Ms\.|Dr\.|Prof\.|Sri\.|Smt\.)?\s?[A-Z][a-z]+(?:\s[A-Z][a-z]+){0,3}")

PLACEMENT_KEYWORDS = [
    "placement", "training", "training & placement", "tpo", "placement cell",
    "career", "recruit", "career development", "industry relations"
]
CONTACT_KEYWORDS = ["contact", "contact-us", "contactus", "faculty", "staff", "office", "people"]

# Scoring rules (strict)
# email score: if local-part contains placement/tpo -> +4 ; if domain contains placement -> +3 ; else +1 for any email on placement page
# phone score: if phone appears within window of keyword -> +3 ; else +1
# name score: if name adjacent to keyword text -> +3 ; else +1
# final threshold (strict) = 4

TIMEOUT = 10
REQUEST_SLEEP = 0.6  # polite

def safe_get(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT, verify=False)
        if r.status_code == 200:
            return r.text
    except Exception:
        return None
    return None

def normalize_text(s):
    if s is None:
        return ""
    return " ".join(str(s).replace("\xa0", " ").split()).strip()

def is_placement_anchor(text, href):
    txt = (text or "").lower()
    href_l = (href or "").lower()
    if any(k in txt for k in PLACEMENT_KEYWORDS):
        return True
    if any(k in href_l for k in PLACEMENT_KEYWORDS):
        return True
    return False

def find_candidate_pages(home_html, base_url):
    """
    From homepage HTML, return candidate URLs (placement/contact pages) in priority order.
    """
    pages = []
    try:
        soup = BeautifulSoup(home_html, "lxml")
    except Exception:
        return pages

    # First pass: anchors with placement keywords in text or href
    for a in soup.find_all("a", href=True):
        text = normalize_text(a.get_text())
        href = a["href"]
        if is_placement_anchor(text, href):
            full = urljoin(base_url, href)
            pages.append(full)

    # second pass: contact/staff pages
    for a in soup.find_all("a", href=True):
        text = normalize_text(a.get_text())
        href = a["href"]
        if any(k in text.lower() for k in CONTACT_KEYWORDS) or any(k in href.lower() for k in CONTACT_KEYWORDS):
            full = urljoin(base_url, href)
            pages.append(full)

    # dedupe preserving order
    seen = set()
    pages_clean = []
    for p in pages:
        p_n = p.split('#')[0].rstrip('/')
        if p_n not in seen:
            seen.add(p_n)
            pages_clean.append(p_n)
    return pages_clean

def extract_from_html(html):
    """Return emails, phones and candidate text blocks"""
    if not html:
        return [], [], []

    text = html
    emails = list(set(EMAIL_RE.findall(text)))
    phones = list(set(PHONE_RE.findall(text)))

    # collect text blocks around keywords to find names near keywords
    blocks = []
    low = text.lower()
    for kw in PLACEMENT_KEYWORDS:
        idx = low.find(kw)
        if idx != -1:
            start = max(0, idx-250)
            end = min(len(text), idx+250)
            block = text[start:end]
            blocks.append(block)

    # if no keyword block, fallback to entire text chunks (split by <p>, <div> tags)
    if not blocks:
        # naive paragraphs splitting
        parts = re.split(r"</p>|<br|</div>", text, flags=re.I)
        for p in parts[:5]:
            if len(p) > 50:
                blocks.append(p)

    # find names in blocks
    names = []
    for block in blocks:
        for m in NAME_CANDIDATE_RE.finditer(block):
            n = " ".join(m.group().split())
            if len(n) >= 3 and len(n) <= 50:
                names.append(n)

    names = list(dict.fromkeys(names))  # keep order unique
    return emails, phones, names

def score_candidate(email=None, phone=None, name=None, context_text=""):
    """
    Score a candidate using strict rules. Higher is better.
    Strict threshold ~4
    """
    score = 0
    ctx = (context_text or "").lower()

    if email:
        local = email.split("@")[0].lower()
        domain = email.split("@")[-1].lower()
        if any(k in local for k in ["tpo", "placement", "career", "train"]):
            score += 4
        elif any(k in domain for k in ["placement", "tpo", "career", "train"]):
            score += 3
        else:
            # email on a placement page is still a signal
            score += 1

    if phone:
        # if phone appears close to keyword in context text
        if any(k in ctx for k in PLACEMENT_KEYWORDS):
            score += 3
        else:
            score += 1

    if name:
        # if name string appears in context with keyword, good signal
        if any(k in ctx for k in PLACEMENT_KEYWORDS):
            score += 3
        else:
            # small credit
            score += 1

    # small normalization
    return score

def choose_tpo_for_college(college_row, strict=True):
    """
    Given a row with columns: college_name, source_url (optional), maybe website in extra column,
    attempt to find a high-confidence TPO. Returns dict with tpo_name/tpo_email/tpo_phone/score/placement_page/website
    """
    name = normalize_text(college_row.get("college_name", ""))
    # prefer website column if exists
    website_candidates = []
    if "website" in college_row and college_row.get("website"):
        website_candidates.append(college_row.get("website"))
    # fallback: try using source_url if it looks like a domain
    src = college_row.get("source_url", "")
    if isinstance(src, str) and src.startswith("http") and "github" not in src and "aicte" not in src and "ugc" not in src:
        parsed = urlparse(src)
        base = f"{parsed.scheme}://{parsed.netloc}"
        website_candidates.append(base)

    # If nothing, try quick guessed domain (less reliable) - optional
    # Not performing Google search to avoid fragility & TOS issues.

    # normalize candidates
    website_candidates = [w.rstrip("/") for w in website_candidates if w and isinstance(w, str)]
    website_candidates = list(dict.fromkeys(website_candidates))  # dedupe

    # Fetch homepage for each website candidate until we find a good placement page
    for website in website_candidates:
        html = safe_fetch(website)
        if not html:
            continue
        pages = find_candidate_pages(html, website)
        # include homepage as last resort
        pages = pages + [website]
        # examine candidate pages in priority order
        best = None  # tuple (score, email, phone, name, placement_page, context)
        for p in pages:
            p_html = safe_fetch(p)
            emails, phones, names = extract_from_html(p_html)
            # build candidate list and contexts (use page text as context)
            context = (p_html or "")[:5000]
            # evaluate email-first candidates
            for e in emails:
                sc = score_candidate(email=e, phone=None, name=None, context_text=context)
                if best is None or sc > best[0]:
                    best = (sc, e, None, None, p, context)
            # then phone-first
            for ph in phones:
                sc = score_candidate(email=None, phone=ph, name=None, context_text=context)
                if best is None or sc > best[0]:
                    best = (sc, None, ph, None, p, context)
            # then name-first
            for nm in names:
                sc = score_candidate(email=None, phone=None, name=nm, context_text=context)
                if best is None or sc > best[0]:
                    best = (sc, None, None, nm, p, context)

            # if we have a candidate that already meets strict threshold, stop early
            if best and best[0] >= 4:
                # pick best and return
                sc, e, ph, nm, page, ctx = best
                return {
                    "tpo_name": nm if nm and nm != "" else "-",
                    "tpo_email": e if e else "-",
                    "tpo_phone": ph if ph else "-",
                    "tpo_conf_score": sc,
                    "placement_page": page,
                    "website": website
                }

        # no high confidence in this website; continue to next website candidate

    # No website candidates produced high-confidence result. Strict mode: return blanks.
    return {
        "tpo_name": "-",
        "tpo_email": "-",
        "tpo_phone": "-",
        "tpo_conf_score": 0,
        "placement_page": "-",
        "website": website_candidates[0] if website_candidates else "-"
    }

def safe_fetch(url):
    if not url or url == "-":
        return None
    try:
        html = requests.get(url, headers=HEADERS, timeout=10, verify=False).text
        time.sleep(REQUEST_SLEEP)
        return html
    except Exception:
        return None

def auto_enrich_dataframe(df, max_workers=6, strict=True):
    """
    Input: DataFrame with at least 'college_name' column and optionally 'website' or 'source_url'.
    Output: new DataFrame with appended TPO columns.
    Strict mode returns '-' when score<4.
    """
    rows = df.to_dict(orient="records")
    results = []

    def worker(row):
        try:
            res = choose_tpo_for_college(row, strict=strict)
            out = dict(row)  # copy original columns
            out.update({
                "TPO_NAME": res["tpo_name"],
                "TPO_EMAIL": res["tpo_email"],
                "TPO_PHONE": res["tpo_phone"],
                "tpo_confidence_score": res["tpo_conf_score"],
                "tpo_placement_page": res["placement_page"],
                "tpo_website_used": res["website"]
            })
            return out
        except Exception:
            out = dict(row)
            out.update({
                "TPO_NAME": "-",
                "TPO_EMAIL": "-",
                "TPO_PHONE": "-",
                "tpo_confidence_score": 0,
                "tpo_placement_page": "-",
                "tpo_website_used": "-"
            })
            return out

    # concurrency
    with ThreadPoolExecutor(max_workers=max_workers) as exe:
        futures = [exe.submit(worker, r) for r in rows]
        for fut in as_completed(futures):
            results.append(fut.result())

    # preserve original order using college_name index mapping
    df_out = pd.DataFrame(results)
    # attempt to re-order to original by college_name if unique else return as-is
    return df_out
