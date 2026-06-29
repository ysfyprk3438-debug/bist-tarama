# -*- coding: utf-8 -*-
"""
APEX — v2.9 · KURUMSAL ARAYUZ (self-contained) · GERCEK VERI · DURUST CERCEVE
Tasarim tezi: "olcum aleti" — kalibre edilmis supheyi on plana koyan bir
navigasyon/olcu cihazi. Pusula metaforu. Amber = guven (supheli), teal =
dogrulanmis eksen (risk disiplini), pas-kirmizi = olgusal negatif.

Onceki surumlerden devam eden DURUSTLUK cekirdegi (degismedi):
  - Getiri tahmini ~ yazi-tura (sicil ~%49) — KANITLANMIS edge DEGIL.
  - Dogrulanmis eksen: hisse-basi vol-target Poz + ATR(14) stop.
  - Canli veri yoksa FIYAT UYDURULMAZ ("—" gosterilir). Sahte Sharpe yok.

v2.5 -> v2.6: Teknik sekmesine 3 ekleme — Grafik Ogretmen, Dusus Riski kutusu,
Projektor konisi.

v2.6 -> v2.7: TERS MATEMATIK tamamlandi. 6 manuel tuzak bayragi (broker, float,
markup, dagitim, temel, pazar) artik Karar Cercevesi'nde elle girilir; 4 oto +
6 manuel TEK profilde birlesir -> tam 10/10 tuzak skoru. Karar Cercevesi'nde
once "neden ALMAMALIYIM?" kapisi (tuzak kontrolu) acilir, sonra poz/stop gelir.

v2.7 -> v2.8: DENETIM + RISK SIRALAMASI. (1) Sahte sicil kaldirildi: eski
hash(sym) tabanli "gecmis isabet %49/%53" UYDURMAYDI — silindi, durust "—".
(2) Her hisseye KACINMA/RISK skoru (0-100): dusus riski(0.55) + oto tuzak(0.30)
+ RSI-asiri/vol(0.15) agirlikli ort. YON ICERMEZ; "yukselir mi" olasiligi DEGIL.
(3) Havuz bu skora gore siralanir (en kirilgan ustte) + sort secenekleri.
   Felsefe: "en iyi alim" listesi DEGIL — tersinden "once alinmayacaklar".

v2.8 -> v2.9: 2 yaniltici-sayi hatasi duzeltildi. (1) Kesisim "MA50 MA200'un
%X altinda" mevcut fiyata bolunuyordu -> coken hissede %204 gibi sacma cikiyordu;
artik MA200'e bolunur (sinirli, dogru). (2) R/Odul: coken/dusus-trendi hissede
teknik hedef (60-gun direnci) eski zirve olunca 13x gibi abartili cikiyordu ->
hedef cok uzaksa (vol bazinda BUYUK) R/Odul ⚠ ile isaretlenir + "yaniltici,
gercekci hedef degil" notu. Boylece "KACIN" yaninda sahte "buyuk odul" gozukmez.

requirements.txt:  streamlit  yfinance  numpy
"""
import json, datetime, math, pathlib
import numpy as np

OUT = "apex.html"
SURUM = "v3.3"
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
    gap_pct=round(float(diff[-1]/m200[-1]*100),1) if m200[-1] else 0.0
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


# ── 6 MANUEL TUZAK BAYRAGI (ForInvest/takas — elle girilir) ──
# (anahtar, kisa ad, ipucu/esik). Ters matematik: "neden ALMAMALIYIM?"
MANUEL_BAYRAK = [
    ("broker", "Broker konsantrasyonu",
     "ForInvest AKD dagiliminda tek broker, islem hacminin %60'indan fazlasini mi yapiyor? Tek elden toplama/dagitim imzasi."),
    ("float", "Float darligi",
     "Halka acik oran (free float) %20'nin altinda mi? Dar float = az hisseyle fiyat oynatilabilir."),
    ("markup", "Maliyeti yukselen alici",
     "Takasta buyuk alicinin ortalama maliyeti hizla yukari mi kayiyor? (Markup — pompalama hazirligi.)"),
    ("dagitim", "Fon/yabanci net satici",
     "Fonlar veya yabanci son donemde net satici mi? (Dagitim/dump hazirligi.)"),
    ("temel", "Temel anomali",
     "ROE negatif ya da F/K asiri ucta mi? Fiyati tasiyan temel yok."),
    ("pazar", "Pazar sinifi / tedbir",
     "Hisse Yakin Izleme Pazari'nda ya da tedbir/brut-takas listesinde mi?"),
]

def tuzak_birlesik(oto, manuel):
    """4 oto bayrak (fiyat+hacim) + 6 manuel bayragi (ForInvest/takas) TEK profilde
    birlestirir -> tam 10/10 tuzak skoru.
      oto    : tuzak_bayraklari()'nin donus dict'i (veya None).
      manuel : {anahtar: 'yanan'|'temiz'|'bilinmiyor'} sozlugu.
    Donen: toplam yanan /10, degerlendirilen kac bayrak, kategori, renk, tam liste.
    'bilinmiyor' = ne tuzak ne temiz (kor nokta) — durust tutulur."""
    bayrak = []; oto_var = bool(oto and oto.get("bayrak")); oto_yanan = 0
    if oto_var:
        for b in oto.get("bayrak", []):
            bayrak.append({"kaynak": "oto", "durum": b[0], "ad": b[1], "not": b[2]})
        oto_yanan = int(oto.get("yanan", 0))
    else:
        bayrak.append({"kaynak": "oto", "durum": "veriyok", "ad": "Oto bayraklar",
                       "not": "Fiyat/hacim verisi yetersiz — oto tarama yapilamadi."})
    manuel = manuel or {}; man_yanan = 0; man_degerlendirilen = 0
    for k, ad, ipucu in MANUEL_BAYRAK:
        durum = manuel.get(k, "bilinmiyor")
        if durum == "yanan": man_yanan += 1; man_degerlendirilen += 1
        elif durum == "temiz": man_degerlendirilen += 1
        bayrak.append({"kaynak": "manuel", "durum": durum, "ad": ad, "not": ipucu})
    toplam_yanan = oto_yanan + man_yanan
    degerlendirilen = (4 if oto_var else 0) + man_degerlendirilen
    # Oto-YUKSEK (>=2) sinyalini manuel eksigi GORUNTULEMESIN: oto severity taban olur.
    if toplam_yanan >= 3 or oto_yanan >= 2:
        kategori, renk = "YUKSEK — guclu tuzak belirtileri", "rust"
    elif toplam_yanan >= 1:
        kategori, renk = "ORTA — en az bir bayrak yandi", "amber"
    else:
        kategori, renk = "DUSUK — bariz tuzak yok", "teal"
    return {"yanan": toplam_yanan, "toplam": 10, "degerlendirilen": degerlendirilen,
            "oto_yanan": oto_yanan, "oto_var": oto_var, "man_yanan": man_yanan,
            "kategori": kategori, "renk": renk, "bayrak": bayrak}


