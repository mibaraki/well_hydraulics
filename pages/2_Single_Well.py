"""2_Single_Well.py — Standard Theis drawdown calculator"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import streamlit as st
from utils.theis import calc_drawdown
from utils.plotting import (render_aquifer_sidebar, render_upload_sidebar,
                             make_loglog_figure, add_theis_trace, add_data_trace)

st.set_page_config(page_title="Single Well", page_icon="🔵", layout="wide")
st.title("🔵 Single Well — Standard Theis")
st.markdown("Calculates drawdown at a single observation point in a confined aquifer.")

# ── Sidebar ──────────────────────────────────────────────────────────────────
T, S = render_aquifer_sidebar()

st.sidebar.header("Well & Observation")
Q = st.sidebar.number_input("Pumping rate Q (m³/day)", value=500.0, min_value=0.1)
r = st.sidebar.number_input("Distance r (m)", value=50.0, min_value=0.1)

df_data = render_upload_sidebar()

# ── Calculation ───────────────────────────────────────────────────────────────
times = np.logspace(np.log10(1), np.log10(1440), 300)
drawdown = calc_drawdown(times, T, S, r, Q)

# ── Chart ────────────────────────────────────────────────────────────────────
fig = make_loglog_figure("Theis Drawdown — Single Well")
add_theis_trace(fig, times, drawdown, name="Theis", dash="solid")
add_data_trace(fig, df_data)
st.plotly_chart(fig, use_container_width=True)

# ── Results table ─────────────────────────────────────────────────────────────
st.subheader("Results at selected times")
import pandas as pd
t_show = [1, 5, 10, 30, 60, 120, 240, 480, 720, 1440]
s_show = calc_drawdown(t_show, T, S, r, Q)
df_res = pd.DataFrame({"Time (min)": t_show, "Drawdown (m)": [f"{s:.4f}" for s in s_show]})
st.dataframe(df_res, use_container_width=False, hide_index=True)

st.caption(f"T = {T:.3g} m²/day · S = {S:.2e} · r = {r:.1f} m · Q = {Q:.1f} m³/day")
