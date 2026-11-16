# utils/plotting.py
# Shared Streamlit UI components and Plotly chart builders

import json

import numpy as np
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import plotly.graph_objects as go
import plotly.io as pio

from utils.i18n import tr


# ── Font scale (×1.2 from original baseline) ─────────────────────────────────
# Original:  base=14, title=18, axis_title=16, tick=13
# ×1.2:      base=17, title=22, axis_title=19, tick=16

_BASE_FONT  = 17
_TITLE_FONT = 22
_AXIS_TITLE = 19
_TICK_FONT  = 16

# Height (px) of the log-log charts on the page. Streamlit's default is 450, which
# looks too wide on a wide screen; 700 gives a taller y-axis.
LOGLOG_HEIGHT = 700


# ── Sidebar widgets ──────────────────────────────────────────────────────────

def render_aquifer_sidebar():
    """Render T and S log-scale sliders. Returns (T, S)."""
    st.sidebar.header(tr("Aquifer Parameters", "帯水層パラメータ"))

    log_T = st.sidebar.slider(
        tr("Transmissivity T (m²/day)", "透水量係数 T (m²/日)"),
        min_value=-2.0, max_value=3.0, value=2.0, step=0.01
    )
    T = 10 ** log_T
    st.sidebar.caption(f"T = {T:.3g} " + tr("m²/day", "m²/日"))

    log_S = st.sidebar.slider(
        tr("Storativity S", "貯留係数 S"),
        min_value=-6.0, max_value=-1.0, value=-4.0, step=0.01
    )
    S = 10 ** log_S
    st.sidebar.caption(f"S = {S:.2e}")

    return T, S


def render_upload_sidebar():
    """
    Render CSV upload widget.
    Returns DataFrame with columns [time_min, drawdown_m] or None.
    """
    st.sidebar.header(tr("Measurement Data", "観測データ"))
    uploaded = st.sidebar.file_uploader(
        tr("Upload CSV or TXT (time min, drawdown m)",
           "CSV または TXT をアップロード（時間 min、水位低下量 m）"),
        type=["csv", "txt"]
    )
    if uploaded is not None:
        try:
            df = pd.read_csv(
                uploaded, header=None, comment="#",
                names=["time_min", "drawdown_m"],
                sep=None, engine="python"
            )
            df = df[pd.to_numeric(df["time_min"], errors="coerce").notna()]
            df = df[pd.to_numeric(df["drawdown_m"], errors="coerce").notna()]
            df = df.astype(float)
            df = df[(df["time_min"] > 0) & (df["drawdown_m"] > 0)]
            df = df.reset_index(drop=True)
            st.sidebar.success(tr(f"{len(df)} data points loaded", f"{len(df)} 点のデータを読み込みました"))
            return df
        except Exception as e:
            st.sidebar.error(tr(f"Could not read file: {e}", f"ファイルを読み込めません: {e}"))
    return None


# ── Print button ──────────────────────────────────────────────────────────────

