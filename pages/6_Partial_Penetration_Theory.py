"""6_Partial_Penetration_Theory.py — Theory of partially penetrating wells"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from scipy.special import exp1, k0
from scipy.integrate import quad

st.set_page_config(page_title="Partial Penetration Theory", page_icon="📚", layout="wide")
st.title("📚 Partial Penetration — Theory")

# ── 1. Physical Concept ──────────────────────────────────────────────────────
st.header("1. Physical Concept")
st.markdown("""
A **fully penetrating well** screens the entire aquifer thickness — flow to the well
is purely horizontal (radial). A **partially penetrating well** only screens part of
the aquifer, inducing **vertical flow components** near the well.

This additional vertical flow increases drawdown near the well compared to the
fully penetrating case. The effect becomes negligible at large distances:

> The correction is negligible when **r > 1.5 b √(Kₕ/Kᵥ)**

where b is the aquifer thickness and Kₕ/Kᵥ is the anisotropy ratio.

**Screen position parameters:**
- **b** — total aquifer thickness (m)
- **l** — depth to top of screen (m)
- **d** — depth to bottom of screen (m)
- **z** — depth of observation point (m)
""")

col1, col2 = st.columns(2)
with col1:
    st.markdown("**Fully penetrating:**")
    st.code("""
0 ──────────────── water table
  |=== screen ===|
  |=== screen ===|
  |=== screen ===|  ← full thickness b
  |=== screen ===|
b ──────────────── aquifer base
""", language=None)
with col2:
    st.markdown("**Partially penetrating:**")
    st.code("""
0 ──────────────── water table
  |    casing    |
l |=== screen ===|  ↑
  |=== screen ===|  screen length (d−l)
d |=== screen ===|  ↓
  |    open      |
b ──────────────── aquifer base
""", language=None)

# ── 2. Governing Equation ────────────────────────────────────────────────────
st.header("2. Governing Equation")
st.markdown("""
The 3D groundwater flow equation in cylindrical coordinates (r, z):
""")
st.latex(
    r"\frac{\partial^2 s}{\partial r^2} + "
    r"\frac{1}{r}\frac{\partial s}{\partial r} + "
    r"\frac{K_v}{K_h}\frac{\partial^2 s}{\partial z^2} = "
    r"\frac{S}{T}\frac{\partial s}{\partial t}"
)
st.markdown("""
Compared to the standard Theis equation (2D, radial flow only), the extra term
**Kᵥ/Kₕ · ∂²s/∂z²** captures the vertical flow component introduced by partial
penetration.
""")

# ── 3. Hantush (1961) Solution ───────────────────────────────────────────────
st.header("3. Hantush (1961) Solution")
st.markdown("The solution splits into a Theis part and a correction term:")
st.latex(r"s(r, z, t) = s_{Theis}(r,t) + s_{correction}(r, z, t)")

st.markdown("The Theis part:")
st.latex(r"s_{Theis} = \frac{Q}{4\pi T}\, W(u), \qquad u = \frac{r^2 S}{4Tt}")

st.markdown("The partial penetration correction:")
st.latex(
    r"s_{correction} = \frac{Qb}{2\pi^2 T(d-l)} "
    r"\sum_{n=1}^{\infty} \frac{1}{n} "
    r"\left[\sin\frac{n\pi d}{b} - \sin\frac{n\pi l}{b}\right] "
    r"\cos\frac{n\pi z}{b} \cdot W\!\left(u,\, \frac{n\pi r}{b}\right)"
)

# ── 4. Hantush Well Function W(u, β) ─────────────────────────────────────────
st.header("4. The Hantush Well Function W(u, β)")
st.latex(
    r"W(u, \beta) = \int_u^{\infty} \frac{1}{t} \exp\!\left(-t - \frac{\beta^2}{4t}\right) dt"
)
st.markdown("""
where β = nπr/b. Key properties:
- When **β → 0**: reduces to Theis W(u) = E₁(u)
- When **u → 0** (steady state): reduces to 2K₀(β)
- The extra factor exp(−β²/4t) damps early-time and large-r contributions
""")

st.latex(
    r"W(u, \beta) = \int_u^{\infty} \frac{e^{-t}}{t} \cdot e^{-\beta^2/4t}\, dt"
)

# ── 5. Fourier Series Decomposition ──────────────────────────────────────────
st.header("5. Fourier Series Decomposition")
st.markdown("Each term in the correction series has three components:")

df_fourier = pd.DataFrame({
    "Component": ["Screen geometry", "Vertical distribution", "Radial decay", "Amplitude"],
    "Expression": ["sin(nπd/b) − sin(nπl/b)", "cos(nπz/b)",
                   "W(u, nπr/b)", "1/n"],
    "Role": [
        "How much of Fourier mode n the screen intercepts",
        "Vertical variation of drawdown at observation depth z",
        "Transient radial decay of the nth mode",
        "Higher modes contribute less",
    ]
})
st.dataframe(df_fourier, use_container_width=True, hide_index=True)

# ── 6. Relationship W(u,β) and K₀(β) ─────────────────────────────────────────
st.header("6. Relationship Between W(u, β) and K₀(β)")
st.latex(
    r"K_0(\beta) = \frac{1}{2}\,W(0,\, \beta) = "
    r"\frac{1}{2}\lim_{u \to 0} W(u,\, \beta)"
)
st.markdown("""
- **K₀(β)** is the **steady-state limit** of W(u, β)
- Using W(u, β) gives the **full transient solution** — more accurate especially at early time
- At late time both converge to the same result
- Both solutions are derived from the same radial Bessel operator — K₀ is the physically
  required solution that decays to zero at r → ∞
