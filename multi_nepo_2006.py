import csv
from collections import Counter

rows = [r for r in csv.DictReader(open("bollywood_all_with_nepo.csv", encoding="utf-8"))
        if int(r["year"]) == 2006 and r["nepo_kid"] == "yes"]

dist = Counter()
multi = []
for r in rows:
    n = len([x for x in r["nepo_kids_in_cast"].split(";") if x.strip()])
    dist[n] += 1
    if n > 1:
        multi.append((r["title"], n))

total = len(rows)
multi_count = sum(c for n, c in dist.items() if n > 1)

print(f"2006 nepo films: {total}")
print(f"\nDistribution by # of nepo kids in cast:")
for n in sorted(dist):
    print(f"  {n} nepo kid(s): {dist[n]:>3}  ({dist[n]/total*100:.1f}%)")

print(f"\nFilms with >1 nepo kid: {multi_count} / {total} = {multi_count/total*100:.1f}%")

print(f"\nThe multi-nepo 2006 films:")
for title, n in sorted(multi, key=lambda x: -x[1]):
    print(f"  {n} kids: {title}")
