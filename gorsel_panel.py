# surum 2
# -*- coding: utf-8 -*-
"""
═══════════════════════════════════════════════════════════════
GÖRSEL PANEL — APEX
═══════════════════════════════════════════════════════════════
Kare tile grid + tek ekran detay. Her grafik okuması YÖN SÖYLEMEZ;
geometrik/teknik durumu betimler, sonra "piyasa bunu nasıl okur" der.
Asıl başrol VERİDİR: her okuma kendi SİCİLİNİ taşır —
bu hissede son ~1 yılda kaç kez yaşandı, sonraki ~10 günde
▲kaç (ort +%) / ▼kaç (ort −%), isabet ~%kaç.
İsabet 40-60 ise nötr "≈ yazı-tura". Küçük örneklemde "güvenme".

Bağlanış (app.py içinde):
    import gorsel_panel as gp
    gp.goster(["THYAO", "AKBNK", "ASELS", ...])
"""
import json
import numpy as np
import pandas as pd

try:
    import streamlit as st
    import streamlit.components.v1 as components
except Exception:
    st = None
    components = None

import veri  # veri.veri_al(kod) -> (df, durum)

# BIST 100 (XU100) — kullanıcı sayfadan düzenleyebilir
XU100 = [
    "AEFES","AGHOL","AKBNK","AKCNS","AKFGY","AKSA","AKSEN","ALARK","ALFAS","ARCLK",
    "ASELS","ASTOR","BERA","BIMAS","BRSAN","BRYAT","BUCIM","CCOLA","CIMSA","DOAS",
    "DOHOL","ECILC","EGEEN","EKGYO","ENJSA","ENKAI","EREGL","EUPWR","FROTO","GARAN",
    "GESAN","GUBRF","HALKB","HEKTS","ISCTR","ISGYO","ISMEN","IZMDC","KAYSE","KCHOL",
    "KONTR","KONYA","KORDS","KOZAA","KOZAL","KRDMD","MAVI","MGROS","MIATK","ODAS",
    "OTKAR","OYAKC","PETKM","PGSUS","PSGYO","QUAGR","SAHOL","SASA","SISE","SKBNK",
    "SMRTG","SOKM","TAVHL","TCELL","THYAO","TKFEN","TOASO","TTKOM","TTRAK","TUKAS",
    "TUPRS","ULKER","VAKBN","VESBE","VESTL","YKBNK","ZOREN","ALBRK","ANSGR","ARDYZ",
    "BFREN","CANTE","CWENE","DAPGM","ENERY","FENER","GENIL","GLYHO","IZINS","KMPUR",
    "KZBGY","MPARK","PAPIL","REEDR","TABGD","TSKB","TUREX","YEOTK","YYLGD","ZRGYO",
]

UFUK = 10
NOTR_ALT, NOTR_UST = 40.0, 60.0
KUCUK_ORNEKLEM = 5
SPARK_GUN = 90
DETAY_GUN = 160


# ══════════════════════════════════════════════════════════════
# GÖSTERGELER
# ══════════════════════════════════════════════════════════════
def gostergeler(df):
    d = df.copy()
    k = d["Close"]
    d["MA20"] = k.rolling(20).mean()
    d["MA50"] = k.rolling(50).mean()
    d["MA200"] = k.rolling(200).mean()
    delta = k.diff()
    up = delta.clip(lower=0).rolling(14).mean()
    dn = (-delta.clip(upper=0)).rolling(14).mean()
    rs = up / dn.replace(0, np.nan)
    d["RSI"] = 100 - 100 / (1 + rs)
    std20 = k.rolling(20).std()
    d["BB_ust"] = d["MA20"] + 2 * std20
    d["BB_alt"] = d["MA20"] - 2 * std20
    d["BB_gen"] = (d["BB_ust"] - d["BB_alt"]) / d["MA20"]
    d["getiri"] = k.pct_change()
    d["vol20"] = d["getiri"].rolling(20).std()
    return d


