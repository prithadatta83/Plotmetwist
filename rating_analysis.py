import csv
import statistics as st

rows = list(csv.DictReader(open("actor_timeseries_long_all_with_ratings.csv", encoding="utf-8")))

# Dedup to film-level
seen = set()
films = []
for r in rows:
    key = (int(r["year"]), r["movie"])
    if key in seen:
        continue
    seen.add(key)
    films.append({
        "year": int(r["year"]),
        "movie": r["movie"],
        "nepo": r["film_has_nepo_cast"],
        "gross_cr": float(r["gross_cr"]) if r["gross_cr"] else None,
        "rating": float(r["imdb_rating"]) if r["imdb_rating"] else None,
        "votes": int(r["imdb_votes"]) if r["imdb_votes"] else None,
    })

n_total = len(films)
n_rating = sum(1 for f in films if f["rating"] is not None)
n_gross = sum(1 for f in films if f["gross_cr"] is not None)
print(f"Total unique films: {n_total}")
print(f"With IMDb rating:   {n_rating} ({n_rating/n_total*100:.1f}%)")
print(f"With gross:         {n_gross} ({n_gross/n_total*100:.1f}%)")

# Top 15 by rating
print("\n=== Top 15 films by IMDb rating (>=5000 votes) ===")
high_votes = [f for f in films if f["rating"] is not None and f["votes"] and f["votes"] >= 5000]
high_votes.sort(key=lambda f: -f["rating"])
for f in high_votes[:15]:
    print(f"  {f['year']} {f['movie'][:40]:<40} {f['rating']:>4} ({f['votes']:>7,} votes) [{f['nepo']}]")

# Top 15 by vote count (proxy for popularity / commercial reach)
print("\n=== Top 15 films by IMDb vote count ===")
by_votes = sorted([f for f in films if f["votes"]], key=lambda f: -f["votes"])
for f in by_votes[:15]:
    g = f"₹{f['gross_cr']:.0f}cr" if f['gross_cr'] else "-"
    print(f"  {f['year']} {f['movie'][:40]:<40} {f['rating']:>4} ({f['votes']:>7,} votes) gross={g:<10} [{f['nepo']}]")

# Nepo vs non-nepo: ratings and votes
print("\n=== Nepo vs non-nepo (films with IMDb data) ===")
nepo = [f for f in films if f["nepo"] == "yes" and f["rating"] is not None]
non = [f for f in films if f["nepo"] == "no" and f["rating"] is not None]
print(f"Films with rating:    nepo={len(nepo)},  non-nepo={len(non)}")
print(f"Avg rating:           nepo={st.mean(f['rating'] for f in nepo):.2f},  non-nepo={st.mean(f['rating'] for f in non):.2f}")
print(f"Median rating:        nepo={st.median(f['rating'] for f in nepo):.2f},  non-nepo={st.median(f['rating'] for f in non):.2f}")

nepo_v = [f for f in films if f["nepo"] == "yes" and f["votes"]]
non_v = [f for f in films if f["nepo"] == "no" and f["votes"]]
print(f"Avg votes:            nepo={st.mean(f['votes'] for f in nepo_v):,.0f},  non-nepo={st.mean(f['votes'] for f in non_v):,.0f}")
print(f"Median votes:         nepo={st.median(f['votes'] for f in nepo_v):,.0f},  non-nepo={st.median(f['votes'] for f in non_v):,.0f}")

# Per-year averages
print("\n=== Yearly: avg rating & avg votes, nepo vs non-nepo ===")
print(f"{'year':<6}{'rate_nepo':>10}{'rate_non':>10}{'votes_nepo':>13}{'votes_non':>13}")
print("-" * 60)
by_year = {}
for f in films:
    y = f["year"]
    by_year.setdefault(y, []).append(f)
for y in sorted(by_year):
    yr = by_year[y]
    nepo_r = [f["rating"] for f in yr if f["nepo"] == "yes" and f["rating"]]
    non_r = [f["rating"] for f in yr if f["nepo"] == "no" and f["rating"]]
    nepo_v_y = [f["votes"] for f in yr if f["nepo"] == "yes" and f["votes"]]
    non_v_y = [f["votes"] for f in yr if f["nepo"] == "no" and f["votes"]]
    nr = st.mean(nepo_r) if nepo_r else 0
    nor = st.mean(non_r) if non_r else 0
    nv = st.mean(nepo_v_y) if nepo_v_y else 0
    nov = st.mean(non_v_y) if non_v_y else 0
    print(f"{y:<6}{nr:>10.2f}{nor:>10.2f}{nv:>13,.0f}{nov:>13,.0f}")
