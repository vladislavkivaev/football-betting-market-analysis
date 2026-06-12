"""
Match Explorer — pick any game, see everything about it.
Drop this in your Streamlit app (e.g. as a page, or import explorer() into your nav).

It auto-detects column names from scored_matches.parquet. If a guess is wrong,
fix it once in COLS below — nothing else needs to change.

    streamlit run match_explorer.py
"""

from pathlib import Path
import pandas as pd
import streamlit as st

# --------------------------------------------------------------------------- #
# 0. Where the data lives + column mapping
# --------------------------------------------------------------------------- #
DATA = Path(__file__).resolve().parent.parent / "data" / "processed" / "scored_matches.parquet"

# Map logical fields -> a list of candidate column names (first match wins).
# Adjust any of these to your real column names if auto-detect picks wrong.
CANDIDATES = {
    "date":     ["Date", "date", "match_date"],
    "league":   ["league", "League", "Div", "division"],
    "season":   ["season", "Season"],
    "home":     ["HomeTeam", "home_team", "Home", "home"],
    "away":     ["AwayTeam", "away_team", "Away", "away"],
    "result":   ["FTR", "result", "Result", "ftr"],
    # closing odds (Bet365)
    "odds_h":   ["B365CH", "B365H", "odds_home_close", "AvgCH", "home_close"],
    "odds_d":   ["B365CD", "B365D", "odds_draw_close", "AvgCD", "draw_close"],
    "odds_a":   ["B365CA", "B365A", "odds_away_close", "AvgCA", "away_close"],
    # anomaly outputs
    "score":    ["if_t_score", "if_u_score", "anomaly_score", "score"],
    "flag":     ["is_flagged", "flagged", "if_t_flag", "if_u_flag", "anomaly_flag"],
}


@st.cache_data
def load():
    df = pd.read_parquet(DATA)
    cols, missing = {}, []
    for key, opts in CANDIDATES.items():
        hit = next((c for c in opts if c in df.columns), None)
        cols[key] = hit
        if hit is None:
            missing.append(key)
    return df, cols, missing


def implied(o):
    try:
        return 1.0 / float(o)
    except (TypeError, ZeroDivisionError, ValueError):
        return None


