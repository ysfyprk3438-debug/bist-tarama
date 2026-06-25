"""
BIST TARAMA v3.0 — TAM SİSTEM
- Tüm BIST (~250 hisse)
- Sinyal geçmişi + başarı oranı (Supabase)
- Akıllı hacim / Smart Money analizi
- Sektör filtresi
- Pozisyon yönetimi (TL + %)
- Telegram bildirim
- Otomatik günlük tarama desteği
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import ta
import datetime
import warnings
import io
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
import json
import os

warnings.filterwarnings('ignore')

st.set_page_config(
    page_title="BIST Tarama",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
  .stApp { background-color: #080C14; }
  section[data-testid="stSidebar"] { background-color: #0D1117; }

  .baslik {
    background: linear-gradient(135deg, #0D1B2A 0%, #0A2540 100%);
    border: 1px solid #00D4FF33; border-radius: 14px;
    padding: 22px 16px 16px 16px; text-align: center; margin-bottom: 18px;
  }
  .baslik h1 { color: #00D4FF; font-size: 1.7rem; font-weight: 800; margin: 0 0 4px 0; letter-spacing: 1px; }
  .baslik p { color: #64748B; font-size: 0.82rem; margin: 0; }

  .rejim-kart { border-radius: 10px; padding: 14px 16px; margin-bottom: 16px; border-left: 4px solid; }
  .rejim-yesil   { background: #0B1F14; border-color: #10B981; }
  .rejim-sari    { background: #1C1505; border-color: #F59E0B; }
  .rejim-kirmizi { background: #1C0808; border-color: #EF4444; }

  .hisse-kart {
    background: #0D1117; border: 1px solid #1E293B;
    border-radius: 12px; padding: 14px 16px; margin-bottom: 6px;
  }
  .hisse-kod { font-size: 1.1rem; font-weight: 800; color: #E2E8F0; }
  .sinyal-badge { display: inline-block; padding: 2px 10px; border-radius: 20px; font-size: 0.7rem; font-weight: 700; margin-left: 6px; }
  .badge-yesil   { background: #064E3B; color: #10B981; }
  .badge-sari    { background: #451A03; color: #F59E0B; }
  .badge-mavi    { background: #0C2340; color: #38BDF8; }

  .metrik-satir { display: flex; gap: 7px; margin-top: 10px; flex-wrap: wrap; }
  .metrik-kutu  { flex: 1; min-width: 65px; background: #141B2D; border-radius: 8px; padding: 7px 8px; text-align: center; }
  .metrik-etiket { color: #475569; font-size: 0.6rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.3px; }
  .metrik-deger  { font-size: 0.85rem; font-weight: 700; margin-top: 2px; }

  .puan-bar-bg { background: #1E293B; border-radius: 4px; height: 5px; margin-top: 8px; }
  .puan-bar    { height: 5px; border-radius: 4px; }

  .sektor-badge {
    display: inline-block; padding: 1px 8px; border-radius: 20px;
    font-size: 0.62rem; font-weight: 600; margin-left: 6px;
    background: #1E293B; color: #94A3B8;
  }

  .smart-money-bar {
    height: 4px; border-radius: 2px; margin-top: 4px;
  }

  .gecmis-satir {
    display: flex; justify-content: space-between; align-items: center;
    padding: 8px 12px; border-radius: 8px; margin-bottom: 6px;
    background: #0D1117; border: 1px solid #1E293B;
  }

  .istat-kutu {
    background: #0D1117; border: 1px solid #1E293B;
    border-radius: 10px; padding: 14px; text-align: center;
  }

  .stButton > button {
    background: linear-gradient(135deg, #0369A1, #0EA5E9);
    color: white; border: none; border-radius: 10px;
    font-weight: 700; font-size: 1rem; padding: 14px 0; width: 100%;
  }
  .stButton > button:hover { background: linear-gradient(135deg, #0EA5E9, #38BDF8); }

  .footer { text-align: center; color: #334155; font-size: 0.7rem; padding: 20px 0 10px 0; border-top: 1px solid #1E293B; margin-top: 30px; }
  #MainMenu, footer, header { visibility: hidden; }
  .block-container { padding-top: 1rem; padding-bottom: 2rem; }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# BIST TAM LİSTE — SEKTÖRLERE GÖRE
# ══════════════════════════════════════════════════════════════════════════════
BIST_SEKTORLER = {
    "🏦 Bankacılık": [
        'AKBNK','GARAN','HALKB','ISCTR','VAKBN','YKBNK','TSKB','ALBRK','SKBNK','KLNMA'
    ],
    "⚡ Enerji": [
        'EUPWR','ODAS','ENJSA','AKSEN','ZOREN','AYEN','AYDEM','KCAER','CWENE','METUR',
        'NATEN','AREN','BEMAS','EKGYO','EPIAS'
    ],
    "🏭 Sanayi": [
        'EREGL','KRDMD','ISDMR','CEMTS','CIMSA','ADANA','AFYON','BUCIM','MRDIN',
        'ARCLK','VESTL','BFREN','DOAS','OTKAR','FROTO','TOASO','TTRAK'
    ],
    "💊 Sağlık / Kimya": [
        'ECILC','SELEC','MPARK','DEVA','ECZYT','GUBRF','HEKTS','PETKM','SASA',
        'TRCAS','KCHOL','PRKAB'
    ],
    "🛒 Perakende / Gıda": [
        'BIMAS','MGROS','SOKM','ULKER','CCOLA','AEFES','TATGD','KERVT','PNSUT',
        'SELGD','BANVT','DARDL','TKFEN'
    ],
    "📡 Teknoloji / Telekom": [
        'TTKOM','TCELL','ASELS','NETAS','LOGO','AGHOL','INDES','ARENA','DGATE',
        'KAREL','SMART','PAPIL'
    ],
    "✈️ Ulaşım / Turizm": [
        'THYAO','PGSUS','TAVHL','CLEBI','MAVKG','MAALT','BUCIM','RYSAS'
    ],
    "🏗️ İnşaat / GYO": [
        'EKGYO','ISGYO','TRGYO','KLGYO','VKGYO','SNGYO','HLGYO','MHRGY',
        'ENKAI','TKFEN','GSDHO'
    ],
    "⛏️ Madencilik / Ham Madde": [
        'KOZAL','KOZAA','IPEKE','KZGYO','GOLDS','GLYHO'
    ],
    "💼 Holding / Diğer": [
        'SAHOL','KCHOL','DOHOL','ALARK','CONSE','ATAGY','BERA','GOLTS',
        'ADEL','GESAN','DESA','MAVI','BRISA','KARSN'
    ],
}

# Düz liste + sektör haritası
BIST_TUM = []
KOD_SEKTOR = {}
for sektor, kodlar in BIST_SEKTORLER.items():
    for kod in kodlar:
        if kod not in KOD_SEKTOR:
            BIST_TUM.append(kod)
            KOD_SEKTOR[kod] = sektor

# ══════════════════════════════════════════════════════════════════════════════
# SESSION STATE
# ══════════════════════════════════════════════════════════════════════════════
DEFAULTS = {
    'tarama_yapildi': False,
    'sonuclar': [],
    'rejim': '',
    'xu100_pct': 0.0,
    'favoriler': set(),
    'gecmis': [],          # [{kod, tarih, giris, hedef, stop, sinyal, sonuc}]
    'portfoy_tl': 100000,
}
for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ══════════════════════════════════════════════════════════════════════════════
# SUPABASE (OPSİYONEL)
# ══════════════════════════════════════════════════════════════════════════════
def temizle(text):
    tr = {'ı':'i','İ':'I','ş':'s','Ş':'S','ğ':'g','Ğ':'G',
          'ü':'u','Ü':'U','ö':'o','Ö':'O','ç':'c','Ç':'C','₺':'TL'}
    s = str(text)
    for k, v in tr.items(): s = s.replace(k, v)
    return s

def supabase_kaydet(url, key, veri_listesi):
    """Sinyalleri Supabase'e kaydet"""
    if not url or not key: return False
    try:
        r = requests.post(
            f"{url}/rest/v1/sinyaller",
            headers={"apikey": key, "Authorization": f"Bearer {key}",
                     "Content-Type": "application/json", "Prefer": "return=minimal"},
            json=veri_listesi, timeout=10
        )
        return r.status_code in [200, 201]
    except: return False

