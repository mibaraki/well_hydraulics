"""8_Parameter_Estimation.py — Auto-fit T and S from measured drawdown data"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from utils.theis import calc_drawdown, TIME_MAX_MIN
from utils.fitting import theis_vec, fit_theis
from utils.plotting import (make_loglog_figure, add_data_trace,
                             plotly_chart_with_print, COLORS)

st.set_page_config(page_title="Parameter Estimation", page_icon="📈", layout="wide")
st.title("📈 Parameter Estimation — Curve Fitting")
st.markdown("""
Fits **T** (transmissivity) and **S** (storativity) to measured drawdown with the
standard Theis equation. By default the misfit is measured on **log₁₀(drawdown)**, so
every point counts equally on a log-log plot. You can also restrict the fit to a
time window, for example to leave out late-time data that no longer follows Theis.
""")

# ── Upload data ───────────────────────────────────────────────────────────────
st.sidebar.header("Measurement Data")
uploaded = st.sidebar.file_uploader(
    "Upload CSV or TXT (time min, drawdown m)",
    type=["csv", "txt"]
)

df_data = None
if uploaded is not None:
    try:
        df_data = pd.read_csv(
            uploaded, header=None, comment="#",
            names=["time_min", "drawdown_m"],
            sep=None, engine="python"
        )
        df_data = df_data[pd.to_numeric(df_data["time_min"], errors="coerce").notna()]
        df_data = df_data[pd.to_numeric(df_data["drawdown_m"], errors="coerce").notna()]
        df_data = df_data.astype(float)
        df_data = df_data[(df_data["time_min"] > 0) & (df_data["drawdown_m"] > 0)]
        df_data = df_data.reset_index(drop=True)
        st.sidebar.success(f"{len(df_data)} data points loaded")
    except Exception as e:
        st.sidebar.error(f"Could not read file: {e}")
        df_data = None

# ── Fixed well/aquifer parameters ─────────────────────────────────────────────
st.sidebar.header("Fixed Parameters")
r = st.sidebar.number_input("Distance r (m)", value=50.0, min_value=0.1)
Q = st.sidebar.number_input("Pumping rate Q (m³/day)", value=500.0, min_value=0.1)

st.sidebar.header("Initial Guess")
log_T0 = st.sidebar.slider("log₁₀(T) initial guess", -2.0, 3.0, 2.0, step=0.1)
log_S0 = st.sidebar.slider("log₁₀(S) initial guess", -6.0, -1.0, -4.0, step=0.1)
st.sidebar.caption(f"T₀ = {10**log_T0:.3g} m²/day · S₀ = {10**log_S0:.2e}")

# ── Data checks ───────────────────────────────────────────────────────────────
if df_data is None:
    st.info("Upload a CSV file with measured drawdown data to begin.")
    st.stop()

if len(df_data) < 3:
    st.error("Need at least 3 data points to fit T and S.")
    st.stop()

times_obs = df_data["time_min"].values
s_obs = df_data["drawdown_m"].values

# ── Fit settings (need the data range, so they come after the upload) ────────
st.sidebar.header("Fit Settings")
objective = st.sidebar.radio(
    "Misfit measure",
    ["Log₁₀ drawdown (recommended)", "Linear drawdown (m)"],
    help="Log: equal relative weight for every point, matches how a log-log plot "
         "looks. Linear: large late-time drawdowns dominate and early points are "
         "almost ignored.",
)
use_log = objective.startswith("Log")

key = uploaded.name
t_lo = st.sidebar.number_input("Fit from t (min)", value=float(times_obs.min()),
                               min_value=0.0, step=10.0, key=f"t_lo_{key}")
t_hi = st.sidebar.number_input("Fit to t (min)", value=float(times_obs.max()),
                               min_value=0.0, step=10.0, key=f"t_hi_{key}")
s_min = st.sidebar.number_input(
    "Ignore drawdown below (m)", value=0.01, min_value=0.0, step=0.001, format="%.3f",
    help="Very small drawdowns are dominated by reading resolution (a 0.5 mm error "
         "is 25% of a 2 mm reading), yet a log fit counts them as much as any other "
         "point. Default 0.01 m, the same as the lower limit of the drawdown plots.")
multi = st.sidebar.checkbox("Try several starting points", value=True,
                            help="Runs the fit from a grid of starting values and "
                                 "keeps the best result.")

use = (times_obs >= t_lo) & (times_obs <= t_hi) & (s_obs >= s_min)
if use.sum() < 3:
    st.error("Fewer than 3 data points pass the fit window and the minimum "
             "drawdown. Widen the window or lower the minimum.")
    st.stop()

# ── Fitting ───────────────────────────────────────────────────────────────────
fit = fit_theis(times_obs[use], s_obs[use], r, Q, use_log=use_log,
                start=(log_T0, log_S0), multi_start=multi)
if fit is None:
    st.error("Curve fitting failed. Try a different initial guess or fit window.")
    st.stop()

T_fit, S_fit = fit["T"], fit["S"]

st.info(f"Fitting with **r = {r:g} m** and **Q = {Q:g} m³/day** "
        f"({int(use.sum())} of {len(df_data)} points, "
        f"{t_lo:g}–{t_hi:g} min, drawdown ≥ {s_min:g} m). "
        f"T and S scale with Q, so a wrong Q gives wrong T and S.")

# ── Results ───────────────────────────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
col1.metric("T (m²/day)", f"{T_fit:.4g}",
            f"×/÷ {10 ** fit['sigma_logT']:.2f}", delta_color="off")
col2.metric("S (–)", f"{S_fit:.3e}",
            f"×/÷ {10 ** fit['sigma_logS']:.2f}", delta_color="off")
col3.metric("RMSE (m)", f"{fit['rms_m']:.4f}")
col4.metric("Log₁₀ misfit (decades)", f"{fit['rms_log']:.3f}")

st.caption(f"T = {T_fit / 1440:.4e} m²/min · correlation between T and S = {fit['corr']:+.3f}")
if np.isfinite(fit["corr"]) and abs(fit["corr"]) > 0.95:
    st.warning("T and S are strongly correlated for this data, so they are not "
               "independently well determined. Treat the uncertainty factors above "
               "as optimistic.")
if fit["at_bound"]:
    st.warning("The best fit is at the edge of the allowed range "
               "(T: 0.01–10,000 m²/day, S: 1e-7–1). Check r, Q and the fit window.")

# ── Chart ────────────────────────────────────────────────────────────────────
times_plot = np.logspace(np.log10(times_obs.min()),
                         np.log10(max(times_obs.max(), TIME_MAX_MIN)), 300)
s_fit_plot = calc_drawdown(times_plot, T_fit, S_fit, r, Q)

fig = make_loglog_figure("Parameter Estimation — Best-Fit Theis Curve")
fig.add_trace(go.Scatter(
    x=times_plot, y=s_fit_plot, mode="lines",
    name=f"Best fit (T={T_fit:.3g}, S={S_fit:.2e})",
    line=dict(color=COLORS["model"], width=2.5)
))
add_data_trace(fig, df_data[use], name="Measured data (used in fit)")
if (~use).any():
    df_out = df_data[~use]
    fig.add_trace(go.Scatter(
        x=df_out["time_min"], y=df_out["drawdown_m"], mode="markers",
        name="Excluded from fit",
        marker=dict(color="#999999", size=8, symbol="x")
    ))
plotly_chart_with_print(fig, filename='parameter-estimation', use_container_width=True)

# ── Residual plot ─────────────────────────────────────────────────────────────
s_fitted = theis_vec(times_obs, T_fit, S_fit, r, Q)
if use_log:
    residuals = np.log10(s_obs) - np.log10(np.maximum(s_fitted, 1e-300))
    res_label = "log₁₀(observed) − log₁₀(fitted)"
else:
    residuals = s_obs - s_fitted
    res_label = "Observed − fitted (m)"

fig_res = go.Figure()
fig_res.add_trace(go.Scatter(
    x=times_obs[use], y=residuals[use], mode="markers",
    marker=dict(color=COLORS["data"], size=8), name="Used in fit"
))
if (~use).any():
    fig_res.add_trace(go.Scatter(
        x=times_obs[~use], y=residuals[~use], mode="markers",
        marker=dict(color="#999999", size=8, symbol="x"), name="Excluded from fit"
    ))
fig_res.add_hline(y=0, line=dict(color="#aaa", dash="dash"))
fig_res.update_layout(
    paper_bgcolor="white", plot_bgcolor="white",
    font=dict(family="Helvetica, Arial, sans-serif", size=17),
    title=dict(text="Residuals", font=dict(size=22)),
    xaxis=dict(type="log", title="Time (min)",
               showgrid=True, gridcolor="#e0e0e0",
               title_font=dict(size=19), tickfont=dict(size=16)),
    yaxis=dict(title=res_label,
               showgrid=True, gridcolor="#e0e0e0",
               title_font=dict(size=19), tickfont=dict(size=16)),
    legend=dict(font=dict(size=16)),
    margin=dict(l=85, r=35, t=75, b=85),
)
plotly_chart_with_print(fig_res, filename='residuals', use_container_width=True)

# ── Data table ────────────────────────────────────────────────────────────────
st.subheader("Data vs. Fitted Values")
df_compare = pd.DataFrame({
    "Time (min)": times_obs,
    "Observed s (m)": [f"{v:.4f}" for v in s_obs],
    "Fitted s (m)":   [f"{v:.4f}" for v in s_fitted],
    "Fitted / observed": [f"{v:.2f}" for v in s_fitted / s_obs],
    "Used in fit": np.where(use, "yes", "no"),
})
st.dataframe(df_compare, use_container_width=False, hide_index=True)

st.caption(f"r = {r:.1f} m · Q = {Q:.1f} m³/day · {len(df_data)} data points")
