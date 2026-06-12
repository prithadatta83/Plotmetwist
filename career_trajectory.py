"""
Per-actor career trajectory analysis.

For each actor with >= 5 rated films:
  - Sort films by year (then alphabetically within year)
  - Compute the slope of rating vs film_number (linear regression)
  - Compute the slope of log10(votes) vs film_number
  - Build the indexed trajectory (mean metric at film position N)

Then aggregate by nepo vs non-nepo.

Outputs:
  - career_trajectory_summary.csv  (per-actor slopes)
  - chart_trajectory_rating.png
  - chart_trajectory_votes.png
  - chart_slope_distribution.png
"""

import csv
import sys
import math
import statistics as st
from collections import defaultdict

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

IN_CSV = "actor_timeseries_long_all_with_ratings.csv"
MIN_FILMS = 5

# Read
rows = list(csv.DictReader(open(IN_CSV, encoding="utf-8")))

# Build per-actor sorted list with rating + votes
actor_films = defaultdict(list)
for r in rows:
    actor = r["actor"].strip()
    if not actor or len(actor) < 3 or actor.startswith(("&", "(")):
        continue
    if not r["imdb_rating"] or not r["imdb_votes"]:
        continue
    try:
        rating = float(r["imdb_rating"])
        votes = int(r["imdb_votes"])
    except ValueError:
        continue
    actor_films[actor].append({
        "year": int(r["year"]),
        "movie": r["movie"],
        "rating": rating,
        "votes": votes,
        "nepo": r["actor_nepo"],
    })

for a in actor_films:
    actor_films[a].sort(key=lambda f: (f["year"], f["movie"]))

# Filter to actors with at least MIN_FILMS rated films
actors = {a: fs for a, fs in actor_films.items() if len(fs) >= MIN_FILMS}
print(f"Actors with >= {MIN_FILMS} rated films: {len(actors)}", file=sys.stderr)

# Linear regression helper
def slope(ys):
    n = len(ys)
    xs = list(range(1, n + 1))
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    num = sum((xs[i] - mean_x) * (ys[i] - mean_y) for i in range(n))
    den = sum((xs[i] - mean_x) ** 2 for i in range(n))
    return num / den if den else 0.0

# Per-actor slopes
records = []
for actor, fs in actors.items():
    nepo = fs[0]["nepo"]  # actor's nepo flag (same on every row)
    ratings = [f["rating"] for f in fs]
    log_votes = [math.log10(f["votes"] + 1) for f in fs]
    records.append({
        "actor": actor,
        "nepo": nepo,
        "n_films": len(fs),
        "rating_slope": slope(ratings),
        "log_votes_slope": slope(log_votes),
        "rating_first": ratings[0],
        "rating_last": ratings[-1],
        "votes_first": fs[0]["votes"],
        "votes_last": fs[-1]["votes"],
    })

