import streamlit as st

from lib import components as C
from lib import theme as T


def render(df):
    C.page_header(
        "Overview",
        "Football Betting Integrity Monitor",
        "A market-efficiency study with anomaly screening — seven seasons of football odds.",
    )

    c1, c2, c3 = st.columns(3)
    C.kpi(c1, "8,915", "matches analysed")
    C.kpi(c2, "4", "leagues · Bundesliga · EPL · Turkey · Greece")
    C.kpi(c3, "7", "seasons · 2019/20 – 2025/26")

    st.write("")
    st.markdown(
        "**Source:** football-data.co.uk — real Bet365 &amp; Pinnacle odds "
        "(opening + closing).", unsafe_allow_html=True)

    C.soft_divider()

    st.markdown('<div class="eyebrow">Pipeline</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="pipe">'
        '<span class="step">Raw CSVs</span><span class="arrow">›</span>'
        '<span class="step">pandas</span><span class="arrow">›</span>'
        '<span class="step">PostgreSQL</span><span class="arrow">›</span>'
        '<span class="step">dbt</span><span class="arrow">›</span>'
        '<span class="step">Model + App</span>'
        '</div>', unsafe_allow_html=True)

    st.write("")
    st.markdown(
        "**Methods:** EDA → 35 engineered features → Isolation Forest → "
        "SHAP → hypothesis testing")
    st.markdown(
        '<span class="chip">8,915 rows scored</span>'
        '<span class="chip">Streamlit + Tableau</span>'
        '<span class="chip">dbt · 9 passing tests</span>',
        unsafe_allow_html=True)

    C.soft_divider()

    left, right = st.columns([1.15, 1])
    with left:
        with C.card("What this is — and what it is not"):
            st.markdown(
                "This project studies how an efficient market with a built-in fee "
                "behaves, and screens for matches whose odds behave **unlike their "
                "league**. It is framed as a *market-efficiency study with anomaly "
                "screening*, not a match-fixing detector.\n\n"
                "There are no ground-truth fixing labels, so the honest output is a "
                "**differential flagging rate** — never a false-positive rate or an "
                "accusation. The same way professional integrity monitors operate: "
                "*unusual ≠ rigged.*")
    with right:
        with C.card("The four hypotheses"):
            st.markdown(
                "<div class='note'>Written down before testing, so nothing is "
                "cherry-picked after the fact.</div>", unsafe_allow_html=True)
            st.markdown(
                "**H1** · Smaller leagues priced less efficiently than big ones  \n"
                "**H2** · Draws mispriced (Greece under, EPL correct)  \n"
                "**H3** · Anomalies detectable; league-aware tuning rebalances flags  \n"
                "**H4** · Bookmaker disagreement spikes at season's end")

    if df["_synthetic"].iloc[0]:
        st.write("")
        st.info(
            "Running on a **calibrated demo dataset** (real files not detected). "
            "Aggregate figures — flag rates, overround, spreads, drift — match the "
            "project's real results. Drop `scored_matches.parquet` and "
            "`features.parquet` into `data/processed/` to switch to live data.",
            icon="🧪")
