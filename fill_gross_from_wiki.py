"""
Fill in missing gross data by scraping each film's Wikipedia page.

Steps:
  1. Re-fetch year-index pages 2000-2025 to extract Wikipedia URL per film
  2. For each film in bollywood_all_with_nepo.csv without gross_cr,
     fetch the film's Wikipedia page and parse the infobox 'Box office' row
  3. Write progress to bollywood_filled_gross.csv every 100 films
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
        "Chrome/124.0 Safari/537.36 "
        "(nepotism-analysis research script; contact: pritha.datta@ondc.org)"
    )
}
BASE = "https://en.wikipedia.org"
IN_CSV = "bollywood_all_with_nepo.csv"
OUT_CSV = "bollywood_filled_gross.csv"
URL_MAP_CSV = "film_urls.csv"
DELAY = 0.4


def normalise(s):
    return re.sub(r"\s+", " ", s or "").strip()


def expand_rowspans(table):
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


def parse_gross_crore(s):
    """Convert a Box office text snippet to crore INR."""
    if not s:
        return None
    s_low = s.lower()
    # Drop parenthetical (USD equivalents)
    s_main = re.sub(r"\([^)]*\)", "", s_low)

    # ₹ X crore
    m = re.search(r"₹\s*([\d][\d.,]*)\s*crore", s_main)
    if m:
        try:
            return float(m.group(1).replace(",", ""))
        except ValueError:
            pass
    # ₹ X billion (1 billion = 100 crore)
    m = re.search(r"₹\s*([\d][\d.,]*)\s*billion", s_main)
    if m:
        try:
            return float(m.group(1).replace(",", "")) * 100
        except ValueError:
            pass
    # ₹ X million (1 crore = 10 million)
    m = re.search(r"₹\s*([\d][\d.,]*)\s*million", s_main)
    if m:
        try:
            return float(m.group(1).replace(",", "")) / 10
        except ValueError:
            pass
    # ₹ X lakh (1 crore = 100 lakh)
    m = re.search(r"₹\s*([\d][\d.,]*)\s*lakh", s_main)
    if m:
        try:
            return float(m.group(1).replace(",", "")) / 100
        except ValueError:
            pass
    # Indian numbering: ₹ NN,NN,NN,NNN
    m = re.search(r"₹\s*([\d]+(?:,\d+){2,})", s_main)
    if m:
        try:
            return float(m.group(1).replace(",", "")) / 1e7
        except ValueError:
            pass
    return None


def parse_box_office(soup):
    info = soup.find("table", class_=re.compile(r"infobox"))
    if info is None:
        return ""
    for tr in info.find_all("tr"):
        th = tr.find("th")
        if not th:
            continue
        label = normalise(th.get_text()).lower()
        if "box office" in label:
            td = tr.find("td")
            if td is None:
                return ""
            for sup in td.find_all("sup"):
                sup.decompose()
            for br in td.find_all("br"):
                br.replace_with(" / ")
            return normalise(td.get_text(" "))
    return ""


def build_url_map():
    """Re-fetch year-index pages and return {(year, title): url}."""
    url_map = {}
    for year in range(2000, 2026):
        print(f"Indexing {year}...", file=sys.stderr)
        try:
            resp = requests.get(
                f"{BASE}/wiki/List_of_Bollywood_films_of_{year}",
                headers=HEADERS, timeout=30,
            )
            if resp.status_code != 200:
                resp = requests.get(
                    f"{BASE}/wiki/List_of_Hindi_films_of_{year}",
                    headers=HEADERS, timeout=30,
                )
            if resp.status_code != 200:
                continue
        except Exception as e:
            print(f"  failed: {e}", file=sys.stderr)
            continue
        soup = BeautifulSoup(resp.text, "html.parser")
        for table in soup.find_all("table", class_="wikitable"):
            grid = expand_rowspans(table)
            if not grid:
                continue
            headers = []
            for c in grid[0]:
                headers.append(normalise(c.get_text()).lower() if c else "")
            has_title = any("title" in h or "film" in h for h in headers)
            has_credit = any("cast" in h or "starring" in h or "director" in h for h in headers)
            has_gross = any("gross" in h for h in headers)
            if not has_title:
                continue
            if not (has_credit or has_gross):
                continue
            title_i = next(
                (i for i, h in enumerate(headers) if "title" in h or "film" in h),
                None,
            )
            if title_i is None:
                continue
            for row in grid[1:]:
                if title_i >= len(row) or row[title_i] is None:
                    continue
                cell = row[title_i]
                link = cell.find("a", href=True)
                title = normalise(cell.get_text(" "))
                if not title or not link:
                    continue
                href = link["href"]
                if href.startswith("#") or "redlink=1" in href:
                    continue
                url_map[(year, title.lower())] = urljoin(BASE, href)
        time.sleep(DELAY)

    # Save URL map for inspection / resumption
    with open(URL_MAP_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["year", "title", "url"])
        for (year, title), url in sorted(url_map.items()):
            w.writerow([year, title, url])
    print(f"\nCollected {len(url_map)} URLs -> {URL_MAP_CSV}", file=sys.stderr)
    return url_map


def main():
    # Step 1: URL map
    url_map = build_url_map()

    # Step 2: load existing data
    with open(IN_CSV, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    field_order = list(rows[0].keys())

    # Resume support: if OUT_CSV exists, prefer those rows as the starting point
    try:
        with open(OUT_CSV, encoding="utf-8") as f:
            existing = list(csv.DictReader(f))
        if existing and len(existing) == len(rows):
            rows = existing
            print(f"Resuming from {OUT_CSV} ({len(rows)} rows).", file=sys.stderr)
    except FileNotFoundError:
        pass

    to_fetch = [r for r in rows if not r.get("gross_cr")]
    print(f"Films missing gross: {len(to_fetch)}/{len(rows)}", file=sys.stderr)

    # Map row -> URL
    fetched = 0
    found = 0
    not_found = 0
    no_url = 0

    def save():
        with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=field_order)
            w.writeheader()
            w.writerows(rows)

    for i, r in enumerate(to_fetch, 1):
        year = int(r["year"])
        title = r["title"]
        url = url_map.get((year, title.lower()))
        if not url:
            no_url += 1
            continue
        try:
            resp = requests.get(url, headers=HEADERS, timeout=30)
            fetched += 1
            if resp.status_code != 200:
                not_found += 1
                continue
            soup = BeautifulSoup(resp.text, "html.parser")
            bo = parse_box_office(soup)
            if bo:
                cr = parse_gross_crore(bo)
                r["gross_raw"] = bo
                if cr is not None:
                    r["gross_cr"] = f"{cr:.2f}"
                    found += 1
        except Exception as e:
            print(f"  [{title}] error: {e}", file=sys.stderr)

        if i % 50 == 0:
            print(f"  [{i}/{len(to_fetch)}] fetched={fetched} found_gross={found} "
                  f"no_url={no_url} not_found={not_found}",
                  file=sys.stderr)
        if i % 100 == 0:
            save()
        time.sleep(DELAY)

    save()
    print(f"\nDone.", file=sys.stderr)
    print(f"  Films processed: {len(to_fetch)}", file=sys.stderr)
    print(f"  Films with URL:  {len(to_fetch) - no_url}", file=sys.stderr)
    print(f"  Pages fetched:   {fetched}", file=sys.stderr)
    print(f"  Gross extracted: {found}", file=sys.stderr)


if __name__ == "__main__":
    main()
