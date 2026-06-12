import csv

rows = list(csv.DictReader(open("bollywood_all_with_nepo.csv", encoding="utf-8")))

def has_gross(r):
    return bool(r["gross_cr"].strip())

def is_nepo(r):
    return r["nepo_kid"] == "yes"

# --- Overall: missing rate by nepo status ---
nepo_all = [r for r in rows if is_nepo(r)]
non_all = [r for r in rows if not is_nepo(r)]
nepo_missing = sum(1 for r in nepo_all if not has_gross(r))
non_missing = sum(1 for r in non_all if not has_gross(r))

print("=== Missing-gross rate by nepo status (all years) ===")
print(f"Nepo films:     {len(nepo_all):>5} total, {nepo_missing:>5} missing "
      f"({nepo_missing/len(nepo_all)*100:.1f}%)")
print(f"Non-nepo films: {len(non_all):>5} total, {non_missing:>5} missing "
      f"({non_missing/len(non_all)*100:.1f}%)")
print()

# --- Per year: nepo share among ALL vs among films WITH gross ---
print("=== Nepo share: ALL films vs only-films-with-gross ===")
print(f"{'year':<6}{'all_n':>6}{'all_nepo%':>11}{'wg_n':>6}{'wg_nepo%':>11}{'delta':>8}")
print("-" * 50)
by_year = {}
for r in rows:
    y = int(r["year"])
    by_year.setdefault(y, [])
    by_year[y].append(r)

deltas = []
for y in sorted(by_year):
    yr = by_year[y]
    all_n = len(yr)
    all_nepo = sum(1 for r in yr if is_nepo(r))
    all_pct = all_nepo / all_n * 100

    wg = [r for r in yr if has_gross(r)]
    wg_n = len(wg)
    wg_nepo = sum(1 for r in wg if is_nepo(r))
    wg_pct = wg_nepo / wg_n * 100 if wg_n else 0

    delta = wg_pct - all_pct
    deltas.append(delta)
    print(f"{y:<6}{all_n:>6}{all_pct:>10.1f}%{wg_n:>6}{wg_pct:>10.1f}%{delta:>+7.1f}")

# Overall comparison
all_pct_o = sum(1 for r in rows if is_nepo(r)) / len(rows) * 100
wg = [r for r in rows if has_gross(r)]
wg_pct_o = sum(1 for r in wg if is_nepo(r)) / len(wg) * 100
print("-" * 50)
print(f"{'ALL':<6}{len(rows):>6}{all_pct_o:>10.1f}%{len(wg):>6}{wg_pct_o:>10.1f}%{wg_pct_o-all_pct_o:>+7.1f}")
print()
print(f"Avg per-year delta (wg% - all%): {sum(deltas)/len(deltas):+.1f} pts")
print(f"Years where with-gross nepo% is HIGHER: {sum(1 for d in deltas if d>0)}/{len(deltas)}")
