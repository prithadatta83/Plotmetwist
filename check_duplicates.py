import csv
from collections import Counter

# Per-film file
rows = list(csv.DictReader(open("bollywood_all_with_nepo.csv", encoding="utf-8")))
total = len(rows)

# 1. Exact (year, title) duplicates
key_counts = Counter((int(r["year"]), r["title"]) for r in rows)
exact_dupes = {k: c for k, c in key_counts.items() if c > 1}
print(f"Total film rows:                          {total}")
print(f"Unique (year, title) combos:              {len(key_counts)}")
print(f"Exact (year, title) duplicate combos:     {len(exact_dupes)}")
print(f"Extra rows from those duplicates:         {sum(c-1 for c in exact_dupes.values())}")

# 2. Same title across multiple years (sequels OR same-name remakes)
title_to_years = {}
for r in rows:
    title_to_years.setdefault(r["title"], set()).add(int(r["year"]))
multi_year = {t: yrs for t, yrs in title_to_years.items() if len(yrs) > 1}
print(f"\nTitles appearing in >1 year:              {len(multi_year)}")
print("  Examples (likely sequels/remakes, not bugs):")
for t, yrs in sorted(multi_year.items())[:10]:
    print(f"    {t}  ->  {sorted(yrs)}")

# 3. Show the exact (year, title) dupes that exist
if exact_dupes:
    print(f"\nExact (year, title) duplicates:")
    for (y, t), c in sorted(exact_dupes.items()):
        print(f"  {y}  {t}  x{c}")