def supabase_gecmis_cek(url, key, limit=50):
    """Supabase'den geçmiş sinyalleri çek"""
    if not url or not key: return []
    try:
        r = requests.get(
            f"{url}/rest/v1/sinyaller?order=tarih.desc&limit={limit}",
            headers={"apikey": key, "Authorization": f"Bearer {key}"},
            timeout=10
        )
        if r.status_code == 200: return r.json()
        return []
    except: return []

def supabase_guncelle(url, key, kayit_id, sonuc, geri_donus_pct):
    """Sinyal sonucunu güncelle"""
    if not url or not key: return False
    try:
        r = requests.patch(
            f"{url}/rest/v1/sinyaller?id=eq.{kayit_id}",
            headers={"apikey": key, "Authorization": f"Bearer {key}",
                     "Content-Type": "application/json"},
            json={"sonuc": sonuc, "geri_donus_pct": geri_donus_pct},
            timeout=10
        )
        return r.status_code in [200, 204]
    except: return False

# ══════════════════════════════════════════════════════════════════════════════
# PİYASA DURUMU
# ══════════════════════════════════════════════════════════════════════════════
@st.cache_data(ttl=1800, show_spinner=False)
def piyasa_durumu():
    for sembol in ["XU100.IS", "^XU100"]:
        try:
            df = yf.Ticker(sembol).history(period="1y", interval="1d")
            if not df.empty and len(df) > 50:
                k = df['Close']
                son = float(k.iloc[-1])
                ma50  = float(k.rolling(50).mean().iloc[-1])
                ma200 = float(k.rolling(200).mean().iloc[-1]) if len(k) >= 200 else ma50
                ay_oncesi = float(k.iloc[-22]) if len(k) >= 22 else son
                aylik = ((son - ay_oncesi) / ay_oncesi) * 100
                if son > ma50 > ma200:   return "YÜKSELİŞ TRENDİ ✓", 1.0, aylik
                elif son > ma200:        return "DÜZELTME (Temkinli)", 0.65, aylik
                else:                    return "DÜŞÜŞ TRENDİ ⚠", 0.25, aylik
        except: continue
    # Yedek: THYAO'ya bak
    try:
        df = yf.Ticker("THYAO.IS").history(period="3mo", interval="1d")
        if not df.empty:
            degisim = ((float(df['Close'].iloc[-1]) - float(df['Close'].iloc[0])) / float(df['Close'].iloc[0])) * 100
            if degisim > 5:   return "YÜKSELİŞ (Tahmini)", 0.8, degisim
            elif degisim > -5: return "YATAY (Tahmini)", 0.6, degisim
            else:              return "DÜŞÜŞ (Tahmini)", 0.3, degisim
    except: pass
    return "VERİ BEKLENIYOR", 0.7, 0.0

