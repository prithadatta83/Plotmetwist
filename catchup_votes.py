"""
Cumulative-votes catchup analysis.

For each actor, sort films by year, compute the cumulative IMDb-vote total
at each film position. Average across nepo / non-nepo groups (median is more
robust because vote counts are heavy-tailed; we report both).

Then map: at nepo film position K, the avg cumulative votes = V.
What film position N does the avg non-nepo actor need to reach V?
"""

import csv
import math
import sys
import statistics as st
from collections import defaultdict

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

MIN_FILMS = 5
rows = list(csv.DictReader(open("actor_timeseries_long_all_with_ratings.csv", encoding="utf-8")))

actor_films = defaultdict(list)
for r in rows:
    a = r["actor"].strip()
    if not a or len(a) < 3 or a.startswith(("&", "(")):
        continue
    if not r["imdb_votes"]:
        continue
    try:
        actor_films[a].append({
            "year": int(r["year"]),
            "movie": r["movie"],
            "votes": int(r["imdb_votes"]),
            "nepo": r["actor_nepo"],
        })
    except ValueError:
        continue

# Sort each actor's films
for a in actor_films:
    actor_films[a].sort(key=lambda f: (f["year"], f["movie"]))

# Build cumulative trajectories, indexed by film position
def cum_traj(group, max_pos):
    """Return per-position list of cumulative vote totals across actors in group."""
    cum = []
    for pos in range(1, max_pos + 1):
        vals = []
        for a, fs in actor_films.items():
            if len(fs) < MIN_FILMS:
                continue
            if fs[0]["nepo"] != group:
                continue
            if len(fs) < pos:
                continue
            cum_v = sum(f["votes"] for f in fs[:pos])
            vals.append(cum_v)
        if len(vals) >= 5:
            cum.append((pos, st.mean(vals), st.median(vals), len(vals)))
    return cum

max_pos_overall = max(len(fs) for fs in actor_films.values())
nepo_traj = cum_traj("yes", max_pos_overall)
non_traj  = cum_traj("no",  max_pos_overall)

# Build position -> avg cum lookups
nepo_mean = {p: m for p, m, _, _ in nepo_traj}
nepo_med  = {p: med for p, _, med, _ in nepo_traj}
non_mean  = {p: m for p, m, _, _ in non_traj}
non_med   = {p: med for p, _, med, _ in non_traj}

def catchup(target_v, non_dict):
    """Smallest N such that non[N] >= target_v."""
    for n in sorted(non_dict):
        if non_dict[n] >= target_v:
            return n
    return None  # never catches up

print(f"=== Cumulative votes by film position (n actors with >= {MIN_FILMS} films) ===")
print(f"{'pos':>5}{'nepo_mean':>14}{'non_mean':>14}{'nepo_med':>14}{'non_med':>14}")
print("-" * 65)
positions = sorted(set(nepo_mean) | set(non_mean))
for p in positions:
    nm = nepo_mean.get(p, "")
    nom = non_mean.get(p, "")
    nme = nepo_med.get(p, "")
    nome = non_med.get(p, "")
    fmt = lambda x: f"{x:>14,.0f}" if isinstance(x, (int, float)) else f"{'':>14}"
    print(f"{p:>5}{fmt(nm)}{fmt(nom)}{fmt(nme)}{fmt(nome)}")

print("\n=== Catchup table (means) ===")
print(f"{'nepo_pos':>10}{'nepo_cumV':>14}{'non_pos_needed':>16}")
print("-" * 45)
for K in (1, 3, 5, 10, 15, 20, 25, 30):
    if K not in nepo_mean:
        continue
    target = nepo_mean[K]
    N = catchup(target, non_mean)
    label = f"{N}" if N else f">{max(non_mean)}"
    print(f"{K:>10}{target:>14,.0f}{label:>16}")

print("\n=== Catchup table (medians, more robust) ===")
print(f"{'nepo_pos':>10}{'nepo_cumV':>14}{'non_pos_needed':>16}")
print("-" * 45)
for K in (1, 3, 5, 10, 15, 20, 25, 30):
    if K not in nepo_med:
        continue
    target = nepo_med[K]
    N = catchup(target, non_med)
    label = f"{N}" if N else f">{max(non_med)}"
    print(f"{K:>10}{target:>14,.0f}{label:>16}")

# Chart
try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(11, 5))
    ax.plot([p for p, _, _, _ in nepo_traj], [m for _, m, _, _ in nepo_traj],
            "o-", color="#c0392b", label="Nepo (mean cumulative)")
    ax.plot([p for p, _, _, _ in non_traj], [m for _, m, _, _ in non_traj],
            "s-", color="#2980b9", label="Non-nepo (mean cumulative)")
    ax.set_yscale("log")
    ax.set_xlabel("Film number in career")
    ax.set_ylabel("Mean cumulative IMDb votes (log scale)")
    ax.set_title("Cumulative attention over career: nepo vs non-nepo")
    ax.legend()
    ax.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig("chart_cumulative_votes.png", dpi=140)
    print("\nSaved chart_cumulative_votes.png", file=sys.stderr)
except ImportError:
    pass
