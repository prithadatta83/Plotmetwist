"""
Pull IMDb ratings for every unique film in actor_timeseries_long_all.csv
using IMDb's public TSV dumps (https://datasets.imdbws.com/).

Steps:
  1. Download title.basics.tsv.gz and title.ratings.tsv.gz (cache locally)
  2. Stream-filter basics to movies/tvMovies with startYear 2000-2025
  3. Join with ratings → (title_lower, year) -> (rating, votes)
  4. Match against unique films in our data; write enriched CSVs:
       - film_ratings.csv          (per unique film with rating)
       - actor_timeseries_long_all_with_ratings.csv
"""

import csv
import gzip
import os
import re
import sys
import time
import urllib.request

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

BASICS_URL = "https://datasets.imdbws.com/title.basics.tsv.gz"
RATINGS_URL = "https://datasets.imdbws.com/title.ratings.tsv.gz"
BASICS_GZ = "title.basics.tsv.gz"
RATINGS_GZ = "title.ratings.tsv.gz"
LONG_CSV = "actor_timeseries_long_all.csv"
FILM_OUT = "film_ratings.csv"
LONG_OUT = "actor_timeseries_long_all_with_ratings.csv"

# Allowed types and year range for the basics filter
ALLOWED_TYPES = {"movie", "tvMovie"}
YEARS = set(range(2000, 2026))


def download(url, path):
    if os.path.exists(path) and os.path.getsize(path) > 1_000_000:
        print(f"  Using cached {path} ({os.path.getsize(path)/1e6:.1f} MB)", file=sys.stderr)
        return
    print(f"  Downloading {url} -> {path}", file=sys.stderr)
    t0 = time.time()
    urllib.request.urlretrieve(url, path)
    print(f"    done in {time.time()-t0:.1f}s ({os.path.getsize(path)/1e6:.1f} MB)", file=sys.stderr)


def norm_title(s):
    """Lowercase, strip punctuation/spaces for fuzzy matching."""
    return re.sub(r"[^a-z0-9]+", "", (s or "").lower())


def main():
    print("Step 1: download IMDb dumps", file=sys.stderr)
    download(BASICS_URL, BASICS_GZ)
    download(RATINGS_URL, RATINGS_GZ)

    print("\nStep 2: stream basics, build tconst -> (titles, year)", file=sys.stderr)
    tconst_to_info = {}  # tconst -> (primary, original, year)
    with gzip.open(BASICS_GZ, "rt", encoding="utf-8", newline="") as f:
        reader = csv.reader(f, delimiter="\t")
        header = next(reader)
        # header: tconst, titleType, primaryTitle, originalTitle, isAdult, startYear, endYear, runtime, genres
        for i, row in enumerate(reader):
            if i % 1_000_000 == 0 and i:
                print(f"    scanned {i:,} rows, kept {len(tconst_to_info):,}", file=sys.stderr)
            if len(row) < 6:
                continue
            ttype = row[1]
            if ttype not in ALLOWED_TYPES:
                continue
            year_str = row[5]
            if not year_str.isdigit():
                continue
            year = int(year_str)
            if year not in YEARS:
                continue
            tconst_to_info[row[0]] = (row[2], row[3], year)
    print(f"  kept {len(tconst_to_info):,} candidate IMDb titles", file=sys.stderr)

    print("\nStep 3: load ratings", file=sys.stderr)
    # title.ratings.tsv: tconst, averageRating, numVotes
    ratings_lookup = {}  # (norm_title, year) -> (rating, votes, primaryTitle)
    with gzip.open(RATINGS_GZ, "rt", encoding="utf-8", newline="") as f:
        reader = csv.reader(f, delimiter="\t")
        next(reader)  # header
        for tconst, rating_str, votes_str in reader:
            info = tconst_to_info.get(tconst)
            if not info:
                continue
            primary, original, year = info
            try:
                rating = float(rating_str)
                votes = int(votes_str)
            except ValueError:
                continue
            for title_variant in {primary, original}:
                key = (norm_title(title_variant), year)
                if not key[0]:
                    continue
                # Prefer the higher-votes entry on collision (rare)
                existing = ratings_lookup.get(key)
                if existing is None or votes > existing[1]:
                    ratings_lookup[key] = (rating, votes, primary)
    print(f"  built lookup for {len(ratings_lookup):,} (title,year) keys", file=sys.stderr)

    print("\nStep 4: load our films & match", file=sys.stderr)
    with open(LONG_CSV, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    unique_films = {}  # (year, title) -> {meta}
    for r in rows:
        key = (int(r["year"]), r["movie"])
        unique_films.setdefault(key, r)
    print(f"  {len(unique_films):,} unique films, {len(rows):,} actor-film rows", file=sys.stderr)

    # Try exact (year, normalised-title) match, then (year-1) and (year+1) fallback
    matched = 0
    film_ratings = {}  # (year, title) -> (rating, votes, imdb_primary)
    for (year, title) in unique_films:
        nt = norm_title(title)
        result = ratings_lookup.get((nt, year))
        if result is None:
            for dy in (-1, 1, -2, 2):
                result = ratings_lookup.get((nt, year + dy))
                if result is not None:
                    break
        if result is not None:
            film_ratings[(year, title)] = result
            matched += 1
    print(f"  matched {matched:,}/{len(unique_films):,} films "
          f"({matched/len(unique_films)*100:.1f}%)", file=sys.stderr)

    print("\nStep 5: write outputs", file=sys.stderr)
    # film_ratings.csv
    with open(FILM_OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["year", "movie", "imdb_rating", "imdb_votes", "imdb_matched_title"])
        for (year, title) in sorted(unique_films):
            r = film_ratings.get((year, title))
            if r:
                w.writerow([year, title, r[0], r[1], r[2]])
            else:
                w.writerow([year, title, "", "", ""])
    print(f"  wrote {FILM_OUT}", file=sys.stderr)

    # long CSV with rating columns
    with open(LONG_OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(list(rows[0].keys()) + ["imdb_rating", "imdb_votes", "imdb_matched_title"])
        for r in rows:
            key = (int(r["year"]), r["movie"])
            match = film_ratings.get(key)
            extras = list(match) if match else ["", "", ""]
            w.writerow(list(r.values()) + [extras[0], extras[1], extras[2]])
    print(f"  wrote {LONG_OUT}", file=sys.stderr)

    print(f"\nDone. {matched:,}/{len(unique_films):,} unique films "
          f"({matched/len(unique_films)*100:.1f}%) got an IMDb rating.",
          file=sys.stderr)


if __name__ == "__main__":
    main()
