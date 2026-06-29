# -*- coding: utf-8 -*-
"""
gorsel_panel.py — APEX gerçek-veri görsel özet (koyu tema, SVG).

FELSEFE: Sinyal/hedef/yön tahmini YOK. Veri yoksa "—".
Çizgiler ve olay işaretleri GEÇMİŞ OLGUdur; gelecek tahmini değildir.
Ortalama kesişimi yönsüz gösterilir (backtest: ~%50 yazı-tura).

Kullanım (app.py içinde bir sekmede):
    import gorsel_panel
    st.markdown(gorsel_panel.panel_html(), unsafe_allow_html=True)

Sadece veri.veri_al'a bağlıdır; motoru (karar/sinyal) ÇAĞIRMAZ.
"""

import numpy as np
import pandas as pd

from veri import veri_al, VADE_AYAR

# Kendi izleme listen:
IZLEME = IZLEME = [
    # 🏦 Bankacılık
    "AKBNK","GARAN","HALKB","ISCTR","VAKBN","YKBNK","TSKB","ALBRK","SKBNK","KLNMA",
    # ⚡ Enerji
    "EUPWR","ODAS","ENJSA","AKSEN","ZOREN","AYEN","AYDEM","KCAER","CWENE","NATEN",
    # 🏭 Sanayi
    "EREGL","KRDMD","ISDMR","CEMTS","CIMSA","AFYON","ARCLK","VESTL","BFREN","DOAS","OTKAR","FROTO","TOASO","TTRAK",
    # 💊 Sağlık / Kimya
    "ECILC","SELEC","MPARK","DEVA","ECZYT","GUBRF","HEKTS","PETKM","SASA","TRCAS","PRKAB",
    # 🛒 Perakende / Gıda
    "BIMAS","MGROS","SOKM","ULKER","CCOLA","AEFES","TATGD","PNSUT","BANVT","DARDL",
    # 📡 Teknoloji / Telekom
    "TTKOM","TCELL","ASELS","NETAS","LOGO","INDES","ARENA","DGATE","KAREL","SMART","PAPIL",
    # ✈️ Ulaşım / Turizm
    "THYAO","PGSUS","TAVHL","CLEBI","MAALT","RYSAS",
    # 🏗️ İnşaat / GYO
    "EKGYO","ISGYO","TRGYO","KLGYO","VKGYO","SNGYO","HLGYO","ENKAI","TKFEN","GSDHO",
    # 💼 Holding
    "SAHOL","KCHOL","DOHOL","ALARK","BERA","GOLTS","ADEL","GESAN","MAVI","BRISA","KARSN","GLYHO",
]

PAL = dict(siyah="#06080B", panel="#0C1117", panel2="#10161E", cizgi="#1B2530",
           metin="#E8E4D8", soluk="#69727E", soluk2="#454D58", notr="#9AA3AD",
           teal="#2DD4BF", rust="#E2563B", amber="#F2B441")

_AY = ["Oca", "Şub", "Mar", "Nis", "May", "Haz", "Tem", "Ağu", "Eyl", "Eki", "Kas", "Ara"]
_NSON = 60  # grafikte gösterilecek son bar sayısı


def _etk(ts):
    try:
        return f"{ts.day} {_AY[ts.month - 1]}"
    except Exception:
        return ""


# ── METRİKLER (betimleyici, ham df'ten) ────────────────────────────
def _metrik(df, vade):
    if df is None or len(df) < 2:
        return None
    close = df["Close"].astype(float)
    high = df["High"].astype(float)
    low = df["Low"].astype(float)
    vol = df["Volume"].astype(float)
    son = float(close.iloc[-1])
    gun = float(close.iloc[-1] / close.iloc[-2] - 1) * 100
    n = min(20, len(df))
    tp = (high + low + close) / 3.0
    hac = vol.iloc[-n:].sum()
    vwap = float((tp.iloc[-n:] * vol.iloc[-n:]).sum() / hac) if hac > 0 else son
    konum = (son / vwap - 1) * 100 if vwap > 0 else None
    pc = close.shift(1)
    tr = pd.concat([(high - low), (high - pc).abs(), (low - pc).abs()], axis=1).max(axis=1)
    atr = float(tr.iloc[-14:].mean()) if len(tr.dropna()) >= 1 else None
    stop = (atr * float(vade.get("atr_stop", 1.0)) / son) * 100 if (atr and son > 0) else None
    ret = close.pct_change().dropna()
    oyn = "—"
    if len(ret) >= 30:
        kisa = ret.iloc[-20:].std()
        dag = ret.rolling(20).std().dropna()
        if len(dag) >= 5 and pd.notna(kisa):
            p = float((dag < kisa).mean())
            oyn = "fırtına" if p > 0.66 else ("sakin" if p < 0.33 else "normal")
    return dict(son=son, gun=gun, konum=konum, stop=stop, oyn=oyn)


