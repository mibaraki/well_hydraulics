# utils/i18n.py
# English / Japanese switch. The choice lives in st.session_state["lang_choice"],
# set by the radio button that Home.py draws at the top of the left sidebar.

import streamlit as st

LANG_KEY = "lang_choice"
OPTIONS = ["English", "日本語"]


def lang():
    """Return "ja" or "en"."""
    try:
        return "ja" if st.session_state.get(LANG_KEY) == "日本語" else "en"
    except Exception:          # used outside a running app (e.g. make_key.py)
        return "en"


def is_ja():
    return lang() == "ja"


def tr(en, ja=None):
    """Return the Japanese text when Japanese is selected (and one is given)."""
    return ja if (is_ja() and ja) else en


def language_switch():
    """English / Japanese radio at the top of the sidebar (call once, in Home.py)."""
    with st.sidebar:
        st.radio("Language / 言語", OPTIONS, key=LANG_KEY, horizontal=True)
