"""Home.py — entry point. Builds the page list for the free or pro edition.

Because this file calls st.navigation(), Streamlit ignores the pages/ folder's
automatic listing: a page that is not registered here cannot be opened, not even
by typing its URL. The free edition therefore never exposes the pro pages.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
from utils.i18n import tr, language_switch
from utils.license import is_pro_edition, is_pro_page

st.set_page_config(page_title=tr("Theis Groundwater Calculator", "テイス式 地下水計算ツール"),
                   page_icon="💧", layout="wide")

# (file, English title, Japanese title, icon, url slug)
ALL_PAGES = [
    ("home_page.py",                          "Home",                      "ホーム",             "💧", ""),
    ("pages/1_Theory.py",                     "Theory",                    "理論",               "📚", "theory"),
    ("pages/2_Single_Well.py",                "Single Well",               "単一井戸",           "🔵", "single-well"),
    ("pages/3_Multiple_Wells.py",             "Multiple Wells",            "複数井戸",           "🔵", "multiple-wells"),
    ("pages/4_River_Boundary.py",             "River Boundary",            "河川境界",           "🌊", "river-boundary"),
    ("pages/5_NoFlow_Barrier.py",             "No-Flow Barrier",           "不透水境界",         "🧱", "no-flow-barrier"),
    ("pages/6_Partial_Penetration_Theory.py", "Partial Penetration Theory", "部分貫入井の理論",   "📚", "partial-penetration-theory"),
    ("pages/7_Partial_Penetration.py",        "Partial Penetration",       "部分貫入井",         "🔵", "partial-penetration"),
    ("pages/8_Parameter_Estimation.py",       "Parameter Estimation",      "パラメータ推定",     "📈", "parameter-estimation"),
]

pro = is_pro_edition()
pages = []
for path, en, ja, icon, slug in ALL_PAGES:
    if is_pro_page(path) and not pro:
        continue                       # free edition: page does not exist
    kwargs = dict(title=tr(en, ja), icon=icon)
    if slug:
        kwargs["url_path"] = slug
    else:
        kwargs["default"] = True
    pages.append(st.Page(path, **kwargs))

nav = st.navigation(pages)
language_switch()                      # English / 日本語 switch, left sidebar
nav.run()
