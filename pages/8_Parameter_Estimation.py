"""8_Parameter_Estimation.py — Auto-fit T and S from measured drawdown data"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from scipy.optimize import curve_fit
from utils.theis import calc_drawdown
from utils.plotting import make_loglog_figure, add_theis_trace, add_data_trace, COLORS

st.set_page_config(page_title="Parameter Estimation", page_icon="📈", layout="wide")
st.title("📈 Parameter Estimation — Curve Fitting")
st.markdown("""
Automatically fits **T** (transmissivity) and **S** (storativity) to measured
drawdown data using least-squares optimisation of the standard Theis equation.
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
T0 = 10 ** log_T0
S0 = 10 ** log_S0
st.sidebar.caption(f"T₀ = {T0:.3g} m²/day · S₀ = {S0:.2e}")

# ── Fitting ───────────────────────────────────────────────────────────────────
if df_data is None:
    st.info("Upload a CSV file with measured drawdown data to begin.")
    st.stop()

if len(df_data) < 3:
    st.error("Need at least 3 data points to fit T and S.")
    st.stop()

times_obs = df_data["time_min"].values
s_obs = df_data["drawdown_m"].values

def theis_model(times, T, S):
    return calc_drawdown(times, T, S, r, Q)

try:
    popt, pcov = curve_fit(
        theis_model, times_obs, s_obs,
        p0=[T0, S0],
        bounds=([0.01, 1e-7], [1e4, 1.0]),
        maxfev=5000
    )
    T_fit, S_fit = popt
    perr = np.sqrt(np.diag(pcov))
    T_err, S_err = perr
    fit_ok = True
except Exception as e:
    st.error(f"Curve fitting failed: {e}")
    T_fit, S_fit = T0, S0
    T_err, S_err = 0.0, 0.0
    fit_ok = False

# ── Results ───────────────────────────────────────────────────────────────────
if fit_ok:
    col1, col2, col3 = st.columns(3)
    col1.metric("T (m²/day)", f"{T_fit:.4g}", f"± {T_err:.2g}")
    col2.metric("S (–)", f"{S_fit:.3e}", f"± {S_err:.2e}")
    residuals = s_obs - theis_model(times_obs, T_fit, S_fit)
    rmse = np.sqrt(np.mean(residuals**2))
    col3.metric("RMSE (m)", f"{rmse:.4f}")

# ── Chart ────────────────────────────────────────────────────────────────────
times_plot = np.logspace(np.log10(times_obs.min()), np.log10(times_obs.max()), 300)
s_fit_plot = calc_drawdown(times_plot, T_fit, S_fit, r, Q)

fig = make_loglog_figure("Parameter Estimation — Best-Fit Theis Curve")
fig.add_trace(go.Scatter(
    x=times_plot, y=s_fit_plot, mode="lines",
    name=f"Best fit (T={T_fit:.3g}, S={S_fit:.2e})",
    line=dict(color=COLORS["model"], width=2.5)
))
add_data_trace(fig, df_data)
st.plotly_chart(fig, use_container_width=True)

# ── Residual plot ─────────────────────────────────────────────────────────────
if fit_ok:
    fig_res = go.Figure()
    fig_res.add_trace(go.Scatter(
        x=times_obs, y=residuals, mode="markers",
        marker=dict(color=COLORS["data"], size=8),
        name="Residuals"
    ))
    fig_res.add_hline(y=0, line=dict(color="#aaa", dash="dash"))
    fig_res.update_layout(
        paper_bgcolor="white", plot_bgcolor="white",
        font=dict(family="Helvetica, Arial, sans-serif", size=13),
        title="Residuals (observed − fitted)",
        xaxis=dict(type="log", title="Time (min)",
                   showgrid=True, gridcolor="#e0e0e0"),
        yaxis=dict(title="Residual (m)",
                   showgrid=True, gridcolor="#e0e0e0"),
        margin=dict(l=60, r=30, t=50, b=60),
    )
    st.plotly_chart(fig_res, use_container_width=True)

# ── Data table ────────────────────────────────────────────────────────────────
if fit_ok:
    st.subheader("Data vs. Fitted Values")
    s_fitted = theis_model(times_obs, T_fit, S_fit)
    df_compare = pd.DataFrame({
        "Time (min)": times_obs,
        "Observed s (m)": [f"{v:.4f}" for v in s_obs],
        "Fitted s (m)":   [f"{v:.4f}" for v in s_fitted],
        "Residual (m)":   [f"{v:.4f}" for v in residuals],
    })
    st.dataframe(df_compare, use_container_width=False, hide_index=True)

st.caption(f"r = {r:.1f} m · Q = {Q:.1f} m³/day · {len(df_data)} data points")
