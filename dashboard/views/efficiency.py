import streamlit as st

from lib import charts
from lib import components as C
from lib import theme as T


def render(df):
    C.page_header(
        "Market Efficiency",
        "Is the betting market any good?",
        "8,915 matches · what the odds get right, and where they bend.",
    )

    c1, c2, c3, c4 = st.columns(4)
    C.kpi(c1, "43%", "home-win rate")
    C.kpi(c2, "53.1%", "favourites win")
    C.kpi(c3, "r = 0.99", "predicted vs actual", color=T.GREEN)
    C.kpi(c4, "+1.5pp", "Greece draw gap", color=T.AMBER)

    C.soft_divider()

    hero_l, hero_r = st.columns([1.4, 1])
    with hero_l:
        with C.card("The proof — predicted probability vs what actually happened"):
            st.plotly_chart(charts.calibration_curve(), width="stretch",
                            config={"displayModeBar": False})
    with hero_r:
        st.write("")
        st.markdown("### The dots sit on the line.")
        st.markdown(
            "When the market says **30%**, it happens about **30%** of the time. "
            "Across 8,915 games the correlation between predicted and realised "
            "frequency is near-perfect (**r ≈ 0.99**).\n\n"
            "The crowd is wise: thousands of bettors and a profit-seeking book "
            "converge on probabilities that hold up.")
        st.markdown(f"<div style='color:{T.BLUE_LIGHT};font-style:italic'>"
                    f"Galton's ox, but for football.</div>", unsafe_allow_html=True)

    st.write("")
    r1c1, r1c2 = st.columns(2)
    with r1c1:
        with C.card("Match results — Home / Draw / Away"):
            st.plotly_chart(charts.result_bars((0.435, 0.250, 0.315)),
                            width="stretch", config={"displayModeBar": False})
            C.note("Home advantage is the most reliable pattern in football — "
                   "the market prices it correctly almost everywhere.")
    with r1c2:
        with C.card("Favourite–longshot bias"):
            st.plotly_chart(charts.fav_longshot(), width="stretch",
                            config={"displayModeBar": False})
            C.note("Heavy favourites are slightly **under**-priced and longshots "
                   "**over**-priced — the classic bias, strongest in the mid-tier "
                   "leagues (amber). Elite leagues (blue) sit near fair.")

    st.write("")
    r2c1, r2c2 = st.columns(2)
    with r2c1:
        with C.card("Draws are under-priced (implied vs realised)"):
            st.plotly_chart(charts.draw_mispricing(), width="stretch",
                            config={"displayModeBar": False})
            C.note("Draws happen slightly more often than the odds imply — most in "
                   "**Greece** (+1.5pp) and Bundesliga. EPL is the one correctly-priced "
                   "draw market.")
    with r2c2:
        with C.card("High-street vs professional book (margin)"):
            st.plotly_chart(charts.margin_retail_vs_sharp(), width="stretch",
                            config={"displayModeBar": False})
            C.note("Pinnacle (sharp, amber) runs at roughly **half** Bet365's margin "
                   "(retail, blue). The gap between the two books is itself a signal "
                   "the anomaly model watches.")

    C.soft_divider()
    with C.card("So what?"):
        st.markdown(
            "The market is **broadly efficient** — calibration is near-perfect and the "
            "big patterns (home advantage, favourite strength) are priced correctly. "
            "The interesting story is in the **small, systematic bends**: the draw gap, "
            "the favourite–longshot bias, and the league-to-league differences in "
            "margin and disagreement. Those bends are where the anomaly screen goes "
            "looking.")