# ══════════════════════════════════════════════════════════════
# SİCİL MOTORU — False→True geçişlerini olay sayar, sonraki UFUK günü ölçer
# ══════════════════════════════════════════════════════════════
def sicil(d, kosul, ufuk=UFUK):
    k = d["Close"].values
    n = len(k)
    if isinstance(kosul, pd.Series):
        kosul = kosul.values
    kosul = np.asarray(kosul, dtype=bool)
    tetik = np.zeros(n, dtype=bool)
    tetik[0] = kosul[0]
    tetik[1:] = kosul[1:] & ~kosul[:-1]
    idx = [i for i in np.where(tetik)[0] if i + ufuk < n]
    getiriler = []
    for i in idx:
        g = (k[i + ufuk] - k[i]) / k[i] * 100.0
        if np.isfinite(g):
            getiriler.append(g)
    say = len(getiriler)
    if say == 0:
        return {"n": 0, "yukari": 0, "asagi": 0, "ort_yukari": 0.0,
                "ort_asagi": 0.0, "isabet": 0.0, "notr": True, "kucuk": True}
    arr = np.array(getiriler)
    yuk, asg = arr[arr > 0], arr[arr < 0]
    isabet = len(yuk) / say * 100.0
    return {
        "n": say, "yukari": int(len(yuk)), "asagi": int(len(asg)),
        "ort_yukari": round(float(yuk.mean()), 1) if len(yuk) else 0.0,
        "ort_asagi": round(float(asg.mean()), 1) if len(asg) else 0.0,
        "isabet": round(float(isabet)),
        "notr": NOTR_ALT <= isabet <= NOTR_UST,
        "kucuk": say < KUCUK_ORNEKLEM,
    }


