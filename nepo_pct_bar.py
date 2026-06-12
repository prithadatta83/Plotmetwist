"""Year-on-year bars of total films + nepo % trend line + key debut annotations."""

import csv
import sys
import importlib.util
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Load the nepo set
spec = importlib.util.spec_from_file_location("tag_mod", "tag_and_analyze_all.py")
tag_mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(tag_mod)
NEPO = set(tag_mod.NEPO_KIDS)

SAME = {
    "Karishma Kapoor": "Karisma Kapoor",
    "Kareena Kapoor Khan": "Kareena Kapoor",
    "Mimoh Chakraborty": "Mahaakshay Chakraborty",
    "Meezaan Jafri": "Meezaan Jaffery",
    "Pratik Babbar": "Prateik Babbar",
}
def canon(n): return SAME.get(n.strip(), n.strip())
NEPO_C = {canon(n) for n in NEPO}

rows = list(csv.DictReader(open("bollywood_all_with_nepo.csv", encoding="utf-8")))

# Yearly totals + nepo share
by_year = {}
# First appearance per nepo actor
first_year = {}
for r in rows:
    y = int(r["year"])
    by_year.setdefault(y, {"nepo": 0, "non": 0})
    by_year[y]["nepo" if r["nepo_kid"] == "yes" else "non"] += 1
    for c in r["cast"].split(";"):
        c = canon(c)
        if c in NEPO_C:
            if c not in first_year or y < first_year[c]:
                first_year[c] = y

# Build debuts per year (first time the actor shows up in our dataset window)
debuts_by_year = {}
for actor, y in first_year.items():
    debuts_by_year.setdefault(y, []).append(actor)

# Curated list of "notable" debuts to annotate (the big launches)
NOTABLE = {
    "Hrithik Roshan", "Abhishek Bachchan", "Kareena Kapoor",
    "Vivek Oberoi", "Esha Deol",
    "Emraan Hashmi", "Shahid Kapoor",
    "Tusshar Kapoor",
    "Ranbir Kapoor", "Sonam Kapoor",
    "Imran Khan",
    "Sonakshi Sinha",
    "Arjun Kapoor",
    "Alia Bhatt", "Varun Dhawan",
    "Tiger Shroff",
    "Sara Ali Khan", "Janhvi Kapoor", "Ishaan Khatter",
    "Ananya Panday",
    "Suhana Khan", "Khushi Kapoor", "Agastya Nanda",
    "Ahaan Panday",
}
notable_debuts = {}
for y, names in debuts_by_year.items():
    big = [n for n in names if n in NOTABLE]
    if big:
        notable_debuts[y] = sorted(big)

years   = sorted(by_year)
totals  = [by_year[y]["nepo"] + by_year[y]["non"] for y in years]
nepo    = [by_year[y]["nepo"] for y in years]
pcts    = [n / t * 100 for n, t in zip(nepo, totals)]

# Plot with a dedicated top panel for debut labels
fig, (ax_top, ax1) = plt.subplots(
    2, 1, figsize=(16, 9), sharex=True,
    gridspec_kw={"height_ratios": [1.3, 4]},
)
ax_top.set_ylim(0, 1)
ax_top.axis("off")

# Bars: total films
bars = ax1.bar(years, totals, color="#7f8c8d", alpha=0.7, label="Total films")
for y, t in zip(years, totals):
    ax1.text(y, t + 1.5, str(t), ha="center", fontsize=8, fontweight="bold", color="#333")

ax1.set_xlabel("Year")
ax1.set_ylabel("Total films released", color="#333")
ax1.tick_params(axis="y", labelcolor="#333")
ax1.set_xticks(years)
ax1.set_xticklabels([str(y) for y in years], rotation=45)
ax1.set_ylim(0, max(totals) * 1.15)
ax1.grid(axis="y", alpha=0.3)

# Line: nepo %
ax2 = ax1.twinx()
ax2.plot(years, pcts, "o-", color="#c0392b", linewidth=2.2, markersize=7, label="Nepo share (%)")
for y, p in zip(years, pcts):
    ax2.text(y, p + 1.4, f"{p:.0f}%", ha="center", fontsize=7, color="#c0392b", fontweight="bold")
ax2.set_ylabel("Nepo share of films (%)", color="#c0392b")
ax2.tick_params(axis="y", labelcolor="#c0392b")
ax2.set_ylim(0, max(pcts) * 1.25)

# Debut annotations on the top panel — vertical lines into the bars + name stack
for y, names in notable_debuts.items():
    label = "\n".join(names)
    # Vertical dotted line from top panel down through the bar's top
    ax1.axvline(y, color="#1f4e79", linestyle=":", linewidth=0.7, alpha=0.45)
    ax_top.text(
        y, 0.95, label,
        ha="center", va="top",
        fontsize=8, color="#1f4e79", fontweight="bold",
    )

ax1.legend([bars, ax2.lines[0]], ["Total films", "Nepo share (%)"], loc="upper left")
plt.title(
    "Bollywood 2000–2025: total films (bars), nepo share (line), key nepo-kid debuts (labels)",
    fontsize=12,
)
plt.tight_layout()
plt.savefig("chart_yearly_with_debuts.png", dpi=140)
print("Saved chart_yearly_with_debuts.png", file=sys.stderr)

print("\nNotable nepo debuts by year (first appearance in our 2000–2025 data):")
for y in sorted(notable_debuts):
    print(f"  {y}: {', '.join(notable_debuts[y])}")
