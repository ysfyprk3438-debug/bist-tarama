# surum 1
# -*- coding: utf-8 -*-
"""
APEX · Görsel Panel sayfası
Bağımsız sayfa (app.py'ye dokunmaz). gorsel_panel modülünü besler.
Hisse evrenini kullanıcı seçer; panel her hisse için yönsüz okuma + sicil üretir.
"""
import streamlit as st
import gorsel_panel as gp

st.set_page_config(page_title="APEX · Görsel Panel", layout="wide",
                   initial_sidebar_state="collapsed")

# menü/header/footer gizle (APEX tutarlılığı)
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

# ── Hisse evreni ──
VARSAYILAN = ["THYAO", "ASELS", "AKBNK", "GARAN", "SISE", "EREGL",
              "KCHOL", "FROTO", "TUPRS", "BIMAS", "SAHOL", "PGSUS"]

with st.expander("Hisse listesini düzenle", expanded=False):
    secim = st.text_area(
        "BIST kodları (virgül veya boşlukla ayır)",
        value=", ".join(VARSAYILAN),
        height=70,
        help="Örn: THYAO, ASELS, AKBNK")
    kodlar = [k.strip().upper() for k in secim.replace(",", " ").split() if k.strip()]
    st.caption(f"{len(kodlar)} hisse · veri 15 dk önbellekli (yfinance)")

if not kodlar:
    st.info("En az bir BIST kodu gir.")
else:
    with st.spinner("Veri çekiliyor ve okumalar hesaplanıyor…"):
        gp.goster(kodlar)