def risk_skoru(rd, tuzak, rsi_val, vol_frac):
    """KACINMA/RISK skoru 0-100 (yuksek = daha kirilgan, daha cok dikkat).
    OLCULEBILIR risk sinyallerinin AGIRLIKLI ORTALAMASI — TAHMIN DEGIL.
    'Yukselir/duser' OLASILIGI DEGIL; YON ICERMEZ. Surucu listesi seffaf.
    Agirliklar: dusus_riski 0.55 + oto_tuzak 0.30 + (RSI-asiri / vol) 0.15."""
    surucu = []
    dr = int(rd.get("skor", 0)) if rd else 0
    if dr > 0: surucu.append(("Dusus riski " + str(dr) + "/100", dr))
    ty = int(tuzak.get("yanan", 0)) if tuzak else 0
    tpct = ty / 4.0 * 100.0
    if ty > 0: surucu.append((str(ty) + " oto tuzak bayragi", tpct))
    ek = 0.0
    if rsi_val is not None:
        try: rv = float(rsi_val)
        except Exception: rv = None
        if rv is not None and rv >= 70:
            rr = 100.0 if rv >= 78 else 55.0
            ek = max(ek, rr); surucu.append(("RSI " + str(int(rv)) + " asiri alim", rr))
    if vol_frac:
        vp = round(float(vol_frac) * 100)
        if float(vol_frac) >= 0.55:
            ek = max(ek, 100.0); surucu.append(("Yillik vol %" + str(vp), 100.0))
        elif float(vol_frac) >= 0.40:
            ek = max(ek, 50.0); surucu.append(("Yillik vol %" + str(vp), 50.0))
    skor = int(max(0, min(100, round(0.55 * dr + 0.30 * tpct + 0.15 * ek))))
    if skor >= 60: kat, renk = "YUKSEK kacinma", "rust"
    elif skor >= 35: kat, renk = "ORTA", "amber"
    else: kat, renk = "DUSUK", "teal"
    surucu = [s[0] for s in sorted(surucu, key=lambda x: -x[1])[:3]]
    return {"skor": skor, "kat": kat, "renk": renk, "surucu": surucu}


# ══════════════════════════════════════════════════════════════
# AKD (Araci Kurum Dagilimi) — ForInvest akdAt verisi
# ══════════════════════════════════════════════════════════════
# Veri AKISI: ForInvest MCP -> Claude Desktop (Yusuf'un makinesi) gunluk
# ceker -> akd_takas.json'a yazilir -> repoya konur -> bu terminal okur.
# Streamlit Cloud MCP CAGIRAMAZ; sadece JSON snapshot okur. Dosya yoksa "—".
#
# JSON sema (akdAt inputType=symbol ciktisindan turetilir):
# {
#   "uretildi": "2026-06-26T18:30",
#   "kaynak": "ForInvest akdAt",
#   "hisseler": {
#     "THYAO": {
#       "tarih": "20260626",
#       "grand_total_amount": <GrandTotalAmount, TL>,
#       "grand_net_amount":   <GrandNetAmount, TL>,
#       "alici":  [ {"broker":"BMK","ad":"...","net_amount":..,"total_amount":..,"tip":"yabanci|fon|yerli|?"}, ... ilk 5 net alici ],
#       "satici": [ {"broker":"...","net_amount":..(negatif),"total_amount":..,"tip":".."}, ... ilk 5 net satici ]
#     }, ...
#   }
# }
AKD_DOSYA = "akd_takas.json"
AKD_KONS_ESIK = 60.0          # tek broker hacmin >%60'i -> konsantrasyon bayragi
_AKD_CACHE = {"yuklendi": False, "veri": {}}

def akd_oku():
    """akd_takas.json'u bir kez okur (cache'ler). Dosya yoksa/bozuksa bos dict.
    UYDURMA YOK: dosya yoksa AKD ozelligi sessizce '—' kalir."""
    if _AKD_CACHE["yuklendi"]:
        return _AKD_CACHE["veri"]
    veri = {}
    try:
        p = pathlib.Path(AKD_DOSYA)
        if p.exists():
            ham = json.loads(p.read_text(encoding="utf-8"))
            if isinstance(ham, dict) and isinstance(ham.get("hisseler"), dict):
                veri = ham
    except Exception:
        veri = {}
    _AKD_CACHE["yuklendi"] = True; _AKD_CACHE["veri"] = veri
    return veri

def akd_hisse(sym):
    """Tek hissenin AKD snapshot'i (dict) veya None."""
    v = akd_oku()
    if not v:
        return None
    return (v.get("hisseler") or {}).get(sym)

def _akd_konsantrasyon(akd_sym):
    """En buyuk islem hacmine sahip brokerin toplam hacme oranini (%) dondurur.
    (broker_ad, yuzde) veya (None, None). 'broker' tuzak bayragini besler."""
    if not akd_sym:
        return None, None
    gt = akd_sym.get("grand_total_amount")
    try:
        gt = float(gt)
    except Exception:
        gt = 0.0
    if gt <= 0:
        return None, None
    en_ad, en_pay = None, 0.0
    for grup in ("alici", "satici"):
        for b in (akd_sym.get(grup) or []):
            try:
                ta = float(b.get("total_amount") or 0.0)
            except Exception:
                ta = 0.0
            pay = ta / gt * 100.0
            if pay > en_pay:
                en_pay = pay; en_ad = b.get("ad") or b.get("broker") or "?"
    if en_ad is None:
        return None, None
    return en_ad, round(en_pay, 1)

def _akd_yabanci_fon_net(akd_sym):
    """Yabanci+fon brokerlarin TEK GUNLUK net TL akisini dondurur (toplam).
    tip alani yoksa None. Tek gun 'son donem' DEGIL — yon icin BILGI, bayrak DEGIL."""
    if not akd_sym:
        return None
    tipli = False; net = 0.0
    for grup in ("alici", "satici"):
        for b in (akd_sym.get(grup) or []):
            t = (b.get("tip") or "").lower()
            if t in ("yabanci", "fon", "yabancı"):
                tipli = True
                try:
                    net += float(b.get("net_amount") or 0.0)
                except Exception:
                    pass
    return net if tipli else None

