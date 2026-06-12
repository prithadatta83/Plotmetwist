"""
Read bollywood_credits_2000_2010.csv and add:
  - nepo_kid: yes/no  (yes if any cast member is on the curated list)
  - nepo_kids_in_cast: semicolon-separated names that matched

Curated list: actors who are first-generation children of prominent
Bollywood/film-industry figures. Edit NEPO_KIDS below to refine.
"""

import csv
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

IN_CSV = "bollywood_credits_2000_2010.csv"
OUT_CSV = "bollywood_with_nepo_2000_2010.csv"

# Curated map: canonical name -> short reason
NEPO_KIDS = {
    # Bachchan family
    "Abhishek Bachchan": "son of Amitabh & Jaya Bachchan",
    # Kapoor family
    "Karisma Kapoor": "Kapoor family (Randhir Kapoor)",
    "Karishma Kapoor": "Kapoor family (Randhir Kapoor)",
    "Kareena Kapoor": "Kapoor family (Randhir Kapoor)",
    "Kareena Kapoor Khan": "Kapoor family (Randhir Kapoor)",
    "Ranbir Kapoor": "son of Rishi Kapoor & Neetu Singh",
    "Rishi Kapoor": "son of Raj Kapoor",
    "Tusshar Kapoor": "son of Jeetendra",
    "Shahid Kapoor": "son of Pankaj Kapur",
    "Sonam Kapoor": "daughter of Anil Kapoor",
    # Roshan family
    "Hrithik Roshan": "son of Rakesh Roshan",
    # Salim Khan family
    "Salman Khan": "son of Salim Khan",
    "Sohail Khan": "son of Salim Khan",
    "Arbaaz Khan": "son of Salim Khan",
    # Tahir Hussain / Aamir Khan family
    "Aamir Khan": "son of Tahir Hussain",
    "Faisal Khan": "son of Tahir Hussain",
    "Imran Khan": "nephew of Aamir Khan (Hussain family)",
    # Pataudi-Tagore family
    "Saif Ali Khan": "son of Sharmila Tagore",
    "Soha Ali Khan": "daughter of Sharmila Tagore",
    # Deol family
    "Sunny Deol": "son of Dharmendra",
    "Bobby Deol": "son of Dharmendra",
    "Esha Deol": "daughter of Hema Malini & Dharmendra",
    # Dutt family
    "Sanjay Dutt": "son of Sunil Dutt & Nargis",
    # Khanna families
    "Twinkle Khanna": "daughter of Rajesh Khanna & Dimple Kapadia",
    "Akshaye Khanna": "son of Vinod Khanna",
    # Yash Chopra family
    "Uday Chopra": "son of Yash Chopra",
    # Mukherjee-Samarth family
    "Rani Mukerji": "Mukherjee-Samarth family",
    "Kajol": "Mukherjee-Samarth family (daughter of Tanuja)",
    # Sinha family
    "Sonakshi Sinha": "daughter of Shatrughan Sinha",
    # Oberoi family
    "Vivek Oberoi": "son of Suresh Oberoi",
    # Ganesan family
    "Rekha": "daughter of Gemini Ganesan",
}


def canonical(name: str) -> str:
    return re.sub(r"\s+", " ", name).strip()


nepo_set = {canonical(k): v for k, v in NEPO_KIDS.items()}


def find_nepo_in_cast(cast_field: str):
    if not cast_field:
        return []
    parts = [canonical(p) for p in cast_field.split(";")]
    hits = []
    for p in parts:
        if p in nepo_set and p not in hits:
            hits.append(p)
    return hits


def main():
    with open(IN_CSV, encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))

    out_rows = []
    for r in rows:
        hits = find_nepo_in_cast(r["cast"])
        r["nepo_kid"] = "yes" if hits else "no"
        r["nepo_kids_in_cast"] = "; ".join(hits)
        out_rows.append(r)

    fieldnames = ["year", "title", "gross", "director", "cast", "nepo_kid", "nepo_kids_in_cast", "url"]
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(out_rows)

    yes_count = sum(1 for r in out_rows if r["nepo_kid"] == "yes")
    print(f"Wrote {len(out_rows)} rows to {OUT_CSV}", file=sys.stderr)
    print(f"nepo_kid=yes: {yes_count}/{len(out_rows)} "
          f"({yes_count*100/len(out_rows):.0f}%)", file=sys.stderr)

    # Print summary table
    for r in out_rows:
        flag = r["nepo_kid"].upper()
        names = r["nepo_kids_in_cast"]
        print(f"{r['year']}  [{flag}]  {r['title']}"
              + (f"   -> {names}" if names else ""))


if __name__ == "__main__":
    main()
