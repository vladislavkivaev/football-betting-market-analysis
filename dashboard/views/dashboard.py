import pandas as pd
import streamlit as st

from lib import charts
from lib import components as C
from lib import theme as T
from lib.data import LEAGUE_NAME, LEAGUE_CODE, SEASONS


def _favourite_band(row):
    """Cheapest outcome's implied prob -> favourite strength band."""
    try:
        lowest = min(row["b365_h"], row["b365_d"], row["b365_a"])
        imp = 1 / lowest
    except Exception:
        return "all"
    return "heavy favourite" if imp >= 0.6 else "even / longshot"


def render(df):
    C.page_header(
        "Match Dashboard",
        "Explore any game in the dataset",
        "Filter the 8,915 matches, then open one to see why the model did or "
        "didn't flag it.",
    )

    rail, main = st.columns([1, 2.5], gap="large")

    # ----------------------------- FILTER RAIL ----------------------------- #
    with rail:
        with C.card("Filters"):
            flagged_only = st.toggle("Flagged only", value=False)
            league_choice = st.selectbox(
                "League", ["All leagues"] + list(LEAGUE_NAME.values()))
            season_choice = st.selectbox("Season", ["All seasons"] + SEASONS)
            result_choice = st.segmented_control(
                "Result", ["All", "H", "D", "A"], default="All")
            fav_choice = st.selectbox(
                "Favourite / longshot",
                ["all", "heavy favourite", "even / longshot"])
            over_band = st.selectbox(
                "Overround band", ["any", "< 5%", "5–6%", "6–7%", "> 7%"])

    # ------------------------------- FILTER -------------------------------- #
    f = df.copy()
    if flagged_only:
        f = f[f["if_u_flag"]]
    if league_choice != "All leagues":
        f = f[f["league"] == LEAGUE_CODE[league_choice]]
    if season_choice != "All seasons":
        f = f[f["season"] == season_choice]
    if result_choice and result_choice != "All":
        f = f[f["full_time_result"] == result_choice]
    if fav_choice != "all":
        f = f[f.apply(lambda r: _favourite_band(r) == fav_choice, axis=1)]
    if over_band != "any":
        ips = f["implied_prob_sum"]
        if over_band == "< 5%":
            f = f[ips < 1.05]
        elif over_band == "5–6%":
            f = f[(ips >= 1.05) & (ips < 1.06)]
        elif over_band == "6–7%":
            f = f[(ips >= 1.06) & (ips < 1.07)]
        else:
            f = f[ips >= 1.07]

    if flagged_only:
        f = f.sort_values("anomaly_score", ascending=False).reset_index(drop=True)
    else:
        f = f.sort_values("match_date", ascending=False).reset_index(drop=True)

    # --------------------------------- TABLE ------------------------------- #
    with main:
        if len(f) == 0:
            with C.card("Matches · 0 shown"):
                st.markdown("<div class='note'>No matches fit those filters — "
                            "loosen one above.</div>", unsafe_allow_html=True)
            return

        view = f.copy()
        view["Match"] = view["home_team"] + " – " + view["away_team"]
        view["Date"] = pd.to_datetime(view["match_date"]).dt.strftime("%Y-%m-%d")
        view["Flag"] = view["if_u_flag"].map({True: "🚩", False: ""})
        view["Score"] = view["anomaly_score"].round(2)
        table = view[["Date", "Match", "league_name", "full_time_result",
                      "Score", "Flag"]].rename(
            columns={"league_name": "League", "full_time_result": "Res"})

        with C.card(f"Matches · {len(f):,} shown"):
            event = st.dataframe(
                table, hide_index=True, width="stretch", height=300,
                on_select="rerun", selection_mode="multi-row",
                column_config={"Score": st.column_config.NumberColumn(format="%.2f")})
            sort_note = ("Sorted by anomaly score (most unusual first)." if flagged_only
                         else "Sorted by date (most recent first).")
            C.note(f"Tap rows to select one or more matches. {sort_note}")

        selected_rows = event.selection.rows if event and event.selection else []
        if not selected_rows:
            selected_rows = [0]  # default to the top match

        key_sig = tuple(sorted(selected_rows))
        if st.session_state.get("_sel_sig") != key_sig:
            st.session_state["_sel_sig"] = key_sig
            st.session_state["_step"] = 0
        step = st.session_state.get("_step", 0) % len(selected_rows)
        row = view.iloc[selected_rows[step]]

        # ----------------------------- DETAIL ------------------------------ #
        st.write("")
        with C.card():
            title = f"{row['home_team']} vs {row['away_team']} · " \
                    f"{row['league_name']} · {row['Date']}"
            nav_l, nav_r = st.columns([3, 1])
            nav_l.markdown(f"**Selected match — {title}**")
            if len(selected_rows) > 1:
                if nav_r.button(f"Next ›  ({step + 1}/{len(selected_rows)})",
                                width="stretch"):
                    st.session_state["_step"] = step + 1
                    st.rerun()

            st.write("")
            d1, d2, d3, d4 = st.columns(4)
            flagged = bool(row["if_u_flag"])
            badge = (C.pill("🚩 FLAGGED", "red") if flagged
                     else C.pill("✓ not flagged", "green"))
            d1.markdown(badge, unsafe_allow_html=True)
            res_map = {"H": "Home win", "D": "Draw", "A": "Away win"}
            d2.markdown(
                f"<div class='note' style='font-size:0.8rem'>RESULT</div>"
                f"<div style='font-weight:700;font-size:1.1rem'>"
                f"{res_map[row['full_time_result']]} "
                f"({row['home_goals']}–{row['away_goals']})</div>",
                unsafe_allow_html=True)
            d3.markdown(
                f"<div class='note' style='font-size:0.8rem'>MODEL SCORE</div>"
                f"<div style='font-weight:800;font-size:1.1rem;color:{T.BLUE}'>"
                f"{row['anomaly_score']:.2f}</div>", unsafe_allow_html=True)
            d4.markdown(
                f"<div class='note' style='font-size:0.8rem'>ODDS H/D/A</div>"
                f"<div style='font-weight:700;font-size:1.1rem'>"
                f"{row['b365_h']:.2f} / {row['b365_d']:.2f} / "
                f"{row['b365_a']:.2f}</div>", unsafe_allow_html=True)

            st.markdown("<hr class='soft' style='margin:16px 0'>",
                        unsafe_allow_html=True)
            st.markdown(
                "<div class='note'>Why the model scored it this way — "
                "feature contributions</div>", unsafe_allow_html=True)
            contribs = {
                "Spread (book disagreement)": float(row["contrib_spread"]),
                "Drift (price moved late)": float(row["contrib_drift"]),
                "Implied imbalance": float(row["contrib_implied"]),
            }
            st.plotly_chart(charts.feature_contrib_bars(contribs),
                            width="stretch", config={"displayModeBar": False})

            dom = row.get("dom_family_u", "spread")
            if flagged:
                C.note(f"Dominant signal: **{dom}**. The odds for this game behaved "
                       f"unlike others in {row['league_name']} — that's why it "
                       f"surfaced. A screen, not a verdict.")
            else:
                C.note("This match scored below the flag threshold — its odds behaved "
                       "normally for its league.")

    # ----------------------------- FOOTER ---------------------------------- #
    st.write("")
    st.markdown(
        f"<div class='card'><h3>How to read this · scope &amp; limitations</h3>"
        f"<div class='muted'>"
        f"• A flag means a match's odds behave unlike its league — it is a screening "
        f"signal.<br>"
        f"• There are no ground-truth fixing labels, so this reports differential "
        f"flagging rates, never false-positive rates.<br>"
        f"• \u201cUnusual \u2260 rigged.\u201d The honest output is \u201chere is "
        f"where a human should look\u201d — the same way real models "
        f"operate.</div></div>", unsafe_allow_html=True)
