"""Mean / median films per actor, nepo vs non-nepo, at several thresholds."""

import csv
import statistics as st
import importlib.util
from collections import Counter

# Load the curated nepo list
spec = importlib.util.spec_from_file_location("tag_mod", "tag_and_analyze_all.py")
tag_mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(tag_mod)
NEPO = set(tag_mod.NEPO_KIDS)

# Merge known same-person variants to one canonical name
SAME = {
    "Karishma Kapoor": "Karisma Kapoor",
    "Kareena Kapoor Khan": "Kareena Kapoor",
    "Mimoh Chakraborty": "Mahaakshay Chakraborty",
    "Meezaan Jafri": "Meezaan Jaffery",
    "Pratik Babbar": "Prateik Babbar",
    "Shahrukh Khan": "Shah Rukh Khan",
    "Ajay Devgan": "Ajay Devgn",
    "Aishwarya Rai Bachchan": "Aishwarya Rai",
    "Karishma Kapoor": "Karisma Kapoor",
}

def canon(name):
    name = name.strip()
    return SAME.get(name, name)

NEPO_CANON = {canon(n) for n in NEPO}

# Count films per actor (using long CSV - one row per actor-film)
rows = list(csv.DictReader(open("actor_timeseries_long_all_with_ratings.csv", encoding="utf-8")))

actor_films = Counter()
for r in rows:
    actor = canon(r["actor"])
    if not actor or len(actor) < 3 or actor.startswith(("&", "(")):
        continue
    actor_films[actor] += 1

# Classify
nepo = {a: n for a, n in actor_films.items() if a in NEPO_CANON}
non_nepo = {a: n for a, n in actor_films.items() if a not in NEPO_CANON}

print(f"Unique actors total:                {len(actor_films):>5}")
print(f"  - nepo kids (in our list):        {len(nepo):>5}")
print(f"  - non-nepo:                       {len(non_nepo):>5}")
print(f"\nNepo kids in NEPO_KIDS who never appear in data: "
      f"{len(NEPO_CANON - set(nepo.keys()))}")

def summary(name, d, threshold=1):
    counts = [c for c in d.values() if c >= threshold]
    if not counts:
        print(f"  {name}: no actors")
        return
    print(f"  {name:<14} n={len(counts):<5} mean={st.mean(counts):>5.2f}  "
          f"median={int(st.median(counts)):>3}  max={max(counts):>3}")

for thr in (1, 3, 5, 10):
    print(f"\n=== Films per actor, threshold >= {thr} films ===")
    summary("nepo", nepo, thr)
    summary("non-nepo", non_nepo, thr)

# Distribution buckets
print(f"\n=== Distribution (all actors with >=1 film) ===")
def buckets(d):
    b = Counter()
    for c in d.values():
        if c == 1: b["1 film"] += 1
        elif c <= 3: b["2-3 films"] += 1
        elif c <= 5: b["4-5 films"] += 1
        elif c <= 10: b["6-10 films"] += 1
        elif c <= 25: b["11-25 films"] += 1
        else: b["26+ films"] += 1
    return b

nepo_b = buckets(nepo)
non_b = buckets(non_nepo)
labels = ["1 film", "2-3 films", "4-5 films", "6-10 films", "11-25 films", "26+ films"]
print(f"  {'bucket':<14}{'nepo':>8}{'nepo%':>8}{'non-nepo':>10}{'non%':>7}")
n_total = sum(nepo.values()) and len(nepo)
nn_total = len(non_nepo)
for lab in labels:
    n_count = nepo_b.get(lab, 0)
    nn_count = non_b.get(lab, 0)
    print(f"  {lab:<14}{n_count:>8}{n_count/len(nepo)*100:>7.1f}%"
          f"{nn_count:>10}{nn_count/len(non_nepo)*100:>6.1f}%")
