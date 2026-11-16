"""8_Parameter_Estimation.py — Auto-fit T and S from measured drawdown data"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from utils.i18n import tr
from utils.theis import calc_drawdown, TIME_MAX_MIN
from utils.fitting import theis_vec, fit_theis
from utils.plotting import (make_loglog_figure, add_data_trace,
                             plotly_chart_with_print, COLORS)

st.set_page_config(page_title=tr("Parameter Estimation", "パラメータ推定"), page_icon="📈", layout="wide")

from utils.license import require_license
require_license()   # Pro page: needs a valid license key
st.title(tr("📈 Parameter Estimation — Curve Fitting", "📈 パラメータ推定 — 曲線あてはめ"))
st.markdown(tr("""
Fits **T** (transmissivity) and **S** (storativity) to measured drawdown with the
standard Theis equation. By default the misfit is measured on **log₁₀(drawdown)**, so
every point counts equally on a log-log plot. You can also restrict the fit to a
time window, for example to leave out late-time data that no longer follows Theis.
""", """
標準のタイス式を観測された水位低下量にあてはめて、**T**（透水量係数）と **S**（貯留係数）を求めます。
既定では **log₁₀(水位低下量)** で残差を測るため、両対数グラフ上ですべての点が同じ重みになります。
時間範囲を限定することもできます。たとえば、タイス式に従わなくなった後期のデータを除外できます。
"""))

# ── Upload data ───────────────────────────────────────────────────────────────
st.sidebar.header(tr("Measurement Data", "観測データ"))
uploaded = st.sidebar.file_uploader(
    tr("Upload CSV or TXT (time min, drawdown m)", "CSV または TXT をアップロード（時間 min、水位低下量 m）"),
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
        st.sidebar.success(tr(f"{len(df_data)} data points loaded", f"{len(df_data)} 点のデータを読み込みました"))
    except Exception as e:
        st.sidebar.error(tr(f"Could not read file: {e}", f"ファイルを読み込めません: {e}"))
        df_data = None

# ── Fixed well/aquifer parameters ─────────────────────────────────────────────
st.sidebar.header(tr("Fixed Parameters", "固定パラメータ"))
r = st.sidebar.number_input(tr("Distance r (m)", "距離 r (m)"), value=50.0, min_value=0.1)
Q = st.sidebar.number_input(tr("Pumping rate Q (m³/day)", "揚水量 Q (m³/日)"), value=500.0, min_value=0.1)

st.sidebar.header(tr("Initial Guess", "初期値"))
log_T0 = st.sidebar.slider(tr("log₁₀(T) initial guess", "log₁₀(T) の初期値"), -2.0, 3.0, 2.0, step=0.1)
log_S0 = st.sidebar.slider(tr("log₁₀(S) initial guess", "log₁₀(S) の初期値"), -6.0, -1.0, -4.0, step=0.1)
st.sidebar.caption(f"T₀ = {10**log_T0:.3g} " + tr("m²/day", "m²/日") + f" · S₀ = {10**log_S0:.2e}")

# ── Data checks ───────────────────────────────────────────────────────────────
if df_data is None:
    st.info(tr("Upload a CSV file with measured drawdown data to begin.", "水位低下量の観測データを含む CSV ファイルをアップロードしてください。"))
    st.stop()

if len(df_data) < 3:
    st.error(tr("Need at least 3 data points to fit T and S.", "T と S を推定するには、3 点以上のデータが必要です。"))
    st.stop()

times_obs = df_data["time_min"].values
s_obs = df_data["drawdown_m"].values

# ── Fit settings (need the data range, so they come after the upload) ────────
st.sidebar.header(tr("Fit Settings", "あてはめの設定"))
objective = st.sidebar.radio(
    tr("Misfit measure", "残差の測り方"),
    ["log", "linear"],
    format_func=lambda v: tr("Log₁₀ drawdown (recommended)", "log₁₀ 水位低下量（推奨）") if v == "log"
                          else tr("Linear drawdown (m)", "水位低下量そのまま (m)"),
    help=tr("Log: equal relative weight for every point, matches how a log-log plot "
            "looks. Linear: large late-time drawdowns dominate and early points are "
            "almost ignored.",
            "log: すべての点に同じ相対的な重みを与え、両対数グラフの見え方に合います。"
            "linear: 後期の大きな水位低下量が支配的になり、初期の点はほとんど無視されます。"),
)
use_log = objective == "log"

key = uploaded.name
t_lo = st.sidebar.number_input(tr("Fit from t (min)", "あてはめ開始時間 (min)"), value=float(times_obs.min()),
                               min_value=0.0, step=10.0, key=f"t_lo_{key}")
t_hi = st.sidebar.number_input(tr("Fit to t (min)", "あてはめ終了時間 (min)"), value=float(times_obs.max()),
                               min_value=0.0, step=10.0, key=f"t_hi_{key}")
s_min = st.sidebar.number_input(
    tr("Ignore drawdown below (m)", "これより小さい水位低下量は除外 (m)"), value=0.01, min_value=0.0, step=0.001, format="%.3f",
    help=tr("Very small drawdowns are dominated by reading resolution (a 0.5 mm error "
            "is 25% of a 2 mm reading), yet a log fit counts them as much as any other "
            "point. Default 0.01 m, the same as the lower limit of the drawdown plots.",
            "ごく小さい水位低下量は測定の分解能に支配されます（2 mm の読みに対する 0.5 mm の誤差は 25%）。"
            "それでも log でのあてはめでは他の点と同じ重みで扱われます。"
            "既定値は 0.01 m で、水位低下量グラフの下限と同じです。"))
multi = st.sidebar.checkbox(tr("Try several starting points", "複数の初期値を試す"), value=True,
                            help=tr("Runs the fit from a grid of starting values and "
                                    "keeps the best result.",
                                    "初期値を格子状に変えてあてはめを繰り返し、最良の結果を採用します。"))

use = (times_obs >= t_lo) & (times_obs <= t_hi) & (s_obs >= s_min)
if use.sum() < 3:
    st.error(tr("Fewer than 3 data points pass the fit window and the minimum "
                "drawdown. Widen the window or lower the minimum.",
                "あてはめの時間範囲と水位低下量の下限を満たすデータが 3 点未満です。"
                "範囲を広げるか、下限を下げてください。"))
    st.stop()

# ── Fitting ───────────────────────────────────────────────────────────────────
fit = fit_theis(times_obs[use], s_obs[use], r, Q, use_log=use_log,
                start=(log_T0, log_S0), multi_start=multi)
if fit is None:
    st.error(tr("Curve fitting failed. Try a different initial guess or fit window.", "曲線あてはめに失敗しました。初期値またはあてはめの範囲を変えてみてください。"))
    st.stop()

T_fit, S_fit = fit["T"], fit["S"]

st.info(tr(f"Fitting with **r = {r:g} m** and **Q = {Q:g} m³/day** "
           f"({int(use.sum())} of {len(df_data)} points, "
           f"{t_lo:g}–{t_hi:g} min, drawdown ≥ {s_min:g} m). "
           f"T and S scale with Q, so a wrong Q gives wrong T and S.",
           f"**r = {r:g} m**、**Q = {Q:g} m³/日** であてはめました"
           f"（{len(df_data)} 点中 {int(use.sum())} 点、{t_lo:g}–{t_hi:g} min、水位低下量 ≥ {s_min:g} m）。"
           f"T と S は Q に比例するため、Q が違うと T と S も正しくなくなります。"))

# ── Results ───────────────────────────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
col1.metric(tr("T (m²/day)", "T (m²/日)"), f"{T_fit:.4g}",
            f"×/÷ {10 ** fit['sigma_logT']:.2f}", delta_color="off")
col2.metric("S (–)", f"{S_fit:.3e}",
            f"×/÷ {10 ** fit['sigma_logS']:.2f}", delta_color="off")
col3.metric(tr("RMSE (m)", "RMSE (m)"), f"{fit['rms_m']:.4f}")
col4.metric(tr("Log₁₀ misfit (decades)", "log₁₀ 残差 (桁)"), f"{fit['rms_log']:.3f}")

st.caption(tr(f"T = {T_fit / 1440:.4e} m²/min · correlation between T and S = {fit['corr']:+.3f}", f"T = {T_fit / 1440:.4e} m²/min · T と S の相関 = {fit['corr']:+.3f}"))
if np.isfinite(fit["corr"]) and abs(fit["corr"]) > 0.95:
    st.warning(tr("T and S are strongly correlated for this data, so they are not "
                  "independently well determined. Treat the uncertainty factors above "
                  "as optimistic.",
                  "このデータでは T と S の相関が強く、それぞれを独立に精度よく決められません。"
                  "上の不確かさの係数は楽観的な値として扱ってください。"))
if fit["at_bound"]:
    st.warning(tr("The best fit is at the edge of the allowed range "
                  "(T: 0.01–10,000 m²/day, S: 1e-7–1). Check r, Q and the fit window.",
                  "最適解が許容範囲の端にあります（T: 0.01–10,000 m²/日、S: 1e-7–1）。"
                  "r、Q、あてはめの範囲を確認してください。"))

# ── Chart ────────────────────────────────────────────────────────────────────
times_plot = np.logspace(np.log10(times_obs.min()),
                         np.log10(max(times_obs.max(), TIME_MAX_MIN)), 300)
s_fit_plot = calc_drawdown(times_plot, T_fit, S_fit, r, Q)

fig = make_loglog_figure(tr("Parameter Estimation — Best-Fit Theis Curve", "パラメータ推定 — 最適なタイス曲線"))
fig.add_trace(go.Scatter(
    x=times_plot, y=s_fit_plot, mode="lines",
    name=tr(f"Best fit (T={T_fit:.3g}, S={S_fit:.2e})", f"最適あてはめ (T={T_fit:.3g}, S={S_fit:.2e})"),
    line=dict(color=COLORS["model"], width=2.5)
))
add_data_trace(fig, df_data[use], name=tr("Measured data (used in fit)", "観測データ（あてはめに使用）"))
if (~use).any():
    df_out = df_data[~use]
    fig.add_trace(go.Scatter(
        x=df_out["time_min"], y=df_out["drawdown_m"], mode="markers",
        name=tr("Excluded from fit", "あてはめから除外"),
        marker=dict(color="#999999", size=8, symbol="x")
    ))
plotly_chart_with_print(fig, filename='parameter-estimation', use_container_width=True)

# ── Residual plot ─────────────────────────────────────────────────────────────
s_fitted = theis_vec(times_obs, T_fit, S_fit, r, Q)
if use_log:
    residuals = np.log10(s_obs) - np.log10(np.maximum(s_fitted, 1e-300))
    res_label = tr("log₁₀(observed) − log₁₀(fitted)", "log₁₀(観測値) − log₁₀(計算値)")
else:
    residuals = s_obs - s_fitted
    res_label = tr("Observed − fitted (m)", "観測値 − 計算値 (m)")

fig_res = go.Figure()
fig_res.add_trace(go.Scatter(
    x=times_obs[use], y=residuals[use], mode="markers",
    marker=dict(color=COLORS["data"], size=8), name=tr("Used in fit", "あてはめに使用")
))
if (~use).any():
    fig_res.add_trace(go.Scatter(
        x=times_obs[~use], y=residuals[~use], mode="markers",
        marker=dict(color="#999999", size=8, symbol="x"), name=tr("Excluded from fit", "あてはめから除外")
    ))
fig_res.add_hline(y=0, line=dict(color="#aaa", dash="dash"))
fig_res.update_layout(
    paper_bgcolor="white", plot_bgcolor="white",
    font=dict(family="Helvetica, Arial, sans-serif", size=17),
    title=dict(text=tr("Residuals", "残差"), font=dict(size=22)),
    xaxis=dict(type="log", title=tr("Time (min)", "時間 (min)"),
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
st.subheader(tr("Data vs. Fitted Values", "観測値と計算値の比較"))
df_compare = pd.DataFrame({
    tr("Time (min)", "時間 (min)"): times_obs,
    tr("Observed s (m)", "観測値 s (m)"): [f"{v:.4f}" for v in s_obs],
    tr("Fitted s (m)", "計算値 s (m)"):   [f"{v:.4f}" for v in s_fitted],
    tr("Fitted / observed", "計算値 / 観測値"): [f"{v:.2f}" for v in s_fitted / s_obs],
    tr("Used in fit", "あてはめに使用"): np.where(use, tr("yes", "はい"), tr("no", "いいえ")),
})
st.dataframe(df_compare, use_container_width=False, hide_index=True)

st.caption(f"r = {r:.1f} m · Q = {Q:.1f} " + tr("m³/day", "m³/日") + " · " + tr(f"{len(df_data)} data points", f"データ {len(df_data)} 点"))
