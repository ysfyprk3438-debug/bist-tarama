# surum 1
import streamlit as st
import streamlit.components.v1 as components
from pathlib import Path

st.set_page_config(page_title="APEX Sanal Borsa", layout="centered")

_html_path = Path(__file__).resolve().parent.parent / "apex_app.html"
try:
    _html = _html_path.read_text(encoding="utf-8")
    components.html(_html, height=880, scrolling=True)
except FileNotFoundError:
    st.error("apex_app.html bulunamadi. Depo kokune apex_app.html dosyasini ekle.")
