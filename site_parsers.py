# site_parsers.py -- VTU AJAX parser (DTE disabled)

from scraper_core import fetch_html, soupify
from utils import normalize_text

def parse_vtu_affiliated(url):
    """
    Parse VTU affiliated colleges using the REAL AJAX endpoint.
    It returns HTML with all institute tables.
    """
    ajax_url = "https://vtu.ac.in/wp-admin/admin-ajax.php?action=get_affiliated_institutes"
    print(f"[VTU] Fetching from AJAX endpoint: {ajax_url}")

    html = fetch_html(ajax_url)
    soup = soupify(html)
    rows = []

    tables = soup.find_all("table")
    if not tables:
        print("[VTU] No tables found — Cloudflare probably still blocking.")
        return []

    for table in tables:
        trs = table.find_all("tr")
        if len(trs) < 2:
            continue

        for tr in trs[1:]:
            cols = [normalize_text(td.get_text()) for td in tr.find_all("td")]

            if len(cols) >= 3:
                rows.append({
                    "college_name": cols[0],
                    "city_town": cols[1],
                    "district": cols[2],
                    "affiliating_university": "VTU",
                    "tpo_name": "-",
                    "tpo_phone": "-",
                    "source_url": ajax_url
                })

    print(f"[VTU] Extracted {len(rows)} colleges")
    return rows


def parse_dte_karnataka(url):
    """
    DTE Karnataka blocks Colab traffic.
    Returning empty list for now.
    """
    print("[DTE] Skipped (DTE site blocks cloud requests)")
    return []
