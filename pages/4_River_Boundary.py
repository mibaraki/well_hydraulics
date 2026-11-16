"""4_River_Boundary.py — Constant-head boundary (river) using method of superposition"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import streamlit as st
from utils.i18n import tr
from utils.theis import calc_drawdown, calc_drawdown_river, TIME_MAX_MIN
from utils.plotting import (render_aquifer_sidebar, render_upload_sidebar,
                             make_loglog_figure, add_theis_trace,
                             add_model_trace, add_data_trace,
                             render_geometry_diagram, plotly_chart_with_print)

st.set_page_config(page_title=tr("River Boundary", "河川境界"), page_icon="🔵", layout="wide")

from utils.license import require_license
require_license()   # Pro page: needs a valid license key
st.title(tr("🔵 River Boundary — Constant-Head", "🔵 河川境界 — 定水頭境界"))
st.markdown(tr("""
A river, lake, or canal acts as a **constant-head boundary**.
The method of superposition places an **injection well** (−Q) mirrored across the river.
Drawdown is **less** than standard Theis at late time as the river recharges the aquifer.
""", """
河川・湖・水路は**定水頭境界**として働きます。
重ね合わせ法では、河川を挟んで鏡像の位置に**注水の鏡像井戸（イメージ・ウェル）**（−Q）を置きます。
河川から帯水層に水が供給されるため、後期の水位低下量は標準タイス式より**小さく**なります。
"""))

# ── Sidebar ──────────────────────────────────────────────────────────────────
T, S = render_aquifer_sidebar()

st.sidebar.header(tr("Well & Boundary", "井戸と境界"))
Q = st.sidebar.number_input(tr("Pumping rate Q (m³/day)", "揚水量 Q (m³/日)"), value=500.0, min_value=0.1)
a = st.sidebar.number_input(tr("Distance to river a (m)", "河川までの距離 a (m)"), value=100.0, min_value=1.0)

st.sidebar.header(tr("Observation Point", "観測点"))
r = st.sidebar.number_input(tr("Distance from pump r (m)", "揚水井からの距離 r (m)"), value=50.0, min_value=0.1)
theta = st.sidebar.slider(tr("Angle θ (degrees)", "角度 θ (度)"), 0.0, 360.0, 90.0, step=1.0)

df_data = render_upload_sidebar()

# ── Validity check ────────────────────────────────────────────────────────────
s_boundary, r_image, x_obs, y_obs = calc_drawdown_river(
    [60], T, S, r, theta, a, Q)
if x_obs >= a:
    st.error(tr(
        f"⚠️ Observation point (x = {x_obs:.1f} m) is beyond or on the river "
        f"(x = {a:.1f} m). Method of superposition is not valid here.",
        f"⚠️ 観測点 (x = {x_obs:.1f} m) が河川 (x = {a:.1f} m) の向こう側、または河川上にあります。"
        "この条件では重ね合わせ法は適用できません。"
    ))
    st.stop()

# ── Calculation ───────────────────────────────────────────────────────────────
times = np.logspace(np.log10(1), np.log10(TIME_MAX_MIN), 300)
s_river, r_image, x_obs, y_obs = calc_drawdown_river(times, T, S, r, theta, a, Q)
s_theis = calc_drawdown(times, T, S, r, Q)

# ── Layout: chart + geometry ──────────────────────────────────────────────────
col1, col2 = st.columns([2, 1])

with col1:
    fig = make_loglog_figure(tr("River Boundary — Method of Superposition", "河川境界 — 重ね合わせ法"))
    add_theis_trace(fig, times, s_theis, name=tr("Standard Theis (no boundary)", "標準タイス式（境界なし）"),
                    dash="dot", color="#aaa")
    add_model_trace(fig, times, s_river, name=tr("River boundary (−Q image)", "河川境界（−Q の鏡像井戸）"))
    add_data_trace(fig, df_data)
    plotly_chart_with_print(fig, filename='river-boundary', use_container_width=True)

with col2:
    fig_geo = render_geometry_diagram(
        r, theta, a, x_obs, y_obs, r_image,
        boundary_label=tr("River", "河川"), image_label=tr("Image (injection)", "鏡像井戸（注水）")
    )
    plotly_chart_with_print(fig_geo, filename='river-geometry', use_container_width=True)

st.info(
    f"r = {r:.1f} m · θ = {theta:.0f}° · a = {a:.1f} m · "
    f"r_image = {r_image:.1f} m · "
    f"T = {T:.3g} " + tr("m²/day", "m²/日") + f" · S = {S:.2e} · Q = {Q:.1f} " + tr("m³/day", "m³/日")
)