def akd_bayraklari(akd_sym):
    """AKD'den OTOMATIK turetilebilen tuzak bayraklari + bilgi metrikleri.
    Donen:
      oto_manuel : {"broker": "yanan"|"temiz"}  -> manuel bayrak on-doldurmasi
                   (sadece HESAPLANABILEN bayrak; digerleri 'bilinmiyor' kalir)
      bilgi      : UI'da gosterilecek ham metrikler (uydurmasiz)
    AKD yoksa None."""
    if not akd_sym:
        return None
    en_ad, en_pay = _akd_konsantrasyon(akd_sym)
    oto_manuel = {}
    if en_pay is not None:
        oto_manuel["broker"] = "yanan" if en_pay > AKD_KONS_ESIK else "temiz"
    yf_net = _akd_yabanci_fon_net(akd_sym)
    alici = (akd_sym.get("alici") or [])[:5]
    satici = (akd_sym.get("satici") or [])[:5]
    bilgi = {"tarih": akd_sym.get("tarih"),
             "en_buyuk_broker": en_ad, "en_buyuk_pay": en_pay,
             "yabanci_fon_net": yf_net,
             "alici": alici, "satici": satici,
             "grand_net": akd_sym.get("grand_net_amount")}
    return {"oto_manuel": oto_manuel, "bilgi": bilgi}


# ══════════════════════════════════════════════════════════════
# AKIS (gun-ici / intraday) — "su an ne oluyor" BETIMLEYICI metrikler
# ══════════════════════════════════════════════════════════════
# TUM metrikler BETIMLEYICIDIR: bugunu olcer, yarini TAHMIN ETMEZ.
# Hicbiri 'al/sat' demez. 'Sayilarin agirlik siddeti' = hacim-agirligi.
# Yon kehaneti YOK; sadece "fiyat nerede, hacim kimde, geri cekilme ne kadar".
def akis_metrikleri(o, h, l, c, v):
    """Intraday bar dizilerinden (orn. 5dk) gun-ici akis profili. Yetersiz -> None.
    Donen alanlar HEPSI 'su an' durumu — gelecek imasi YOK."""
    o = np.asarray(o, float); h = np.asarray(h, float); l = np.asarray(l, float)
    c = np.asarray(c, float); v = np.asarray(v, float)
    n = len(c)
    if n < 6 or float(np.nansum(v)) <= 0:
        return None
    tp = (h + l + c) / 3.0
    vsum = float(np.nansum(v))
    vwap = float(np.nansum(tp * v) / max(vsum, 1e-9))
    px = float(c[-1]); acilis = float(o[0])
    vwap_pos = round((px / vwap - 1) * 100, 2) if vwap > 0 else 0.0
    gun = round((px / acilis - 1) * 100, 2) if acilis > 0 else 0.0
    gun_hi = float(np.nanmax(h)); gun_lo = float(np.nanmin(l))
    tepe_geri = round((px / gun_hi - 1) * 100, 2) if gun_hi > 0 else 0.0   # zirveden % (<=0)
    dip_toparla = round((px / gun_lo - 1) * 100, 2) if gun_lo > 0 else 0.0  # dipten % (>=0)
    dif = np.diff(c); vv = v[1:]
    up = float(vv[dif > 0].sum()); dn = float(vv[dif < 0].sum()); tot = up + dn
    hacim_denge = round((up - dn) / tot * 100, 1) if tot > 0 else 0.0       # -100..+100
    k = min(6, n - 1); rv = vv[-k:]; rtot = float(rv.sum())
    yuklenme = round(float((np.sign(dif[-k:]) * rv).sum()) / rtot * 100, 1) if rtot > 0 else 0.0
    orn = min(6, n); or_hi = float(np.nanmax(h[:orn])); or_lo = float(np.nanmin(l[:orn]))
    if px > or_hi: acilis_durum = "kirilim yukari"
    elif px < or_lo: acilis_durum = "kirilim asagi"
    else: acilis_durum = "aralikta"
    kb = min(12, n - 1); sv = vv[-kb:]; svt = float(sv.sum())
    kap_yon = round(float((np.sign(dif[-kb:]) * sv).sum()) / max(svt, 1e-9) * 100, 1) if svt > 0 else 0.0
    kap_hacim_pay = round(svt / max(vsum, 1e-9) * 100, 1)
    yer = "VWAP ustu" if vwap_pos > 0 else ("VWAP alti" if vwap_pos < 0 else "VWAP'ta")
    bask = ("alici yuklenmesi" if yuklenme >= 25 else
            "satici yuklenmesi" if yuklenme <= -25 else "denge")
    return {"vwap": round(vwap, 2), "vwap_pos": vwap_pos, "gun": gun,
            "tepe_geri": tepe_geri, "dip_toparla": dip_toparla,
            "hacim_denge": hacim_denge, "yuklenme": yuklenme,
            "acilis_durum": acilis_durum, "or_hi": round(or_hi, 2), "or_lo": round(or_lo, 2),
            "kap_yon": kap_yon, "kap_hacim_pay": kap_hacim_pay,
            "durum": yer + " \u00b7 " + bask, "bar": n}


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

def fetch_intraday():
    """Tum BIST icin gun-ici 5dk barlari ceker, her hisseye akis_metrikleri uygular.
    yfinance gun-ici veriyi sadece SON gun(ler) icin verir + 15dk GECIKMELI.
    Piyasa kapaliysa/veri yoksa -> bos dict (UYDURMA YOK). {sym: akis_dict}."""
    try:
        import yfinance as yf
    except Exception:
        return {}
    syms = [s + ".IS" for s, _ in BIST]; out = {}
    try:
        df = yf.download(syms, period="1d", interval="5m", group_by="ticker",
                         auto_adjust=True, progress=False, threads=True)
    except Exception:
        return {}
    for s, _ in BIST:
        try:
            sub = df[s + ".IS"][["Open", "High", "Low", "Close", "Volume"]].dropna()
            if len(sub) < 6:
                continue
            m = akis_metrikleri(sub["Open"].values, sub["High"].values, sub["Low"].values,
                                sub["Close"].values, sub["Volume"].values)
            if m:
                out[s] = m
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

# ══════════════════════════════════════════════════════════════
# KALIBRASYON DEFTERI — sistemin KENDI sinyallerini SINAR (tahmin satmaz)
# ══════════════════════════════════════════════════════════════
# Felsefe: bir sinyalin (akis yuklenmesi, tuzak, risk) ima ettigi yonu kaydet,
# 'ufuk' gun sonra fiyat gercekte ne yapti olc. Isabet = sinyal kac kez tuttu.
# Placebo cizgisi = %50 (rastgele). Isabet placebo'ya yakinsa -> "yon vermiyor,
# GUVENME" ve Guven skorunu ASAGI ceker. Amac tahmin DEGIL, oz-denetim.
# Veri zamanla birikir (gunluk cron). N dusukken sonuc GURULTUDUR, oyle isaretlenir.
KALIB_DOSYA = "kalibrasyon_defteri.csv"
KALIB_UFUK = 5                 # kac islem gunu sonra sonuca bakilir
KALIB_BASLIK = ["tarih","hisse","sinyal","yon","ufuk","giris","sonuc_tarih","cikis","gercek","isabet"]

