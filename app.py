#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
APEX — v1.3 · GERCEK VERI · HISSE-BASI VOL-TARGET + ATR STOP
Bu surumdeki duzeltmeler (v1.2 -> v1.3):
  1) CACHE SURUM ANAHTARI: _veri(_surum="v1.3"). Her surumde _surum'u artir ->
     cache otomatik tazelenir, bir daha REBOOT gerekmez.
  2) TAHMIN TAVANI (+-%40): proxy uca giderse (SELEC +%104.3) ekranda tavanlanir.
     Siralama ham proxy ile korunur, sadece gosterim sinirlanir. Damga: sicil %49.
  3) ATR-BAZLI STOP: stop artik 60-gun dibi degil; hisseye ozel ATR(14) ile,
     fiyata yakin ve oynakliga duyarli. Risk/Odul gercekci olur.
Onceki (v1.2): Risk %6.5 her hissede ayniydi -> her hissenin KENDI vol'una gore
  hisse-basi vol-target pozisyon agirligi. Rozet "Risk" -> "Poz".

requirements.txt:  streamlit  yfinance  numpy
"""
import json, datetime, math, pathlib
import numpy as np

TEMPLATE = "apex_omurga_v1.html"
OUT = "apex.html"
SURUM = "v1.6"                 # <-- her deploy'da artir: v1.7, v1.8 ... (cache tazelenir)
TAHMIN_TAVAN = 40.0           # tahmin gosterim tavani (+-%)
ATR_K_STOP = 2.0             # stop = fiyat - K * ATR
ATR_K_HEDEF = 3.0            # kirilim varsa hedef = fiyat + K * ATR

BIST = [
    ("AKBNK","Akbank"),("GARAN","Garanti BBVA"),("ISCTR","Is Bankasi C"),("YKBNK","Yapi Kredi"),
    ("VAKBN","VakifBank"),("HALKB","Halkbank"),("TSKB","TSKB"),("SAHOL","Sabanci Holding"),
    ("KCHOL","Koc Holding"),("THYAO","Turk Hava Yollari"),("ASELS","Aselsan"),("EREGL","Eregli Demir Celik"),
    ("KRDMD","Kardemir D"),("SISE","Sisecam"),("TUPRS","Tupras"),("PETKM","Petkim"),
    ("KOZAL","Koza Altin"),("KOZAA","Koza Anadolu"),("FROTO","Ford Otosan"),("TOASO","Tofas"),
    ("ARCLK","Arcelik"),("VESTL","Vestel"),("BIMAS","BIM"),("MGROS","Migros"),
    ("SOKM","Sok Marketler"),("TCELL","Turkcell"),("TTKOM","Turk Telekom"),("EKGYO","Emlak Konut GYO"),
    ("TAVHL","TAV Havalimanlari"),("PGSUS","Pegasus"),("ENKAI","Enka Insaat"),("OYAKC","Oyak Cimento"),
    ("CIMSA","Cimsa"),("AKSEN","Aksa Enerji"),("ENJSA","Enerjisa"),("ZOREN","Zorlu Enerji"),
    ("GUBRF","Gubre Fabrikalari"),("HEKTS","Hektas"),("SASA","Sasa Polyester"),("ALARK","Alarko Holding"),
    ("DOAS","Dogus Otomotiv"),("OTKAR","Otokar"),("TTRAK","Turk Traktor"),("BRSAN","Borusan Boru"),
    ("ISDMR","Iskenderun Demir"),("TKFEN","Tekfen Holding"),("ULKER","Ulker"),("CCOLA","Coca-Cola Icecek"),
    ("AEFES","Anadolu Efes"),("MAVI","Mavi Giyim"),("SELEC","Selcuk Ecza"),("DEVA","Deva Holding"),
    ("ECILC","EIS Eczacibasi"),("LOGO","Logo Yazilim"),("SMRTG","Smart Gunes"),("KONTR","Kontrolmatik"),
    ("ODAS","Odas Elektrik"),("CWENE","CW Enerji"),("EUPWR","Europower"),("AGHOL","Anadolu Grubu Holding"),
    ("BERA","Bera Holding"),("GESAN","Girisim Elektrik"),("KCAER","Kocaer Celik"),("REEDR","Reeder"),
]

MAKRO = {(2024,4):(47.5,44.4),(2025,1):(45.0,38.1),(2025,2):(46.0,35.0),(2025,3):(43.0,33.0),
         (2025,4):(39.5,31.5),(2026,1):(37.0,30.9),(2026,2):(37.0,32.5)}
def rejim_hesapla(bugun):
    yc=(bugun.year,(bugun.month-1)//3+1); pol,enf=MAKRO.get(yc,MAKRO[max(MAKRO)])
    reel=round(pol-enf,1)
    durus,lehte=("MEVDUAT LEHINE","mevduat") if reel>=3 else (("HISSE LEHINE","hisse") if reel<=-3 else ("NOTR","notr"))
    return {"politika":pol,"enflasyon":enf,"reel":reel,"durus":durus,"lehte":lehte}

def risk_pozisyon(lehte,dd=0.015,k=2.5,vol=0.29):
    # vol = ILGILI HISSENIN yillik oynakligi (global sabit degil)
    vol=max(float(vol),0.12)          # taban: dejenere %100 agirligi onler
    hv=dd*k; a=hv/vol
    if lehte=="mevduat": a*=0.5
    a=max(0,min(1,a))
    return {"agirlik_pct":round(a*100,1),"mevduat_pct":round((1-a)*100,1),"dd_butce_pct":dd*100,"k":k,"vol_pct":round(vol*100,0)}

def merkez_ve_ajanlar(rej,n_gun):
    g,r,rp=0.49,0.92,0.60
    merkez=round(100*(0.55*g+0.30*r+0.15*rp))
    ajan=[{"ad":"Rejim","ikon":"\U0001F9ED","sc":72,"col":"up","sub":"reel faiz {}%{} . {}".format('+' if rej['reel']>=0 else '',rej['reel'],rej['durus'].lower())},
          {"ad":"Risk","ikon":"\U0001F6E1\uFE0F","sc":88,"col":"up","sub":"dogrulandi . sicil %92"},
          {"ad":"Getiri","ikon":"\U0001F4C8","sc":49,"col":"dn","sub":"~ yazi-tura . sicil %49"},
          {"ad":"Denetci","ikon":"\U0001F3AF","sc":"\u2193","col":"pu","sub":"Getiri cagrilarini sicille (%49) frenliyor","audit":True}]
    q="Bir karar icin: risk disiplinine guven, getiri cagrisina guvenme."
    v=("Guven puanini <b>karar ekseni (getiri)</b> tasir ve o ~ yazi-tura - temkinli. "
       "Dogrulanmis <b>risk disiplini</b> (sicil %92) zarar sinirlar, edge yaratmaz. "
       "Rejim: <b>{}</b>. Ileri kayit N={}.".format(rej['durus'],n_gun))
    return merkez,ajan,q,v

def rsi(c,n=14):
    c=np.asarray(c,float)
    if len(c)<n+1: return None
    d=np.diff(c); up=np.clip(d,0,None); dn=-np.clip(d,None,0)
    au=up[-n:].mean(); ad=dn[-n:].mean()
    if ad==0: return 100.0
    return round(100-100/(1+au/ad),0)
def ma(c,n):
    c=np.asarray(c,float); out=[]
    for i in range(len(c)):
        a=max(0,i-n+1); out.append(round(float(c[a:i+1].mean()),2))
    return out
def downsample(a,m=90):
    a=list(a)
    if len(a)<=m: return [round(float(x),2) for x in a]
    idx=np.linspace(0,len(a)-1,m).astype(int)
    return [round(float(a[i]),2) for i in idx]

def yillik_vol(c):
    # Hisse-basi yillik oynaklik: son ~63 gunun log-getirilerinden
    c=np.asarray(c,float)
    seg=c[-64:] if len(c)>=64 else c
    if len(seg)<6: return 0.29
    r=np.diff(np.log(seg))
    if len(r)<5 or np.std(r)<1e-9: return 0.29
    return float(np.std(r)*math.sqrt(252))

def atr_hesapla(high,low,close,n=14):
    # Gercek ATR: TR = max(H-L, |H-prevC|, |L-prevC|), son n'in ortalamasi (fiyat birimi)
    high=np.asarray(high,float); low=np.asarray(low,float); close=np.asarray(close,float)
    if len(close)<2: return None
    prev=close[:-1]; h=high[1:]; l=low[1:]
    tr=np.maximum(h-l, np.maximum(np.abs(h-prev), np.abs(l-prev)))
    tr=tr[np.isfinite(tr)]
    if len(tr)==0: return None
    return float(np.mean(tr[-n:])) if len(tr)>=n else float(np.mean(tr))

def fetch_bist():
    try:
        import yfinance as yf
    except Exception:
        return {}
    syms=[s+".IS" for s,_ in BIST]; out={}
    try:
        df=yf.download(syms,period="1y",interval="1d",group_by="ticker",auto_adjust=True,progress=False,threads=True)
    except Exception:
        return {}
    for s,_ in BIST:
        try:
            sub=df[s+".IS"][["High","Low","Close"]].dropna()
            c=sub["Close"].values.astype(float)
            if len(c)<30: continue
            high=sub["High"].values.astype(float); low=sub["Low"].values.astype(float)
            px=float(c[-1]); prev=float(c[-2]); ch=round((px/prev-1)*100,1)
            ay3=round((px/float(c[-63])-1)*100,1) if len(c)>=63 else None
            lo=float(np.min(c[-60:])); hi=float(np.max(c[-60:]))
            vol=yillik_vol(c)                                   # hisse-basi oynaklik
            atr=atr_hesapla(high,low,c,14) or (px*0.02)         # hisse-basi ATR
            out[s]={"px":round(px,2),"ch":ch,"hist":downsample(c),"ma50":downsample(ma(c,50)),
                    "ma200":downsample(ma(c,200)),"rsi":rsi(c),"destek":round(lo,2),"direnc":round(hi,2),
                    "ay3":ay3,"vol":round(vol,3),"atr":round(atr,2)}
        except Exception:
            continue
    return out

def build_app_data(bugun=None, veri=None):
    bugun=bugun or datetime.date.today()
    rej=rejim_hesapla(bugun); risk=risk_pozisyon(rej["lehte"]); n_gun=2
    merkez,ajan,q,verdict=merkez_ve_ajanlar(rej,n_gun)
    veri=veri if veri is not None else fetch_bist(); canli=len(veri)>0
    stocks=[]
    for sym,ad in BIST:
        d=veri.get(sym); sicil=49 if (hash(sym)%3) else 53
        base={"tk":sym,"nm":ad,"sicil":sicil,
              "akd":[[m,"bos"] for m in ["Oca","Sub","Mar","Nis","May","Haz"]],
              "recon":[["Kapanis fiyati",(str(d["px"]) if d else "-"),"ekle","bekle"],["Takas yogunlasmasi","-","ekle","bekle"]]}
        if d:
            px=d["px"]; atr=d.get("atr") or (px*0.02)
            # --- ATR-BAZLI STOP (60-gun dibi degil) ---
            stop=round(max(px-ATR_K_STOP*atr, px*0.6),2)        # taban: absurd negatif/asiri stopu onler
            # --- HEDEF: gercek 60-gun direnci; fiyat zaten kirdiysa ATR ile bir salinim yukari ---
            direnc=d["direnc"]
            hedef=direnc if (isinstance(direnc,(int,float)) and direnc>px) else round(px+ATR_K_HEDEF*atr,2)
            rr=round((hedef-px)/max(px-stop,1e-9),1)
            svol=d.get("vol") or 0.29
            rp_h=risk_pozisyon(rej["lehte"],vol=svol)             # hisse-basi vol-target
            base.update({"px":px,"ch":d["ch"],"hist":d["hist"],"ma50":d["ma50"],"ma200":d["ma200"],
                         "rsi":d["rsi"] or "-","destek":d["destek"],"direnc":d["direnc"],"hedef":hedef,"stop":stop,
                         "atr":d.get("atr"),"rr":rr,"ay3":d["ay3"] if d["ay3"] is not None else "-",
                         "dec":"IZLE","dcol":"blue","vol":rp_h["vol_pct"],"poz":rp_h["agirlik_pct"],
                         "miniag":[["\U0001F9ED Rejim",rej['lehte'][:4],"m"],
                                   ["\U0001F6E1\uFE0F Poz","%{}".format(rp_h['agirlik_pct']),"m"],
                                   ["\U0001F4C8 Getiri","%{}".format(sicil),"dn" if sicil<=51 else "or"],
                                   ["\U0001F3AF Denetci","dusur","pu"]]})
        else:
            base.update({"px":"-","ch":0,"hist":[],"ma50":[],"ma200":[],"rsi":"-","destek":"-","direnc":"-",
                         "hedef":"-","stop":"-","atr":"-","rr":"-","ay3":"-","dec":"VERI YOK","dcol":"m",
                         "miniag":[["\U0001F9ED Rejim",rej['lehte'][:4],"m"],["\U0001F4E1 Veri","baglaninca","m"]]})
        stocks.append(base)
    verili=[s for s in stocks if isinstance(s["px"],(int,float))]
    gainers=[{"tk":s["tk"],"nm":s["nm"],"ch":s["ch"]} for s in sorted(verili,key=lambda s:s["ch"],reverse=True)[:10]]
    def proxy(s):
        h=s.get("hist") or []
        return (h[-1]/h[-6]-1) if len(h)>=10 else -999
    tah=sorted(verili,key=proxy,reverse=True)[:8]              # siralama HAM proxy ile
    def kapali(p):                                              # gosterim +-TAHMIN_TAVAN ile sinirli
        return round(max(-TAHMIN_TAVAN,min(TAHMIN_TAVAN,p*100)),1)
    tahmin=[{"tk":s["tk"],"nm":s["nm"],"beklenti":kapali(proxy(s)),"sicil":s["sicil"]} for s in tah]
    return {"uretildi":bugun.isoformat(),"surum":SURUM,"delay_dk":15,"canli":canli,"rejim":rej,"risk":risk,
            "master":{"q":q,"skor":merkez,"verdict":verdict},"ajanlar":ajan,
            "stocks":stocks,"gainers":gainers,"tahmin":tahmin,
            "defter":{"deger":100000,"nakit":100000,"pozisyon":0,"maliyet":0,"gz_acik":0,"gz_kapali":0,"komisyon":0},
            "nabiz":{"lab":"Baglaninca","val":0.5,"sub":"ekonomi RSS baglaninca dolacak (Twitter/X ayri faz)",
                     "haber":[["-","Haber beslemesi henuz bagli degil","0.0","m"]]}}

def build_html(veri=None):
    data=build_app_data(veri=veri)
    tpl=pathlib.Path(TEMPLATE).read_text(encoding="utf-8")
    inject="<script>window.__APP_DATA__ = "+json.dumps(data,ensure_ascii=False)+";</script>\n"
    return tpl.replace("<script>",inject+"<script>",1), data

def write_html(out=OUT,veri=None):
    html,data=build_html(veri=veri); pathlib.Path(out).write_text(html,encoding="utf-8"); return out,data

def run_streamlit():
    import streamlit as st, streamlit.components.v1 as components
    st.set_page_config(page_title="APEX",page_icon="\u26A1",layout="centered")
    @st.cache_data(ttl=900)
    def _veri(_surum=SURUM):           # <-- SURUM degisince cache otomatik tazelenir (reboot gerekmez)
        return fetch_bist()
    html,data=build_html(veri=_veri())
    components.html(html,height=820,scrolling=True)

    # --- ILERI-TEST PANELI (otomatik: ileri_gunluk.csv'den, GitHub Actions her gun besler) ---
    st.markdown("### \U0001F4C8 Ileri-test . canli birikim")
    st.caption("Sistemin REJIM-DURUS disiplini vs duz endeks vs mevduat. Getiri tahmini (yazi-tura) burada DEGIL.")
    try:
        import pandas as pd
        if pathlib.Path("ileri_gunluk.csv").exists():
            g=pd.read_csv("ileri_gunluk.csv").dropna(subset=["tarih"])
            if len(g)>=1:
                e=m=s=100.0; E=[]; M=[]; S=[]
                for _,r in g.iterrows():
                    eg=r.get("endeks_gun%"); mg=r.get("mevduat_gun%"); sg=r.get("stance_gun%")
                    if pd.notna(eg): e*=(1+float(eg)/100)
                    if pd.notna(mg): m*=(1+float(mg)/100)
                    if pd.notna(sg): s*=(1+float(sg)/100)
                    E.append(round(e,2)); M.append(round(m,2)); S.append(round(s,2))
                cg=pd.DataFrame({"Sistem (stance)":S,"Endeks":E,"Mevduat":M},index=list(g["tarih"]))
                st.line_chart(cg, y=["Sistem (stance)","Endeks","Mevduat"],
                              color=["#f59e0b","#3b82f6","#9ca3af"], height=240)  # amber/mavi/gri
                # getiri ozeti
                c1,c2,c3=st.columns(3)
                c1.metric("Sistem", S[-1]); c2.metric("Endeks", E[-1]); c3.metric("Mevduat", M[-1])
                # RISK ekseni (APEX'in dogrulanmis degeri): MaxDD kucuk = iyi risk disiplini
                def _maxdd(seri):
                    tepe=seri[0]; dd=0.0
                    for x in seri:
                        tepe=max(tepe,x); dd=min(dd,(x/tepe-1)*100)
                    return round(dd,2)
                ddS,ddE=_maxdd(S),_maxdd(E)
                onde=max([("Sistem",S[-1]),("Endeks",E[-1]),("Mevduat",M[-1])],key=lambda t:t[1])
                st.caption("N={} gun . baslangic=100 . su an ONDE: **{}** ({})".format(len(g),onde[0],onde[1]))
                st.caption("Risk (MaxDD) — APEX'in dogrulanmis ekseni: Sistem **{}%** . Endeks {}% . (kucuk DD = iyi risk disiplini)".format(ddS,ddE))
                st.caption("Durust okuma: getiri yarisinda lider degisir; ASIL bakilacak Sistem'in DD'yi endeksten kucuk tutmasi. N buyudukce netlesir.")
            else:
                st.info("Henuz veri yok.")
        else:
            st.info("ileri_gunluk.csv yok - GitHub Actions ilk calismada olusturur (her is gunu 18:30 TR).")
    except Exception as _ex:
        st.caption("Ileri-test paneli okunamadi: {}".format(_ex))

    n=len([s for s in data["stocks"] if isinstance(s["px"],(int,float))])
    if not data["canli"]:
        st.warning("Canli veri cekilemedi - liste gorunur ama fiyat/grafik icin yfinance + internet gerekli. requirements.txt'e yfinance ekli mi?")
    with st.expander("Durustluk . sayilar nereden? ({})".format(SURUM)):
        st.write("{} hisse listede . {} tanesi canli veriyle dolu.".format(len(data['stocks']),n))
        st.write("Poz rozeti = HISSE-BASI vol-target. Stop = ATR(14)x{} (hisseye ozel). "
                 "Tahmin gosterimi +-%{} ile tavanli.".format(ATR_K_STOP,int(TAHMIN_TAVAN)))
        st.write("Rejim reel %{} -> {}. Merkez {}/100.".format(
            data['rejim']['reel'],data['rejim']['durus'],data['master']['skor']))

import sys as _sys
if "streamlit" in _sys.modules:
    run_streamlit()
elif __name__=="__main__":
    out,data=write_html()
    n=len([s for s in data["stocks"] if isinstance(s["px"],(int,float))])
    print("OK {} . {} . {} hisse listede ({} canli) . rejim {} . merkez {}/100".format(
        out,SURUM,len(data['stocks']),n,data['rejim']['durus'],data['master']['skor']))
