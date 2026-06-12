import csv
rows = list(csv.DictReader(open("actor_timeseries_wide_all.csv", encoding="utf-8")))
for r in rows[:20]:
    print(f"{r['num_films']:>5} {r['nepo']:<4} {r['actor'][:120]}")