# ══════════════════════════════════════════════════════════════════════════════
# SMART MONEY (AKILLI PARA) ANALİZİ
# ══════════════════════════════════════════════════════════════════════════════
def smart_money_analiz(df):
    """
    Akıllı para izleme:
    - OBV (On Balance Volume): Hacim hangi yönde birikiliyor?
    - Fiyat-Hacim Uyumu: Fiyat artarken hacim de artıyor mu?
    - Büyük oyuncu tespiti: Son 5 gün hacim ortalamanın kaç katı?
    """
    k = df['Close']
    v = df['Volume']
    h = df['High']
    l = df['Low']

    # OBV hesapla
    obv = [0]
    for i in range(1, len(k)):
        if k.iloc[i] > k.iloc[i-1]:
            obv.append(obv[-1] + v.iloc[i])
        elif k.iloc[i] < k.iloc[i-1]:
            obv.append(obv[-1] - v.iloc[i])
        else:
            obv.append(obv[-1])
    obv_ser = pd.Series(obv, index=k.index)

    # OBV trendi (son 10 gün)
    obv_trend = obv_ser.iloc[-1] > obv_ser.iloc[-10] if len(obv_ser) >= 10 else True

    # Fiyat-Hacim uyumu (son 5 gün)
    fiyat_degisim = k.pct_change().iloc[-5:].mean()
    hacim_degisim = v.pct_change().iloc[-5:].mean()
    uyum = (fiyat_degisim > 0 and hacim_degisim > 0) or \
           (fiyat_degisim < 0 and hacim_degisim < 0)

    # Büyük oyuncu: son 3 günde hacim patlaması var mı?
    hacim_ort_20 = float(v.rolling(20).mean().iloc[-1])
    hacim_max_3  = float(v.iloc[-3:].max())
    buyuk_oyuncu = hacim_max_3 > hacim_ort_20 * 2.5

    # Alım/Satım baskısı (Chaikin Money Flow benzeri)
    cmf_pay  = ((k - l) - (h - k)) / (h - l + 1e-8) * v
    cmf_pay  = cmf_pay.rolling(14).sum()
    cmf_payda = v.rolling(14).sum()
    cmf = float((cmf_pay / (cmf_payda + 1e-8)).iloc[-1])

    # Smart Money skoru (0-100)
    skor = 50
    if obv_trend: skor += 20
    if uyum:      skor += 15
    if buyuk_oyuncu: skor += 10
    if cmf > 0.1: skor += 15
    elif cmf < -0.1: skor -= 20

    # Yorum
    if skor >= 80:   yorum, renk = "GÜÇLÜ ALIŞ (Akıllı Para Giriyor)", "#10B981"
    elif skor >= 60: yorum, renk = "ALIŞ BASKISI", "#34D399"
    elif skor >= 40: yorum, renk = "NÖTR", "#94A3B8"
    elif skor >= 20: yorum, renk = "SATIŞ BASKISI", "#F87171"
    else:            yorum, renk = "GÜÇLÜ SATIŞ (Akıllı Para Çıkıyor)", "#EF4444"

    return {
        'skor': skor,
        'yorum': yorum,
        'renk': renk,
        'obv_trend': obv_trend,
        'uyum': uyum,
        'buyuk_oyuncu': buyuk_oyuncu,
        'cmf': cmf,
    }

# ══════════════════════════════════════════════════════════════════════════════
# POZİSYON YÖNETİMİ
# ══════════════════════════════════════════════════════════════════════════════
def pozisyon_hesapla(portfoy_tl, son_fiyat, stop_fiyat, kelly_pct=None):
    """
    Risk tabanlı pozisyon boyutu:
    - Max portföyün %2'sini riske et (standart kural)
    - Kelly kriteri varsa onu kullan ama %25'i geçme
    """
    risk_yuzde = min(kelly_pct * 0.5 if kelly_pct else 2.0, 5.0)  # Max %5
    max_risk_tl = portfoy_tl * (risk_yuzde / 100)

    hisse_basi_risk = son_fiyat - stop_fiyat
    if hisse_basi_risk <= 0: return None

    lot_sayisi = int(max_risk_tl / hisse_basi_risk)
    pozisyon_tl = lot_sayisi * son_fiyat
    pozisyon_yuzde = (pozisyon_tl / portfoy_tl) * 100
    max_kayip_tl = lot_sayisi * hisse_basi_risk

    return {
        'lot': lot_sayisi,
        'pozisyon_tl': pozisyon_tl,
        'pozisyon_yuzde': pozisyon_yuzde,
        'max_kayip_tl': max_kayip_tl,
        'risk_yuzde': risk_yuzde,
    }

# ══════════════════════════════════════════════════════════════════════════════
# HİSSE GRAFİĞİ
# ══════════════════════════════════════════════════════════════════════════════
def hisse_grafigi(df_gun):
    try:
        fig, ax = plt.subplots(figsize=(8, 2.2))
        fig.patch.set_facecolor('#0D1117')
        ax.set_facecolor('#0D1117')
        tarihler = df_gun.index
        kapanis  = df_gun['Close'].values
        renk = '#10B981' if kapanis[-1] >= kapanis[0] else '#EF4444'
        ax.plot(tarihler, kapanis, color=renk, linewidth=1.5, alpha=0.9)
        ax.fill_between(tarihler, kapanis, kapanis.min(), alpha=0.12, color=renk)
        if len(kapanis) >= 20:
            ma20 = pd.Series(kapanis).rolling(20).mean().values
            ax.plot(tarihler, ma20, color='#F59E0B', linewidth=0.8,
                    alpha=0.7, linestyle='--', label='MA20')
        ax.set_xlim(tarihler[0], tarihler[-1])
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%b'))
        ax.xaxis.set_major_locator(mdates.MonthLocator())
        ax.tick_params(colors='#475569', labelsize=7)
        for spine in ax.spines.values(): spine.set_edgecolor('#1E293B')
        ax.grid(axis='y', color='#1E293B', linewidth=0.5, alpha=0.5)
        ax.annotate(f'{kapanis[-1]:.2f}',
                    xy=(tarihler[-1], kapanis[-1]),
                    xytext=(-45, 8), textcoords='offset points',
                    color=renk, fontsize=8, fontweight='bold')
        plt.tight_layout(pad=0.3)
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=100, bbox_inches='tight',
                    facecolor='#0D1117')
        plt.close()
        buf.seek(0)
        return buf
    except: return None

