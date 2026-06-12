import csv

rows = list(csv.DictReader(open("bollywood_all_with_nepo.csv", encoding="utf-8")))
total = len(rows)

has_cr = sum(1 for r in rows if r["gross_cr"].strip())
has_raw = sum(1 for r in rows if r["gross_raw"].strip())
raw_no_cr = sum(1 for r in rows if r["gross_raw"].strip() and not r["gross_cr"].strip())
no_raw = sum(1 for r in rows if not r["gross_raw"].strip())

print(f"Total films:                         {total}")
print(f"Has numeric gross_cr:                {has_cr}  ({has_cr/total*100:.1f}%)")
print(f"MISSING numeric gross_cr:            {total-has_cr}  ({(total-has_cr)/total*100:.1f}%)")
print(f"  - of which: no gross_raw at all:   {no_raw}  ({no_raw/total*100:.1f}%)")
print(f"  - of which: raw present, unparsed: {raw_no_cr}  ({raw_no_cr/total*100:.1f}%)")
print()

# By year
print(f"{'year':<6}{'total':>7}{'has_cr':>8}{'missing':>9}{'miss%':>8}")
print("-" * 40)
by_year = {}
for r in rows:
    y = int(r["year"])
    by_year.setdefault(y, {"t": 0, "c": 0})
    by_year[y]["t"] += 1
    if r["gross_cr"].strip():
        by_year[y]["c"] += 1
for y in sorted(by_year):
    t = by_year[y]["t"]
    c = by_year[y]["c"]
    miss = t - c
    print(f"{y:<6}{t:>7}{c:>8}{miss:>9}{miss/t*100:>7.1f}%")
