"""6_Partial_Penetration_Theory.py — Theory of partially penetrating wells"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import plotly.graph_objects as go
from scipy.special import exp1, k0
from scipy.integrate import quad

from utils.i18n import tr

st.set_page_config(page_title=tr("Partial Penetration Theory", "部分貫入井の理論"), page_icon="📚", layout="wide")

from utils.license import require_license
require_license()   # Pro page: needs a valid license key
st.title(tr("📚 Partial Penetration — Theory", "📚 部分貫入井 — 理論"))

# ── 1. Physical Concept ──────────────────────────────────────────────────────
st.header(tr("1. Physical Concept", "1. 物理的な考え方"))
st.markdown(tr("""
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
""", """
**完全貫入井**は帯水層の全層厚にストレーナーがあり、井戸へ向かう流れは水平方向（放射状）だけです。
**部分貫入井**は帯水層の一部にしかストレーナーがないため、井戸の近くに**鉛直方向の流れ成分**が生じます。

この鉛直方向の流れによって、井戸の近くでは完全貫入の場合より水位低下量が大きくなります。
距離が離れると、この影響は無視できるほど小さくなります。

> **r > 1.5 b √(Kₕ/Kᵥ)** のとき、補正は無視できます

ここで b は帯水層の厚さ、Kₕ/Kᵥ は異方性比です。

**ストレーナー位置のパラメータ:**
- **b** — 帯水層の全層厚 (m)
- **l** — ストレーナー上端の深さ (m)
- **d** — ストレーナー下端の深さ (m)
- **z** — 観測点の深さ (m)
"""))

col1, col2 = st.columns(2)
with col1:
    st.markdown(tr("**Fully penetrating:**", "**完全貫入:**"))
    st.code(tr("""
0 ──────────────── water table
  |=== screen ===|
  |=== screen ===|
  |=== screen ===|  ← full thickness b
  |=== screen ===|
b ──────────────── aquifer base
""", """
0 ──────────────── 地下水面
  |= ストレーナー =|
  |= ストレーナー =|
  |= ストレーナー =|  ← 全層厚 b
  |= ストレーナー =|
b ──────────────── 帯水層の底面
"""), language=None)
with col2:
    st.markdown(tr("**Partially penetrating:**", "**部分貫入:**"))
    st.code(tr("""
0 ──────────────── water table
  |    casing    |
l |=== screen ===|  ↑
  |=== screen ===|  screen length (d−l)
d |=== screen ===|  ↓
  |    open      |
b ──────────────── aquifer base
""", """
0 ──────────────── 地下水面
  |  ケーシング  |
l |= ストレーナー =|  ↑
  |= ストレーナー =|  ストレーナー長 (d−l)
d |= ストレーナー =|  ↓
  |    裸孔      |
