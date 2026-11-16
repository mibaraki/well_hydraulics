"""home_page.py — landing page (shown by the Home.py router)"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
from utils.i18n import tr
from utils.license import is_pro_edition, license_status_sidebar

st.set_page_config(
    page_title=tr("Theis Groundwater Calculator", "テイス式 地下水計算ツール"),
    page_icon="💧",
    layout="wide",
)

license_status_sidebar()

st.title(tr("💧 Theis Groundwater Calculator", "💧 テイス式 地下水計算ツール"))
st.markdown(tr(
    "An interactive multi-page app for confined aquifer drawdown analysis "
    "based on the **Theis (1935)** equation and its extensions.",
    "**テイス (1935)** の式とその拡張にもとづく、被圧帯水層の水位低下量を解析する"
    "対話型のマルチページアプリです。"))

if not is_pro_edition():
    st.info(tr("You are using the **free edition**. Pages marked ⭐ belong to the Pro "
               "edition (one-year license).",
               "現在は**無料版**です。⭐ の付いたページは Pro 版（1 年ライセンス）の機能です。"))

st.divider()

col1, col2 = st.columns(2)

with col1:
    st.subheader(tr("📚 Theory Pages", "📚 理論ページ"))
    st.markdown(tr("""
| Page | Content |
|---|---|
| **1 — Theory** | Theis equation, W(u), assumptions |
| **6 — Partial Penetration Theory** ⭐ | Hantush (1961), W(u,β), K₀ |
""", """
| ページ | 内容 |
|---|---|
| **1 — 理論** | テイスの式、W(u)、前提条件 |
| **6 — 部分貫入井の理論** ⭐ | Hantush (1961)、W(u,β)、K₀ |
"""))

    st.subheader(tr("🔧 Calculator Pages", "🔧 計算ページ"))
    st.markdown(tr("""
| Page | Method |
|---|---|
| **2 — Single Well** | Standard Theis |
| **3 — Multiple Wells** ⭐ | Superposition |
| **4 — River Boundary** ⭐ | Method of images — injection well |
| **5 — No-Flow Barrier** ⭐ | Method of images — pumping well |
| **7 — Partial Penetration** ⭐ | Hantush (1961) W(u,β) |
| **8 — Parameter Estimation** ⭐ | Least-squares curve fitting |
""", """
| ページ | 手法 |
|---|---|
| **2 — 単一井戸** | 標準テイス式 |
| **3 — 複数井戸** ⭐ | 重ね合わせ |
| **4 — 河川境界** ⭐ | 影像法 — 注水の影像井戸 |
| **5 — 不透水境界** ⭐ | 影像法 — 揚水の影像井戸 |
| **7 — 部分貫入井** ⭐ | Hantush (1961) W(u,β) |
| **8 — パラメータ推定** ⭐ | 最小二乗法による曲線あてはめ |
"""))

with col2:
    st.subheader(tr("📋 Common Assumptions", "📋 共通の前提条件"))
    st.markdown(tr("""
All calculators assume the aquifer is:
- **Confined** — fully saturated between two impermeable layers
- **Homogeneous and isotropic** — uniform properties in all directions
- **Infinite in areal extent** — no external boundaries (except where modelled)
- **Fully saturated** before pumping begins
- Pumped at a **constant rate** Q
- The pumping well has an **infinitesimally small diameter**

These are the classical **Theis (1935)** assumptions. Each calculator page notes
any additional assumptions specific to that method.
""", """
すべての計算で、帯水層は次のとおりと仮定します。
- **被圧**されている — 2 枚の不透水層に挟まれ、完全に飽和している
- **均質・等方** — どの方向にも性質が一様
- **水平方向に無限に広い** — 外側の境界はない（モデル化したものを除く）
- 揚水開始前は**完全に飽和**している
- **一定の揚水量** Q で揚水する
- 揚水井の**直径は無限小**とする

これらは**テイス (1935)** の古典的な前提条件です。各ページには、その手法に固有の追加の前提条件も記載しています。
"""))

    st.subheader(tr("📁 Data Upload Format", "📁 データのアップロード形式"))
    st.markdown(tr("""
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
""", """
どの計算ページでも、水位低下量の観測データを 2 列のファイルで読み込めます。

```
# time (min), drawdown (m)
10,  0.12
30,  0.45
60,  0.78
120, 1.05
```

対応形式: CSV、TXT（区切りはカンマ、タブ、空白のいずれも可）。
`#` で始まる行はコメントとして自動的に無視されます。
"""))

st.divider()
st.caption(
    "References: Theis (1935) Trans. AGU 16:519–524 · "
    "Hantush (1961) J. Hydraul. Div. ASCE 87(5):171–195 · "
    "Kruseman & de Ridder (1994) ILRI Publ. 47"
)
