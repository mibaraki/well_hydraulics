"""Home.py — entry point. Builds the page list for the free or pro edition.

Because this file calls st.navigation(), Streamlit ignores the pages/ folder's
automatic listing: a page that is not registered here cannot be opened, not even
by typing its URL. The free edition therefore never exposes the pro pages.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
from utils.license import is_pro_edition, is_pro_page

st.set_page_config(page_title="Theis Groundwater Calculator", page_icon="💧", layout="wide")

# (file, title, icon)
ALL_PAGES = [
    ("home_page.py",                       "Home",                       "💧"),
    ("pages/1_Theory.py",                  "Theory",                     "📚"),
    ("pages/2_Single_Well.py",             "Single Well",                "🔵"),
    ("pages/3_Multiple_Wells.py",          "Multiple Wells",             "🔵"),
    ("pages/4_River_Boundary.py",          "River Boundary",             "🌊"),
    ("pages/5_NoFlow_Barrier.py",          "No-Flow Barrier",            "🧱"),
    ("pages/6_Partial_Penetration_Theory.py", "Partial Penetration Theory", "📚"),
    ("pages/7_Partial_Penetration.py",     "Partial Penetration",        "🔵"),
    ("pages/8_Parameter_Estimation.py",    "Parameter Estimation",       "📈"),
]

pro = is_pro_edition()
pages = []
for path, title, icon in ALL_PAGES:
    if is_pro_page(path) and not pro:
        continue                       # free edition: page does not exist
    pages.append(st.Page(path, title=title, icon=icon,
                         default=(path == "home_page.py")))

st.navigation(pages).run()