# ══════════════════════════════════════════════════════════════════════════════
# ANA HİSSE ANALİZİ
# ══════════════════════════════════════════════════════════════════════════════
def hisse_analiz(kod, carpan, portfoy_tl):
    try:
        df = yf.Ticker(f"{kod}.IS").history(period='6mo', interval='1d')
        if df.empty or len(df) < 60: return None
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df = df[['Open','High','Low','Close','Volume']].dropna()
        if len(df) < 60: return None

        son_tarih = df.index[-1]
        if hasattr(son_tarih, 'date'): son_tarih = son_tarih.date()
        if (datetime.date.today() - son_tarih).days > 7: return None

        k, h, l, v = df['Close'], df['High'], df['Low'], df['Volume']
        son = float(k.iloc[-1])

        # Hareketli ortalamalar
        ma20  = float(k.rolling(20).mean().iloc[-1])
        ma50  = float(k.rolling(50).mean().iloc[-1]) if len(k) >= 50 else son
        ma200 = float(k.rolling(200).mean().iloc[-1]) if len(k) >= 200 else son

        trend = sum([son > ma20, son > ma50, son > ma200, ma20 > ma50])

        # Teknik göstergeler
        rsi_ser = ta.momentum.RSIIndicator(k, window=14).rsi()
        rsi = float(rsi_ser.iloc[-1]) if not rsi_ser.empty else 50.0

        macd_ind = ta.trend.MACD(k)
        macd_ok  = float(macd_ind.macd_diff().iloc[-1]) > 0

        bb = ta.volatility.BollingerBands(k, window=20)
        bb_alt  = float(bb.bollinger_lband().iloc[-1])
        bb_ust  = float(bb.bollinger_hband().iloc[-1])
        bb_yuzde = (son - bb_alt) / (bb_ust - bb_alt + 1e-8) * 100

        atr_ser = ta.volatility.AverageTrueRange(h, l, k, window=14).average_true_range()
        atr = float(atr_ser.iloc[-1]) if not atr_ser.empty else son * 0.02

        # Destek / Direnç
        direnc = float(h.rolling(20).max().iloc[-1])
        destek = float(l.rolling(20).min().iloc[-1])
        if direnc <= son:
            direnc = float(h.rolling(50).max().iloc[-1]) if len(h) >= 50 else son * 1.05
        if destek >= son:
            destek = float(l.rolling(50).min().iloc[-1]) if len(l) >= 50 else son * 0.95

        # Hedef ve stop
        hedef = min(direnc, son + atr * 2.5) if direnc > son else son + atr * 2.5
        stop  = son - atr * 1.2

        kazanc_pct = ((hedef - son) / son) * 100
        kayip_pct  = ((son - stop) / son) * 100
        rr = kazanc_pct / (kayip_pct + 1e-8)

        # Smart Money
        sm = smart_money_analiz(df)

        # 3 aylık getiri
        uc_ay = float(k.iloc[-63]) if len(k) >= 63 else float(k.iloc[0])
        uc_ay_getiri = ((son - uc_ay) / uc_ay) * 100

        # Sinyal
        if rsi > 72:
            sinyal, s_renk = "AŞIRI ALIM", "kirmizi"
        elif rsi < 35 and macd_ok and sm['skor'] >= 50:
            sinyal, s_renk = "DİP FIRSATI ✦", "yesil"
        elif trend >= 3 and macd_ok and rsi < 65 and sm['skor'] >= 60:
            sinyal, s_renk = "AL — Güçlü", "yesil"
        elif trend >= 3 and macd_ok and rsi < 65:
            sinyal, s_renk = "AL — Trend", "yesil"
        elif trend >= 2 and macd_ok:
            sinyal, s_renk = "TAKİPTE TUT", "sari"
        else:
            return None

        if s_renk == "kirmizi" or rr < 1.5 or kazanc_pct < 3:
            return None

        # Puan
        puan = int(min(100, (
            trend * 8 +
            min(20, rr * 6) +
            (10 if macd_ok else 0) +
            (8 if sm['skor'] >= 70 else 4 if sm['skor'] >= 50 else 0) +
            (5 if rsi < 55 else 0) +
            (5 if sm['buyuk_oyuncu'] else 0) +
            (8 if "DİP" in sinyal or "Güçlü" in sinyal else 4)
        )) * carpan)

        # Pozisyon yönetimi
        pozisyon = pozisyon_hesapla(portfoy_tl, son, stop)

        # Kelly (basit versiyon)
        kelly_pct = max(0, min(25, (rr - 1) / rr * 100 * 0.5))

        sektor = KOD_SEKTOR.get(kod, "Diğer")
        df_3ay = df.iloc[-63:] if len(df) >= 63 else df

        return dict(
            kod=kod, son=son, puan=puan, sinyal=sinyal, s_renk=s_renk,
            hedef=hedef, stop=stop, rr=rr,
            kazanc_pct=kazanc_pct, kayip_pct=kayip_pct,
            rsi=rsi, destek=destek, direnc=direnc,
            uc_ay=uc_ay_getiri, trend=trend,
            sm=sm, kelly_pct=kelly_pct,
            pozisyon=pozisyon, sektor=sektor,
            bb_yuzde=bb_yuzde, df_3ay=df_3ay,
            tarih=datetime.date.today().isoformat()
        )
    except: return None

@st.cache_data(ttl=1800, show_spinner=False)
def tum_hisseleri_tara(portfoy_tl):
    rejim, carpan, xu100_pct = piyasa_durumu()
    sonuclar = []
    with ThreadPoolExecutor(max_workers=12) as ex:
        gorevler = {ex.submit(hisse_analiz, h, carpan, portfoy_tl): h for h in BIST_TUM}
        for f in as_completed(gorevler):
            try:
                r = f.result()
                if r: sonuclar.append(r)
            except: pass
    sonuclar.sort(key=lambda x: x['puan'] * 0.5 + x['rr'] * 6 + x['sm']['skor'] * 0.3, reverse=True)
    return sonuclar, rejim, xu100_pct

