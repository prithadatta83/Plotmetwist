"""Print Tabu and Kareena Kapoor filmographies side by side."""

import csv

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
                "votes": int(r["imdb_votes"]),
                "rating": float(r["imdb_rating"]) if r["imdb_rating"] else None,
            })
        except ValueError:
            continue
    films.sort(key=lambda f: (f["year"], f["movie"]))
    return films

tabu = pull("Tabu")
kareena = pull("Kareena Kapoor")

def show(name, films):
    cum = 0
    total = sum(f["votes"] for f in films)
    print(f"\n=== {name}  ({len(films)} rated films, total {total:,} votes) ===")
    print(f"{'#':>3} {'year':>5} {'movie':<40} {'rating':>6} {'votes':>9} {'cum_votes':>11}")
    for i, f in enumerate(films, 1):
        cum += f["votes"]
        rt = f"{f['rating']:.1f}" if f["rating"] is not None else "-"
        print(f"{i:>3} {f['year']:>5} {f['movie'][:40]:<40} {rt:>6} {f['votes']:>9,} {cum:>11,}")

show("Tabu (non-nepo)", tabu)
show("Kareena Kapoor (nepo)", kareena)
