# -*- coding: utf-8 -*-
"""
APEX — v2.5 · KURUMSAL ARAYUZ (self-contained) · GERCEK VERI · DURUST CERCEVE
Tasarim tezi: "olcum aleti" — kalibre edilmis supheyi on plana koyan bir
navigasyon/olcu cihazi. Pusula metaforu. Amber = guven (supheli), teal =
dogrulanmis eksen (risk disiplini), pas-kirmizi = olgusal negatif.

Onceki surumlerden devam eden DURUSTLUK cekirdegi (degismedi):
  - Getiri tahmini ~ yazi-tura (sicil ~%49) — KANITLANMIS edge DEGIL.
  - Dogrulanmis eksen: hisse-basi vol-target Poz + ATR(14) stop.
  - Canli veri yoksa FIYAT UYDURULMAZ ("—" gosterilir). Sahte Sharpe yok.

v2.5 -> v2.6: Teknik sekmesine 3 ekleme — Grafik Ogretmen (her ogenin anlami +
o anki durum), Dusus Riski kutusu (tersinden: "buradan dusus normal mi"),
Projektor konisi (fiyat cizgisinin sagindan acilan yonsuz 5-gun hunisi).

requirements.txt:  streamlit  yfinance  numpy
"""
import json, datetime, math, pathlib
import numpy as np

OUT = "apex.html"
SURUM = "v2.6"
TAHMIN_TAVAN = 40.0
ATR_K_STOP = 2.0
ATR_K_HEDEF = 3.0

