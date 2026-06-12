"""
Scrape Wikipedia "List of Bollywood films of YYYY" pages for 2000-2010
and collect the highest-grossing films table for each year.

Run:
    pip install requests beautifulsoup4
    python scrape_bollywood_2000_2010.py
"""

import csv
import re
import sys
import time
import requests
from bs4 import BeautifulSoup

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    )
}

YEARS = range(2000, 2011)
OUT_CSV = "bollywood_2000_2010.csv"


def normalise(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def find_gross_table(soup: BeautifulSoup):
    """Find the wikitable whose headers contain a 'gross' column."""
    for table in soup.find_all("table", class_="wikitable"):
        headers = [normalise(th.get_text()).lower() for th in table.find_all("th")]
        if any("gross" in h for h in headers) and any("title" in h or "film" in h for h in headers):
            return table
    return None


def parse_row_cells(tr):
    cells = []
    for td in tr.find_all(["td", "th"]):
        for sup in td.find_all("sup"):
            sup.decompose()
        cells.append(normalise(td.get_text(" ")))
    return cells


def scrape_year(year: int):
    url = f"https://en.wikipedia.org/wiki/List_of_Bollywood_films_of_{year}"
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    table = find_gross_table(soup)
    if table is None:
        print(f"[{year}] no gross table found", file=sys.stderr)
        return []

    header_cells = [normalise(th.get_text()).lower() for th in table.find("tr").find_all(["th", "td"])]

    def col_idx(*needles, default=None):
        for i, h in enumerate(header_cells):
            if any(n in h for n in needles):
                return i
        return default

    title_idx = col_idx("title", "film", default=1)
    gross_idx = col_idx("gross", default=len(header_cells) - 1)
    studio_idx = col_idx("production", "studio", "company")

    rows = []
    for tr in table.find_all("tr")[1:]:
        cells = parse_row_cells(tr)
        if len(cells) <= max(title_idx, gross_idx):
            continue
        title = cells[title_idx]
        gross = cells[gross_idx]
        studio = cells[studio_idx] if studio_idx is not None and studio_idx < len(cells) else ""
        if not title or not gross:
            continue
        rows.append({
            "year": year,
            "title": title,
            "studio": studio,
            "gross": gross,
        })
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
        time.sleep(1.0)

    for r in all_rows:
        print(f"{r['year']}\t{r['gross']}\t{r['title']}")

    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["year", "title", "studio", "gross"])
        writer.writeheader()
        writer.writerows(all_rows)
    print(f"\nWrote {len(all_rows)} rows to {OUT_CSV}", file=sys.stderr)


if __name__ == "__main__":
    main()
