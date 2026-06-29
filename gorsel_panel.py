# -*- coding: utf-8 -*-
"""
gorsel_panel.py — APEX gercek-veri gorsel ozet (koyu tema, SVG).

YAPI: (1) overview_html -> taranabilir kart izgarasi (yuzde/emoji/isaret),
      (2) detay_html -> tek hisse tam detay (renkli golgeli grafik + sade okuma + metrikler + olaylar).

FELSEFE: Sinyal/hedef/yon tahmini YOK. Veri yoksa "—".
Renkli golge "grafik okuma"ya yardim eder ama OLANI anlatir, gelecegi degil.
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

# ── METRIK (sade: 20-gun basit ortalama) ──
def _metrik(df, vade):
    if df is None or len(df) < 2: return None
    close = df["Close"].astype(float); high = df["High"].astype(float)
    low = df["Low"].astype(float)
    son = float(close.iloc[-1]); gun = float(close.iloc[-1]/close.iloc[-2]-1)*100
    n = min(20, len(df)); avg20 = float(close.iloc[-n:].mean())
    konum = (son/avg20-1)*100 if avg20 > 0 else None
    pc = close.shift(1)
    tr = pd.concat([(high-low),(high-pc).abs(),(low-pc).abs()],axis=1).max(axis=1)
    atr = float(tr.iloc[-14:].mean()) if len(tr.dropna()) >= 1 else None
    stop = (atr*float(vade.get("atr_stop",1.0))/son)*100 if (atr and son>0) else None
    ret = close.pct_change().dropna(); oyn = "—"
    if len(ret) >= 30:
        kisa = ret.iloc[-20:].std(); dag = ret.rolling(20).std().dropna()
        if len(dag) >= 5 and pd.notna(kisa):
            p = float((dag < kisa).mean())
            oyn = "fırtına" if p>0.66 else ("sakin" if p<0.33 else "normal")
    win = close.iloc[-_NSON:]
    hi_i = int(win.values.argmax()); lo_i = int(win.values.argmin())
    return dict(son=son, gun=gun, avg20=avg20, konum=konum, stop=stop, oyn=oyn,
                hi=float(win.iloc[hi_i]), lo=float(win.iloc[lo_i]),
                hi_t=win.index[hi_i], lo_t=win.index[lo_i], n=len(win))

# ── OLAYLAR ──
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
    ev=[e for e in ev if e[0]>=n-40]; ev.sort(key=lambda e:e[0])
    return ev[-4:]

_EMOJI={"kesisim":"◯","zirve":"△","dip":"▽","oyn":"🌀","gap":"⚡"}
def _olay_cumle(i,tip,g,dates):
    t=_etk(dates[i]) if i<len(dates) else ""
    if tip=="kesisim": return (t,"kısa ve uzun ortalama kesişti — geçmişte ~%50 isabet (yazı-tura), yön sinyali DEĞİL",True)
    if tip=="zirve": return (t,"son 20 günün en yüksek fiyatı görüldü",False)
    if tip=="dip": return (t,"son 20 günün en düşük fiyatı görüldü",False)
    if tip=="oyn": return (t,"iniş-çıkış sertliği değişti (sakin↔sert)",False)
    if tip=="gap": return (t,f"bir günde büyük sıçrama: %{g*100:.1f}",False)
    return (t,"",False)

# ── GRAFIK (renkli golgeli: ort. ustu yesil / alti kirmizi) ──
def _svg(s, dates, ev, buyuk=False):
    s=np.asarray(s,float); n=len(s)
    W,H = (640,240) if buyuk else (560,90)
    pl,pr,pt,pb = (10,54,14,24) if buyuk else (4,4,6,6)
    ix,iy=W-pl-pr,H-pt-pb
    lo,hi=float(s.min()),float(s.max()); rg=(hi-lo) or 1.0
    X=lambda i: pl+i/(n-1)*ix; Y=lambda v: pt+(1-(v-lo)/rg)*iy
    m=pd.Series(s).rolling(20).mean().values
    parts=[]
    # zemin grid + eksen (sadece buyuk)
    if buyuk:
        for v in (hi,(hi+lo)/2,lo):
            parts.append(f'<line x1="{pl}" y1="{Y(v):.1f}" x2="{W-pr}" y2="{Y(v):.1f}" stroke="{PAL["cizgi"]}"/>')
            parts.append(f'<text x="{W-pr+7}" y="{Y(v)+3:.1f}" fill="{PAL["soluk"]}" font-size="11" font-family="monospace">{v:.2f}</text>')
        xi=[0,n//3,2*n//3,n-1]
        for i in xi:
            anc="start" if i==0 else ("end" if i==n-1 else "middle")
            parts.append(f'<text x="{X(i):.1f}" y="{H-7}" fill="{PAL["soluk2"]}" font-size="10.5" font-family="monospace" text-anchor="{anc}">{_etk(dates[i]) if i<len(dates) else ""}</text>')
    # renkli golge: fiyat ile ortalama arasi, isarete gore
    if buyuk:
        i=0
        while i<n:
            if np.isnan(m[i]): i+=1; continue
            sgn = s[i]>=m[i]; j=i
            while j+1<n and not np.isnan(m[j+1]) and ((s[j+1]>=m[j+1])==sgn): j+=1
            pts=[f"{X(k):.1f},{Y(s[k]):.1f}" for k in range(i,j+1)]
            pts+=[f"{X(k):.1f},{Y(m[k]):.1f}" for k in range(j,i-1,-1)]
            col = "rgba(45,212,191,.22)" if sgn else "rgba(226,86,59,.22)"
            parts.append(f'<polygon points="{" ".join(pts)}" fill="{col}"/>')
            i=j+1
    # ortalama cizgi
    mp=""
    for i,v in enumerate(m):
        if not np.isnan(v): mp+=f"{'L' if mp else 'M'}{X(i):.1f},{Y(v):.1f} "
    if mp: parts.append(f'<path d="{mp}" fill="none" stroke="{PAL["amber"]}" stroke-width="{1.4 if buyuk else 1}" stroke-dasharray="4 3" opacity=".85"/>')
    # fiyat cizgi
    fp=" ".join(f"{'L' if i else 'M'}{X(i):.1f},{Y(v):.1f}" for i,v in enumerate(s))
    parts.append(f'<path d="{fp}" fill="none" stroke="{PAL["teal"]}" stroke-width="{2.2 if buyuk else 1.6}"/>')
    # olay isaretleri (buyuk)
    if buyuk:
        for i,tip,_ in ev:
            cx,cy=X(i),Y(s[i])
            if tip=="kesisim": parts.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="4.5" fill="none" stroke="{PAL["notr"]}" stroke-width="1.7"/>')
            elif tip=="zirve": parts.append(f'<path d="M{cx:.1f},{cy-7:.1f} L{cx-5:.1f},{cy+2:.1f} L{cx+5:.1f},{cy+2:.1f} Z" fill="none" stroke="#C7C2B5" stroke-width="1.5"/>')
            elif tip=="dip": parts.append(f'<path d="M{cx:.1f},{cy+7:.1f} L{cx-5:.1f},{cy-2:.1f} L{cx+5:.1f},{cy-2:.1f} Z" fill="none" stroke="#C7C2B5" stroke-width="1.5"/>')
            elif tip=="oyn": parts.append(f'<rect x="{cx-4.5:.1f}" y="{cy-4.5:.1f}" width="9" height="9" fill="none" stroke="{PAL["amber"]}" stroke-width="1.6"/>')
            elif tip=="gap": parts.append(f'<line x1="{cx:.1f}" y1="{cy-9:.1f}" x2="{cx:.1f}" y2="{cy+9:.1f}" stroke="{PAL["notr"]}" stroke-width="1.6" stroke-dasharray="2 2"/>')
    parts.append(f'<circle cx="{X(n-1):.1f}" cy="{Y(s[n-1]):.1f}" r="{3.6 if buyuk else 2.6}" fill="{PAL["teal"]}"/>')
    return f'<svg viewBox="0 0 {W} {H}" preserveAspectRatio="none" style="width:100%;height:auto">{"".join(parts)}</svg>'

# ── KART (overview) ──
def _kart(kod, vade):
    df,_=veri_al(kod,gun=vade["gun"],min_gun=vade["min_gun"],aralik=vade["aralik"])
    m=_metrik(df,vade)
    if m is None:
        return (f'<div style="background:{PAL["panel"]};border:1px solid {PAL["cizgi"]};border-radius:12px;padding:13px 14px">'
                f'<div style="font-family:Archivo,sans-serif;font-weight:800;font-size:1.05rem">{kod}</div>'
                f'<div style="color:{PAL["soluk"]};margin-top:6px;font-size:.8rem">veri yok</div></div>')
    s=df["Close"].astype(float).values[-30:]; dates=list(df.index[-30:])
    ev=_olaylar(df["Close"].astype(float).values[-_NSON:])
    ust=(m["konum"] or 0)>=0
    gun_emoji = "▲" if m["gun"]>0 else ("▼" if m["gun"]<0 else "■")
    gun_renk = PAL["teal"] if m["gun"]>0 else (PAL["rust"] if m["gun"]<0 else PAL["soluk"])
    oyn_emoji = {"sakin":"😴","normal":"🌤️","fırtına":"🌀","—":"·"}.get(m["oyn"],"·")
    konum_emoji = "↑" if ust else "↓"
    konum_renk = PAL["teal"] if ust else PAL["rust"]
    konum_txt = (f'<span style="color:{konum_renk}">{konum_emoji} ort. {"+" if ust else "−"}%{abs(m["konum"]):.1f}</span>') if m["konum"] is not None else "ort. —"
    olay_rozet = f'<span style="color:{PAL["amber"]}">⚑ {len(ev)} olay</span>' if ev else f'<span style="color:{PAL["soluk2"]}">olay yok</span>'
    return (f'<div style="background:{PAL["panel"]};border:1px solid {PAL["cizgi"]};border-radius:12px;padding:13px 14px">'
            f'<div style="display:flex;justify-content:space-between;align-items:baseline">'
            f'<span style="font-family:Archivo,sans-serif;font-weight:800;font-size:1.1rem">{kod}</span>'
            f'<span style="font-family:monospace;font-size:.95rem;color:{gun_renk}">{gun_emoji}%{abs(m["gun"]):.1f}</span></div>'
            f'<div style="font-family:monospace;font-size:1.15rem;font-weight:600;margin-top:3px">{m["son"]:.2f}₺</div>'
            f'<div style="margin:7px 0">{_svg(s,dates,[],buyuk=False)}</div>'
            f'<div style="display:flex;justify-content:space-between;font-family:monospace;font-size:.72rem">'
            f'{konum_txt}<span title="oynaklık">{oyn_emoji} {m["oyn"]}</span></div>'
            f'<div style="font-family:monospace;font-size:.7rem;margin-top:5px">{olay_rozet}</div></div>')

def overview_html(kodlar=None, vade_key="gunluk"):
    kodlar=kodlar or IZLEME
    vade=VADE_AYAR.get(vade_key,VADE_AYAR["gunluk"])
    kartlar="".join(_kart(k,vade) for k in kodlar)
    return (f'<div style="background:{PAL["siyah"]};padding:14px 12px;border-radius:16px">'
            f'<div style="font-family:\'Hanken Grotesk\',sans-serif;color:{PAL["soluk"]};font-size:.78rem;margin-bottom:10px">'
            f'Kartları tara → ilgini çekeni aşağıdan seç, tam detayı aç. ▲▼ bugün · ↑↓ ortalamaya göre · 😴🌤️🌀 oynaklık · ⚑ olay sayısı</div>'
            f'<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px">{kartlar}</div></div>')

# ── DETAY (tek hisse, tam) ──
def detay_html(kod, vade_key="gunluk"):
    vade=VADE_AYAR.get(vade_key,VADE_AYAR["gunluk"])
    df,_=veri_al(kod,gun=vade["gun"],min_gun=vade["min_gun"],aralik=vade["aralik"])
    m=_metrik(df,vade)
    C=PAL
    if m is None:
        return f'<div style="background:{C["siyah"]};color:{C["metin"]};padding:18px;border-radius:16px">{kod} · veri yok</div>'
    s=df["Close"].astype(float).values[-_NSON:]; dates=list(df.index[-_NSON:]); ev=_olaylar(s)
    ust=(m["konum"] or 0)>=0
    gun_renk=C["teal"] if m["gun"]>0 else (C["rust"] if m["gun"]<0 else C["soluk"])
    gs="+" if m["gun"]>0 else ("−" if m["gun"]<0 else "")
    # ust seritler (sade dil)
    konum_c=C["teal"] if ust else C["rust"]
    cip=lambda h:f'<span style="font-family:monospace;font-size:.74rem;color:{C["soluk"]};background:{C["panel2"]};border:1px solid {C["cizgi"]};border-radius:7px;padding:4px 9px;display:inline-block">{h}</span>'
    seritler=" ".join([
        cip(f'bugün <b style="color:{gun_renk}">{gs}%{abs(m["gun"]):.1f}</b>'),
        cip(f'ortalamaya göre <b style="color:{konum_c}">{"+" if ust else "−"}%{abs(m["konum"]):.1f}</b>') if m["konum"] is not None else cip("ortalama —"),
        cip(f'oynaklık <b style="color:{C["amber"]}">{m["oyn"]}</b>'),
        cip(f'risk-stop <b>~−%{m["stop"]:.1f}</b>') if m["stop"] is not None else cip("stop —"),
    ])
    # grafik okuma rehberi (golgelerin anlami)
    rehber=(f'<div style="display:flex;flex-direction:column;gap:6px;margin-top:10px;font-size:.78rem;color:#B7B2A6">'
            f'<div>🟩 <b style="color:{C["metin"]}">Yeşil gölge</b>: fiyatın 20-gün ortalamasının ÜSTÜNDE kaldığı günler — o aralıkta ortalamadan pahalı işlem görmüş (alıcı baskın).</div>'
            f'<div>🟥 <b style="color:{C["metin"]}">Kırmızı gölge</b>: ortalamanın ALTINDA kaldığı günler — ortalamadan ucuz (satıcı baskın).</div>'
            f'<div>🟡 <b style="color:{C["metin"]}">Sarı kesik çizgi</b>: son 20 günün ortalaması (fiyatın "normal" çizgisi).</div>'
            f'<div>İşaretler: ◯ ortalama kesişimi · △▽ 20-gün zirve/dip · 🌀 oynaklık değişimi · ⚡ büyük sıçrama. Hepsi GEÇMİŞ olay — "yükselir/düşer" demez.</div></div>')
    # olay zaman cizelgesi
    olay_html=""
    if ev:
        sat=[]
        for i,tip,g in ev:
            t,cum,uyari=_olay_cumle(i,tip,g,dates)
            renk=C["amber"] if (tip=="oyn" or uyari) else C["notr"]
            cum_html=f'<span style="color:{C["amber"]}">{cum}</span>' if uyari else cum
            sat.append(f'<div style="display:flex;gap:9px;font-size:.8rem;color:#B7B2A6"><span style="flex:none;width:18px;color:{renk};font-family:monospace">{_EMOJI[tip]}</span>'
                       f'<span><span style="color:{C["soluk"]};font-family:monospace">{t}</span> · {cum_html}</span></div>')
        olay_html=(f'<div style="margin-top:14px;padding-top:12px;border-top:1px solid {C["cizgi"]}">'
                   f'<div style="font-size:.72rem;letter-spacing:.12em;color:{C["soluk"]};text-transform:uppercase;margin-bottom:8px">Bu dönemde ne oldu</div>'
                   f'<div style="display:flex;flex-direction:column;gap:6px">{"".join(sat)}</div></div>')
    # sade yorum
    if m["konum"] is None: yorum="Ortalama hesaplanamadı (yetersiz veri)."
    elif ust: yorum=f'Fiyat şu an 20 günlük ortalamasının <b style="color:{C["metin"]}">%{m["konum"]:.1f} üstünde</b>. Yani son günlerde ortalamadan pahalı işlem görüyor — kısa vadede alıcılar daha istekli.'
    else: yorum=f'Fiyat şu an 20 günlük ortalamasının <b style="color:{C["metin"]}">%{abs(m["konum"]):.1f} altında</b>. Yani son günlerde ortalamadan ucuz işlem görüyor — kısa vadede satıcılar daha baskın.'
    yorum+={"sakin":" Hareket sakin: günler arası iniş-çıkış az.","normal":" Hareket normal sertlikte.","fırtına":" Hareket sert: günler arası iniş-çıkış yüksek, sürprize açık.","—":""}.get(m["oyn"],"")
    if m["stop"] is not None: yorum+=f' Eğer alırsan, oynaklığına göre mantıklı zarar-kes (stop) mesafesi yaklaşık <b style="color:{C["metin"]}">−%{m["stop"]:.1f}</b> — bu bir tahmin değil, riskini ölçmen için.'
    # gercek sayilar kutusu
    kutu=(f'<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:8px;margin-top:12px">'
          + "".join(f'<div style="background:{C["panel2"]};border:1px solid {C["cizgi"]};border-radius:9px;padding:9px 11px">'
                    f'<div style="font-size:.62rem;letter-spacing:.06em;color:{C["soluk"]};text-transform:uppercase">{ad}</div>'
                    f'<div style="font-family:monospace;font-size:.92rem;margin-top:3px">{deg}</div></div>'
                    for ad,deg in [
                        ("Son fiyat",f'{m["son"]:.2f}₺'),
                        ("20-gün ort.",f'{m["avg20"]:.2f}₺'),
                        (f'En yüksek ({_etk(m["hi_t"])})',f'{m["hi"]:.2f}₺'),
                        (f'En düşük ({_etk(m["lo_t"])})',f'{m["lo"]:.2f}₺'),
                        ("Gösterilen gün",f'{m["n"]} işlem günü'),
                    ])
          + '</div>')
    return (f'<div style="background:{C["siyah"]};color:{C["metin"]};font-family:\'Hanken Grotesk\',sans-serif;padding:18px 16px;border-radius:16px">'
            f'<div style="display:flex;align-items:baseline;justify-content:space-between;gap:10px">'
            f'<span style="font-family:Archivo,sans-serif;font-weight:800;font-size:1.5rem;letter-spacing:.02em">{kod}</span>'
            f'<span style="font-family:monospace;font-size:1.25rem;font-weight:600">{m["son"]:.2f}₺</span></div>'
            f'<div style="display:flex;flex-wrap:wrap;gap:7px;margin:12px 0">{seritler}</div>'
            f'{_svg(s,dates,ev,buyuk=True)}'
            f'{rehber}{olay_html}'
            f'<div style="font-size:.9rem;line-height:1.65;color:#D2CDC0;margin-top:14px;padding-top:12px;border-top:1px solid {C["cizgi"]}">{yorum}</div>'
            f'{kutu}'
            f'<div style="margin-top:14px;font-size:.72rem;color:{C["soluk"]};line-height:1.5">Sinyal yok · hedef/getiri yok · «yükselir/beklenir» yok. Karar senin. Yatırım tavsiyesi değildir.</div>'
            f'</div>')