def _kalib_sinyaller(s):
    """Bir hisse dict'inden o anki FIRLEYEN sinyalleri + ima ettikleri yonu cikarir.
    Donen: [(sinyal_adi, yon)] — yon +1 (yukari beklerdi) / -1 (asagi beklerdi).
    Sadece NET firleyen sinyaller kaydedilir; notr olanlar atlanir.
    NOT: bu yonlerin DOGRU oldugunu IDDIA ETMIYORUZ — tutup tutmadigini SINIYORUZ.
    Cogunun ~%50 (placebo) cikmasini bekliyoruz."""
    out = []
    ak = s.get("akis")
    if ak:
        y = ak.get("yuklenme", 0)
        if y >= 25: out.append(("akis_yuklenme", 1))
        elif y <= -25: out.append(("akis_yuklenme", -1))
    tz = s.get("tuzak")
    if tz:
        if int(tz.get("yanan", 0)) >= 2: out.append(("tuzak_yuksek", -1))
    rs = s.get("risk_skor")
    try:
        if rs not in (None, "-") and float(rs) >= 60: out.append(("risk_yuksek", -1))
    except Exception:
        pass
    ks = s.get("kesisim")
    if isinstance(ks, dict):
        t = (ks.get("tip") or "").lower()
        if "golden" in t or "altin" in t: out.append(("ma_kesisim", 1))
        elif "death" in t or "olum" in t: out.append(("ma_kesisim", -1))
    return out

def kalibrasyon_kaydet(bugun, data, ufuk=KALIB_UFUK):
    """O gunun firleyen sinyallerini deftere ACIK kayit olarak ekler (idempotent).
    Sonuc alanlari bos baslar, vade dolunca dolar. Eklenen kayit sayisini dondurur."""
    import csv as _csv
    bugun = bugun.isoformat() if hasattr(bugun, "isoformat") else str(bugun)
    p = pathlib.Path(KALIB_DOSYA); mevcut = set(); satirlar = []
    if p.exists():
        try:
            with open(p, encoding="utf-8") as f:
                for row in _csv.DictReader(f):
                    satirlar.append(row); mevcut.add((row.get("tarih"), row.get("hisse"), row.get("sinyal")))
        except Exception:
            satirlar = []; mevcut = set()
    yeni = 0
    for s in data.get("stocks", []):
        if not s.get("veri"): continue
        try: giris = float(s.get("px"))
        except Exception: continue
        for sinyal, yon in _kalib_sinyaller(s):
            if (bugun, s["tk"], sinyal) in mevcut: continue
            satirlar.append({"tarih": bugun, "hisse": s["tk"], "sinyal": sinyal, "yon": yon,
                             "ufuk": ufuk, "giris": giris, "sonuc_tarih": "", "cikis": "",
                             "gercek": "", "isabet": ""})
            mevcut.add((bugun, s["tk"], sinyal)); yeni += 1
    try:
        with open(p, "w", encoding="utf-8", newline="") as f:
            w = _csv.DictWriter(f, fieldnames=KALIB_BASLIK); w.writeheader()
            for r in satirlar: w.writerow({k: r.get(k, "") for k in KALIB_BASLIK})
    except Exception:
        return 0
    return yeni

def kalibrasyon_sonuclandir(bugun, fiyatlar):
    """Vadesi dolmus ACIK kayitlari guncel fiyatla kapatir, isabet isaretler.
    fiyatlar: {hisse: guncel_fiyat}. gercek = sign(cikis/giris-1)."""
    import csv as _csv, datetime as _dt
    p = pathlib.Path(KALIB_DOSYA)
    if not p.exists(): return 0
    bug = bugun if hasattr(bugun, "toordinal") else _dt.date.fromisoformat(str(bugun))
    try:
        with open(p, encoding="utf-8") as f: satirlar = list(_csv.DictReader(f))
    except Exception:
        return 0
    kapatilan = 0
    for r in satirlar:
        if (r.get("isabet") or "") != "": continue
        try: kt = _dt.date.fromisoformat(r["tarih"]); uf = int(r["ufuk"])
        except Exception: continue
        if (bug - kt).days < uf: continue
        px = fiyatlar.get(r["hisse"])
        if px in (None, "-", ""): continue
        try: giris = float(r["giris"]); cikis = float(px); yon = int(r["yon"])
        except Exception: continue
        gercek = 1 if cikis > giris else (-1 if cikis < giris else 0)
        r["sonuc_tarih"] = bug.isoformat(); r["cikis"] = cikis
        r["gercek"] = gercek; r["isabet"] = (1 if (gercek != 0 and yon == gercek) else 0)
        kapatilan += 1
    if kapatilan:
        try:
            with open(p, "w", encoding="utf-8", newline="") as f:
                w = _csv.DictWriter(f, fieldnames=KALIB_BASLIK); w.writeheader()
                for r in satirlar: w.writerow({k: r.get(k, "") for k in KALIB_BASLIK})
        except Exception:
            return 0
    return kapatilan

def kalibrasyon_ozet():
    """Sinyal-bazli + TOPLAM isabet ozeti. Defter yok/bos -> None (UYDURMA YOK)."""
    import csv as _csv
    p = pathlib.Path(KALIB_DOSYA)
    if not p.exists(): return None
    try:
        with open(p, encoding="utf-8") as f: rows = list(_csv.DictReader(f))
    except Exception:
        return None
    grup = {}; acik = 0
    for r in rows:
        if (r.get("isabet") or "") == "": acik += 1; continue
        try: h = int(r["isabet"])
        except Exception: continue
        g = grup.setdefault(r.get("sinyal","?"), {"n":0,"h":0}); g["n"] += 1; g["h"] += h
    def _etiket(n, pct):
        if n < 30: return ("yetersiz", "Gurultu — guvenilir yargi icin >=30 kapali kayit gerek.")
        if 42 <= pct <= 58: return ("placebo", "Yazi-tura seviyesi — bu sinyal yon VERMIYOR.")
        if n >= 50: return ("aday", "Placebo disinda — izlenmeye deger AMA hala kanit degil.")
        return ("izlenmeli", "Placebo disinda ama N dusuk — birikmesini bekle.")
    sinyaller = []; tn = th = 0
    for ad, g in sorted(grup.items()):
        pct = round(g["h"]/g["n"]*100, 1) if g["n"] else 0.0
        et, ac = _etiket(g["n"], pct)
        sinyaller.append({"sinyal": ad, "n": g["n"], "isabet": pct, "etiket": et, "aciklama": ac})
        tn += g["n"]; th += g["h"]
    toplam_pct = round(th/tn*100, 1) if tn else None
    t_et, t_ac = _etiket(tn, toplam_pct if toplam_pct is not None else 0)
    return {"sinyaller": sinyaller, "toplam_n": tn, "toplam_isabet": toplam_pct,
            "toplam_etiket": t_et, "toplam_aciklama": t_ac, "acik_kayit": acik, "placebo": 50}


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

