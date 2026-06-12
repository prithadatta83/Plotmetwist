# Bollywood Nepotism Analysis (2000–2025)

A data-driven look at how much of Bollywood's last quarter-century has been driven by star kids. **2,824 films · 3,425 actors · 26 years.**

Living writeup: **[plot-twist-nepotism.html](./plot-twist-nepotism.html)** (open the file in a browser, or host via GitHub Pages).

## Key findings

| Question | Answer |
|---|---|
| Share of films with ≥1 nepo kid | **32.8%** (peak 53% in 2006, trough 19% in 2020) |
| Share of actors who are nepo kids | **2.3%** (79 of 3,425) — a 14× over-representation in screen time |
| Films / actor (≥1 film) | nepo **16.6**, non-nepo **3.4** |
| % of actors who appear in only one film | nepo **14%**, non-nepo **63%** |
| Correlation: gross vs IMDb rating | +0.18 (weak) |
| Correlation: gross vs log(IMDb votes) | **+0.72** (strong) — votes is the better proxy |
| % of nepo kids with a Filmfare Award | **47%** (vs 8% of non-nepo) |
| Catchup tax | non-nepo needs ~1.4× as many films to match nepo cumulative vote reach |

## What this repository contains

### Reports
- `plot-twist-nepotism.html` — the polished writeup
- `nepotism_analysis.ipynb` — Jupyter notebook with the full analysis pipeline

### Data (CSVs)
- `bollywood_all_with_nepo.csv` — every film 2000–2025 (`year, title, director, cast, gross, nepo_kid`)
- `actor_timeseries_long_all_with_ratings.csv` — one row per actor-film (with IMDb rating, votes)
- `actor_timeseries_wide_all.csv` — one row per actor, films spread across columns
- `yearly_aggregates_all.csv` — per-year nepo vs non-nepo summary
- `film_ratings.csv` — film × IMDb rating/votes lookup
- `career_trajectory_summary.csv` — per-actor regression slopes
- `actors_with_awards.csv` — National + Filmfare winner flags

### Scrapers
- `scrape_bollywood_all_2000_2025.py` — Wikipedia year-index pages
- `fill_gross_from_wiki.py` — per-film infobox gross
- `fetch_imdb_ratings.py` — IMDb TSV dumps (free; downloads ~250MB)
- `fetch_awards.py` — National Film Awards + Filmfare lists
- `scrape_bollywood_credits.py` — director + cast from infoboxes

### Analysis
- `tag_and_analyze_all.py` — nepo-tagging + time-series + aggregates (run this after scraping)
- `career_trajectory.py` — per-actor regression of rating/votes vs film number
- `rating_gross_correlation.py` — rating vs gross vs votes correlations
- `missingness_bias.py` — checks whether gross-missingness is correlated with nepo status
- `non_nepo_breakthroughs.py` — outsiders who reached nepo vote levels
- `rajkummar_vs_sonam.py` — case-study chart
- `nepo_pct_bar.py` — yearly bar + trend line chart

### Charts (PNG)
- `chart_yearly_with_debuts.png` — total films + nepo % + key debut labels
- `chart_trajectory_votes.png` — career trajectory by film position
- `chart_cumulative_votes.png` — cumulative-votes catchup curve
- `chart_rajkummar_vs_sonam.png` — case-study
- `chart_gross_vs_rating_votes.png` — correlation scatter
- `chart_slope_distribution.png` — per-actor slope histogram

## Reproducing the analysis

```bash
pip install -r requirements.txt

# 1. Scrape Wikipedia (~5 min)
python scrape_bollywood_all_2000_2025.py

# 2. Fill gross from individual film pages (~17 min, 2,500 requests)
python fill_gross_from_wiki.py

# 3. Tag + aggregate
python tag_and_analyze_all.py

# 4. Pull IMDb ratings (downloads ~260MB of TSV dumps)
python fetch_imdb_ratings.py

# 5. Generate all analysis charts
python nepo_pct_bar.py
python career_trajectory.py
python rating_gross_correlation.py
python rajkummar_vs_sonam.py
```

Or open `nepotism_analysis.ipynb` and Run-All.

## Method notes

- **Nepo kid** = first-generation child/close relative of a prominent Bollywood figure. Curated list of 92 unique people lives at the top of `tag_and_analyze_all.py` (`NEPO_KIDS` set) — edit and rerun to refine.
- **Excluded from nepo flag**: spouses who married in (Aishwarya Rai), actors with film-adjacent but non-film parents (Riteish Deshmukh's father was a politician, Veer Pahariya's family is political).
- **Gross data** is incomplete (56% missing) and the missingness is heavily skewed toward outsider films, which is why most quantitative findings rely on IMDb vote count instead.
- **Years covered**: 2000–2025 (Wikipedia "List of Bollywood films of YYYY" indexes). Pre-2000 films are out of scope.

## Caveats

This is an **observational** dataset. It can describe correlations (nepo kids → more films, more reach, lower-rated films open bigger) but cannot prove causation about nepotism vs talent vs studio strategy. The dataset is biased toward films that got Wikipedia entries and IMDb ratings, which itself favors films that drew some audience.

## License

CC BY 4.0 for the data and writeup; MIT for the scripts.
