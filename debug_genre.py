import csv
rows = list(csv.DictReader(open("bollywood_all_2000_2025.csv", encoding="utf-8")))
genres = {"Drama", "Comedy", "Romance", "Thriller", "Action", "Horror", "Crime"}
hits = [r for r in rows if any(p.strip() in genres for p in r["cast"].split(";"))]
print(f"Films with genre-as-cast: {len(hits)}")
from collections import Counter
years = Counter(r["year"] for r in hits)
for y in sorted(years):
    print(f"  {y}: {years[y]}")
print("\nSample bad rows:")
for r in hits[:5]:
    print(f"  {r['year']} | {r['title']} | dir={r['director'][:30]} | cast={r['cast'][:100]}")