def render_print_button(fig, filename="chart"):
    """
    Render a Print button beneath a Plotly figure.

    Serialises the figure to a self-contained HTML page and opens it in a new
    browser tab. window.print() fires automatically when the tab loads, giving
    the user a clean print dialog containing only the chart.

    Parameters
    ----------
    fig      : plotly.graph_objects.Figure
    filename : str   label used in the button tooltip
    """
    # Fixed figure size that fits a landscape A4 / Letter page. Without it Plotly
    # sizes the figure to the popup window, which is wider than the paper, and the
    # right-hand side of the chart is cut off when printed.
    print_w = 900
    # capped at 640 px so the chart plus margins stays on one landscape sheet
    print_h = min(int(fig.layout.height), 640) if fig.layout.height else 600
    fig_html = pio.to_html(
        fig,
        full_html=True,
        include_plotlyjs="cdn",
        config={"displayModeBar": False},
        default_width=f"{print_w}px",
        default_height=f"{print_h}px",
    )

    print_css = (
        "<style>@page{size:landscape;margin:12mm}"
        "html,body{margin:0;padding:0;background:#fff}"
        "body{-webkit-print-color-adjust:exact;print-color-adjust:exact}</style>"
    )
    fig_html = fig_html.replace("</head>", print_css + "</head>")

    # Auto-trigger print shortly after the popup has drawn the figure
    # (runs only inside the popup)
    print_script = ("<script>window.onload=function(){"
                    "setTimeout(function(){window.print();},500);};</script>")
    fig_html_final = fig_html.replace("</body>", print_script + "</body>")

    # Embed the page as a JSON string literal. "</" and "<!--" must be broken
    # up, otherwise the browser would end THIS <script> block at the first
    # "</script>" inside the figure HTML and leak the rest (including the
    # auto-print line) into the iframe, which then prints on every rerun.
    js_literal = (
        json.dumps(fig_html_final)
        .replace("</", "<\\/")
        .replace("<!--", "<\\!--")
    )

    print_label = tr("Print", "印刷")
    popup_msg = json.dumps(tr("Please allow pop-ups to print this figure.",
                              "この図を印刷するには、ポップアップを許可してください。"))
    html = f"""
    <script>
    var __figHtml = {js_literal};
    function doPrint() {{
        var w = window.open('', '_blank');
        if (!w) {{ alert({popup_msg}); return; }}
        w.document.open();
        w.document.write(__figHtml);
        w.document.close();
    }}
    </script>
    <button
        onclick="doPrint()"
        title="{print_label}: {filename}"
        style="display:inline-flex;align-items:center;gap:6px;
               background:#f0f2f6;border:1px solid #ccc;border-radius:6px;
               padding:6px 18px;font-size:14px;
               font-family:Helvetica,Arial,sans-serif;
               cursor:pointer;color:#333;margin-top:2px;">
      🖨&nbsp;{print_label}
    </button>
    """
    components.html(html, height=52)


def apply_drawdown_floor(fig, ymin=0.01):
    """
    For log-scale drawdown plots, fix the lower y limit at `ymin` (m, default
    0.01) so the axis never drops to micrometre values. The upper limit is still
    set automatically from the largest plotted value.
    Figures without a log "Drawdown (m)" y-axis are left untouched.
    """
    yaxis = fig.layout.yaxis
    ytitle = yaxis.title.text if yaxis.title is not None else None
    if yaxis.type != "log" or ytitle not in ("Drawdown (m)", "水位低下量 (m)"):
        return fig

    ymax = 0.0
    for tr in fig.data:
        y = getattr(tr, "y", None)
        if y is None:
            continue
        arr = np.asarray(y, dtype=float)
        arr = arr[np.isfinite(arr) & (arr > 0)]
        if arr.size:
            ymax = max(ymax, float(arr.max()))
    if ymax <= 0:
        ymax = 1.0

    lower = np.log10(ymin)
    upper = max(np.log10(ymax) + 0.05, lower + 1.0)  # at least one decade shown
    fig.update_yaxes(range=[lower, upper])
    return fig


def plotly_chart_with_print(fig, filename="chart", **kwargs):
    """
    Drop-in replacement for st.plotly_chart() that also shows a Print button.
    All extra kwargs are forwarded to st.plotly_chart().
    Drawdown (log) axes are floored at 0.01 m.
    """
    apply_drawdown_floor(fig)
    st.plotly_chart(fig, **kwargs)
    render_print_button(fig, filename=filename)


# ── Shared layout base ────────────────────────────────────────────────────────

COLORS = {
    "theis": "#1f77b4",
    "model": "#2ca02c",
    "image": "#ff7f0e",
    "data":  "#d62728",
    "grid":  "#e0e0e0",
}

LAYOUT_BASE = dict(
    paper_bgcolor="white",
    plot_bgcolor="white",
    font=dict(family="Helvetica, Arial, sans-serif", size=_BASE_FONT, color="#222"),
    legend=dict(
        x=0.02, y=0.98,
        bgcolor="rgba(255,255,255,0.8)",
        bordercolor="#ccc", borderwidth=1,
        font=dict(size=_BASE_FONT - 1),
    ),
    margin=dict(l=85, r=35, t=75, b=85),
)


# ── Log-log chart builder ─────────────────────────────────────────────────────

