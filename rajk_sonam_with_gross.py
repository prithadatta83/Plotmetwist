"""Rajkummar Rao + Sonam Kapoor filmographies with gross."""

import csv

# Build (year, title) -> gross_cr lookup
gross = {}
for r in csv.DictReader(open("bollywood_all_with_nepo.csv", encoding="utf-8")):
    gross[(int(r["year"]), r["title"])] = r["gross_cr"]

def pull(actor):
    films = []
    for r in csv.DictReader(open("actor_timeseries_long_all_with_ratings.csv", encoding="utf-8")):
        if r["actor"].strip() != actor:
            continue
        if not r["imdb_votes"]:
            continue
        try:
            films.append({
                "year": int(r["year"]),
                "movie": r["movie"],
                "rating": float(r["imdb_rating"]) if r["imdb_rating"] else None,
                "votes": int(r["imdb_votes"]),
                "gross": gross.get((int(r["year"]), r["movie"]), ""),
            })
        except ValueError:
            continue
    films.sort(key=lambda f: (f["year"], f["movie"]))
    return films

def show(name, films):
    total_v = sum(f["votes"] for f in films)
    grossed = [f for f in films if f["gross"]]
    total_g = sum(float(f["gross"]) for f in grossed)
    print(f"\n=== {name} ({len(films)} rated films, {len(grossed)} with gross) ===")
    print(f"    total votes: {total_v:,}  |  total gross of known films: ₹{total_g:.0f} cr")
    print(f"{'#':>3} {'year':>5} {'movie':<40} {'rating':>7} {'votes':>9} {'gross_cr':>9}")
    for i, f in enumerate(films, 1):
        rt = f"{f['rating']:.1f}" if f["rating"] is not None else "-"
        g = f"₹{float(f['gross']):.2f}" if f["gross"] else "-"
        print(f"{i:>3} {f['year']:>5} {f['movie'][:40]:<40} {rt:>7} {f['votes']:>9,} {g:>9}")

show("Rajkummar Rao (non-nepo)", pull("Rajkummar Rao"))
show("Sonam Kapoor (nepo)", pull("Sonam Kapoor"))
