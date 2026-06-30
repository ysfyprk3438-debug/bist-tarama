# surum 2
# -*- coding: utf-8 -*-
"""
APEX · Görsel Panel sayfası
Bağımsız sayfa (app.py'ye dokunmaz). gorsel_panel modülünü besler.
Varsayılan evren: BIST 100 (XU100). Her hisse için yönsüz okuma + sicil.
"""
import streamlit as st
import gorsel_panel as gp

st.set_page_config(page_title="APEX · Görsel Panel", layout="wide",
                   initial_sidebar_state="collapsed")

st.markdown("""
<style>
#MainMenu{visibility:hidden} header{visibility:hidden} footer{visibility:hidden}
.block-container{padding-top:1.2rem;padding-bottom:1rem;max-width:760px}
a.apexnav{display:inline-block;color:#8A93A0;text-decoration:none;font-size:13px;
  font-family:ui-monospace,monospace;border:1px solid #1E2530;border-radius:8px;
  padding:6px 12px;margin-bottom:6px}
a.apexnav:hover{color:#2DD4BF;border-color:#2DD4BF}
</style>
""", unsafe_allow_html=True)

st.markdown("<a class='apexnav' href='/' target='_self'>← APEX ana sayfa</a>",
            unsafe_allow_html=True)

# ── Hisse evreni: varsayılan tüm BIST100 ──
kodlar = gp.XU100

with st.expander(f"Hisse listesi · {len(gp.XU100)} BIST100 hissesi (özelleştir)", expanded=False):
    ozel = st.text_area(
        "Özel liste — boş bırakırsan tüm BIST100 gösterilir",
        value="", height=80,
        placeholder="THYAO, ASELS, AKBNK …")
    if ozel.strip():
        kodlar = [k.strip().upper() for k in ozel.replace(",", " ").split() if k.strip()]
    st.caption(f"{len(kodlar)} hisse · veri 15 dk önbellekli (yfinance) · "
               "ilk açılış 100 hisse için 30-60 sn sürebilir, sonra hızlı.")

if not kodlar:
    st.info("En az bir BIST kodu gir.")
else:
    with st.spinner(f"{len(kodlar)} hisse çekiliyor ve okumalar hesaplanıyor…"):
        gp.goster(kodlar)