# ── OLAYLAR (gerçek kapanıştan, yönsüz) ─────────────────────────────
def _olaylar(s):
    n = len(s)
    ev = []
    if n < 31:
        return ev
    ser = pd.Series(s)
    m1 = ser.rolling(10).mean().values
    m2 = ser.rolling(30).mean().values
    for i in range(31, n):
        a, b = m1[i - 1] - m2[i - 1], m1[i] - m2[i]
        if not np.isnan(a) and not np.isnan(b) and a != 0 and ((a < 0) != (b < 0)):
            ev.append((i, "kesisim", None))
    for i in range(20, n):
        win = s[i - 19:i + 1]
        if s[i] == win.max() and s[i - 1] != s[i - 20:i].max():
            ev.append((i, "zirve", None))
        if s[i] == win.min() and s[i - 1] != s[i - 20:i].min():
            ev.append((i, "dip", None))
    ret = np.concatenate([[0.0], np.diff(s) / s[:-1]])
    std = pd.Series(ret).rolling(20).std().values
    valid = std[~np.isnan(std)]
    if len(valid) >= 6:
        t1, t2 = np.quantile(valid, 1 / 3), np.quantile(valid, 2 / 3)
        lab = lambda x: None if np.isnan(x) else (2 if x > t2 else (0 if x < t1 else 1))
        prev = None
        for i in range(20, n):
            L = lab(std[i])
            if prev is not None and L is not None and L != prev:
                ev.append((i, "oyn", None))
            if L is not None:
                prev = L
    sig = float(np.nanstd(np.diff(s) / s[:-1])) or 0.01
    for i in range(1, n):
        g = s[i] / s[i - 1] - 1
        if abs(g) > 2.3 * sig:
            ev.append((i, "gap", g))
    ev = [e for e in ev if e[0] >= n - 40]
    ev.sort(key=lambda e: e[0])
    return ev[-4:]


def _isaret(cx, cy, tip):
    cx, cy = float(cx), float(cy)
    if tip == "kesisim":
        return f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="4.2" fill="none" stroke="{PAL["notr"]}" stroke-width="1.6"/>'
    if tip == "zirve":
        return f'<path d="M{cx:.1f},{cy-6:.1f} L{cx-4.5:.1f},{cy+2:.1f} L{cx+4.5:.1f},{cy+2:.1f} Z" fill="none" stroke="#C7C2B5" stroke-width="1.4"/>'
    if tip == "dip":
        return f'<path d="M{cx:.1f},{cy+6:.1f} L{cx-4.5:.1f},{cy-2:.1f} L{cx+4.5:.1f},{cy-2:.1f} Z" fill="none" stroke="#C7C2B5" stroke-width="1.4"/>'
    if tip == "oyn":
        return f'<rect x="{cx-4:.1f}" y="{cy-4:.1f}" width="8" height="8" fill="none" stroke="{PAL["amber"]}" stroke-width="1.5"/>'
    if tip == "gap":
        return f'<line x1="{cx:.1f}" y1="{cy-8:.1f}" x2="{cx:.1f}" y2="{cy+8:.1f}" stroke="{PAL["notr"]}" stroke-width="1.5" stroke-dasharray="2 2"/>'
    return ""


def _olay_yazi(i, tip, g, dates):
    t = _etk(dates[i]) if i < len(dates) else ""
    if tip == "kesisim":
        return ("◯", True, f'<span style="color:{PAL["soluk"]};font-family:monospace">{t}</span> · kısa/uzun ortalama kesişti — '
                            f'<span style="color:{PAL["amber"]}">geçmişte ~%50 isabet (yazı-tura), yön sinyali değil</span>')
    if tip == "zirve":
        return ("△", False, f'<span style="color:{PAL["soluk"]};font-family:monospace">{t}</span> · son 20 günün en yükseği görüldü')
    if tip == "dip":
        return ("▽", False, f'<span style="color:{PAL["soluk"]};font-family:monospace">{t}</span> · son 20 günün en düşüğü görüldü')
    if tip == "oyn":
        return ("▢", True, f'<span style="color:{PAL["soluk"]};font-family:monospace">{t}</span> · oynaklık rejimi değişti')
    if tip == "gap":
        return ("⋮", False, f'<span style="color:{PAL["soluk"]};font-family:monospace">{t}</span> · büyük günlük boşluk %{g*100:.1f}')
    return ("", False, "")