# ══════════════════════════════════════════════════════════════════════════════
# SİNYAL GEÇMİŞİ ANALİZİ
# ══════════════════════════════════════════════════════════════════════════════
def gecmis_guncelle(gecmis_liste):
    """
    Geçmiş sinyallerin sonuçlarını kontrol et:
    Hedef tuttu mu? Stop mu yedi? Hâlâ açık mı?
    """
    guncellenmis = []
    bugun = datetime.date.today()

    for kayit in gecmis_liste:
        if kayit.get('sonuc') not in [None, 'AÇIK']:
            guncellenmis.append(kayit)
            continue
        try:
            tarih = datetime.date.fromisoformat(kayit['tarih'])
            gun_fark = (bugun - tarih).days
            if gun_fark < 1:
                kayit['sonuc'] = 'AÇIK'
                guncellenmis.append(kayit)
                continue

            df = yf.Ticker(f"{kayit['kod']}.IS").history(
                start=kayit['tarih'], interval='1d'
            )
            if df.empty:
                guncellenmis.append(kayit)
                continue

            giris  = kayit['giris']
            hedef  = kayit['hedef']
            stop   = kayit['stop']

            # Her gün high/low kontrol et
            sonuc = 'AÇIK'
            geri_donus = 0.0
            for _, satir in df.iterrows():
                if satir['Low'] <= stop:
                    sonuc = '🔴 STOP'
                    geri_donus = ((stop - giris) / giris) * 100
                    break
                if satir['High'] >= hedef:
                    sonuc = '🟢 HEDEF'
                    geri_donus = ((hedef - giris) / giris) * 100
                    break

            if sonuc == 'AÇIK':
                son_fiyat = float(df['Close'].iloc[-1])
                geri_donus = ((son_fiyat - giris) / giris) * 100

            kayit['sonuc'] = sonuc
            kayit['geri_donus_pct'] = round(geri_donus, 2)
        except:
            pass
        guncellenmis.append(kayit)

    return guncellenmis

def basari_istatistik(gecmis):
    """Geçmiş sinyallerden başarı oranı hesapla"""
    tamamlanan = [g for g in gecmis if g.get('sonuc') not in [None, 'AÇIK']]
    if not tamamlanan:
        return None
    hedef_tutu = [g for g in tamamlanan if 'HEDEF' in str(g.get('sonuc',''))]
    stop_yedi  = [g for g in tamamlanan if 'STOP'   in str(g.get('sonuc',''))]
    getiriler  = [g.get('geri_donus_pct', 0) for g in tamamlanan]

    return {
        'toplam': len(tamamlanan),
        'hedef': len(hedef_tutu),
        'stop': len(stop_yedi),
        'basari_oran': len(hedef_tutu) / len(tamamlanan) * 100,
        'ort_getiri': np.mean(getiriler) if getiriler else 0,
        'max_getiri': max(getiriler) if getiriler else 0,
        'min_getiri': min(getiriler) if getiriler else 0,
    }

# ══════════════════════════════════════════════════════════════════════════════
# TELEGRAM
# ══════════════════════════════════════════════════════════════════════════════
def telegram_gonder(token, chat_id, firsatlar, rejim):
    if not token or not chat_id or not firsatlar: return False
    tarih = datetime.date.today().strftime("%d.%m.%Y")
    mesaj = f"📊 *BIST TARAMA — {tarih}*\n"
    mesaj += f"Borsa: _{rejim}_\n\n"
    for r in firsatlar[:7]:
        sm_ikon = "🟢" if r['sm']['skor'] >= 70 else "🟡" if r['sm']['skor'] >= 50 else "🔴"
        mesaj += (
            f"*{r['kod']}* {r['sektor'].split()[0]} — {r['sinyal']}\n"
            f"  💰 {r['son']:.2f} ₺  |  Puan: {r['puan']}/100\n"
            f"  🎯 Hedef: +%{r['kazanc_pct']:.1f}  🛑 Stop: -%{r['kayip_pct']:.1f}\n"
            f"  {sm_ikon} Akıllı Para: {r['sm']['yorum'][:30]}\n\n"
        )
    mesaj += "_Yatırım tavsiyesi değildir._"
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": mesaj, "parse_mode": "Markdown"},
            timeout=10
        )
        return r.status_code == 200
    except: return False