def make_loglog_figure(title=None):
    """Return a base Plotly figure with log-log axes and ×1.2 fonts."""
    title = title or tr("Theis Drawdown — Log-Log", "テイス法による水位低下量（両対数）")
    fig = go.Figure()
    fig.update_layout(
        **LAYOUT_BASE,
        height=LOGLOG_HEIGHT,
        title=dict(text=title, font=dict(size=_TITLE_FONT)),
        xaxis=dict(
            type="log", title=tr("Time (min)", "時間 (min)"),
            showgrid=True, gridcolor=COLORS["grid"],
            minor=dict(showgrid=True, gridcolor="#f0f0f0"),
            title_font=dict(size=_AXIS_TITLE),
            tickfont=dict(size=_TICK_FONT),
        ),
        yaxis=dict(
            type="log", title=tr("Drawdown (m)", "水位低下量 (m)"),
            showgrid=True, gridcolor=COLORS["grid"],
            minor=dict(showgrid=True, gridcolor="#f0f0f0"),
            title_font=dict(size=_AXIS_TITLE),
            tickfont=dict(size=_TICK_FONT),
        ),
    )
    return fig


# ── Trace helpers ─────────────────────────────────────────────────────────────

def add_theis_trace(fig, times, drawdown, name="Theis", dash="dot", color=None):
    color = color or COLORS["theis"]
    fig.add_trace(go.Scatter(
        x=times, y=drawdown, mode="lines", name=name,
        line=dict(color=color, width=2, dash=dash)
    ))


def add_model_trace(fig, times, drawdown, name=None, color=None):
    name = name or tr("Model", "モデル")
    color = color or COLORS["model"]
    fig.add_trace(go.Scatter(
        x=times, y=drawdown, mode="lines", name=name,
        line=dict(color=color, width=2.5)
    ))


def add_data_trace(fig, df, name=None):
    name = name or tr("Measured data", "観測データ")
    if df is not None and len(df) > 0:
        fig.add_trace(go.Scatter(
            x=df["time_min"], y=df["drawdown_m"],
            mode="markers", name=name,
            marker=dict(color=COLORS["data"], size=8,
                        symbol="circle-open", line=dict(width=2))
        ))


# ── Geometry diagram (plan view) ──────────────────────────────────────────────

def render_geometry_diagram(r, theta_deg, a, x_obs, y_obs, r_image,
                             boundary_label=None, image_label=None):
    """Plan-view geometry diagram for river / barrier pages."""
    boundary_label = boundary_label or tr("Boundary", "境界")
    image_label = image_label or tr("Image well", "影像井戸")
    fig = go.Figure()

    # Boundary line
    span_y = max(r, a, abs(y_obs)) * 1.4 + 10
    fig.add_shape(
        type="line", x0=a, x1=a,
        y0=-span_y, y1=span_y,
        line=dict(color="#4a90d9", width=2, dash="dash")
    )
    fig.add_annotation(
        x=a, y=span_y * 0.9, text=boundary_label,
        showarrow=False, font=dict(color="#4a90d9", size=_BASE_FONT - 2)
    )

    # Image well
    fig.add_trace(go.Scatter(
        x=[2 * a], y=[0], mode="markers+text",
        marker=dict(symbol="circle-open", size=14, color="#ff7f0e",
                    line=dict(width=2)),
        text=[image_label], textposition="top center",
        textfont=dict(size=_BASE_FONT - 3, color="#ff7f0e"),
        showlegend=False
    ))

    # Pumping well
    fig.add_trace(go.Scatter(
        x=[0], y=[0], mode="markers+text",
        marker=dict(symbol="circle", size=14, color="#1f77b4"),
        text=[tr("Pump", "揚水井")], textposition="top center",
        textfont=dict(size=_BASE_FONT - 3, color="#1f77b4"),
        showlegend=False
    ))

    # Observation point
    obs_color = "#2ca02c" if x_obs < a else "#d62728"
    fig.add_trace(go.Scatter(
        x=[x_obs], y=[y_obs], mode="markers+text",
        marker=dict(symbol="star", size=14, color=obs_color),
        text=[tr("Obs", "観測点")], textposition="top center",
        textfont=dict(size=_BASE_FONT - 3, color=obs_color),
        showlegend=False
    ))

    # Connector lines
    fig.add_trace(go.Scatter(
        x=[0, x_obs], y=[0, y_obs], mode="lines",
        line=dict(color="#2ca02c", width=1.5, dash="dot"), showlegend=False
    ))
    fig.add_trace(go.Scatter(
        x=[x_obs, 2 * a], y=[y_obs, 0], mode="lines",
        line=dict(color="#ff7f0e", width=1.5, dash="dot"), showlegend=False
    ))

    # Distance labels
    fig.add_annotation(x=x_obs / 2, y=y_obs / 2, text=f"r = {r:.0f} m",
                       showarrow=False,
                       font=dict(size=_BASE_FONT - 4, color="#2ca02c"))
    fig.add_annotation(x=(x_obs + 2 * a) / 2, y=y_obs / 2,
                       text=f"r' = {r_image:.0f} m",
                       showarrow=False,
                       font=dict(size=_BASE_FONT - 4, color="#ff7f0e"))

    span_x = max(2 * a, span_y)
    layout = {
        **LAYOUT_BASE,
        "title": dict(text=tr("Plan View — Well & Boundary Geometry", "平面図 — 井戸と境界の配置"),
                      font=dict(size=_TITLE_FONT - 2)),
        "xaxis": dict(
            title="x (m)", range=[-span_x * 0.25, span_x * 1.1],
            showgrid=True, gridcolor=COLORS["grid"],
            title_font=dict(size=_AXIS_TITLE - 2),
            tickfont=dict(size=_TICK_FONT - 2),
        ),
        "yaxis": dict(
            title="y (m)", range=[-span_y, span_y],
            showgrid=True, gridcolor=COLORS["grid"],
            scaleanchor="x",
            title_font=dict(size=_AXIS_TITLE - 2),
            tickfont=dict(size=_TICK_FONT - 2),
        ),
        "height": 390,
    }
    fig.update_layout(**layout)
    return fig


