"""7_Partial_Penetration.py — Hantush (1961) partial penetration calculator"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import pandas as pd
import streamlit as st
from utils.i18n import tr
from utils.theis import calc_drawdown, calc_drawdown_partial, TIME_MAX_MIN
from utils.plotting import (render_aquifer_sidebar, render_upload_sidebar,
                             make_loglog_figure, add_theis_trace,
                             add_model_trace, add_data_trace,
                             render_crosssection_diagram, plotly_chart_with_print)

st.set_page_config(page_title=tr("Partial Penetration", "部分貫入井"), page_icon="🔵", layout="wide")

from utils.license import require_license
require_license()   # Pro page: needs a valid license key
st.title(tr("🔵 Partial Penetration — Hantush (1961)", "🔵 部分貫入井 — Hantush (1961)"))
st.markdown(tr("""
Drawdown for a **partially penetrating** pumping well using the full transient
Hantush (1961) solution with W(u, nπr/b).
""", """
**部分貫入井**の水位低下量を、W(u, nπr/b) を用いた Hantush (1961) の完全な非定常解で計算します。
"""))

# ── Sidebar ──────────────────────────────────────────────────────────────────
T, S = render_aquifer_sidebar()

st.sidebar.header(tr("Well & Aquifer", "井戸と帯水層"))
Q = st.sidebar.number_input(tr("Pumping rate Q (m³/day)", "揚水量 Q (m³/日)"), value=500.0, min_value=0.1)
b = st.sidebar.number_input(tr("Aquifer thickness b (m)", "帯水層の厚さ b (m)"), value=30.0, min_value=1.0)
l = st.sidebar.number_input(tr("Depth to top of screen l (m)", "ストレーナー上端の深さ l (m)"), value=0.0, min_value=0.0)
d = st.sidebar.number_input(tr("Depth to bottom of screen d (m)", "ストレーナー下端の深さ d (m)"), value=15.0, min_value=0.1)

st.sidebar.header(tr("Observation Point", "観測点"))
r = st.sidebar.number_input(tr("Distance r (m)", "距離 r (m)"), value=50.0, min_value=0.1)
z = st.sidebar.number_input(tr("Observation depth z (m)", "観測深度 z (m)"), value=5.0, min_value=0.0)

df_data = render_upload_sidebar()

# ── Validation ────────────────────────────────────────────────────────────────
errors = []
if d > b:
    errors.append(tr("Bottom of screen d cannot exceed aquifer thickness b.", "ストレーナー下端 d は帯水層の厚さ b を超えられません。"))
if l >= d:
    errors.append(tr("Top of screen l must be less than bottom of screen d.", "ストレーナー上端 l は下端 d より小さくなければなりません。"))
if z > b:
    errors.append(tr("Observation depth z cannot exceed aquifer thickness b.", "観測深度 z は帯水層の厚さ b を超えられません。"))
if errors:
    for e in errors:
        st.error(e)
    st.stop()

if r > 1.5 * b:
    st.warning(tr(
        f"r = {r:.1f} m > 1.5 b = {1.5*b:.1f} m. "
        "Partial penetration correction may be negligible at this distance.",
        f"r = {r:.1f} m > 1.5 b = {1.5*b:.1f} m です。"
        "この距離では、部分貫入の補正はほとんど無視できる可能性があります。"
    ))

# ── Calculation ───────────────────────────────────────────────────────────────
times = np.logspace(np.log10(1), np.log10(TIME_MAX_MIN), 150)  # fewer points — W(u,β) is slow

with st.spinner(tr("Computing Hantush W(u, β) — this may take a few seconds...", "Hantush W(u, β) を計算中です。数秒かかることがあります...")):
    s_partial = calc_drawdown_partial(times, T, S, r, Q, b, l, d, z)
s_theis = calc_drawdown(times, T, S, r, Q)

# ── Layout ────────────────────────────────────────────────────────────────────
col1, col2 = st.columns([2, 1])

with col1:
    fig = make_loglog_figure(tr("Partial Penetration — Hantush (1961)", "部分貫入井 — Hantush (1961)"))
    add_theis_trace(fig, times, s_theis,
                    name=tr("Standard Theis (full penetration)", "標準タイス式（完全貫入）"), dash="dot", color="#aaa")
    add_model_trace(fig, times, s_partial,
                    name=tr("Hantush W(u, nπr/b) — partial penetration", "Hantush W(u, nπr/b) — 部分貫入"),
                    color="#9467bd")
    add_data_trace(fig, df_data)
    plotly_chart_with_print(fig, filename='partial-penetration', use_container_width=True)

with col2:
    fig_xs = render_crosssection_diagram(b, l, d, z)
    plotly_chart_with_print(fig_xs, filename='cross-section', use_container_width=True)

# ── Results table ─────────────────────────────────────────────────────────────
st.subheader(tr("Results at selected times", "指定時間での計算結果"))
t_show = [1, 5, 10, 30, 60, 120, 240, 480, 1440, 2880, 3500]
with st.spinner(tr("Computing results table...", "結果の表を計算中です...")):
    s_part_show = calc_drawdown_partial(t_show, T, S, r, Q, b, l, d, z)
s_theis_show = calc_drawdown(t_show, T, S, r, Q)

df_res = pd.DataFrame({
    tr("Time (min)", "時間 (min)"): t_show,
    tr("Theis s (m)", "タイス s (m)"): [f"{s:.4f}" for s in s_theis_show],
    tr("Hantush s (m)", "Hantush s (m)"): [f"{s:.4f}" for s in s_part_show],
    tr("Correction (m)", "補正量 (m)"): [f"{sp-st:.4f}" for sp, st in zip(s_part_show, s_theis_show)],
})
st.dataframe(df_res, use_container_width=False, hide_index=True)

st.caption(
    f"T = {T:.3g} " + tr("m²/day", "m²/日") + f" · S = {S:.2e} · b = {b:.1f} m · "
    f"l = {l:.1f} m · d = {d:.1f} m · z = {z:.1f} m · "
    f"r = {r:.1f} m · Q = {Q:.1f} " + tr("m³/day", "m³/日")
)
