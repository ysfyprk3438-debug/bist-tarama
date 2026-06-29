# -*- coding: utf-8 -*-
# surum 2 - tile yenile
"""
gorsel_panel.py — APEX gercek-veri gorsel ozet (koyu tema, SVG).

YAPI: tile_html(kod) -> kutu sekme (yuzde/emoji/trend/mini grafik)
      detay_html(kod) -> grafikten konusan zengin detay (hacim + golge + olaylar, AZ yazi).
FELSEFE: Sinyal/hedef/yon tahmini YOK. Veri yoksa "—".
Renkli golge/hacim "grafik okuma"ya yardim eder; OLANI anlatir, gelecegi degil.
Sadece veri.veri_al'a baglidir.
"""
import numpy as np
import pandas as pd
from veri import veri_al, VADE_AYAR

IZLEME = ["AKBNK", "GARAN", "EREGL", "THYAO", "TUPRS", "ASELS"]
PAL = dict(siyah="#06080B", panel="#0C1117", panel2="#10161E", cizgi="#1B2530",
           metin="#E8E4D8", soluk="#69727E", soluk2="#454D58", notr="#9AA3AD",
           teal="#2DD4BF", rust="#E2563B", amber="#F2B441")
_AY = ["Oca","Şub","Mar","Nis","May","Haz","Tem","Ağu","Eyl","Eki","Kas","Ara"]
_NSON = 60

def _etk(ts):
    try: return f"{ts.day} {_AY[ts.month-1]}"
    except Exception: return ""

def _metrik(df, vade):
    if df is None or len(df) < 2: return None
    close=df["Close"].astype(float); high=df["High"].astype(float); low=df["Low"].astype(float)
    son=float(close.iloc[-1]); gun=float(close.iloc[-1]/close.iloc[-2]-1)*100
    n=min(20,len(df)); avg20=float(close.iloc[-n:].mean())
    konum=(son/avg20-1)*100 if avg20>0 else None
    pc=close.shift(1); tr=pd.concat([(high-low),(high-pc).abs(),(low-pc).abs()],axis=1).max(axis=1)
    atr=float(tr.iloc[-14:].mean()) if len(tr.dropna())>=1 else None
    stop=(atr*float(vade.get("atr_stop",1.0))/son)*100 if (atr and son>0) else None
    ret=close.pct_change().dropna(); oyn="—"
    if len(ret)>=30:
        kisa=ret.iloc[-20:].std(); dag=ret.rolling(20).std().dropna()
        if len(dag)>=5 and pd.notna(kisa):
            p=float((dag<kisa).mean()); oyn="fırtına" if p>0.66 else ("sakin" if p<0.33 else "normal")
    trend=None
    if len(close)>=6:
        trend=float(close.iloc[-1]/close.iloc[-6]-1)*100  # son 5 gun
    win=close.iloc[-_NSON:]; hi_i=int(win.values.argmax()); lo_i=int(win.values.argmin())
    return dict(son=son,gun=gun,avg20=avg20,konum=konum,stop=stop,oyn=oyn,trend=trend,
                hi=float(win.iloc[hi_i]),lo=float(win.iloc[lo_i]),
                hi_t=win.index[hi_i],lo_t=win.index[lo_i],n=len(win))

