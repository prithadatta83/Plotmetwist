"""
Read bollywood_all_2000_2025.csv, tag with expanded nepo-kid list,
and produce three outputs:
  - bollywood_all_with_nepo.csv         (per-film, with nepo_kid yes/no)
  - actor_timeseries_long_all.csv       (one row per actor-film)
  - actor_timeseries_wide_all.csv       (one row per actor, films as columns)
  - yearly_aggregates_all.csv           (per-year nepo vs non-nepo)
"""

import csv
import re
import sys
from collections import defaultdict

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import os
IN_CSV = "bollywood_filled_gross.csv" if os.path.exists("bollywood_filled_gross.csv") else "bollywood_all_2000_2025.csv"
TAGGED_CSV = "bollywood_all_with_nepo.csv"
LONG_CSV = "actor_timeseries_long_all.csv"
WIDE_CSV = "actor_timeseries_wide_all.csv"
AGG_CSV = "yearly_aggregates_all.csv"

# Expanded NEPO_KIDS list - first-generation children/close relatives of
# prominent film-industry figures. Edit to refine.
NEPO_KIDS = {
    # Bachchan family
    "Abhishek Bachchan", "Agastya Nanda",
    # Kapoor family (Raj Kapoor lineage + Surinder Kapoor + Jeetendra + Pankaj Kapur)
    "Karisma Kapoor", "Karishma Kapoor",
    "Kareena Kapoor", "Kareena Kapoor Khan",
    "Ranbir Kapoor", "Rishi Kapoor",
    "Tusshar Kapoor", "Shahid Kapoor",
    "Sonam Kapoor", "Arjun Kapoor", "Anshula Kapoor",
    "Janhvi Kapoor", "Khushi Kapoor", "Shanaya Kapoor",
    "Aadar Jain", "Armaan Jain",
    "Sanjay Kapoor",
    "Ishaan Khatter",
    # Roshan family
    "Hrithik Roshan", "Pashmina Roshan",
    # Salim Khan family (Salman)
    "Salman Khan", "Sohail Khan", "Arbaaz Khan",
    "Arhaan Khan", "Helena Khan",
    # Tahir Hussain / Aamir Khan family
    "Aamir Khan", "Faisal Khan", "Imran Khan", "Junaid Khan",
    "Ira Khan",
    # Pataudi-Tagore family (Saif)
    "Saif Ali Khan", "Soha Ali Khan",
    "Sara Ali Khan", "Ibrahim Ali Khan",
    # Khan / SRK family
    "Aryan Khan", "Suhana Khan",
    # Deol / Dharmendra family
    "Sunny Deol", "Bobby Deol", "Esha Deol",
    "Karan Deol", "Rajveer Deol", "Abhay Deol",
    # Dutt family
    "Sanjay Dutt", "Trishala Dutt",
    # Khanna families
    "Twinkle Khanna", "Akshaye Khanna", "Rinke Khanna",
    # Yash Chopra family
    "Uday Chopra",
    # Mukherjee-Samarth family
    "Rani Mukerji", "Kajol", "Tanishaa Mukerji",
    "Mohnish Bahl",
    # Sinha family
    "Sonakshi Sinha", "Luv Sinha", "Kussh Sinha",
    # Oberoi family
    "Vivek Oberoi",
    # Ganesan family
    "Rekha",
    # Bhatt family
    "Alia Bhatt", "Pooja Bhatt", "Emraan Hashmi", "Rahul Bhatt",
    # Dhawan family
    "Varun Dhawan", "Rohit Dhawan",
    # Shetty family (Suniel)
    "Athiya Shetty", "Ahan Shetty",
    # Shroff family (Jackie)
    "Tiger Shroff", "Krishna Shroff",
    # Panday family (Chunky)
    "Ananya Panday", "Rysa Panday",
    # Roy Kapur / Roy Kapoor
    "Aditya Roy Kapur", "Kunaal Roy Kapur",
    # Kaushal family (Sham Kaushal, action director)
    "Vicky Kaushal", "Sunny Kaushal",
    # Khan (Irrfan)
    "Babil Khan", "Ayaan Khan",
    # Devgan family
    "Aaman Devgan", "Nysa Devgan",
    # Tandon family
    "Rasha Thadani",
    # Babbar family
    "Pratik Babbar", "Prateik Babbar", "Juhi Babbar", "Arya Babbar",
    # Bachchan (Shweta's kids already - Agastya, Navya Naveli)
    "Navya Naveli Nanda",
    # Chunky Panday family
    "Ahaan Panday",
    # Aditya Pancholi family
    "Sooraj Pancholi",
    # Anupam Kher / Kirron Kher family
    "Sikandar Kher",
    # Anil Kapoor family (son + nephew)
    "Harshvardhan Kapoor", "Mohit Marwah",
    # Vashu Bhagnani family
    "Jackky Bhagnani",
    # Javed Jaffrey family
    "Meezaan Jaffery", "Meezaan Jafri",
    # Mithun Chakraborty family (one person, two stage names)
    "Mimoh Chakraborty", "Mahaakshay Chakraborty",
    # Feroz Khan family
    "Fardeen Khan",
    # Sanjay Khan family
    "Zayed Khan",
    # Misc film families
    "Athiya Shetty", "Krishna Shroff",
}