# ══════════════════════════════════════════════════════════════
# YÖNSÜZ OKUMALAR
# ══════════════════════════════════════════════════════════════
def okumalar(d):
    out = []
    k = d["Close"]
    n = len(d)
    if n < 60:
        return out
    son = float(k.iloc[-1])
    ma20, ma50, ma200, rsi = d["MA20"], d["MA50"], d["MA200"], d["RSI"]

    def ekle(tip, baslik, betim, algi, kosul):
        out.append({"tip": tip, "baslik": baslik, "betim": betim,
                    "algi": algi, "sicil": sicil(d, kosul)})

    if ma50.notna().iloc[-1] and ma200.notna().iloc[-1]:
        ustte = ma50 > ma200
        g_yuk = (ustte & ~ustte.shift(1, fill_value=ustte.iloc[0])).iloc[-10:].any()
        g_asg = (~ustte & ustte.shift(1, fill_value=ustte.iloc[0])).iloc[-10:].any()
        if g_yuk:
            ekle("golden", "MA50, MA200'ü yukarı kesti",
                 "Kısa ortalama uzun ortalamanın üstüne geçti (golden cross).",
                 "Klasik teoride 'yükseliş başlangıcı' sayılır — bu hissede sınanmalı.",
                 ustte & ~ustte.shift(1, fill_value=False))
        elif g_asg:
            ekle("death", "MA50, MA200'ü aşağı kesti",
                 "Kısa ortalama uzun ortalamanın altına geçti (death cross).",
                 "Klasik teoride 'zayıflama' sayılır — bu hissede sınanmalı.",
                 ~ustte & ustte.shift(1, fill_value=False))

    if ma20.notna().iloc[-1]:
        ust20 = k > ma20
        g_yuk = (ust20 & ~ust20.shift(1, fill_value=ust20.iloc[0])).iloc[-5:].any()
        g_asg = (~ust20 & ust20.shift(1, fill_value=ust20.iloc[0])).iloc[-5:].any()
        if g_yuk:
            ekle("fiyat_ma20_ust", "Fiyat 20 günlük ortalamanın üstüne çıktı",
                 "Kapanış kısa vadeli ortalamayı yukarı kesti.",
                 "Kısa vadeli güç okuması sayılır — sicile bak.",
                 ust20 & ~ust20.shift(1, fill_value=False))
        elif g_asg:
            ekle("fiyat_ma20_alt", "Fiyat 20 günlük ortalamanın altına indi",
                 "Kapanış kısa vadeli ortalamayı aşağı kesti.",
                 "Kısa vadeli zayıflık okuması sayılır — sicile bak.",
                 ~ust20 & ust20.shift(1, fill_value=False))

    pencere = min(250, n - 1)
    if son >= float(k.rolling(pencere).max().iloc[-1]) * 0.999:
        ekle("zirve", f"{pencere} günün en yükseğinde",
             "Fiyat seçili penceredeki en yüksek kapanışta.",
             "'Yeni zirve' güç sayılır ama tepe de olabilir — sicile bak.",
             k >= k.rolling(pencere).max() * 0.999)
    elif son <= float(k.rolling(pencere).min().iloc[-1]) * 1.001:
        ekle("dip", f"{pencere} günün en düşüğünde",
             "Fiyat seçili penceredeki en düşük kapanışta.",
             "'Yeni dip' zayıflık ya da dipten dönüş olabilir — sicile bak.",
             k <= k.rolling(pencere).min() * 1.001)

    if rsi.notna().iloc[-1]:
        rv = float(rsi.iloc[-1])
        if rv >= 70:
            ekle("rsi_yuksek", f"RSI yüksek ({rv:.0f})",
                 "Momentum göstergesi aşırı-alım bölgesinde.",
                 "Geleneksel okumada 'fazla ısındı' denir — sicil ne diyor?",
                 rsi >= 70)
        elif rv <= 30:
            ekle("rsi_dusuk", f"RSI düşük ({rv:.0f})",
                 "Momentum göstergesi aşırı-satım bölgesinde.",
                 "Geleneksel okumada 'fazla satıldı' denir — sicil ne diyor?",
                 rsi <= 30)

    if ma20.notna().iloc[-1]:
        if abs(son - float(ma20.iloc[-1])) / float(ma20.iloc[-1]) < 0.015:
            ekle("pullback", "Fiyat 20 günlük ortalamaya yaslandı",
                 "Kapanış kısa ortalamaya çok yakın (temas/pullback).",
                 "Ortalamadan dönüş klasik beklentidir — ama sınanmalı.",
                 (abs(k - ma20) / ma20 < 0.015))

    bg = d["BB_gen"]
    if bg.notna().iloc[-1]:
        esik = float(bg.dropna().iloc[-pencere:].quantile(0.15))
        if float(bg.iloc[-1]) <= esik:
            ekle("sikisma", "Bollinger bantları sıkıştı",
                 "Oynaklık daraldı; bantlar son dönemin en dar bölgesinde.",
                 "Sıkışma sonrası 'sert hareket' beklenir — yön belirsiz, sicile bak.",
                 bg <= bg.rolling(pencere, min_periods=20).quantile(0.15))

    if "Open" in d.columns:
        gap = (d["Open"] - k.shift(1)) / k.shift(1)
        if gap.notna().iloc[-1] and abs(float(gap.iloc[-1])) >= 0.03:
            yon = "yukarı" if float(gap.iloc[-1]) > 0 else "aşağı"
            ekle("gap", f"Fiyat {yon} boşlukla açıldı",
                 f"Açılış önceki kapanıştan belirgin {yon} (gap).",
                 "Boşluklar bazen dolar bazen sürüklenir — sicile bak.",
                 gap.abs() >= 0.03)

    return out


# ══════════════════════════════════════════════════════════════
# YAPI TESPİTİ (yönsüz geometrik gözlem)
# ══════════════════════════════════════════════════════════════
def yapilar(d, pencere=80):
    k = d["Close"].values
    n = len(k)
    if n < 40:
        return []
    seg = k[-pencere:] if n > pencere else k
    m = len(seg)
    x = np.arange(m)
    out = []
    egim, kesim = np.polyfit(x, seg, 1)
    tahmin = egim * x + kesim
    ss_res = np.sum((seg - tahmin) ** 2)
    ss_tot = np.sum((seg - seg.mean()) ** 2) + 1e-9
    r2 = 1 - ss_res / ss_tot
    ort = seg.mean()
    egim_oran = egim * m / ort
    if r2 >= 0.5 and abs(egim_oran) >= 0.05:
        out.append({"tip": "kanal",
                    "ad": "Yükselen kanal" if egim > 0 else "Düşen kanal",
                    "i0": int(m - m), "i1": int(m - 1)})  # detay-segment indeksleri
    elif (seg.max() - seg.min()) / ort < 0.08:
        out.append({"tip": "konsolidasyon", "ad": "Konsolidasyon bandı",
                    "i0": 0, "i1": int(m - 1)})

    def yerel(arr, tepe=True):
        u = []
        for i in range(2, len(arr) - 2):
            w = arr[i-2:i+3]
            if tepe and arr[i] == w.max():
                u.append(i)
            if not tepe and arr[i] == w.min():
                u.append(i)
        return u
    for tepe, ad, tip in [(True, "Olası çift tepe", "cift_tepe"),
                          (False, "Olası çift dip", "cift_dip")]:
        u = yerel(seg, tepe)
        if len(u) >= 2:
            a, b = u[-2], u[-1]
            if b - a >= 8 and abs(seg[a] - seg[b]) / ort < 0.03:
                out.append({"tip": tip, "ad": ad, "i0": int(a), "i1": int(b)})
                break
    return out


