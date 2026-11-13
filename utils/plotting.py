# utils/plotting.py
# Shared Streamlit UI components and Plotly chart builders

import numpy as np
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import plotly.graph_objects as go
import plotly.io as pio


# ── Font scale (×1.2 from original baseline) ─────────────────────────────────
# Original:  base=14, title=18, axis_title=16, tick=13
# ×1.2:      base=17, title=22, axis_title=19, tick=16

_BASE_FONT  = 17
_TITLE_FONT = 22
_AXIS_TITLE = 19
_TICK_FONT  = 16


# ── Sidebar widgets ──────────────────────────────────────────────────────────

def render_aquifer_sidebar():
    """Render T and S log-scale sliders. Returns (T, S)."""
    st.sidebar.header("Aquifer Parameters")

    log_T = st.sidebar.slider(
        "Transmissivity T (m²/day)",
        min_value=-2.0, max_value=3.0, value=2.0, step=0.01
    )
    T = 10 ** log_T
    st.sidebar.caption(f"T = {T:.3g} m²/day")

    log_S = st.sidebar.slider(
        "Storativity S",
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
    st.sidebar.header("Measurement Data")
    uploaded = st.sidebar.file_uploader(
        "Upload CSV or TXT (time min, drawdown m)",
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
            st.sidebar.success(f"{len(df)} data points loaded")
            return df
        except Exception as e:
            st.sidebar.error(f"Could not read file: {e}")
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
    fig_html = pio.to_html(
        fig,
        full_html=True,
        include_plotlyjs="cdn",
        config={"displayModeBar": False},
    )

    # Escape characters that would break the JS template literal
    fig_html_escaped = (
        fig_html
        .replace("\\", "\\\\")
        .replace("`", "\\`")
        .replace("${", "\\${")
    )

    # Auto-trigger print when the popup opens
    print_script = "<script>window.onload=function(){window.print();};</script>"
    fig_html_final = fig_html_escaped.replace("</body>", print_script + "</body>")

    html = f"""
    <script>
    function doPrint_{filename.replace('-','_')}() {{
        var w = window.open('', '_blank');
        w.document.open();
        w.document.write(`{fig_html_final}`);
        w.document.close();
    }}
    </script>
    <button
        onclick="doPrint_{filename.replace('-','_')}()"
        title="Print {filename}"
        style="display:inline-flex;align-items:center;gap:6px;
               background:#f0f2f6;border:1px solid #ccc;border-radius:6px;
               padding:6px 18px;font-size:14px;
               font-family:Helvetica,Arial,sans-serif;
               cursor:pointer;color:#333;margin-top:2px;">
      🖨&nbsp;Print
    </button>
    """
    components.html(html, height=52)


def apply_drawdown_floor(fig, ymin=0.01):
    """
    For log-scale drawdown plots, fix the lower y limit at `ymin` (m) so the
    axis never drops to micrometre values. The upper limit is still set
    automatically from the largest plotted value.
    Figures without a log "Drawdown (m)" y-axis are left untouched.
    """
    yaxis = fig.layout.yaxis
    ytitle = yaxis.title.text if yaxis.title is not None else None
    if yaxis.type != "log" or ytitle != "Drawdown (m)":
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

def make_loglog_figure(title="Theis Drawdown — Log-Log"):
    """Return a base Plotly figure with log-log axes and ×1.2 fonts."""
    fig = go.Figure()
    fig.update_layout(
        **LAYOUT_BASE,
        title=dict(text=title, font=dict(size=_TITLE_FONT)),
        xaxis=dict(
            type="log", title="Time (min)",
            showgrid=True, gridcolor=COLORS["grid"],
            minor=dict(showgrid=True, gridcolor="#f0f0f0"),
            title_font=dict(size=_AXIS_TITLE),
            tickfont=dict(size=_TICK_FONT),
        ),
        yaxis=dict(
            type="log", title="Drawdown (m)",
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


def add_model_trace(fig, times, drawdown, name="Model", color=None):
    color = color or COLORS["model"]
    fig.add_trace(go.Scatter(
        x=times, y=drawdown, mode="lines", name=name,
        line=dict(color=color, width=2.5)
    ))


def add_data_trace(fig, df, name="Measured data"):
    if df is not None and len(df) > 0:
        fig.add_trace(go.Scatter(
            x=df["time_min"], y=df["drawdown_m"],
            mode="markers", name=name,
            marker=dict(color=COLORS["data"], size=8,
                        symbol="circle-open", line=dict(width=2))
        ))


# ── Geometry diagram (plan view) ──────────────────────────────────────────────

def render_geometry_diagram(r, theta_deg, a, x_obs, y_obs, r_image,
                             boundary_label="Boundary", image_label="Image well"):
    """Plan-view geometry diagram for river / barrier pages."""
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
        text=["Pump"], textposition="top center",
        textfont=dict(size=_BASE_FONT - 3, color="#1f77b4"),
        showlegend=False
    ))

    # Observation point
    obs_color = "#2ca02c" if x_obs < a else "#d62728"
    fig.add_trace(go.Scatter(
        x=[x_obs], y=[y_obs], mode="markers+text",
        marker=dict(symbol="star", size=14, color=obs_color),
        text=["Obs"], textposition="top center",
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
        "title": dict(text="Plan View — Well & Boundary Geometry",
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
    fig.add_annotation(x=W * 0.5, y=(l + d) / 2, text="Screen",
                       showarrow=False,
                       font=dict(color="white", size=_BASE_FONT - 3))

    # Well casing (above screen)
    fig.add_shape(type="rect", x0=W * 0.42, x1=W * 0.58, y0=d, y1=b,
                  fillcolor="#999", line=dict(color="#666", width=1))

    # Depth reference lines and labels
    for depth, label in [
        (0, "b (base)"),
        (b, "Water table"),
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
            text=[f"Obs  z = {z:.1f} m"], textposition="middle right",
            textfont=dict(size=_BASE_FONT - 4, color="#d62728"),
            showlegend=False
        ))

    layout = {
        **LAYOUT_BASE,
        "title": dict(text="Vertical Cross-Section",
                      font=dict(size=_TITLE_FONT - 2)),
        "xaxis": dict(showticklabels=False, showgrid=False,
                      range=[-0.1, W + 0.6], zeroline=False),
        "yaxis": dict(
            title="Depth (m)", autorange="reversed",
            showgrid=False,
            title_font=dict(size=_AXIS_TITLE - 2),
            tickfont=dict(size=_TICK_FONT - 2),
        ),
        "height": 390,
        "margin": dict(l=75, r=150, t=65, b=55),
    }
    fig.update_layout(**layout)
    return fig
