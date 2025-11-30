# site_parsers.py -- extract college rows from specific authoritative pages (VTU AJAX endpoint)

from scraper_core import fetch_html, soupify
from utils import normalize_text, extract_phone

def parse_vtu_affiliated(url):
    """
    Parse VTU affiliated institutes using the REAL AJAX endpoint.
    This endpoint returns full HTML containing all affiliated colleges.
    """
    ajax_url = "https://vtu.ac.in/wp-admin/admin-ajax.php?action=get_affiliated_institutes"

    print(f"[VTU] Fetching data from AJAX endpoint: {ajax_url}")
    html = fetch_html(ajax_url)
    soup = soupify(html)
    rows = []

    for table in soup.find_all("table"):
        for tr in table.find_all("tr")[1:]:  # skip header
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


# DTE parser disabled for now (site blocks Colab & times out)
def parse_dte_karnataka(url):
    """
    DISABLED: DTE site blocks scripted requests from Colab.
    Returning empty list for now.
    """
    print("[DTE] Skipped (site blocks requests from cloud IPs)")
    return []
