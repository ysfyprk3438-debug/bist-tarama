"""
═══════════════════════════════════════════════════════════════
BIST PARA AVCISI v4.0 — ANA UYGULAMA
═══════════════════════════════════════════════════════════════
Modüller: veri, analiz, cuzdan, arayuz, izleme, backtest
6 Sekme: Av Panosu · Tarama · Sanal Cüzdan · İzleme+Alarm · Geçmiş+Backtest · Isı Haritası

NOT: Yatırım tavsiyesi değildir. Karar destek aracıdır. Teknik analize dayanır.
"""

import streamlit as st
import datetime
import io
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd

# ── Modüller ──
from veri import veri_al, VADE_AYAR
from analiz import analiz_et
import cuzdan as cz
import arayuz as ui
import izleme as iz
import backtest as bt
import robot as rb
import gecmis as gc
import yol_haritasi as yh
import durum as dr
import piyasa as pi
import ruzgar as rz
import performans as pf
import radar as rd
import grafik as gf
import genislik as gen
import seffaflik as sf
import strateji as strj
import psikoloji as psi
import kalibrasyon as klb

st.set_page_config(
    page_title="BIST Para Avcısı",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ══════════════════════════════════════════════════════════════
# BIST LİSTE — sektörlere göre (tekrarsız)
# ══════════════════════════════════════════════════════════════
BIST_SEKTORLER = {
    "🏦 Bankacılık": ['AKBNK','GARAN','HALKB','ISCTR','VAKBN','YKBNK','TSKB','ALBRK','SKBNK','KLNMA'],
    "⚡ Enerji": ['EUPWR','ODAS','ENJSA','AKSEN','ZOREN','AYEN','AYDEM','KCAER','CWENE','NATEN'],
    "🏭 Sanayi": ['EREGL','KRDMD','ISDMR','CEMTS','CIMSA','AFYON','ARCLK','VESTL','BFREN','DOAS','OTKAR','FROTO','TOASO','TTRAK'],
    "💊 Sağlık / Kimya": ['ECILC','SELEC','MPARK','DEVA','ECZYT','GUBRF','HEKTS','PETKM','SASA','TRCAS','PRKAB'],
    "🛒 Perakende / Gıda": ['BIMAS','MGROS','SOKM','ULKER','CCOLA','AEFES','TATGD','PNSUT','BANVT','DARDL'],
    "📡 Teknoloji / Telekom": ['TTKOM','TCELL','ASELS','NETAS','LOGO','INDES','ARENA','DGATE','KAREL','SMART','PAPIL'],
    "✈️ Ulaşım / Turizm": ['THYAO','PGSUS','TAVHL','CLEBI','MAALT','RYSAS'],
    "🏗️ İnşaat / GYO": ['EKGYO','ISGYO','TRGYO','KLGYO','VKGYO','SNGYO','HLGYO','ENKAI','TKFEN','GSDHO'],
    "💼 Holding": ['SAHOL','KCHOL','DOHOL','ALARK','BERA','GOLTS','ADEL','GESAN','MAVI','BRISA','KARSN','GLYHO'],
}

BIST_TUM, KOD_SEKTOR = [], {}
for _sek, _kodlar in BIST_SEKTORLER.items():
    for _k in _kodlar:
        if _k not in KOD_SEKTOR:
            BIST_TUM.append(_k)
            KOD_SEKTOR[_k] = _sek

# ══════════════════════════════════════════════════════════════
# SESSION STATE
# ══════════════════════════════════════════════════════════════
_DEFAULTS = {
    "tarama_yapildi": False,
    "sonuclar": [],
    "rejim": "",
    "xu100_pct": 0.0,
    "vade": "haftalik",
    "tarama_log": {},      # {kod: sebep} — sessiz hata yok
    "favoriler": set(),
    "izleme": [],          # watchlist kodları
    "alarmlar": [],
    "cuzdan": None,
    "gunluk_hedef": 1000,  # günlük kazanç hedefi (TL)
    "robot_cuzdan": None,  # robotun ayrı sanal cüzdanı
    "robot_log": [],       # robotun işlem günlüğü
    "robot_cooldown": {},  # satılan hisselerin soğuma sayacı (turlar arası)
    "robot_deger_gecmis": [],  # robot portföy değeri zaman serisi (karne için)
    "robot_baslangic": 100000,  # robot başlangıç bakiyesi (getiri hesabı)
    "gecmis": [],          # sinyal geçmişi (öz-ölçüm + performans karnesi)
    "genislik": None,      # piyasa genişliği (market breadth)
    "psikoloji": None,     # kalabalık psikolojisi (korku/açgözlülük)
}
for _k, _v in _DEFAULTS.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v

# ══════════════════════════════════════════════════════════════
# GLOBAL CSS
# ══════════════════════════════════════════════════════════════
st.markdown(ui.temiz_html("""
<style>
.stApp { background-color: #080C14; }
section[data-testid="stSidebar"] { background-color: #0D1117; }
.stButton > button {
  background: linear-gradient(135deg, #0369A1, #0EA5E9);
  color: white; border: none; border-radius: 10px;
  font-weight: 700; font-size: 0.95rem; padding: 12px 0; width: 100%;
}
.stButton > button:hover { background: linear-gradient(135deg, #0EA5E9, #38BDF8); }
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 1rem; padding-bottom: 2rem; }
@keyframes pulse-yesil { 0%,100% { box-shadow: 0 0 0 0 rgba(16,185,129,0.0); } 50% { box-shadow: 0 0 16px 2px rgba(16,185,129,0.7); } }
@keyframes pulse-kirmizi { 0%,100% { box-shadow: 0 0 0 0 rgba(239,68,68,0.0); } 50% { box-shadow: 0 0 16px 2px rgba(239,68,68,0.7); } }
@keyframes pulse-mavi { 0%,100% { box-shadow: 0 0 0 0 rgba(56,189,248,0.0); } 50% { box-shadow: 0 0 16px 2px rgba(56,189,248,0.7); } }
@keyframes pulse-turuncu { 0%,100% { box-shadow: 0 0 0 0 rgba(245,158,11,0.0); } 50% { box-shadow: 0 0 16px 2px rgba(245,158,11,0.7); } }
@keyframes pulse-turkuaz { 0%,100% { box-shadow: 0 0 0 0 rgba(6,182,212,0.0); } 50% { box-shadow: 0 0 16px 2px rgba(6,182,212,0.7); } }
</style>
"""), unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# PİYASA REJİMİ
# ══════════════════════════════════════════════════════════════
@st.cache_data(ttl=1800, show_spinner=False)
def piyasa_durumu():
    try:
        df, _ = veri_al("XU100", gun=365, min_gun=50)
        if df is None:
            # endeks sembolü farklı olabilir, hisse bazlı yedek
            df, _ = veri_al("GARAN", gun=365, min_gun=50)
        if df is not None and len(df) > 50:
            k = df["Close"]
            son = float(k.iloc[-1])
            ma50 = float(k.rolling(50).mean().iloc[-1])
            ma200 = float(k.rolling(200).mean().iloc[-1]) if len(k) >= 200 else ma50
            ay_once = float(k.iloc[-22]) if len(k) >= 22 else son
            aylik = ((son - ay_once) / ay_once) * 100
            if son > ma50 > ma200:
                return "YÜKSELİŞ TRENDİ", 1.0, aylik
            elif son > ma200:
                return "DÜZELTME (Temkinli)", 0.65, aylik
            else:
                return "DÜŞÜŞ TRENDİ", 0.25, aylik
    except Exception:
        pass
    return "VERİ BEKLENİYOR", 0.7, 0.0

# ══════════════════════════════════════════════════════════════
# TARAMA ORKESTRASYON — hata görünür
# ══════════════════════════════════════════════════════════════
@st.cache_data(ttl=900, show_spinner=False)
def tum_tarama(vade_key, _ts):
    """
    _ts: cache'i tazelemek için zaman damgası (tarama butonu basınca değişir)
    Dönen: (sonuclar, rejim, xu100, log)
    """
    ayar = VADE_AYAR[vade_key]
    rejim, carpan, xu100 = piyasa_durumu()
    sonuclar = []
    log = {}

    # Endeks kapanış serisini bir kez çek (relatif güç için tüm hisselere geçecek)
    endeks_close = None
    try:
        edf, _ = veri_al("XU100", gun=ayar["gun"], min_gun=ayar["min_gun"], aralik=ayar["aralik"])
        if edf is None:
            edf, _ = veri_al("GARAN", gun=ayar["gun"], min_gun=ayar["min_gun"], aralik=ayar["aralik"])
        if edf is not None:
            endeks_close = edf["Close"].values
    except Exception:
        endeks_close = None

    def _tek(kod):
        df, durum = veri_al(kod, gun=ayar["gun"], min_gun=ayar["min_gun"], aralik=ayar["aralik"])
        if df is None:
            return kod, None, durum, None
        # Genişlik katkısı (sinyal versin vermesin, tüm hisselerden toplanır)
        gk = gen.genislik_katki(df)
        r = analiz_et(kod, df, ayar, 100000, carpan, KOD_SEKTOR.get(kod, "Diğer"), endeks_close=endeks_close)
        return kod, r, durum, gk

    genislik_katkilari = []
    with ThreadPoolExecutor(max_workers=8) as ex:
        gorevler = {ex.submit(_tek, h): h for h in BIST_TUM}
        for f in as_completed(gorevler):
            try:
                kod, r, durum, gk = f.result()
                log[kod] = durum
                if gk is not None:
                    genislik_katkilari.append(gk)
                if r:
                    sonuclar.append(r)
            except Exception as e:
                log[gorevler[f]] = f"hata:{type(e).__name__}"

    # Piyasa genişliği özeti (tüm hisselerden)
    genislik = gen.genislik_ozeti(genislik_katkilari, endeks_pct=xu100)

    # Av skoruna göre sırala (varsa); yoksa eski formül
    sonuclar.sort(key=lambda x: x.get("karar", {}).get("skor", x["puan"]), reverse=True)
    return sonuclar, rejim, xu100, log, genislik

# ══════════════════════════════════════════════════════════════
# MİNİ GRAFİK
# ══════════════════════════════════════════════════════════════
def mini_grafik(df):
    try:
        fig, ax = plt.subplots(figsize=(8, 2.0))
        fig.patch.set_facecolor("#0D1117")
        ax.set_facecolor("#0D1117")
        t = df.index
        k = df["Close"].values
        renk = "#10B981" if k[-1] >= k[0] else "#EF4444"
        ax.plot(t, k, color=renk, linewidth=1.5)
        ax.fill_between(t, k, k.min(), alpha=0.12, color=renk)
        if len(k) >= 20:
            ma = pd.Series(k).rolling(20).mean().values
            ax.plot(t, ma, color="#F59E0B", linewidth=0.8, linestyle="--")
        ax.tick_params(colors="#475569", labelsize=7)
        for s in ax.spines.values():
            s.set_edgecolor("#1E293B")
        ax.grid(axis="y", color="#1E293B", linewidth=0.5, alpha=0.5)
        plt.tight_layout(pad=0.3)
        buf = io.BytesIO()
        plt.savefig(buf, format="png", dpi=100, bbox_inches="tight", facecolor="#0D1117")
        plt.close()
        buf.seek(0)
        return buf
    except Exception:
        plt.close()
        return None

# ══════════════════════════════════════════════════════════════
# YAN PANEL
# ══════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("### 💼 Sanal Cüzdan")
    if st.session_state.cuzdan is None:
        baslangic = st.number_input("Başlangıç bakiyesi (₺)", 1000, 100_000_000, 100_000, 1000)
        komisyon = st.number_input("Komisyon (%)", 0.0, 1.0, 0.2, 0.05) / 100
        if st.button("Cüzdanı Oluştur"):
            c = cz.cuzdan_olustur(baslangic)
            c["komisyon_oran"] = komisyon
            st.session_state.cuzdan = c
            st.rerun()
    else:
        c = st.session_state.cuzdan
        st.markdown(f"**Nakit:** {c['nakit']:,.0f}₺")
        st.markdown(f"**Komisyon:** %{c['komisyon_oran']*100:.2f}")
        if st.button("Cüzdanı Sıfırla"):
            st.session_state.cuzdan = None
            st.rerun()

    st.markdown("---")
    st.markdown("### 🎯 Günlük Hedef")
    st.session_state.gunluk_hedef = st.number_input(
        "Günlük kazanç hedefi (₺)", 0, 1_000_000, st.session_state.gunluk_hedef, 100)

    st.markdown("---")
    st.markdown("### 🔔 Telegram")
    tg_token = st.text_input("Bot Token", type="password")
    tg_chat = st.text_input("Chat ID")

    st.markdown("---")
    st.markdown("### 🗄️ Supabase (Geçmiş)")
    sb_url = st.text_input("Supabase URL", type="password")
    sb_key = st.text_input("Supabase Key", type="password")

# ── Telegram yardımcı ──
def telegram_gonder(token, chat_id, mesaj):
    if not token or not chat_id:
        return False
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": mesaj, "parse_mode": "Markdown"},
            timeout=10)
        return r.status_code == 200
    except Exception:
        return False

# ── Güncel fiyatları topla (cüzdan/izleme için) ──
def guncel_fiyatlar():
    f = {}
    for r in st.session_state.sonuclar:
        f[r["kod"]] = r["son"]
    return f

# ══════════════════════════════════════════════════════════════
# BAŞLIK
# ══════════════════════════════════════════════════════════════
st.markdown(ui.temiz_html("""
<div style="background:linear-gradient(135deg,#0D1B2A,#0A2540);border:1px solid #00D4FF33;
border-radius:14px;padding:18px 16px;text-align:center;margin-bottom:16px">
  <h1 style="color:#00D4FF;font-size:1.6rem;font-weight:800;margin:0">🎯 BIST PARA AVCISI</h1>
  <p style="color:#64748B;font-size:0.8rem;margin:4px 0 0 0">Tarama · Sanal Cüzdan · Alarm · Backtest · Akıllı Para</p>
</div>
"""), unsafe_allow_html=True)

sekmeler = st.tabs([
    "📡 Radar", "🎯 Av Panosu", "📊 Tarama", "💼 Cüzdan",
    "⭐ İzleme", "📈 Backtest", "🔥 Isı Haritası", "🤖 Robot", "🧭 Yol Haritası",
])

# ──────────────────────────────────────────────────────────────
# SEKME 0: FIRSAT RADARI (nişan ekranı — şu an aksiyon gerektirenler)
# ──────────────────────────────────────────────────────────────
with sekmeler[0]:
    st.markdown("#### 📡 Fırsat Radarı")
    if not st.session_state.get("tarama_yapildi") or not st.session_state.get("sonuclar"):
        st.info("Önce **Tarama** sekmesinden BIST'i tara — radar, aksiyon gerektiren fırsatları burada toplar.")
    else:
        # Piyasa genişliği (sağlık) şeridi — fırsatlardan önce genel hava
        gnsl = st.session_state.get("genislik")
        if gnsl:
            st.markdown(ui.temiz_html(f"""<div style="background:#0D1117;border:1px solid {gnsl['renk']}55;border-left:4px solid {gnsl['renk']};border-radius:10px;padding:12px 14px;margin-bottom:6px"><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px"><span style="color:{gnsl['renk']};font-size:0.85rem;font-weight:800">🩺 PİYASA SAĞLIĞI: {gnsl['saglik']}</span><span style="color:#94A3B8;font-size:0.68rem">{gnsl['toplam']} hisse</span></div><div style="display:flex;gap:10px;margin-bottom:6px"><span style="color:#94A3B8;font-size:0.7rem">MA200 üstü: <b style="color:{gnsl['renk']}">%{gnsl['ma200_oran']:.0f}</b></span><span style="color:#94A3B8;font-size:0.7rem">MA50 üstü: <b style="color:#E2E8F0">%{gnsl['ma50_oran']:.0f}</b></span><span style="color:#94A3B8;font-size:0.7rem">Yükselen: <b style="color:#E2E8F0">%{gnsl['yukselen_oran']:.0f}</b></span></div><div style="color:#94A3B8;font-size:0.7rem;line-height:1.4">{gnsl['mesaj']}</div>{f'<div style="color:{gnsl["iraksama"]["renk"]};font-size:0.72rem;font-weight:600;margin-top:6px">{gnsl["iraksama"]["mesaj"]}</div>' if gnsl['iraksama']['var'] else ''}</div>"""), unsafe_allow_html=True)

        rad = rd.firsat_radari(st.session_state.sonuclar)
        # Bugünün oyunu — piyasa stratejisi sezonu (adaptif meta-beyin)
        ps = st.session_state.get("piyasa_strateji")
        if ps:
            st.markdown(ui.temiz_html(f"""<div style="background:{ps['renk']}15;border:1px solid {ps['renk']}55;border-radius:10px;padding:10px 14px;margin-bottom:8px"><div style="color:{ps['renk']};font-size:0.8rem;font-weight:800">{ps['ikon']} BUGÜNÜN OYUNU: {ps['ad']}</div><div style="color:#94A3B8;font-size:0.7rem;margin-top:2px">{ps['gerekce']}</div></div>"""), unsafe_allow_html=True)

        # Kalabalık psikolojisi — korku/açgözlülük endeksi (Katman 5)
        psk = st.session_state.get("psikoloji")
        if psk:
            # Görsel bar (0=korku yeşil, 100=açgözlülük kırmızı)
            bar_pos = psk["skor"]
            st.markdown(ui.temiz_html(f"""<div style="background:#0D1117;border:1px solid {psk['renk']}55;border-radius:10px;padding:10px 14px;margin-bottom:8px"><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px"><span style="color:{psk['renk']};font-size:0.8rem;font-weight:800">{psk['ikon']} KORKU & AÇGÖZLÜLÜK: {psk['skor']}/100</span><span style="color:{psk['renk']};font-size:0.72rem;font-weight:700">{psk['bolge']}</span></div><div style="background:linear-gradient(90deg,#10B981 0%,#94A3B8 50%,#EF4444 100%);height:6px;border-radius:3px;position:relative;margin-bottom:6px"><div style="position:absolute;left:{bar_pos}%;top:-3px;width:3px;height:12px;background:#fff;border-radius:2px;transform:translateX(-50%)"></div></div><div style="color:#94A3B8;font-size:0.7rem;line-height:1.4">{psk['contrarian']}</div></div>"""), unsafe_allow_html=True)
        if rad["toplam_firsat"] == 0 and not rad["izle"]:
            st.markdown(ui.temiz_html("""<div style="text-align:center;padding:30px;color:#64748B"><div style="font-size:2rem;margin-bottom:8px">🌙</div><div style="font-size:0.9rem">Şu an radar temiz — acil aksiyon gerektiren fırsat yok.</div><div style="font-size:0.75rem;margin-top:6px">Sakin kalmak da bir stratejidir. Piyasa fırsat sunduğunda burada göreceksin.</div></div>"""), unsafe_allow_html=True)

        def _radar_satir(r, vurgu=False):
            b = rd.radar_satir_bilgi(r)
            olay_html = f'<span style="color:{b["olay_renk"]};font-size:0.68rem">{b["olay"]}</span>' if b["olay"] else ""
            kenar = f"border:1px solid {b['karar_renk']};" if vurgu else "border:1px solid #1E293B;"
            return ui.temiz_html(f"""<div style="background:#0D1117;{kenar}border-radius:10px;padding:10px 12px;margin-bottom:6px"><div style="display:flex;justify-content:space-between;align-items:center"><div><span style="color:#E2E8F0;font-weight:800;font-size:0.95rem">{b['kod']}</span> <span style="color:{b['karar_renk']};font-size:0.72rem;font-weight:700">{b['ikon']} {b['karar']}</span><div style="margin-top:2px">{olay_html}</div></div><div style="text-align:right"><div style="color:{b['karar_renk']};font-weight:800;font-size:1.1rem">{b['av_skoru']}</div><div style="color:#475569;font-size:0.6rem">AV SKORU · {b['son']:.2f}₺</div></div></div></div>""")

        if rad["simdi"]:
            st.markdown('<div style="color:#10B981;font-size:0.8rem;font-weight:800;margin:6px 0">🔴 ŞİMDİ — fırsat penceresi açık</div>', unsafe_allow_html=True)
            for r in rad["simdi"]:
                st.markdown(_radar_satir(r, vurgu=True), unsafe_allow_html=True)

        if rad["yaklasan"]:
            st.markdown('<div style="color:#38BDF8;font-size:0.8rem;font-weight:800;margin:12px 0 6px">⚡ YAKLAŞAN — hazırlan</div>', unsafe_allow_html=True)
            for r in rad["yaklasan"]:
                st.markdown(_radar_satir(r), unsafe_allow_html=True)

        if rad["izle"]:
            st.markdown('<div style="color:#94A3B8;font-size:0.8rem;font-weight:800;margin:12px 0 6px">👁 İZLE — takipte tut</div>', unsafe_allow_html=True)
            for r in rad["izle"]:
                st.markdown(_radar_satir(r), unsafe_allow_html=True)

        st.caption(f"Radar, son taramadaki {len(st.session_state.sonuclar)} sinyalden aksiyon gerektirenleri süzer. Detay için Tarama sekmesine bak.")

        # Çeşitlendirme kontrolü — sahte çeşitlendirme tuzağı (aksiyon adayları arasında)
        aksiyon_adaylari = rad["simdi"] + rad["yaklasan"]
        if len(aksiyon_adaylari) >= 2:
            ces = pi.cesitlendirme_kontrol(aksiyon_adaylari)
            if ces and ces["uyari"]:
                st.markdown("---")
                gruplar_html = "".join(f'<div style="color:#94A3B8;font-size:0.72rem;padding:2px 0">🔗 {" + ".join(k["hisseler"])} <span style="color:#64748B">({k["sektor"]})</span></div>' for k in ces["kumeler"])
                st.markdown(ui.temiz_html(f"""<div style="background:#F59E0B15;border:1px solid #F59E0B55;border-radius:10px;padding:12px 14px"><div style="color:#F59E0B;font-size:0.78rem;font-weight:800;margin-bottom:4px">🔗 ÇEŞİTLENDİRME UYARISI</div><div style="color:#94A3B8;font-size:0.72rem;line-height:1.4;margin-bottom:6px">{ces['mesaj']}</div>{gruplar_html}</div>"""), unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────
# SEKME 1: AV PANOSU
# ──────────────────────────────────────────────────────────────
with sekmeler[1]:
    st.markdown("#### 🎯 Bugünün Avı")
    c = st.session_state.cuzdan
    if c is None:
        st.info("Sanal cüzdan oluştur (sol panel), av panosu burada canlanır.")
    else:
        ozet = cz.portfoy_degeri(c, guncel_fiyatlar())
        karne = cz.gunluk_karne(c)
        # Günlük hedef ilerlemesi
        y, renk, durum = iz.hedef_ilerleme(karne["realize_kar"], st.session_state.gunluk_hedef)
        st.markdown(ui.temiz_html(f"""
        <div style="background:#0D1117;border:1px solid #1E293B;border-radius:12px;padding:16px">
          <div style="display:flex;justify-content:space-between;margin-bottom:10px">
            <div><div style="color:#94A3B8;font-size:0.7rem">PORTFÖY DEĞERİ</div>
              <div style="color:#E2E8F0;font-size:1.5rem;font-weight:800">{ozet['toplam']:,.0f}₺</div></div>
            <div style="text-align:right"><div style="color:#94A3B8;font-size:0.7rem">TOPLAM K/Z</div>
              <div style="color:{'#10B981' if ozet['toplam_kar']>=0 else '#EF4444'};font-size:1.5rem;font-weight:800">{ozet['toplam_kar']:+,.0f}₺</div></div>
          </div>
          <div style="color:#94A3B8;font-size:0.7rem;margin-bottom:4px">GÜNLÜK HEDEF: {karne['realize_kar']:+,.0f}₺ / {st.session_state.gunluk_hedef:,}₺ — {durum}</div>
          <div style="background:#1E293B;border-radius:5px;height:8px">
            <div style="width:{y}%;height:8px;border-radius:5px;background:{renk}"></div>
          </div>
        </div>
        """), unsafe_allow_html=True)

        cols = st.columns(3)
        with cols[0]:
            st.markdown(ui.istat_kutu("BUGÜN İŞLEM", karne["islem_sayisi"], "#38BDF8"), unsafe_allow_html=True)
        with cols[1]:
            st.markdown(ui.istat_kutu("KAZANAN", karne["kazanan"], "#10B981"), unsafe_allow_html=True)
        with cols[2]:
            st.markdown(ui.istat_kutu("BAŞARI", f"%{karne['basari_pct']:.0f}", "#F59E0B"), unsafe_allow_html=True)

        if ozet["pozisyonlar"]:
            # Yığılma / konsantrasyon uyarısı (Katman 2)
            yig = pi.yigilma_analiz(ozet["pozisyonlar"], KOD_SEKTOR)
            if yig:
                yrenk = "#EF4444" if yig["risk_seviye"] == "YÜKSEK" else ("#F59E0B" if yig["risk_seviye"] == "ORTA" else "#10B981")
                ikon = "⚠️" if yig["uyari"] else "✓"
                st.markdown(ui.temiz_html(f"""<div style="background:#0D1117;border:1px solid {yrenk}44;border-left:3px solid {yrenk};border-radius:8px;padding:10px 12px;margin-bottom:10px"><div style="color:{yrenk};font-size:0.7rem;font-weight:700;margin-bottom:3px">{ikon} SEKTÖR DAĞILIMI — {yig['risk_seviye']} RİSK</div><div style="color:#94A3B8;font-size:0.74rem">{yig['mesaj']}</div></div>"""), unsafe_allow_html=True)

            st.markdown("##### Açık Pozisyonlar")
            for p in ozet["pozisyonlar"]:
                ilerleme = p["hedef_ilerleme"]
                bar = ""
                if ilerleme is not None:
                    bar = f'<div style="background:#1E293B;border-radius:3px;height:5px;margin-top:5px"><div style="width:{ilerleme}%;height:5px;border-radius:3px;background:#10B981"></div></div>'
                st.markdown(ui.temiz_html(f"""
                <div style="background:#0D1117;border:1px solid #1E293B;border-radius:10px;padding:10px 12px;margin-bottom:6px">
                  <div style="display:flex;justify-content:space-between">
                    <span style="color:#E2E8F0;font-weight:700">{p['kod']} · {p['lot']:,} lot</span>
                    <span style="color:{'#10B981' if p['kar']>=0 else '#EF4444'};font-weight:700">{p['kar']:+,.0f}₺ (%{p['kar_pct']:+.1f})</span>
                  </div>
                  <div style="color:#64748B;font-size:0.7rem">Maliyet {p['ort_maliyet']:.2f}₺ → Güncel {p['guncel']:.2f}₺</div>
                  {bar}
                </div>
                """), unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────
# SEKME 2: TARAMA
# ──────────────────────────────────────────────────────────────
with sekmeler[2]:
    vade_secim = st.radio(
        "Vade", list(VADE_AYAR.keys()),
        format_func=lambda k: VADE_AYAR[k]["ad"],
        horizontal=True, key="vade_radio")
    st.session_state.vade = vade_secim

    c1, c2 = st.columns(2)
    with c1:
        min_puan = st.slider("Min Puan", 0, 90, 20, 5)
    with c2:
        sektor_sec = st.selectbox("Sektör", ["Tümü"] + list(BIST_SEKTORLER.keys()))
    sm_filtre = st.checkbox("Sadece Akıllı Para ≥ 60")

    if st.button("🔍 BIST'İ TARA", use_container_width=True):
        with st.spinner(f"{VADE_AYAR[vade_secim]['ad']} taranıyor..."):
            ts = datetime.datetime.now().isoformat()
            sonuclar, rejim, xu100, log, genislik = tum_tarama(vade_secim, ts)
            st.session_state.update({
                "sonuclar": sonuclar, "rejim": rejim, "xu100_pct": xu100,
                "tarama_yapildi": True, "tarama_log": log, "genislik": genislik,
            })
            # Rüzgar yönü: rotasyonu bir kez hesapla, her sonuca ekle (Bağlam Katmanı)
            rotasyon_t = pi.sektor_rotasyon(sonuclar)
            # Piyasa stratejisi (sezon): bir kez hesapla — adaptif meta-beyin
            endeks_vol = genislik.get("_endeks_vol") if genislik else None
            piyasa_strat = strj.piyasa_stratejisi(genislik, rejim)
            st.session_state["piyasa_strateji"] = piyasa_strat
            # Kalabalık psikolojisi (Katman 5): korku/açgözlülük endeksi — bir kez
            psikoloji = psi.korku_acgozluluk(genislik, endeks_vol, xu100)
            st.session_state["psikoloji"] = psikoloji
            for r in sonuclar:
                r["ruzgar"] = rz.ruzgar_hesapla(r, rejim, rotasyon_t)
                # Strateji uyumu (hisse oyunu vs piyasa sezonu)
                r["strateji"] = strj.strateji_analizi(r, piyasa_strat)
                # Strateji + kalabalık psikolojisi kararı etkiler
                if r.get("karar"):
                    h_strat = r["strateji"]["hisse_strateji"]
                    psi_etki = psi.psikoloji_karar_etkisi(psikoloji, h_strat)
                    # Kalibrasyon: sistemin gerçek sicilinden öğrendiği ayar (Katman 1)
                    kalib = klb.kalibrasyon_ayari(st.session_state.gecmis, r.get("sinyal"))
                    toplam_etki = r["strateji"]["karar_etkisi"] + psi_etki["etki"] + kalib["ayar"]
                    yeni_skor = max(0, min(100, r["karar"]["skor"] + toplam_etki))
                    r["karar"]["skor"] = yeni_skor
                    if kalib.get("gerekce"):
                        r["kalibrasyon_not"] = kalib["gerekce"]
                # Güveni rüzgarla güncelle
                if r.get("guven"):
                    carpan = rz.ruzgar_guven_etkisi(r["ruzgar"])
                    yeni_yuzde = max(0, min(100, int(r["guven"]["yuzde"] * carpan)))
                    r["guven"]["yuzde"] = yeni_yuzde
                    if yeni_yuzde >= 75: r["guven"]["seviye"], r["guven"]["renk"] = "YÜKSEK", "#10B981"
                    elif yeni_yuzde >= 55: r["guven"]["seviye"], r["guven"]["renk"] = "ORTA", "#F59E0B"
                    elif yeni_yuzde >= 35: r["guven"]["seviye"], r["guven"]["renk"] = "DÜŞÜK", "#FB923C"
                    else: r["guven"]["seviye"], r["guven"]["renk"] = "ZAYIF", "#EF4444"
            # Öz-ölçüm: sinyalleri kaydet + açık pozisyonların sonucunu kontrol et
            for r in sonuclar:
                gc.sinyal_kaydet(st.session_state.gecmis, r)
            gc.sonuc_kontrol(st.session_state.gecmis, guncel_fiyatlar())
            if tg_token and tg_chat and sonuclar:
                m = f"🎯 *BIST AVI — {VADE_AYAR[vade_secim]['ad']}*\nBorsa: {rejim}\n\n"
                for r in sonuclar[:7]:
                    m += f"*{r['kod']}* {r['sinyal']} | {r['son']:.2f}₺ | +%{r['kazanc_pct']:.1f} | Puan {r['puan']}\n"
                m += "\n_Yatırım tavsiyesi değildir._"
                telegram_gonder(tg_token, tg_chat, m)

    if st.session_state.tarama_yapildi:
        sonuclar = st.session_state.sonuclar
        st.markdown(ui.rejim_kart(st.session_state.rejim, st.session_state.xu100_pct), unsafe_allow_html=True)

        # Tarama sağlık raporu — sessiz hata yok
        log = st.session_state.tarama_log
        basarili = len([v for v in log.values() if v and (":" in v and v.split(":")[1].isdigit())])
        with st.expander(f"📡 Tarama Raporu — {len(sonuclar)} fırsat / {len(log)} hisse tarandı"):
            gelmedi = {k: v for k, v in log.items() if v and not (len(v.split(":")) > 1 and v.split(":")[1].split()[0].isdigit())}
            if gelmedi:
                st.markdown(f"**Veri gelmeyen {len(gelmedi)} hisse:**")
                st.text("\n".join(f"{k}: {v}" for k, v in list(gelmedi.items())[:30]))
            else:
                st.success("Tüm hisselerden veri alındı.")

        # Özet kutular
        guclu = len([r for r in sonuclar if "Güçlü" in r["sinyal"] or "DİP" in r["sinyal"]])
        buyuk = len([r for r in sonuclar if r["sm"]["buyuk_oyuncu"]])
        ort_puan = np.mean([r["puan"] for r in sonuclar]) if sonuclar else 0
        k1, k2, k3, k4 = st.columns(4)
        with k1: st.markdown(ui.istat_kutu("FIRSAT", len(sonuclar), "#00D4FF"), unsafe_allow_html=True)
        with k2: st.markdown(ui.istat_kutu("GÜÇLÜ", guclu, "#10B981"), unsafe_allow_html=True)
        with k3: st.markdown(ui.istat_kutu("🐋 BÜYÜK", buyuk, "#60A5FA"), unsafe_allow_html=True)
        with k4: st.markdown(ui.istat_kutu("ORT PUAN", f"{ort_puan:.0f}", "#F59E0B"), unsafe_allow_html=True)

        # Filtre
        goster = [r for r in sonuclar if r["puan"] >= min_puan]
        if sektor_sec != "Tümü":
            goster = [r for r in goster if r["sektor"] == sektor_sec]
        if sm_filtre:
            goster = [r for r in goster if r["sm"]["skor"] >= 60]

        # Tıklanır kutular — tek tek kaydırmaya son
        guclu_list = [r for r in goster if "Güçlü" in r["sinyal"] or "DİP" in r["sinyal"]]
        buyuk_list = [r for r in goster if r["sm"]["buyuk_oyuncu"]]
        with st.expander(f"🔥 Güçlü Sinyaller ({len(guclu_list)})"):
            for r in guclu_list:
                st.markdown(ui.kompakt_satir(r), unsafe_allow_html=True)
        with st.expander(f"🐋 Büyük Oyuncu Girişi ({len(buyuk_list)})"):
            for r in buyuk_list:
                st.markdown(ui.kompakt_satir(r), unsafe_allow_html=True)

        st.markdown(f"##### Tüm Fırsatlar ({len(goster)})")
        for r in goster:
            kk, kf = st.columns([6, 1])
            with kk:
                st.markdown(ui.hisse_kart(r), unsafe_allow_html=True)
                # Tıklanır grafik — basınca açılır, teknik olaylar işaretli + tek cümle yorum
                with st.expander(f"📈 {r['kod']} Grafik & Teknik Analiz"):
                    # ŞEFFAFLIK PANELİ — neden bu karar? (güven = şeffaflık + dürüstlük)
                    defter = sf.karar_defteri(r)
                    gb = gc.basari_orani(st.session_state.gecmis, r.get("sinyal"))
                    gb_ornek = len([k for k in st.session_state.gecmis if k.get("sonuc") and r.get("sinyal","") in k.get("sinyal_tip","")])
                    dn = sf.durustluk_notu(r, gecmis_basari=gb, gecmis_ornek=gb_ornek)
                    # Dürüstlük başlığı
                    st.markdown(ui.temiz_html(f"""<div style="background:{dn['renk']}15;border:1px solid {dn['renk']}55;border-radius:8px;padding:10px 12px;margin-bottom:8px"><div style="color:{dn['renk']};font-size:0.78rem;font-weight:800;margin-bottom:4px">🔍 NEDEN BU KARAR? · {dn['seviye']}</div><div style="color:#94A3B8;font-size:0.7rem;line-height:1.4">📊 {dn['sicil_metni']}</div></div>"""), unsafe_allow_html=True)
                    # Lehte / Aleyhte / Belirsiz
                    cL, cA = st.columns(2)
                    with cL:
                        if defter["lehte"]:
                            st.markdown('<div style="color:#10B981;font-size:0.7rem;font-weight:700;margin-bottom:3px">✓ LEHTE</div>', unsafe_allow_html=True)
                            for ad, acik in defter["lehte"]:
                                st.markdown(ui.temiz_html(f'<div style="color:#94A3B8;font-size:0.66rem;margin-bottom:3px" title="{acik}">• {ad}</div>'), unsafe_allow_html=True)
                    with cA:
                        if defter["aleyhte"]:
                            st.markdown('<div style="color:#EF4444;font-size:0.7rem;font-weight:700;margin-bottom:3px">✗ ALEYHTE / RİSK</div>', unsafe_allow_html=True)
                            for ad, acik in defter["aleyhte"]:
                                st.markdown(ui.temiz_html(f'<div style="color:#94A3B8;font-size:0.66rem;margin-bottom:3px" title="{acik}">• {ad}</div>'), unsafe_allow_html=True)
                        if defter["belirsiz"]:
                            st.markdown('<div style="color:#64748B;font-size:0.7rem;font-weight:700;margin:4px 0 3px">? BELİRSİZ</div>', unsafe_allow_html=True)
                            for ad, acik in defter["belirsiz"]:
                                st.markdown(ui.temiz_html(f'<div style="color:#64748B;font-size:0.66rem;margin-bottom:3px">• {ad}</div>'), unsafe_allow_html=True)
                    if dn["notlar"]:
                        st.caption("⚖️ " + " · ".join(dn["notlar"][:2]))
                    st.markdown("<div style='border-top:1px solid #1E293B;margin:8px 0'></div>", unsafe_allow_html=True)

                    # Hacim profili & VWAP — kurumsal seviyeler (nereden al/sat)
                    hac = r.get("hacim", {})
                    if hac and hac.get("profil"):
                        hp = hac["profil"]; vw = hac.get("vwap")
                        vw_txt = f" · VWAP {vw['vwap']}₺ ({vw['konum']})" if vw else ""
                        st.markdown(ui.temiz_html(f"""<div style="background:#0D1117;border:1px solid {hac['renk']}44;border-radius:8px;padding:10px 12px;margin-bottom:8px"><div style="color:{hac['renk']};font-size:0.72rem;font-weight:700;margin-bottom:4px">📊 KURUMSAL SEVİYELER · Yapı {hac['yapi_skoru']}/100</div><div style="color:#94A3B8;font-size:0.7rem;line-height:1.5">POC (en güçlü destek): <b style="color:#E2E8F0">{hp['poc']}₺</b><br>Değer alanı: <b style="color:#E2E8F0">{hp['va_alt']}₺ — {hp['va_ust']}₺</b>{vw_txt}<br>{hp['aciklama']}</div></div>"""), unsafe_allow_html=True)

                    # Matematiksel seviyeler (Fibonacci + pivot)
                    ms = r.get("mat_seviye", {})
                    if ms and (ms.get("yakin_destek") or ms.get("yakin_direnc")):
                        d = ms.get("yakin_destek"); dr = ms.get("yakin_direnc")
                        d_txt = f'{d[0]}: <b style="color:#10B981">{d[1]}₺</b>' if d else "—"
                        dr_txt = f'{dr[0]}: <b style="color:#EF4444">{dr[1]}₺</b>' if dr else "—"
                        onay_txt = f'<div style="color:#F59E0B;font-size:0.68rem;margin-top:4px">{ms["hacim_onayi"]["mesaj"]}</div>' if ms.get("hacim_onayi") else ""
                        fib_txt = ""
                        if ms.get("fib"):
                            fl = ms["fib"]["seviyeler"]
                            fib_txt = f'<br><span style="color:#64748B;font-size:0.66rem">Fib ({ms["fib"]["yon"]}): ' + " · ".join(f'{et} {f}₺' for o, f, et in fl[1:4]) + '</span>'
                        st.markdown(ui.temiz_html(f"""<div style="background:#0D1117;border:1px solid #334155;border-radius:8px;padding:10px 12px;margin-bottom:8px"><div style="color:#A78BFA;font-size:0.72rem;font-weight:700;margin-bottom:4px">📐 MATEMATİKSEL SEVİYELER</div><div style="color:#94A3B8;font-size:0.7rem;line-height:1.5">Yakın destek → {d_txt}<br>Yakın direnç → {dr_txt}{fib_txt}</div>{onay_txt}</div>"""), unsafe_allow_html=True)

                    # Hisse DNA'sı: karakter (Hurst) + rol (relatif güç) + strateji uyumu
                    krk = r.get("karakter", {})
                    if krk.get("dna"):
                        uyum = krk.get("uyum_skoru", 50)
                        urenk = "#10B981" if uyum >= 70 else ("#F59E0B" if uyum >= 45 else "#EF4444")
                        h_txt = f"H={krk['H']}" if krk.get("H") is not None else ""
                        rs_txt = ""
                        if krk.get("rs"):
                            rs_txt = f" · Endekse karşı %{krk['rs']['getiri_farki']:+.1f}"
                        st.markdown(ui.temiz_html(f"""<div style="background:#0D1117;border:1px solid {urenk}44;border-radius:8px;padding:10px 12px;margin-bottom:8px"><div style="color:{urenk};font-size:0.72rem;font-weight:700;margin-bottom:3px">🧬 DNA: {krk['dna']} <span style="color:#475569;font-weight:400">{h_txt}{rs_txt}</span></div><div style="color:#94A3B8;font-size:0.72rem;line-height:1.4">{krk.get('uyum_yorum','')}</div></div>"""), unsafe_allow_html=True)
                    # Volatilite rejimi + strateji önerisi (derin bilgi)
                    vr = r.get("volatilite", {})
                    if vr.get("rejim") and vr["rejim"] != "BELİRSİZ":
                        st.markdown(ui.temiz_html(f"""<div style="background:#0D1117;border:1px solid {vr['renk']}44;border-radius:8px;padding:10px 12px;margin-bottom:8px"><div style="color:{vr['renk']};font-size:0.72rem;font-weight:700;margin-bottom:3px">🌡️ {vr['rejim']} REJİM · ATR %{vr['atr_pct']} · vol {vr['vol_yon']}</div><div style="color:#94A3B8;font-size:0.72rem;line-height:1.4">{vr['strateji_onerisi']}</div></div>"""), unsafe_allow_html=True)
                    yorum = r.get("grafik_yorum", "")
                    if yorum:
                        olay_var = bool(r.get("teknik_olay"))
                        yrenk = "#10B981" if olay_var and any(o["yon"]=="pozitif" for o in r["teknik_olay"]) else "#94A3B8"
                        st.markdown(ui.temiz_html(f"""<div style="background:#0A1628;border-left:3px solid {yrenk};border-radius:8px;padding:10px 12px;margin-bottom:8px"><div style="color:#E2E8F0;font-size:0.82rem">💡 {yorum}</div></div>"""), unsafe_allow_html=True)
                    if r.get("df_grafik") is not None:
                        g = gf.grafik_ciz(r["df_grafik"], r.get("teknik_olay"), r["kod"])
                        if g:
                            st.image(g, use_container_width=True)
                    # Teknik olay rozetleri
                    if r.get("teknik_olay"):
                        rozetler = " ".join(f'<span style="background:{o["renk"]}22;color:{o["renk"]};padding:2px 8px;border-radius:10px;font-size:0.68rem;font-weight:600;margin-right:4px">{o["etiket"]}</span>' for o in r["teknik_olay"])
                        st.markdown(ui.temiz_html(f'<div style="margin-top:6px">{rozetler}</div>'), unsafe_allow_html=True)
            with kf:
                izli = r["kod"] in st.session_state.izleme
                if st.button("★" if izli else "☆", key=f"iz_{r['kod']}"):
                    if izli:
                        st.session_state.izleme.remove(r["kod"])
                    else:
                        st.session_state.izleme.append(r["kod"])
                    st.rerun()
    else:
        st.info("Vade seç ve **BIST'İ TARA**'ya bas.")

# ──────────────────────────────────────────────────────────────
# SEKME 3: SANAL CÜZDAN
# ──────────────────────────────────────────────────────────────
with sekmeler[3]:
    c = st.session_state.cuzdan
    if c is None:
        st.info("Sol panelden sanal cüzdan oluştur.")
    else:
        st.markdown("#### 💼 Sanal Al-Sat")
        kodlar = [r["kod"] for r in st.session_state.sonuclar] or BIST_TUM[:20]
        ac1, ac2, ac3 = st.columns([2, 1, 1])
        with ac1:
            sec_kod = st.selectbox("Hisse", kodlar)
        with ac2:
            islem_lot = st.number_input("Lot", 1, 1_000_000, 100)
        with ac3:
            st.write("")
            st.write("")
            islem_tip = st.radio("", ["AL", "SAT"], horizontal=True, label_visibility="collapsed")
        guncel = guncel_fiyatlar().get(sec_kod)
        if guncel:
            st.caption(f"Güncel: {guncel:.2f}₺ (son taramadan)")
        if st.button(f"{islem_tip} işlemini gerçekleştir"):
            fiyat = guncel or 0
            if fiyat <= 0:
                st.error("Fiyat yok — önce tarama yap.")
            elif islem_tip == "AL":
                r_eslesen = next((x for x in st.session_state.sonuclar if x["kod"] == sec_kod), None)
                hedef = r_eslesen["hedef"] if r_eslesen else None
                stop = r_eslesen["stop"] if r_eslesen else None
                ok, msg = cz.alis_yap(c, sec_kod, fiyat, islem_lot, hedef, stop)
                st.success(msg) if ok else st.error(msg)
                st.rerun()
            else:
                ok, msg = cz.satis_yap(c, sec_kod, fiyat, islem_lot)
                st.success(msg) if ok else st.error(msg)
                st.rerun()

        ozet = cz.portfoy_degeri(c, guncel_fiyatlar())
        st.markdown(f"**Toplam değer:** {ozet['toplam']:,.0f}₺ | **K/Z:** {ozet['toplam_kar']:+,.0f}₺ (%{ozet['toplam_kar_pct']:+.2f})")

        if c["islemler"]:
            st.markdown("##### İşlem Geçmişi")
            for i in reversed(c["islemler"][-20:]):
                kz = ""
                if i.get("kar_zarar") is not None:
                    kz = f" | {i['kar_zarar']:+,.0f}₺"
                renk = "#10B981" if i["tip"] == "ALIŞ" else ("#EF4444" if (i.get("kar_zarar", 0) or 0) < 0 else "#10B981")
                st.markdown(ui.temiz_html(f"""
                <div style="display:flex;justify-content:space-between;padding:6px 10px;border-bottom:1px solid #1E293B">
                  <span style="color:{renk};font-weight:600">{i['tip']} {i['kod']}</span>
                  <span style="color:#94A3B8;font-size:0.8rem">{i['lot']:,} @ {i['fiyat']:.2f}₺{kz}</span>
                </div>
                """), unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────
# SEKME 4: İZLEME + ALARM
# ──────────────────────────────────────────────────────────────
with sekmeler[4]:
    st.markdown("#### ⭐ İzleme Listesi")
    if not st.session_state.izleme:
        st.info("Tarama sekmesinden ☆ ile hisse ekle.")
    else:
        fiyatlar = guncel_fiyatlar()
        for kod in st.session_state.izleme:
            r = next((x for x in st.session_state.sonuclar if x["kod"] == kod), None)
            if r:
                st.markdown(ui.kompakt_satir(r), unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("#### 🔔 Fiyat Alarmı")
    al1, al2 = st.columns([2, 1])
    with al1:
        alarm_kod = st.selectbox("Hisse", [r["kod"] for r in st.session_state.sonuclar] or BIST_TUM[:20], key="alarm_kod")
    with al2:
        alarm_fiyat = st.number_input("Hedef fiyat", 0.0, 100000.0, 0.0, 0.5)
    if st.button("Alarm Kur"):
        mevcut = guncel_fiyatlar().get(alarm_kod)
        msg = iz.alarm_ekle(st.session_state.alarmlar, alarm_kod, alarm_fiyat, None, mevcut)
        st.success(msg)

    if st.session_state.alarmlar:
        st.markdown("##### Aktif Alarmlar")
        for a in st.session_state.alarmlar:
            durum = "🔔 TETİKLENDİ" if a.get("tetiklendi") else "⏳ bekliyor"
            st.markdown(f"- **{a['kod']}** {a['hedef_fiyat']:.2f}₺ {'↑' if a['yon']=='ustu' else '↓'} — {durum}")

# ──────────────────────────────────────────────────────────────
# SEKME 5: GEÇMİŞ + BACKTEST + KARNE
# ──────────────────────────────────────────────────────────────
with sekmeler[5]:
    alt1, alt2 = st.tabs(["📋 Sinyal Geçmişi & Karne", "📈 Strateji Backtest"])

    with alt1:
        st.markdown("#### 📋 Sinyal Geçmişi & Öz-Ölçüm")
        gecmis = st.session_state.gecmis
        if not gecmis:
            st.info("Henüz sinyal yok — tarama yapınca sinyaller otomatik kaydedilir, başarısı ölçülür.")
        else:
            ozet = gc.performans_ozet(gecmis)
            if ozet:
                st.markdown("##### Öz-Ölçüm Karnesi")
                k1,k2,k3,k4 = st.columns(4)
                with k1: st.markdown(ui.istat_kutu("TOPLAM", ozet["toplam"], "#38BDF8"), unsafe_allow_html=True)
                with k2: st.markdown(ui.istat_kutu("BAŞARI", f"%{ozet['basari_pct']:.0f}", "#10B981"), unsafe_allow_html=True)
                with k3: st.markdown(ui.istat_kutu("ORT GETİRİ", f"%{ozet['ort_getiri']:+.1f}", "#F59E0B"), unsafe_allow_html=True)
                with k4: st.markdown(ui.istat_kutu("BEKLEMEDE", ozet["beklemede"], "#94A3B8"), unsafe_allow_html=True)
                if ozet["tip_karne"]:
                    st.markdown("##### Sinyal Tipi Karnesi")
                    for tip, v in sorted(ozet["tip_karne"].items(), key=lambda x: x[1]["basari_pct"], reverse=True):
                        renk = "#10B981" if v["basari_pct"] >= 60 else ("#F59E0B" if v["basari_pct"] >= 40 else "#EF4444")
                        st.markdown(ui.temiz_html(f"""<div style="display:flex;justify-content:space-between;padding:8px 12px;border-bottom:1px solid #1E293B"><span style="color:#E2E8F0;font-size:0.85rem">{tip}</span><span><span style="color:{renk};font-weight:700">%{v['basari_pct']:.0f}</span><span style="color:#64748B;font-size:0.75rem;margin-left:8px">{v['adet']} sinyal | ort %{v['ort_getiri']:+.1f}</span></span></div>"""), unsafe_allow_html=True)
            beklemede = [k for k in gecmis if k["sonuc"] is None]
            kapali = [k for k in gecmis if k["sonuc"] is not None]
            if beklemede:
                with st.expander(f"⏳ Beklemede ({len(beklemede)})"):
                    for k in beklemede:
                        st.markdown(f"**{k['kod']}** · {k['sinyal_tip']} · {k['giris_fiyat']:.2f}₺ → H:{k['hedef']:.2f} S:{k['stop']:.2f}")
            st.markdown("##### Kapanan Sinyaller")
            for k in sorted(kapali, key=lambda x: x.get("kontrol_tarih",""), reverse=True)[:30]:
                renk = "#10B981" if (k.get("getiri_pct") or 0) > 0 else "#EF4444"
                ikon = "🎯" if k["sonuc"]=="HEDEF" else ("🛑" if k["sonuc"]=="STOP" else "⏱")
                st.markdown(ui.temiz_html(f"""<div style="display:flex;justify-content:space-between;padding:7px 10px;border-bottom:1px solid #1E293B"><div><span style="color:#E2E8F0;font-weight:600">{k['kod']}</span><span style="color:#64748B;font-size:0.7rem;margin-left:6px">{k['sinyal_tip']}</span></div><div><span style="color:{renk};font-weight:700">{k.get('getiri_pct',0):+.1f}%</span><span style="color:#64748B;font-size:0.7rem;margin-left:6px">{ikon} {k['sonuc']}</span></div></div>"""), unsafe_allow_html=True)

    with alt2:
        st.markdown("#### 📈 Strateji Backtest")
        bt_kod = st.selectbox("Hisse", BIST_TUM, key="bt_kod")
        bt_vade = st.selectbox("Vade", list(VADE_AYAR.keys()), format_func=lambda k: VADE_AYAR[k]["ad"], key="bt_vade")
        if st.button("Backtest Çalıştır"):
            with st.spinner("Geçmiş test ediliyor..."):
                ayar = VADE_AYAR[bt_vade]
                df, durum = veri_al(bt_kod, gun=max(ayar["gun"], 400), min_gun=ayar["min_gun"], aralik=ayar["aralik"])
                if df is None:
                    st.error(f"Veri alınamadı: {durum}")
                else:
                    sonuc = bt.backtest_calistir(df, ayar, analiz_et, KOD_SEKTOR.get(bt_kod,"Diğer"))
                    if not sonuc or sonuc.get("islem_sayisi",0) == 0:
                        st.warning("Bu hisse/vadede geçmişte sinyal üretilmedi.")
                    else:
                        b1,b2,b3 = st.columns(3)
                        with b1: st.markdown(ui.istat_kutu("İŞLEM", sonuc["islem_sayisi"], "#38BDF8"), unsafe_allow_html=True)
                        with b2: st.markdown(ui.istat_kutu("BAŞARI", f"%{sonuc['basari_pct']:.0f}", "#10B981"), unsafe_allow_html=True)
                        with b3: st.markdown(ui.istat_kutu("BİLEŞİK", f"%{sonuc['toplam_bilesik']:+.0f}", "#F59E0B"), unsafe_allow_html=True)
                        st.markdown(f"Hedef: **{sonuc['hedef_tutan']}** | Stop: **{sonuc['stop_yiyen']}** | Ort.süre: **{sonuc['ort_gun']:.0f}g**")

# ──────────────────────────────────────────────────────────────
# SEKME 6: SEKTÖR ISI HARİTASI
# ──────────────────────────────────────────────────────────────
with sekmeler[6]:
    st.markdown("#### 🔥 Sektör Isı Haritası")
    if not st.session_state.tarama_yapildi or not st.session_state.sonuclar:
        st.info("Önce tarama yap — paranın hangi sektöre aktığını göster.")
    else:
        # Sektör rotasyonu — para nereden nereye akıyor (Katman 2)
        rot = pi.sektor_rotasyon(st.session_state.sonuclar)
        if rot and rot["giren"]:
            st.markdown(ui.temiz_html(f"""<div style="background:#0A1628;border-left:3px solid #00D4FF;border-radius:8px;padding:12px 14px;margin-bottom:14px"><div style="color:#00D4FF;font-size:0.7rem;font-weight:700;margin-bottom:4px">🧭 PARA AKIŞ YÖNÜ</div><div style="color:#E2E8F0;font-size:0.8rem">{pi.rotasyon_yorum(rot)}</div></div>"""), unsafe_allow_html=True)
            rc1, rc2 = st.columns(2)
            with rc1:
                st.markdown('<div style="color:#10B981;font-size:0.72rem;font-weight:700;margin-bottom:4px">▲ PARA GİREN</div>', unsafe_allow_html=True)
                for s in rot["giren"]:
                    st.markdown(ui.temiz_html(f"""<div style="color:#94A3B8;font-size:0.72rem;padding:2px 0">{s['sektor']} <span style="color:#10B981">%{s['momentum']:+.0f}</span> · {s['lider'] or '-'}</div>"""), unsafe_allow_html=True)
            with rc2:
                if rot["cikan"]:
                    st.markdown('<div style="color:#EF4444;font-size:0.72rem;font-weight:700;margin-bottom:4px">▼ PARA ÇIKAN</div>', unsafe_allow_html=True)
                    for s in rot["cikan"]:
                        st.markdown(ui.temiz_html(f"""<div style="color:#94A3B8;font-size:0.72rem;padding:2px 0">{s['sektor']} <span style="color:#EF4444">%{s['momentum']:+.0f}</span></div>"""), unsafe_allow_html=True)
            st.markdown("<div style='margin-bottom:12px'></div>", unsafe_allow_html=True)

            # Sektör momentum sıralaması (güce göre 1..N dizilmiş)
            if rot.get("tum") and len(rot["tum"]) >= 2:
                st.markdown('<div style="color:#A78BFA;font-size:0.75rem;font-weight:800;margin-bottom:6px">📊 SEKTÖR GÜÇ SIRALAMASI</div>', unsafe_allow_html=True)
                tum = rot["tum"]
                en_yuksek_akis = max(abs(s["akis"]) for s in tum) or 1
                for i, s in enumerate(tum, 1):
                    # Güç barı (akış skoruna göre)
                    oran = (s["akis"] / en_yuksek_akis) if s["akis"] > 0 else 0
                    bar_g = max(8, oran * 100)
                    renk = "#10B981" if s["akis"] > 5 else ("#F59E0B" if s["akis"] > -5 else "#EF4444")
                    madalya = ["🥇", "🥈", "🥉"][i-1] if i <= 3 else f"{i}."
                    st.markdown(ui.temiz_html(f"""<div style="display:flex;align-items:center;gap:8px;margin-bottom:4px"><span style="color:#64748B;font-size:0.7rem;width:24px">{madalya}</span><span style="color:#E2E8F0;font-size:0.74rem;width:130px;overflow:hidden">{s['sektor']}</span><div style="flex:1;background:#1E293B;border-radius:4px;height:14px"><div style="width:{bar_g}%;height:14px;border-radius:4px;background:{renk}"></div></div><span style="color:{renk};font-size:0.68rem;font-weight:700;width:48px;text-align:right">%{s['momentum']:+.0f}</span></div>"""), unsafe_allow_html=True)
                st.caption("Sıralama: momentum + akıllı para + fırsat yoğunluğu birleşik gücü. Lider sektördeki lider hisseler genelde en güvenli.")
                st.markdown("<div style='margin-bottom:12px'></div>", unsafe_allow_html=True)

        isi = bt.sektor_isi(st.session_state.sonuclar)
        if isi:
            max_guc = isi[0]["guc"]
            for s in isi:
                renk = bt.isi_renk(s["guc"], max_guc)
                genislik = max(15, (s["guc"] / max_guc) * 100)
                st.markdown(ui.temiz_html(f"""
                <div style="margin-bottom:8px">
                  <div style="display:flex;justify-content:space-between;margin-bottom:3px">
                    <span style="color:#E2E8F0;font-weight:600;font-size:0.85rem">{s['sektor']}</span>
                    <span style="color:{renk};font-size:0.75rem;font-weight:700">{s['adet']} fırsat · AP {s['ort_ap']:.0f}{' · 🐋'+str(s['buyuk_oyuncu']) if s['buyuk_oyuncu'] else ''}</span>
                  </div>
                  <div style="background:#1E293B;border-radius:5px;height:22px">
                    <div style="width:{genislik}%;height:22px;border-radius:5px;background:{renk};display:flex;align-items:center;padding-left:8px">
                      <span style="color:#0A0F1A;font-size:0.7rem;font-weight:700">%{s['ort_kazanc']:+.1f} ort</span>
                    </div>
                  </div>
                </div>
                """), unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────
# SEKME 7: ROBOT
# ──────────────────────────────────────────────────────────────
with sekmeler[7]:
    st.markdown("#### 🤖 Otomatik Strateji Robotu")
    st.caption("Sanal parayla kendi kendine al-sat yapar. Gerçeğe dökmeden stratejini test et.")

    rc1, rc2 = st.columns(2)
    with rc1:
        robot_mod = st.radio("Mod", ["disiplinli", "basit"],
            format_func=lambda x: "Disiplinli (risk + rotasyon)" if x == "disiplinli" else "Basit (hepsini al)")
    with rc2:
        robot_maxp = st.slider("Hedef kadro (pozisyon)", 3, 30, 15)

    rc3, rc4 = st.columns(2)
    with rc3:
        robot_minpuan = st.slider("Min puan", 0, 90, 50, 5)
    with rc4:
        robot_bakiye = st.number_input("Robot bakiyesi (₺)", 1000, 100_000_000, 100_000, 1000)

    robot_ayar = {
        "mod": robot_mod, "max_pozisyon": robot_maxp,
        "min_puan": robot_minpuan, "rotasyon_esigi": 10, "pozisyon_risk": 0.02,
        "cooldown_tur": 3,
    }

    rb1, rb2 = st.columns(2)
    with rb1:
        if st.button("🤖 Robotu Kur / Sıfırla", use_container_width=True):
            rcz = cz.cuzdan_olustur(robot_bakiye)
            st.session_state.robot_cuzdan = rcz
            st.session_state.robot_log = []
            st.session_state.robot_cooldown = {}
            st.session_state.robot_deger_gecmis = []
            st.session_state.robot_baslangic = robot_bakiye
            st.rerun()
    with rb2:
        calistir = st.button("▶️ Canlı Tur Çalıştır", use_container_width=True)

    if st.session_state.robot_cuzdan is None:
        st.info("Önce robotu kur. Sonra tarama yapıp 'Canlı Tur Çalıştır'a bas — robot karar versin.")
    else:
        rcz = st.session_state.robot_cuzdan
        if calistir:
            if not st.session_state.sonuclar:
                st.error("Önce Tarama sekmesinden tarama yap.")
            else:
                # Piyasa rejimi freni: kötü piyasada robot savunmaya geçer
                fren = pi.piyasa_rejimi_freni(st.session_state.get("rejim", ""), st.session_state.get("xu100_pct", 0))
                olaylar = rb.canli_adim(rcz, st.session_state.sonuclar, guncel_fiyatlar(), robot_ayar, cz, st.session_state.robot_cooldown, fren=fren)
                zaman = datetime.datetime.now().strftime("%H:%M")
                st.session_state.robot_log = [f"[{zaman}] {o}" for o in olaylar] + st.session_state.robot_log
                # Karne için değer snapshot'ı al
                _rozet = cz.portfoy_degeri(rcz, guncel_fiyatlar())
                pf.anlik_kaydet(st.session_state.robot_deger_gecmis, _rozet["toplam"],
                                _rozet["nakit"], len(_rozet["pozisyonlar"]), st.session_state.xu100_pct)
                st.rerun()

        # Robot durumu
        rozet = cz.portfoy_degeri(rcz, guncel_fiyatlar())
        m1, m2, m3 = st.columns(3)
        with m1:
            st.markdown(ui.istat_kutu("ROBOT DEĞERİ", f"{rozet['toplam']:,.0f}₺", "#38BDF8"), unsafe_allow_html=True)
        with m2:
            renk = "#10B981" if rozet["toplam_kar"] >= 0 else "#EF4444"
            st.markdown(ui.istat_kutu("K/Z", f"{rozet['toplam_kar']:+,.0f}₺", renk), unsafe_allow_html=True)
        with m3:
            st.markdown(ui.istat_kutu("AÇIK POZ", len(rozet["pozisyonlar"]), "#F59E0B"), unsafe_allow_html=True)

        # XU100 kıyası
        st.caption(f"Robot getirisi: %{rozet['toplam_kar_pct']:+.2f} | XU100 aylık: %{st.session_state.xu100_pct:+.1f} → "
                   f"{'Robot endeksi yeniyor ✓' if rozet['toplam_kar_pct'] > st.session_state.xu100_pct else 'Endeks önde'}")

        # Piyasa rejimi freni durumu (robotun risk modu)
        if st.session_state.get("tarama_yapildi"):
            fren = pi.piyasa_rejimi_freni(st.session_state.get("rejim", ""), st.session_state.get("xu100_pct", 0))
            st.markdown(ui.temiz_html(f"""<div style="background:{fren['renk']}18;border-left:3px solid {fren['renk']};border-radius:8px;padding:8px 12px;margin:8px 0"><span style="color:{fren['renk']};font-size:0.75rem;font-weight:700">🛡️ {fren['mod']}</span><div style="color:#94A3B8;font-size:0.68rem;margin-top:2px">{fren['mesaj']}</div></div>"""), unsafe_allow_html=True)

        # ── ROBOT KARNESİ (öz-puanlama + dönemsel getiri) ──
        st.markdown("---")
        st.markdown("##### 🎓 Robot Karnesi")
        deger_gec = st.session_state.robot_deger_gecmis
        if len(deger_gec) < 1:
            st.info("Robot henüz tur çalıştırmadı. 'Canlı Tur Çalıştır'a bastıkça karne oluşur. (Gün gün birikmesi için Supabase bağla — sol panel.)")
        else:
            dg = pf.donemsel_getiri(deger_gec, st.session_state.robot_baslangic)
            karne_oz = gc.performans_ozet(st.session_state.gecmis)
            puan = pf.oz_puanlama(karne_oz, dg, st.session_state.xu100_pct)

            # Öz-puan kartı
            st.markdown(ui.temiz_html(f"""<div style="background:#0D1117;border:1px solid #1E293B;border-left:4px solid {puan['renk']};border-radius:12px;padding:16px;margin-bottom:12px"><div style="display:flex;justify-content:space-between;align-items:center"><div><div style="color:#94A3B8;font-size:0.7rem">ROBOT ÖZ-PUANI</div><div style="display:flex;align-items:baseline;gap:8px"><span style="color:{puan['renk']};font-size:2.4rem;font-weight:800">{puan['harf']}</span><span style="color:#E2E8F0;font-size:1rem;font-weight:600">{puan['puan']}/100</span></div></div><div style="text-align:right;max-width:50%"><div style="color:{puan['renk']};font-size:0.8rem;font-weight:600">{puan['yorum']}</div></div></div></div>"""), unsafe_allow_html=True)

            # Puan kırılımı
            with st.expander("📊 Puan Kırılımı"):
                for ad, alinan, max_p, aciklama in puan["detay"]:
                    oran = (alinan / max_p * 100) if max_p > 0 else 0
                    brenk = "#10B981" if oran >= 70 else ("#F59E0B" if oran >= 40 else "#EF4444")
                    st.markdown(ui.temiz_html(f"""<div style="margin-bottom:8px"><div style="display:flex;justify-content:space-between;font-size:0.75rem"><span style="color:#94A3B8">{ad} <span style="color:#64748B">({aciklama})</span></span><span style="color:{brenk};font-weight:700">{alinan}/{max_p}</span></div><div style="background:#1E293B;border-radius:3px;height:4px;margin-top:3px"><div style="width:{oran}%;height:4px;border-radius:3px;background:{brenk}"></div></div></div>"""), unsafe_allow_html=True)

            # Dönemsel getiri tablosu
            st.markdown("###### Dönemsel Getiri")
            dn1, dn2, dn3, dn4 = st.columns(4)
            for kol, (etiket, anahtar) in zip([dn1,dn2,dn3,dn4],
                [("GÜNLÜK","gunluk"),("HAFTALIK","haftalik"),("AYLIK","aylik"),("YILLIK","yillik")]):
                v = dg[anahtar]
                renk = "#10B981" if v["pct"] >= 0 else "#EF4444"
                with kol:
                    st.markdown(ui.temiz_html(f"""<div style="background:#0D1117;border:1px solid #1E293B;border-radius:8px;padding:10px;text-align:center"><div style="color:#64748B;font-size:0.6rem">{etiket}</div><div style="color:{renk};font-size:1rem;font-weight:700">%{v['pct']:+.1f}</div><div style="color:#475569;font-size:0.62rem">{v['tl']:+,.0f}₺</div></div>"""), unsafe_allow_html=True)

            # Değer grafiği
            seri = pf.deger_serisi(deger_gec)
            if len(seri) >= 2:
                st.markdown("###### Portföy Değeri Seyri")
                import pandas as _pd
                df_seri = _pd.DataFrame(seri, columns=["tarih","değer"]).set_index("tarih")
                st.line_chart(df_seri, height=180)

            # Risk-düzeltilmiş kalite (Sharpe/Sortino/Max Drawdown)
            risk = pf.risk_metrikleri(deger_gec)
            if risk:
                st.markdown("###### 🎯 Risk-Düzeltilmiş Kalite")
                st.markdown(ui.temiz_html(f"""<div style="background:#0D1117;border:1px solid {risk['renk']}55;border-left:4px solid {risk['renk']};border-radius:10px;padding:12px 14px;margin-bottom:8px"><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px"><span style="color:{risk['renk']};font-size:0.9rem;font-weight:800">{risk['kalite']}</span><span style="color:#94A3B8;font-size:0.7rem">{'✓ Mevduatı yeniyor' if risk['mevduati_yeniyor'] else '⚠ Mevduatın altında'}</span></div><div style="color:#94A3B8;font-size:0.72rem;line-height:1.4">{risk['yorum']}</div></div>"""), unsafe_allow_html=True)
                rm1, rm2, rm3 = st.columns(3)
                with rm1: st.markdown(ui.istat_kutu("SHARPE", risk["sharpe"], risk["renk"]), unsafe_allow_html=True)
                with rm2: st.markdown(ui.istat_kutu("SORTINO", risk["sortino"], "#34D399"), unsafe_allow_html=True)
                with rm3: st.markdown(ui.istat_kutu("MAX DÜŞÜŞ", f"%{risk['max_dd']}", "#EF4444"), unsafe_allow_html=True)
                st.caption(f"Sharpe = risk başına getiri (>1 iyi, >2 mükemmel) · Sortino = kötü dalgalanma başına getiri · Max Düşüş = en kötü tepe-dip · Risksiz: %{risk['risksiz_yillik']:.0f} (TL mevduat)")

        if rozet["pozisyonlar"]:
            with st.expander(f"📦 Robotun Portföyü ({len(rozet['pozisyonlar'])})"):
                for p in sorted(rozet["pozisyonlar"], key=lambda x: x["kar"], reverse=True):
                    st.markdown(ui.temiz_html(f"""
                    <div style="display:flex;justify-content:space-between;padding:6px 10px;border-bottom:1px solid #1E293B">
                      <span style="color:#E2E8F0;font-weight:600">{p['kod']} · {p['lot']:,} lot</span>
                      <span style="color:{'#10B981' if p['kar']>=0 else '#EF4444'}">{p['kar']:+,.0f}₺ (%{p['kar_pct']:+.1f})</span>
                    </div>
                    """), unsafe_allow_html=True)

        if st.session_state.robot_log:
            st.markdown("##### 📋 Robot Günlüğü")
            for satir in st.session_state.robot_log[:40]:
                st.markdown(f"<div style='color:#94A3B8;font-size:0.78rem;padding:3px 0'>{satir}</div>", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────
# SEKME 8: YOL HARİTASI (projenin hafızası + vizyon)
# ──────────────────────────────────────────────────────────────
with sekmeler[8]:
    st.markdown("#### 🧭 Yol Haritası & Vizyon")

    # Güvenli erişim — durum.py / yol_haritasi.py eski/uyumsuz olsa bile sekme (ve tüm uygulama) çökmez
    _surum = getattr(dr, "SURUM", "v4")
    _su_an = getattr(dr, "SU_AN", {}) or {}
    _asama = _su_an.get("asama", "Geliştirme aşamasında")
    _siradaki = _su_an.get("siradaki_adim", "—")
    _deploy_adimlari = getattr(dr, "DEPLOY_ADIMLARI", []) or []
    _tamamlanan = getattr(yh, "TAMAMLANAN", []) or []
    _katmanlar = getattr(yh, "KATMANLAR", []) or []
    _ek_fikirler = getattr(yh, "EK_FIKIRLER", []) or []

    # Kalibrasyon olgunluğu — sistem ne kadar öğrendi? (Katman 1)
    kd = klb.kalibrasyon_durumu(st.session_state.get("gecmis", []))
    olg_renk = "#10B981" if kd["hazir"] else ("#F59E0B" if kd["olgunluk_yuzde"] > 0 else "#64748B")
    st.markdown(ui.temiz_html(f"""<div style="background:#0D1117;border:1px solid {olg_renk}55;border-radius:10px;padding:10px 14px;margin-bottom:10px"><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:5px"><span style="color:{olg_renk};font-size:0.76rem;font-weight:800">🧠 SİSTEM OLGUNLUĞU (Kalibrasyon)</span><span style="color:{olg_renk};font-size:0.7rem;font-weight:700">{kd['kapali_sinyal']} sinyal · %{kd['olgunluk_yuzde']}</span></div><div style="background:#1E293B;border-radius:4px;height:6px;margin-bottom:5px"><div style="width:{max(2,kd['olgunluk_yuzde'])}%;height:6px;border-radius:4px;background:{olg_renk}"></div></div><div style="color:#94A3B8;font-size:0.68rem;line-height:1.4">{kd['mesaj']}</div></div>"""), unsafe_allow_html=True)


    # Kullanım rehberi (tüm özellikler özet)
    with st.expander("📖 Kullanım Rehberi — tüm özellikler nasıl çalışır?"):
        st.markdown("""**🧠 Her hisse 10 katmandan geçer:** veri → teknik → akıllı para → niyet → rüzgar → alarm → volatilite → karakter(DNA) → hacim → zaman dilimi → **tek KARAR**.

**📱 Sekmeler:**
- **📡 Radar**: nişan ekranı — sadece aksiyon gerektirenler + piyasa sağlığı
- **🎯 Av Panosu**: kişisel durum, günlük hedef, yığılma uyarısı
- **📊 Tarama**: tüm fırsatlar, kart kart + grafik
- **💼 Cüzdan**: sanal alım-satım (paper trading)
- **⭐ İzleme**: takip + alarm + "keşke alsaydın"
- **📈 Backtest**: geçmiş test + sinyal karnesi
- **🔥 Isı Haritası**: para akış yönü + sektör
- **🤖 Robot**: otomatik işlem + karne + Sharpe + rejim freni
- **🧭 Yol Haritası**: bu sekme

**🃏 Kart okuma:** En üstte karar şeridi (ŞİMDİ AL / İZLE / UZAK DUR) + AV SKORU. Kart titreşiyorsa kritik olay yakın. Grafiğe dokun → DNA, kurumsal seviyeler, volatilite.

**🛡️ Seni koruyanlar:** manipülasyon tespiti, karşı rüzgar, zaman dilimi çelişkisi, yığılma uyarısı, volatilite adaptasyonu, rejim freni, ıraksama uyarısı.

**💡 İpucu:** Güne Radar'dan başla. UZAK DUR'a saygı göster. Robot karnesinde Sharpe'a bak — yüksek getiri tek başına yetmez.

*Tam rehber için REHBER.md dosyasına bak.*""")

    # ŞU AN BURADAYIZ — kontrol noktası şeridi
    st.markdown(ui.temiz_html(f"""<div style="background:linear-gradient(135deg,#00D4FF22,#0A2540);border:1px solid #00D4FF;border-radius:10px;padding:14px 16px;margin-bottom:14px"><div style="color:#00D4FF;font-size:0.7rem;font-weight:700;letter-spacing:1px;margin-bottom:4px">📍 ŞU AN BURADAYIZ — {_surum}</div><div style="color:#E2E8F0;font-size:0.85rem;font-weight:600;margin-bottom:6px">{_asama}</div><div style="color:#94A3B8;font-size:0.76rem"><b style="color:#38BDF8">Sıradaki adım:</b> {_siradaki}</div></div>"""), unsafe_allow_html=True)
    with st.expander("📋 Deploy Adımları (eve gidince)"):
        for a in _deploy_adimlari:
            st.markdown(a)
    st.markdown(ui.temiz_html("""<div style="background:#0A1628;border-left:3px solid #00D4FF;border-radius:8px;padding:12px 14px;margin-bottom:14px"><div style="color:#94A3B8;font-size:0.78rem;line-height:1.5"><b style="color:#E2E8F0">Felsefe:</b> Piyasa uyarlanır bir sistemdir. Bir kenar bulunup kullanıldıkça aşınır — kalıcı zirve yoktur, zirve ona çıktıkça yer değiştirir. Asıl kazanan zirveyi bulan değil, zirve kayınca en hızlı yeniden konumlanan sistemdir. Hedefimiz bitmiş program değil, kendini sürekli yeniden icat eden bir organizma.</div></div>"""), unsafe_allow_html=True)

    st.markdown(f"##### ✅ Tamamlananlar ({len(_tamamlanan)})")
    with st.expander("Bugüne kadar yapılanlar"):
        for ad, durum in _tamamlanan:
            st.markdown(f"{durum} {ad}")

    st.markdown("##### 🧭 Katmanlar — Zirve Kaydıkça Kovalamak")
    durum_renk = {"🎯":"#00D4FF", "🔨":"#F59E0B", "🔭":"#94A3B8", "🔒":"#EF4444", "✅":"#10B981"}
    for k in _katmanlar:
        renk = durum_renk.get(k.get("durum",""), "#94A3B8")
        st.markdown(ui.temiz_html(f"""<div style="background:#0D1117;border:1px solid #1E293B;border-left:3px solid {renk};border-radius:10px;padding:12px 14px;margin-bottom:8px"><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px"><span style="color:#E2E8F0;font-weight:700;font-size:0.9rem">{k.get('durum','')} Katman {k.get('no','?')}: {k.get('ad','')}</span></div><div style="color:#94A3B8;font-size:0.76rem;line-height:1.45;margin-bottom:6px">{k.get('ozet','')}</div><div style="color:#64748B;font-size:0.7rem;line-height:1.4"><b>Nasıl:</b> {k.get('nasil','')}</div><div style="color:#475569;font-size:0.68rem;margin-top:4px"><b>Önkoşul:</b> {k.get('onkosul','')}</div></div>"""), unsafe_allow_html=True)

    st.markdown("##### 💡 Akla Gelen Ek Fikirler")
    with st.expander("Kaybolmasın diye — ileride değerlendirilecekler"):
        for f in _ek_fikirler:
            st.markdown(f"• {f}")

st.markdown(ui.temiz_html("""
<div style="text-align:center;color:#334155;font-size:0.68rem;padding:20px 0 10px 0;border-top:1px solid #1E293B;margin-top:24px">
BIST Para Avcısı v4.0 · Yatırım tavsiyesi değildir · Teknik analize dayanır · Veriler gecikmeli olabilir
</div>
"""), unsafe_allow_html=True)