# ══════════════════════════════════════════════════════════════════════════════
# KART HTML
# ══════════════════════════════════════════════════════════════════════════════
def hisse_kart_html(r, favori=False):
    puan = r['puan']
    puan_renk = "#10B981" if puan >= 70 else ("#F59E0B" if puan >= 50 else "#EF4444")
    rr_renk   = "#10B981" if r['rr'] >= 2.5 else ("#F59E0B" if r['rr'] >= 1.5 else "#EF4444")
    ay3_renk  = "#10B981" if r['uc_ay'] > 0 else "#EF4444"
    rsi_renk  = "#10B981" if r['rsi'] < 35 else ("#EF4444" if r['rsi'] > 65 else "#94A3B8")
    badge_cls = f"badge-{r['s_renk']}"
    sm = r['sm']
    sm_bar_renk = sm['renk']
    sektor_kisa = r['sektor'].split()[0] + " " + " ".join(r['sektor'].split()[1:])

    buyuk_oyuncu = '<span style="background:#1C2940;color:#60A5FA;font-size:0.6rem;padding:1px 6px;border-radius:10px;margin-left:4px">🐋 BÜYÜK OYUNCU</span>' if sm['buyuk_oyuncu'] else ''

    pozisyon = r.get('pozisyon')
    poz_html = ""
    if pozisyon and pozisyon['lot'] > 0:
        poz_html = f"""
        <div style="margin-top:10px;background:#0A1628;border-radius:8px;padding:10px 12px;border:1px solid #1E3A5F">
          <div style="color:#38BDF8;font-size:0.65rem;font-weight:700;margin-bottom:6px">📐 POZİSYON YÖNETİMİ</div>
          <div style="display:flex;gap:8px;flex-wrap:wrap">
            <div style="flex:1;text-align:center">
              <div style="color:#475569;font-size:0.6rem">LOT</div>
              <div style="color:#E2E8F0;font-weight:700;font-size:0.9rem">{pozisyon['lot']:,}</div>
            </div>
            <div style="flex:1;text-align:center">
              <div style="color:#475569;font-size:0.6rem">TUTAR</div>
              <div style="color:#E2E8F0;font-weight:700;font-size:0.9rem">{pozisyon['pozisyon_tl']:,.0f} ₺</div>
            </div>
            <div style="flex:1;text-align:center">
              <div style="color:#475569;font-size:0.6rem">PORTFÖY %</div>
              <div style="color:#F59E0B;font-weight:700;font-size:0.9rem">%{pozisyon['pozisyon_yuzde']:.1f}</div>
            </div>
            <div style="flex:1;text-align:center">
              <div style="color:#475569;font-size:0.6rem">MAX KAYIP</div>
              <div style="color:#EF4444;font-weight:700;font-size:0.9rem">{pozisyon['max_kayip_tl']:,.0f} ₺</div>
            </div>
          </div>
        </div>"""

    return f"""
    <div class="hisse-kart">
      <div style="display:flex;justify-content:space-between;align-items:flex-start">
        <div>
          <span class="hisse-kod">{r['kod']}</span>
          <span class="sektor-badge">{sektor_kisa}</span>
          {buyuk_oyuncu}
          <br><span class="sinyal-badge {badge_cls}">{r['sinyal']}</span>
        </div>
        <div style="text-align:right">
          <div style="color:#E2E8F0;font-weight:700;font-size:1.05rem">{r['son']:.2f} ₺</div>
          <div style="color:#475569;font-size:0.68rem">RSI {r['rsi']:.0f}</div>
        </div>
      </div>

      <div class="puan-bar-bg">
        <div class="puan-bar" style="width:{puan}%;background:{puan_renk}"></div>
      </div>
      <div style="display:flex;justify-content:space-between;margin-top:2px">
        <span style="color:#475569;font-size:0.65rem">Alım Puanı</span>
        <span style="color:{puan_renk};font-size:0.7rem;font-weight:700">{puan}/100</span>
      </div>

      <div class="metrik-satir">
        <div class="metrik-kutu">
          <div class="metrik-etiket">HEDEF</div>
          <div class="metrik-deger" style="color:#10B981">{r['hedef']:.2f} ₺</div>
          <div style="color:#10B981;font-size:0.65rem">+%{r['kazanc_pct']:.1f}</div>
        </div>
        <div class="metrik-kutu">
          <div class="metrik-etiket">STOP</div>
          <div class="metrik-deger" style="color:#EF4444">{r['stop']:.2f} ₺</div>
          <div style="color:#EF4444;font-size:0.65rem">-%{r['kayip_pct']:.1f}</div>
        </div>
        <div class="metrik-kutu">
          <div class="metrik-etiket">K/K ORANI</div>
          <div class="metrik-deger" style="color:{rr_renk}">1:{r['rr']:.1f}</div>
        </div>
        <div class="metrik-kutu">
          <div class="metrik-etiket">3 AYLIK</div>
          <div class="metrik-deger" style="color:{ay3_renk}">%{r['uc_ay']:+.1f}</div>
        </div>
      </div>

      <div style="margin-top:8px;background:#0A0F1A;border-radius:6px;padding:8px 10px">
        <div style="display:flex;justify-content:space-between;align-items:center">
          <span style="color:#64748B;font-size:0.62rem;font-weight:600">AKILLI PARA ANALİZİ</span>
          <span style="color:{sm_bar_renk};font-size:0.65rem;font-weight:700">{sm['skor']}/100</span>
        </div>
        <div style="background:#1E293B;border-radius:3px;height:4px;margin-top:4px">
          <div style="width:{sm['skor']}%;height:4px;border-radius:3px;background:{sm_bar_renk}"></div>
        </div>
        <div style="color:{sm_bar_renk};font-size:0.65rem;margin-top:4px">{sm['yorum']}</div>
      </div>

      {poz_html}
    </div>"""

# ══════════════════════════════════════════════════════════════════════════════
# ANA UYGULAMA
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="baslik"><h1>📊 BIST TARAMA v3</h1><p>Akıllı Para · Sektör Analizi · Pozisyon Yönetimi</p></div>', unsafe_allow_html=True)

# ── YAN PANEL ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 💼 Portföy Ayarları")
    portfoy_tl = st.number_input(
        "Toplam Portföy (₺)",
        min_value=10000, max_value=10000000,
        value=st.session_state.portfoy_tl, step=10000,
        help="Pozisyon boyutu bu değere göre hesaplanır"
    )
    st.session_state.portfoy_tl = portfoy_tl
    st.markdown(f"*Max risk/işlem: ₺{portfoy_tl*0.02:,.0f} (%2)*")

    st.markdown("---")
    st.markdown("### 🗄️ Supabase (Geçmiş)")
    sb_url = st.text_input("Supabase URL", type="password",
                            help="https://xxx.supabase.co")
    sb_key = st.text_input("Supabase Key", type="password")

    st.markdown("---")
    st.markdown("### 🔔 Telegram")
    tg_token = st.text_input("Bot Token", type="password")
    tg_chat  = st.text_input("Chat ID")
    if st.button("Test"):
        ok = telegram_gonder(tg_token, tg_chat,
             [{'kod':'TEST','sektor':'🧪 Test','sinyal':'Test mesajı',
               'son':100,'hedef':110,'kazanc_pct':10,'stop':95,
               'kayip_pct':5,'puan':80,'sm':{'skor':75,'yorum':'Test','renk':'#10B981','buyuk_oyuncu':False},
               'uc_ay':5,'rr':2.0}], "Test Rejimi")
        st.success("✅") if ok else st.error("❌")

    st.markdown("---")
    st.markdown("**Supabase Kurulum:**\n1. supabase.com → yeni proje\n2. SQL editörde:\n```sql\nCREATE TABLE sinyaller (\n  id SERIAL PRIMARY KEY,\n  kod TEXT,\n  tarih DATE,\n  giris FLOAT,\n  hedef FLOAT,\n  stop FLOAT,\n  sinyal TEXT,\n  puan INT,\n  sonuc TEXT,\n  geri_donus_pct FLOAT\n);\n```\n3. URL ve Key'i buraya yapıştır")

