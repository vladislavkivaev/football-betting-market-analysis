# Football Betting Integrity Monitor — Streamlit app

The presentation + dashboard for the capstone. A *market-efficiency study with
anomaly screening* — not a match-fixing detector. Six pages, left-sidebar nav,
black/blue theme.

## Where this lives

The app is meant to sit in `football-betting-integrity-monitor/dashboard/`.
It auto-finds the real data one level up at `../data/processed/`:

```
football-betting-integrity-monitor/
├── dashboard/          ← this app  (run `streamlit run app.py` here)
├── data/processed/     ← scored_matches.parquet, features.parquet, feature_dictionary.csv
└── notebooks/
```

## Run it

```bash
cd dashboard
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Opens at http://localhost:8501.

## Pages

1. **Overview** — title, data, leagues, pipeline, the four hypotheses.
2. **Betting 101** — decimal/US odds, implied %, the 106% overround (WC-2026
   opener), real overround-by-league chart.
3. **Market Efficiency** — calibration hero, KPIs, favourite–longshot bias,
   results, draw mispricing, retail-vs-sharp margin.
4. **Hypothesis Testing** — colour-coded H1–H4 scorecard, the H3 win, "why
   nulls matter", effect-size details.
5. **Anomaly Detection** — score distribution + threshold, SHAP drivers, the
   open→close drift example, signals list, flag rate by league, ethics strip.
6. **Match Dashboard** — filter rail, selectable match table, and a
   selected-match detail panel. Select several rows and step through them with
   the **Next ›** button.

## Demo data vs. real data

The app auto-detects `../data/processed/scored_matches.parquet`. If it's there,
you get **live data** (real fixtures, odds, scores, flags). If not, the app
falls back to a **calibrated synthetic dataset** whose aggregates match the
project's real results, so it still runs and demos correctly anywhere.

Live data uses these real columns (mapped internally — no edits needed):

```
scored_matches.parquet : if_u_score, if_u_flag, dom_family_u, league, season(int), ...
features.parquet       : b365_close_{h,d,a}, ps_close_{h,d,a}, implied_prob_sum_close,
                         closing_spread_*, b365_drift_*, pinnacle_drift_*, *_z
```

`season` ints like `1920` are shown as `19/20`; `if_u_score` (more negative =
more anomalous) becomes the 0–1 display score; per-match contribution bars come
from the `_z` columns (how unusual a match is *for its own league*). The
Overview page shows a banner only when running on synthetic data.

## Layout

```
app.py                  entry: theme + sidebar nav + routing
.streamlit/config.toml  dark theme
lib/
  theme.py              palette + global CSS
  data.py               loader (real parquet OR synthetic fallback)
  components.py         page header, KPI/card/pill helpers
  charts.py             plotly chart builders
views/                  one module per page
data/processed/         drop real parquets here
```

## Notes for finalizing

- Numbers are wired to the project's real results where known (overround, flag
  rates, SHAP families, hypothesis verdicts). Swap in the parquets to make the
  dashboard table show real fixtures.
- This is a **draft** — tabs are meant to be adjusted. Each page is its own
  `views/*.py` module, so edits stay isolated.
