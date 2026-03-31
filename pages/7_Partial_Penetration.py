"""7_Partial_Penetration.py — Hantush (1961) partial penetration calculator"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import pandas as pd
import streamlit as st
from utils.theis import calc_drawdown, calc_drawdown_partial
from utils.plotting import (render_aquifer_sidebar, render_upload_sidebar,
                             make_loglog_figure, add_theis_trace,
                             add_model_trace, add_data_trace,
                             render_crosssection_diagram)

st.set_page_config(page_title="Partial Penetration", page_icon="🔵", layout="wide")
st.title("🔵 Partial Penetration — Hantush (1961)")
st.markdown("""
Drawdown for a **partially penetrating** pumping well using the full transient
Hantush (1961) solution with W(u, nπr/b).
""")

# ── Sidebar ──────────────────────────────────────────────────────────────────
T, S = render_aquifer_sidebar()

st.sidebar.header("Well & Aquifer")
Q = st.sidebar.number_input("Pumping rate Q (m³/day)", value=500.0, min_value=0.1)
b = st.sidebar.number_input("Aquifer thickness b (m)", value=30.0, min_value=1.0)
l = st.sidebar.number_input("Depth to top of screen l (m)", value=0.0, min_value=0.0)
d = st.sidebar.number_input("Depth to bottom of screen d (m)", value=15.0, min_value=0.1)

st.sidebar.header("Observation Point")
r = st.sidebar.number_input("Distance r (m)", value=50.0, min_value=0.1)
z = st.sidebar.number_input("Observation depth z (m)", value=15.0, min_value=0.0)

df_data = render_upload_sidebar()

# ── Validation ────────────────────────────────────────────────────────────────
errors = []
if d > b:
    errors.append("Bottom of screen d cannot exceed aquifer thickness b.")
if l >= d:
    errors.append("Top of screen l must be less than bottom of screen d.")
if z > b:
    errors.append("Observation depth z cannot exceed aquifer thickness b.")
if errors:
    for e in errors:
        st.error(e)
    st.stop()

if r > 1.5 * b:
    st.warning(
        f"r = {r:.1f} m > 1.5 b = {1.5*b:.1f} m. "
        "Partial penetration correction may be negligible at this distance."
    )

# ── Calculation ───────────────────────────────────────────────────────────────
times = np.logspace(np.log10(1), np.log10(1440), 150)  # fewer points — W(u,β) is slow

with st.spinner("Computing Hantush W(u, β) — this may take a few seconds..."):
    s_partial = calc_drawdown_partial(times, T, S, r, Q, b, l, d, z)
s_theis = calc_drawdown(times, T, S, r, Q)

# ── Layout ────────────────────────────────────────────────────────────────────
col1, col2 = st.columns([2, 1])

with col1:
    fig = make_loglog_figure("Partial Penetration — Hantush (1961)")
    add_theis_trace(fig, times, s_theis,
                    name="Standard Theis (full penetration)", dash="dot", color="#aaa")
    add_model_trace(fig, times, s_partial,
                    name="Hantush W(u, nπr/b) — partial penetration",
                    color="#9467bd")
    add_data_trace(fig, df_data)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    fig_xs = render_crosssection_diagram(b, l, d, z)
    st.plotly_chart(fig_xs, use_container_width=True)

# ── Results table ─────────────────────────────────────────────────────────────
st.subheader("Results at selected times")
t_show = [1, 5, 10, 30, 60, 120, 240, 480, 1440]
with st.spinner("Computing results table..."):
    s_part_show = calc_drawdown_partial(t_show, T, S, r, Q, b, l, d, z)
s_theis_show = calc_drawdown(t_show, T, S, r, Q)

df_res = pd.DataFrame({
    "Time (min)": t_show,
    "Theis s (m)": [f"{s:.4f}" for s in s_theis_show],
    "Hantush s (m)": [f"{s:.4f}" for s in s_part_show],
    "Correction (m)": [f"{sp-st:.4f}" for sp, st in zip(s_part_show, s_theis_show)],
})
st.dataframe(df_res, use_container_width=False, hide_index=True)

st.caption(
    f"T = {T:.3g} m²/day · S = {S:.2e} · b = {b:.1f} m · "
    f"l = {l:.1f} m · d = {d:.1f} m · z = {z:.1f} m · "
    f"r = {r:.1f} m · Q = {Q:.1f} m³/day"
)
