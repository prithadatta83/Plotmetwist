"""
Pivot bollywood_with_nepo_2000_2010.csv to a per-actor time series.

Each row = one actor.
Columns: actor, nepo, num_films, year_1, movie_1, gross_cr_1, year_2, ...

Gross is normalised to crore INR (₹ crore).
"""

import csv
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

IN_CSV = "bollywood_with_nepo_2000_2010.csv"
OUT_CSV = "actor_timeseries_2000_2010.csv"

# Same curated nepo list as tag_nepo_kids.py
NEPO_KIDS = {
    "Abhishek Bachchan", "Karisma Kapoor", "Karishma Kapoor",
    "Kareena Kapoor", "Kareena Kapoor Khan", "Ranbir Kapoor",
    "Rishi Kapoor", "Tusshar Kapoor", "Shahid Kapoor", "Sonam Kapoor",
    "Hrithik Roshan", "Salman Khan", "Sohail Khan", "Arbaaz Khan",
    "Aamir Khan", "Faisal Khan", "Imran Khan",
    "Saif Ali Khan", "Soha Ali Khan",
    "Sunny Deol", "Bobby Deol", "Esha Deol",
    "Sanjay Dutt", "Twinkle Khanna", "Akshaye Khanna",
    "Uday Chopra", "Rani Mukerji", "Kajol",
    "Sonakshi Sinha", "Vivek Oberoi", "Rekha",
}


def parse_gross_crore(s: str):
    """Return gross in crore INR (float), or None."""
    if not s:
        return None
    # Pattern 1: "₹ 80.01 crore"
    m = re.search(r"₹\s*([\d][\d.,]*)\s*crore", s)
    if m:
        try:
            return float(m.group(1).replace(",", ""))
        except ValueError:
            pass
    # Pattern 2: "₹ 95,13,50,000" (Indian numbering, no 'crore' word)
    m = re.search(r"₹\s*([\d]+(?:,\d+)+)", s)
    if m:
        try:
            return float(m.group(1).replace(",", "")) / 1e7
        except ValueError:
            pass
    return None


def normalise(name: str) -> str:
    return re.sub(r"\s+", " ", name).strip()


def main():
    with open(IN_CSV, encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))

    # actor -> list of (year, title, gross_crore)
    appearances = {}
    for r in rows:
        year = int(r["year"])
        title = r["title"]
        gross_cr = parse_gross_crore(r["gross"])
        cast = [normalise(c) for c in r["cast"].split(";") if normalise(c)]
        # de-dup within a film (some rows had a flat string followed by split entries)
        seen = set()
        unique_cast = []
        for c in cast:
            if c not in seen:
                seen.add(c)
                unique_cast.append(c)
        for actor in unique_cast:
            appearances.setdefault(actor, []).append((year, title, gross_cr))

    for actor in appearances:
        appearances[actor].sort(key=lambda x: (x[0], x[1]))

    max_films = max(len(v) for v in appearances.values())

    fieldnames = ["actor", "nepo", "num_films", "total_gross_cr"]
    for i in range(1, max_films + 1):
        fieldnames += [f"year_{i}", f"movie_{i}", f"gross_cr_{i}"]

    sorted_actors = sorted(
        appearances.items(),
        key=lambda kv: (-len(kv[1]), kv[0]),
    )

    with open(OUT_CSV, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for actor, films in sorted_actors:
            total = sum(g for _, _, g in films if g is not None)
            row = {
                "actor": actor,
                "nepo": "yes" if actor in NEPO_KIDS else "no",
                "num_films": len(films),
                "total_gross_cr": f"{total:.2f}",
            }
            for i, (year, title, gross_cr) in enumerate(films, 1):
                row[f"year_{i}"] = year
                row[f"movie_{i}"] = title
                row[f"gross_cr_{i}"] = f"{gross_cr:.2f}" if gross_cr is not None else ""
            writer.writerow(row)

    print(f"Wrote {len(sorted_actors)} actors to {OUT_CSV}", file=sys.stderr)
    print(f"Max films by any actor: {max_films}", file=sys.stderr)

    # Print preview: top 25 actors by # films
    print(f"\n{'actor':<28} {'nepo':<5} {'#films':>6}  {'total cr':>10}  appearances")
    print("-" * 100)
    for actor, films in sorted_actors[:25]:
        total = sum(g for _, _, g in films if g is not None)
        nepo = "yes" if actor in NEPO_KIDS else "no"
        apps = ", ".join(f"{y}:{t}" for y, t, _ in films[:5])
        if len(films) > 5:
            apps += f", +{len(films)-5} more"
        print(f"{actor:<28} {nepo:<5} {len(films):>6}  {total:>10.2f}  {apps}")


if __name__ == "__main__":
    main()
