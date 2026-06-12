import csv

rows = list(csv.DictReader(open("career_trajectory_summary.csv", encoding="utf-8")))
for r in rows:
    r["log_votes_slope"] = float(r["log_votes_slope"])
    r["rating_slope"] = float(r["rating_slope"])
    r["n_films"] = int(r["n_films"])

nepo = [r for r in rows if r["nepo"] == "yes"]
non  = [r for r in rows if r["nepo"] == "no"]

def show(label, group, key, top=10):
    s = sorted(group, key=lambda r: r[key])
    print(f"\n=== {label} — {key} ===")
    print(f"  BOTTOM {top} (steepest decline, left tail):")
    for r in s[:top]:
        mult = 10 ** r["log_votes_slope"]
        print(f"    {r['actor'][:28]:<28}  slope={r[key]:+.3f}  ×{mult:.2f}/film  n={r['n_films']}")
    print(f"  TOP {top} (steepest growth, right tail):")
    for r in s[-top:][::-1]:
        mult = 10 ** r["log_votes_slope"]
        print(f"    {r['actor'][:28]:<28}  slope={r[key]:+.3f}  ×{mult:.2f}/film  n={r['n_films']}")

show("NEPO actors (votes slope)", nepo, "log_votes_slope", top=10)
show("NON-NEPO actors (votes slope)", non, "log_votes_slope", top=10)
