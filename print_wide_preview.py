import csv

with open("actor_timeseries_wide_all.csv", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

print(f"{'actor':<28}{'nepo':<5}{'films':>6}{'total_cr':>11}{'w/gross':>8}  first_film")
print("-" * 95)
for r in rows[:100]:
    first = ""
    if r.get("year_1"):
        first = f"{r['year_1']}:{r.get('movie_1','')[:30]} ({r.get('gross_cr_1','') or '-'})"
    print(f"{r['actor'][:27]:<28}{r['nepo']:<5}{r['num_films']:>6}"
          f"{r['total_gross_cr']:>11}{r['films_with_gross']:>8}  {first}")
