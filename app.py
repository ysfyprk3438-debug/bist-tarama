"""
BIST 100 AKILLI TARAMA — Streamlit Web Uygulaması
Telefonda kullanım için optimize edilmiştir.
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import ta
import datetime
import warnings
import io
import os
import urllib.request
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from concurrent.futures import ThreadPoolExecutor, as_completed
from fpdf import FPDF

warnings.filterwarnings('ignore')

# ── Sayfa Ayarları ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="BIST Tarama",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── CSS: Koyu Tema, Mobil Uyumlu ─────────────────────────────────────────────
st.markdown("""
<style>
  /* Genel arka plan */
  .stApp { background-color: #080C14; }
  section[data-testid="stSidebar"] { background-color: #0D1117; }

  /* Başlık */
  .baslik {
    background: linear-gradient(135deg, #0D1B2A 0%, #0A2540 100%);
    border: 1px solid #00D4FF33;
    border-radius: 14px;
    padding: 22px 16px 16px 16px;
    text-align: center;
    margin-bottom: 18px;
  }
  .baslik h1 {
    color: #00D4FF;
    font-size: 1.7rem;
    font-weight: 800;
    margin: 0 0 4px 0;
    letter-spacing: 1px;
  }
  .baslik p { color: #64748B; font-size: 0.82rem; margin: 0; }

  /* Piyasa durum kartı */
  .rejim-kart {
    border-radius: 10px;
    padding: 14px 16px;
    margin-bottom: 16px;
    border-left: 4px solid;
  }
  .rejim-yesil { background: #0B1F14; border-color: #10B981; }
  .rejim-sari  { background: #1C1505; border-color: #F59E0B; }
  .rejim-kirmizi { background: #1C0808; border-color: #EF4444; }

  /* Hisse kartları */
  .hisse-kart {
    background: #0D1117;
    border: 1px solid #1E293B;
    border-radius: 12px;
    padding: 14px 16px;
    margin-bottom: 10px;
    position: relative;
  }
  .hisse-kart:hover { border-color: #00D4FF44; }

  .hisse-kod {
    font-size: 1.15rem;
    font-weight: 800;
    color: #E2E8F0;
    letter-spacing: 0.5px;
  }
  .sinyal-badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 20px;
    font-size: 0.72rem;
    font-weight: 700;
    margin-left: 8px;
  }
  .badge-yesil { background: #064E3B; color: #10B981; }
  .badge-sari  { background: #451A03; color: #F59E0B; }
  .badge-kirmizi { background: #450A0A; color: #EF4444; }

  .metrik-satir {
    display: flex;
    gap: 10px;
    margin-top: 10px;
    flex-wrap: wrap;
  }
  .metrik-kutu {
    flex: 1;
    min-width: 80px;
    background: #141B2D;
    border-radius: 8px;
    padding: 8px 10px;
    text-align: center;
  }
  .metrik-etiket {
    color: #475569;
    font-size: 0.65rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }
  .metrik-deger {
    font-size: 0.9rem;
    font-weight: 700;
    margin-top: 2px;
  }
  .renk-yesil { color: #10B981; }
  .renk-kirmizi { color: #EF4444; }
  .renk-sari { color: #F59E0B; }
  .renk-mavi { color: #00D4FF; }
  .renk-gri { color: #94A3B8; }

  /* Puan çubuğu */
  .puan-bar-bg {
    background: #1E293B;
    border-radius: 4px;
    height: 6px;
    margin-top: 8px;
  }
  .puan-bar {
    height: 6px;
    border-radius: 4px;
    transition: width 0.5s;
  }

  /* Buton */
  .stButton > button {
    background: linear-gradient(135deg, #0369A1, #0EA5E9);
    color: white;
    border: none;
    border-radius: 10px;
    font-weight: 700;
    font-size: 1rem;
    padding: 14px 0;
    width: 100%;
    cursor: pointer;
    letter-spacing: 0.5px;
  }
  .stButton > button:hover {
    background: linear-gradient(135deg, #0EA5E9, #38BDF8);
  }

  /* Uyarı kutusu */
  .uyari-kutu {
    background: #1C0808;
    border: 1px solid #EF444444;
    border-radius: 10px;
    padding: 16px;
    text-align: center;
    color: #FCA5A5;
    margin: 20px 0;
  }

  /* Footer */
  .footer {
    text-align: center;
    color: #334155;
    font-size: 0.72rem;
    padding: 20px 0 10px 0;
    border-top: 1px solid #1E293B;
    margin-top: 30px;
  }

  /* Streamlit elementlerini gizle */
  #MainMenu, footer, header { visibility: hidden; }
  .block-container { padding-top: 1rem; padding-bottom: 2rem; }
</style>
""", unsafe_allow_html=True)

# ── BIST 100 Listesi ─────────────────────────────────────────────────────────
BIST100 = list(dict.fromkeys([
    'AKBNK','GARAN','HALKB','ISCTR','VAKBN','YKBNK','TSKB','ALBRK',
    'KCHOL','SAHOL','THYAO','TUPRS','EREGL','PETKM','SASA','ASTOR',
    'FROTO','TOASO','DOAS','OTKAR','PGSUS','TAVHL','ENKAI','EKGYO',
    'SISE','TTKOM','TCELL','BIMAS','MGROS','SOKM',
    'KOZAL','KOZAA','EUPWR','ODAS','ENJSA','AKSEN','ZOREN',
    'ASELS','AGHOL','LOGO','NETAS',
    'GUBRF','HEKTS','CIMSA','KRDMD','ALARK','ARCLK','VESTL',
    'TKFEN','ULKER','CCOLA','AEFES','BRISA','KARSN','ISGYO',
    'MPARK','ISDMR','RYSAS','TRGYO','MAVI','DOHOL',
    'BERA','KLGYO','SMART','CWENE','KCAER',
    'SKBNK','FENER','BJKAS','GSRAY',
    'SNGYO','DESA','EGEEN','VKGYO','KONTR',
]))

# ── Yardımcı Fonksiyonlar ─────────────────────────────────────────────────────
def temizle(text):
    tr = {'ı':'i','İ':'I','ş':'s','Ş':'S','ğ':'g','Ğ':'G',
          'ü':'u','Ü':'U','ö':'o','Ö':'O','ç':'c','Ç':'C','₺':'TL'}
    s = str(text)
    for k, v in tr.items():
        s = s.replace(k, v)
    return s

@st.cache_data(ttl=1800, show_spinner=False)
def piyasa_durumu():
    try:
        df = yf.Ticker("XU100.IS").history(period="1y", interval="1d")
        if df.empty:
            return "BİLİNMİYOR", 1.0, 0.0
        k = df['Close']
        son = float(k.iloc[-1])
        ma50 = float(k.rolling(50).mean().iloc[-1])
        ma200 = float(k.rolling(200).mean().iloc[-1])
        ay_oncesi = float(k.iloc[-22]) if len(k) >= 22 else son
        aylik = ((son - ay_oncesi) / ay_oncesi) * 100
        if son > ma50 > ma200:
            return "YÜKSELİŞ TRENDİ ✓", 1.0, aylik
        elif son > ma200:
            return "DÜZELTME (Temkinli)", 0.65, aylik
        else:
            return "DÜŞÜŞ TRENDİ ⚠", 0.25, aylik
    except:
        return "BİLİNMİYOR", 1.0, 0.0

def hisse_analiz(kod, carpan):
    try:
        df = yf.Ticker(f"{kod}.IS").history(period='1y', interval='1d')
        if df.empty or len(df) < 60:
            return None
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df = df[['Open','High','Low','Close','Volume']].dropna()
        if len(df) < 60:
            return None

        # Tazelik kontrolü
        son_tarih = df.index[-1]
        if hasattr(son_tarih, 'date'):
            son_tarih = son_tarih.date()
        if (datetime.date.today() - son_tarih).days > 7:
            return None

        k, h, l, v = df['Close'], df['High'], df['Low'], df['Volume']
        son = float(k.iloc[-1])

        ma20 = float(k.rolling(20).mean().iloc[-1])
        ma50 = float(k.rolling(50).mean().iloc[-1]) if len(k) >= 50 else son
        ma200 = float(k.rolling(200).mean().iloc[-1]) if len(k) >= 200 else son

        trend = sum([son > ma20, son > ma50, son > ma200, ma20 > ma50])

        rsi_ser = ta.momentum.RSIIndicator(k, window=14).rsi()
        rsi = float(rsi_ser.iloc[-1]) if not rsi_ser.empty else 50.0

        macd_ind = ta.trend.MACD(k)
        macd_diff = float(macd_ind.macd_diff().iloc[-1])
        macd_ok = macd_diff > 0

        atr_ser = ta.volatility.AverageTrueRange(h, l, k, window=14).average_true_range()
        atr = float(atr_ser.iloc[-1]) if not atr_ser.empty else son * 0.02

        direnc = float(h.rolling(20).max().iloc[-1])
        destek = float(l.rolling(20).min().iloc[-1])
        if direnc <= son:
            direnc = float(h.rolling(50).max().iloc[-1]) if len(h) >= 50 else son * 1.05
        if destek >= son:
            destek = float(l.rolling(50).min().iloc[-1]) if len(l) >= 50 else son * 0.95

        hacim_ort = float(v.rolling(20).mean().iloc[-1])
        hacim_son = float(v.iloc[-1])
        hacim_guclu = hacim_son > hacim_ort * 1.3

        hedef = min(direnc, son + atr * 2.5) if direnc > son else son + atr * 2.5
        stop = son - atr * 1.2

        kazanc_pct = ((hedef - son) / son) * 100
        kayip_pct  = ((son - stop) / son) * 100
        rr = kazanc_pct / (kayip_pct + 1e-8)

        uc_ay = float(k.iloc[-63]) if len(k) >= 63 else float(k.iloc[0])
        uc_ay_getiri = ((son - uc_ay) / uc_ay) * 100

        if rsi > 72:
            sinyal, s_renk = "AŞIRI ALIM", "kirmizi"
        elif rsi < 35 and macd_ok:
            sinyal, s_renk = "DİP FIRSATI", "yesil"
        elif trend >= 3 and macd_ok and rsi < 65:
            sinyal, s_renk = "AL — Trend Destekli", "yesil"
        elif trend >= 2 and macd_ok:
            sinyal, s_renk = "TAKİPTE TUT", "sari"
        else:
            return None

        if s_renk == "kirmizi" or rr < 1.5 or kazanc_pct < 3:
            return None

        puan = int(min(100, (
            trend * 10 +
            min(25, rr * 8) +
            (10 if macd_ok else 0) +
            (10 if hacim_guclu else 0) +
            (5 if rsi < 55 else 0) +
            (10 if "DİP" in sinyal or "AL" in sinyal else 0)
        )) * carpan)

        return dict(
            kod=kod, son=son, puan=puan, sinyal=sinyal, s_renk=s_renk,
            hedef=hedef, stop=stop, rr=rr,
            kazanc_pct=kazanc_pct, kayip_pct=kayip_pct,
            rsi=rsi, destek=destek, direnc=direnc,
            uc_ay=uc_ay_getiri, hacim=hacim_guclu, trend=trend
        )
    except:
        return None

@st.cache_data(ttl=1800, show_spinner=False)
def tum_hisseleri_tara():
    rejim, carpan, xu100_pct = piyasa_durumu()
    sonuclar = []
    with ThreadPoolExecutor(max_workers=10) as ex:
        gorevler = {ex.submit(hisse_analiz, h, carpan): h for h in BIST100}
        for f in as_completed(gorevler):
            try:
                r = f.result()
                if r:
                    sonuclar.append(r)
            except:
                pass
    sonuclar.sort(key=lambda x: x['puan'] * 0.6 + x['rr'] * 8, reverse=True)
    return sonuclar, rejim, xu100_pct

# ── PDF Oluşturucu ────────────────────────────────────────────────────────────
def fontlari_hazirla():
    fonts = {
        "Roboto-Regular.ttf": "https://github.com/googlefonts/roboto/raw/main/src/hinted/Roboto-Regular.ttf",
        "Roboto-Bold.ttf":    "https://github.com/googlefonts/roboto/raw/main/src/hinted/Roboto-Bold.ttf",
    }
    for fname, url in fonts.items():
        if not os.path.exists(fname):
            try: urllib.request.urlretrieve(url, fname)
            except: pass

def pdf_olustur_streamlit(firsatlar, rejim, xu100_pct):
    fontlari_hazirla()

    KOYU = (8, 10, 14); PANEL = (13, 17, 27)
    YESIL = (16, 185, 129); SARI = (245, 158, 11)
    KIRMIZI = (239, 68, 68); MAVI = (0, 212, 255)
    BEYAZ = (255, 255, 255); GRI = (100, 116, 139)
    ACIK_GRI = (148, 163, 184)

    class Rapor(FPDF):
        def __init__(self):
            super().__init__('L', 'mm', 'A4')
            self._f = "helvetica"
            if os.path.exists("Roboto-Regular.ttf"):
                try:
                    self.add_font("Roboto", "", "Roboto-Regular.ttf", uni=True)
                    self.add_font("Roboto", "B", "Roboto-Bold.ttf", uni=True)
                    self._f = "Roboto"
                except: pass

        def header(self):
            self.set_fill_color(*KOYU); self.rect(0, 0, 297, 210, 'F')
            self.set_fill_color(0, 30, 50); self.rect(0, 0, 297, 22, 'F')
            self.set_font(self._f, 'B', 15); self.set_text_color(*MAVI)
            self.set_xy(0, 4)
            self.cell(0, 8, 'BIST 100 — AKILLI TARAMA RAPORU', 0, 1, 'C')
            self.set_font(self._f, '', 8); self.set_text_color(*GRI)
            tarih = datetime.datetime.now().strftime("%d.%m.%Y %H:%M")
            self.cell(0, 6,
                f'Olusturulma: {tarih}   |   Borsa: {temizle(rejim)}   |   '
                f'XU100 Aylik: %{xu100_pct:+.1f}   |   Firsat Sayisi: {len(firsatlar)}',
                0, 1, 'C')
            self.ln(2)

    pdf = Rapor()
    pdf.set_auto_page_break(auto=True, margin=10)
    pdf.add_page()
    F = pdf._f

    if not firsatlar:
        pdf.set_font(F, 'B', 14); pdf.set_text_color(*KIRMIZI)
        pdf.ln(30); pdf.cell(0, 12, 'PIYASADA ANLAMLI FIRSAT BULUNAMADI.', 0, 1, 'C')
        pdf.set_text_color(*SARI); pdf.set_font(F, '', 11)
        pdf.cell(0, 10, temizle('Öneri: Nakitte kal.'), 0, 1, 'C')
    else:
        COL = [18, 20, 13, 30, 24, 24, 17, 19, 20, 21, 21, 30]
        BAS = ['HİSSE','FİYAT','PUAN','SİNYAL','HEDEF','STOP',
               'R:O','RSI','3AY %','DESTEK','DİRENÇ','TREND']

        pdf.set_font(F, 'B', 7); pdf.set_text_color(*MAVI)
        pdf.set_fill_color(0, 30, 50); pdf.set_draw_color(0, 80, 120)
        for i, b in enumerate(BAS):
            pdf.cell(COL[i], 10, temizle(b), 1, 0, 'C', fill=True)
        pdf.ln()

        pdf.set_font(F, '', 7)
        for idx, r in enumerate(firsatlar):
            fc = (12, 16, 26) if idx % 2 == 0 else (16, 20, 32)
            pdf.set_fill_color(*fc)

            s_renk = YESIL if r['s_renk'] == 'yesil' else SARI
            rr_renk = YESIL if r['rr'] >= 2.5 else (SARI if r['rr'] >= 1.5 else KIRMIZI)
            ay3_renk = YESIL if r['uc_ay'] > 0 else KIRMIZI
            rsi_renk = YESIL if r['rsi'] < 35 else (KIRMIZI if r['rsi'] > 65 else BEYAZ)
            hacim_ikon = " V+" if r['hacim'] else ""

            pdf.set_text_color(*BEYAZ)
            pdf.cell(COL[0], 9, r['kod'] + hacim_ikon, 1, 0, 'C', fill=True)
            pdf.cell(COL[1], 9, f"{r['son']:.2f}", 1, 0, 'C', fill=True)

            pdf.set_text_color(*SARI)
            pdf.cell(COL[2], 9, str(r['puan']), 1, 0, 'C', fill=True)

            pdf.set_text_color(*s_renk)
            pdf.cell(COL[3], 9, temizle(r['sinyal']), 1, 0, 'C', fill=True)

            pdf.set_text_color(*YESIL)
            pdf.cell(COL[4], 9, f"{r['hedef']:.2f} +%{r['kazanc_pct']:.1f}", 1, 0, 'C', fill=True)

            pdf.set_text_color(*KIRMIZI)
            pdf.cell(COL[5], 9, f"{r['stop']:.2f} -%{r['kayip_pct']:.1f}", 1, 0, 'C', fill=True)

            pdf.set_text_color(*rr_renk)
            pdf.cell(COL[6], 9, f"1:{r['rr']:.1f}", 1, 0, 'C', fill=True)

            pdf.set_text_color(*rsi_renk)
            pdf.cell(COL[7], 9, f"{r['rsi']:.0f}", 1, 0, 'C', fill=True)

            pdf.set_text_color(*ay3_renk)
            pdf.cell(COL[8], 9, f"%{r['uc_ay']:+.1f}", 1, 0, 'C', fill=True)

            pdf.set_text_color(*ACIK_GRI)
            pdf.cell(COL[9], 9, f"{r['destek']:.2f}", 1, 0, 'C', fill=True)
            pdf.cell(COL[10], 9, f"{r['direnc']:.2f}", 1, 0, 'C', fill=True)

            trend_bar = "●" * r['trend'] + "○" * (4 - r['trend'])
            t_renk = YESIL if r['trend'] >= 3 else (SARI if r['trend'] == 2 else GRI)
            pdf.set_text_color(*t_renk)
            pdf.cell(COL[11], 9, temizle(f"Trend {trend_bar}"), 1, 0, 'C', fill=True)
            pdf.ln()

    pdf.ln(3)
    pdf.set_font(F, '', 7); pdf.set_text_color(*GRI)
    pdf.set_x(8)
    pdf.multi_cell(0, 4, temizle(
        "NOT: Bu rapor yatırım tavsiyesi değildir. Teknik analize dayanır. "
        "Tüm kararların sorumluluğu yatırımcıya aittir. "
        "Stop seviyelerine uymak zorunludur."
    ), 0, 'L')

    buf = io.BytesIO()
    pdf.output(buf)
    buf.seek(0)
    return buf.read()

# ── Kart HTML ─────────────────────────────────────────────────────────────────
def hisse_kart_html(r):
    badge_cls = f"badge-{r['s_renk']}"
    puan = r['puan']
    puan_renk = "#10B981" if puan >= 70 else ("#F59E0B" if puan >= 50 else "#EF4444")
    rr_renk = "#10B981" if r['rr'] >= 2.5 else ("#F59E0B" if r['rr'] >= 1.5 else "#EF4444")
    ay3_renk = "#10B981" if r['uc_ay'] > 0 else "#EF4444"
    rsi_renk = "#10B981" if r['rsi'] < 35 else ("#EF4444" if r['rsi'] > 65 else "#94A3B8")
    hacim_badge = '<span style="background:#1E3A5F;color:#38BDF8;font-size:0.65rem;padding:1px 6px;border-radius:10px;margin-left:4px">HACİM ↑</span>' if r['hacim'] else ''

    return f"""
    <div class="hisse-kart">
      <div style="display:flex;justify-content:space-between;align-items:center">
        <div>
          <span class="hisse-kod">{r['kod']}</span>{hacim_badge}
          <span class="sinyal-badge {badge_cls}">{r['sinyal']}</span>
        </div>
        <div style="text-align:right">
          <span style="color:#E2E8F0;font-weight:700;font-size:1.1rem">{r['son']:.2f} ₺</span>
        </div>
      </div>

      <div class="puan-bar-bg">
        <div class="puan-bar" style="width:{puan}%;background:{puan_renk}"></div>
      </div>
      <div style="display:flex;justify-content:space-between;margin-top:3px">
        <span style="color:#475569;font-size:0.68rem">Puan</span>
        <span style="color:{puan_renk};font-size:0.72rem;font-weight:700">{puan}/100</span>
      </div>

      <div class="metrik-satir">
        <div class="metrik-kutu">
          <div class="metrik-etiket">HEDEF</div>
          <div class="metrik-deger renk-yesil">{r['hedef']:.2f} ₺</div>
          <div style="color:#10B981;font-size:0.68rem">+%{r['kazanc_pct']:.1f}</div>
        </div>
        <div class="metrik-kutu">
          <div class="metrik-etiket">STOP</div>
          <div class="metrik-deger renk-kirmizi">{r['stop']:.2f} ₺</div>
          <div style="color:#EF4444;font-size:0.68rem">-%{r['kayip_pct']:.1f}</div>
        </div>
        <div class="metrik-kutu">
          <div class="metrik-etiket">KAZAN/KAYBET</div>
          <div class="metrik-deger" style="color:{rr_renk}">1:{r['rr']:.1f}</div>
          <div style="color:#475569;font-size:0.68rem">oran</div>
        </div>
        <div class="metrik-kutu">
          <div class="metrik-etiket">RSI</div>
          <div class="metrik-deger" style="color:{rsi_renk}">{r['rsi']:.0f}</div>
          <div style="color:#475569;font-size:0.68rem">{"Aşırı Satım" if r['rsi']<35 else ("Aşırı Alım" if r['rsi']>65 else "Normal")}</div>
        </div>
        <div class="metrik-kutu">
          <div class="metrik-etiket">3 AYLIK</div>
          <div class="metrik-deger" style="color:{ay3_renk}">%{r['uc_ay']:+.1f}</div>
          <div style="color:#475569;font-size:0.68rem">getiri</div>
        </div>
      </div>
    </div>
    """

# ══════════════════════════════════════════════════════════════════════════════
# ANA UYGULAMA
# ══════════════════════════════════════════════════════════════════════════════

st.markdown("""
<div class="baslik">
  <h1>📊 BIST 100 TARAMA</h1>
  <p>Al ya da alma — sade, net, doğru</p>
</div>
""", unsafe_allow_html=True)

# State yönetimi
if 'tarama_yapildi' not in st.session_state:
    st.session_state.tarama_yapildi = False
if 'sonuclar' not in st.session_state:
    st.session_state.sonuclar = []
if 'rejim' not in st.session_state:
    st.session_state.rejim = ""
if 'xu100_pct' not in st.session_state:
    st.session_state.xu100_pct = 0.0

# Filtre
col_f1, col_f2 = st.columns([1, 1])
with col_f1:
    min_puan = st.slider("Minimum Puan", 0, 90, 40, 5,
                         help="Sadece bu puanın üzerindeki hisseler gösterilir")
with col_f2:
    sinyal_filtre = st.selectbox("Sinyal Filtresi",
                                  ["Tümü", "AL — Trend Destekli", "DİP FIRSATI", "TAKİPTE TUT"])

# Tara butonu
if st.button("🔍  BIST 100'Ü TARA", use_container_width=True):
    with st.spinner("BIST 100 taranıyor... (~1-2 dakika)"):
        sonuclar, rejim, xu100_pct = tum_hisseleri_tara()
        st.session_state.sonuclar = sonuclar
        st.session_state.rejim = rejim
        st.session_state.xu100_pct = xu100_pct
        st.session_state.tarama_yapildi = True

# Sonuçları göster
if st.session_state.tarama_yapildi:
    rejim = st.session_state.rejim
    xu100_pct = st.session_state.xu100_pct
    sonuclar = st.session_state.sonuclar

    # Piyasa durumu
    if "YÜKSELİŞ" in rejim:
        kart_cls = "rejim-yesil"
        ikon = "🟢"
    elif "DÜZELTME" in rejim:
        kart_cls = "rejim-sari"
        ikon = "🟡"
    else:
        kart_cls = "rejim-kirmizi"
        ikon = "🔴"

    st.markdown(f"""
    <div class="rejim-kart {kart_cls}">
      <div style="display:flex;justify-content:space-between;align-items:center">
        <div>
          <span style="color:#94A3B8;font-size:0.75rem;font-weight:600">BORSA GENEL DURUMU</span><br>
          <span style="color:#E2E8F0;font-size:1rem;font-weight:700">{ikon} {rejim}</span>
        </div>
        <div style="text-align:right">
          <span style="color:#94A3B8;font-size:0.72rem">XU100 Aylık</span><br>
          <span style="color:{'#10B981' if xu100_pct>0 else '#EF4444'};font-size:1.1rem;font-weight:700">
            %{xu100_pct:+.1f}
          </span>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Filtrele
    goster = [r for r in sonuclar if r['puan'] >= min_puan]
    if sinyal_filtre != "Tümü":
        goster = [r for r in goster if sinyal_filtre in r['sinyal']]

    if not goster:
        st.markdown("""
        <div class="uyari-kutu">
          <div style="font-size:2rem">⚠️</div>
          <div style="font-weight:700;margin-top:8px">Seçili filtrelere uygun hisse bulunamadı.</div>
          <div style="font-size:0.82rem;margin-top:4px;color:#94A3B8">
            Minimum puanı düşür veya filtreyi değiştir.
          </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
          <span style="color:#94A3B8;font-size:0.82rem">{len(goster)} hisse listeleniyor</span>
          <span style="color:#F59E0B;font-size:0.78rem">
            Puana göre sıralı • Tarama: {datetime.datetime.now().strftime('%H:%M')}
          </span>
        </div>
        """, unsafe_allow_html=True)

        # Kartlar
        for r in goster:
            st.markdown(hisse_kart_html(r), unsafe_allow_html=True)

        # PDF İndir
        st.markdown("<div style='margin-top:16px'></div>", unsafe_allow_html=True)
        if st.button("📥  PDF RAPORU İNDİR", use_container_width=True):
            with st.spinner("PDF hazırlanıyor..."):
                pdf_bytes = pdf_olustur_streamlit(goster, rejim, xu100_pct)
                dosya_adi = f"BIST100_{datetime.datetime.now().strftime('%d%m%Y_%H%M')}.pdf"
                st.download_button(
                    label="⬇️  PDF İndir",
                    data=pdf_bytes,
                    file_name=dosya_adi,
                    mime="application/pdf",
                    use_container_width=True
                )

# Footer
st.markdown("""
<div class="footer">
  Bu uygulama yatırım tavsiyesi değildir. Teknik analize dayanır.<br>
  Tüm kararların sorumluluğu yatırımcıya aittir.
</div>
""", unsafe_allow_html=True)