# ══════════════════════════════════════════════════════════════
# HİSSE PAKETİ — df çek, her şeyi hesapla, JSON-uyumlu dict döndür
# ══════════════════════════════════════════════════════════════
def _temiz(seri):
    return [None if (v is None or (isinstance(v, float) and not np.isfinite(v))) else round(float(v), 4)
            for v in seri]


def hisse_paketi(kod, gun=400):
    df, durum = veri.veri_al(kod, gun=gun, min_gun=60)
    if df is None or len(df) < 60:
        return {"kod": kod, "hata": durum or "veri yok"}
    d = gostergeler(df)
    oks = okumalar(d)
    yps = yapilar(d)

    detay = d.tail(DETAY_GUN)
    son = float(d["Close"].iloc[-1])
    onceki = float(d["Close"].iloc[-2]) if len(d) > 1 else son
    gun_pct = round((son - onceki) / onceki * 100, 2) if onceki else 0.0

    v_son = d["vol20"].dropna()
    vol_artti = bool(len(v_son) >= 6 and v_son.iloc[-1] > v_son.iloc[-6])

    # zirve/dip indeksleri (detay segmentinde)
    dk = detay["Close"].values
    return {
        "kod": kod,
        "son": round(son, 2),
        "gun_pct": gun_pct,
        "spark": _temiz(d["Close"].tail(SPARK_GUN).values),
        "detay": {
            "fiyat": _temiz(dk),
            "ma20": _temiz(detay["MA20"].values),
            "zirve_i": int(np.nanargmax(dk)),
            "dip_i": int(np.nanargmin(dk)),
            "ort": round(float(np.nanmean(dk)), 2),
        },
        "okumalar": oks,
        "yapilar": yps,
        "vol_artti": vol_artti,
    }


