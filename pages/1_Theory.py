"""1_Theory.py — Theis equation theory and well function"""

import streamlit as st
import numpy as np
import plotly.graph_objects as go
from scipy.special import exp1

st.set_page_config(page_title="Theory", page_icon="📚", layout="wide")
st.title("📚 Theis Equation — Theory")

# ── 1. Governing equation ────────────────────────────────────────────────────
st.header("1. Governing Equation")
st.markdown("""
The Theis (1935) equation describes transient drawdown in a confined aquifer
due to a pumping well. It is derived from the radial groundwater flow equation:
""")
st.latex(
    r"\frac{\partial^2 s}{\partial r^2} + "
    r"\frac{1}{r}\frac{\partial s}{\partial r} = "
    r"\frac{S}{T}\frac{\partial s}{\partial t}"
)
st.markdown("""
where **s** (m) is drawdown, **r** (m) is radial distance, **t** (day) is time,
**T** (m²/day) is transmissivity, and **S** (–) is storativity.
""")

# ── 2. Theis solution ────────────────────────────────────────────────────────
st.header("2. Theis Solution")
col1, col2 = st.columns(2)
with col1:
    st.latex(r"s(r,t) = \frac{Q}{4\pi T}\, W(u)")
with col2:
    st.latex(r"u = \frac{r^2 S}{4Tt}")
st.markdown("""
**Q** (m³/day) is the pumping rate. **W(u)** is the Theis well function
(exponential integral E₁):
""")
st.latex(r"W(u) = E_1(u) = \int_u^{\infty} \frac{e^{-t}}{t}\, dt")

# ── 3. W(u) table ────────────────────────────────────────────────────────────
st.header("3. Well Function W(u) Values")
u_vals = [1e-4, 1e-3, 0.01, 0.05, 0.1, 0.2, 0.5, 1.0, 2.0, 5.0, 10.0]
wu_vals = [float(exp1(u)) for u in u_vals]

import pandas as pd
df_wu = pd.DataFrame({"u": u_vals, "W(u)": [f"{w:.4f}" for w in wu_vals]})
st.dataframe(df_wu, use_container_width=False, hide_index=True)

# W(u) plot
u_plot = np.logspace(-4, 1, 200)
wu_plot = exp1(u_plot)
fig = go.Figure()
fig.add_trace(go.Scatter(
    x=u_plot, y=wu_plot, mode="lines",
    line=dict(color="#1f77b4", width=2.5), name="W(u)"
))
fig.update_layout(
    paper_bgcolor="white", plot_bgcolor="white",
    font=dict(family="Helvetica, Arial, sans-serif", size=14),
    title="Theis Well Function W(u)",
    xaxis=dict(type="log", title="u", showgrid=True, gridcolor="#e0e0e0",
               title_font=dict(size=15), tickfont=dict(size=12)),
    yaxis=dict(type="log", title="W(u)", showgrid=True, gridcolor="#e0e0e0",
               title_font=dict(size=15), tickfont=dict(size=12)),
    legend=dict(x=0.02, y=0.05),
    margin=dict(l=60, r=30, t=50, b=60),
)
st.plotly_chart(fig, use_container_width=True)

# ── 4. Method of Images ──────────────────────────────────────────────────────
st.header("4. Method of Images")
st.markdown("""
Boundary conditions are handled by superposing a **real pumping well** with an
**image well** mirrored across the boundary. The image well sign determines the
boundary type:

| Boundary | Image well | Effect on drawdown |
|---|---|---|
| Constant-head (river, lake) | Injection −Q | Less than Theis at late time |
| No-flow (fault, barrier) | Pumping +Q | Greater than Theis at late time |

The distance from the image well to the observation point is:
""")
st.latex(
    r"r' = \sqrt{(x_{obs} - 2a)^2 + y_{obs}^2}"
)
st.markdown("""
where **a** is the distance from the pumping well to the boundary, and
(x_obs, y_obs) = (r cosθ, r sinθ) are the observation point coordinates.

The total drawdown is then:
""")
col1, col2 = st.columns(2)
with col1:
    st.markdown("**River (constant-head):**")
    st.latex(r"s = \frac{Q}{4\pi T}\left[W(u) - W(u')\right]")
with col2:
    st.markdown("**Barrier (no-flow):**")
    st.latex(r"s = \frac{Q}{4\pi T}\left[W(u) + W(u')\right]")

st.markdown("where u = r²S/4Tt and u' = r'²S/4Tt.")

# ── 5. Assumptions ───────────────────────────────────────────────────────────
st.header("5. Key Assumptions")
st.markdown("""
- Aquifer is **confined**, homogeneous, isotropic, and of infinite areal extent
- Well fully penetrates the aquifer (unless using the partial penetration page)
- Pumping rate **Q** is constant
- Aquifer is fully saturated before pumping; no dewatering occurs
- Well has infinitesimal diameter (no wellbore storage)
""")

# ── 6. References ────────────────────────────────────────────────────────────
st.header("6. References")
st.markdown("""
- Theis, C.V. (1935). The relation between the lowering of the piezometric surface
  and the rate and duration of discharge of a well using ground-water storage.
  *Transactions AGU*, 16, 519–524.
- Hantush, M.S. (1961). Aquifer tests on partially penetrating wells.
  *Journal of the Hydraulics Division*, ASCE, 87(5), 171–195.
- Kruseman, G.P. and de Ridder, N.A. (1994).
  *Analysis and Evaluation of Pumping Test Data* (2nd ed.). ILRI Publication 47.
""")
