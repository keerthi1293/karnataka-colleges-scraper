# tpo_enrichment.py
import requests
from bs4 import BeautifulSoup
import re, time
from urllib.parse import urljoin, urlparse
import pandas as pd
from tqdm import tqdm

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36"
}

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}")
PHONE_RE = re.compile(r"(?:\+91[- ]?)?\d{10}")

NAME_RE = re.compile(
    r"(Mr\.|Mrs\.|Ms\.|Dr\.|Prof\.|Sri\.|Smt\.)?\s?[A-Z][a-z]+(\s[A-Z][a-z]+){0,3}"
)

KEYWORDS = [
    "placement",
    "training",
    "tpo",
    "placement officer",
    "placement cell",
    "career",
    "recruitment",
]

def fetch(url):
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        if res.status_code == 200:
            return res.text
    except:
        return None
    return None

def discover_website(college_name):
    query = college_name.replace(" ", "+") + "+official+website"
    search_url = f"https://www.google.com/search?q={query}"
    html = fetch(search_url)
    if html:
        links = re.findall(r'href="(https?://[^"]+)"', html)
        for link in links:
            if "google" not in link and "youtube" not in link:
                return link.split("&")[0]
    return "-"

def find_placement_page(base_url, homepage_html):
    if homepage_html is None:
        return "-"

    soup = BeautifulSoup(homepage_html, "lxml")

    for a in soup.find_all("a", href=True):
        text = a.get_text().lower()
        href = a["href"]
        if any(k in text for k in KEYWORDS):
            return urljoin(base_url, href)

    return "-"

def extract_contacts(html):
    if html is None:
        return [], [], []

    emails = list(set(EMAIL_RE.findall(html)))
    phones = list(set(PHONE_RE.findall(html)))

    # extract possible names
    names = list(set(NAME_RE.findall(html)))
    names = [" ".join(n).strip() for n in names]

    return emails, phones, names

def enrich_dataset(df):
    data = []

    for idx, row in tqdm(df.iterrows(), total=len(df), desc="Extracting TPO Data"):
        name = row["college_name"]

        # Step 1: Discover website
        website = discover_website(name)
        if website == "-":
            data.append([name, "-", "-", "-", "-", "-", "-"])
            continue

        homepage_html = fetch(website)

        # Step 2: Identify placement/contact page
        placement_url = find_placement_page(website, homepage_html)
        placement_html = fetch(placement_url) if placement_url != "-" else homepage_html

        # Step 3: Extract emails, phones, names
        emails, phones, names_found = extract_contacts(placement_html)

        data.append([
            name,
            website,
            placement_url,
            "; ".join(emails) if emails else "-",
            "; ".join(phones) if phones else "-",
            "; ".join(names_found) if names_found else "-",
            row["district"]
        ])

        time.sleep(1)  # polite delay

    return pd.DataFrame(data, columns=[
        "college_name",
        "website",
        "placement_page",
        "emails_found",
        "phones_found",
        "names_extracted",
        "district"
    ])