# ══════════════════════════════════════════════════════════════
# HTML/JS RENDER
# ══════════════════════════════════════════════════════════════
_TMPL = r"""
<div id="apexgp"></div>
<style>
#apexgp *{box-sizing:border-box;margin:0;padding:0;font-family:ui-monospace,'SF Mono',Menlo,monospace}
#apexgp{--bg:#0B0E13;--kart:#11161D;--cizgi:#1E2530;--ana:#E8EAED;--ikincil:#8A93A0;
  --silik:#5A6470;--teal:#2DD4BF;--amber:#F5A623;--yuk:#34D399;--dus:#F87171;--notr:#6B7280;
  background:var(--bg);color:var(--ana);padding:14px 4px;min-height:200px;position:relative}
#apexgp .ust{display:flex;justify-content:space-between;align-items:baseline;padding:0 8px 12px}
#apexgp .ust h2{font-size:15px;letter-spacing:1px;font-weight:600}
#apexgp .ust span{font-size:10px;color:var(--silik);letter-spacing:.5px}
#apexgp .grid{display:grid;grid-template-columns:1fr 1fr;gap:8px;padding:0 8px}
#apexgp .tile{position:relative;aspect-ratio:1/1;background:var(--kart);border:1px solid var(--cizgi);
  border-radius:12px;overflow:hidden;cursor:pointer;transition:border-color .15s,transform .1s}
#apexgp .tile:active{transform:scale(.985)}
#apexgp .tile svg.spk{position:absolute;inset:0;width:100%;height:100%;opacity:.5}
#apexgp .tile .ic{position:relative;z-index:2;padding:11px 12px;height:100%;display:flex;flex-direction:column;justify-content:space-between}
#apexgp .tile .kod{font-size:16px;font-weight:600;letter-spacing:.5px}
#apexgp .tile .fiyat{font-size:13px;color:var(--ana)}
#apexgp .tile .deg{font-size:11px;font-weight:600}
#apexgp .tile .alt{display:flex;justify-content:space-between;align-items:flex-end}
#apexgp .rozet{font-size:9.5px;color:var(--silik);background:#0B0E13aa;border:1px solid var(--cizgi);
  border-radius:20px;padding:2px 7px;letter-spacing:.3px}
#apexgp .hata{grid-column:span 1;aspect-ratio:1/1;display:flex;align-items:center;justify-content:center;
  background:var(--kart);border:1px solid var(--cizgi);border-radius:12px;color:var(--silik);font-size:10px;text-align:center;padding:10px}

/* slide-up detay */
#apexgp .detay{position:absolute;inset:0;background:var(--bg);transform:translateY(101%);
  transition:transform .28s cubic-bezier(.4,0,.2,1);overflow-y:auto;z-index:10;padding:14px 12px 30px}
#apexgp .detay.acik{transform:translateY(0)}
#apexgp .dust{display:flex;justify-content:space-between;align-items:center;margin-bottom:6px}
#apexgp .dust .sol{display:flex;align-items:baseline;gap:9px}
#apexgp .dust .kod{font-size:20px;font-weight:600;letter-spacing:.5px}
#apexgp .dust .fiyat{font-size:15px}
#apexgp .dust .deg{font-size:12px;font-weight:600}
#apexgp .kapat{background:none;border:1px solid var(--cizgi);color:var(--ikincil);
  border-radius:8px;padding:6px 12px;font-size:12px;cursor:pointer}
#apexgp .grafik{background:var(--kart);border:1px solid var(--cizgi);border-radius:12px;
  padding:8px;margin:8px 0 4px}
#apexgp .grafik svg{width:100%;display:block;overflow:visible}
#apexgp .yapibar{display:flex;gap:6px;flex-wrap:wrap;margin:6px 0 10px}
#apexgp .yapibar .y{font-size:10px;color:var(--amber);border:1px solid #F5A62355;
  background:#F5A6231a;border-radius:20px;padding:3px 9px}
#apexgp .okbas{font-size:10px;color:var(--silik);letter-spacing:1px;margin:12px 2px 6px;text-transform:uppercase}
#apexgp .ok{background:var(--kart);border:1px solid var(--cizgi);border-radius:11px;padding:11px 12px;margin-bottom:8px}
#apexgp .ok .b{font-size:13.5px;font-weight:600;margin-bottom:3px}
#apexgp .ok .bt{font-size:11.5px;color:var(--ikincil);line-height:1.45;margin-bottom:5px}
#apexgp .ok .al{font-size:11px;color:var(--amber);line-height:1.4;margin-bottom:9px}
#apexgp .ok .al::before{content:'piyasa algısı · '}
#apexgp .sic{border-top:1px dashed var(--cizgi);padding-top:8px}
#apexgp .sic .sb{display:flex;justify-content:space-between;align-items:center;margin-bottom:6px}
#apexgp .sic .et{font-size:9.5px;color:var(--silik);letter-spacing:.5px}
#apexgp .sic .nn{font-size:10px;color:var(--ikincil)}
#apexgp .sic .say{display:flex;gap:14px;font-size:12px;margin-bottom:7px}
#apexgp .sic .yuk b{color:var(--yuk)} #apexgp .sic .dus b{color:var(--dus)}
#apexgp .sic .say .o{color:var(--silik);font-size:10.5px}
#apexgp .bar{height:6px;background:#0B0E13;border:1px solid var(--cizgi);border-radius:4px;overflow:hidden;position:relative}
#apexgp .bar i{position:absolute;top:0;bottom:0;left:0;display:block}
#apexgp .bar .mid{position:absolute;left:50%;top:-2px;bottom:-2px;width:1px;background:var(--silik);opacity:.6}
#apexgp .isb{display:flex;justify-content:space-between;font-size:10px;margin-top:4px;color:var(--ikincil)}
#apexgp .uyari{font-size:10px;color:var(--notr);margin-top:6px;font-style:italic}
#apexgp .bos{text-align:center;color:var(--silik);font-size:11px;padding:18px}
</style>
<script>
const APEX_GP = __VERI__;
(function(){
  const kok = document.getElementById('apexgp');
  const renk = (g)=> g>0?'var(--yuk)': g<0?'var(--dus)':'var(--ikincil)';

  function sparkSVG(arr){
    const v = arr.filter(x=>x!=null);
    if(v.length<2) return '';
    const mn=Math.min(...v), mx=Math.max(...v), rng=(mx-mn)||1;
    const W=100,H=40, n=arr.length;
    let d='', started=false;
    arr.forEach((y,i)=>{ if(y==null) return;
      const px=(i/(n-1))*W, py=H-((y-mn)/rng)*H;
      d += (started?'L':'M')+px.toFixed(1)+' '+py.toFixed(1)+' '; started=true; });
    const up = v[v.length-1]>=v[0];
    const c = up?'#34D399':'#F87171';
    return '<svg class="spk" viewBox="0 0 100 40" preserveAspectRatio="none">'+
      '<path d="'+d+'" fill="none" stroke="'+c+'" stroke-width="1.4"/></svg>';
  }

  // ── DETAY grafik: fiyat + ma20 + zirve/dip callout + ort + 20G ort uç etiketi + vol ──
  function detaySVG(p){
    const f=p.detay.fiyat, ma=p.detay.ma20, n=f.length;
    const W=320,H=150, padT=14,padB=14, plotH=H-padT-padB;
    const vals=f.filter(x=>x!=null).concat(ma.filter(x=>x!=null));
    const mn=Math.min(...vals), mx=Math.max(...vals), rng=(mx-mn)||1;
    const X=i=> (i/(n-1))*W;
    const Y=y=> padT+plotH-((y-mn)/rng)*plotH;
    let fp='',st=false;
    f.forEach((y,i)=>{ if(y==null)return; fp+=(st?'L':'M')+X(i).toFixed(1)+' '+Y(y).toFixed(1)+' '; st=true; });
    let mp='',st2=false;
    ma.forEach((y,i)=>{ if(y==null)return; mp+=(st2?'L':'M')+X(i).toFixed(1)+' '+Y(y).toFixed(1)+' '; st2=true; });
    const up=f[n-1]>=f.find(x=>x!=null);
    const fc=up?'#34D399':'#F87171';

    // amber yapı overlay
    let yapi='';
    (p.yapilar||[]).forEach(yp=>{
      if(yp.tip==='kanal'){
        // segment regresyon çizgisi (basit: i0..i1 uçları fiyatla)
        const a=Math.max(0,yp.i0), b=Math.min(n-1,yp.i1);
        if(f[a]!=null&&f[b]!=null)
          yapi+='<line x1="'+X(a)+'" y1="'+Y(f[a])+'" x2="'+X(b)+'" y2="'+Y(f[b])+'" stroke="#F5A623" stroke-width="1" stroke-dasharray="3 3" opacity=".8"/>';
      } else if(yp.tip==='konsolidasyon'){
        const seg=f.slice(yp.i0,yp.i1+1).filter(x=>x!=null);
        if(seg.length){const u=Math.max(...seg),l=Math.min(...seg);
          yapi+='<rect x="'+X(yp.i0)+'" y="'+Y(u)+'" width="'+(X(yp.i1)-X(yp.i0))+'" height="'+(Y(l)-Y(u))+'" fill="#F5A6231a" stroke="#F5A62366" stroke-width="1"/>';}
      } else { // çift tepe/dip
        [yp.i0,yp.i1].forEach(ix=>{ if(f[ix]!=null)
          yapi+='<circle cx="'+X(ix)+'" cy="'+Y(f[ix])+'" r="3" fill="none" stroke="#F5A623" stroke-width="1.2"/>';});
        if(f[yp.i0]!=null&&f[yp.i1]!=null)
          yapi+='<line x1="'+X(yp.i0)+'" y1="'+Y(f[yp.i0])+'" x2="'+X(yp.i1)+'" y2="'+Y(f[yp.i1])+'" stroke="#F5A62366" stroke-width="1" stroke-dasharray="2 2"/>';
      }
    });

    // zirve / dip callout
    const zi=p.detay.zirve_i, di=p.detay.dip_i;
    let cal='';
    if(f[zi]!=null){ cal+='<circle cx="'+X(zi)+'" cy="'+Y(f[zi])+'" r="2.4" fill="#E8EAED"/>'+
      '<text x="'+X(zi)+'" y="'+(Y(f[zi])-5)+'" fill="#8A93A0" font-size="8" text-anchor="middle">zirve '+f[zi].toFixed(2)+'</text>'; }
    if(f[di]!=null){ cal+='<circle cx="'+X(di)+'" cy="'+Y(f[di])+'" r="2.4" fill="#E8EAED"/>'+
      '<text x="'+X(di)+'" y="'+(Y(f[di])+11)+'" fill="#8A93A0" font-size="8" text-anchor="middle">dip '+f[di].toFixed(2)+'</text>'; }

    // 20G ortalama uç etiketi
    let maEt='';
    const lastMa=[...ma].reverse().find(x=>x!=null);
    if(lastMa!=null){ maEt='<text x="'+(W-2)+'" y="'+(Y(lastMa)-3)+'" fill="#38BDF8" font-size="8" text-anchor="end">20G ort</text>'; }

    // ortalama çizgisi (kesik)
    const ortY=Y(p.detay.ort);
    const ortLn='<line x1="0" y1="'+ortY+'" x2="'+W+'" y2="'+ortY+'" stroke="#5A6470" stroke-width=".6" stroke-dasharray="1 4"/>'+
      '<text x="2" y="'+(ortY-3)+'" fill="#5A6470" font-size="7.5">dönem ort '+p.detay.ort.toFixed(2)+'</text>';

    // son fiyat noktası + vol işareti
    let sonN='';
    const li=(function(){for(let i=n-1;i>=0;i--)if(f[i]!=null)return i;return n-1;})();
    if(f[li]!=null){ sonN='<circle cx="'+X(li)+'" cy="'+Y(f[li])+'" r="3" fill="'+fc+'"/>'; }
    const volEt = p.vol_artti
      ? '<text x="2" y="11" fill="#F5A623" font-size="8">⚠ oynaklık arttı</text>'
      : '<text x="2" y="11" fill="#5A6470" font-size="8">oynaklık sakin</text>';

    return '<svg viewBox="0 0 '+W+' '+H+'">'+ortLn+yapi+
      '<path d="'+mp+'" fill="none" stroke="#38BDF8" stroke-width="1" opacity=".85"/>'+
      '<path d="'+fp+'" fill="none" stroke="'+fc+'" stroke-width="1.5"/>'+
      cal+maEt+sonN+volEt+'</svg>';
  }

  function sicilHTML(s){
    if(s.n===0) return '<div class="sic"><div class="uyari">Bu hissede son 1 yılda örnek yok — sicil hesaplanamadı.</div></div>';
    const w = s.isabet, sol=Math.min(100,Math.max(0,w));
    const barRenk = s.notr ? 'var(--notr)' : (s.kucuk?'var(--silik)':'var(--teal)');
    let durum='';
    if(s.notr) durum='<span class="nn">≈ yazı-tura</span>';
    else if(s.kucuk) durum='<span class="nn">küçük örneklem</span>';
    return '<div class="sic">'+
      '<div class="sb"><span class="et">SON 1 YIL · '+s.n+' KEZ YAŞANDI · sonraki ~10 gün</span>'+durum+'</div>'+
      '<div class="say">'+
        '<span class="yuk">▲ <b>'+s.yukari+'</b> <span class="o">ort +'+s.ort_yukari+'%</span></span>'+
        '<span class="dus">▼ <b>'+s.asagi+'</b> <span class="o">ort '+s.ort_asagi+'%</span></span>'+
      '</div>'+
      '<div class="bar"><i style="width:'+sol+'%;background:'+barRenk+';opacity:.55"></i><span class="mid"></span></div>'+
      '<div class="isb"><span>sonraki ~10 günde yukarı kapatma</span><span style="color:'+barRenk+'">%'+w+'</span></div>'+
      (s.kucuk&&!s.notr?'<div class="uyari">Küçük örneklem — güvenme.</div>':'')+
      '</div>';
  }

  function detayHTML(p){
    const okHtml = (p.okumalar&&p.okumalar.length)
      ? p.okumalar.map(o=>'<div class="ok"><div class="b">'+o.baslik+'</div>'+
          '<div class="bt">'+o.betim+'</div><div class="al">'+o.algi+'</div>'+sicilHTML(o.sicil)+'</div>').join('')
      : '<div class="bos">Bugün belirgin bir okuma yok. Sade seyir.</div>';
    const yapiBar = (p.yapilar&&p.yapilar.length)
      ? '<div class="yapibar">'+p.yapilar.map(y=>'<span class="y">▱ '+y.ad+'</span>').join('')+'</div>' : '';
    return '<div class="dust"><div class="sol"><span class="kod">'+p.kod+'</span>'+
      '<span class="fiyat">'+p.son+'</span>'+
      '<span class="deg" style="color:'+renk(p.gun_pct)+'">'+(p.gun_pct>0?'+':'')+p.gun_pct+'%</span></div>'+
      '<button class="kapat" onclick="window.__apexKapat()">✕ kapat</button></div>'+
      '<div class="grafik">'+detaySVG(p)+'</div>'+yapiBar+
      '<div class="okbas">Okumalar · veri önde, yön yok</div>'+okHtml;
  }

  // tile grid
  let g='<div class="ust"><h2>APEX · GÖRSEL PANEL</h2><span>VERİ ÖNDE · YÖN YOK · HER OKUMA SİCİLİNİ TAŞIR</span></div><div class="grid">';
  APEX_GP.forEach((p,ix)=>{
    if(p.hata){ g+='<div class="hata">'+p.kod+'<br>veri yok</div>'; return; }
    const adet=(p.okumalar||[]).length;
    g+='<div class="tile" onclick="window.__apexAc('+ix+')">'+sparkSVG(p.spark)+
      '<div class="ic"><div><div class="kod">'+p.kod+'</div></div>'+
      '<div class="alt"><div><div class="fiyat">'+p.son+'</div>'+
      '<div class="deg" style="color:'+renk(p.gun_pct)+'">'+(p.gun_pct>0?'+':'')+p.gun_pct+'%</div></div>'+
      '<div class="rozet">'+(adet?adet+' okuma':'sade')+'</div></div></div></div>';
  });
  g+='</div><div class="detay" id="apexdetay"></div>';
  kok.innerHTML=g;

  const dt=document.getElementById('apexdetay');
  window.__apexAc=(ix)=>{ dt.innerHTML=detayHTML(APEX_GP[ix]); dt.classList.add('acik'); dt.scrollTop=0; };
  window.__apexKapat=()=>{ dt.classList.remove('acik'); };
})();
</script>
"""