b ──────────────── 帯水層の底面
"""), language=None)

# ── 2. Governing Equation ────────────────────────────────────────────────────
st.header(tr("2. Governing Equation", "2. 支配方程式"))
st.markdown(tr("""
The 3D groundwater flow equation in cylindrical coordinates (r, z):
""", """
円筒座標 (r, z) で表した 3 次元の地下水流動方程式:
"""))
st.latex(
    r"\frac{\partial^2 s}{\partial r^2} + "
    r"\frac{1}{r}\frac{\partial s}{\partial r} + "
    r"\frac{K_v}{K_h}\frac{\partial^2 s}{\partial z^2} = "
    r"\frac{S}{T}\frac{\partial s}{\partial t}"
)
st.markdown(tr("""
Compared to the standard Theis equation (2D, radial flow only), the extra term
**Kᵥ/Kₕ · ∂²s/∂z²** captures the vertical flow component introduced by partial
penetration.
""", """
標準のテイスの式（2 次元、放射状の流れのみ）と比べて、追加の項
**Kᵥ/Kₕ · ∂²s/∂z²** が、部分貫入によって生じる鉛直方向の流れ成分を表します。
"""))

# ── 3. Hantush (1961) Solution ───────────────────────────────────────────────
st.header(tr("3. Hantush (1961) Solution", "3. Hantush (1961) の解"))
st.markdown(tr("The solution splits into a Theis part and a correction term:", "解は、テイス項と補正項に分けられます。"))
st.latex(r"s(r, z, t) = s_{Theis}(r,t) + s_{correction}(r, z, t)")

st.markdown(tr("The Theis part:", "テイス項:"))
st.latex(r"s_{Theis} = \frac{Q}{4\pi T}\, W(u), \qquad u = \frac{r^2 S}{4Tt}")

st.markdown(tr("The partial penetration correction:", "部分貫入の補正項:"))
st.latex(
    r"s_{correction} = \frac{Qb}{2\pi^2 T(d-l)} "
    r"\sum_{n=1}^{\infty} \frac{1}{n} "
    r"\left[\sin\frac{n\pi d}{b} - \sin\frac{n\pi l}{b}\right] "
    r"\cos\frac{n\pi z}{b} \cdot W\!\left(u,\, \frac{n\pi r}{b}\right)"
)

# ── 4. Hantush Well Function W(u, β) ─────────────────────────────────────────
st.header(tr("4. The Hantush Well Function W(u, β)", "4. Hantush の井戸関数 W(u, β)"))
st.latex(
    r"W(u, \beta) = \int_u^{\infty} \frac{1}{t} \exp\!\left(-t - \frac{\beta^2}{4t}\right) dt"
)
st.markdown(tr("""
where β = nπr/b. Key properties:
- When **β → 0**: reduces to Theis W(u) = E₁(u)
- When **u → 0** (steady state): reduces to 2K₀(β)
- The extra factor exp(−β²/4t) damps early-time and large-r contributions
""", """
ここで β = nπr/b です。主な性質:
- **β → 0** のとき、テイスの W(u) = E₁(u) に一致する
- **u → 0**（定常状態）のとき、2K₀(β) に一致する
- 追加の因子 exp(−β²/4t) が、初期の寄与と r が大きい場合の寄与を減衰させる
"""))

st.latex(
    r"W(u, \beta) = \int_u^{\infty} \frac{e^{-t}}{t} \cdot e^{-\beta^2/4t}\, dt"
)

# ── 5. Fourier Series Decomposition ──────────────────────────────────────────
st.header(tr("5. Fourier Series Decomposition", "5. フーリエ級数展開"))
st.markdown(tr("Each term in the correction series has three components:", "補正項の級数の各項は、次の要素からなります。"))

df_fourier = pd.DataFrame({
    tr("Component", "要素"): [*tr(["Screen geometry", "Vertical distribution", "Radial decay", "Amplitude"],
                                  ["ストレーナーの形状", "鉛直方向の分布", "半径方向の減衰", "振幅"])],
    tr("Expression", "式"): ["sin(nπd/b) − sin(nπl/b)", "cos(nπz/b)",
                   "W(u, nπr/b)", "1/n"],
    tr("Role", "役割"): tr([
        "How much of Fourier mode n the screen intercepts",
        "Vertical variation of drawdown at observation depth z",
        "Transient radial decay of the nth mode",
        "Higher modes contribute less",
    ], [
        "ストレーナーがフーリエ第 n モードをどれだけ捉えるか",
        "観測深度 z での水位低下量の鉛直方向の変化",
        "第 n モードの非定常な半径方向の減衰",
        "高次のモードほど寄与が小さい",
    ])
})
st.dataframe(df_fourier, use_container_width=True, hide_index=True)

# ── 6. Relationship W(u,β) and K₀(β) ─────────────────────────────────────────
st.header(tr("6. Relationship Between W(u, β) and K₀(β)", "6. W(u, β) と K₀(β) の関係"))
st.latex(
    r"K_0(\beta) = \frac{1}{2}\,W(0,\, \beta) = "
    r"\frac{1}{2}\lim_{u \to 0} W(u,\, \beta)"
)
st.markdown(tr("""
- **K₀(β)** is the **steady-state limit** of W(u, β)
- Using W(u, β) gives the **full transient solution** — more accurate especially at early time
- At late time both converge to the same result
- Both solutions are derived from the same radial Bessel operator — K₀ is the physically
  required solution that decays to zero at r → ∞
