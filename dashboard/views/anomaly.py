import streamlit as st

from lib import charts
from lib import components as C
from lib import theme as T
from lib.data import FLAG_RATE_UNIVERSAL, FLAG_RATE_TIER, load_family_shap


def render(df):
    C.page_header(
        "Anomaly Detection",
        "Teaching a model to flag the odd ones",
        "Isolation Forest on 35 odds features · explained with SHAP.",
    )

    # ---- 1. What makes a match unusual + signals the model watches --------- #
    top_l, top_r = st.columns([1.4, 1])
    with top_l:
        with C.card("What makes a match unusual — odds drift, open → close"):
            st.markdown(
                "<div class='note'>Aris vs PAOK · Greece · 2025-03-02 · "
                "the away price drifted hard late</div>", unsafe_allow_html=True)
            st.plotly_chart(charts.drift_example(), width="stretch",
                            config={"displayModeBar": False})
            C.note("The away odds jumped 2.85 → 3.60 — a big, late move. On its own "
                   "that's nothing; combined with a wide book disagreement, the model "
                   "treats it as a red flag worth a human look.")
    with top_r:
        with C.card("The signals the model watches"):
            st.markdown(
                "**Drift** — how far open → close odds moved  \n"
                "**Spread** — disagreement between bookmakers  \n"
                "**Implied imbalance** — lopsided home/draw/away pricing  \n"
                "**Public–sharp gap** — Bet365 vs Pinnacle divergence  \n"
                "**Reversal proxy** — price moves then snaps back")
            st.markdown(f"<div style='color:{T.BLUE_LIGHT};font-style:italic;"
                        f"margin-top:8px'>35 features in 5 families — no team or "
                        f"player data, by design.</div>", unsafe_allow_html=True)

    # ---- 2. Anomaly score distribution, full width -------------------------- #
    st.write("")
    with C.card("Anomaly score distribution — flag threshold"):
        thr = df["score_raw"].quantile(0.95)
        st.plotly_chart(charts.score_distribution(df["score_raw"], thr),
                        width="stretch", config={"displayModeBar": False})
        C.note("Most matches look normal (blue). The long red tail — the top ~5% "
               "by score — is what gets flagged for a closer look.")

    # ---- 3. Flag rate by league: universal vs tier-aware -------------------- #
    st.write("")
    with C.card("Flag rate by league — universal vs tier-aware model"):
        st.plotly_chart(charts.flag_rate_by_league(FLAG_RATE_UNIVERSAL, FLAG_RATE_TIER),
                        width="stretch", config={"displayModeBar": False},
                        key="flag_rate_chart_1")
        C.note("The universal model (grey) over-flags Greece (10.6%) and under-flags "
               "Turkey (2.0%) — it's comparing every league to the same global bar. "
               "Unusual is not an accusation.")

    st.write("")
    with C.card("Per-league calibration fixes over-flagging"):
        st.plotly_chart(charts.flag_rate_by_league(FLAG_RATE_UNIVERSAL, FLAG_RATE_TIER),
                        width="stretch", config={"displayModeBar": False},
                        key="flag_rate_chart_2")
        C.note("Re-scoring each league against its own history (z-scored per "
               "league-season) pulls every flag rate toward ~5% — Greece drops from "
               "10.6% to 5.5%, Turkey rises from 2.0% to 4.3%. Same idea as "
               "per-merchant calibration in fraud detection: a screen should ask "
               "\u201cis this unusual for this market\u201d, not \u201cis this unusual "
               "overall\u201d.")

    # ---- 4. SHAP, full width ------------------------------------------------ #
    st.write("")
    family_shap, shap_is_synthetic = load_family_shap()
    with C.card("SHAP — what drives the anomaly score (Greece)"):
        st.plotly_chart(charts.shap_drivers(family_shap, league_code="G1"),
                        width="stretch", config={"displayModeBar": False})
        C.note("Signed SHAP, averaged across <b>all</b> Greek matches vs. all "
               "other leagues — not just flagged ones. <b>Drift</b> and "
               "<b>spread</b> together account for most of the gap that makes "
               "a typical Greek match score more anomalous than a typical match "
               "elsewhere; the other three families add texture underneath.")

    # ---- 5. Two models, one A/B test ---------------------------------------- #
    st.write("")
    with C.card("Two models, one A/B test"):
        cc1, cc2 = st.columns(2)
        with cc1:
            st.markdown(
                "**Universal** — one pooled model on natural-unit features. Asks: *is "
                "this match unusual compared to all 8,915?* Concentrates flags in "
                "Greece (10.6%) and barely touches Turkey (2.0%).")
        with cc2:
            st.markdown(
                "**League-aware** — the same model on per-league-season z-scored "
                "features. Asks: *is this match unusual **for its own league**?* Pulls "
                "Greece to 5.5% and nudges Turkey to 4.3% — every league near "
                "baseline.")
        st.markdown(
            "<div class='note'>They agree on 328 matches but each catch 118 the other "
            "misses — different lenses on the same data, which is exactly the point "
            "of the comparison.</div>", unsafe_allow_html=True)

    # ---- 6. No ground-truth labels ------------------------------------------ #
    st.write("")
    st.markdown(
        f"<div class='card' style='border-color:{T.AMBER}'>"
        f"<h3 style='color:{T.AMBER}'>⚖️ No ground-truth labels exist.</h3>"
        f"<div class='muted'>So this reports <b>differential flagging rates</b> — "
        f"never false-positive rates or claims of wrongdoing. A flag means a match's "
        f"odds behaved unlike its league; it is a screening signal, not a verdict. "
        f"The honest output is \u201chere is where a human should look\u201d — the "
        f"same way real integrity monitors operate. <b>Unusual \u2260 rigged.</b>"
        f"</div></div>", unsafe_allow_html=True)
