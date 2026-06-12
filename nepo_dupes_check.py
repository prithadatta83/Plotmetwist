"""Check for (a) duplicate films among nepo-tagged ones, and
(b) duplicate names / variant-spellings in the curated NEPO_KIDS set."""

import csv
from collections import Counter

# (a) Duplicate films among nepo-tagged
rows = list(csv.DictReader(open("bollywood_all_with_nepo.csv", encoding="utf-8")))
nepo_rows = [r for r in rows if r["nepo_kid"] == "yes"]
key_counts = Counter((int(r["year"]), r["title"]) for r in nepo_rows)
print(f"Nepo-tagged film rows:                 {len(nepo_rows)}")
print(f"Unique (year, title):                  {len(key_counts)}")
print(f"Exact duplicates:                      {sum(1 for c in key_counts.values() if c > 1)}")

# (b) Variant spellings inside NEPO_KIDS
# Load the set by importing from tag_and_analyze_all
import importlib.util
spec = importlib.util.spec_from_file_location("tag_mod", "tag_and_analyze_all.py")
tag_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tag_mod)
NEPO = tag_mod.NEPO_KIDS

print(f"\nNEPO_KIDS entries:                     {len(NEPO)}")

# Map known same-person variants → canonical
SAME_PERSON = {
    "Karisma Kapoor": "Karisma Kapoor",
    "Karishma Kapoor": "Karisma Kapoor",
    "Kareena Kapoor": "Kareena Kapoor",
    "Kareena Kapoor Khan": "Kareena Kapoor",
    "Mimoh Chakraborty": "Mahaakshay Chakraborty",
    "Mahaakshay Chakraborty": "Mahaakshay Chakraborty",
    "Meezaan Jaffery": "Meezaan Jaffrey",
    "Meezaan Jafri": "Meezaan Jaffrey",
    "Pratik Babbar": "Prateik Babbar",
    "Prateik Babbar": "Prateik Babbar",
}

canonical = set()
duplicates = []
for name in NEPO:
    canon = SAME_PERSON.get(name, name)
    if canon in canonical:
        duplicates.append((name, canon))
    canonical.add(canon)

print(f"Unique people (after merging variants): {len(canonical)}")
print(f"Variant entries (extras):              {len(NEPO) - len(canonical)}")

print("\nKnown variant pairs (same person, different spellings):")
groups = {}
for name, canon in SAME_PERSON.items():
    groups.setdefault(canon, []).append(name)
for canon, variants in groups.items():
    if len(variants) > 1:
        print(f"  {canon}: {variants}")