def goster(kodlar, gun=400, yukseklik=None):
    """app.py/sayfadan çağrılır. kodlar: hisse kodu listesi."""
    if st is None:
        raise RuntimeError("streamlit yok")
    paketler = _paketler_cache(tuple(kodlar), gun)
    veri_json = json.dumps(paketler, ensure_ascii=False)
    html = _TMPL.replace("__VERI__", veri_json)
    if yukseklik is None:
        satir = (len(kodlar) + 1) // 2
        yukseklik = 90 + satir * 180  # grid yüksekliği; detay overlay üstüne biner
    components.html(html, height=int(yukseklik), scrolling=True)


def _paketleri_cek(kodlar, gun):
    """Hisseleri paralel çek (100 hisse seri olursa çok yavaş)."""
    from concurrent.futures import ThreadPoolExecutor
    out = {}
    with ThreadPoolExecutor(max_workers=8) as ex:
        futs = {ex.submit(hisse_paketi, k, gun): k for k in kodlar}
        for f in futs:
            k = futs[f]
            try:
                out[k] = f.result()
            except Exception as e:
                out[k] = {"kod": k, "hata": type(e).__name__}
    return [out[k] for k in kodlar]  # giriş sırasını koru


# Streamlit cache (varsa) — veri çekimi pahalı
if st is not None:
    @st.cache_data(ttl=900, show_spinner=False)
    def _paketler_cache(kodlar_tuple, gun):
        return _paketleri_cek(list(kodlar_tuple), gun)
else:
    def _paketler_cache(kodlar_tuple, gun):
        return _paketleri_cek(list(kodlar_tuple), gun)
