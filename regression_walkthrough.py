"""Worked example: show the regression for Aamir Khan step by step."""

import csv
import math

ACTOR = "Aamir Khan"
rows = list(csv.DictReader(open("actor_timeseries_long_all_with_ratings.csv", encoding="utf-8")))

films = []
for r in rows:
    if r["actor"].strip() != ACTOR:
        continue
    if not r["imdb_rating"] or not r["imdb_votes"]:
        continue
    films.append({
        "year": int(r["year"]),
        "movie": r["movie"],
        "rating": float(r["imdb_rating"]),
        "votes": int(r["imdb_votes"]),
    })
films.sort(key=lambda f: (f["year"], f["movie"]))

print(f"=== STEP 1: pull all rated films for '{ACTOR}', sort by year ===\n")
print(f"{'i':>3} {'year':>5} {'movie':<35} {'rating':>7} {'votes':>9} {'log10(v)':>9}")
print("-" * 75)
xs = []
ys_rating = []
ys_logvotes = []
for i, f in enumerate(films, 1):
    log_v = math.log10(f["votes"] + 1)
    xs.append(i)
    ys_rating.append(f["rating"])
    ys_logvotes.append(log_v)
    print(f"{i:>3} {f['year']:>5} {f['movie'][:35]:<35} {f['rating']:>7.1f} {f['votes']:>9,} {log_v:>9.3f}")

n = len(xs)
print(f"\nn = {n} films")

print("\n=== STEP 2: regression formula ===")
print("  y = slope * x + intercept")
print("  slope = Σ((xᵢ - x̄) * (yᵢ - ȳ)) / Σ((xᵢ - x̄)²)")
print("  x = film position (1, 2, ..., n)")
print("  y = rating  OR  log10(votes)")

def regress(xs, ys, label):
    n = len(xs)
    mx = sum(xs) / n
    my = sum(ys) / n
    num = sum((xs[i] - mx) * (ys[i] - my) for i in range(n))
    den = sum((xs[i] - mx) ** 2 for i in range(n))
    slope = num / den
    intercept = my - slope * mx
    print(f"\n--- {label} ---")
    print(f"  x̄ (mean position)            = {mx:.3f}")
    print(f"  ȳ (mean {label})              = {my:.3f}")
    print(f"  Σ((xᵢ-x̄)(yᵢ-ȳ))  = {num:.4f}")
    print(f"  Σ((xᵢ-x̄)²)         = {den:.4f}")
    print(f"  SLOPE = {num:.4f} / {den:.4f} = {slope:+.4f}")
    print(f"  intercept = ȳ - slope·x̄ = {intercept:.4f}")
    print(f"  → fitted line:  y = {slope:+.4f}·x + {intercept:.4f}")
    print(f"  Interpretation: each next film changes {label} by {slope:+.4f}")
    if "votes" in label:
        mult = 10 ** slope
        print(f"      In linear vote terms: each next film = ×{mult:.3f}")
    return slope, intercept

print("\n=== STEP 3: run regression for RATING ===")
regress(xs, ys_rating, "rating")

print("\n=== STEP 4: run regression for log10(VOTES) ===")
regress(xs, ys_logvotes, "log10(votes)")

print("\n=== STEP 5: repeat for every actor with >= 5 films, then aggregate ===")
print("  - 533 actors qualify (53 nepo, 480 non-nepo)")
print("  - Take the mean slope within each group")
print("  - Compare nepo vs non-nepo")
