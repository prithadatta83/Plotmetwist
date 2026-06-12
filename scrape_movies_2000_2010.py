"""
Scrape Box Office Mojo yearly charts for 2000-2010 and print
each movie's title, year, and domestic gross. Also writes a CSV.

Run:
    pip install requests beautifulsoup4 pandas
    python scrape_movies_2000_2010.py
"""

import time
import csv
import sys
import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    )
}

YEARS = range(2000, 2011)
OUT_CSV = "movies_2000_2010.csv"


def scrape_year(year: int):
    url = f"https://www.boxofficemojo.com/year/{year}/"
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    table = soup.find("table")
    if table is None:
        print(f"[{year}] no table found", file=sys.stderr)
        return []

    headers = [th.get_text(strip=True) for th in table.find_all("th")]
    try:
        title_idx = headers.index("Release")
    except ValueError:
        title_idx = 1
    try:
        gross_idx = headers.index("Gross")
    except ValueError:
        gross_idx = 2

    rows = []
    for tr in table.find_all("tr")[1:]:
        cells = [td.get_text(strip=True) for td in tr.find_all("td")]
        if len(cells) <= max(title_idx, gross_idx):
            continue
        title = cells[title_idx]
        gross = cells[gross_idx]
        rows.append({"year": year, "title": title, "gross": gross})
    return rows


def main():
    all_rows = []
    for year in YEARS:
        print(f"Fetching {year}...", file=sys.stderr)
        try:
            rows = scrape_year(year)
        except Exception as e:
            print(f"[{year}] failed: {e}", file=sys.stderr)
            continue
        all_rows.extend(rows)
        time.sleep(1.5)  # be polite

    for r in all_rows:
        print(f"{r['year']}\t{r['gross']}\t{r['title']}")

    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["year", "title", "gross"])
        writer.writeheader()
        writer.writerows(all_rows)
    print(f"\nWrote {len(all_rows)} rows to {OUT_CSV}", file=sys.stderr)


if __name__ == "__main__":
    main()
