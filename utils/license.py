# utils/license.py
# Edition switch (free / pro) and signed one-year license keys.
#
# A license key is   THEIS.<payload>.<signature>   (both base64url)
#   payload   = JSON {"v":1, "id":..., "c": customer, "e": "YYYY-MM-DD" (last valid day)}
#   signature = Ed25519 signature of the payload, made with YOUR private key
#               (make_key.py, kept on your own computer).
# The app only holds the PUBLIC key, which can check signatures but not make them.
#
# Settings (environment variable, or Streamlit secrets of the same name):
#   EDITION             "free" (default) or "pro"
#   LICENSE_PUBLIC_KEY  public key printed by `python make_key.py --init`
#   REVOKED_IDS         optional, comma-separated key ids that must stop working

import base64
import json
import os
from datetime import date, datetime

import streamlit as st

from utils.i18n import tr

PREFIX = "THEIS"

# Pages that need a license. Everything else is free.
# Names are the file names in pages/.
PRO_PAGES = {
    "3_Multiple_Wells.py",
    "4_River_Boundary.py",
    "5_NoFlow_Barrier.py",
    "6_Partial_Penetration_Theory.py",
    "7_Partial_Penetration.py",
    "8_Parameter_Estimation.py",
}

_SESSION_KEY = "license_key_text"


# ── settings ──────────────────────────────────────────────────────────────────
def _setting(name, default=""):
    """Environment variable first, then Streamlit secrets, then default."""
    val = os.environ.get(name)
    if val:
        return val.strip()
    try:
        val = st.secrets.get(name, "")
    except Exception:          # no secrets file at all
        val = ""
    return str(val).strip() if val else default


def get_edition():
    ed = _setting("EDITION", "free").lower()
    return "pro" if ed == "pro" else "free"


def is_pro_edition():
    return get_edition() == "pro"


def is_pro_page(filename):
    return os.path.basename(filename) in PRO_PAGES


# ── key checking ──────────────────────────────────────────────────────────────
def _b64d(s):
    s = s.strip()
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def verify_key(key_text, public_key_b64=None, today=None, revoked=None):
    """
    Check a license key.

    Returns (ok, info, message). `info` is the payload dict when the signature
    is genuine (even if the key is expired or revoked), else {}.
    """
    from cryptography.exceptions import InvalidSignature
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

    today = today or date.today()
    pub = public_key_b64 if public_key_b64 is not None else _setting("LICENSE_PUBLIC_KEY")
    if not pub:
        return False, {}, tr("This server has no license public key configured.", "このサーバーにはライセンス公開鍵が設定されていません。")
    if revoked is None:
        revoked = {x.strip() for x in _setting("REVOKED_IDS").split(",") if x.strip()}

    try:
        prefix, payload_b64, sig_b64 = key_text.strip().split(".")
        if prefix != PREFIX:
            raise ValueError("bad prefix")
        payload_bytes = _b64d(payload_b64)
        Ed25519PublicKey.from_public_bytes(_b64d(pub)).verify(_b64d(sig_b64), payload_bytes)
        info = json.loads(payload_bytes)
        expiry = datetime.strptime(info["e"], "%Y-%m-%d").date()
    except (ValueError, KeyError, InvalidSignature, TypeError):
        return False, {}, tr("This license key is not valid. Check that it was copied completely.", "このライセンスキーは無効です。キー全体が正しくコピーされているか確認してください。")

    if info.get("id") in revoked:
        return False, info, tr("This license key has been revoked. Please contact the seller.", "このライセンスキーは失効しています。販売元にお問い合わせください。")
    if today > expiry:
        return False, info, tr(f"This license key expired on {expiry:%Y-%m-%d}. Please renew it.", f"このライセンスキーは {expiry:%Y-%m-%d} に有効期限が切れました。更新してください。")
    return True, info, tr(f"Licensed to {info.get('c', '?')} · valid through {expiry:%Y-%m-%d}", f"ライセンス名義: {info.get('c', '?')} · {expiry:%Y-%m-%d} まで有効")


# ── Streamlit UI ──────────────────────────────────────────────────────────────
def _license_box(label_visible=True):
    """Key entry box. Returns (ok, info, message) for the stored key."""
    stored = st.session_state.get(_SESSION_KEY, "")
    entered = st.text_input(
        tr("License key", "ライセンスキー"), value=stored, type="password", key="license_key_input",
        placeholder="THEIS.…", label_visibility="visible" if label_visible else "collapsed")
    entered = entered.strip()
    st.session_state[_SESSION_KEY] = entered
    if not entered:
        return False, {}, ""
    return verify_key(entered)


def license_status_sidebar():
    """Small license panel for the sidebar of the Home page (pro edition only)."""
    if not is_pro_edition():
        return
    with st.sidebar:
        st.markdown(tr("### 🔑 License", "### 🔑 ライセンス"))
        ok, _, msg = _license_box()
        if ok:
            st.success(msg)
        elif msg:
            st.error(msg)
        else:
            st.info(tr("Enter your license key to unlock all pages.", "ライセンスキーを入力すると、すべてのページが使えます。"))


def require_license():
    """
    Call at the top of every pro page, right after st.set_page_config().
    Stops the page unless this is the pro edition AND a valid key is entered.
    """
    if not is_pro_edition():
        st.title(tr("🔒 Pro feature", "🔒 Pro 版の機能"))
        st.info(tr("This page is part of the Pro edition and is not available in the "
                   "free version.", "このページは Pro 版の機能で、無料版では利用できません。"))
        st.stop()

    ok, _, msg = verify_key(st.session_state.get(_SESSION_KEY, "")) \
        if st.session_state.get(_SESSION_KEY) else (False, {}, "")
    if ok:
        with st.sidebar:
            st.caption(f"🔑 {msg}")
        return

    st.title(tr("🔑 License required", "🔑 ライセンスが必要です"))
    st.write(tr("Enter your license key to use this page. The key is kept only for "
                "this browser session.",
                "このページを使うにはライセンスキーを入力してください。キーはこのブラウザのセッション中だけ保持されます。"))
    ok, _, msg = _license_box()
    if ok:
        st.rerun()
    if msg:
        st.error(msg)
    st.stop()
