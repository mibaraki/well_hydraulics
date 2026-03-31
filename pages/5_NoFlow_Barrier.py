"""5_NoFlow_Barrier.py — No-flow barrier (thinning aquifer) using method of images"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import streamlit as st
from utils.theis import calc_drawdown, calc_drawdown_barrier
from utils.plotting import (render_aquifer_sidebar, render_upload_sidebar,
                             make_loglog_figure, add_theis_trace,
                             add_model_trace, add_data_trace,
                             render_geometry_diagram)

st.set_page_config(page_title="No-Flow Barrier", page_icon="🔵", layout="wide")
st.title("🔵 No-Flow Barrier — Thinning Aquifer")
st.markdown("""
An impermeable fault, aquifer pinchout, or valley wall acts as a **no-flow boundary**.
The method of images places a **pumping well** (+Q) mirrored across the barrier.
Drawdown is **greater** than standard Theis at late time — no recharge from the barrier side.
""")

# ── Sidebar ──────────────────────────────────────────────────────────────────
T, S = render_aquifer_sidebar()

st.sidebar.header("Well & Boundary")
Q = st.sidebar.number_input("Pumping rate Q (m³/day)", value=500.0, min_value=0.1)
a = st.sidebar.number_input("Distance to barrier a (m)", value=100.0, min_value=1.0)

st.sidebar.header("Observation Point")
r = st.sidebar.number_input("Distance from pump r (m)", value=50.0, min_value=0.1)
theta = st.sidebar.slider("Angle θ (degrees)", 0.0, 360.0, 90.0, step=1.0)

df_data = render_upload_sidebar()

# ── Validity check ────────────────────────────────────────────────────────────
s_test, r_image, x_obs, y_obs = calc_drawdown_barrier([60], T, S, r, theta, a, Q)
if x_obs >= a:
    st.error(
        f"⚠️ Observation point (x = {x_obs:.1f} m) is beyond or on the barrier "
        f"(x = {a:.1f} m). Method of images is not valid here."
    )
    st.stop()

# ── Calculation ───────────────────────────────────────────────────────────────
times = np.logspace(np.log10(1), np.log10(1440), 300)
s_barrier, r_image, x_obs, y_obs = calc_drawdown_barrier(times, T, S, r, theta, a, Q)
s_theis = calc_drawdown(times, T, S, r, Q)

# ── Layout ────────────────────────────────────────────────────────────────────
col1, col2 = st.columns([2, 1])

with col1:
    fig = make_loglog_figure("No-Flow Barrier — Method of Images")
    add_theis_trace(fig, times, s_theis, name="Standard Theis (no boundary)",
                    dash="dot", color="#aaa")
    add_model_trace(fig, times, s_barrier, name="No-flow barrier (+Q image)",
                    color="#d62728")
    add_data_trace(fig, df_data)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    fig_geo = render_geometry_diagram(
        r, theta, a, x_obs, y_obs, r_image,
        boundary_label="Barrier", image_label="Image (pump)"
    )
    st.plotly_chart(fig_geo, use_container_width=True)

st.info(
    f"r = {r:.1f} m · θ = {theta:.0f}° · a = {a:.1f} m · "
    f"r_image = {r_image:.1f} m · "
    f"T = {T:.3g} m²/day · S = {S:.2e} · Q = {Q:.1f} m³/day"
)