""", """
- **K₀(β)** は W(u, β) の**定常状態での極限**です
- W(u, β) を使うと**完全な非定常解**が得られ、特に初期の精度が高くなります
- 後期には両者は同じ結果に収束します
- どちらも同じ放射状のベッセル演算子から導かれます。K₀ は r → ∞ でゼロに減衰するという物理的な条件を満たす解です
"""))

# ── 7. Convergence ────────────────────────────────────────────────────────────
st.header(tr("7. Convergence of the Series", "7. 級数の収束"))

# Interactive convergence demo
r_demo = st.slider(tr("r/b ratio for convergence demo", "収束の確認用の r/b 比"), 0.1, 3.0, 0.5, step=0.1)
u_demo = 0.01  # representative u value

rows = []
cumulative = 0.0
for n in range(1, 21):
    beta = n * np.pi * r_demo
    wu_b, _ = quad(lambda t: np.exp(-t - beta**2/(4*t))/t, u_demo, np.inf, limit=100)
    term_mag = abs((1/n) * wu_b)
    cumulative += term_mag
    rows.append({"n": n, "β = nπr/b": f"{beta:.2f}", "W(u,β)": f"{wu_b:.4e}",
                 tr("|term|", "|項|"): f"{term_mag:.4e}"})
    if n > 5 and term_mag < 1e-8:
        break

df_conv = pd.DataFrame(rows)
st.dataframe(df_conv, use_container_width=False, hide_index=True)
st.caption(tr(f"At r/b = {r_demo:.1f}, u = {u_demo}. The number of terms needed grows as r/b gets smaller: "
              "a handful near r/b ≈ 1, several tens near r/b ≈ 0.1.",
              f"r/b = {r_demo:.1f}、u = {u_demo} の場合。r/b が小さいほど必要な項数が増えます。"
              "r/b ≈ 1 付近では数項、r/b ≈ 0.1 付近では数十項が必要です。"))

# ── 8. Validity and Limitations ───────────────────────────────────────────────
st.header(tr("8. Validity and Limitations", "8. 適用範囲と限界"))
st.markdown(tr("""
- Correction is **negligible** when r > 1.5 b √(Kₕ/Kᵥ) — standard Theis suffices there
- Assumes **confined**, homogeneous, isotropic aquifer
- Screen must be fully within the aquifer: l ≥ 0, d ≤ b
- All standard Theis assumptions still apply (constant Q, infinite aquifer, etc.)
- The isotropic form shown here assumes Kₕ = Kᵥ; anisotropy can be incorporated
  by rescaling the vertical coordinate
""", """
- r > 1.5 b √(Kₕ/Kᵥ) のとき補正は**無視できる**ため、その範囲では標準のテイス式で十分です
- **被圧**・均質・等方の帯水層を仮定します
- ストレーナーは帯水層内に完全に収まる必要があります: l ≥ 0、d ≤ b
- テイスの標準的な前提条件（一定の Q、無限に広い帯水層など）はそのまま適用されます
- ここに示した等方の形式は Kₕ = Kᵥ を仮定しています。異方性は鉛直座標のスケール変換で取り込めます
"""))

# ── 9. References ─────────────────────────────────────────────────────────────
st.header(tr("9. References", "9. 参考文献"))
st.markdown("""
- Hantush, M.S. (1961). Aquifer tests on partially penetrating wells.
  *Journal of the Hydraulics Division*, ASCE, 87(5), 171–195.
- Hantush, M.S. (1964). Hydraulics of wells.
  *Advances in Hydroscience*, 1, 281–432.
- Kruseman, G.P. and de Ridder, N.A. (1994).
  *Analysis and Evaluation of Pumping Test Data* (2nd ed.). ILRI Publication 47.
""")
