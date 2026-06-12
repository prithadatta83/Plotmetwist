"""Which non-nepo actors achieved nepo-level cumulative votes?"""

import csv
import importlib.util
import statistics as st
from collections import defaultdict

# Load nepo set + canonicaliser (same as before)
spec = importlib.util.spec_from_file_location("tag_mod", "tag_and_analyze_all.py")
tag_mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(tag_mod)
NEPO = set(tag_mod.NEPO_KIDS)

SAME = {
    "Karishma Kapoor": "Karisma Kapoor",
    "Kareena Kapoor Khan": "Kareena Kapoor",
    "Mimoh Chakraborty": "Mahaakshay Chakraborty",
    "Meezaan Jafri": "Meezaan Jaffery",
    "Pratik Babbar": "Prateik Babbar",
    "Shahrukh Khan": "Shah Rukh Khan",
    "Ajay Devgan": "Ajay Devgn",
    "Aishwarya Rai Bachchan": "Aishwarya Rai",
}

def canon(n):
    n = (n or "").strip()
    return SAME.get(n, n)

NEPO_C = {canon(n) for n in NEPO}

# Sum votes per actor
actor_votes = defaultdict(int)
actor_films = defaultdict(int)
for r in csv.DictReader(open("actor_timeseries_long_all_with_ratings.csv", encoding="utf-8")):
    a = canon(r["actor"])
    if not a or len(a) < 3 or a.startswith(("&", "(")):
        continue
    if not r["imdb_votes"]:
        continue
    try:
        actor_votes[a] += int(r["imdb_votes"])
        actor_films[a] += 1
    except ValueError:
        continue

# Build table
table = sorted(actor_votes.items(), key=lambda kv: -kv[1])

# Get nepo totals
nepo_totals = [v for a, v in actor_votes.items() if a in NEPO_C and v > 0]
non_totals  = [v for a, v in actor_votes.items() if a not in NEPO_C and v > 0]

print(f"Actors with vote data:           {len(actor_votes)}")
print(f"  Nepo:                          {len(nepo_totals)}")
print(f"  Non-nepo:                      {len(non_totals)}")

print(f"\n=== Career-total votes — group stats ===")
print(f"Nepo:      median={st.median(nepo_totals):>10,.0f}  mean={st.mean(nepo_totals):>10,.0f}  max={max(nepo_totals):>10,.0f}")
print(f"Non-nepo:  median={st.median(non_totals):>10,.0f}  mean={st.mean(non_totals):>10,.0f}  max={max(non_totals):>10,.0f}")

# Thresholds — Nepo median, top-quartile, top-10%
nepo_sorted = sorted(nepo_totals)
thr_median = st.median(nepo_totals)
thr_p75 = nepo_sorted[int(len(nepo_sorted) * 0.75)]
thr_p90 = nepo_sorted[int(len(nepo_sorted) * 0.90)]

print(f"\n=== Nepo benchmarks ===")
print(f"  Nepo median votes:   {thr_median:>12,.0f}")
print(f"  Nepo 75th pct votes: {thr_p75:>12,.0f}")
print(f"  Nepo 90th pct votes: {thr_p90:>12,.0f}")

non_above_median = [(a, v) for a, v in actor_votes.items() if a not in NEPO_C and v >= thr_median]
non_above_p75 = [(a, v) for a, v in actor_votes.items() if a not in NEPO_C and v >= thr_p75]
non_above_p90 = [(a, v) for a, v in actor_votes.items() if a not in NEPO_C and v >= thr_p90]

print(f"\n=== Non-nepo actors above each nepo threshold ===")
print(f"  Above nepo median:     {len(non_above_median)} actors")
print(f"  Above nepo 75th pct:   {len(non_above_p75)} actors")
print(f"  Above nepo top-10:     {len(non_above_p90)} actors")

print(f"\n=== Top 20 actors by total career votes (mixed) ===")
print(f"{'rank':>4} {'actor':<28}{'nepo':>5}{'films':>7}{'total_votes':>14}")
print("-" * 70)
for i, (a, v) in enumerate(table[:20], 1):
    print(f"{i:>4} {a:<28}{'yes' if a in NEPO_C else 'no':>5}{actor_films[a]:>7}{v:>14,}")

print(f"\n=== Top 25 NON-NEPO actors by total career votes (the 'breakthroughs') ===")
print(f"{'rank':>4} {'actor':<28}{'films':>7}{'total_votes':>14}")
print("-" * 60)
non_only = [(a, v) for a, v in table if a not in NEPO_C]
for i, (a, v) in enumerate(non_only[:25], 1):
    mark = " ← above nepo top-10" if v >= thr_p90 else (" ← above nepo top-25" if v >= thr_p75 else "")
    print(f"{i:>4} {a:<28}{actor_films[a]:>7}{v:>14,}{mark}")