# ── FİLTRELER ─────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["📊 Tarama", "📈 Sinyal Geçmişi", "⭐ Favoriler"])

with tab1:
    c1, c2, c3 = st.columns(3)
    with c1:
        min_puan = st.slider("Min Puan", 0, 90, 40, 5)
    with c2:
        sektor_sec = st.selectbox("Sektör", ["Tümü"] + list(BIST_SEKTORLER.keys()))
    with c3:
        sinyal_filtre = st.selectbox("Sinyal", ["Tümü","AL — Güçlü","AL — Trend","DİP FIRSATI ✦","TAKİPTE TUT"])

    sm_filtre = st.checkbox("Sadece Akıllı Para ≥ 60 olanları göster", value=False)

    if st.button("🔍  BIST'İ TARA (~250 HİSSE)", use_container_width=True):
        with st.spinner("Tüm BIST taranıyor... (~2-3 dk)"):
            sonuclar, rejim, xu100_pct = tum_hisseleri_tara(portfoy_tl)
            st.session_state.update({
                'sonuclar': sonuclar, 'rejim': rejim,
                'xu100_pct': xu100_pct, 'tarama_yapildi': True
            })
            # Supabase kaydet
            if sb_url and sb_key and sonuclar:
                veri = [{'kod': r['kod'], 'tarih': r['tarih'],
                          'giris': r['son'], 'hedef': r['hedef'],
                          'stop': r['stop'], 'sinyal': r['sinyal'],
                          'puan': r['puan'], 'sonuc': 'AÇIK'}
                        for r in sonuclar]
                supabase_kaydet(sb_url, sb_key, veri)
            # Telegram
            if tg_token and tg_chat and sonuclar:
                telegram_gonder(tg_token, tg_chat, sonuclar[:7], rejim)

    if st.session_state.tarama_yapildi:
        rejim    = st.session_state.rejim
        xu100_pct = st.session_state.xu100_pct
        sonuclar = st.session_state.sonuclar

        kart_cls = "rejim-yesil" if "YÜKSELİŞ" in rejim else ("rejim-sari" if "DÜZELTME" in rejim or "YATAY" in rejim else "rejim-kirmizi")
        ikon = "🟢" if "YÜKSELİŞ" in rejim else ("🟡" if "DÜZELTME" in rejim or "YATAY" in rejim else "🔴")

        st.markdown(f"""
        <div class="rejim-kart {kart_cls}">
          <div style="display:flex;justify-content:space-between;align-items:center">
            <div><span style="color:#94A3B8;font-size:0.75rem;font-weight:600">BORSA DURUMU</span><br>
              <span style="color:#E2E8F0;font-size:1rem;font-weight:700">{ikon} {rejim}</span></div>
            <div style="text-align:right">
              <span style="color:#94A3B8;font-size:0.72rem">XU100 Aylık</span><br>
              <span style="color:{'#10B981' if xu100_pct>0 else '#EF4444'};font-size:1.1rem;font-weight:700">%{xu100_pct:+.1f}</span>
            </div>
          </div>
        </div>""", unsafe_allow_html=True)

        # Özet istatistikler
        ck1, ck2, ck3, ck4 = st.columns(4)
        with ck1:
            st.markdown(f'<div class="istat-kutu"><div style="color:#94A3B8;font-size:0.7rem">TOPLAM FİRSAT</div><div style="color:#00D4FF;font-size:1.8rem;font-weight:800">{len(sonuclar)}</div></div>', unsafe_allow_html=True)
        with ck2:
            guclu = len([r for r in sonuclar if "Güçlü" in r['sinyal'] or "DİP" in r['sinyal']])
            st.markdown(f'<div class="istat-kutu"><div style="color:#94A3B8;font-size:0.7rem">GÜÇLÜ SİNYAL</div><div style="color:#10B981;font-size:1.8rem;font-weight:800">{guclu}</div></div>', unsafe_allow_html=True)
        with ck3:
            buyuk = len([r for r in sonuclar if r['sm']['buyuk_oyuncu']])
            st.markdown(f'<div class="istat-kutu"><div style="color:#94A3B8;font-size:0.7rem">BÜYÜK OYUNCU</div><div style="color:#60A5FA;font-size:1.8rem;font-weight:800">{buyuk}</div></div>', unsafe_allow_html=True)
        with ck4:
            ort_puan = np.mean([r['puan'] for r in sonuclar]) if sonuclar else 0
            st.markdown(f'<div class="istat-kutu"><div style="color:#94A3B8;font-size:0.7rem">ORT PUAN</div><div style="color:#F59E0B;font-size:1.8rem;font-weight:800">{ort_puan:.0f}</div></div>', unsafe_allow_html=True)

        st.markdown("<div style='margin-top:12px'></div>", unsafe_allow_html=True)

        # Filtrele
        goster = [r for r in sonuclar if r['puan'] >= min_puan]
        if sektor_sec != "Tümü":
            goster = [r for r in goster if r['sektor'] == sektor_sec]
        if sinyal_filtre != "Tümü":
            goster = [r for r in goster if sinyal_filtre in r['sinyal']]
        if sm_filtre:
            goster = [r for r in goster if r['sm']['skor'] >= 60]

        if not goster:
            st.markdown('<div style="background:#1C0808;border:1px solid #EF444444;border-radius:10px;padding:16px;text-align:center;color:#FCA5A5;margin:20px 0"><div style="font-size:2rem">⚠️</div><div style="font-weight:700">Filtrelere uygun hisse bulunamadı</div></div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div style="color:#94A3B8;font-size:0.8rem;margin-bottom:10px">{len(goster)} hisse • {datetime.datetime.now().strftime("%H:%M")}</div>', unsafe_allow_html=True)
            for r in goster:
                fav = r['kod'] in st.session_state.favoriler
                ck, cf = st.columns([6, 1])
                with ck:
                    st.markdown(hisse_kart_html(r, fav), unsafe_allow_html=True)
                    g = hisse_grafigi(r['df_3ay'])
                    if g: st.image(g, use_container_width=True)
                with cf:
                    if st.button("⭐" if fav else "☆", key=f"f_{r['kod']}"):
                        if fav: st.session_state.favoriler.discard(r['kod'])
                        else: st.session_state.favoriler.add(r['kod'])
                        st.rerun()