def normalise(name: str) -> str:
    name = re.sub(r"\s+", " ", name).strip()
    name = re.sub(r"^[•·\-\*]\s*", "", name)
    return name


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


def is_nepo(name: str) -> bool:
    return normalise(name) in NEPO_KIDS


def main():
    with open(IN_CSV, encoding="utf-8") as fh:
        films = list(csv.DictReader(fh))

    # 1. Tag films
    tagged = []
    for f in films:
        cast = [normalise(c) for c in f["cast"].split(";") if normalise(c)]
        # de-dup within film
        seen = set()
        unique_cast = []
        for c in cast:
            if c not in seen:
                seen.add(c)
                unique_cast.append(c)
        hits = [c for c in unique_cast if is_nepo(c)]
        gr_str = f["gross_cr"]
        gr = float(gr_str) if gr_str else None
        tagged.append({
            "year": int(f["year"]),
            "title": f["title"],
            "director": f["director"],
            "cast": "; ".join(unique_cast),
            "gross_raw": f["gross_raw"],
            "gross_cr": gr_str,
            "nepo_kid": "yes" if hits else "no",
            "nepo_kids_in_cast": "; ".join(hits),
        })

    with open(TAGGED_CSV, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=[
            "year", "title", "director", "cast",
            "gross_raw", "gross_cr", "nepo_kid", "nepo_kids_in_cast",
        ])
        writer.writeheader()
        writer.writerows(tagged)
    print(f"Wrote {len(tagged)} tagged films -> {TAGGED_CSV}", file=sys.stderr)

    # 2. Long format: one row per actor-film
    long_rows = []
    actor_films = defaultdict(list)  # actor -> list of (year, title, gross_cr)
    for f in tagged:
        cast = [normalise(c) for c in f["cast"].split(";") if normalise(c)]
        for actor in cast:
            gr = float(f["gross_cr"]) if f["gross_cr"] else None
            long_rows.append({
                "actor": actor,
                "actor_nepo": "yes" if is_nepo(actor) else "no",
                "year": f["year"],
                "movie": f["title"],
                "gross_cr": f["gross_cr"],
                "film_has_nepo_cast": f["nepo_kid"],
                "director": f["director"],
            })
            actor_films[actor].append((f["year"], f["title"], gr))

    long_rows.sort(key=lambda r: (r["actor"], r["year"], r["movie"]))
    with open(LONG_CSV, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=[
            "actor", "actor_nepo", "year", "movie", "gross_cr",
            "film_has_nepo_cast", "director",
        ])
        writer.writeheader()
        writer.writerows(long_rows)
    print(f"Wrote {len(long_rows)} actor-film rows -> {LONG_CSV}", file=sys.stderr)

    # 3. Wide format: one row per actor
    for a in actor_films:
        actor_films[a].sort(key=lambda x: (x[0], x[1]))
    max_films = max(len(v) for v in actor_films.values())

    fieldnames = ["actor", "nepo", "num_films", "total_gross_cr", "films_with_gross"]
    for i in range(1, max_films + 1):
        fieldnames += [f"year_{i}", f"movie_{i}", f"gross_cr_{i}"]

    sorted_actors = sorted(actor_films.items(), key=lambda kv: (-len(kv[1]), kv[0]))
    with open(WIDE_CSV, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for actor, films in sorted_actors:
            grosses = [g for _, _, g in films if g is not None]
            total = sum(grosses)
            row = {
                "actor": actor,
                "nepo": "yes" if is_nepo(actor) else "no",
                "num_films": len(films),
                "total_gross_cr": f"{total:.2f}",
                "films_with_gross": len(grosses),
            }
            for i, (year, title, gross) in enumerate(films, 1):
                row[f"year_{i}"] = year
                row[f"movie_{i}"] = title
                row[f"gross_cr_{i}"] = f"{gross:.2f}" if gross is not None else ""
            writer.writerow(row)
    print(f"Wrote {len(sorted_actors)} actors (max {max_films} films) -> {WIDE_CSV}",
          file=sys.stderr)

    # 4. Yearly aggregates
    by_year = defaultdict(lambda: {
        "nepo_films": 0, "nepo_gross": 0.0, "nepo_with_gross": 0,
        "non_films": 0, "non_gross": 0.0, "non_with_gross": 0,
    })
    for f in tagged:
        gr = float(f["gross_cr"]) if f["gross_cr"] else None
        bucket = "nepo" if f["nepo_kid"] == "yes" else "non"
        by_year[f["year"]][f"{bucket}_films"] += 1
        if gr is not None:
            by_year[f["year"]][f"{bucket}_gross"] += gr
            by_year[f["year"]][f"{bucket}_with_gross"] += 1

    with open(AGG_CSV, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow([
            "year",
            "nepo_films", "nepo_share_films_pct",
            "nepo_gross_cr", "nepo_avg_gross_cr",
            "non_films", "non_gross_cr", "non_avg_gross_cr",
        ])
        for year in sorted(by_year):
            b = by_year[year]
            total_f = b["nepo_films"] + b["non_films"]
            share_f = b["nepo_films"] / total_f * 100 if total_f else 0
            nepo_avg = b["nepo_gross"] / b["nepo_with_gross"] if b["nepo_with_gross"] else 0
            non_avg = b["non_gross"] / b["non_with_gross"] if b["non_with_gross"] else 0
            writer.writerow([
                year, b["nepo_films"], f"{share_f:.1f}",
                f"{b['nepo_gross']:.2f}", f"{nepo_avg:.2f}",
                b["non_films"], f"{b['non_gross']:.2f}", f"{non_avg:.2f}",
            ])
    print(f"Wrote yearly aggregates -> {AGG_CSV}", file=sys.stderr)

    # Summary
    n_nepo = sum(1 for f in tagged if f["nepo_kid"] == "yes")
    total = len(tagged)
    print(f"\n=== Overall 2000-2025 ===", file=sys.stderr)
    print(f"Films total:        {total}", file=sys.stderr)
    print(f"With any nepo kid:  {n_nepo} ({n_nepo*100/total:.1f}%)", file=sys.stderr)
    print(f"\nPer-year nepo share:")
    print(f"{'year':<6}{'films':>7}{'nepo':>7}{'share':>8}{'avg_gr_nepo':>13}{'avg_gr_non':>13}")
    print("-" * 60)
    for year in sorted(by_year):
        b = by_year[year]
        total_f = b["nepo_films"] + b["non_films"]
        share_f = b["nepo_films"] / total_f * 100 if total_f else 0
        nepo_avg = b["nepo_gross"] / b["nepo_with_gross"] if b["nepo_with_gross"] else 0
        non_avg = b["non_gross"] / b["non_with_gross"] if b["non_with_gross"] else 0
        print(f"{year:<6}{total_f:>7}{b['nepo_films']:>7}{share_f:>7.1f}%"
              f"{nepo_avg:>13.2f}{non_avg:>13.2f}")


if __name__ == "__main__":
    main()
