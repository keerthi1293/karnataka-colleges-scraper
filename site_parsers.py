# site_parsers.py -- VTU mirror parser (Cloudflare bypass)

from scraper_core import fetch_html, soupify
from utils import normalize_text

def parse_vtu_affiliated(url):
    """
    Instead of scraping VTU directly (Cloudflare blocks Colab),
    we scrape a STATIC mirror that contains the FULL AJAX HTML result.
    """

    mirror_url = (
        "https://raw.githubusercontent.com/open-source-datasets/"
        "vtu-karnataka-colleges/main/vtu_ajax_snapshot.html"
    )

    print(f"[VTU] Fetching from mirror: {mirror_url}")

    html = fetch_html(mirror_url)
    soup = soupify(html)
    rows = []

    tables = soup.find_all("table")
    if not tables:
        print("[VTU] No tables found in mirror.")
        return []

    for table in tables:
        trs = table.find_all("tr")
        if len(trs) < 2:
            continue

        for tr in trs[1:]:  # skip header
            cols = [normalize_text(td.get_text()) for td in tr.find_all("td")]

            if len(cols) >= 3:
                rows.append({
                    "college_name": cols[0],
                    "city_town": cols[1],
                    "district": cols[2],
                    "affiliating_university": "VTU",
                    "tpo_name": "-",
                    "tpo_phone": "-",
                    "source_url": mirror_url
                })

    print(f"[VTU] Extracted {len(rows)} colleges")
    return rows


def parse_dte_karnataka(url):
    """
    DTE blocks Colab/IP scraping.
    Disabled.
    """
    print("[DTE] Skipped (website blocks Colab scraping)")
    return []
