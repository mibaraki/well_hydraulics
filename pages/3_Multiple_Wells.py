"""3_Multiple_Wells.py — Superposition of multiple pumping wells"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from utils.i18n import tr
from utils.theis import calc_drawdown, TIME_MAX_MIN
from utils.plotting import (render_aquifer_sidebar, render_upload_sidebar,
                             make_loglog_figure, add_data_trace,
                             plotly_chart_with_print, COLORS, LAYOUT_BASE)

st.set_page_config(page_title=tr("Multiple Wells", "複数井戸"), page_icon="🔵", layout="wide")

from utils.license import require_license
require_license()   # Pro page: needs a valid license key
st.title(tr("🔵 Multiple Wells — Superposition", "🔵 複数井戸 — 重ね合わせ"))
st.markdown(tr(
    "Total drawdown at one observation point from multiple pumping wells, "
    "calculated by superposition: s_total = Σ s_i",
    "複数の揚水井による 1 つの観測点での合計水位低下量を、重ね合わせ (s_total = Σ s_i) で計算します。"
))

# ── Sidebar ──────────────────────────────────────────────────────────────────
T, S = render_aquifer_sidebar()

st.sidebar.header(tr("Wells", "井戸"))
n_wells = st.sidebar.number_input(tr("Number of wells", "井戸の数"), min_value=1, max_value=10, value=2)

well_params = []
palette = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
           "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"]

for i in range(n_wells):
    with st.sidebar.expander(tr(f"Well {i+1}", f"井戸 {i+1}"), expanded=(i == 0)):
        r_i = st.number_input(tr("Distance r (m)", "距離 r (m)"), value=50.0 + i * 30,
                              min_value=0.1, key=f"r_{i}")
        Q_i = st.number_input(tr("Pumping rate Q (m³/day)", "揚水量 Q (m³/日)"), value=300.0,
                              min_value=0.1, key=f"Q_{i}")
        well_params.append((r_i, Q_i))

df_data = render_upload_sidebar()

# ── Calculation ───────────────────────────────────────────────────────────────
times = np.logspace(np.log10(1), np.log10(TIME_MAX_MIN), 300)

individual = []
total = np.zeros(len(times))
for r_i, Q_i in well_params:
    s_i = calc_drawdown(times, T, S, r_i, Q_i)
    individual.append(s_i)
    total += s_i

# ── Chart ────────────────────────────────────────────────────────────────────
fig = make_loglog_figure(tr("Theis Drawdown — Superposition", "タイス式による水位低下量 — 重ね合わせ"))

for i, s_i in enumerate(individual):
    r_i, Q_i = well_params[i]
    fig.add_trace(go.Scatter(
        x=times, y=s_i, mode="lines",
        name=tr(f"Well {i+1} (r={r_i:.0f}m, Q={Q_i:.0f})", f"井戸 {i+1} (r={r_i:.0f}m, Q={Q_i:.0f})"),
        line=dict(color=palette[i % len(palette)], width=1.5, dash="dot")
    ))

fig.add_trace(go.Scatter(
    x=times, y=total, mode="lines",
    name=tr("Total drawdown", "合計水位低下量"),
    line=dict(color="#111", width=2.5)
))

add_data_trace(fig, df_data)
plotly_chart_with_print(fig, filename='multiple-wells', use_container_width=True)

# ── Results table ─────────────────────────────────────────────────────────────
st.subheader(tr("Total drawdown at selected times", "指定時間での合計水位低下量"))
t_show = [1, 10, 30, 60, 120, 240, 480, 1440, 2880, 3500]
total_show = np.zeros(len(t_show))
for r_i, Q_i in well_params:
    total_show += np.array(calc_drawdown(t_show, T, S, r_i, Q_i))

df_res = pd.DataFrame({tr("Time (min)", "時間 (min)"): t_show,
                        tr("Total drawdown (m)", "合計水位低下量 (m)"): [f"{s:.4f}" for s in total_show]})
st.dataframe(df_res, use_container_width=False, hide_index=True)

st.caption(f"T = {T:.3g} " + tr("m²/day", "m²/日") + f" · S = {S:.2e} · " + tr(f"{n_wells} well(s)", f"井戸 {n_wells} 本"))