def _olaylar(s):
    n=len(s); ev=[]
    if n<31: return ev
    ser=pd.Series(s); m1=ser.rolling(10).mean().values; m2=ser.rolling(30).mean().values
    for i in range(31,n):
        a,b=m1[i-1]-m2[i-1],m1[i]-m2[i]
        if not np.isnan(a) and not np.isnan(b) and a!=0 and ((a<0)!=(b<0)): ev.append((i,"kesisim",None))
    for i in range(20,n):
        w=s[i-19:i+1]
        if s[i]==w.max() and s[i-1]!=s[i-20:i].max(): ev.append((i,"zirve",None))
        if s[i]==w.min() and s[i-1]!=s[i-20:i].min(): ev.append((i,"dip",None))
    ret=np.concatenate([[0.0],np.diff(s)/s[:-1]]); std=pd.Series(ret).rolling(20).std().values
    val=std[~np.isnan(std)]
    if len(val)>=6:
        t1,t2=np.quantile(val,1/3),np.quantile(val,2/3)
        lab=lambda x: None if np.isnan(x) else (2 if x>t2 else (0 if x<t1 else 1)); prev=None
        for i in range(20,n):
            L=lab(std[i])
            if prev is not None and L is not None and L!=prev: ev.append((i,"oyn",None))
            if L is not None: prev=L
    sig=float(np.nanstd(np.diff(s)/s[:-1])) or 0.01
    for i in range(1,n):
        g=s[i]/s[i-1]-1
        if abs(g)>2.3*sig: ev.append((i,"gap",g))
    ev=[e for e in ev if e[0]>=n-40]; ev.sort(key=lambda e:e[0]); return ev[-4:]

_EMOJI={"kesisim":"◯","zirve":"△","dip":"▽","oyn":"🌀","gap":"⚡"}
def _olay_cumle(i,tip,g,dates):
    t=_etk(dates[i]) if i<len(dates) else ""
    if tip=="kesisim": return (t,"ortalama kesişimi — geçmişte ~%50 (yazı-tura), yön sinyali DEĞİL",True)
    if tip=="zirve": return (t,"son 20 günün en yükseği",False)
    if tip=="dip": return (t,"son 20 günün en düşüğü",False)
    if tip=="oyn": return (t,"oynaklık değişti",False)
    if tip=="gap": return (t,f"büyük sıçrama %{g*100:.1f}",False)
    return (t,"",False)