def explorer():
    st.header("🔎 Match Explorer")
    st.caption("Pick any game in the dataset and see everything about it — result, odds, "
               "implied probabilities, and whether the model flagged it.")

    if not DATA.exists():
        st.error(f"Couldn't find {DATA}. Point DATA at your scored_matches.parquet.")
        return

    df, C, missing = load()
    if missing:
        st.warning(f"Couldn't auto-detect: {', '.join(missing)}. "
                   "Set the right column name(s) in CANDIDATES at the top of the file.")

    # ---------------- Sidebar filters ----------------
    with st.sidebar:
        st.subheader("Filters")
        flagged_only = False
        if C["flag"]:
            flagged_only = st.toggle("🚩 Flagged games only", value=False)
        leagues = sorted(df[C["league"]].dropna().unique()) if C["league"] else []
        pick_league = st.multiselect("League", leagues, default=leagues) if leagues else None
        seasons = sorted(df[C["season"]].dropna().unique()) if C["season"] else []
        pick_season = st.multiselect("Season", seasons, default=seasons) if seasons else None
        pick_result = None
        if C["result"]:
            pick_result = st.multiselect("Result", ["H", "D", "A"], default=["H", "D", "A"])
        search = st.text_input("Search team")

    # ---------------- Apply filters ----------------
    view = df.copy()
    if flagged_only and C["flag"]:
        view = view[view[C["flag"]].astype(bool)]
    if pick_league is not None:
        view = view[view[C["league"]].isin(pick_league)]
    if pick_season is not None:
        view = view[view[C["season"]].isin(pick_season)]
    if pick_result and C["result"]:
        view = view[view[C["result"]].isin(pick_result)]
    if search and (C["home"] or C["away"]):
        mask = pd.Series(False, index=view.index)
        if C["home"]:
            mask |= view[C["home"]].astype(str).str.contains(search, case=False, na=False)
        if C["away"]:
            mask |= view[C["away"]].astype(str).str.contains(search, case=False, na=False)
        view = view[mask]

    # ---------------- Summary line ----------------
    total = len(df)
    n = len(view)
    n_flag = int(df[C["flag"]].astype(bool).sum()) if C["flag"] else 0
    c1, c2, c3 = st.columns(3)
    c1.metric("Matches shown", f"{n:,}")
    c2.metric("In full dataset", f"{total:,}")
    if C["flag"]:
        c3.metric("Flagged (all data)", f"{n_flag:,}  ({n_flag/total:.1%})")

    if n == 0:
        st.info("No matches with these filters. Loosen them in the sidebar.")
        return

    # ---------------- The table (build display columns that exist) ----------------
    show_map = [("date", "Date"), ("league", "League"), ("season", "Season"),
                ("home", "Home"), ("away", "Away"), ("result", "Result"),
                ("odds_h", "Odds H"), ("odds_d", "Odds D"), ("odds_a", "Odds A"),
                ("score", "Anomaly score"), ("flag", "Flagged")]
    display_cols, rename = [], {}
    for key, label in show_map:
        if C[key]:
            display_cols.append(C[key])
            rename[C[key]] = label
    table = view[display_cols].rename(columns=rename).reset_index(drop=True)
    if "Flagged" in table:
        table["Flagged"] = table["Flagged"].map(lambda v: "🚩" if bool(v) else "")

    st.markdown("##### Select a match")
    selection = st.dataframe(
        table, use_container_width=True, hide_index=True, height=340,
        on_select="rerun", selection_mode="single-row",
    )

    rows = selection.selection.get("rows", []) if hasattr(selection, "selection") else []
    if not rows:
        st.info("👆 Click a row to see the full match breakdown.")
        return

    # ---------------- Detail panel for the selected match ----------------
    row = view.iloc[rows[0]]
    g = lambda k: row[C[k]] if C[k] else None

    home, away = g("home") or "Home", g("away") or "Away"
    st.divider()
    head = f"{home}  vs  {away}"
    if C["league"] or C["season"] or C["date"]:
        bits = [str(x) for x in (g("league"), g("season"), g("date")) if x is not None]
        head += "   ·   " + "  ·  ".join(bits)
    st.subheader(head)

    # flag badge
    if C["flag"]:
        if bool(g("flag")):
            st.error("🚩 **Flagged as unusual** — this match's odds behave unlike the rest "
                     "of its league. *Unusual ≠ rigged: a signal worth a closer look, not a verdict.*")
        else:
            st.success("✅ **Not flagged** — this match's odds look normal for its league.")

    left, right = st.columns(2)
    with left:
        st.markdown("**Result**")
        res = g("result")
        res_txt = {"H": f"Home win — {home}", "D": "Draw", "A": f"Away win — {away}"}.get(res, res)
        st.markdown(f"### {res_txt}")
        if C["score"] and g("score") is not None:
            st.metric("Anomaly score", f"{float(g('score')):.3f}")

    with right:
        st.markdown("**Closing odds & implied probability**")
        oh, od, oa = g("odds_h"), g("odds_d"), g("odds_a")
        ph, pd_, pa = implied(oh), implied(od), implied(oa)
        odds_tbl = {
            "Outcome": [f"Home ({home})", "Draw", f"Away ({away})"],
            "Odds": [oh, od, oa],
            "Implied %": [f"{p:.1%}" if p else "—" for p in (ph, pd_, pa)],
        }
        st.table(odds_tbl)
        if all(p is not None for p in (ph, pd_, pa)):
            over = (ph + pd_ + pa - 1) * 100
            st.caption(f"Bookmaker margin (overround): **{over:.1f}%** "
                       f"— the three chances sum to {ph + pd_ + pa:.1%}, not 100%.")


if __name__ == "__main__":
    st.set_page_config(page_title="Match Explorer", page_icon="🔎", layout="wide")
    explorer()