# ── SİNYAL GEÇMİŞİ ──────────────────────────────────────────────────────────
with tab2:
    st.markdown("### 📈 Sinyal Geçmişi & Başarı Oranı")

    col_sb, col_guncelle = st.columns([3,1])
    with col_sb:
        st.info("Geçmişi görmek için Supabase bağlantısı gerekli. Sol panelden ayarla.")
    with col_guncelle:
        if st.button("🔄 Güncelle", use_container_width=True):
            if sb_url and sb_key:
                with st.spinner("Sonuçlar kontrol ediliyor..."):
                    gecmis = supabase_gecmis_cek(sb_url, sb_key, limit=100)
                    gecmis = gecmis_guncelle(gecmis)
                    st.session_state.gecmis = gecmis
            else:
                # Supabase yoksa demo veri göster
                st.session_state.gecmis = [
                    {'kod':'DEMO','tarih':'2025-01-01','giris':10,'hedef':11.5,
                     'stop':9.2,'sinyal':'AL — Demo','puan':75,'sonuc':'🟢 HEDEF','geri_donus_pct':15.0},
                ]

    gecmis = st.session_state.gecmis
    if gecmis:
        istat = basari_istatistik(gecmis)
        if istat:
            g1, g2, g3, g4 = st.columns(4)
            with g1:
                st.markdown(f'<div class="istat-kutu"><div style="color:#94A3B8;font-size:0.7rem">BAŞARI ORANI</div><div style="color:#10B981;font-size:1.8rem;font-weight:800">%{istat["basari_oran"]:.0f}</div><div style="color:#475569;font-size:0.65rem">{istat["hedef"]} / {istat["toplam"]} sinyal</div></div>', unsafe_allow_html=True)
            with g2:
                renk = "#10B981" if istat["ort_getiri"] > 0 else "#EF4444"
                st.markdown(f'<div class="istat-kutu"><div style="color:#94A3B8;font-size:0.7rem">ORT GETİRİ</div><div style="color:{renk};font-size:1.8rem;font-weight:800">%{istat["ort_getiri"]:+.1f}</div></div>', unsafe_allow_html=True)
            with g3:
                st.markdown(f'<div class="istat-kutu"><div style="color:#94A3B8;font-size:0.7rem">EN İYİ</div><div style="color:#10B981;font-size:1.8rem;font-weight:800">%{istat["max_getiri"]:+.1f}</div></div>', unsafe_allow_html=True)
            with g4:
                st.markdown(f'<div class="istat-kutu"><div style="color:#94A3B8;font-size:0.7rem">STOP SAYISI</div><div style="color:#EF4444;font-size:1.8rem;font-weight:800">{istat["stop"]}</div></div>', unsafe_allow_html=True)

        st.markdown("<div style='margin-top:12px'></div>", unsafe_allow_html=True)
        for g in gecmis[:30]:
            sonuc_renk = "#10B981" if "HEDEF" in str(g.get('sonuc','')) else ("#EF4444" if "STOP" in str(g.get('sonuc','')) else "#94A3B8")
            getiri_str = f"%{g.get('geri_donus_pct',0):+.1f}" if g.get('geri_donus_pct') is not None else "—"
            st.markdown(f"""
            <div class="gecmis-satir">
              <div>
                <span style="color:#E2E8F0;font-weight:700;font-size:0.9rem">{g.get('kod','')}</span>
                <span style="color:#64748B;font-size:0.72rem;margin-left:8px">{g.get('tarih','')}</span><br>
                <span style="color:#94A3B8;font-size:0.72rem">{g.get('sinyal','')} • Giriş: {g.get('giris',0):.2f} ₺</span>
              </div>
              <div style="text-align:right">
                <div style="color:{sonuc_renk};font-weight:700;font-size:0.85rem">{g.get('sonuc','AÇIK')}</div>
                <div style="color:{sonuc_renk};font-size:0.8rem">{getiri_str}</div>
              </div>
            </div>""", unsafe_allow_html=True)
    else:
        st.markdown('<div style="text-align:center;color:#475569;padding:40px">Henüz geçmiş sinyal yok.<br>Tarama yaptıkça veriler birikir.</div>', unsafe_allow_html=True)

# ── FAVORİLER ─────────────────────────────────────────────────────────────────
with tab3:
    st.markdown("### ⭐ Favori Hisselerim")
    favori_sonuclar = [r for r in st.session_state.sonuclar
                       if r['kod'] in st.session_state.favoriler]
    if not favori_sonuclar:
        st.markdown('<div style="text-align:center;color:#475569;padding:40px">Henüz favori yok.<br>Tarama sonuçlarından ☆ ikonu ile ekleyebilirsin.</div>', unsafe_allow_html=True)
    else:
        for r in favori_sonuclar:
            ck, cf = st.columns([6,1])
            with ck:
                st.markdown(hisse_kart_html(r, True), unsafe_allow_html=True)
                g = hisse_grafigi(r['df_3ay'])
                if g: st.image(g, use_container_width=True)
            with cf:
                if st.button("⭐", key=f"fr_{r['kod']}"):
                    st.session_state.favoriler.discard(r['kod']); st.rerun()

st.markdown('<div class="footer">BIST Tarama v3.0 • Yatırım tavsiyesi değildir • Teknik analize dayanır</div>', unsafe_allow_html=True)

