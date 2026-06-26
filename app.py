# -*- coding: utf-8 -*-
"""
BIST PARA AVCISI — ANA UYGULAMA (native arayüz: Pro Analiz + Trade)
Onaylanan iki modlu native arayüzü Streamlit içine gömer, gerçek analiz çekirdeğinden besler.
Veri gelmezse demo veriyle açılır. Klasik tam sürüm: app_klasik.py
"""
import io
import datetime
import streamlit as st
import streamlit.components.v1 as components

import ui_app
import payload as pl
import rapor
from tarama_core import tara

st.set_page_config(page_title="BIST Para Avcısı", page_icon="🎯", layout="centered")
st.markdown("""
<style>
#MainMenu, footer, header {visibility:hidden;}
.block-container {padding:0 !important; max-width:520px !important;}
.stApp {background:#06070A;}
iframe {border:none !important;}
[data-testid="stSidebar"] {background:#0D1117;}
</style>
""", unsafe_allow_html=True)


@st.cache_data(ttl=900, show_spinner=False)
def _scan(vade_key, gecmis_n=0):
    try:
        return tara(vade_key)
    except Exception:
        return [], 0.0


@st.cache_data(ttl=900, show_spinner=False)
def _excel_bytes(vade_key):
    sonuclar, xu100 = _scan(vade_key)
    if not sonuclar:
        return None
    buf = io.BytesIO()
    rapor.excel_rapor(sonuclar, buf, xu100)
    return buf.getvalue()


VADE_ETIKET = {"gun_ici": "Gün İçi", "gunluk": "Günlük", "haftalik": "Haftalık", "aylik": "Aylık"}
with st.sidebar:
    st.markdown("### 🎯 BIST Para Avcısı")
    vade = st.selectbox("Vade", list(VADE_ETIKET.keys()), index=2, format_func=lambda k: VADE_ETIKET[k])
    if st.button("🔄 Yeniden tara"):
        st.cache_data.clear()
    st.divider()
    xls = _excel_bytes(vade)
    if xls:
        st.download_button("📊 Excel rapor indir", xls,
                           file_name=f"BIST_rapor_{datetime.date.today().isoformat()}.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    else:
        st.caption("📊 Excel rapor: canlı veri gerekli")
    st.caption("Karar destek aracıdır · yatırım tavsiyesi değildir")

def robot_ozet(sonuclar):
    """NOVA'nın gerçek sanal durumu (robot_durum.json varsa)."""
    try:
        import robot_motor as rm
        durum = rm.yukle()
        if not durum.get("islemler") and not durum.get("pozisyonlar"):
            return None
        uis = {}
        for r in (sonuclar or []):
            try:
                u = pl.to_ui(r)
                uis[u["tk"]] = u
            except Exception:
                pass
        k = rm.karne(durum)
        deg = rm.deger(durum, uis)
        getiri_pct = (deg / durum["baslangic"] - 1) * 100 if durum["baslangic"] else 0
        poz = []
        for kod, p in durum["pozisyonlar"].items():
            fiyat = uis.get(kod, {}).get("px", p["maliyet"])
            kzp = (fiyat - p["maliyet"]) / p["maliyet"] * 100 if p["maliyet"] else 0
            poz.append({"kod": kod, "lot": p["lot"], "fiyat": round(float(fiyat), 2), "kz": round(kzp, 1)})
        son = [{"kod": i["kod"], "kz": i.get("kz_pct", 0), "sebep": i.get("sebep", "")}
               for i in durum["islemler"][-6:]][::-1]
        return {"deger": round(deg), "getiri_pct": round(getiri_pct, 1), "basari": k["basari"],
                "skor": k["skor"], "islem": k["islem"], "acik": len(poz), "nakit": round(durum["nakit"]),
                "getiri": k["getiri"], "zarar": k["zarar"], "karakter": durum.get("karakter", "dengeli"),
                "sortino": k.get("sortino"), "mdd": k.get("mdd"), "ulcer": k.get("ulcer"),
                "pozisyonlar": poz, "islemler": son}
    except Exception:
        return None


sonuclar, xu100 = _scan(vade)
data = pl.build_payload(sonuclar, xu100)
ro = robot_ozet(sonuclar)
if ro:
    data["robot"] = ro
if not data.get("stocks"):
    st.sidebar.warning("Canlı veri yok — demo veriyle gösteriliyor.")
else:
    st.sidebar.success(f"Canlı: {len(data['stocks'])} hisse")

components.html(ui_app.render(data), height=880, scrolling=True)
