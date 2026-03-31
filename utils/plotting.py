# utils/plotting.py
# Shared Streamlit UI components and Plotly chart builders

import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go


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


# ── Chart builders ────────────────────────────────────────────────────────────

COLORS = {
    "theis":   "#1f77b4",
    "model":   "#2ca02c",
    "image":   "#ff7f0e",
    "data":    "#d62728",
    "grid":    "#e0e0e0",
}

LAYOUT_BASE = dict(
    paper_bgcolor="white",
    plot_bgcolor="white",
    font=dict(family="Helvetica, Arial, sans-serif", size=14, color="#222"),
    legend=dict(x=0.02, y=0.98, bgcolor="rgba(255,255,255,0.8)",
                bordercolor="#ccc", borderwidth=1),
    margin=dict(l=70, r=30, t=60, b=70),
)


def make_loglog_figure(title="Theis Drawdown — Log-Log"):
    """Return a base Plotly figure with log-log axes."""
    fig = go.Figure()
    fig.update_layout(
        **LAYOUT_BASE,
        title=dict(text=title, font=dict(size=18)),
        xaxis=dict(
            type="log", title="Time (min)",
            showgrid=True, gridcolor=COLORS["grid"],
            minor=dict(showgrid=True, gridcolor="#f0f0f0"),
            title_font=dict(size=16), tickfont=dict(size=13),
        ),
        yaxis=dict(
            type="log", title="Drawdown (m)",
            showgrid=True, gridcolor=COLORS["grid"],
            minor=dict(showgrid=True, gridcolor="#f0f0f0"),
            title_font=dict(size=16), tickfont=dict(size=13),
        ),
    )
    return fig


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


# ── Geometry diagram (plan view for image-well pages) ─────────────────────────

def render_geometry_diagram(r, theta_deg, a, x_obs, y_obs, r_image,
                             boundary_label="Boundary", image_label="Image well"):
    """
    Plan-view geometry diagram for river / barrier pages.
    """
    theta = np.radians(theta_deg)

    fig = go.Figure()

    # Boundary line
    fig.add_shape(
        type="line", x0=a, x1=a,
        y0=-max(r, a) * 1.3, y1=max(r, a) * 1.3,
        line=dict(color="#4a90d9", width=2, dash="dash")
    )
    fig.add_annotation(
        x=a, y=max(r, a) * 1.2, text=boundary_label,
        showarrow=False, font=dict(color="#4a90d9", size=12)
    )

    # Image well
    fig.add_trace(go.Scatter(
        x=[2 * a], y=[0], mode="markers+text",
        marker=dict(symbol="circle-open", size=14, color="#ff7f0e",
                    line=dict(width=2)),
        text=[image_label], textposition="top center",
        textfont=dict(size=11, color="#ff7f0e"),
        name=image_label, showlegend=False
    ))

    # Pumping well
    fig.add_trace(go.Scatter(
        x=[0], y=[0], mode="markers+text",
        marker=dict(symbol="circle", size=14, color="#1f77b4"),
        text=["Pump"], textposition="top center",
        textfont=dict(size=11, color="#1f77b4"),
        name="Pumping well", showlegend=False
    ))

    # Observation point
    valid = x_obs < a
    obs_color = "#2ca02c" if valid else "#d62728"
    fig.add_trace(go.Scatter(
        x=[x_obs], y=[y_obs], mode="markers+text",
        marker=dict(symbol="star", size=14, color=obs_color),
        text=["Obs"], textposition="top center",
        textfont=dict(size=11, color=obs_color),
        name="Observation point", showlegend=False
    ))

    # Lines: pump → obs, pump → image
    fig.add_trace(go.Scatter(
        x=[0, x_obs], y=[0, y_obs], mode="lines",
        line=dict(color="#2ca02c", width=1.5, dash="dot"),
        showlegend=False
    ))
    fig.add_trace(go.Scatter(
        x=[x_obs, 2 * a], y=[y_obs, 0], mode="lines",
        line=dict(color="#ff7f0e", width=1.5, dash="dot"),
        showlegend=False
    ))

    # Labels r and r_image
    mid_x = x_obs / 2
    mid_y = y_obs / 2
    fig.add_annotation(x=mid_x, y=mid_y, text=f"r={r:.0f}m",
                       showarrow=False, font=dict(size=10, color="#2ca02c"))
    mid_x2 = (x_obs + 2 * a) / 2
    mid_y2 = y_obs / 2
    fig.add_annotation(x=mid_x2, y=mid_y2, text=f"r'={r_image:.0f}m",
                       showarrow=False, font=dict(size=10, color="#ff7f0e"))

    span = max(r, a, abs(y_obs)) * 1.4 + 10
    fig.update_layout(
        **LAYOUT_BASE,
        title="Plan View — Well & Boundary Geometry",
        xaxis=dict(title="x (m)", range=[-span * 0.3, max(2 * a, span)],
                   showgrid=True, gridcolor=COLORS["grid"]),
        yaxis=dict(title="y (m)", range=[-span, span],
                   showgrid=True, gridcolor=COLORS["grid"],
                   scaleanchor="x"),
        height=350,
    )
    return fig


# ── Cross-section diagram (for partial penetration) ───────────────────────────

def render_crosssection_diagram(b, l, d, z):
    """Vertical cross-section showing aquifer, screen, and observation depth."""
    fig = go.Figure()

    W = 1.0  # normalized width

    # Aquifer block
    fig.add_shape(type="rect", x0=0, x1=W, y0=0, y1=b,
                  fillcolor="#dbeeff", line=dict(color="#4a90d9", width=1.5))

    # Screen
    fig.add_shape(type="rect", x0=W * 0.3, x1=W * 0.7, y0=l, y1=d,
                  fillcolor="#1f77b4", line=dict(color="#1f77b4", width=0))
    fig.add_annotation(x=W * 0.5, y=(l + d) / 2, text="Screen",
                       showarrow=False, font=dict(color="white", size=11))

    # Well casing
    fig.add_shape(type="rect", x0=W * 0.42, x1=W * 0.58, y0=d, y1=b,
                  fillcolor="#999", line=dict(color="#666", width=1))

    # Depth labels
    for depth, label in [(0, "b (base)"), (b, "Water table"), (l, f"l={l:.1f}m"), (d, f"d={d:.1f}m")]:
        fig.add_annotation(x=W + 0.05, y=depth, text=label,
                           showarrow=False, xanchor="left",
                           font=dict(size=10, color="#444"))
        fig.add_shape(type="line", x0=0, x1=W + 0.04, y0=depth, y1=depth,
                      line=dict(color="#aaa", width=1, dash="dot"))

    # Observation point
    if 0 <= z <= b:
        fig.add_trace(go.Scatter(
            x=[W * 0.85], y=[z], mode="markers+text",
            marker=dict(symbol="star", size=14, color="#d62728"),
            text=[f"Obs z={z:.1f}m"], textposition="middle right",
            textfont=dict(size=10, color="#d62728"),
            showlegend=False
        ))

    fig.update_layout(
        **LAYOUT_BASE,
        title="Vertical Cross-Section",
        xaxis=dict(showticklabels=False, showgrid=False,
                   range=[-0.1, W + 0.5], zeroline=False),
        yaxis=dict(title="Depth (m)", autorange="reversed",
                   showgrid=False, tickfont=dict(size=11)),
        height=350,
        margin=dict(l=60, r=120, t=50, b=40),
    )
    return fig
