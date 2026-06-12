"""
Scrape Wikipedia "List of Bollywood films of YYYY" for 2000-2025.
For each year, pull every release table (per-month/quarter) AND the
top-grossing table, then merge gross by title.

Output: bollywood_all_2000_2025.csv with columns
    year, title, director, cast, gross_raw, gross_cr
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

YEARS = range(2000, 2026)
BASE = "https://en.wikipedia.org"
OUT_CSV = "bollywood_all_2000_2025.csv"


def normalise(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def parse_gross_crore(s: str):
    if not s:
        return None
    m = re.search(r"₹\s*([\d][\d.,]*)\s*crore", s)
    if m:
        try:
            return float(m.group(1).replace(",", ""))
        except ValueError:
            pass
    m = re.search(r"₹\s*([\d]+(?:,\d+)+)", s)
    if m:
        try:
            return float(m.group(1).replace(",", "")) / 1e7
        except ValueError:
            pass
    return None


def classify_headers(headers):
    has_title = any("title" in h or "film" in h for h in headers)
    has_cast = any("cast" in h or "starring" in h for h in headers)
    has_gross = any("gross" in h for h in headers)
    has_director = any("director" in h for h in headers)
    if has_gross and has_title:
        return "gross"
    if has_title and (has_cast or has_director):
        return "release"
    return None


def col_idx(headers, *needles):
    for i, h in enumerate(headers):
        if any(n in h for n in needles):
            return i
    return None


def extract_cast(td):
    """Return a list of actor names from a Cast cell."""
    if td is None:
        return []
    for sup in td.find_all("sup"):
        sup.decompose()
    # Convert <br> to newlines (works alongside <li> processing)
    for br in td.find_all("br"):
        br.replace_with("\n")

    parts = []
    items = td.find_all("li")
    if items:
        for li in items:
            parts.extend(li.get_text("\n").split("\n"))
    else:
        parts = td.get_text("\n").split("\n")

    # Further split any chunk containing commas (most Wikipedia tables
    # use comma-separated cast lists, sometimes mixed with <br>s)
    expanded = []
    for p in parts:
        for sub in re.split(r"[,;]", p):
            expanded.append(sub)

    # Strip bullets, whitespace, lingering commas
    cleaned = [re.sub(r"^[•·\-\*\s,]+|[\s,]+$", "", x) for x in expanded]
    return [n for n in cleaned if n and len(n) >= 2 and re.search(r"[A-Za-z]", n)]


def expand_rowspans(table):
    """Return a 2D grid of BS4 cell elements, expanding row/colspans.
    grid[r][c] = same <td>/<th> element if cell spans into (r, c)."""
    grid = []
    for r_idx, tr in enumerate(table.find_all("tr")):
        while len(grid) <= r_idx:
            grid.append([])
        row = grid[r_idx]
        col = 0
        for cell in tr.find_all(["td", "th"], recursive=False):
            while col < len(row) and row[col] is not None:
                col += 1
            try:
                cs = int(cell.get("colspan", 1))
            except (TypeError, ValueError):
                cs = 1
            try:
                rs = int(cell.get("rowspan", 1))
            except (TypeError, ValueError):
                rs = 1
            for dc in range(cs):
                for dr in range(rs):
                    tr_idx = r_idx + dr
                    tc_idx = col + dc
                    while len(grid) <= tr_idx:
                        grid.append([])
                    while len(grid[tr_idx]) <= tc_idx:
                        grid[tr_idx].append(None)
                    grid[tr_idx][tc_idx] = cell
            col += cs
    return grid


def parse_table(table, year, kind):
    grid = expand_rowspans(table)
    if not grid:
        return []
    header_cells = grid[0]
    headers = []
    for c in header_cells:
        if c is None:
            headers.append("")
        else:
            headers.append(normalise(c.get_text()).lower())

    title_i = col_idx(headers, "title", "film")
    director_i = col_idx(headers, "director")
    cast_i = col_idx(headers, "cast", "starring")
    gross_i = col_idx(headers, "gross")

    if title_i is None:
        return []

    def cell_text(c):
        if c is None:
            return ""
        for sup in c.find_all("sup"):
            sup.decompose()
        for br in c.find_all("br"):
            br.replace_with("\n")
        return normalise(c.get_text(" "))

    rows = []
    for row in grid[1:]:
        if title_i >= len(row):
            continue
        title = cell_text(row[title_i])
        if not title or len(title) < 2:
            continue
        director = cell_text(row[director_i]) if director_i is not None and director_i < len(row) else ""
        cast_list = extract_cast(row[cast_i]) if cast_i is not None and cast_i < len(row) else []
        cast = "; ".join(cast_list)
        gross_raw = cell_text(row[gross_i]) if (kind == "gross" and gross_i is not None and gross_i < len(row)) else ""

        rows.append({
            "year": year,
            "title": title,
            "director": director,
            "cast": cast,
            "gross_raw": gross_raw,
        })
    return rows


def scrape_year(year):
    url = f"{BASE}/wiki/List_of_Bollywood_films_of_{year}"
    resp = requests.get(url, headers=HEADERS, timeout=30)
    if resp.status_code != 200:
        # Try Hindi variant
        url2 = f"{BASE}/wiki/List_of_Hindi_films_of_{year}"
        resp = requests.get(url2, headers=HEADERS, timeout=30)
        if resp.status_code != 200:
            return [], []
    soup = BeautifulSoup(resp.text, "html.parser")

    release_rows = []
    gross_rows = []
    for table in soup.find_all("table", class_="wikitable"):
        header_row = table.find("tr")
        if header_row is None:
            continue
        headers = [normalise(th.get_text()).lower() for th in header_row.find_all(["th", "td"])]
        kind = classify_headers(headers)
        if kind == "gross":
            gross_rows.extend(parse_table(table, year, "gross"))
        elif kind == "release":
            release_rows.extend(parse_table(table, year, "release"))
    return release_rows, gross_rows


def main():
    all_releases = []
    gross_map = {}  # (year, title_lower) -> gross_raw

    for year in YEARS:
        print(f"Year {year}...", file=sys.stderr)
        try:
            releases, grosses = scrape_year(year)
        except Exception as e:
            print(f"  failed: {e}", file=sys.stderr)
            continue
        print(f"  {len(releases)} releases, {len(grosses)} with gross", file=sys.stderr)
        all_releases.extend(releases)
        for g in grosses:
            gross_map[(year, g["title"].lower())] = g["gross_raw"]
        time.sleep(1.0)

    # De-dup releases by (year, title)
    seen = set()
    unique = []
    for r in all_releases:
        key = (r["year"], r["title"].lower())
        if key in seen:
            continue
        seen.add(key)
        unique.append(r)

    # Merge gross
    for r in unique:
        key = (r["year"], r["title"].lower())
        if not r["gross_raw"] and key in gross_map:
            r["gross_raw"] = gross_map[key]
        cr = parse_gross_crore(r["gross_raw"])
        r["gross_cr"] = f"{cr:.2f}" if cr is not None else ""

    # Also include gross-only rows that weren't in any release table (shouldn't happen often)
    release_keys = {(r["year"], r["title"].lower()) for r in unique}
    for (year, title_lower), gross_raw in gross_map.items():
        if (year, title_lower) not in release_keys:
            cr = parse_gross_crore(gross_raw)
            unique.append({
                "year": year,
                "title": title_lower.title(),
                "director": "",
                "cast": "",
                "gross_raw": gross_raw,
                "gross_cr": f"{cr:.2f}" if cr is not None else "",
            })

    with open(OUT_CSV, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["year", "title", "director", "cast", "gross_raw", "gross_cr"])
        writer.writeheader()
        writer.writerows(unique)

    print(f"\nWrote {len(unique)} films to {OUT_CSV}", file=sys.stderr)
    from collections import Counter
    by_year = Counter(r["year"] for r in unique)
    with_gross = sum(1 for r in unique if r["gross_cr"])
    print(f"With gross: {with_gross}/{len(unique)}", file=sys.stderr)
    print("\nPer-year counts:", file=sys.stderr)
    for year in sorted(by_year):
        n = by_year[year]
        ng = sum(1 for r in unique if r["year"] == year and r["gross_cr"])
        print(f"  {year}: {n} films ({ng} with gross)", file=sys.stderr)


if __name__ == "__main__":
    main()