""")

# ── 7. Convergence ────────────────────────────────────────────────────────────
st.header("7. Convergence of the Series")

# Interactive convergence demo
r_demo = st.slider("r/b ratio for convergence demo", 0.1, 3.0, 0.5, step=0.1)
u_demo = 0.01  # representative u value

rows = []
cumulative = 0.0
for n in range(1, 21):
    beta = n * np.pi * r_demo
    wu_b, _ = quad(lambda t: np.exp(-t - beta**2/(4*t))/t, u_demo, np.inf, limit=100)
    term_mag = abs((1/n) * wu_b)
    cumulative += term_mag
    rows.append({"n": n, "β = nπr/b": f"{beta:.2f}", "W(u,β)": f"{wu_b:.4e}",
                 "|term|": f"{term_mag:.4e}"})
    if n > 5 and term_mag < 1e-8:
        break

df_conv = pd.DataFrame(rows)
st.dataframe(df_conv, use_container_width=False, hide_index=True)
st.caption(f"At r/b = {r_demo:.1f}, u = {u_demo}. Series typically converges in 5–20 terms.")

# ── 8. Validity and Limitations ───────────────────────────────────────────────
st.header("8. Validity and Limitations")
st.markdown("""
- Correction is **negligible** when r > 1.5 b √(Kₕ/Kᵥ) — standard Theis suffices there
- Assumes **confined**, homogeneous, isotropic aquifer
- Screen must be fully within the aquifer: l ≥ 0, d ≤ b
- All standard Theis assumptions still apply (constant Q, infinite aquifer, etc.)
- The isotropic form shown here assumes Kₕ = Kᵥ; anisotropy can be incorporated
  by rescaling the vertical coordinate
""")

# ── 9. References ─────────────────────────────────────────────────────────────
st.header("9. References")
st.markdown("""
- Hantush, M.S. (1961). Aquifer tests on partially penetrating wells.
  *Journal of the Hydraulics Division*, ASCE, 87(5), 171–195.
- Hantush, M.S. (1964). Hydraulics of wells.
  *Advances in Hydroscience*, 1, 281–432.
- Kruseman, G.P. and de Ridder, N.A. (1994).
  *Analysis and Evaluation of Pumping Test Data* (2nd ed.). ILRI Publication 47.
""")
