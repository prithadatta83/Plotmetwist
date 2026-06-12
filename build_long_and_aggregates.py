"""
From bollywood_with_nepo_2000_2010.csv produce:
  1. actor_timeseries_long.csv   - one row per (actor, film)
  2. yearly_aggregates.csv       - per-year totals split by nepo / non-nepo
"""

import csv
import re
import sys
from collections import defaultdict

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

IN_CSV = "bollywood_with_nepo_2000_2010.csv"
LONG_CSV = "actor_timeseries_long.csv"
AGG_CSV = "yearly_aggregates.csv"

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
    if not s:
        return None
    m = re.search(r"₹\s*([\d][\d.,]*)\s*crore", s)
    if m:
        try:
            return float(m.group(1).replace(",", ""))
        except ValueError:
            pass
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
        films = list(csv.DictReader(fh))

    # --- 1. Long format ---
    long_rows = []
    for f in films:
        year = int(f["year"])
        title = f["title"]
        gross_cr = parse_gross_crore(f["gross"])
        film_nepo_flag = f["nepo_kid"]
        cast = [normalise(c) for c in f["cast"].split(";") if normalise(c)]
        seen = set()
        for actor in cast:
            if actor in seen:
                continue
            seen.add(actor)
            long_rows.append({
                "actor": actor,
                "actor_nepo": "yes" if actor in NEPO_KIDS else "no",
                "year": year,
                "movie": title,
                "gross_cr": f"{gross_cr:.2f}" if gross_cr is not None else "",
                "film_has_nepo_cast": film_nepo_flag,
                "director": f["director"],
            })

    long_rows.sort(key=lambda r: (r["actor"], r["year"], r["movie"]))

    with open(LONG_CSV, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=[
            "actor", "actor_nepo", "year", "movie", "gross_cr",
            "film_has_nepo_cast", "director",
        ])
        writer.writeheader()
        writer.writerows(long_rows)
    print(f"Wrote {len(long_rows)} actor-film rows to {LONG_CSV}", file=sys.stderr)

    # --- 2. Yearly aggregates ---
    # Per-film bucket: nepo if any nepo kid in cast (already flagged).
    by_year = defaultdict(lambda: {
        "nepo_films": 0, "nepo_gross": 0.0,
        "non_nepo_films": 0, "non_nepo_gross": 0.0,
    })
    for f in films:
        year = int(f["year"])
        gross_cr = parse_gross_crore(f["gross"]) or 0.0
        if f["nepo_kid"] == "yes":
            by_year[year]["nepo_films"] += 1
            by_year[year]["nepo_gross"] += gross_cr
        else:
            by_year[year]["non_nepo_films"] += 1
            by_year[year]["non_nepo_gross"] += gross_cr

    with open(AGG_CSV, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow([
            "year",
            "nepo_films", "nepo_total_gross_cr", "nepo_avg_gross_cr",
            "non_nepo_films", "non_nepo_total_gross_cr", "non_nepo_avg_gross_cr",
            "nepo_share_of_films_pct", "nepo_share_of_gross_pct",
        ])
        for year in sorted(by_year):
            b = by_year[year]
            total_films = b["nepo_films"] + b["non_nepo_films"]
            total_gross = b["nepo_gross"] + b["non_nepo_gross"]
            nepo_avg = b["nepo_gross"] / b["nepo_films"] if b["nepo_films"] else 0
            non_avg = b["non_nepo_gross"] / b["non_nepo_films"] if b["non_nepo_films"] else 0
            share_films = b["nepo_films"] / total_films * 100 if total_films else 0
            share_gross = b["nepo_gross"] / total_gross * 100 if total_gross else 0
            writer.writerow([
                year,
                b["nepo_films"], f"{b['nepo_gross']:.2f}", f"{nepo_avg:.2f}",
                b["non_nepo_films"], f"{b['non_nepo_gross']:.2f}", f"{non_avg:.2f}",
                f"{share_films:.1f}", f"{share_gross:.1f}",
            ])
    print(f"Wrote yearly aggregates to {AGG_CSV}", file=sys.stderr)

    # Print aggregates table
    print(f"\n{'year':<6}{'nepo#':>6}{'nepo_tot_cr':>13}{'nepo_avg':>10}"
          f"{'non#':>6}{'non_tot_cr':>13}{'non_avg':>10}{'%films_nepo':>13}{'%gross_nepo':>13}")
    print("-" * 100)
    grand = {"nf": 0, "ng": 0.0, "of": 0, "og": 0.0}
    for year in sorted(by_year):
        b = by_year[year]
        total_films = b["nepo_films"] + b["non_nepo_films"]
        total_gross = b["nepo_gross"] + b["non_nepo_gross"]
        nepo_avg = b["nepo_gross"] / b["nepo_films"] if b["nepo_films"] else 0
        non_avg = b["non_nepo_gross"] / b["non_nepo_films"] if b["non_nepo_films"] else 0
        share_films = b["nepo_films"] / total_films * 100 if total_films else 0
        share_gross = b["nepo_gross"] / total_gross * 100 if total_gross else 0
        grand["nf"] += b["nepo_films"]; grand["ng"] += b["nepo_gross"]
        grand["of"] += b["non_nepo_films"]; grand["og"] += b["non_nepo_gross"]
        print(f"{year:<6}{b['nepo_films']:>6}{b['nepo_gross']:>13.2f}{nepo_avg:>10.2f}"
              f"{b['non_nepo_films']:>6}{b['non_nepo_gross']:>13.2f}{non_avg:>10.2f}"
              f"{share_films:>12.1f}%{share_gross:>12.1f}%")
    tot_f = grand["nf"] + grand["of"]
    tot_g = grand["ng"] + grand["og"]
    print("-" * 100)
    print(f"{'ALL':<6}{grand['nf']:>6}{grand['ng']:>13.2f}"
          f"{(grand['ng']/grand['nf']):>10.2f}"
          f"{grand['of']:>6}{grand['og']:>13.2f}"
          f"{(grand['og']/grand['of']):>10.2f}"
          f"{(grand['nf']/tot_f*100):>12.1f}%{(grand['ng']/tot_g*100):>12.1f}%")


if __name__ == "__main__":
    main()