# ── GRAFIK: fiyat + ortalama + renkli golge + (buyukse) hacim cubuklari + olaylar ──
def _svg(s, dates, ev, vol=None, buyuk=False):
    s=np.asarray(s,float); n=len(s)
    W,H=(640,260) if buyuk else (560,86)
    pl,pr,pt,pb=(10,56,14,24) if buyuk else (4,4,5,5)
    vbh=40 if buyuk else 0                     # hacim bandi yuksekligi
    p_bot=H-pb-vbh-(6 if buyuk else 0)         # fiyat alani alt siniri
    ix=W-pl-pr; iyP=p_bot-pt
    lo,hi=float(s.min()),float(s.max()); rg=(hi-lo) or 1.0
    X=lambda i: pl+i/(n-1)*ix
    Y=lambda v: pt+(1-(v-lo)/rg)*iyP
    m=pd.Series(s).rolling(20).mean().values
    P=[]
    if buyuk:
        for v in (hi,(hi+lo)/2,lo):
            P.append(f'<line x1="{pl}" y1="{Y(v):.1f}" x2="{W-pr}" y2="{Y(v):.1f}" stroke="{PAL["cizgi"]}"/>')
            P.append(f'<text x="{W-pr+7}" y="{Y(v)+3:.1f}" fill="{PAL["soluk"]}" font-size="11" font-family="monospace">{v:.2f}</text>')
        for i in [0,n//3,2*n//3,n-1]:
            anc="start" if i==0 else ("end" if i==n-1 else "middle")
            P.append(f'<text x="{X(i):.1f}" y="{H-7}" fill="{PAL["soluk2"]}" font-size="10.5" font-family="monospace" text-anchor="{anc}">{_etk(dates[i]) if i<len(dates) else ""}</text>')
        # renkli golge (fiyat-ortalama arasi)
        i=0
        while i<n:
            if np.isnan(m[i]): i+=1; continue
            sgn=s[i]>=m[i]; j=i
            while j+1<n and not np.isnan(m[j+1]) and ((s[j+1]>=m[j+1])==sgn): j+=1
            pts=[f"{X(k):.1f},{Y(s[k]):.1f}" for k in range(i,j+1)]+[f"{X(k):.1f},{Y(m[k]):.1f}" for k in range(j,i-1,-1)]
            col="rgba(45,212,191,.22)" if sgn else "rgba(226,86,59,.22)"
            P.append(f'<polygon points="{" ".join(pts)}" fill="{col}"/>'); i=j+1
        # hacim cubuklari
        if vol is not None and len(vol)==n:
            vv=np.asarray(vol,float); vmax=float(np.nanmax(vv)) or 1.0
            bw=max(ix/n*0.62,1.0); vtop=H-pb-vbh; vbase=H-pb
            for i in range(n):
                hgt=(vv[i]/vmax)*vbh if vmax>0 else 0
                up = s[i]>=s[i-1] if i>0 else True
                vc = "rgba(45,212,191,.5)" if up else "rgba(226,86,59,.5)"
                P.append(f'<rect x="{X(i)-bw/2:.1f}" y="{vbase-hgt:.1f}" width="{bw:.1f}" height="{hgt:.1f}" fill="{vc}"/>')
            P.append(f'<text x="{pl}" y="{vtop-3:.1f}" fill="{PAL["soluk2"]}" font-size="9.5" font-family="monospace">hacim</text>')
    # ortalama
    mp=""
    for i,v in enumerate(m):
        if not np.isnan(v): mp+=f"{'L' if mp else 'M'}{X(i):.1f},{Y(v):.1f} "
    if mp: P.append(f'<path d="{mp}" fill="none" stroke="{PAL["amber"]}" stroke-width="{1.4 if buyuk else 1}" stroke-dasharray="4 3" opacity=".85"/>')
    # fiyat
    fp=" ".join(f"{'L' if i else 'M'}{X(i):.1f},{Y(v):.1f}" for i,v in enumerate(s))
    P.append(f'<path d="{fp}" fill="none" stroke="{PAL["teal"]}" stroke-width="{2.2 if buyuk else 1.6}"/>')
    if buyuk:
        for i,tip,_ in ev:
            cx,cy=X(i),Y(s[i])
            if tip=="kesisim": P.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="4.5" fill="none" stroke="{PAL["notr"]}" stroke-width="1.7"/>')
            elif tip=="zirve": P.append(f'<path d="M{cx:.1f},{cy-7:.1f} L{cx-5:.1f},{cy+2:.1f} L{cx+5:.1f},{cy+2:.1f} Z" fill="none" stroke="#C7C2B5" stroke-width="1.5"/>')
            elif tip=="dip": P.append(f'<path d="M{cx:.1f},{cy+7:.1f} L{cx-5:.1f},{cy-2:.1f} L{cx+5:.1f},{cy-2:.1f} Z" fill="none" stroke="#C7C2B5" stroke-width="1.5"/>')
            elif tip=="oyn": P.append(f'<rect x="{cx-4.5:.1f}" y="{cy-4.5:.1f}" width="9" height="9" fill="none" stroke="{PAL["amber"]}" stroke-width="1.6"/>')
            elif tip=="gap": P.append(f'<line x1="{cx:.1f}" y1="{cy-9:.1f}" x2="{cx:.1f}" y2="{cy+9:.1f}" stroke="{PAL["notr"]}" stroke-width="1.6" stroke-dasharray="2 2"/>')
    P.append(f'<circle cx="{X(n-1):.1f}" cy="{Y(s[n-1]):.1f}" r="{3.6 if buyuk else 2.6}" fill="{PAL["teal"]}"/>')
    return f'<svg viewBox="0 0 {W} {H}" preserveAspectRatio="none" style="width:100%;height:auto">{"".join(P)}</svg>'

def _trend_emoji(tr):
    if tr is None: return ("→", PAL["soluk"])
    if tr > 1.0: return ("↗", PAL["teal"])
    if tr < -1.0: return ("↘", PAL["rust"])
    return ("→", PAL["soluk"])

# ── TILE (kutu sekme) ──
def tile_html(kod, vade_key="gunluk"):
    vade=VADE_AYAR.get(vade_key,VADE_AYAR["gunluk"])
    df,_=veri_al(kod,gun=vade["gun"],min_gun=vade["min_gun"],aralik=vade["aralik"])
    m=_metrik(df,vade); C=PAL
    if m is None:
        return (f'<div style="background:{C["panel"]};border:1px solid {C["cizgi"]};border-radius:12px;padding:11px 12px">'
                f'<b style="font-family:Archivo,sans-serif;font-size:1.05rem">{kod}</b>'
                f'<div style="color:{C["soluk"]};font-size:.75rem;margin-top:5px">veri yok</div></div>')
    s=df["Close"].astype(float).values[-30:]; dates=list(df.index[-30:])
    gr=PAL["teal"] if m["gun"]>0 else (PAL["rust"] if m["gun"]<0 else PAL["soluk"])
    ga="▲" if m["gun"]>0 else ("▼" if m["gun"]<0 else "■")
    oy={"sakin":"😴","normal":"🌤️","fırtına":"🌀","—":"·"}.get(m["oyn"],"·")
    tem,trk=_trend_emoji(m["trend"])
    ust=(m["konum"] or 0)>=0
    kk=(f'<span style="color:{C["teal"] if ust else C["rust"]}">{"↑" if ust else "↓"}%{abs(m["konum"]):.1f}</span>') if m["konum"] is not None else "—"
    return (f'<div style="background:{C["panel"]};border:1px solid {C["cizgi"]};border-radius:12px;padding:11px 12px">'
            f'<div style="display:flex;justify-content:space-between;align-items:baseline">'
            f'<b style="font-family:Archivo,sans-serif;font-size:1.05rem">{kod}</b>'
            f'<span style="font-family:monospace;font-size:.9rem;color:{gr}">{ga}%{abs(m["gun"]):.1f}</span></div>'
            f'<div style="font-family:monospace;font-size:1.05rem;font-weight:600;margin-top:2px">{m["son"]:.2f}₺</div>'
            f'<div style="margin:6px 0 4px">{_svg(s,dates,[],buyuk=False)}</div>'
            f'<div style="display:flex;justify-content:space-between;align-items:center;font-family:monospace;font-size:.72rem">'
            f'<span style="color:{trk};font-size:.95rem">{tem}</span>{kk}<span title="oynaklık">{oy}</span></div></div>')

# ── DETAY (grafikten konusan, AZ yazi) ──
def detay_html(kod, vade_key="gunluk"):
    vade=VADE_AYAR.get(vade_key,VADE_AYAR["gunluk"]); C=PAL
    df,_=veri_al(kod,gun=vade["gun"],min_gun=vade["min_gun"],aralik=vade["aralik"])
    m=_metrik(df,vade)
    if m is None:
        return f'<div style="background:{C["siyah"]};color:{C["metin"]};padding:18px;border-radius:16px">{kod} · veri yok</div>'
    close=df["Close"].astype(float).values[-_NSON:]; vol=df["Volume"].astype(float).values[-_NSON:]
    dates=list(df.index[-_NSON:]); ev=_olaylar(close)
    ust=(m["konum"] or 0)>=0
    gr=C["teal"] if m["gun"]>0 else (C["rust"] if m["gun"]<0 else C["soluk"])
    gs="+" if m["gun"]>0 else ("−" if m["gun"]<0 else "")
    tem,trk=_trend_emoji(m["trend"])
    cip=lambda h:f'<span style="font-family:monospace;font-size:.74rem;color:{C["soluk"]};background:{C["panel2"]};border:1px solid {C["cizgi"]};border-radius:7px;padding:4px 9px">{h}</span>'
    seritler=" ".join([
        cip(f'bugün <b style="color:{gr}">{gs}%{abs(m["gun"]):.1f}</b>'),
        cip(f'5-gün trend <b style="color:{trk}">{tem} {("+" if (m["trend"] or 0)>=0 else "−")}%{abs(m["trend"] or 0):.1f}</b>') if m["trend"] is not None else "",
        cip(f'ortalamaya göre <b style="color:{C["teal"] if ust else C["rust"]}">{"+" if ust else "−"}%{abs(m["konum"]):.1f}</b>') if m["konum"] is not None else "",
        cip(f'oynaklık <b style="color:{C["amber"]}">{m["oyn"]}</b>'),
        cip(f'risk-stop <b>~−%{m["stop"]:.1f}</b>') if m["stop"] is not None else "",
    ])
    # kisa okuma rehberi (golge anlami) — 2 satir
    rehber=(f'<div style="display:flex;flex-wrap:wrap;gap:12px;margin-top:9px;font-size:.72rem;color:{C["soluk"]}">'
            f'<span>🟩 ortalama üstü (alıcı baskın)</span><span>🟥 ortalama altı (satıcı baskın)</span>'
            f'<span>🟡 20-gün ortalaması</span><span>▮ hacim</span></div>')
    olay_html=""
    if ev:
        sat=[]
        for i,tip,g in ev:
            t,cum,uyari=_olay_cumle(i,tip,g,dates)
            cum_html=f'<span style="color:{C["amber"]}">{cum}</span>' if uyari else cum
            sat.append(f'<span style="font-size:.74rem;color:#B7B2A6;white-space:nowrap">{_EMOJI[tip]} <span style="color:{C["soluk"]};font-family:monospace">{t}</span> {cum_html}</span>')
        olay_html=(f'<div style="margin-top:12px;display:flex;flex-wrap:wrap;gap:6px 16px">{"".join(sat)}</div>')
    # tek cumle ozet (cogunu grafik anlatiyor)
    if m["konum"] is None: oz="Ortalama hesaplanamadı."
    elif ust: oz=f'Grafikte yeşil ağırlıkta: fiyat ortalamasının <b style="color:{C["metin"]}">%{m["konum"]:.1f} üstünde</b>.'
    else: oz=f'Grafikte kırmızı ağırlıkta: fiyat ortalamasının <b style="color:{C["metin"]}">%{abs(m["konum"]):.1f} altında</b>.'
    kutu=("".join(f'<div style="background:{C["panel2"]};border:1px solid {C["cizgi"]};border-radius:9px;padding:8px 10px">'
                  f'<div style="font-size:.6rem;letter-spacing:.05em;color:{C["soluk"]};text-transform:uppercase">{ad}</div>'
                  f'<div style="font-family:monospace;font-size:.88rem;margin-top:2px">{deg}</div></div>'
                  for ad,deg in [("Son",f'{m["son"]:.2f}₺'),("20-gün ort.",f'{m["avg20"]:.2f}₺'),
                                 (f'Zirve {_etk(m["hi_t"])}',f'{m["hi"]:.2f}₺'),(f'Dip {_etk(m["lo_t"])}',f'{m["lo"]:.2f}₺')]))
    return (f'<div style="background:{C["siyah"]};color:{C["metin"]};font-family:\'Hanken Grotesk\',sans-serif;padding:18px 16px;border-radius:16px">'
            f'<div style="display:flex;align-items:baseline;justify-content:space-between;gap:10px">'
            f'<span style="font-family:Archivo,sans-serif;font-weight:800;font-size:1.55rem">{kod}</span>'
            f'<span style="font-family:monospace;font-size:1.3rem;font-weight:600">{m["son"]:.2f}₺</span></div>'
            f'<div style="display:flex;flex-wrap:wrap;gap:6px;margin:11px 0">{seritler}</div>'
            f'{_svg(close,dates,ev,vol=vol,buyuk=True)}{rehber}{olay_html}'
            f'<div style="font-size:.86rem;line-height:1.55;color:#D2CDC0;margin-top:12px">{oz}</div>'
            f'<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(110px,1fr));gap:8px;margin-top:10px">{kutu}</div>'
            f'<div style="margin-top:12px;font-size:.7rem;color:{C["soluk"]}">Sinyal yok · hedef/getiri yok · «yükselir/beklenir» yok. Karar senin.</div></div>')

# geriye uyum
def overview_html(kodlar=None, vade_key="gunluk"):
    kodlar=kodlar or IZLEME
    return ('<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px">'
            + "".join(tile_html(k,vade_key) for k in kodlar) + "</div>")
