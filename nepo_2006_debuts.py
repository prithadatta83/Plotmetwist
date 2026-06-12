"""For each 2006 nepo film, list the nepo kids and check if 2006 was their debut."""

import csv
from collections import defaultdict

rows = list(csv.DictReader(open("bollywood_all_with_nepo.csv", encoding="utf-8")))

# Build: actor -> earliest year seen in our data
first_year = {}
for r in rows:
    cast = [c.strip() for c in r["cast"].split(";") if c.strip()]
    yr = int(r["year"])
    for actor in cast:
        if actor not in first_year or yr < first_year[actor]:
            first_year[actor] = yr

# Find 2006 nepo films
films_2006 = [r for r in rows if int(r["year"]) == 2006 and r["nepo_kid"] == "yes"]
films_2006.sort(key=lambda r: r["title"])

print(f"2006 films with nepo kids: {len(films_2006)}\n")
for r in films_2006:
    nepos = [n.strip() for n in r["nepo_kids_in_cast"].split(";") if n.strip()]
    print(f"  {r['title']:<40}  director: {r['director']}")
    for n in nepos:
        fy = first_year.get(n, "?")
        is_debut = "DEBUT (in dataset)" if fy == 2006 else f"already active since {fy}"
        print(f"     - {n:<25} → {is_debut}")
    print()