# Write summary CSV
with open("career_trajectory_summary.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(records[0].keys()))
    w.writeheader()
    w.writerows(records)
print(f"Wrote career_trajectory_summary.csv ({len(records)} actors)", file=sys.stderr)

# Aggregate: mean slope by group
nepo_actors = [r for r in records if r["nepo"] == "yes"]
non_actors = [r for r in records if r["nepo"] == "no"]
print(f"\n=== Summary (n_films >= {MIN_FILMS}) ===")
print(f"Nepo actors:      {len(nepo_actors)}")
print(f"Non-nepo actors:  {len(non_actors)}")

print(f"\nMean rating slope (per-film delta):")
print(f"  nepo:      {st.mean(r['rating_slope'] for r in nepo_actors):+.4f}")
print(f"  non-nepo:  {st.mean(r['rating_slope'] for r in non_actors):+.4f}")
print(f"Median rating slope:")
print(f"  nepo:      {st.median(r['rating_slope'] for r in nepo_actors):+.4f}")
print(f"  non-nepo:  {st.median(r['rating_slope'] for r in non_actors):+.4f}")

print(f"\nMean log10(votes) slope (per-film delta):")
print(f"  nepo:      {st.mean(r['log_votes_slope'] for r in nepo_actors):+.4f}")
print(f"  non-nepo:  {st.mean(r['log_votes_slope'] for r in non_actors):+.4f}")
print(f"Median log10(votes) slope:")
print(f"  nepo:      {st.median(r['log_votes_slope'] for r in nepo_actors):+.4f}")
print(f"  non-nepo:  {st.median(r['log_votes_slope'] for r in non_actors):+.4f}")

# Indexed trajectory: mean rating / votes at film position N (across actors with >= N films)
max_pos = max(r["n_films"] for r in records)

def traj(group, metric_fn):
    out = []
    for pos in range(1, max_pos + 1):
        vals = [metric_fn(actors[a["actor"]][pos - 1]) for a in group
                if len(actors[a["actor"]]) >= pos]
        if len(vals) >= 5:  # require at least 5 actors to report
            out.append((pos, st.mean(vals), len(vals)))
    return out

rating_nepo = traj(nepo_actors, lambda f: f["rating"])
rating_non = traj(non_actors, lambda f: f["rating"])
votes_nepo = traj(nepo_actors, lambda f: math.log10(f["votes"] + 1))
votes_non = traj(non_actors, lambda f: math.log10(f["votes"] + 1))

# Plot
try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    # Chart 1: rating trajectory
    fig, ax = plt.subplots(figsize=(11, 5))
    ax.plot([p for p, _, _ in rating_nepo], [v for _, v, _ in rating_nepo],
            "o-", color="#c0392b", label=f"Nepo (n actors={len(nepo_actors)})")
    ax.plot([p for p, _, _ in rating_non], [v for _, v, _ in rating_non],
            "s-", color="#2980b9", label=f"Non-nepo (n actors={len(non_actors)})")
    ax.set_xlabel("Film number in career (1 = debut)")
    ax.set_ylabel("Mean IMDb rating")
    ax.set_title("Career trajectory: mean rating by film number")
    ax.legend()
    ax.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig("chart_trajectory_rating.png", dpi=140)
    print("Saved chart_trajectory_rating.png", file=sys.stderr)

    # Chart 2: votes trajectory (log scale)
    fig, ax = plt.subplots(figsize=(11, 5))
    ax.plot([p for p, _, _ in votes_nepo], [v for _, v, _ in votes_nepo],
            "o-", color="#c0392b", label=f"Nepo (n={len(nepo_actors)})")
    ax.plot([p for p, _, _ in votes_non], [v for _, v, _ in votes_non],
            "s-", color="#2980b9", label=f"Non-nepo (n={len(non_actors)})")
    ax.set_xlabel("Film number in career")
    ax.set_ylabel("Mean log10(IMDb votes)")
    ax.set_title("Career trajectory: mean log10(votes) by film number")
    ax.legend()
    ax.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig("chart_trajectory_votes.png", dpi=140)
    print("Saved chart_trajectory_votes.png", file=sys.stderr)

    # Chart 3: distribution of per-actor slopes
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    axes[0].hist([r["rating_slope"] for r in nepo_actors], bins=30, alpha=0.6,
                 color="#c0392b", label="Nepo")
    axes[0].hist([r["rating_slope"] for r in non_actors], bins=30, alpha=0.6,
                 color="#2980b9", label="Non-nepo")
    axes[0].axvline(0, color="#888", linestyle=":")
    axes[0].set_xlabel("Rating slope (Δ per film)")
    axes[0].set_ylabel("Number of actors")
    axes[0].set_title("Per-actor rating-slope distribution")
    axes[0].legend()

    axes[1].hist([r["log_votes_slope"] for r in nepo_actors], bins=30, alpha=0.6,
                 color="#c0392b", label="Nepo")
    axes[1].hist([r["log_votes_slope"] for r in non_actors], bins=30, alpha=0.6,
                 color="#2980b9", label="Non-nepo")
    axes[1].axvline(0, color="#888", linestyle=":")
    axes[1].set_xlabel("log10(votes) slope (Δ per film)")
    axes[1].set_ylabel("Number of actors")
    axes[1].set_title("Per-actor votes-slope distribution")
    axes[1].legend()
    plt.tight_layout()
    plt.savefig("chart_slope_distribution.png", dpi=140)
    print("Saved chart_slope_distribution.png", file=sys.stderr)
except ImportError:
    print("matplotlib not installed — skipping charts. pip install matplotlib", file=sys.stderr)

# Top/bottom by slope
print("\n=== Top 10 actors by rating slope (best career improvers) ===")
for r in sorted(records, key=lambda x: -x["rating_slope"])[:10]:
    print(f"  {r['actor'][:30]:<30} [{r['nepo']:<3}] slope={r['rating_slope']:+.3f}  films={r['n_films']}")
print("\n=== Bottom 10 by rating slope ===")
for r in sorted(records, key=lambda x: x["rating_slope"])[:10]:
    print(f"  {r['actor'][:30]:<30} [{r['nepo']:<3}] slope={r['rating_slope']:+.3f}  films={r['n_films']}")
