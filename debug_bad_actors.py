import csv
rows = list(csv.DictReader(open("bollywood_all_2000_2025.csv", encoding="utf-8")))
# Show films where cast contains "Drama" or "Comedy" or single-word entries
bad_terms = {"Drama", "Comedy", "Romance", "Thriller", "Action", "T-Series Films", "ZEE5", ","}
count = 0
for r in rows:
    cast_parts = [p.strip() for p in r["cast"].split(";")]
    if any(p in bad_terms for p in cast_parts):
        count += 1
        if count <= 8:
            print(f"{r['year']} | {r['title'][:40]:<40} | cast: {r['cast'][:120]}")
print(f"\nTotal films with bad cast entries: {count}")
