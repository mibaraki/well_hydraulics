"""1_Theory.py — Theis equation theory and well function"""

import streamlit as st
import numpy as np
import plotly.graph_objects as go
from scipy.special import exp1
from utils.i18n import tr
from utils.plotting import plotly_chart_with_print

st.set_page_config(page_title=tr("Theory", "理論"), page_icon="📚", layout="wide")
st.title(tr("📚 Theis Equation — Theory", "📚 タイスの式 — 理論"))

# ── 1. Governing equation ────────────────────────────────────────────────────
st.header(tr("1. Governing Equation", "1. 支配方程式"))
st.markdown(tr("""
The Theis (1935) equation describes transient drawdown in a confined aquifer
due to a pumping well. It is derived from the radial groundwater flow equation:
""", """
タイス (1935) の式は、揚水井による被圧帯水層の非定常な水位低下量を表します。
放射状の地下水流動方程式から導かれます。
"""))
st.latex(
    r"\frac{\partial^2 s}{\partial r^2} + "
    r"\frac{1}{r}\frac{\partial s}{\partial r} = "
    r"\frac{S}{T}\frac{\partial s}{\partial t}"
)
st.markdown(tr("""
where **s** [L] is drawdown, **r** [L] is radial distance, **t** [T] is time,
**T** [L²/T] is transmissivity, and **S** [–] is storativity (dimensionless).
Dimensions are given in brackets: L = length, T = time.
""", """
ここで **s** [L] は水位低下量、**r** [L] は半径方向の距離、**t** [T] は時間、
**T** [L²/T] は透水量係数、**S** [–] は貯留係数（無次元）です。
次元は括弧内に示します（L = 長さ、T = 時間）。
"""))

# ── 2. Theis solution ────────────────────────────────────────────────────────
st.header(tr("2. Theis Solution", "2. タイスの解"))
col1, col2 = st.columns(2)
with col1:
    st.latex(r"s(r,t) = \frac{Q}{4\pi T}\, W(u)")
with col2:
    st.latex(r"u = \frac{r^2 S}{4Tt}")
st.markdown(tr("""
**Q** [L³/T] is the pumping rate. **W(u)** is the Theis well function
(exponential integral E₁):
""", """
**Q** [L³/T] は揚水量です。**W(u)** はタイスの井戸関数（指数積分 E₁）です。
"""))
st.latex(r"W(u) = E_1(u) = \int_u^{\infty} \frac{e^{-t}}{t}\, dt")

# ── 3. W(u) table ────────────────────────────────────────────────────────────
st.header(tr("3. Well Function W(u) Values", "3. 井戸関数 W(u) の値"))
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
    font=dict(family="Helvetica, Arial, sans-serif", size=17),
    title=dict(text=tr("Theis Well Function W(u)", "タイスの井戸関数 W(u)"), font=dict(size=22)),
    xaxis=dict(type="log", title="u", showgrid=True, gridcolor="#e0e0e0",
               title_font=dict(size=19), tickfont=dict(size=16)),
    yaxis=dict(type="log", title="W(u)", showgrid=True, gridcolor="#e0e0e0",
               title_font=dict(size=19), tickfont=dict(size=16)),
    legend=dict(x=0.02, y=0.05),
    margin=dict(l=85, r=35, t=75, b=85),
    height=700,
)
plotly_chart_with_print(fig, filename="well-function", use_container_width=True)

# ── 4. Method of Superposition ──────────────────────────────────────────────────────
st.header(tr("4. Method of Superposition", "4. 重ね合わせ法"))
st.markdown(tr("""
Boundary conditions are handled by superposing a **real pumping well** with an
**image well** mirrored across the boundary. The image well sign determines the
boundary type:

| Boundary | Image well | Effect on drawdown |
|---|---|---|
| Constant-head (river, lake) | Injection −Q | Less than Theis at late time |
| No-flow (fault, barrier) | Pumping +Q | Greater than Theis at late time |

The distance from the image well to the observation point is:
""", """
境界条件は、**実際の揚水井**と、境界を挟んで鏡像の位置に置いた**鏡像井戸（イメージ・ウェル）**を重ね合わせて扱います。
鏡像井戸の符号によって境界の種類が決まります。

| 境界 | 鏡像井戸 | 水位低下量への影響 |
|---|---|---|
| 定水頭境界（河川・湖） | 注水 −Q | 後期にタイス式より小さい |
| 不透水境界（断層・遮水壁） | 揚水 +Q | 後期にタイス式より大きい |

鏡像井戸から観測点までの距離は次のとおりです。
"""))
st.latex(
    r"r' = \sqrt{(x_{obs} - 2a)^2 + y_{obs}^2}"
)
st.markdown(tr("""
where **a** is the distance from the pumping well to the boundary, and
(x_obs, y_obs) = (r cosθ, r sinθ) are the observation point coordinates.

The total drawdown is then:
""", """
ここで **a** は揚水井から境界までの距離、(x_obs, y_obs) = (r cosθ, r sinθ) は観測点の座標です。

合計の水位低下量は次のとおりです。
"""))
col1, col2 = st.columns(2)
with col1:
    st.markdown(tr("**River (constant-head):**", "**河川（定水頭）:**"))
    st.latex(r"s = \frac{Q}{4\pi T}\left[W(u) - W(u')\right]")
with col2:
    st.markdown(tr("**Barrier (no-flow):**", "**不透水境界:**"))
    st.latex(r"s = \frac{Q}{4\pi T}\left[W(u) + W(u')\right]")

st.markdown(tr("where u = r²S/4Tt and u' = r'²S/4Tt.", "ここで u = r²S/4Tt、u' = r'²S/4Tt です。"))

# ── 5. Assumptions ───────────────────────────────────────────────────────────
st.header(tr("5. Key Assumptions", "5. 主な前提条件"))
st.markdown(tr("""
- Aquifer is **confined**, homogeneous, isotropic, and of infinite areal extent
- Well fully penetrates the aquifer (unless using the partial penetration page)
- Pumping rate **Q** is constant
- Aquifer is fully saturated before pumping; no dewatering occurs
- Well has infinitesimal diameter (no wellbore storage)
""", """
- 帯水層は**被圧**され、均質・等方で、水平方向に無限に広い
- 井戸は帯水層を完全に貫通している（部分貫入のページを除く）
- 揚水量 **Q** は一定
- 揚水前は完全に飽和しており、排水（水位が帯水層上端を下回ること）は起こらない
- 井戸の直径は無限小（井戸内貯留なし）
"""))

# ── 6. References ────────────────────────────────────────────────────────────
st.header(tr("6. References", "6. 参考文献"))
st.markdown("""
- Theis, C.V. (1935). The relation between the lowering of the piezometric surface
  and the rate and duration of discharge of a well using ground-water storage.
  *Transactions AGU*, 16, 519–524.
- Hantush, M.S. (1961). Aquifer tests on partially penetrating wells.
  *Journal of the Hydraulics Division*, ASCE, 87(5), 171–195.
- Kruseman, G.P. and de Ridder, N.A. (1994).
  *Analysis and Evaluation of Pumping Test Data* (2nd ed.). ILRI Publication 47.
""")