def _svg(s, dates, ev):
    W, H, pl, pr, pt, pb = 600, 170, 8, 52, 14, 22
    ix, iy = W - pl - pr, H - pt - pb
    lo, hi = float(np.min(s)), float(np.max(s))
    rg = (hi - lo) or 1.0
    n = len(s)
    X = lambda i: pl + i / (n - 1) * ix
    Y = lambda v: pt + (1 - (v - lo) / rg) * iy
    m = pd.Series(s).rolling(20).mean().values
    fp = " ".join(f"{'L' if i else 'M'}{X(i):.1f},{Y(v):.1f}" for i, v in enumerate(s))
    mp = ""
    for i, v in enumerate(m):
        if not np.isnan(v):
            mp += f"{'L' if mp else 'M'}{X(i):.1f},{Y(v):.1f} "
    ap = f"{fp} L{X(n-1):.1f},{H-pb:.1f} L{X(0):.1f},{H-pb:.1f} Z"
    gx = "".join(f'<line x1="{pl}" y1="{Y(v):.1f}" x2="{W-pr}" y2="{Y(v):.1f}" stroke="{PAL["cizgi"]}"/>'
                 for v in (hi, (hi + lo) / 2, lo))
    yl = "".join(f'<text x="{W-pr+8}" y="{Y(v)+3:.1f}" fill="{PAL["soluk"]}" font-size="10" font-family="monospace">{v:.2f}</text>'
                 for v in (hi, (hi + lo) / 2, lo))
    xi = [0, n // 3, 2 * n // 3, n - 1]
    anc = lambda i: "start" if i == 0 else ("end" if i == n - 1 else "middle")
    xl = "".join(f'<text x="{X(i):.1f}" y="{H-6}" fill="{PAL["soluk2"]}" font-size="9.5" font-family="monospace" text-anchor="{anc(i)}">{_etk(dates[i]) if i < len(dates) else ""}</text>'
                 for i in xi)
    mk = "".join(_isaret(X(i), Y(s[i]), tip) for i, tip, _ in ev)
    cx, cy = X(n - 1), Y(s[n - 1])
    return (f'<svg viewBox="0 0 {W} {H}" preserveAspectRatio="none" style="width:100%;height:auto;margin-top:6px">'
            f'{gx}<path d="{ap}" fill="{PAL["teal"]}11"/>'
            f'<path d="{mp}" fill="none" stroke="{PAL["amber"]}" stroke-width="1.3" stroke-dasharray="4 3" opacity="0.8"/>'
            f'<path d="{fp}" fill="none" stroke="{PAL["teal"]}" stroke-width="2"/>'
            f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="3.3" fill="{PAL["teal"]}"/>'
            f'{mk}{yl}{xl}</svg>')


def _blok(kod, vade_key):
    vade = VADE_AYAR.get(vade_key, VADE_AYAR["gunluk"])
    df, _ = veri_al(kod, gun=vade["gun"], min_gun=vade["min_gun"], aralik=vade["aralik"])
    m = _metrik(df, vade)
    if m is None:
        return (f'<div style="background:{PAL["panel"]};border:1px solid {PAL["cizgi"]};border-radius:14px;'
                f'padding:16px;margin-bottom:16px"><div style="font-family:Archivo,sans-serif;font-weight:800;'
                f'font-size:1.15rem">{kod}</div><div style="color:{PAL["soluk"]};margin-top:8px">— veri yok</div></div>')
    s = df["Close"].astype(float).values[-_NSON:]
    dates = list(df.index[-_NSON:])
    ev = _olaylar(s)
    ust = (m["konum"] or 0) >= 0
    gc = PAL["teal"] if m["gun"] > 0 else (PAL["rust"] if m["gun"] < 0 else PAL["soluk"])
    gs = "+" if m["gun"] > 0 else ("−" if m["gun"] < 0 else "")
    konum_html = (f'ort. <b style="color:{PAL["teal"] if ust else PAL["rust"]}">{"+" if ust else "−"}%{abs(m["konum"]):.1f}</b> '
                  f'{"üstünde" if ust else "altında"}') if m["konum"] is not None else "ort. —"
    stop_html = f'~−%{m["stop"]:.1f}' if m["stop"] is not None else "—"
    cip = lambda html: f'<span style="font-family:monospace;font-size:.68rem;color:{PAL["soluk"]};background:{PAL["panel2"]};border:1px solid {PAL["cizgi"]};border-radius:6px;padding:3px 8px">{html}</span>'
    cipler = " ".join([cip(konum_html), cip(f'oynaklık <b style="color:{PAL["amber"]}">{m["oyn"]}</b>'), cip(f'stop <b>{stop_html}</b>')])

    olay_html = ""
    if ev:
        satir = []
        for i, tip, g in ev:
            ik, amb, html = _olay_yazi(i, tip, g, dates)
            renk = PAL["amber"] if amb else PAL["notr"]
            satir.append(f'<div style="display:flex;gap:8px;font-size:.74rem;line-height:1.45;color:#B7B2A6">'
                         f'<span style="flex:none;width:16px;text-align:center;color:{renk};font-family:monospace">{ik}</span>'
                         f'<span>{html}</span></div>')
        olay_html = f'<div style="margin-top:11px;display:flex;flex-direction:column;gap:5px">{"".join(satir)}</div>'

    if m["konum"] is None:
        yorum = "Konum hesaplanamadı (yetersiz veri)."
    elif ust:
        yorum = f'Fiyat son 20 günün ortalamasının <b style="color:{PAL["metin"]}">%{m["konum"]:.1f} üstünde</b> — son işlemler ortalamanın üzerinde, kısa vadede alıcı baskın.'
    else:
        yorum = f'Fiyat son 20 günün ortalamasının <b style="color:{PAL["metin"]}">%{abs(m["konum"]):.1f} altında</b> — son işlemler ortalamanın altında, kısa vadede satıcı baskın.'
    oyn_y = {"sakin": " Oynaklık sakin, hareket sıkışık.", "normal": " Oynaklık normal.",
             "fırtına": " Oynaklık sert, hareket geniş.", "—": ""}.get(m["oyn"], "")
    yorum += oyn_y + (f' Pozisyon alınırsa makul risk (stop) mesafesi <b style="color:{PAL["metin"]}">{stop_html}</b>.' if m["stop"] is not None else "")

    return (f'<div style="background:{PAL["panel"]};border:1px solid {PAL["cizgi"]};border-radius:14px;padding:16px 16px 14px;margin-bottom:16px">'
            f'<div style="display:flex;align-items:baseline;justify-content:space-between;gap:10px">'
            f'<span style="font-family:Archivo,sans-serif;font-weight:800;font-size:1.15rem">{kod}</span>'
            f'<span><span style="font-family:monospace;font-size:1.05rem">{m["son"]:.2f}₺</span> '
            f'<span style="font-family:monospace;font-size:.8rem;color:{gc};border:1px solid {PAL["cizgi"]};border-radius:6px;padding:2px 8px">bugün {gs}%{abs(m["gun"]):.1f}</span></span></div>'
            f'<div style="display:flex;flex-wrap:wrap;gap:7px;margin:11px 0 4px">{cipler}</div>'
            f'{_svg(s, dates, ev)}{olay_html}'
            f'<div style="font-size:.82rem;line-height:1.6;color:#C7C2B5;margin-top:12px;padding-top:12px;border-top:1px solid {PAL["cizgi"]}">{yorum}</div>'
            f'</div>')


def panel_html(kodlar=None, vade_key="gunluk"):
    kodlar = kodlar or IZLEME
    bloklar = "".join(_blok(k, vade_key) for k in kodlar)
    dipnot = (f'<div style="display:flex;flex-wrap:wrap;gap:13px;margin-top:6px;padding-top:12px;border-top:1px solid {PAL["cizgi"]};font-size:.7rem;color:{PAL["soluk"]}">'
              f'<span><span style="font-family:monospace;color:{PAL["notr"]}">◯</span> ortalama kesişimi</span>'
              f'<span><span style="font-family:monospace;color:{PAL["notr"]}">△ ▽</span> 20-gün zirve / dip</span>'
              f'<span><span style="font-family:monospace;color:{PAL["amber"]}">▢</span> oynaklık değişimi</span>'
              f'<span><span style="font-family:monospace;color:{PAL["notr"]}">⋮</span> büyük boşluk</span></div>'
              f'<div style="margin-top:12px;font-size:.72rem;color:{PAL["soluk"]};line-height:1.55">'
              f'Tüm işaretler <b style="color:{PAL["metin"]}">geçmiş olaylardır, tahmin değildir.</b> Ortalama kesişimi yön sinyali sanılır ama kalibrasyonda ~%50 (yazı-tura) çıktı.<br>'
              f'Sinyal yok · hedef/getiri yok · «şu olur / beklenir» yok. Karar senin. Yatırım tavsiyesi değildir.</div>')
    return (f'<div style="background:{PAL["siyah"]};color:{PAL["metin"]};font-family:\'Hanken Grotesk\',sans-serif;'
            f'padding:18px 14px;border-radius:16px">'
            f'<div style="font-family:Archivo,sans-serif;font-weight:800;font-size:1.4rem;letter-spacing:.05em;margin-bottom:14px">'
            f'A<span style="color:{PAL["teal"]}">P</span>EX <span style="font-family:monospace;font-weight:400;font-size:.8rem;color:{PAL["soluk"]}">· kapanış analizi</span></div>'
            f'{bloklar}{dipnot}</div>')


def render(kodlar=None, vade_key="gunluk"):
    import streamlit as st
    st.markdown(panel_html(kodlar, vade_key), unsafe_allow_html=True)
