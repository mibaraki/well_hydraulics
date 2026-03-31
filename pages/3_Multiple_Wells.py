"""3_Multiple_Wells.py — Superposition of multiple pumping wells"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from utils.theis import calc_drawdown
from utils.plotting import (render_aquifer_sidebar, render_upload_sidebar,
                             make_loglog_figure, add_data_trace, COLORS, LAYOUT_BASE)

st.set_page_config(page_title="Multiple Wells", page_icon="🔵", layout="wide")
st.title("🔵 Multiple Wells — Superposition")
st.markdown(
    "Total drawdown at one observation point from multiple pumping wells, "
    "calculated by superposition: s_total = Σ s_i"
)

# ── Sidebar ──────────────────────────────────────────────────────────────────
T, S = render_aquifer_sidebar()

st.sidebar.header("Wells")
n_wells = st.sidebar.number_input("Number of wells", min_value=1, max_value=10, value=2)

well_params = []
palette = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
           "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"]

for i in range(n_wells):
    with st.sidebar.expander(f"Well {i+1}", expanded=(i == 0)):
        r_i = st.number_input(f"Distance r (m)", value=50.0 + i * 30,
                              min_value=0.1, key=f"r_{i}")
        Q_i = st.number_input(f"Pumping rate Q (m³/day)", value=300.0,
                              min_value=0.1, key=f"Q_{i}")
        well_params.append((r_i, Q_i))

df_data = render_upload_sidebar()

# ── Calculation ───────────────────────────────────────────────────────────────
times = np.logspace(np.log10(1), np.log10(1440), 300)

individual = []
total = np.zeros(len(times))
for r_i, Q_i in well_params:
    s_i = calc_drawdown(times, T, S, r_i, Q_i)
    individual.append(s_i)
    total += s_i

# ── Chart ────────────────────────────────────────────────────────────────────
fig = make_loglog_figure("Theis Drawdown — Superposition")

for i, s_i in enumerate(individual):
    r_i, Q_i = well_params[i]
    fig.add_trace(go.Scatter(
        x=times, y=s_i, mode="lines",
        name=f"Well {i+1} (r={r_i:.0f}m, Q={Q_i:.0f})",
        line=dict(color=palette[i % len(palette)], width=1.5, dash="dot")
    ))

fig.add_trace(go.Scatter(
    x=times, y=total, mode="lines",
    name="Total drawdown",
    line=dict(color="#111", width=2.5)
))

add_data_trace(fig, df_data)
st.plotly_chart(fig, use_container_width=True)

# ── Results table ─────────────────────────────────────────────────────────────
st.subheader("Total drawdown at selected times")
t_show = [1, 10, 30, 60, 120, 240, 480, 1440]
total_show = np.zeros(len(t_show))
for r_i, Q_i in well_params:
    total_show += np.array(calc_drawdown(t_show, T, S, r_i, Q_i))

df_res = pd.DataFrame({"Time (min)": t_show,
                        "Total drawdown (m)": [f"{s:.4f}" for s in total_show]})
st.dataframe(df_res, use_container_width=False, hide_index=True)

st.caption(f"T = {T:.3g} m²/day · S = {S:.2e} · {n_wells} well(s)")
