import csv
rows = [r for r in csv.DictReader(open("bollywood_all_2000_2025.csv", encoding="utf-8")) if r["year"] == "2018"]
print(f"2018 films: {len(rows)}")
empty_cast = sum(1 for r in rows if not r["cast"])
print(f"Empty cast: {empty_cast}")
print("\nFirst 10 films:")
for r in rows[:10]:
    print(f"  {r['title'][:30]:<30} | cast={r['cast'][:120]}")
