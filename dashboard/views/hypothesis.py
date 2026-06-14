import streamlit as st

from lib import charts
from lib import components as C
from lib import theme as T

ROWS = [
    ("H1", "Smaller leagues priced less efficiently than big ones",
     "Pre-registered", "Not supported", "red"),
    ("H2", "Draws mispriced (Greece under, EPL correct)",
     "EDA-informed", "Mixed", "amber"),
    ("H3", "Anomalies detectable; league-aware tuning rebalances flags",
     "Pre-registered", "Supported", "green"),
    ("H4", "Bookmaker disagreement spikes at season's end",
     "Pre-registered", "Rejected", "red"),
]


def render(df):
    C.page_header(
        "Hypothesis Testing",
        "Four predictions, written down first",
        "Two held, two didn't — and reporting that honestly is the point.",
    )

    with C.card():
        head = st.columns([0.5, 4.2, 1.6, 1.6])
        for col, txt in zip(head, ["#", "What we predicted", "Type", "Result"]):
            col.markdown(f"<div class='note' style='font-size:0.8rem;letter-spacing:"
                         f"0.1em;text-transform:uppercase'>{txt}</div>",
                         unsafe_allow_html=True)
        st.markdown("<hr class='soft' style='margin:10px 0'>", unsafe_allow_html=True)
        for h, pred, typ, verdict, kind in ROWS:
            c0, c1, c2, c3 = st.columns([0.5, 4.2, 1.6, 1.6])
            c0.markdown(f"**{h}**")
            c1.markdown(pred)
            c2.markdown(f"<span class='note'>{typ}</span>", unsafe_allow_html=True)
            c3.markdown(C.pill(verdict, kind), unsafe_allow_html=True)
            st.write("")

    st.write("")
    a, b = st.columns([1, 1.1])
    with a:
        with C.card("H3 — the one clean win (Greece flag rate)"):
            st.plotly_chart(charts.h3_winbar(), width="stretch",
                            config={"displayModeBar": False})
            C.note("Grading each league against itself (per-league-season z-scoring) "
                   "roughly **halves** Greece's flag rate — 10.6% → 5.5% — pulling "
                   "every league back toward the 5% baseline. That's the "
                   "pre-registered criterion met.")
    with b:
        with C.card("Why two nulls still matter"):
            st.markdown(
                "Pre-registering H1–H4 *before* testing means the results can't be "
                "cherry-picked. H1 and H4 failing is **evidence the method is "
                "honest** — not tuned after the fact to tell a tidy story.\n\n"
                "**H1** turned out to be a *league*-level effect, not a tier one: "
                "Turkey is the overround outlier, Greece the spread outlier — they "
                "don't move together as a 'mid-tier block'.\n\n"
                "**H4** was rejected outright: disagreement is *lowest* at season's "
                "end, not highest.")
            st.markdown(f"<div style='color:{T.BLUE_LIGHT};font-style:italic'>"
                        f"H4′ (exploratory): Greece is the noisiest market in every "
                        f"quarter — a persistent league effect, not a seasonal "
                        f"one.</div>", unsafe_allow_html=True)

    C.soft_divider()
    with st.expander("Effect sizes & test details (the honest reading)"):
        st.markdown(
            "- **H1** — pooled KS significant on 4/4 efficiency features (p ≈ 0), but "
            "*within*-tier pairs are also significant, so the tier framing fails. "
            "Overround ordering: T1 1.068 > G1 1.062 > D1 1.056 > E0 1.055.\n"
            "- **H2** — mean draw gaps are real and substantive (D1 +6.7%, G1 +6.0%, "
            "EPL −0.8%) and EPL-correctly-priced is confirmed, but with only n=7 "
            "league-seasons the Holm-corrected MWU doesn't clear significance — hence "
            "*mixed*. D1 is significant vs zero (p=0.020, |r|=0.71).\n"
            "- **H3** — flag-rate gap reduction exceeds the >half threshold; flagged "
            "vs unflagged separate strongly on spread (max closing spread KS D=0.896, "
            "|r|=0.978).\n"
            "- **H4** — ANOVA technically significant (n-artefact, η²<0.01) but "
            "Kruskal-Wallis not; both effect sizes negligible. Rejected as framed.")