def build_app_data(bugun=None, veri=None, akis=None):
    bugun=bugun or datetime.date.today()
    rej=rejim_hesapla(bugun)
    veri=veri if veri is not None else fetch_bist(); canli=len(veri)>0
    akis=akis if akis is not None else {}
    il=ileri_seri()
    g,r,rp=49,92,60
    merkez=round(0.55*g+0.30*r+0.15*rp)
    stocks=[]
    for sym,ad in BIST:
        d=veri.get(sym)
        base={"tk":sym,"nm":ad,"sicil":None}
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
            rsk=risk_skoru(d.get("risk_dusus"),d.get("tuzak"),d.get("rsi"),d.get("vol"))
            base.update({"risk_skor":rsk["skor"],"risk_kat":rsk["kat"],"risk_renk":rsk["renk"],"risk_surucu":rsk["surucu"]})
            _sen=senaryo_cerceve(px,hedef,(svol*100.0),atr)
            base["rr_uzak"]=bool(_sen and _sen["yil_oran"]>=1.5)
            base["akis"]=akis.get(sym)
        else:
            base.update({"px":"-","ch":0,"hist":[],"ma50":[],"ma200":[],"rsi":"-","destek":"-","direnc":"-",
                "hedef":"-","stop":"-","atr":"-","rr":"-","ay3":"-","vol":"-","poz":"-","kesisim":None,
                "risk_dusus":None,"cone":None,"tuzak":None,"veri":False})
            base.update({"risk_skor":"-","risk_kat":"-","risk_renk":"","risk_surucu":[]})
            base["rr_uzak"]=False
            base["akis"]=None
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
.row{display:grid;grid-template-columns:76px 1fr 70px 52px 42px 50px 48px;gap:8px;align-items:center;padding:11px 14px;border-bottom:1px solid var(--line);cursor:pointer;transition:background .12s}
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
.sortbar{display:flex;gap:6px;flex-wrap:wrap;margin:0 0 6px}
.sortbar .sb{font-family:var(--mono);font-size:10.5px;letter-spacing:.06em;color:var(--faint);border:1px solid var(--line);border-radius:3px;padding:5px 9px;cursor:pointer;text-transform:uppercase}
.sortbar .sb:hover{color:var(--dim)}
.sortbar .sb.on{color:var(--ink);background:var(--amber);border-color:var(--amber)}
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
  .row{grid-template-columns:52px 1fr 56px 42px 34px 42px 38px;gap:5px;padding:10px 10px}
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
  <div class="sortbar" id="sortbar"></div>
  <div class="faint" id="sort-note" style="font-size:10.5px;margin:-2px 0 10px"></div>
  <div class="pool">
    <div class="row head"><span>Kod</span><span>Sirket</span><span style="text-align:right">Fiyat</span>
      <span style="text-align:right">Gun%</span><span style="text-align:right">Vol</span>
      <span style="text-align:right">Risk</span><span>Poz</span></div>
    <div class="scroll" id="pool"></div>
  </div>
</div>

<div id="view-detail" class="hidden"></div>

<div class="disc" id="disc">APEX v2.9 · yatirim tavsiyesi degildir · getiri tahmini ~ yazi-tura, kanitlanmis edge degil</div>
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
  if(num(s.risk_skor)){riskTxt='Kacinma/risk skoru '+s.risk_skor+'/100 ('+(s.risk_kat||'')+')'+((s.risk_surucu&&s.risk_surucu.length)?' \u2014 '+s.risk_surucu.join(', '):'')+'.';}
  else if(s.risk_dusus){var rk=s.risk_dusus.skor; riskTxt='Dusus riski '+rk+'/100.';}
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
    '<div class="faint" style="font-size:11px;margin-top:8px">Oto bayraklar fiyat+hacimden. <b>Bu 6 manuel bayragi asagidaki Karar Cercevesi \u2192 Tuzak kontrolu panelinden elle girip tam 10/10 profil cikarabilirsin.</b> Ters matematik: kazanani bilemeyiz, tuzagi isaretleyebiliriz.</div></div>';
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
  APP._idx={};(APP.stocks||[]).forEach(function(s,i){APP._idx[s.tk]=i;});
  document.getElementById('pool-meta').textContent=(APP.stocks||[]).length+' hisse · '+APP.n_veri+' canli';
  renderSortbar();renderPool();
}

