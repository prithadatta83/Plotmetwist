"""
Compute correlations:
  gross_cr  vs  imdb_rating
  gross_cr  vs  imdb_votes  (raw and log10)

Both Pearson (linear) and Spearman (rank). Overall and split by nepo flag.
Also fit OLS regressions: gross = f(rating), gross = f(log10(votes)).
"""

import csv
import math
import sys
import statistics as st

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

rows = list(csv.DictReader(open("actor_timeseries_long_all_with_ratings.csv", encoding="utf-8")))

# Dedup to film-level
seen = set()
films = []
for r in rows:
    key = (int(r["year"]), r["movie"])
    if key in seen:
        continue
    seen.add(key)
    if not r["gross_cr"] or not r["imdb_rating"] or not r["imdb_votes"]:
        continue
    try:
        films.append({
            "year": int(r["year"]),
            "movie": r["movie"],
            "gross_cr": float(r["gross_cr"]),
            "rating": float(r["imdb_rating"]),
            "votes": int(r["imdb_votes"]),
            "nepo": r["film_has_nepo_cast"],
        })
    except ValueError:
        continue

print(f"Films with all three (gross + rating + votes): {len(films)}", file=sys.stderr)

# Drop the known outlier Dhurandhar 1349.65 too?  We'll report both.
def stats(films, label):
    n = len(films)
    if n < 3:
        print(f"  {label}: n={n}, too few")
        return
    g  = [f["gross_cr"] for f in films]
    lg = [math.log10(f["gross_cr"] + 1) for f in films]
    r  = [f["rating"] for f in films]
    v  = [f["votes"] for f in films]
    lv = [math.log10(f["votes"] + 1) for f in films]

    def pearson(xs, ys):
        n = len(xs)
        mx = sum(xs)/n; my = sum(ys)/n
        num = sum((xs[i]-mx)*(ys[i]-my) for i in range(n))
        dx = math.sqrt(sum((xs[i]-mx)**2 for i in range(n)))
        dy = math.sqrt(sum((ys[i]-my)**2 for i in range(n)))
        return num/(dx*dy) if dx and dy else float("nan")

    def rank(xs):
        s = sorted(range(len(xs)), key=lambda i: xs[i])
        rk = [0]*len(xs)
        for r_, i in enumerate(s, 1):
            rk[i] = r_
        return rk

    def spearman(xs, ys):
        return pearson(rank(xs), rank(ys))

    def ols(xs, ys):
        n = len(xs); mx = sum(xs)/n; my = sum(ys)/n
        num = sum((xs[i]-mx)*(ys[i]-my) for i in range(n))
        den = sum((xs[i]-mx)**2 for i in range(n))
        b1 = num/den if den else 0
        b0 = my - b1*mx
        ss_tot = sum((y-my)**2 for y in ys)
        ss_res = sum((ys[i]-(b0+b1*xs[i]))**2 for i in range(n))
        r2 = 1 - ss_res/ss_tot if ss_tot else 0
        return b0, b1, r2

    print(f"\n=== {label}  (n={n}) ===")
    print(f"  Pearson:")
    print(f"    gross  vs rating         = {pearson(g, r):+.3f}")
    print(f"    gross  vs votes          = {pearson(g, v):+.3f}")
    print(f"    gross  vs log10(votes)   = {pearson(g, lv):+.3f}")
    print(f"    log(gross) vs rating     = {pearson(lg, r):+.3f}")
    print(f"    log(gross) vs log(votes) = {pearson(lg, lv):+.3f}")
    print(f"  Spearman (rank, robust):")
    print(f"    gross  vs rating         = {spearman(g, r):+.3f}")
    print(f"    gross  vs votes          = {spearman(g, v):+.3f}")
    print(f"  Best linear fits:")
    b0, b1, r2 = ols(r, lg)
    print(f"    log10(gross_cr) = {b1:+.3f}·rating + {b0:.3f}     R² = {r2:.3f}")
    b0, b1, r2 = ols(lv, lg)
    print(f"    log10(gross_cr) = {b1:+.3f}·log10(votes) + {b0:.3f}    R² = {r2:.3f}")

stats(films, "ALL films")
stats([f for f in films if f["gross_cr"] < 1000], "ALL films (excl. Dhurandhar/outliers >1000cr)")
stats([f for f in films if f["nepo"] == "yes"], "Nepo-cast films")
stats([f for f in films if f["nepo"] == "no"], "Non-nepo films")

# Save CSV
out = "gross_rating_votes_film_level.csv"
with open(out, "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow(["year","movie","nepo","gross_cr","rating","votes","log10_votes","log10_gross"])
    for f in films:
        w.writerow([f["year"], f["movie"], f["nepo"], f["gross_cr"], f["rating"],
                    f["votes"], round(math.log10(f["votes"]+1),3), round(math.log10(f["gross_cr"]+1),3)])
print(f"\nWrote film-level data: {out}", file=sys.stderr)

# Chart
try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 2, figsize=(13, 5))

    # Left: gross vs rating
    nepo = [f for f in films if f["nepo"] == "yes" and f["gross_cr"] < 1000]
    non = [f for f in films if f["nepo"] == "no" and f["gross_cr"] < 1000]
    axes[0].scatter([f["rating"] for f in non], [f["gross_cr"] for f in non],
                    alpha=0.4, s=12, color="#2980b9", label="Non-nepo")
    axes[0].scatter([f["rating"] for f in nepo], [f["gross_cr"] for f in nepo],
                    alpha=0.5, s=14, color="#c0392b", label="Nepo")
    axes[0].set_yscale("log")
    axes[0].set_xlabel("IMDb rating")
    axes[0].set_ylabel("Gross (₹ crore, log scale)")
    axes[0].set_title("Gross vs IMDb rating")
    axes[0].legend()
    axes[0].grid(alpha=0.3)

    # Right: gross vs log10(votes)
    axes[1].scatter([math.log10(f["votes"]+1) for f in non], [f["gross_cr"] for f in non],
                    alpha=0.4, s=12, color="#2980b9", label="Non-nepo")
    axes[1].scatter([math.log10(f["votes"]+1) for f in nepo], [f["gross_cr"] for f in nepo],
                    alpha=0.5, s=14, color="#c0392b", label="Nepo")
    axes[1].set_yscale("log")
    axes[1].set_xlabel("log10(IMDb votes)")
    axes[1].set_ylabel("Gross (₹ crore, log scale)")
    axes[1].set_title("Gross vs log10(IMDb votes)")
    axes[1].legend()
    axes[1].grid(alpha=0.3)

    plt.tight_layout()
    plt.savefig("chart_gross_vs_rating_votes.png", dpi=140)
    print("Saved chart_gross_vs_rating_votes.png", file=sys.stderr)
except ImportError:
    pass