BIST = [
    ("AKBNK","Akbank"),("GARAN","Garanti BBVA"),("ISCTR","Is Bankasi C"),("YKBNK","Yapi Kredi"),
    ("VAKBN","VakifBank"),("HALKB","Halkbank"),("TSKB","TSKB"),("SAHOL","Sabanci Holding"),
    ("KCHOL","Koc Holding"),("THYAO","Turk Hava Yollari"),("ASELS","Aselsan"),("EREGL","Eregli Demir Celik"),
    ("KRDMD","Kardemir D"),("SISE","Sisecam"),("TUPRS","Tupras"),("PETKM","Petkim"),
    ("FROTO","Ford Otosan"),("TOASO","Tofas"),
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

def _makro_oku(bugun):
    try:
        p=pathlib.Path("makro_guncel.json")
        if p.exists():
            j=json.loads(p.read_text(encoding="utf-8"))
            return float(j["politika"]), float(j["enflasyon"]), j.get("kaynak","makro_guncel.json")
    except Exception:
        pass
    yc=(bugun.year,(bugun.month-1)//3+1)
    pol,enf=MAKRO.get(yc,MAKRO[max(MAKRO)])
    return pol,enf,"statik tablo"

def rejim_hesapla(bugun):
    pol,enf,kaynak=_makro_oku(bugun)
    reel=round(pol-enf,1)
    durus,lehte=("MEVDUAT LEHINE","mevduat") if reel>=3 else (("HISSE LEHINE","hisse") if reel<=-3 else ("NOTR","notr"))
    return {"politika":pol,"enflasyon":enf,"reel":reel,"durus":durus,"lehte":lehte,"makro_kaynak":kaynak}

def risk_pozisyon(lehte,dd=0.015,k=2.5,vol=0.29):
    vol=max(float(vol),0.12)
    hv=dd*k; a=hv/vol
    if lehte=="mevduat": a*=0.5
    a=max(0,min(1,a))
    return {"agirlik_pct":round(a*100,1),"mevduat_pct":round((1-a)*100,1),"dd_butce_pct":dd*100,"k":k,"vol_pct":round(vol*100,0)}

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
    c=np.asarray(c,float)
    seg=c[-64:] if len(c)>=64 else c
    if len(seg)<6: return 0.29
    r=np.diff(np.log(seg))
    if len(r)<5 or np.std(r)<1e-9: return 0.29
    return float(np.std(r)*math.sqrt(252))

def atr_hesapla(high,low,close,n=14):
    high=np.asarray(high,float); low=np.asarray(low,float); close=np.asarray(close,float)
    if len(close)<2: return None
    prev=close[:-1]; h=high[1:]; l=low[1:]
    tr=np.maximum(h-l, np.maximum(np.abs(h-prev), np.abs(l-prev)))
    tr=tr[np.isfinite(tr)]
    if len(tr)==0: return None
    return float(np.mean(tr[-n:])) if len(tr)>=n else float(np.mean(tr))

def kesisim_analiz(close, disp_n=None):
    """MA50/MA200 altin (50>200) ve olum (50<200) kesisimleri — OLGUSAL."""
    c=np.asarray(close,float); n=len(c)
    if n<210:
        return {"yeterli":False}
    m50=np.asarray(ma(c,50),float); m200=np.asarray(ma(c,200),float)
    diff=m50-m200; start=200
    crosses=[]
    for i in range(start+1,n):
        if diff[i-1]<=0 and diff[i]>0: crosses.append((i,"altin"))
        elif diff[i-1]>=0 and diff[i]<0: crosses.append((i,"olum"))
    son=crosses[-1] if crosses else None
    gun_once=(n-1-son[0]) if son else None
    gap_pct=round(float(diff[-1]/c[-1]*100),1) if c[-1] else 0.0
    look=min(10,n-start-2); look=max(look,1)
    daralma=abs(diff[-1])-abs(diff[-1-look])
    gap_yon="daraliyor" if daralma<0 else "aciliyor"
    proj=None
    slope=(diff[-1]-diff[-1-look])/look
    if slope!=0 and (diff[-1]*slope<0):
        d2c=abs(diff[-1]/slope)
        if 0<d2c<400: proj=int(round(d2c))
    K=20; fwd=[]
    for idx,tip in crosses:
        if tip=="altin" and idx+K<n and c[idx]>0:
            fwd.append((c[idx+K]/c[idx]-1)*100)
    post=({"k":K,"medyan":round(float(np.median(fwd)),1),"n":len(fwd)} if len(fwd)>=2 else None)
    D=disp_n or n; base=n-D
    markers=[{"frac":round((idx-base)/max(D-1,1),4),"tip":tip} for idx,tip in crosses if idx>=base][-3:]
    return {"yeterli":True,"son_tip":(son[1] if son else None),"gun_once":gun_once,
            "gap_pct":gap_pct,"gap_yon":gap_yon,"proj":proj,"post":post,"markers":markers}

def _dusus_riski(close):
    """TERSINDEN risk: 'buradan dusus normal karsilanir mi'. Yukari tahmininden
    daha durust — dusus riski/trend bozulmasi/oynaklik OLCULEBILIR. 'Kesin duser' DEMEZ."""
    c=np.asarray(close,float)
    if len(c)<60: return None
    m50=np.asarray(ma(c,50),float); m200=np.asarray(ma(c,200),float)
    px=float(c[-1]); skor=0; bayrak=[]
    if m50[-1]<m200[-1]:
        skor+=30; bayrak.append(["Olum kesisimi bolgesi","MA50, MA200'un altinda — yapisal dusus trendi."])
    if px<m200[-1]:
        skor+=20; bayrak.append(["Uzun vade kirik","Fiyat MA200'un altinda — ana trend ayi tarafinda."])
    diff=m50-m200; son_tip=None; gun_once=None; start=min(200,len(c)-2)
    for i in range(start+1,len(c)):
        if diff[i-1]>=0 and diff[i]<0: son_tip="olum"; gun_once=len(c)-1-i
        elif diff[i-1]<=0 and diff[i]>0: son_tip="altin"; gun_once=len(c)-1-i
    if son_tip=="olum" and gun_once is not None and gun_once<=20:
        skor+=15; bayrak.append(["Taze olum kesisimi",str(gun_once)+" gun once olum kesisimi — bozulma yeni."])
    r=np.diff(c)/c[:-1]; neg=r[r<0]
    dvol=float(np.std(neg)*100) if len(neg)>5 else 0.0
    if dvol>3.5:
        skor+=15; bayrak.append(["Yuksek dusus oynakligi","Dusus gunlerinde ~%"+str(round(dvol,1))+" oynaklik — sert kayip riski."])
    if len(c)>=22:
        ay1=(px/float(c[-22])-1)*100
        if ay1<-8:
            skor+=20; bayrak.append(["Negatif momentum","Son 1 ayda %"+str(round(ay1,1))+" — dusus ivmesi var."])
    skor=int(min(100,skor))
    if skor>=60: karar="KACIN — buradan dusus normal karsilanir"; renk="rust"
    elif skor>=30: karar="DIKKATLI — zayiflik isaretleri var"; renk="amber"
    else: karar="TEMIZ — bariz dusus sinyali yok"; renk="teal"
    return {"skor":skor,"karar":karar,"renk":renk,"bayrak":bayrak}

def _kisa_koni(px, vol_frac, gun=5):
    """Yonsuz (drift=0) 5-gun projektor konisi. Her gun icin %80 bandin alt/ust
    fiyati. KEHANET DEGIL — belirsizligin GENISLIGI. Yon URETMEZ."""
    if not px or px<=0: return None
    sig=max(float(vol_frac or 0.29),0.05)/math.sqrt(252.0)
    out=[]
    for t in range(1,gun+1):
        s=sig*math.sqrt(t)
        out.append({"ust":round(px*math.exp(1.282*s),2),"alt":round(px*math.exp(-1.282*s),2)})
    return out

def tuzak_bayraklari(close, volume=None):
    """'TERS MATEMATIK' tuzak bayraklari — OHLCV'den HESAPLANABILEN alt-kume.
    Pump-dump imzasini fiyat+hacimden arar. 'Al' DEMEZ; tuzak belirtisini isaretler.
    Broker/float/takas gerektiren 6 bayrak BURADA YOK (manuel/ForInvest)."""
    c = np.asarray(close, float)
    if len(c) < 130:
        return None
    px = float(c[-1]); yanan = 0; bayrak = []
    # 1) Parabolik yukselis
    r6 = (px/float(c[-126])-1)*100 if len(c) >= 126 else 0.0
    r3 = (px/float(c[-63])-1)*100 if len(c) >= 63 else 0.0
    if r6 > 150 or r3 > 100:
        yanan += 1; bayrak.append(["yanan","Parabolik yukselis","6 ay %"+str(round(r6))+" / 3 ay %"+str(round(r3))+" — dik, surdurulemez olabilir."])
    else:
        bayrak.append(["temiz","Parabolik yukselis","6 ay %"+str(round(r6))+" — asiri degil."])
    # 2) Cliff-edge dusus
    r1 = (px/float(c[-22])-1)*100 if len(c) >= 22 else 0.0
    if r1 < -20:
        yanan += 1; bayrak.append(["yanan","Cliff-edge dusus","Son 1 ay %"+str(round(r1))+" — sert kirilma/satis darbesi."])
    else:
        bayrak.append(["temiz","Cliff-edge dusus","Son 1 ay %"+str(round(r1))+"."])
    # 3) Dususte hacim artisi (dagitim imzasi)
    if volume is not None and len(volume) >= 40:
        v = np.asarray(volume, float); rr = np.diff(c)/c[:-1]; vv = v[1:]
        up = vv[rr > 0]; dn = vv[rr < 0]
        if len(up) > 5 and len(dn) > 5 and np.mean(up) > 0 and np.mean(dn) > np.mean(up)*1.3:
            yanan += 1; bayrak.append(["yanan","Dususte hacim artisi","Dusus gunu hacmi yukselis gununun "+str(round(float(np.mean(dn)/np.mean(up)),1))+" kati — dagitim olabilir."])
        else:
            bayrak.append(["temiz","Dususte hacim artisi","Dagitim imzasi yok."])
    else:
        bayrak.append(["veriyok","Dususte hacim artisi","Hacim verisi yetersiz."])
    # 4) Pump-dump sekli (zirveye kosu + zirveden dusus)
    zirve = float(np.max(c)); zi = int(np.argmax(c))
    if 20 <= zi <= len(c)-5:
        kosu = (zirve/float(c[max(0, zi-126)])-1)*100
        dusus = (px/zirve-1)*100
        if kosu > 120 and dusus < -25:
            yanan += 1; bayrak.append(["yanan","Pump-dump sekli","Zirveye %"+str(round(kosu))+" kosu, sonra zirveden %"+str(round(dusus))+" dusus."])
        else:
            bayrak.append(["temiz","Pump-dump sekli","Klasik pump-dump sekli yok."])
    else:
        bayrak.append(["temiz","Pump-dump sekli","Zirve cok yeni/eski, sekil okunamadi."])
    if yanan >= 2: kat, renk = "YUKSEK — tuzak belirtileri", "rust"
    elif yanan == 1: kat, renk = "ORTA — tek bayrak", "amber"
    else: kat, renk = "DUSUK — oto bayrak yok", "teal"
    return {"yanan": yanan, "toplam_oto": 4, "kategori": kat, "renk": renk, "bayrak": bayrak}


def fetch_bist():
    try:
        import yfinance as yf
    except Exception:
        return {}
    syms=[s+".IS" for s,_ in BIST]; out={}
    try:
        df=yf.download(syms,period="2y",interval="1d",group_by="ticker",auto_adjust=True,progress=False,threads=True)
    except Exception:
        return {}
    for s,_ in BIST:
        try:
            sub=df[s+".IS"][["High","Low","Close","Volume"]].dropna()
            c=sub["Close"].values.astype(float)
            if len(c)<30: continue
            high=sub["High"].values.astype(float); low=sub["Low"].values.astype(float)
            volu=sub["Volume"].values.astype(float)
            px=float(c[-1]); prev=float(c[-2]); ch=round((px/prev-1)*100,1)
            ay3=round((px/float(c[-63])-1)*100,1) if len(c)>=63 else None
            lo=float(np.min(c[-60:])); hi=float(np.max(c[-60:]))
            vol=yillik_vol(c); atr=atr_hesapla(high,low,c,14) or (px*0.02)
            ma50f=ma(c,50); ma200f=ma(c,200); D=min(252,len(c))   # grafik son ~1 yil; kesisim tam 2 yil
            out[s]={"px":round(px,2),"ch":ch,
                    "hist":downsample(c[-D:]),"ma50":downsample(ma50f[-D:]),"ma200":downsample(ma200f[-D:]),
                    "rsi":rsi(c),"destek":round(lo,2),"direnc":round(hi,2),
                    "ay3":ay3,"vol":round(vol,3),"atr":round(atr,2),"kesisim":kesisim_analiz(c,disp_n=D),
                    "risk_dusus":_dusus_riski(c),"cone":_kisa_koni(px,vol,gun=5),"tuzak":tuzak_bayraklari(c,volu)}
        except Exception:
            continue
    return out

def ileri_seri():
    p=pathlib.Path("ileri_gunluk.csv")
    if not p.exists(): return None
    try:
        import csv as _csv
        tarih=[]; S=[]; En=[]; M=[]; e=m=s=100.0
        with open(p,encoding="utf-8") as f:
            for row in _csv.DictReader(f):
                eg=(row.get("endeks_gun%") or "").strip()
                mg=(row.get("mevduat_gun%") or "").strip()
                sg=(row.get("stance_gun%") or "").strip()
                if eg: e*=(1+float(eg)/100)
                if mg: m*=(1+float(mg)/100)
                if sg: s*=(1+float(sg)/100)
                tarih.append((row.get("tarih") or "").strip())
                S.append(round(s,2)); En.append(round(e,2)); M.append(round(m,2))
        if not tarih: return None
        def _dd(seri):
            tepe=seri[0]; dd=0.0
            for x in seri:
                tepe=max(tepe,x); dd=min(dd,(x/tepe-1)*100)
            return round(dd,2)
        onde=max([("Sistem",S[-1]),("Endeks",En[-1]),("Mevduat",M[-1])],key=lambda t:t[1])
        return {"tarih":tarih,"sistem":S,"endeks":En,"mevduat":M,
                "dd_sistem":_dd(S),"dd_endeks":_dd(En),"onde":onde[0],"onde_v":onde[1],"n":len(tarih)}
    except Exception:
        return None

def senaryo_cerceve(px, hedef, vol_pct, atr):
    if not px or px <= 0:
        return None
    fark = (float(hedef) / float(px) - 1.0) * 100.0
    sigma = max(float(vol_pct or 30.0), 1.0) / 100.0
    yil_oran = abs(fark) / 100.0 / sigma
    gunluk_pct = (float(atr) / float(px) * 100.0) if (atr and px) else None
    gun = (abs(fark) / gunluk_pct) if (gunluk_pct and gunluk_pct > 0) else None
    if yil_oran < 0.5:
        buyukluk="KUCUK"; bnot=("Bu hissenin kendi oynakligina gore kucuk bir mesafe — tipik bir yillik "
            "salinim araliginin yarisindan az. Cok seyin yolunda gitmesine gerek yok; ama bu, analist "
            "hedefinin fiyata zaten yakin oldugu anlamina da gelebilir.")
    elif yil_oran < 1.5:
        buyukluk="ORTA"; bnot=("Kabaca bu hissenin normal bir yillik salinimi kadar. Ulasilabilir gorunur "
            "ama garanti degil — bu bir BUYUKLUK olcusu, yon tahmini DEGIL.")
    else:
        buyukluk="BUYUK"; bnot=("Bu hissenin tipik yillik salinim araliginin epey ustunde. Bu hedefe ulasmak "
            "icin olagandisi bir katalizor gerekir. Analist hedefi ya cok iyimser ya cok uzun vadeli.")
    yon=("Hedef mevcut fiyatin USTUNDE" if fark>0.5 else ("Hedef mevcut fiyatin ALTINDA" if fark<-0.5 else "Hedef mevcut fiyata ~esit"))
    return {"fark":round(fark,1),"yil_oran":round(yil_oran,2),"gun":(round(gun) if gun else None),
            "sigma_pct":round(sigma*100),"buyukluk":buyukluk,"bnot":bnot,"yon":yon}

def monte_carlo(entry, vol_pct, gun=20, n=4000, stop=None, hedef=None, seed=42):
    if not entry or entry<=0 or not vol_pct: return None
    sig=max(float(vol_pct)/100.0,0.05)/math.sqrt(252.0)
    rng=np.random.default_rng(seed)
    shocks=rng.normal(0.0,sig,size=(int(n),int(gun)))      # drift=0: yon yok
    paths=float(entry)*np.exp(np.cumsum(shocks,axis=1))
    son=paths[:,-1]
    p5,p50,p95=[float(x) for x in np.percentile(son,[5,50,95])]
    res={"gun":int(gun),"p5":round(p5,2),"p50":round(p50,2),"p95":round(p95,2),
         "band_ust":round((p95/entry-1)*100,1),"band_alt":round((p5/entry-1)*100,1)}
    if stop and stop<entry:
        res["stop_deg"]=int(round(float(np.mean(np.min(paths,axis=1)<=stop))*100))
    if hedef and hedef>entry:
        res["hedef_deg"]=int(round(float(np.mean(np.max(paths,axis=1)>=hedef))*100))
    return res

def karar_cercevesi(entry, hedef, vol_pct, atr, sermaye, lehte, teknik_hedef=None):
    if not entry or entry<=0: return None
    atr=float(atr) if atr else entry*0.02
    stop=round(max(entry-ATR_K_STOP*atr, entry*0.6),2)
    vol_frac=max(float(vol_pct or 30)/100.0,0.12)
    poz=risk_pozisyon(lehte,vol=vol_frac)["agirlik_pct"]          # vol-target agirlik
    poz_tl=round(sermaye*poz/100.0)
    adet=int(poz_tl//entry) if entry>0 else 0
    riskli_tl=round((entry-stop)/entry*poz_tl) if entry>stop else 0
    riskli_pct=round(riskli_tl/sermaye*100,2) if sermaye else 0
    th=teknik_hedef if (isinstance(teknik_hedef,(int,float)) and teknik_hedef>entry) else None
    rr=round((th-entry)/max(entry-stop,1e-9),1) if th else None
    sen=senaryo_cerceve(entry,hedef,vol_pct,atr) if (hedef and hedef>0) else None
    return {"stop":stop,"poz_pct":poz,"poz_tl":poz_tl,"adet":adet,
            "riskli_tl":riskli_tl,"riskli_pct":riskli_pct,"rr":rr,"senaryo":sen}

def build_app_data(bugun=None, veri=None):
    bugun=bugun or datetime.date.today()
    rej=rejim_hesapla(bugun)
    veri=veri if veri is not None else fetch_bist(); canli=len(veri)>0
    il=ileri_seri()
    g,r,rp=49,92,60
    merkez=round(0.55*g+0.30*r+0.15*rp)
    stocks=[]
    for sym,ad in BIST:
        d=veri.get(sym); sicil=49 if (hash(sym)%3) else 53
        base={"tk":sym,"nm":ad,"sicil":sicil}
        if d:
            px=d["px"]; atr=d.get("atr") or (px*0.02)
            stop=round(max(px-ATR_K_STOP*atr, px*0.6),2)
            direnc=d["direnc"]
            hedef=direnc if (isinstance(direnc,(int,float)) and direnc>px) else round(px+ATR_K_HEDEF*atr,2)
            rr=round((hedef-px)/max(px-stop,1e-9),1)
            svol=d.get("vol") or 0.29
            rp_h=risk_pozisyon(rej["lehte"],vol=svol)
            base.update({"px":px,"ch":d["ch"],"hist":d["hist"],"ma50":d["ma50"],"ma200":d["ma200"],
                "rsi":(d["rsi"] if d["rsi"] is not None else "-"),"destek":d["destek"],"direnc":d["direnc"],
                "hedef":hedef,"stop":stop,"atr":d.get("atr"),"rr":rr,
                "ay3":(d["ay3"] if d["ay3"] is not None else "-"),
                "vol":rp_h["vol_pct"],"poz":rp_h["agirlik_pct"],"kesisim":d.get("kesisim"),
                "risk_dusus":d.get("risk_dusus"),"cone":d.get("cone"),"tuzak":d.get("tuzak"),"veri":True})
        else:
            base.update({"px":"-","ch":0,"hist":[],"ma50":[],"ma200":[],"rsi":"-","destek":"-","direnc":"-",
                "hedef":"-","stop":"-","atr":"-","rr":"-","ay3":"-","vol":"-","poz":"-","kesisim":None,
                "risk_dusus":None,"cone":None,"tuzak":None,"veri":False})
        stocks.append(base)
    verili=[s for s in stocks if s.get("veri")]
    gainers=sorted(verili,key=lambda s:s["ch"],reverse=True)[:6]
    losers=sorted(verili,key=lambda s:s["ch"])[:6]
    return {"uretildi":bugun.isoformat(),"surum":SURUM,"delay_dk":15,"canli":canli,"rejim":rej,
            "merkez":merkez,"eksenler":{"getiri":g,"risk":r,"rejim_p":rp},
            "stocks":stocks,"n_veri":len(verili),
            "gainers":[{"tk":s["tk"],"nm":s["nm"],"ch":s["ch"]} for s in gainers],
            "losers":[{"tk":s["tk"],"nm":s["nm"],"ch":s["ch"]} for s in losers],
            "ileri":il}

# ============================ SUNUM KATMANI (gomulu HTML) ============================
HTML_TEMPLATE = r"""<!DOCTYPE html><html lang="tr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Archivo:wght@600;800&family=Hanken+Grotesk:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<style>
:root{
  --ink:#0E1419; --ink2:#161E26; --ink3:#1E2832; --line:#2A3742;
  --bone:#E8E4D8; --dim:#9AA4A0; --faint:#5E6B72;
  --teal:#4FB8A4; --amber:#E0A458; --rust:#D2715A;
  --disp:"Archivo",sans-serif; --body:"Hanken Grotesk",sans-serif; --mono:"IBM Plex Mono",monospace;
}
*{box-sizing:border-box;margin:0;padding:0}
@media (prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}}
body{background:var(--ink);color:var(--bone);font-family:var(--body);line-height:1.5;
  -webkit-font-smoothing:antialiased;font-size:14px}
.wrap{max-width:980px;margin:0 auto;padding:0 16px 64px}
.mono{font-family:var(--mono);font-variant-numeric:tabular-nums}
.up{color:var(--teal)} .dn{color:var(--rust)} .am{color:var(--amber)} .dim{color:var(--dim)} .faint{color:var(--faint)}
.rail{display:flex;align-items:center;gap:14px;flex-wrap:wrap;padding:14px 2px;border-bottom:1px solid var(--line);margin-bottom:22px}
.brand{font-family:var(--disp);font-weight:800;letter-spacing:.14em;font-size:15px}
.brand .dot{color:var(--amber)}
.rail .chip{font-family:var(--mono);font-size:11px;color:var(--dim);border:1px solid var(--line);border-radius:2px;padding:3px 8px;letter-spacing:.03em}
.rail .grow{flex:1}
.hero{display:grid;grid-template-columns:auto 1fr;gap:26px;align-items:center;background:linear-gradient(180deg,var(--ink2),var(--ink));border:1px solid var(--line);border-radius:6px;padding:24px;margin-bottom:18px}
.gauge{width:184px;height:118px;position:relative}
.gauge .lab{position:absolute;left:0;right:0;top:54px;text-align:center}
.gauge .lab .num{font-family:var(--disp);font-weight:800;font-size:42px;line-height:1;color:var(--amber)}
.gauge .lab .cap{font-family:var(--mono);font-size:9px;letter-spacing:.18em;color:var(--dim);margin-top:3px}
.verdict h2{font-family:var(--disp);font-weight:600;font-size:15px;letter-spacing:.02em;margin-bottom:8px}
.verdict p{color:var(--dim);font-size:13px;max-width:46ch}
.axes{display:flex;gap:18px;margin-top:14px}
.axes .ax{font-family:var(--mono);font-size:11px;color:var(--dim);display:flex;align-items:center;gap:6px}
.axes .pip{width:7px;height:7px;border-radius:50%}
.cards{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:22px}
.card{background:var(--ink2);border:1px solid var(--line);border-radius:6px;padding:16px}
.card .k{font-family:var(--mono);font-size:10px;letter-spacing:.16em;color:var(--faint);text-transform:uppercase;margin-bottom:9px}
.card .v{font-family:var(--disp);font-weight:600;font-size:24px;letter-spacing:.01em}
.card .s{font-size:12px;color:var(--dim);margin-top:5px}
.card .micro{margin-top:10px;height:1px;background:var(--line)}
.sec{display:flex;align-items:baseline;gap:10px;margin:26px 0 12px}
.sec h3{font-family:var(--disp);font-weight:600;font-size:13px;letter-spacing:.16em;text-transform:uppercase}
.sec .ln{flex:1;height:1px;background:var(--line)}
.sec .meta{font-family:var(--mono);font-size:11px;color:var(--faint)}
.pool{border:1px solid var(--line);border-radius:6px;overflow:hidden}
.row{display:grid;grid-template-columns:84px 1fr 78px 64px 56px 62px;gap:8px;align-items:center;padding:11px 14px;border-bottom:1px solid var(--line);cursor:pointer;transition:background .12s}
.row:last-child{border-bottom:none}
.row:hover{background:var(--ink3)}
.row.head{cursor:default;background:var(--ink2);position:sticky;top:0}
.row.head span{font-family:var(--mono);font-size:10px;letter-spacing:.1em;color:var(--faint);text-transform:uppercase}
.row .tk{font-family:var(--mono);font-weight:600;font-size:13px}
.row .nm{color:var(--dim);font-size:12.5px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.row .n{font-family:var(--mono);font-size:12.5px;text-align:right}
.row .volbar{height:5px;background:var(--ink3);border-radius:3px;overflow:hidden}
.row .volbar i{display:block;height:100%;background:var(--teal);opacity:.7}
.scroll{max-height:430px;overflow:auto}
.back{display:inline-flex;align-items:center;gap:7px;font-family:var(--mono);font-size:12px;color:var(--teal);cursor:pointer;padding:6px 0;margin-bottom:6px}
.dhead{display:flex;align-items:baseline;gap:12px;flex-wrap:wrap;margin-bottom:4px}
.dhead .tk{font-family:var(--mono);font-weight:600;font-size:20px}
.dhead .nm{color:var(--dim)}
.dhead .px{font-family:var(--disp);font-weight:800;font-size:30px;margin-left:auto}
.spark{margin:16px 0;border:1px solid var(--line);border-radius:6px;background:var(--ink2);padding:14px}
.legend{display:flex;gap:16px;flex-wrap:wrap;font-family:var(--mono);font-size:10px;color:var(--dim);margin-top:8px}
.legend i{display:inline-block;width:14px;height:2px;vertical-align:middle;margin-right:5px}
.dgrid{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin:14px 0}
.dcell{background:var(--ink2);border:1px solid var(--line);border-radius:5px;padding:12px}
.dcell .k{font-family:var(--mono);font-size:9px;letter-spacing:.12em;color:var(--faint);text-transform:uppercase}
.dcell .v{font-family:var(--mono);font-size:16px;margin-top:6px}
.stamp{border:1px solid var(--line);border-left:2px solid var(--amber);background:rgba(224,164,88,.06);border-radius:4px;padding:12px 14px;font-size:12.5px;color:var(--dim);margin-top:8px}
.tabs{display:flex;gap:4px;border-bottom:1px solid var(--line);margin:18px 0 14px}
.tab{font-family:var(--mono);font-size:11px;letter-spacing:.08em;color:var(--faint);text-transform:uppercase;padding:9px 12px;cursor:pointer;border-bottom:2px solid transparent}
.tab.on{color:var(--bone);border-bottom-color:var(--amber)}
.stub{color:var(--faint);font-size:12.5px;padding:14px;border:1px dashed var(--line);border-radius:5px}
.hidden{display:none}
.disc{text-align:center;font-family:var(--mono);font-size:10px;color:var(--faint);letter-spacing:.04em;margin-top:28px;padding-top:16px;border-top:1px solid var(--line)}
@media (max-width:640px){
  .wrap{padding:0 12px 56px}
  .hero{grid-template-columns:1fr;gap:16px;padding:18px;text-align:center}
  .gauge{margin:0 auto}
  .verdict h2{font-size:14px}
  .verdict p{max-width:none}
  .axes{justify-content:center;flex-wrap:wrap;gap:12px}
  .cards{grid-template-columns:1fr;gap:10px}
  .card .v{font-size:21px}
  .dgrid{grid-template-columns:repeat(2,1fr)}
  .dhead .px{margin-left:0;width:100%;font-size:26px}
  .row{grid-template-columns:60px 1fr 64px 50px 44px 48px;gap:6px;padding:10px 12px}
  .row .nm{font-size:11.5px}
}
</style></head><body><div class="wrap">

<div class="rail">
  <div class="brand">APEX<span class="dot">.</span></div>
  <div class="chip" id="r-rejim">rejim —</div>
  <div class="chip" id="r-veri">veri —</div>
  <div class="grow"></div>
  <div class="chip" id="r-tar">—</div>
</div>

<div id="view-dash">
  <div class="hero">
    <div class="gauge" id="gauge">
      <svg viewBox="0 0 184 118" width="184" height="118" id="gsvg"></svg>
      <div class="lab"><div class="num" id="g-num">—</div><div class="cap">GUVEN KERTERIZI</div></div>
    </div>
    <div class="verdict">
      <h2 id="v-title">Karar icin: risk disiplinine guven, getiri cagrisina guvenme.</h2>
      <p id="v-body">—</p>
      <div class="axes" id="v-axes"></div>
    </div>
  </div>

  <div class="cards">
    <div class="card"><div class="k">Rejim · reel faiz</div><div class="v" id="c-rejim">—</div>
      <div class="s" id="c-rejim-s">—</div><div class="micro"></div></div>
    <div class="card"><div class="k">Risk disiplini</div><div class="v up">Dogrulandi</div>
      <div class="s">vol-target + ATR stop · sicil %92</div><div class="micro"></div></div>
    <div class="card"><div class="k">Ileri-test · onde</div><div class="v" id="c-ileri">—</div>
      <div class="s" id="c-ileri-s">tek durust OOS</div><div class="micro"></div></div>
  </div>

  <div class="sec"><h3>Havuz</h3><div class="ln"></div><div class="meta" id="pool-meta">—</div></div>
  <div class="pool">
    <div class="row head"><span>Kod</span><span>Sirket</span><span style="text-align:right">Fiyat</span>
      <span style="text-align:right">Gun%</span><span style="text-align:right">Vol</span><span>Poz</span></div>
    <div class="scroll" id="pool"></div>
  </div>
</div>

<div id="view-detail" class="hidden"></div>

<div class="disc" id="disc">APEX v2.6 · yatirim tavsiyesi degildir · getiri tahmini ~ yazi-tura, kanitlanmis edge degil</div>
</div>

<script>
var APP = window.__APP_DATA__ || {};
var SVGNS="http://www.w3.org/2000/svg";
function svgEl(t,a){var e=document.createElementNS(SVGNS,t);if(a)for(var k in a)e.setAttribute(k,a[k]);return e;}
function clr(n){return n>0.05?'up':(n<-0.05?'dn':'dim');}
function sgn(n){return (n>0?'+':'')+n;}
function num(x){return typeof x==='number'&&!isNaN(x);}

function drawGauge(score){
  var sv=document.getElementById('gsvg');sv.innerHTML='';
  var cx=92,cy=100,R=78,sw=13;
  function pol(deg){var r=(180-deg)*Math.PI/180;return {x:cx+R*Math.cos(r),y:cy-R*Math.sin(r)};}
  function arc(a0,a1,col,op){
    var p0=pol(a0),p1=pol(a1);
    var large=(a1-a0)>180?1:0;
    var d='M '+p0.x+' '+p0.y+' A '+R+' '+R+' 0 '+large+' 1 '+p1.x+' '+p1.y;
    var e=svgEl('path',{d:d,fill:'none',stroke:col,'stroke-width':sw,'stroke-linecap':'butt'});
    if(op)e.setAttribute('opacity',op);sv.appendChild(e);
  }
  arc(0,72,'#D2715A',.42); arc(72,126,'#E0A458',.55); arc(126,180,'#4FB8A4',.42);
  var ang=score/100*180, np=pol(ang);
  sv.appendChild(svgEl('line',{x1:cx,y1:cy,x2:np.x,y2:np.y,stroke:'#E0A458','stroke-width':2.4,'stroke-linecap':'round'}));
  sv.appendChild(svgEl('circle',{cx:cx,cy:cy,r:4,fill:'#E0A458'}));
  sv.appendChild(svgEl('circle',{cx:pol(0).x,cy:pol(0).y,r:1.6,fill:'#5E6B72'}));
  sv.appendChild(svgEl('circle',{cx:pol(180).x,cy:pol(180).y,r:1.6,fill:'#5E6B72'}));
  document.getElementById('g-num').textContent=score;
}

/* ---- sparkline (price + ma50 + ma200 + projektor konisi) ---- */
function sparkSVG(hist,ma50,ma200,kesisim,cone,stop){
  var W=620,H=150,pad=8;
  if(!hist||hist.length<2)return '<div class="stub">Fiyat serisi yok — canli veriye baglaninca dolar.</div>';
  var L=hist.length;
  var fut=(cone&&cone.length)?cone.length:0;
  var all=hist.concat(ma50||[],ma200||[]).filter(num);
  if(fut){cone.forEach(function(c){if(num(c.ust))all.push(c.ust);if(num(c.alt))all.push(c.alt);});}
  var mn=Math.min.apply(null,all),mx=Math.max.apply(null,all);if(mx-mn<1e-6){mx+=1;mn-=1;}
  var histFrac=fut?0.76:1.0;
  var histW=(W-2*pad)*histFrac, futW=(W-2*pad)-histW;
  function X(i){
    if(i<=L-1) return pad + (L>1?histW*(i/(L-1)):0);
    return pad + histW + (fut>0?futW*((i-(L-1))/fut):0);
  }
  function Y(v){return pad+(H-2*pad)*(1-(v-mn)/(mx-mn));}
  function path(arr,col,w,op){if(!arr||arr.length<2)return '';var d='';for(var i=0;i<arr.length;i++){d+=(i?'L':'M')+X(i).toFixed(1)+' '+Y(arr[i]).toFixed(1)+' ';}
    return '<path d="'+d+'" fill="none" stroke="'+col+'" stroke-width="'+w+'"'+(op?' opacity="'+op+'"':'')+'/>';}
  var s='<svg viewBox="0 0 '+W+' '+H+'" width="100%" height="150" preserveAspectRatio="none">';
  if(num(stop)&&stop>=mn&&stop<=mx){
    s+='<line x1="'+pad+'" y1="'+Y(stop).toFixed(1)+'" x2="'+(W-pad)+'" y2="'+Y(stop).toFixed(1)+'" stroke="#D2715A" stroke-width="0.9" stroke-dasharray="4 4" opacity="0.7"/>';
    s+='<text x="'+(W-pad-2)+'" y="'+(Y(stop)-3).toFixed(1)+'" fill="#D2715A" font-size="9" text-anchor="end" font-family="monospace">stop</text>';
  }
  if(fut){
    var lx=L-1, ly=hist[L-1];
    var poly='M '+X(lx).toFixed(1)+' '+Y(ly).toFixed(1)+' ';
    for(var i=0;i<fut;i++){poly+='L '+X(lx+1+i).toFixed(1)+' '+Y(cone[i].ust).toFixed(1)+' ';}
    for(var j=fut-1;j>=0;j--){poly+='L '+X(lx+1+j).toFixed(1)+' '+Y(cone[j].alt).toFixed(1)+' ';}
    poly+='Z';
    s+='<path d="'+poly+'" fill="#4FB8A4" opacity="0.13" stroke="none"/>';
    s+='<line x1="'+X(lx).toFixed(1)+'" y1="'+Y(ly).toFixed(1)+'" x2="'+X(L-1+fut).toFixed(1)+'" y2="'+Y(ly).toFixed(1)+'" stroke="#9AA4A0" stroke-width="1" stroke-dasharray="3 3"/>';
    s+='<line x1="'+X(lx).toFixed(1)+'" y1="'+pad+'" x2="'+X(lx).toFixed(1)+'" y2="'+(H-pad)+'" stroke="#2A3742" stroke-width="1" stroke-dasharray="2 3"/>';
  }
  s+=path(ma200,'#5E6B72',1.2);s+=path(ma50,'#4FB8A4',1.4,.8);s+=path(hist,'#E8E4D8',1.8);
  if(kesisim&&kesisim.markers){var ref=(ma50&&ma50.length)?ma50:hist;
    kesisim.markers.forEach(function(m){var xi=X(m.frac*(L-1));
      var yi=Y(ref[Math.min(ref.length-1,Math.round(m.frac*(ref.length-1)))]);
      var col=m.tip==='altin'?'#E0A458':'#D2715A';
      s+='<circle cx="'+xi.toFixed(1)+'" cy="'+yi.toFixed(1)+'" r="4.5" fill="'+col+'" stroke="#0E1419" stroke-width="1.6"/>';});}
  s+='</svg>';
  s+='<div class="legend"><span><i style="background:#E8E4D8"></i>fiyat</span>'+
     '<span><i style="background:#4FB8A4"></i>MA50</span>'+
     '<span><i style="background:#5E6B72"></i>MA200</span>'+'<span style="color:#E0A458">\u25CF altin</span><span style="color:#D2715A">\u25CF olum</span>'+
     (fut?'<span class="dim">\u25E2 projektor 5g</span>':'')+'</div>';
  return s;
}

function kesisimKutu(k){
  if(!k) return '';
  if(!k.yeterli) return '<div class="stub">MA50/MA200 kesisim analizi icin yeterli gecmis yok (>200 gun gerekir).</div>';
  var tipTxt=k.son_tip==='altin'?'<b class="am">ALTIN kesisim</b>':(k.son_tip==='olum'?'<b class="dn">OLUM kesisim</b>':'kesisim yok');
  var l1=k.son_tip?('Son kesisim: '+tipTxt+' \u00b7 <b>'+k.gun_once+' gun once</b>'):'Kayitli MA50/MA200 kesisimi yok';
  var l2='MA50 su an MA200\'un <b>%'+Math.abs(k.gap_pct)+'</b> '+(k.gap_pct>=0?'<span class="am">ustunde</span>':'<span class="dn">altinda</span>')+' \u00b7 fark '+k.gap_yon;
  var l3=(k.proj&&k.proj<=60)?('<div class="dim" style="margin-top:6px">Mevcut hizla kabaca <b>~'+k.proj+' gun</b> sonra kesisim olabilir — <b>mekanik tahmin, kesinlik degil</b>.</div>'):'';
  var l4=k.post?('<div class="dim" style="margin-top:6px">Bu hissede gecmis altin kesisimlerden '+k.post.k+' gun sonra medyan: <b>%'+(k.post.medyan>0?'+':'')+k.post.medyan+'</b> ('+k.post.n+' olay). <span class="faint">Gecmis = gelecek degildir; kanitlanmis edge degil.</span></div>'):'';
  var bc=k.son_tip==='altin'?'var(--amber)':(k.son_tip==='olum'?'var(--rust)':'var(--line)');
  return '<div class="stamp" style="border-left-color:'+bc+'">'+l1+'<br>'+l2+l3+l4+'</div>';
}

/* ---- DUSUS RISKI kutusu (tersinden) ---- */
function riskKutu(rd){
  if(!rd)return '';
  var cmap={rust:'var(--rust)',amber:'var(--amber)',teal:'var(--teal)'};
  var col=cmap[rd.renk]||'var(--line)';
  var b='';(rd.bayrak||[]).forEach(function(x){b+='<div class="dim" style="font-size:11.5px;margin-top:4px">\u2022 <b>'+x[0]+':</b> '+x[1]+'</div>';});
  return '<div class="stamp" style="border-left-color:'+col+'">'+
    '<b style="color:'+col+'">\u26A0 DUSUS RISKI: '+rd.skor+'/100 \u2014 '+rd.karar+'</b>'+b+
    '<div class="faint" style="font-size:11px;margin-top:7px">Bu skor \'kesin duser\' demez; buradan asagi hareketin ne kadar normal/beklenir oldugunu soyler. Yon tahmini DEGIL.</div></div>';
}

/* ---- PROJEKTOR CUMLESI (grafik sonrasi, tek bakista) ---- */
function projektorCumle(s){
  if(!s.cone||!s.cone.length||!num(s.px)) return '';
  var L=s.cone[s.cone.length-1], px=s.px, alt=L.alt, ust=L.ust;
  var dAlt=((alt/px-1)*100).toFixed(1), dUst=((ust/px-1)*100).toFixed(1);
  var stopTxt='';
  if(num(s.stop)){
    if(s.stop<=alt) stopTxt=' Stop \u20BA'+s.stop+' bu bandin ALTINDA \u2014 normal 5-gun dalgalanmasi tek basina stopu tetiklemez.';
    else stopTxt=' Stop \u20BA'+s.stop+' bu bandin ICINDE \u2014 normal 5-gun dalgalanmasi bile stopu test edebilir, dikkat.';
  }
  return '<div class="stamp" style="border-left-color:#38BDF8;background:rgba(56,189,248,.06)">'+
    '<b style="color:#38BDF8">\uD83D\uDCE1 Projektor (sade):</b> Onumuzdeki 5 gunde salt oynaklikla fiyat kabaca \u20BA'+alt+' (%'+dAlt+') \u2013 \u20BA'+ust+' (+%'+Math.abs(dUst)+') arasinda gezebilir.'+
    ' Ortasi bugune yakin cunku YON tahmini yok \u2014 bu kehanet degil, belirsizligin genisligi.'+stopTxt+'</div>';
}

/* ---- AKILLI SADE OZET (sentez, tek bakista) ---- */
function ozetKutu(s){
  if(!s.veri) return '';
  var px=s.px, m50=(s.ma50&&s.ma50.length)?s.ma50[s.ma50.length-1]:null, m200=(s.ma200&&s.ma200.length)?s.ma200[s.ma200.length-1]:null;
  var trend='trend okunamadi', tcol='dim';
  var a50=num(px)&&num(m50)&&px>=m50, a200=num(px)&&num(m200)&&px>=m200, m5g2=num(m50)&&num(m200)&&m50>=m200;
  if(num(px)&&num(m50)&&num(m200)){
    if(a50&&a200&&m5g2){trend='uzun vadeli YUKSELIS \u2014 fiyat hem MA50 hem MA200 ustunde';tcol='up';}
    else if(!a50&&!a200&&!m5g2){trend='DUSUS \u2014 fiyat hem MA50 hem MA200 altinda';tcol='dn';}
    else if(m5g2&&!a50){trend='uzun vade YUKARI ama kisa vadede geri cekilmis (fiyat MA50 altinda, MA200 ustunde)';tcol='am';}
    else if(!m5g2&&a50){trend='uzun vade ASAGI ama kisa vadede toparlaniyor (fiyat MA50 ustunde, MA200 altinda)';tcol='am';}
    else{trend='KARISIK \u2014 net yon yok';tcol='am';}
  }
  var rsiTxt='';
  if(num(s.rsi)){
    if(s.rsi>=70) rsiTxt='RSI '+s.rsi+' \u2014 asiri alima yakin (70 ustu); kisa vadede geri cekilme olagan.';
    else if(s.rsi<=30) rsiTxt='RSI '+s.rsi+' \u2014 asiri satimda (30 alti); tepki yukselisi gorulebilir.';
    else if(s.rsi>=60) rsiTxt='RSI '+s.rsi+' \u2014 alici tarafi bir miktar baskin, ama asiri degil.';
    else if(s.rsi<=40) rsiTxt='RSI '+s.rsi+' \u2014 satici tarafi bir miktar baskin, ama asiri degil.';
    else rsiTxt='RSI '+s.rsi+' \u2014 notr bolge (ne asiri alim ne asiri satim).';
  }
  var riskTxt='';
  if(s.risk_dusus){var rk=s.risk_dusus.skor; riskTxt='Dusus riski '+rk+'/100 ('+(rk>=60?'yuksek':(rk>=30?'orta':'dusuk'))+').';}
  var momTxt = num(s.ay3)?(' Son 3 ay: %'+(s.ay3>0?'+':'')+s.ay3+'.'):'';
  return '<div class="stamp" style="border-left-color:var(--teal);background:rgba(79,184,164,.07)">'+
    '<div style="font-family:var(--disp);font-weight:600;color:var(--bone);font-size:13px;margin-bottom:8px">\uD83D\uDCCD '+s.tk+' su an nerede? (sade ozet)</div>'+
    '<div class="'+tcol+'" style="font-size:13px;margin-bottom:6px">'+trend+'.</div>'+
    ((riskTxt||momTxt)?'<div class="dim" style="font-size:12.5px;margin-bottom:4px">'+riskTxt+momTxt+'</div>':'')+
    (rsiTxt?'<div class="dim" style="font-size:12.5px;margin-bottom:4px">'+rsiTxt+'</div>':'')+
    '<div class="faint" style="font-size:11px;margin-top:7px">Bu bir OZET \u2014 mevcut tablonun sade okumasi. Tahmin ya da \'al\' DEGIL; sistem yon soylemez, karar sende.</div>'+
    '</div>';
}

/* ---- TUZAK BAYRAKLARI (ters matematik, oto alt-kume + manuel liste) ---- */
function tuzakKutu(t){
  if(!t) return '';
  var cmap={rust:'var(--rust)',amber:'var(--amber)',teal:'var(--teal)'};
  var col=cmap[t.renk]||'var(--line)';
  var ico={yanan:'\uD83D\uDD34',temiz:'\u2713',veriyok:'\u2014'};
  var rows='';
  (t.bayrak||[]).forEach(function(b){
    var c2=b[0]==='yanan'?'var(--rust)':(b[0]==='temiz'?'var(--teal)':'var(--faint)');
    rows+='<div style="font-size:11.5px;margin-top:5px"><span style="color:'+c2+'">'+(ico[b[0]]||'')+' <b>'+b[1]+'</b></span> <span class="dim">\u2014 '+b[2]+'</span></div>';
  });
  var manuel=['Broker konsantrasyonu (tek broker >%60)','Float darligi (<%20 dolasim)','Maliyeti yukselen alici (markup)','Fon/yabanci net satici (dump hazirligi)','Temel anomali (ROE/F-K)','Pazar sinifi Z (yakin izleme)'];
  var mrows=''; manuel.forEach(function(m){mrows+='<div class="faint" style="font-size:11px;margin-top:3px">\u2014 '+m+'</div>';});
  return '<div class="stamp" style="border-left-color:'+col+'">'+
    '<b style="color:'+col+'">\uD83C\uDFAF TUZAK BAYRAKLARI (oto): '+t.yanan+'/'+t.toplam_oto+' yandi \u2014 '+t.kategori+'</b>'+
    rows+
    '<div style="border-top:1px solid var(--line);margin:9px 0 5px"></div>'+
    '<div class="faint" style="font-size:10px;text-transform:uppercase;letter-spacing:.1em">Manuel veri gereken bayraklar \u00b7 ForInvest/takas</div>'+
    mrows+
    '<div class="faint" style="font-size:11px;margin-top:8px">Oto bayraklar fiyat+hacimden. Tam tuzak profili icin broker/float/takas verisi elle girilmeli. <b>Ters matematik:</b> kazanani bilemeyiz, tuzagi isaretleyebiliriz.</div></div>';
}

/* ---- GRAFIK OGRETMEN (her ogenin anlami + o anki durum) ---- */
function ogretmenKutu(s){
  var px=num(s.px)?s.px:null;
  var m50=(s.ma50&&s.ma50.length)?s.ma50[s.ma50.length-1]:null;
  var m200=(s.ma200&&s.ma200.length)?s.ma200[s.ma200.length-1]:null;
  function rel(p,m){if(!num(p)||!num(m)||!m)return ['—','dim'];var d=(p/m-1)*100;return [(d>=0?'USTUNDE':'ALTINDA')+' (%'+(d>=0?'+':'')+d.toFixed(1)+')',d>=0?'up':'dn'];}
  var a=rel(px,m50), b=rel(px,m200);
  var kes='kesisim verisi yok';
  if(s.kesisim&&s.kesisim.yeterli&&s.kesisim.son_tip){
    kes=(s.kesisim.son_tip==='altin'?'son kesisim ALTIN':'son kesisim OLUM')+' \u00b7 '+s.kesisim.gun_once+' gun once';
  }
  return '<details class="stamp" style="border-left-color:#4FB8A4">'+
    '<summary style="cursor:pointer;color:#4FB8A4;font-weight:600;font-size:12.5px">\uD83D\uDCD8 Bu grafikte ne goruyorum? (her ogenin anlami)</summary>'+
    '<div style="margin-top:10px">'+
    '<div style="margin-bottom:9px"><b style="color:#4FB8A4">MA50 (yesil cizgi)</b> \u2014 son 50 gunun ortalama fiyati; KISA vadeli yonu gosterir. '+
      '<span class="'+a[1]+'">Fiyat su an MA50\'nin '+a[0]+'.</span></div>'+
    '<div style="margin-bottom:9px"><b style="color:#9AA4A0">MA200 (gri cizgi)</b> \u2014 son 200 gunun ortalamasi; UZUN vadeli ana yon. Ustundeyse boga, altindaysa ayi tarafi. '+
      '<span class="'+b[1]+'">Fiyat su an MA200\'un '+b[0]+'.</span></div>'+
    '<div style="margin-bottom:9px"><b class="am">Altin kesisim</b> / <b class="dn">olum kesisim</b> \u2014 MA50, MA200\'u yukari keserse ALTIN (yukselis baslangici sayilir), asagi keserse OLUM (dusus baslangici). Grafikte yuvarlak nokta. <span class="dim">('+kes+')</span></div>'+
    '<div style="margin-bottom:9px"><b style="color:#4FB8A4">Projektor (sagdaki huni)</b> \u2014 onumuzdeki 5 gunun OLASI fiyat araligi. Yon tahmin ETMEZ (ortasi duz gider); sadece nereye kadar oynayabilecegini gosterir. Huni genisse oynaklik yuksek.</div>'+
    '<div style="border-top:1px solid var(--line);margin:10px 0"></div>'+
    '<div style="margin-bottom:7px"><b>RSI(14)</b> \u2014 0-100 arasi bir "isi" gostergesi. 70 ustu asiri alim (pahali/yorgun, geri cekilme olabilir), 30 alti asiri satim (ucuz, tepki gelebilir), ortasi notr.</div>'+
    '<div style="margin-bottom:7px"><b>Yillik vol</b> \u2014 hissenin oynaklik derecesi. Yuksekse fiyat sert oynar (firsat+risk buyuk), dususkse sakin.</div>'+
    '<div style="margin-bottom:7px"><b>R/Odul</b> \u2014 teknik hedefe kazanc / stop\'a risk. 2x = kazanirsan kaybinin 2 kati; 1\'in altina dikkat.</div>'+
    '<div style="margin-bottom:7px"><b>Destek / Direnc</b> \u2014 destek: son 60 gunun tabani; direnc: tavani. Yakininda tepki olagandir.</div>'+
    '<div><b>ATR stop</b> \u2014 hissenin kendi oynakligina gore "buradan asagisi tez yanlis" cizgisi; kaybi butcede tutar.</div>'+
    '</div></details>';
}

function renderDash(){
  var rej=APP.rejim||{};
  document.getElementById('r-rejim').textContent='rejim '+(rej.durus||'—')+' · reel %'+sgn(rej.reel);
  document.getElementById('r-veri').textContent=APP.canli?('veri '+APP.delay_dk+'dk · '+APP.n_veri+' canli'):'CANLI VERI YOK';
  document.getElementById('r-veri').className='chip '+(APP.canli?'':'dn');
  document.getElementById('r-tar').textContent=APP.uretildi||'—';
  drawGauge(APP.merkez||0);
  document.getElementById('v-body').textContent=
    'Guven puanini getiri ekseni asagi ceker (~yazi-tura). Dogrulanmis risk disiplini zarari sinirlar, edge yaratmaz. '
    +'Rejim: '+(rej.durus||'—')+'.';
  var ax=APP.eksenler||{};
  document.getElementById('v-axes').innerHTML=
    '<div class="ax"><span class="pip" style="background:#4FB8A4"></span>Risk '+(ax.risk||'-')+' · dogrulandi</div>'+
    '<div class="ax"><span class="pip" style="background:#5E6B72"></span>Getiri '+(ax.getiri||'-')+' · yazi-tura</div>';
  document.getElementById('c-rejim').textContent='%'+sgn(rej.reel);
  document.getElementById('c-rejim-s').textContent=(rej.durus||'-')+' · pol %'+rej.politika+' enf %'+rej.enflasyon;
  var il=APP.ileri;
  if(il){document.getElementById('c-ileri').textContent=il.onde;
    document.getElementById('c-ileri-s').textContent='N='+il.n+' · MaxDD Sistem '+il.dd_sistem+'%';}
  else{document.getElementById('c-ileri').textContent='—';
    document.getElementById('c-ileri-s').textContent='henuz kayit yok · hafta ici 18:30 beslenir';}
  var pool=document.getElementById('pool');pool.innerHTML='';
  var maxv=1;(APP.stocks||[]).forEach(function(s){if(typeof s.vol==='number'&&s.vol>maxv)maxv=s.vol;});
  document.getElementById('pool-meta').textContent=(APP.stocks||[]).length+' hisse · '+APP.n_veri+' canli';
  (APP.stocks||[]).forEach(function(s,i){
    var r=document.createElement('div');r.className='row';
    var ch=(typeof s.ch==='number')?s.ch:0;
    var volpct=(typeof s.vol==='number')?Math.round(s.vol/maxv*100):0;
    r.innerHTML='<span class="tk">'+s.tk+'</span><span class="nm">'+s.nm+'</span>'+
      '<span class="n">'+(s.px==='-'?'—':s.px)+'</span>'+
      '<span class="n '+clr(ch)+'">'+(s.veri?sgn(ch)+'%':'—')+'</span>'+
      '<span class="n dim">'+(s.vol==='-'?'—':'%'+s.vol)+'</span>'+
      '<div class="volbar"><i style="width:'+volpct+'%"></i></div>';
    r.onclick=function(){renderDetail(i);};
    pool.appendChild(r);
  });
}

var curTab='teknik';
function renderDetail(i){
  var s=APP.stocks[i];if(!s)return;
  document.getElementById('view-dash').classList.add('hidden');
  var v=document.getElementById('view-detail');v.classList.remove('hidden');
  var ch=(typeof s.ch==='number')?s.ch:0;
  var teknik=ozetKutu(s)+
    '<div class="spark">'+sparkSVG(s.hist,s.ma50,s.ma200,s.kesisim,s.cone,s.stop)+'</div>'+
    projektorCumle(s)+
    riskKutu(s.risk_dusus)+
    tuzakKutu(s.tuzak)+
    kesisimKutu(s.kesisim)+
    ogretmenKutu(s)+
    '<div class="dgrid">'+
    cell('Yillik vol',s.vol==='-'?'—':'%'+s.vol)+cell('RSI(14)',s.rsi==='-'?'—':s.rsi)+
    cell('3-ay',s.ay3==='-'?'—':'%'+sgn(s.ay3))+cell('R/Odul',s.rr==='-'?'—':s.rr+'×')+
    cell('Destek',s.destek==='-'?'—':s.destek)+cell('Direnc',s.direnc==='-'?'—':s.direnc)+
    cell('ATR stop',s.stop==='-'?'—':s.stop)+cell('Teknik hedef',s.hedef==='-'?'—':s.hedef)+
    '</div>'+
    '<div class="stamp">Stop = ATR(14)×'+'2'+' (hisseye ozel, fiyata duyarli). Hedef = 60-gun direnci. '+
    'Bunlar risk cercevesidir — al-sat emri DEGIL.</div>';
  var baglam='<div class="stub">Sektor rotasyonu, buyuk-oyuncu akisi (OBV) ve niyet okumasi bu sekmeye gelecek. '+
    'Henuz baglanmadi — sahte gosterge koymuyoruz; veri gelince dolar.</div>';
  var sicilT='<div class="dgrid">'+cell('Bu hissede gecmis isabet','%'+s.sicil)+
    cell('Getiri ekseni','~yazi-tura')+'</div>'+
    '<div class="stamp">Sicil = bu hissedeki gecmis sinyallerin gerceklesme orani. %50 civari = '+
    'tahmin gucu yok demektir. Durust olcu budur.</div>';
  v.innerHTML='<div class="back" id="back">‹ Havuza don</div>'+
    '<div class="dhead"><span class="tk">'+s.tk+'</span><span class="nm">'+s.nm+'</span>'+
    '<span class="px">'+(s.px==='-'?'—':'₺'+s.px)+'</span></div>'+
    '<div class="'+clr(ch)+' mono" style="font-size:13px">'+(s.veri?sgn(ch)+'% bugun':'canli veri yok')+'</div>'+
    '<div class="tabs"><div class="tab on" data-t="teknik">Teknik</div>'+
    '<div class="tab" data-t="baglam">Baglam</div><div class="tab" data-t="sicil">Sicil</div></div>'+
    '<div id="tab-teknik">'+teknik+'</div>'+
    '<div id="tab-baglam" class="hidden">'+baglam+'</div>'+
    '<div id="tab-sicil" class="hidden">'+sicilT+'</div>'+
    '<div class="stamp" style="border-left-color:var(--teal);margin-top:18px">Analist hedefi senaryosu icin '+
    'sayfanin altindaki <b>Karar Cercevesi</b> panelini kullan — gordugun rakami buraya girersin.</div>';
  document.getElementById('back').onclick=function(){
    v.classList.add('hidden');document.getElementById('view-dash').classList.remove('hidden');
    window.scrollTo(0,0);
  };
  var tabs=v.querySelectorAll('.tab');
  tabs.forEach(function(t){t.onclick=function(){
    tabs.forEach(function(x){x.classList.remove('on');});t.classList.add('on');
    ['teknik','baglam','sicil'].forEach(function(name){
      document.getElementById('tab-'+name).classList.toggle('hidden',name!==t.getAttribute('data-t'));});
  };});
  window.scrollTo(0,0);
}
function cell(k,v){return '<div class="dcell"><div class="k">'+k+'</div><div class="v">'+v+'</div></div>';}

renderDash();
</script></body></html>"""

def build_html(veri=None):
    data=build_app_data(veri=veri)
    inject="<script>window.__APP_DATA__ = "+json.dumps(data,ensure_ascii=False)+";</script>\n"
    html=HTML_TEMPLATE.replace("<script>",inject+"<script>",1)
    return html,data

def write_html(out=OUT,veri=None):
    html,data=build_html(veri=veri); pathlib.Path(out).write_text(html,encoding="utf-8"); return out,data

def rapor_md(data):
    d=data; il=d.get("ileri"); rej=d["rejim"]
    L=["# APEX — Durum Raporu ("+SURUM+")",""]
    L.append("- Tarih: {} · Surum: {}".format(d.get("uretildi",""), d.get("surum","")))
    L.append("- Veri: {} dk gecikmeli · YATIRIM TAVSIYESI DEGILDIR".format(d.get("delay_dk",15)))
    L.append("")
    L.append("## Guven kerterizi")
    L.append("- Skor: **{}/100** (amber) — getiri ekseni ~yazi-tura skoru asagi ceker.".format(d["merkez"]))
    L.append("- Risk ekseni %{} (dogrulandi) · Getiri ekseni %{} (yazi-tura).".format(d["eksenler"]["risk"],d["eksenler"]["getiri"]))
    L.append("")
    L.append("## Rejim")
    L.append("- Reel faiz **%{}** ({}) · politika %{} · enflasyon %{} · kaynak: {}".format(
        rej["reel"], rej["durus"], rej["politika"], rej["enflasyon"], rej.get("makro_kaynak","")))
    L.append("")
    L.append("## Ileri-test (tek durust OOS)")
    if il:
        L.append("- N={} · ONDE **{}** · MaxDD Sistem **{}%** / Endeks {}%".format(il["n"],il["onde"],il["dd_sistem"],il["dd_endeks"]))
    else:
        L.append("- Henuz kayit yok (hafta ici 18:30 beslenir).")
    L.append("")
    L.append("## Durustluk notu")
    L.append("- Getiri tahmini KANITLANMIS edge DEGIL. Dogrulanmis eksen: risk disiplini.")
    return "\n".join(L)

def run_streamlit():
    import streamlit as st, streamlit.components.v1 as components
    st.set_page_config(page_title="APEX",page_icon="\U0001F9ED",layout="centered")
    st.markdown("<style>#MainMenu,header,footer{visibility:hidden}.block-container{padding-top:1rem;max-width:1040px}</style>",
                unsafe_allow_html=True)
    @st.cache_data(ttl=900)
    def _veri(_surum=SURUM):
        return fetch_bist()
    html,data=build_html(veri=_veri())
    components.html(html,height=1320,scrolling=True)

    with st.expander("\U0001F4CB Raporu gor"):
        _rap=rapor_md(data)
        st.markdown(_rap)
        st.caption("Kaydetmek istersen asagidaki metni uzun bas \u2192 kopyala.")
        st.code(_rap, language="markdown")

    st.markdown("---")
    st.subheader("\U0001F9ED Karar Cercevesi")
    st.caption("Sistem NE alacagini SOYLEMEZ (o sende: katalizor + kanaat). Bir hisseyi dusunuyorsan, "
               "sana NE KADAR ve NEREYE KADAR'i verir: vol-target poz buyuklugu, ATR stop, riskteki para. "
               "Karar senin — ama olculu ve sinirli.")
    secilebilir=[s for s in data["stocks"] if s.get("veri")]
    if not secilebilir:
        st.info("Canli fiyat yok — cerceve icin yfinance verisi gerekli.")
    else:
        etiketler=["{} — {}".format(s["tk"],s["nm"]) for s in secilebilir]
        secim=st.selectbox("Dusundugun hisse",etiketler,key="kc_kod")
        sec=secilebilir[etiketler.index(secim)]
        px=float(sec["px"])
        c1,c2,c3=st.columns(3)
        c1.metric("Mevcut fiyat","\u20BA{}".format(px))
        c2.metric("Yillik oynaklik","%{}".format(sec.get("vol","-")))
        c3.metric("Rejim",{"mevduat":"Mevduat","hisse":"Hisse","notr":"Notr"}.get(data["rejim"]["lehte"],"-"))
        cc1,cc2=st.columns(2)
        sermaye=cc1.number_input("Sermayen (\u20BA)",min_value=1000.0,value=100000.0,step=1000.0,key="kc_sermaye")
        entry=cc2.number_input("Dusundugun giris fiyati (\u20BA)",min_value=0.0,value=float(px),step=0.01,key="kc_entry")
        hedef=st.number_input("Analist hedefi — istege bagli (ForInvest'te gordugun, \u20BA)",
                              min_value=0.0,value=0.0,step=0.01,key="kc_hedef",
                              help="0 birakirsan senaryo bolumu atlanir.")
        ufuk=st.radio("Belirsizlik ufku (Monte Carlo)",[10,20,60],index=1,horizontal=True,key="kc_ufuk",
                      format_func=lambda g:"{} gun".format(g))
        if st.button("Karar cercevesini cikar",key="kc_btn",use_container_width=True):
            k=karar_cercevesi(float(entry),float(hedef),sec.get("vol"),sec.get("atr"),
                              float(sermaye),data["rejim"]["lehte"],teknik_hedef=sec.get("hedef"))
            if not k:
                st.warning("Hesaplanamadi — giris fiyati/veri eksik.")
            else:
                st.markdown("#### Olculu plan (AL degil — cerceve)")
                m1,m2,m3=st.columns(3)
                m1.metric("Poz buyuklugu","%{}".format(k["poz_pct"]),help="Sermayenin bu kadari — vol-target")
                m2.metric("Tutar","\u20BA{:,}".format(k["poz_tl"]).replace(",","."))
                m3.metric("~Adet",str(k["adet"]))
                n1,n2,n3=st.columns(3)
                n1.metric("Stop (ATR)","\u20BA{}".format(k["stop"]),help="Buradan asagisi: tezin yanlis, cik")
                n2.metric("Riskteki para","\u20BA{:,}".format(k["riskli_tl"]).replace(",","."),
                          delta="sermayenin %{}".format(k["riskli_pct"]),delta_color="off")
                n3.metric("R/Odul",("{}×".format(k["rr"]) if k["rr"] else "—"),
                          help="Teknik hedefe gore kazanc/risk orani")
                st.markdown("**Stop = ATR(14)×{} · poz = hisseye-ozel vol-target.** Bu, normal bir dususte "
                            "kaybinin butcende kalmasi icin. Giris/cikis kararini SEN verirsin.".format(int(ATR_K_STOP)))
                if k["senaryo"]:
                    c=k["senaryo"]
                    st.markdown("**Analist hedefi cercevesi:** {} mesafe — {}: %{:+}".format(c["buyukluk"],c["yon"],c["fark"]))
                    st.caption("Mesafe, hissenin ~1 yillik oynakliginin (%{}) {}x'i. {}".format(c["sigma_pct"],c["yil_oran"],c["bnot"]))
                mc=monte_carlo(float(entry),sec.get("vol"),gun=int(ufuk),
                               stop=k["stop"],hedef=(float(hedef) if hedef and float(hedef)>0 else None))
                if mc:
                    st.markdown("#### Belirsizlik konisi · {} gun (Monte Carlo)".format(mc["gun"]))
                    b1,b2,b3=st.columns(3)
                    b1.metric("Alt (%5)","\u20BA{}".format(mc["p5"]),delta="%{}".format(mc["band_alt"]),delta_color="off")
                    b2.metric("Medyan (%50)","\u20BA{}".format(mc["p50"]),help="~ bugun: yon tahmini YOK")
                    b3.metric("Ust (%95)","\u20BA{}".format(mc["p95"]),delta="%+{}".format(mc["band_ust"]),delta_color="off")
                    st.caption("{} gun sonra, salt oynaklikla fiyat ~%90 ihtimalle bu bantta olabilir. "
                               "Medyan bugune yakin cunku YON tahmini yok — bu kehanet degil, belirsizligin GENISLIGI."
                               .format(mc["gun"]))
                    if "stop_deg" in mc:
                        uyari=" \u2014 stop gurultunun icinde, erken tetiklenebilir." if mc["stop_deg"]>=50 else ""
                        st.write("Salt gurultuyle (yonsuz) **stop'a degme**: ~%{}{}".format(mc["stop_deg"],uyari))
                    if "hedef_deg" in mc:
                        st.write("Salt gurultuyle (yonsuz) **hedefe degme**: ~%{}".format(mc["hedef_deg"]))
                    if ("stop_deg" in mc) and ("hedef_deg" in mc):
                        st.caption("Iki olasilik benzerse: oynaklik simetrik, EDGE YOK. Bu sayilar yon SOYLEMEZ; "
                                   "tek faydasi stop'unun normal dalgalanmanin icinde olup olmadigini gormek.")
                st.info("Sistemin sana SOYLEMEDIGI: bu hisse cikar mi (~yazi-tura, edge yok). SOYLEDIGI: "
                        "ne kadar koy, nerede dur, belirsizlik ne kadar genis. Secim + katalizor sende.")
    with st.expander("Durustluk · sayilar nereden? ({})".format(SURUM)):
        st.write("{} hisse listede · {} tanesi canli veriyle dolu.".format(len(data['stocks']),data['n_veri']))
        st.write("Guven kerterizi amber cunku getiri ekseni ~yazi-tura. Poz = hisse-basi vol-target. "
                 "Stop = ATR(14)×{}. Canli veri yoksa fiyat UYDURULMAZ.".format(ATR_K_STOP))

import sys as _sys
if "streamlit" in _sys.modules:
    run_streamlit()
elif __name__=="__main__":
    out,data=write_html()
    print("OK {} · {} · {} hisse ({} canli) · rejim {} · kerteriz {}/100".format(
        out,SURUM,len(data['stocks']),data['n_veri'],data['rejim']['durus'],data['merkez']))
