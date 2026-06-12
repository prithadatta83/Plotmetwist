"""Cumulative vote-count comparison: Rajkummar Rao vs Sonam Kapoor."""

import csv
import sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

def pull(actor_name):
    films = []
    for r in csv.DictReader(open("actor_timeseries_long_all_with_ratings.csv", encoding="utf-8")):
        if r["actor"].strip() != actor_name:
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

rajk = pull("Rajkummar Rao")
sonam = pull("Sonam Kapoor")

# Compute cumulative
def cum(films):
    cv = 0
    out = []
    for i, f in enumerate(films, 1):
        cv += f["votes"]
        out.append({"pos": i, "year": f["year"], "movie": f["movie"],
                    "votes": f["votes"], "cum": cv})
    return out

rajk_c = cum(rajk)
sonam_c = cum(sonam)

print(f"\nRajkummar Rao: {len(rajk)} films, total {rajk_c[-1]['cum']:,} votes")
print(f"Sonam Kapoor:  {len(sonam)} films, total {sonam_c[-1]['cum']:,} votes")

# Print full sequences
print(f"\n--- Rajkummar Rao filmography ---")
print(f"{'#':>3} {'year':>5} {'movie':<40} {'votes':>10} {'cum_votes':>12}")
for f in rajk_c:
    print(f"{f['pos']:>3} {f['year']:>5} {f['movie'][:40]:<40} {f['votes']:>10,} {f['cum']:>12,}")

print(f"\n--- Sonam Kapoor filmography ---")
print(f"{'#':>3} {'year':>5} {'movie':<40} {'votes':>10} {'cum_votes':>12}")
for f in sonam_c:
    print(f"{f['pos']:>3} {f['year']:>5} {f['movie'][:40]:<40} {f['votes']:>10,} {f['cum']:>12,}")

# Plot: two panels (by film number, by year)
fig, axes = plt.subplots(1, 2, figsize=(14, 5.5))

# Panel A: by film position
axes[0].plot([f["pos"] for f in rajk_c], [f["cum"] for f in rajk_c],
             "o-", color="#27ae60", label=f"Rajkummar Rao (non-nepo)",
             markersize=5, linewidth=2)
axes[0].plot([f["pos"] for f in sonam_c], [f["cum"] for f in sonam_c],
             "s-", color="#c0392b", label=f"Sonam Kapoor (nepo)",
             markersize=5, linewidth=2)
axes[0].set_xlabel("Film number in career")
axes[0].set_ylabel("Cumulative IMDb votes (log scale)")
axes[0].set_title("Cumulative votes by film number")
axes[0].set_yscale("log")
axes[0].legend(loc="lower right")
axes[0].grid(alpha=0.3, which="both")

# Panel B: by year
axes[1].plot([f["year"] for f in rajk_c], [f["cum"] for f in rajk_c],
             "o-", color="#27ae60", label="Rajkummar Rao",
             markersize=5, linewidth=2)
axes[1].plot([f["year"] for f in sonam_c], [f["cum"] for f in sonam_c],
             "s-", color="#c0392b", label="Sonam Kapoor",
             markersize=5, linewidth=2)
axes[1].set_xlabel("Year")
axes[1].set_ylabel("Cumulative IMDb votes (log scale)")
axes[1].set_title("Cumulative votes over time")
axes[1].set_yscale("log")
axes[1].legend(loc="lower right")
axes[1].grid(alpha=0.3, which="both")

# Annotate biggest single-film jumps for each actor
for actor_data, color in [(rajk_c, "#1e8449"), (sonam_c, "#922b21")]:
    big = sorted(actor_data, key=lambda f: -f["votes"])[:2]
    for f in big:
        axes[0].annotate(f["movie"][:18], xy=(f["pos"], f["cum"]),
                         xytext=(5, 5), textcoords="offset points",
                         fontsize=8, color=color)

plt.suptitle("Cumulative IMDb-vote trajectory: outsider vs star-kid",
             fontsize=13, y=1.02)
plt.tight_layout()
plt.savefig("chart_rajkummar_vs_sonam.png", dpi=140, bbox_inches="tight")
print(f"\nSaved chart_rajkummar_vs_sonam.png", file=sys.stderr)