var SORT_KEYS=[['risk','Risk \u2193'],['ch','Gun%'],['vol','Vol'],['tk','Kod']];
var curSort='risk';
function riskCol(r){return r>=60?'dn':(r>=35?'am':'up');}
function renderSortbar(){
  var sb=document.getElementById('sortbar');if(!sb)return;sb.innerHTML='';
  SORT_KEYS.forEach(function(k){
    var d=document.createElement('div');d.className='sb'+(curSort===k[0]?' on':'');
    d.textContent=k[1];d.onclick=function(){curSort=k[0];renderSortbar();renderPool();};
    sb.appendChild(d);
  });
  var note=document.getElementById('sort-note');
  if(note)note.textContent=(curSort==='risk')
    ?'Risk = kacinma skoru (kirilganlik): dusus riski + tuzak + RSI/vol. \u0027En iyi alim\u0027 DEGIL \u2014 en kirilgan ustte. Yon icermez.'
    :'Risk sutunu = kacinma skoru (kirilganlik); tahmin/al sinyali degil. Siralama: '+curSort+'.';
}
function sortStocks(arr){
  var a=arr.slice();
  function rv(s){return (typeof s.risk_skor==='number')?s.risk_skor:-1;}
  if(curSort==='risk')a.sort(function(x,y){return rv(y)-rv(x);});
  else if(curSort==='ch')a.sort(function(x,y){return (y.veri?y.ch:-1e9)-(x.veri?x.ch:-1e9);});
  else if(curSort==='vol')a.sort(function(x,y){return (typeof y.vol==='number'?y.vol:-1)-(typeof x.vol==='number'?x.vol:-1);});
  else a.sort(function(x,y){return x.tk<y.tk?-1:(x.tk>y.tk?1:0);});
  return a;
}
function renderPool(){
  var pool=document.getElementById('pool');if(!pool)return;pool.innerHTML='';
  var maxv=1;(APP.stocks||[]).forEach(function(s){if(typeof s.vol==='number'&&s.vol>maxv)maxv=s.vol;});
  sortStocks(APP.stocks||[]).forEach(function(s){
    var i=APP._idx[s.tk];
    var r=document.createElement('div');r.className='row';
    var ch=(typeof s.ch==='number')?s.ch:0;
    var volpct=(typeof s.vol==='number')?Math.round(s.vol/maxv*100):0;
    var rk=(typeof s.risk_skor==='number')?s.risk_skor:null;
    r.innerHTML='<span class="tk">'+s.tk+'</span><span class="nm">'+s.nm+'</span>'+
      '<span class="n">'+(s.px==='-'?'\u2014':s.px)+'</span>'+
      '<span class="n '+clr(ch)+'">'+(s.veri?sgn(ch)+'%':'\u2014')+'</span>'+
      '<span class="n dim">'+(s.vol==='-'?'\u2014':'%'+s.vol)+'</span>'+
      '<span class="n '+(rk!==null?riskCol(rk):'faint')+'">'+(rk!==null?rk:'\u2014')+'</span>'+
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
    cell('3-ay',s.ay3==='-'?'—':'%'+sgn(s.ay3))+cell('R/Odul',s.rr==='-'?'—':(s.rr+'×'+(s.rr_uzak?' \u26A0':'')))+
    cell('Destek',s.destek==='-'?'—':s.destek)+cell('Direnc',s.direnc==='-'?'—':s.direnc)+
    cell('ATR stop',s.stop==='-'?'—':s.stop)+cell('Teknik hedef',s.hedef==='-'?'—':s.hedef)+
    '</div>'+
    '<div class="stamp">Stop = ATR(14)×'+'2'+' (hisseye ozel, fiyata duyarli). Hedef = 60-gun direnci. '+
    'Bunlar risk cercevesidir — al-sat emri DEGIL.</div>'+
    (s.rr_uzak?'<div class="stamp" style="border-left-color:var(--rust)">\u26A0 <b>R/Odul yaniltici:</b> teknik hedef (60-gun direnci \u20BA'+s.hedef+') fiyatin cok ustunde. Dusus trendindeki bir hissede bu "eski zirveye donus" demektir — R/Odul abartili gorunur, olagandisi toparlanma gerektirir. Yakin/gercekci bir hedef DEGIL; "buyuk odul" diye okuma.</div>':'');
  var baglam='<div class="stub">Sektor rotasyonu, buyuk-oyuncu akisi (OBV) ve niyet okumasi bu sekmeye gelecek. '+
    'Henuz baglanmadi — sahte gosterge koymuyoruz; veri gelince dolar.</div>';
  var sicilT='<div class="dgrid">'+cell('Bu hissede gecmis isabet','—')+
    cell('Getiri ekseni','~yazi-tura')+'</div>'+
    '<div class="stamp">Bu hisseye OZEL gecmis isabet orani HENUZ YOK — onceki surumlerdeki '+
    '%49/%53 sayisi uydurmaydi (isimden turetiliyordu), kaldirildi. Gercek sicil ancak '+
    'ileri-test (paper) gunlugu hisse bazinda birikince olusur. Durust cevap: getiri tahmini '+
    '~yazi-tura, kanitlanmis edge yok.</div>';
  v.innerHTML='<div class="back" id="back">‹ Havuza don</div>'+
    '<div class="dhead"><span class="tk">'+s.tk+'</span><span class="nm">'+s.nm+'</span>'+
    '<span class="px">'+(s.px==='-'?'—':'₺'+s.px)+'</span></div>'+
    '<div class="'+clr(ch)+' mono" style="font-size:13px">'+(s.veri?sgn(ch)+'% bugun':'canli veri yok')+'</div>'+
    '<div class="tabs"><div class="tab on" data-t="teknik">Teknik</div>'+
    '<div class="tab" data-t="baglam">Baglam</div><div class="tab" data-t="sicil">Sicil</div></div>'+
    '<div id="tab-teknik">'+teknik+'</div>'+
    '<div id="tab-baglam" class="hidden">'+baglam+'</div>'+
    '<div id="tab-sicil" class="hidden">'+sicilT+'</div>'+
    '<div class="stamp" style="border-left-color:var(--teal);margin-top:18px">Analist hedefi senaryosu ve '+
    '<b>10/10 tuzak kontrolu</b> icin sayfanin altindaki <b>Karar Cercevesi</b> panelini kullan.</div>';
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

def build_html(veri=None, akis=None):
    data=build_app_data(veri=veri, akis=akis)
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
    @st.cache_data(ttl=300)
    def _akis(_surum=SURUM):
        return fetch_intraday()
    html,data=build_html(veri=_veri(), akis=_akis())
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

        # ── AKIS PANELI (gun-ici) — BETIMLEYICI: "su an ne oluyor", tahmin DEGIL ──
        with st.expander("\U0001F4CA Akis paneli (gun-ici) — 'su an ne oluyor', tahmin DEGIL", expanded=False):
            ak=sec.get("akis")
            if not ak:
                st.caption("Bu hisse icin gun-ici (5dk) veri yok. Piyasa kapali olabilir ya da "
                           "yfinance intraday bar dondurmedi. Acilis-kapanis arasi dolacak. Veri yoksa UYDURMUYORUZ.")
            else:
                def _ok(x):  # yon oku
                    try: x=float(x)
                    except Exception: return ""
                    return "\u25B2" if x>0 else ("\u25BC" if x<0 else "\u25AC")
                a1,a2,a3=st.columns(3)
                a1.metric("VWAP'a gore","%{:+.2f}".format(ak["vwap_pos"]),help="Fiyatin gun-ici hacim-agirlikli ortalamaya uzakligi. + = ustunde.")
                a2.metric("Gun-ici getiri","%{:+.2f}".format(ak["gun"]),help="Acilis fiyatina gore.")
                a3.metric("Yuklenme","{:+.0f}".format(ak["yuklenme"]),help="Son ~30dk hacim-agirlikli yon. +100 tam alici, -100 tam satici.")
                b1,b2,b3=st.columns(3)
                b1.metric("Zirveden geri","%{:.2f}".format(ak["tepe_geri"]),help="Gun-ici tepeden mevcut geri cekilme.")
                b2.metric("Hacim dengesi","{:+.0f}".format(ak["hacim_denge"]),help="Gun boyu: yukselen bar hacmi vs dusen bar hacmi (-100..+100).")
                b3.metric("Kapanis baskisi","{:+.0f}".format(ak["kap_yon"]),help="Son ~1 saatin hacim-agirlikli yonu.")
                renk="#4FB8A4" if ak["vwap_pos"]>0 else "#D2715A"
                st.markdown("<div style='border-left:3px solid {c};padding:8px 12px;background:rgba(255,255,255,.02);"
                            "border-radius:4px;margin-top:4px'><b style='color:{c}'>Su an: {d}</b>"
                            "<br><span style='color:#9AA4A0;font-size:12px'>Acilis araligi: {ad} "
                            "(OR {lo}\u2013{hi}) \u00b7 {n} bar \u00b7 15dk gecikmeli</span></div>".format(
                                c=renk,d=ak["durum"],ad=ak["acilis_durum"],
                                lo=ak["or_lo"],hi=ak["or_hi"],n=ak["bar"]),unsafe_allow_html=True)
                st.caption("Hepsi BETIMLEYICI \u2014 'su an fiyat nerede, hacim kimde, geri cekilme ne kadar'. "
                           "Hicbiri 'yukselir/al' DEMEZ. Gun-ici akis bugunu anlatir, yarini degil.")

        # ── TUZAK KONTROLU (10/10) — ters matematik: once "neden ALMAMALIYIM?" ──
        with st.expander("\U0001F3AF Tuzak kontrolu (10/10) — once 'neden ALMAMALIYIM?'", expanded=False):
            oto_t=sec.get("tuzak")
            ico={"yanan":"\U0001F534","temiz":"\u2705","veriyok":"\u2014"}
            if oto_t:
                st.markdown("**Oto bayraklar (fiyat+hacimden) — {}/4 yandi:**".format(oto_t.get("yanan",0)))
                for b in oto_t.get("bayrak",[]):
                    st.markdown("{} **{}** — {}".format(ico.get(b[0],""),b[1],b[2]))
            else:
                st.caption("Bu hisse icin oto bayrak hesaplanamadi (fiyat/hacim yetersiz).")
            st.markdown("---")
            # ── ForInvest AKD snapshot (varsa) — bilgi paneli + broker bayrak on-dolum ──
            akd_b = akd_bayraklari(akd_hisse(sec["tk"]))
            akd_oto = {}
            if akd_b:
                bg = akd_b["bilgi"]; akd_oto = akd_b.get("oto_manuel", {})
                def _tl(x):
                    try: x=float(x)
                    except Exception: return "—"
                    a=abs(x)
                    if a>=1e9: return ("{:+.2f} mlr\u20BA").format(x/1e9)
                    if a>=1e6: return ("{:+.1f} mln\u20BA").format(x/1e6)
                    return ("{:+.0f}\u20BA").format(x)
                pay=bg.get("en_buyuk_pay"); brk=bg.get("en_buyuk_broker"); yfn=bg.get("yabanci_fon_net")
                satir=("\U0001F4E1 <b>ForInvest AKD</b> &middot; {t} &nbsp;|&nbsp; "
                       "En buyuk islemci: <b>{b}</b> (hacmin %{p})").format(
                           t=bg.get("tarih") or "—", b=brk or "—",
                           p=(pay if pay is not None else "—"))
                if yfn is not None:
                    satir += " &nbsp;|&nbsp; Yabanci/fon net (gun): <b>{}</b>".format(_tl(yfn))
                st.markdown("<div style='font-size:12px;color:#9AA4A0;background:rgba(79,184,164,.06);"
                            "border-left:3px solid #4FB8A4;padding:8px 12px;border-radius:4px;margin:4px 0'>"
                            +satir+"</div>", unsafe_allow_html=True)
                if yfn is not None:
                    st.caption("Yabanci/fon net = TEK GUNLUK akis; 'son donem' degil. Bayrak degil, BILGI. "
                               "Yon icin sende kalsin, tek gunle 'dagitim' demiyoruz.")
                st.caption("'Broker konsantrasyonu' bayragi AKD'den OTOMATIK on-dolduruldu "
                           "(tek islemci hacmin >%{} ise yanar). Istersen elle degistir.".format(int(AKD_KONS_ESIK)))
                # ── Ilk 5 alici / ilk 5 satici tablosu (net tutar + pay) ──
                gt_amt=bg.get("grand_net")
                def _akd_tablo(rows, baslik, poz):
                    if not rows: return ""
                    h=("<div style='font-size:11px;color:#9AA4A0;margin:6px 0 2px'>"+baslik+"</div>"
                       "<table style='width:100%;border-collapse:collapse;font-size:12px'>")
                    for r in rows[:5]:
                        ad=r.get("ad") or r.get("broker") or "?"
                        na=r.get("net_amount")
                        try: naf=float(na)
                        except Exception: naf=None
                        tl=_tl(naf) if naf is not None else "—"
                        ta=r.get("total_amount")
                        try: pay=round(float(ta)/float(bg_gt)*100,1) if bg_gt else None
                        except Exception: pay=None
                        renk="#4FB8A4" if poz else "#D2715A"
                        h+=("<tr><td style='padding:2px 0'>{a}</td>"
                            "<td style='text-align:right;color:{c}'>{t}</td>"
                            "<td style='text-align:right;color:#9AA4A0'>{p}</td></tr>").format(
                                a=ad,c=renk,t=tl,p=("%"+str(pay) if pay is not None else "—"))
                    return h+"</table>"
                try: bg_gt=float(bg.get("grand_total_amount") or 0) or float(akd_hisse(sec["tk"]).get("grand_total_amount") or 0)
                except Exception: bg_gt=0
                ta1=_akd_tablo(bg.get("alici"),"\u25B2 Ilk 5 net ALICI (net tutar &middot; hacim payi)",True)
                ta2=_akd_tablo(bg.get("satici"),"\u25BC Ilk 5 net SATICI (net tutar &middot; hacim payi)",False)
                if ta1 or ta2:
                    tcol1,tcol2=st.columns(2)
                    if ta1: tcol1.markdown(ta1,unsafe_allow_html=True)
                    if ta2: tcol2.markdown(ta2,unsafe_allow_html=True)
            else:
                st.caption("Bu hisse icin ForInvest AKD snapshot'i yok (akd_takas.json) — 6 bayragi elle gir.")
            st.caption("Asagidaki 6 bayrak ForInvest/takas verisi ister. "
                       "'Bilmiyorum' birakirsan tuzak SAYILMAZ ama TEMIZ de sayilmaz (kor nokta).")
            secenek=["— bilmiyorum —","Temiz","\U0001F534 Tuzak (yaniyor)"]
            harita={"— bilmiyorum —":"bilinmiyor","Temiz":"temiz","\U0001F534 Tuzak (yaniyor)":"yanan"}
            ters={"bilinmiyor":0,"temiz":1,"yanan":2}
            manuel={}
            mc1,mc2=st.columns(2)
            for idx,(k,ad,ipucu) in enumerate(MANUEL_BAYRAK):
                kol=mc1 if idx%2==0 else mc2
                on=ters.get(akd_oto.get(k,"bilinmiyor"),0)   # AKD on-dolum (yoksa bilmiyorum)
                etiket=ad+(" \U0001F4E1" if k in akd_oto else "")
                sv=kol.selectbox(etiket,secenek,index=on,key="tz_"+sec["tk"]+"_"+k,help=ipucu)
                manuel[k]=harita[sv]
            birl=tuzak_birlesik(oto_t,manuel)
            renk_hex={"rust":"#D2715A","amber":"#E0A458","teal":"#4FB8A4"}.get(birl["renk"],"#9AA4A0")
            bos=10-birl["degerlendirilen"]
            st.markdown(
                "<div style='border-left:3px solid {c};padding:10px 14px;background:rgba(255,255,255,.02);"
                "border-radius:4px;margin-top:6px'>"
                "<b style='color:{c}'>Tuzak profili: {y}/10 bayrak yandi — {k}</b><br>"
                "<span style='color:#9AA4A0;font-size:12px'>Oto {oy}/4 + manuel {my}/6 \u00b7 "
                "degerlendirilen {dg}/10 ({bos} bayrak veri girilmedi).</span></div>".format(
                    c=renk_hex,y=birl["yanan"],k=birl["kategori"],oy=birl["oto_yanan"],
                    my=birl["man_yanan"],dg=birl["degerlendirilen"],bos=bos),
                unsafe_allow_html=True)
            if birl["yanan"]>=3:
                st.error("3+ bayrak yandi — klasik tuzak profili. 'Neden ALMAMALIYIM' sorusunun cevabi guclu.")
            elif birl["degerlendirilen"]<5:
                st.caption("Profilin yarisindan azi dolduruldu — ForInvest/takas verisini girmeden 'temiz' diyemeyiz.")
            st.caption("Ters matematik: kazanani bilemeyiz, ama tuzagi bu 10 bayrakla isaretleyebiliriz. "
                       "Bu bir 'satma' emri DEGIL; karar (ve katalizor) sende.")

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
    st.markdown("---")
    st.subheader("\U0001F4D0 Kalibrasyon — sistem kendi sinyallerini siniyor")
    st.caption("Her sinyalin (akis yuklenmesi, tuzak, risk, MA kesisimi) ima ettigi yon "
               "{} gun sonra TUTTU MU? Placebo = %50 (rastgele). Isabet placebo'ya yakinsa "
               "o sinyal YON VERMIYOR demektir — ve Guven skorunu asagi ceker. "
               "Bu tahmin DEGIL, oz-denetim.".format(KALIB_UFUK))
    _koz = kalibrasyon_ozet()
    if not _koz or not _koz.get("sinyaller"):
        _ack = (_koz or {}).get("acik_kayit", 0)
        st.info("Defter henuz bos ya da kapanmis kayit yok. Her gun sinyaller kaydedilir, "
                "{} gun sonra sonuclanir; isabet birikince burada durustce gosterilir. "
                "{} acik (vadesi dolmamis) kayit var. UYDURMA YOK — veri gelene kadar yargi yok.".format(
                    KALIB_UFUK, _ack))
    else:
        renk={"placebo":"#D2715A","yetersiz":"#9AA4A0","izlenmeli":"#E0A458","aday":"#4FB8A4"}
        ti=_koz["toplam_isabet"]; tet=_koz["toplam_etiket"]
        st.markdown("<div style='border-left:3px solid {c};padding:10px 14px;background:rgba(255,255,255,.02);"
                    "border-radius:4px'><b style='color:{c}'>TOPLAM isabet: {i} &nbsp;(placebo %50) &middot; {et}</b>"
                    "<br><span style='color:#9AA4A0;font-size:12px'>{n} kapali kayit \u00b7 {a} acik \u00b7 {ac}</span></div>".format(
                        c=renk.get(tet,"#9AA4A0"),
                        i=("%"+str(ti) if ti is not None else "—"),
                        et=tet.upper(),n=_koz["toplam_n"],a=_koz["acik_kayit"],ac=_koz["toplam_aciklama"]),
                    unsafe_allow_html=True)
        for sg in _koz["sinyaller"]:
            c=renk.get(sg["etiket"],"#9AA4A0")
            st.markdown("<div style='font-size:13px;margin:4px 0'>"
                        "<b style='color:{c}'>{s}</b> &middot; isabet <b>%{i}</b> "
                        "<span style='color:#9AA4A0'>(N={n} \u00b7 {et}) — {ac}</span></div>".format(
                            c=c,s=sg["sinyal"],i=sg["isabet"],n=sg["n"],et=sg["etiket"],ac=sg["aciklama"]),
                        unsafe_allow_html=True)
        st.caption("Hatirla: yuzde ne derse ona uyariz. 'Placebo' diyen sinyale guvenmeyiz — fikir bizim olsa bile.")

    with st.expander("Durustluk · sayilar nereden? ({})".format(SURUM)):
        st.write("{} hisse listede · {} tanesi canli veriyle dolu.".format(len(data['stocks']),data['n_veri']))
        st.write("Guven kerterizi amber cunku getiri ekseni ~yazi-tura. Poz = hisse-basi vol-target. "
                 "Stop = ATR(14)×{}. 4 oto + 6 manuel tuzak bayragi tek 10/10 profilde. "
                 "Havuz RISK sutunu = kacinma skoru (dusus 0.55 + tuzak 0.30 + RSI/vol 0.15, yon icermez). "
                 "Hisse-bazi 'gecmis isabet' sayisi uydurmaydi, kaldirildi. Canli veri yoksa fiyat UYDURULMAZ.".format(ATR_K_STOP))

import sys as _sys
if "streamlit" in _sys.modules:
    run_streamlit()
elif __name__=="__main__":
    if len(_sys.argv) > 1 and _sys.argv[1] == "kalib":
        # CRON GIRISI: bugunun sinyallerini kaydet + vadesi dolanlari sonuclandir.
        # Calistir:  python app.py kalib   (ardindan git add -A && commit && push)
        data = build_app_data()
        bugun = datetime.date.today()
        eklendi = kalibrasyon_kaydet(bugun, data)
        fiyatlar = {s["tk"]: s["px"] for s in data["stocks"] if s.get("veri")}
        kapatildi = kalibrasyon_sonuclandir(bugun, fiyatlar)
        oz = kalibrasyon_ozet() or {}
        print("KALIB {} · {} · +{} yeni sinyal · {} kapatildi · toplam N={} · acik={} · isabet={}".format(
            SURUM, bugun.isoformat(), eklendi, kapatildi,
            oz.get("toplam_n", 0), oz.get("acik_kayit", 0),
            ("%"+str(oz.get("toplam_isabet")) if oz.get("toplam_isabet") is not None else "—")))
    else:
        out,data=write_html()
        print("OK {} · {} · {} hisse ({} canli) · rejim {} · kerteriz {}/100".format(
            out,SURUM,len(data['stocks']),data['n_veri'],data['rejim']['durus'],data['merkez']))