# ── Cross-section diagram (partial penetration) ───────────────────────────────

def render_crosssection_diagram(b, l, d, z):
    """Vertical cross-section: aquifer, screen position, observation depth."""
    fig = go.Figure()
    W = 1.0  # normalised width

    # Aquifer block
    fig.add_shape(type="rect", x0=0, x1=W, y0=0, y1=b,
                  fillcolor="#dbeeff", line=dict(color="#4a90d9", width=1.5))

    # Screen interval
    fig.add_shape(type="rect", x0=W * 0.3, x1=W * 0.7, y0=l, y1=d,
                  fillcolor="#1f77b4", line=dict(color="#1f77b4", width=0))
    fig.add_annotation(x=W * 0.5, y=(l + d) / 2, text=tr("Screen", "ストレーナー"),
                       showarrow=False,
                       font=dict(color="white", size=_BASE_FONT - 3))

    # Well casing (above the screen: depth 0 to l)
    fig.add_shape(type="rect", x0=W * 0.42, x1=W * 0.58, y0=0, y1=l,
                  fillcolor="#999", line=dict(color="#666", width=1))

    # Depth reference lines and labels
    for depth, label in [
        (0, tr("Water table", "地下水面")),
        (b, tr("b (base)", "b（帯水層底面）")),
        (l, f"l = {l:.1f} m"),
        (d, f"d = {d:.1f} m"),
    ]:
        fig.add_shape(type="line", x0=0, x1=W + 0.05, y0=depth, y1=depth,
                      line=dict(color="#aaa", width=1, dash="dot"))
        fig.add_annotation(x=W + 0.07, y=depth, text=label,
                           showarrow=False, xanchor="left",
                           font=dict(size=_BASE_FONT - 4, color="#444"))

    # Observation point
    if 0 <= z <= b:
        fig.add_trace(go.Scatter(
            x=[W * 0.85], y=[z], mode="markers+text",
            marker=dict(symbol="star", size=14, color="#d62728"),
            text=[tr(f"Obs  z = {z:.1f} m", f"観測点  z = {z:.1f} m")], textposition="middle right",
            textfont=dict(size=_BASE_FONT - 4, color="#d62728"),
            showlegend=False
        ))

    layout = {
        **LAYOUT_BASE,
        "title": dict(text=tr("Vertical Cross-Section", "鉛直断面図"),
                      font=dict(size=_TITLE_FONT - 2)),
        "xaxis": dict(showticklabels=False, showgrid=False,
                      range=[-0.1, W + 0.6], zeroline=False),
        "yaxis": dict(
            title=tr("Depth (m)", "深さ (m)"), autorange="reversed",
            showgrid=False,
            title_font=dict(size=_AXIS_TITLE - 2),
            tickfont=dict(size=_TICK_FONT - 2),
        ),
        "height": 390,
        "margin": dict(l=75, r=150, t=65, b=55),
    }
    fig.update_layout(**layout)
    return fig
