"""Home.py — Theis Groundwater Calculator App"""

import streamlit as st

st.set_page_config(
    page_title="Theis Groundwater Calculator",
    page_icon="💧",
    layout="wide",
)

st.title("💧 Theis Groundwater Calculator")
st.markdown(
    "An interactive multi-page app for confined aquifer drawdown analysis "
    "based on the **Theis (1935)** equation and its extensions."
)

st.divider()

col1, col2 = st.columns(2)

with col1:
    st.subheader("📚 Theory Pages")
    st.markdown("""
| Page | Content |
|---|---|
| **1 — Theory** | Theis equation, W(u), assumptions |
| **6 — Partial Penetration Theory** | Hantush (1961), W(u,β), K₀ |
""")

    st.subheader("🔧 Calculator Pages")
    st.markdown("""
| Page | Method |
|---|---|
| **2 — Single Well** | Standard Theis |
| **3 — Multiple Wells** | Superposition |
| **4 — River Boundary** | Method of images — injection well |
| **5 — No-Flow Barrier** | Method of images — pumping well |
| **7 — Partial Penetration** | Hantush (1961) W(u,β) |
| **8 — Parameter Estimation** | Least-squares curve fitting |
""")

with col2:
    st.subheader("📋 Common Assumptions")
    st.markdown("""
All calculators assume the aquifer is:
- **Confined** — fully saturated between two impermeable layers
- **Homogeneous and isotropic** — uniform properties in all directions
- **Infinite in areal extent** — no external boundaries (except where modelled)
- **Fully saturated** before pumping begins
- Pumped at a **constant rate** Q
- The pumping well has an **infinitesimally small diameter**

These are the classical **Theis (1935)** assumptions. Each calculator page notes
any additional assumptions specific to that method.
""")

    st.subheader("📁 Data Upload Format")
    st.markdown("""
All calculator pages accept measured drawdown data as a two-column file:

```
# time (min), drawdown (m)
10,  0.12
30,  0.45
60,  0.78
120, 1.05
```

Accepted formats: CSV, TXT. Comma, tab, or whitespace delimited.
Comment lines starting with `#` are skipped automatically.
""")

st.divider()
st.caption(
    "References: Theis (1935) Trans. AGU 16:519–524 · "
    "Hantush (1961) J. Hydraul. Div. ASCE 87(5):171–195 · "
    "Kruseman & de Ridder (1994) ILRI Publ. 47"
)
