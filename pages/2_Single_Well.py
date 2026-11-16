"""2_Single_Well.py — Standard Theis drawdown calculator"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import streamlit as st
from utils.i18n import tr
from utils.theis import calc_drawdown, TIME_MAX_MIN
from utils.plotting import (render_aquifer_sidebar, render_upload_sidebar,
                             make_loglog_figure, add_theis_trace, add_data_trace,
                             plotly_chart_with_print)

st.set_page_config(page_title=tr("Single Well", "単一井戸"), page_icon="🔵", layout="wide")
st.title(tr("🔵 Single Well — Standard Theis", "🔵 単一井戸 — 標準タイス式"))
st.markdown(tr("Calculates drawdown at a single observation point in a confined aquifer.", "被圧帯水層内の 1 つの観測点における水位低下量を計算します。"))

# ── Sidebar ──────────────────────────────────────────────────────────────────
T, S = render_aquifer_sidebar()

st.sidebar.header(tr("Well & Observation", "井戸と観測点"))
Q = st.sidebar.number_input(tr("Pumping rate Q (m³/day)", "揚水量 Q (m³/日)"), value=500.0, min_value=0.1)
r = st.sidebar.number_input(tr("Distance r (m)", "距離 r (m)"), value=50.0, min_value=0.1)

df_data = render_upload_sidebar()

# ── Calculation ───────────────────────────────────────────────────────────────
times = np.logspace(np.log10(1), np.log10(TIME_MAX_MIN), 300)
drawdown = calc_drawdown(times, T, S, r, Q)

# ── Chart ────────────────────────────────────────────────────────────────────
fig = make_loglog_figure(tr("Theis Drawdown — Single Well", "タイス式による水位低下量 — 単一井戸"))
add_theis_trace(fig, times, drawdown, name=tr("Theis", "タイス式"), dash="solid")
add_data_trace(fig, df_data)
plotly_chart_with_print(fig, filename="single-well", use_container_width=True)

# ── Results table ─────────────────────────────────────────────────────────────
st.subheader(tr("Results at selected times", "指定時間での計算結果"))
import pandas as pd
t_show = [1, 5, 10, 30, 60, 120, 240, 480, 720, 1440, 2880, 3500]
s_show = calc_drawdown(t_show, T, S, r, Q)
df_res = pd.DataFrame({tr("Time (min)", "時間 (min)"): t_show, tr("Drawdown (m)", "水位低下量 (m)"): [f"{s:.4f}" for s in s_show]})
st.dataframe(df_res, use_container_width=False, hide_index=True)

st.caption(f"T = {T:.3g} " + tr("m²/day", "m²/日") + f" · S = {S:.2e} · r = {r:.1f} m · Q = {Q:.1f} " + tr("m³/day", "m³/日"))
