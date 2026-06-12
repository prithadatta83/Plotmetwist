import csv

rows = list(csv.DictReader(open("bollywood_all_with_nepo.csv", encoding="utf-8")))

by_year = {}
for r in rows:
    y = int(r["year"])
    if y not in by_year:
        by_year[y] = {"total": 0, "nepo": 0}
    by_year[y]["total"] += 1
    if r["nepo_kid"] == "yes":
        by_year[y]["nepo"] += 1

print(f"{'year':<6}{'total':>7}{'nepo':>6}{'pct':>8}   bar")
print("-" * 60)
g_total = g_nepo = 0
for y in sorted(by_year):
    t = by_year[y]["total"]
    n = by_year[y]["nepo"]
    pct = n / t * 100
    g_total += t
    g_nepo += n
    bar = "#" * round(pct / 2)
    print(f"{y:<6}{t:>7}{n:>6}{pct:>7.1f}%   {bar}")
print("-" * 60)
print(f"{'ALL':<6}{g_total:>7}{g_nepo:>6}{g_nepo/g_total*100:>7.1f}%")
