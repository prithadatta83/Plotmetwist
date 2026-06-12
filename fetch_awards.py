"""
Scrape Wikipedia lists of National Film Award + Filmfare Award winners
(acting categories), build a set of winners per award system,
then cross-reference with the actors in our dataset.

Outputs:
  - awards_winners.csv  (actor, won_national, won_filmfare)
  - prints summary stats: nepo vs non-nepo award rates
"""

import csv
import re
import sys
import time
import importlib.util
import requests
from bs4 import BeautifulSoup

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

HEADERS = {
    "User-Agent": "Mozilla/5.0 (research, pritha.datta@ondc.org)"
}

NATIONAL_PAGES = [
    "National_Film_Award_for_Best_Actor",
    "National_Film_Award_for_Best_Actress",
    "National_Film_Award_for_Best_Supporting_Actor",
    "National_Film_Award_for_Best_Supporting_Actress",
]

FILMFARE_PAGES = [
    "Filmfare_Award_for_Best_Actor",
    "Filmfare_Award_for_Best_Actress",
    "Filmfare_Award_for_Best_Supporting_Actor",
    "Filmfare_Award_for_Best_Supporting_Actress",
    "Filmfare_Critics_Award_for_Best_Actor",
    "Filmfare_Critics_Award_for_Best_Actress",
    "Filmfare_Award_for_Best_Male_Debut",
    "Filmfare_Award_for_Best_Female_Debut",
]


def norm(s):
    return re.sub(r"\s+", " ", s or "").strip()


def scrape_winners(slug):
    """Pull winner names from a Wikipedia award-list page."""
    url = f"https://en.wikipedia.org/wiki/{slug}"
    r = requests.get(url, headers=HEADERS, timeout=30)
    if r.status_code != 200:
        print(f"  {slug}: HTTP {r.status_code}", file=sys.stderr)
        return set()
    soup = BeautifulSoup(r.text, "html.parser")
    winners = set()
    for table in soup.find_all("table", class_="wikitable"):
        headers = [norm(th.get_text()).lower() for th in table.find_all("th")]
        # Heuristic: look for a column titled "actor", "actress", "recipient", "winner", "recipient(s)"
        actor_idx = None
        for i, h in enumerate(headers):
            if any(k in h for k in ("recipient", "actor", "actress", "winner", "performer")):
                actor_idx = i
                break
        if actor_idx is None:
            continue
        # Process rows: handle rowspans (year/ceremony spans)
        for tr in table.find_all("tr")[1:]:
            tds = tr.find_all(["td", "th"])
            if not tds:
                continue
            # Strip refs
            for sup in tr.find_all("sup"):
                sup.decompose()
            # Take all <a> hrefs inside the row — usually the actor link is the first that points to /wiki/
            # Be conservative: only take links whose href starts with /wiki/ and is NOT a film page
            for a in tr.find_all("a", href=True):
                href = a["href"]
                if not href.startswith("/wiki/"):
                    continue
                if "(film)" in href.lower():
                    continue
                name = norm(a.get_text())
                if not name or len(name) < 3:
                    continue
                # Reject common non-actor link patterns
                if name.lower() in {"hindi", "tamil", "english", "telugu", "kannada", "malayalam", "marathi", "bengali"}:
                    continue
                winners.add(name)
                break  # only first reasonable link per row
    return winners


def collect(pages, label):
    winners = set()
    for slug in pages:
        print(f"  fetching {slug}...", file=sys.stderr)
        winners |= scrape_winners(slug)
        time.sleep(0.8)
    print(f"  {label} winners (raw): {len(winners)}", file=sys.stderr)
    return winners


# ----- Run -----
print("== Step 1: scrape award pages ==", file=sys.stderr)
nat = collect(NATIONAL_PAGES, "National")
fil = collect(FILMFARE_PAGES, "Filmfare")

# Save raw
with open("award_winners_raw.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow(["name", "national", "filmfare"])
    for n in sorted(nat | fil):
        w.writerow([n, n in nat, n in fil])

# ----- Cross-reference with our actor list -----
print("\n== Step 2: cross-ref with our actor list ==", file=sys.stderr)
# Load nepo set
spec = importlib.util.spec_from_file_location("tag_mod", "tag_and_analyze_all.py")
tag_mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(tag_mod)
NEPO = set(tag_mod.NEPO_KIDS)

SAME = {
    "Karishma Kapoor": "Karisma Kapoor",
    "Kareena Kapoor Khan": "Kareena Kapoor",
    "Mimoh Chakraborty": "Mahaakshay Chakraborty",
    "Meezaan Jafri": "Meezaan Jaffery",
    "Pratik Babbar": "Prateik Babbar",
    "Shahrukh Khan": "Shah Rukh Khan",
    "Ajay Devgan": "Ajay Devgn",
    "Aishwarya Rai Bachchan": "Aishwarya Rai",
}

def canon(n):
    n = norm(n)
    return SAME.get(n, n)

NEPO_C = {canon(n) for n in NEPO}

# Load our actors from long CSV
rows = list(csv.DictReader(open("actor_timeseries_long_all_with_ratings.csv", encoding="utf-8")))
from collections import Counter
actor_films = Counter()
for r in rows:
    a = canon(r["actor"])
    if not a or len(a) < 3 or a.startswith(("&", "(")):
        continue
    actor_films[a] += 1
our_actors = set(actor_films.keys())

nat_c = {canon(n) for n in nat}
fil_c = {canon(n) for n in fil}

won_nat = our_actors & nat_c
won_fil = our_actors & fil_c

# Save per-actor with award flags
with open("actors_with_awards.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow(["actor", "nepo", "n_films", "won_national", "won_filmfare"])
    for a in sorted(our_actors, key=lambda x: -actor_films[x]):
        w.writerow([a, a in NEPO_C, actor_films[a],
                    a in nat_c, a in fil_c])

# ----- Stats -----
def split(actors):
    nepo = [a for a in actors if a in NEPO_C]
    non = [a for a in actors if a not in NEPO_C]
    return nepo, non

nepo_actors, non_actors = split(our_actors)
nepo_nat, non_nat = split(won_nat)
nepo_fil, non_fil = split(won_fil)

print(f"\n=== Actors in our dataset ===")
print(f"  Total:     {len(our_actors)}")
print(f"  Nepo:      {len(nepo_actors)}")
print(f"  Non-nepo:  {len(non_actors)}")

print(f"\n=== National Film Award (acting) ===")
print(f"  Total winners in our data:     {len(won_nat)}")
print(f"  Nepo winners:                  {len(nepo_nat)} ({len(nepo_nat)/len(nepo_actors)*100:.1f}% of nepo)")
print(f"  Non-nepo winners:              {len(non_nat)} ({len(non_nat)/len(non_actors)*100:.1f}% of non-nepo)")

print(f"\n=== Filmfare Award (acting + debut + critics) ===")
print(f"  Total winners in our data:     {len(won_fil)}")
print(f"  Nepo winners:                  {len(nepo_fil)} ({len(nepo_fil)/len(nepo_actors)*100:.1f}% of nepo)")
print(f"  Non-nepo winners:              {len(non_fil)} ({len(non_fil)/len(non_actors)*100:.1f}% of non-nepo)")

# Detailed lists
print(f"\n=== Nepo kids in our data who won a National Award ({len(nepo_nat)}) ===")
for a in sorted(nepo_nat):
    print(f"  - {a}")
print(f"\n=== Nepo kids in our data who won a Filmfare Award ({len(nepo_fil)}) ===")
for a in sorted(nepo_fil):
    print(f"  - {a}")
