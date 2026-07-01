#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
APEX — skor_motoru.py · BAGIMSIZ Guven Skoru motoru + skor karne kaydedici

Streamlit YOK. veri.py ile tam fiyat serisi ceker. Sanal Borsa'daki apex_skor ile
AYNI mantik (tek dogru kaynak hedefi). Cron her is gunu calisir:

  python skor_motoru.py

  1) Bugun TUM BIST100 hisselerinin Guven Skorunu (0-100) muhurler -> skor_defteri.csv
     (hisse, skor, durum, giris, stop, hedef; hepsi, sonuc alanlari bos baslar).
  2) Vadesi (~10 islem gunu) dolan muhurleri sonuclandirir: kurulum HEDEFE mi ulasti
     yoksa STOP'a mi degdi (kurulumun kendi mantigi icinde "tuttu mu").

FELSEFE: Skor bir YON tahmini DEGIL — kurulumun ne kadar SAGLAM durdugu. Karne
"yuksek skor gercekten daha cok mu tuttu" sorusunu olcer (skorun kalibrasyonu).
UYDURMA YOK: veri/kayit yoksa bos. Cron COKMEZ (her hata yutulur, exit 0).
"""
import csv
import datetime
import math
import pathlib
import random
import sys

# ── BIST100 (Sanal Borsa TK_DEF ile AYNI sira — seed/index tutarliligi icin) ──
TK = [
    "AEFES","AGHOL","AKBNK","AKCNS","AKFGY","AKSA","AKSEN","ALARK","ALFAS","ARCLK",
    "ASELS","ASTOR","BERA","BIMAS","BRSAN","BRYAT","BUCIM","CCOLA","CIMSA","DOAS",
    "DOHOL","ECILC","EGEEN","EKGYO","ENJSA","ENKAI","EREGL","EUPWR","FROTO","GARAN",
    "GESAN","GUBRF","HALKB","HEKTS","ISCTR","ISGYO","ISMEN","IZMDC","KAYSE","KCHOL",
    "KONTR","KONYA","KORDS","KRDMD","MAVI","MGROS","MIATK","ODAS",
    "OTKAR","OYAKC","PETKM","PGSUS","PSGYO","QUAGR","SAHOL","SASA","SISE","SKBNK",
    "SMRTG","SOKM","TAVHL","TCELL","THYAO","TKFEN","TOASO","TTKOM","TTRAK","TUKAS",
    "TUPRS","ULKER","VAKBN","VESBE","VESTL","YKBNK","ZOREN","ALBRK","ANSGR","ARDYZ",
    "BFREN","CANTE","CWENE","DAPGM","ENERY","FENER","GENIL","GLYHO","IZINS","KMPUR",
    "MPARK","PAPIL","REEDR","TABGD","TSKB","TUREX","YEOTK","YYLGD","ZRGYO",
]
_IDX = {k: i for i, k in enumerate(TK)}

COM = 0.002       # tek yon komisyon
UFUK = 10         # kurulum vadesi (islem gunu)
PENCERE = 260     # skor icin son N gun (Sanal Borsa ile ayni)

# ══════════════════════════════════════════════════════════════
# SAF SKOR FONKSIYONLARI — Sanal Borsa ile BIREBIR (D[k] -> PX parametresi)
# ══════════════════════════════════════════════════════════════
def _sma(a, w):
    out = []
    for i in range(len(a)):
        seg = a[max(0, i - w + 1):i + 1]
        out.append(sum(seg) / len(seg))
    return out

def _rsi(p, per=14):
    r = [None] * len(p)
    if len(p) <= per: return r
    g = l = 0.0
    for i in range(1, per + 1):
        d = p[i] - p[i - 1]
        if d > 0: g += d
        else: l -= d
    ag = g / per; al = l / per
    r[per] = 100 - 100 / (1 + (ag / al if al else 100))
    for i in range(per + 1, len(p)):
        d = p[i] - p[i - 1]
        ag = (ag * (per - 1) + (d if d > 0 else 0)) / per
        al = (al * (per - 1) + (-d if d < 0 else 0)) / per
        r[i] = 100 - 100 / (1 + (ag / al if al else 100))
    return r

def _vol(PX, t):
    rr = [PX[i] / PX[i - 1] - 1 for i in range(max(1, t - 60), t)]
    if not rr: return 0.3
    m = sum(rr) / len(rr)
    return math.sqrt(sum((x - m) ** 2 for x in rr) / len(rr)) * math.sqrt(252)

def _atr(PX, t, per=14):
    s = max(1, t - per + 1)
    trs = [abs(PX[i] - PX[i - 1]) for i in range(s, t + 1)]
    return sum(trs) / len(trs) if trs else PX[t] * 0.02

def _pivot(PX, gun, look=70, w=4):
    a = max(w, gun - look); b = gun; sup = []; res = []
    for i in range(a + w, b - w):
        seg = PX[i - w:i + w + 1]
        if PX[i] == min(seg): sup.append(PX[i])
        if PX[i] == max(seg): res.append(PX[i])
    return sup, res

def _sd(PX, gun):
    f = PX[gun]; atr = _atr(PX, gun); sup, res = _pivot(PX, gun)
    alt = [v for v in sup if v <= f]; ust = [v for v in res if v >= f]
    destek = max(alt) if alt else f - 2 * atr
    direnc = min(ust) if ust else f + 2 * atr
    if destek >= f: destek = f - 2 * atr
    if direnc <= f: direnc = f + 2 * atr
    return destek, direnc, atr

def _giris(f, destek, atr):
    return (destek <= f <= destek + 0.6 * atr) or abs(f - destek) <= 0.4 * atr

def _plan(PX, MA50, RSI, gun):
    f = PX[gun]; ma50 = MA50[gun]; rsi = RSI[gun]
    destek, direnc, atr = _sd(PX, gun); yvol = _vol(PX, gun)
    getiriler = [abs(PX[i] / PX[i - 1] - 1) for i in range(max(1, gun - 20), gun)]
    ort_h = sum(getiriler) / len(getiriler) if getiriler else 0.02
    son_h = abs(PX[gun] / PX[gun - 1] - 1) if gun > 0 else 0
    anormal = (son_h > 3.0 * ort_h) or (yvol > 0.80)
    g_orta = destek + 0.3 * atr
    stop = destek - 1.0 * atr; hedef = direnc
    risk = g_orta - stop; odul = hedef - g_orta
    rr = odul / risk if risk > 0 else 0
    stop_mesafe = (g_orta - stop) / g_orta if g_orta else 1
    risk_gecti = (yvol < 0.70) and (rr >= 1.0) and (stop_mesafe < 0.15)
    dirence_yakin = abs(f - direnc) / direnc < 0.015
    destek_altinda = f < destek - 0.5 * atr
    giriste = _giris(f, destek, atr)
    if anormal: durum = "ANORMAL"
    elif destek_altinda: durum = "STOP"
    elif dirence_yakin: durum = "KAR_ALMA"
    elif giriste and not risk_gecti: durum = "RISK_FILTRE"
    elif giriste and risk_gecti: durum = "GIRIS_AKTIF"
    else: durum = "BEKLE"
    return dict(durum=durum, f=f, g_orta=g_orta, stop=stop, hedef=hedef, rr=rr)

def _kurulum(PX, seed_k=0, ufuk=UFUK):
    N = len(PX); gecerli = list(range(80, N - ufuk))
    def _sonuc(t):
        destek, direnc, atr = _sd(PX, t); f = PX[t]
        stop = destek - 1.0 * atr; hedef = direnc; risk_o = (f - stop) / f
        if risk_o <= 0 or hedef <= f: return None
        cikis = PX[t + ufuk]; tip = "belirsiz"
        for j in range(t + 1, t + ufuk + 1):
            if PX[j] <= stop: cikis = stop; tip = "stop"; break
            if PX[j] >= hedef: cikis = hedef; tip = "hedef"; break
        return ((cikis - f) / f - 2 * COM) / risk_o, tip
    hedef_s = stop_s = 0; R = []
    for t in gecerli:
        destek, direnc, atr = _sd(PX, t); f = PX[t]
        if not _giris(f, destek, atr): continue
        r = _sonuc(t)
        if r is None: continue
        Rv, tip = r
        if tip == "hedef": hedef_s += 1
        elif tip == "stop": stop_s += 1
        R.append(Rv)
    n = len(R); exp = sum(R) / n if n else 0
    _r = random.Random(seed_k * 7 + 1); plc = []
    if gecerli:
        for _ in range(min(max(n * 4, 40), 300)):
            r = _sonuc(_r.choice(gecerli))
            if r: plc.append(r[0])
    placebo = sum(plc) / len(plc) if plc else 0
    edge = exp - placebo
    tot = hedef_s + stop_s; isabet = round(hedef_s / tot * 100) if tot else 0
    return dict(n=n, kapanan=tot, isabet=isabet, edge=edge)

def guven_skor(PX, MA50, RSI, gun, seed_k=0):
    """Sanal Borsa apex_skor ile AYNI 0-100 skor + muhurlenecek plan rakamlari."""
    p = _plan(PX, MA50, RSI, gun); ka = _kurulum(PX, seed_k)
    dp = {"GIRIS_AKTIF": 25, "KAR_ALMA": 15, "BEKLE": 13, "RISK_FILTRE": 9, "STOP": 5, "ANORMAL": 4}.get(p["durum"], 10)
    if ka["kapanan"] < 8: gp = 8.0
    else: gp = max(2.0, min(25.0, (ka["isabet"] - 30) / 40 * 25))
    rr = p["rr"]
    if rr < 1: rp = 6
    elif rr < 1.5: rp = 12
    elif rr <= 3: rp = 25
    elif rr <= 5: rp = 18
    else: rp = 11
    if ka["n"] < 10: ep = 8
    elif ka["edge"] > 0.15: ep = 25
    elif ka["edge"] > 0.05: ep = 16
    elif ka["edge"] > -0.05: ep = 9
    else: ep = 3
    toplam = round(dp + gp + rp + ep)
    return dict(skor=toplam, durum=p["durum"], giris=p["g_orta"],
                stop=p["stop"], hedef=p["hedef"], rr=rr)

# ══════════════════════════════════════════════════════════════
# VERI CEKIMI (veri.py — tam seri, Sanal Borsa gibi)
# ══════════════════════════════════════════════════════════════
def _cek_tum():
    """{kod: (Close listesi, tarih_iso listesi)} — son PENCERE gun. Cekilemezse {}."""
    try:
        from veri import veri_al
    except Exception as e:
        print("veri.py yok:", e); return {}
    from concurrent.futures import ThreadPoolExecutor

    def _one(kod):
        try:
            df, _ = veri_al(kod, gun=430, min_gun=120, aralik="1d")
            if df is not None and len(df) >= 120:
                c = [float(x) for x in df["Close"].tolist()][-PENCERE:]
                t = [str(d)[:10] for d in df.index][-PENCERE:]
                if len(c) >= 120:
                    return kod, (c, t)
        except Exception:
            pass
        return kod, None

    out = {}
    with ThreadPoolExecutor(max_workers=10) as ex:
        for kod, v in ex.map(_one, TK):
            if v:
                out[kod] = v
    return out

# ══════════════════════════════════════════════════════════════
# MUHURLEME + SONUCLANDIRMA (kalibrasyon deseninin kardesi)
# ══════════════════════════════════════════════════════════════
SKOR_CSV = pathlib.Path("skor_defteri.csv")
SKOR_BASLIK = ["tarih", "hisse", "skor", "durum", "giris", "stop", "hedef",
               "ufuk", "sonuc_tarih", "cikis", "sonuc", "tuttu"]

def _oku():
    if not SKOR_CSV.exists(): return []
    try:
        with open(SKOR_CSV, encoding="utf-8") as f:
            return list(csv.DictReader(f))
    except Exception:
        return []

def _yaz(rows):
    with open(SKOR_CSV, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=SKOR_BASLIK); w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in SKOR_BASLIK})

def skor_muhurle(bugun, seriler):
    """Bugun TUM hisselerin skorunu ACIK kayit olarak ekle (idempotent). Eklenen sayi doner."""
    bugun = bugun.isoformat() if hasattr(bugun, "isoformat") else str(bugun)
    rows = _oku(); mevcut = set((r.get("tarih"), r.get("hisse")) for r in rows)
    yeni = 0
    for kod, (c, t) in seriler.items():
        if (bugun, kod) in mevcut: continue
        MA50 = _sma(c, 50); RSI = _rsi(c, 14); gun = len(c) - 1
        try:
            sk = guven_skor(c, MA50, RSI, gun, seed_k=_IDX.get(kod, 0))
        except Exception:
            continue
        rows.append({"tarih": bugun, "hisse": kod, "skor": sk["skor"], "durum": sk["durum"],
                     "giris": round(sk["giris"], 4), "stop": round(sk["stop"], 4),
                     "hedef": round(sk["hedef"], 4), "ufuk": UFUK,
                     "sonuc_tarih": "", "cikis": "", "sonuc": "", "tuttu": ""})
        yeni += 1
    _yaz(rows)
    return yeni

def skor_sonuclandir(seriler):
    """Vadesi dolan ACIK muhurleri sonuclandir: kurulum HEDEFE mi STOP'a mi degdi.
    Muhur gununden sonraki ufuk gunluk pencerede once hangisine deger -> tuttu (1/0)."""
    rows = _oku()
    if not rows: return 0
    kapatilan = 0
    for r in rows:
        if (r.get("tuttu") or "") != "": continue
        kod = r.get("hisse")
        if kod not in seriler: continue
        c, t = seriler[kod]
        mt = r.get("tarih")
        try:
            giris = float(r["giris"]); stop = float(r["stop"]); hedef = float(r["hedef"]); uf = int(r["ufuk"])
        except Exception:
            continue
        if mt not in t: continue          # muhur gunu bu pencerede degilse atla
        i0 = t.index(mt); i_end = i0 + uf
        if i_end >= len(c): continue       # vade henuz dolmadi (ileride veri yok)
        cikis = c[i_end]; sonuc = "belirsiz"
        for j in range(i0 + 1, i_end + 1):
            if c[j] <= stop: cikis = stop; sonuc = "stop"; break
            if c[j] >= hedef: cikis = hedef; sonuc = "hedef"; break
        if sonuc == "hedef": tuttu = 1
        elif sonuc == "stop": tuttu = 0
        else: tuttu = 1 if cikis > giris else 0   # belirsiz -> yon
        r["sonuc_tarih"] = t[i_end]; r["cikis"] = round(cikis, 4)
        r["sonuc"] = sonuc; r["tuttu"] = tuttu
        kapatilan += 1
    if kapatilan: _yaz(rows)
    return kapatilan

def main():
    bugun = datetime.date.today()
    seriler = _cek_tum()
    if not seriler:
        print("SKOR: veri cekilemedi, bugun atlandi."); return
    m = skor_muhurle(bugun, seriler)
    k = skor_sonuclandir(seriler)
    print(f"SKOR {bugun.isoformat()} · +{m} yeni muhur · {k} sonuclandi · defterde toplam {len(_oku())} kayit")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"SKOR hata (cron temiz cikar): {e}")
        sys.exit(0)
