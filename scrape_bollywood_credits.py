"""
Re-scrape Wikipedia "List of Bollywood films of YYYY" (2000-2010),
capturing the Wikipedia link for each top-grossing film, then visit
each film's page and extract Director and Starring from the infobox.

Output: bollywood_credits_2000_2010.csv with columns
    year, title, gross, director, cast, url

Run:
    pip install requests beautifulsoup4
    python scrape_bollywood_credits.py
"""

import csv
import re
import sys
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

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
BASE = "https://en.wikipedia.org"
OUT_CSV = "bollywood_credits_2000_2010.csv"


def normalise(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def find_gross_table(soup: BeautifulSoup):
    for table in soup.find_all("table", class_="wikitable"):
        headers = [normalise(th.get_text()).lower() for th in table.find_all("th")]
        if any("gross" in h for h in headers) and any("title" in h or "film" in h for h in headers):
            return table
    return None


def get_year_films(year: int):
    url = f"{BASE}/wiki/List_of_Bollywood_films_of_{year}"
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    table = find_gross_table(soup)
    if table is None:
        return []

    header_row = table.find("tr")
    headers = [normalise(th.get_text()).lower() for th in header_row.find_all(["th", "td"])]

    def col_idx(*needles, default=None):
        for i, h in enumerate(headers):
            if any(n in h for n in needles):
                return i
        return default

    title_idx = col_idx("title", "film", default=1)
    gross_idx = col_idx("gross", default=len(headers) - 1)

    films = []
    for tr in table.find_all("tr")[1:]:
        tds = tr.find_all(["td", "th"])
        if len(tds) <= max(title_idx, gross_idx):
            continue
        # strip sup
        for sup in tr.find_all("sup"):
            sup.decompose()

        title_cell = tds[title_idx]
        gross_cell = tds[gross_idx]
        title = normalise(title_cell.get_text(" "))
        gross = normalise(gross_cell.get_text(" "))
        link = title_cell.find("a", href=True)
        url = urljoin(BASE, link["href"]) if link else None
        if not title or not gross:
            continue
        films.append({"year": year, "title": title, "gross": gross, "url": url})
    return films


def parse_infobox_field(soup, label_patterns):
    """Find a row in the infobox whose label matches any pattern; return list of strings."""
    info = soup.find("table", class_=re.compile(r"infobox"))
    if info is None:
        return []
    for tr in info.find_all("tr"):
        th = tr.find("th")
        if not th:
            continue
        label = normalise(th.get_text()).lower()
        if any(p in label for p in label_patterns):
            td = tr.find("td")
            if td is None:
                return []
            for sup in td.find_all("sup"):
                sup.decompose()
            # Prefer list items if present
            items = td.find_all("li")
            if items:
                return [normalise(li.get_text(" ")) for li in items if normalise(li.get_text(" "))]
            # Otherwise split on <br>
            for br in td.find_all("br"):
                br.replace_with("\n")
            text = td.get_text("\n")
            parts = [normalise(p) for p in text.split("\n")]
            return [p for p in parts if p]
    return []


def get_credits(url: str):
    if not url:
        return "", ""
    resp = requests.get(url, headers=HEADERS, timeout=30)
    if resp.status_code != 200:
        return "", ""
    soup = BeautifulSoup(resp.text, "html.parser")
    directors = parse_infobox_field(soup, ["directed by", "director"])
    cast = parse_infobox_field(soup, ["starring", "cast"])
    return "; ".join(directors), "; ".join(cast)


def main():
    all_films = []
    for year in YEARS:
        print(f"Year index: {year}...", file=sys.stderr)
        try:
            films = get_year_films(year)
        except Exception as e:
            print(f"[{year}] index failed: {e}", file=sys.stderr)
            continue
        all_films.extend(films)
        time.sleep(1.0)

    print(f"Found {len(all_films)} films. Fetching credits...", file=sys.stderr)

    enriched = []
    for i, f in enumerate(all_films, 1):
        print(f"  [{i}/{len(all_films)}] {f['year']} {f['title']}", file=sys.stderr)
        try:
            director, cast = get_credits(f["url"])
        except Exception as e:
            print(f"    failed: {e}", file=sys.stderr)
            director, cast = "", ""
        enriched.append({**f, "director": director, "cast": cast})
        time.sleep(0.8)

    with open(OUT_CSV, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["year", "title", "gross", "director", "cast", "url"])
        writer.writeheader()
        writer.writerows(enriched)
    print(f"\nWrote {len(enriched)} rows to {OUT_CSV}", file=sys.stderr)

    # Brief preview
    for r in enriched:
        print(f"{r['year']}\t{r['title']}\t| dir: {r['director']}\t| cast: {r['cast']}")


if __name__ == "__main__":
    main()
