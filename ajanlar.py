# -*- coding: utf-8 -*-
"""
═══════════════════════════════════════════════════════════════
ajanlar.py — APEX AJAN KATMANI  (standalone, bağımsız)
═══════════════════════════════════════════════════════════════
Hiçbir mevcut dosyaya BAĞIMLI DEĞİL. Sadece numpy + pandas.
Tek girdi: bir hissenin OHLCV DataFrame'i (Open/High/Low/Close/Volume).
Canlı app.py'yi bozmaz — yalnızca import edilip çağrılır.

İçindeki ajanlar:
  1) grafik_ogretmen(df)   → grafikteki her şeyi AÇIKLAR + O ANKİ durumu okur
  2) kacinilacak_mi(df)    → "buradan düşüş normal mi?" tehlike okuması (tersinden)
  3) projektor(df, gun=5)  → Monte Carlo belirsizlik konisi + stop'a değme olasılığı
  4) risk_parity(adaylar)  → her pozisyon EŞİT risk taşısın diye lot dağıtımı

DÜRÜSTLÜK İLKESİ (değişmez):
  • Hiçbir fonksiyon "şu kadar kazanır" demez. Yön tahmini yok (drift=0).
  • Projektör KEHANET değil — belirsizliğin GENİŞLİĞİDİR.
  • Kaçınılacak ajanı "kesin düşer" demez; "buradan düşüş normal karşılanır" der.
"""

import numpy as np
import pandas as pd


# ══════════════════════════════════════════════════════════════
# ORTAK YARDIMCILAR
# ══════════════════════════════════════════════════════════════
def _ma(close, p):
    return close.rolling(p).mean()


def _atr(df, p=14):
    h, l, c = df["High"], df["Low"], df["Close"]
    onceki = c.shift(1)
    tr = pd.concat([h - l, (h - onceki).abs(), (l - onceki).abs()], axis=1).max(axis=1)
    return tr.rolling(p).mean()


def _son(x, varsayilan=np.nan):
    try:
        v = float(x.iloc[-1])
        return v if not np.isnan(v) else varsayilan
    except Exception:
        return varsayilan


def _kesisim_bul(ma_kisa, ma_uzun):
    """
    MA50/MA200 kesişimlerini bulur.
    Dönen: liste — [{'tip': 'altin'|'olum', 'indeks': i, 'tarih': ts}, ...]
    'altin' = MA50 yukarı keser (golden cross)
    'olum'  = MA50 aşağı keser (death cross)
    """
    k = ma_kisa.values
    u = ma_uzun.values
    idx = ma_kisa.index
    olaylar = []
    for i in range(1, len(k)):
        if np.isnan(k[i]) or np.isnan(u[i]) or np.isnan(k[i - 1]) or np.isnan(u[i - 1]):
            continue
        onceki_fark = k[i - 1] - u[i - 1]
        simdi_fark = k[i] - u[i]
        if onceki_fark <= 0 and simdi_fark > 0:
            olaylar.append({"tip": "altin", "indeks": i, "tarih": idx[i]})
        elif onceki_fark >= 0 and simdi_fark < 0:
            olaylar.append({"tip": "olum", "indeks": i, "tarih": idx[i]})
    return olaylar


# ══════════════════════════════════════════════════════════════
# AJAN 1 — GRAFİK ÖĞRETMEN
# Grafikteki HER ŞEYİ açıklar. Hem ne olduğunu, hem ŞU ANKİ durumu.
# ══════════════════════════════════════════════════════════════
def grafik_ogretmen(df):
    """
    Grafiğin yanında gösterilecek açıklama paketini döner.
    Her madde: {baslik, nedir (statik öğretim), durum (o anki okuma), renk}
    Ayrıca son kesişimi ve 'kaç gün önce' bilgisini verir.
    """
    if df is None or len(df) < 30:
        return {"maddeler": [], "son_kesisim": None, "ozet": "Yeterli veri yok."}

    close = df["Close"]
    son_fiyat = _son(close)
    ma50 = _ma(close, 50)
    ma200 = _ma(close, 200)
    ma50_son = _son(ma50, son_fiyat)
    ma200_son = _son(ma200, son_fiyat)

    maddeler = []

    # — MA50 —
    if son_fiyat >= ma50_son:
        d50 = f"Fiyat MA50'nin ÜSTÜNDE (%{(son_fiyat/ma50_son-1)*100:+.1f}) — kısa vadeli görünüm pozitif."
        r50 = "#10B981"
    else:
        d50 = f"Fiyat MA50'nin ALTINDA (%{(son_fiyat/ma50_son-1)*100:+.1f}) — kısa vadeli görünüm zayıf."
        r50 = "#EF4444"
    maddeler.append({
        "baslik": "MA50 (mavi çizgi)",
        "nedir": "Son 50 günün ortalama kapanış fiyatı. Günlük dalgalanmayı temizler, KISA vadeli yönü gösterir.",
        "durum": d50, "renk": r50,
    })

    # — MA200 —
    if son_fiyat >= ma200_son:
        d200 = f"Fiyat MA200'ün ÜSTÜNDE (%{(son_fiyat/ma200_son-1)*100:+.1f}) — uzun vadeli trend sağlam."
        r200 = "#10B981"
    else:
        d200 = f"Fiyat MA200'ün ALTINDA (%{(son_fiyat/ma200_son-1)*100:+.1f}) — uzun vadeli trend zayıf, dikkat."
        r200 = "#EF4444"
    maddeler.append({
        "baslik": "MA200 (turuncu çizgi)",
        "nedir": "Son 200 günün ortalama kapanış fiyatı. Piyasanın UZUN vadeli ana yönü. Fiyat üstündeyse 'boğa', altındaysa 'ayı' tarafı kabul edilir.",
        "durum": d200, "renk": r200,
    })

    # — Kesişimler —
    olaylar = _kesisim_bul(ma50, ma200)
    son_kesisim = olaylar[-1] if olaylar else None
    if son_kesisim:
        gun_once = len(df) - 1 - son_kesisim["indeks"]
        if son_kesisim["tip"] == "altin":
            dk = (f"En son ALTIN KESİŞİM oldu ({gun_once} gün önce). "
                  "MA50, MA200'ü yukarı kesti — yapısal yükseliş işareti.")
            rk = "#10B981"
        else:
            dk = (f"En son ÖLÜM KESİŞİMİ oldu ({gun_once} gün önce). "
                  "MA50, MA200'ü aşağı kesti — yapısal zayıflık işareti.")
            rk = "#EF4444"
    else:
        dk = "Son dönemde MA50/MA200 kesişimi yok — iki ortalama henüz kesişmedi."
        rk = "#94A3B8"
    maddeler.append({
        "baslik": "Altın / Ölüm Kesişimi (yıldız işaretleri)",
        "nedir": ("ALTIN KESİŞİM: kısa ortalama (MA50) uzun ortalamayı (MA200) AŞAĞIDAN yukarı keser "
                  "→ yükseliş başlangıcı sayılır. ÖLÜM KESİŞİMİ: tam tersi, MA50 MA200'ü yukarıdan "
                  "aşağı keser → düşüş başlangıcı sayılır. Grafikte yıldızla işaretlenir."),
        "durum": dk, "renk": rk,
    })

    # — Projektör konisi açıklaması —
    maddeler.append({
        "baslik": "Projektör (kesik çizgili huni)",
        "nedir": ("Grafiğin SAĞ ucundaki huni, önümüzdeki günlerin OLASI fiyat aralığıdır. "
                  "Yön TAHMİN ETMEZ (ortası düz gider). Sadece 'fiyat nereye kadar sıçrayabilir, "
                  "nereye kadar düşebilir' belirsizliğini gösterir. Huni genişse oynaklık yüksektir."),
        "durum": "Aşağıdaki projektör panelinde 5 günlük olası bant ve stop'a değme olasılığı var.",
        "renk": "#38BDF8",
    })

    # — Özet tek cümle —
    if son_fiyat > ma50_son > ma200_son:
        ozet = "Fiyat her iki ortalamanın da üstünde ve MA50 > MA200 — teknik tablo güçlü/pozitif."
    elif son_fiyat < ma50_son < ma200_son:
        ozet = "Fiyat her iki ortalamanın da altında ve MA50 < MA200 — teknik tablo zayıf/negatif."
    else:
        ozet = "Karışık tablo — fiyat ortalamalar arasında, net bir trend yok. Temkinli izle."

    return {"maddeler": maddeler, "son_kesisim": son_kesisim, "ozet": ozet}


# ══════════════════════════════════════════════════════════════
# AJAN 2 — KAÇINILACAK HİSSE  (tersinden risk okuması)
# "Bu hisse alınmaz" değil → "buradan DÜŞÜŞ normal karşılanır mı?"
# ══════════════════════════════════════════════════════════════
def kacinilacak_mi(df):
    """
    Aşağı yönlü risk sinyallerini toplar. Yukarı tahmininden DAHA dürüsttür:
    düşüş riski, trend bozulması ve oynaklık ölçülebilir.
    Dönen: {tehlike_skoru 0-100, karar, renk, bayraklar[list], aciklama}
    """
    if df is None or len(df) < 60:
        return {"tehlike_skoru": 0, "karar": "VERİ YOK", "renk": "#94A3B8",
                "bayraklar": [], "aciklama": "Yeterli geçmiş veri yok."}

    close = df["Close"]
    son_fiyat = _son(close)
    getiri = close.pct_change().dropna()

    ma50 = _ma(close, 50)
    ma200 = _ma(close, 200)
    ma50_son = _son(ma50, son_fiyat)
    ma200_son = _son(ma200, son_fiyat)

    bayraklar = []
    skor = 0

    # 1) Ölüm kesişimi aktif mi? (MA50 < MA200)
    if ma50_son < ma200_son:
        skor += 30
        bayraklar.append(("Ölüm kesişimi bölgesi", "MA50, MA200'ün altında — yapısal düşüş trendi."))

    # 2) Fiyat MA200 altında mı? (uzun vade kırık)
    if son_fiyat < ma200_son:
        skor += 20
        bayraklar.append(("Uzun vade kırık", "Fiyat MA200'ün altında — ana trend ayı tarafında."))

    # 3) Taze ölüm kesişimi (son 20 gün)
    olaylar = _kesisim_bul(ma50, ma200)
    if olaylar and olaylar[-1]["tip"] == "olum":
        gun_once = len(df) - 1 - olaylar[-1]["indeks"]
        if gun_once <= 20:
            skor += 15
            bayraklar.append(("Taze ölüm kesişimi", f"{gun_once} gün önce ölüm kesişimi oldu — bozulma yeni."))

    # 4) Aşağı yönlü oynaklık yüksek mi? (negatif getirilerin std'si)
    neg = getiri[getiri < 0]
    asagi_vol = float(neg.std() * 100) if len(neg) > 5 else 0.0
    if asagi_vol > 3.5:
        skor += 15
        bayraklar.append(("Yüksek düşüş oynaklığı",
                          f"Düşüş günlerinde günlük ~%{asagi_vol:.1f} oynaklık — sert kayıp riski."))

    # 5) Son 1 ayda alçalan dipler mi? (momentum negatif)
    if len(close) >= 22:
        ay_once = float(close.iloc[-22])
        aylik = (son_fiyat / ay_once - 1) * 100
        if aylik < -8:
            skor += 20
            bayraklar.append(("Negatif momentum", f"Son 1 ayda %{aylik:.1f} — düşüş ivmesi var."))

    skor = int(min(100, skor))

    if skor >= 60:
        karar, renk = "KAÇIN — buradan düşüş normal karşılanır", "#EF4444"
    elif skor >= 30:
        karar, renk = "DİKKATLİ — zayıflık işaretleri var", "#F59E0B"
    else:
        karar, renk = "TEKNİK TABLO TEMİZ — bariz düşüş sinyali yok", "#10B981"

    aciklama = ("Bu skor 'kesin düşer' demez. Geçmiş örüntüye göre buradan AŞAĞI hareketin "
                "ne kadar 'normal/beklenir' olduğunu söyler. Yüksek skor = aşağı risk yüksek.")

    return {"tehlike_skoru": skor, "karar": karar, "renk": renk,
            "bayraklar": bayraklar, "asagi_vol": round(asagi_vol, 2), "aciklama": aciklama}


# ══════════════════════════════════════════════════════════════
# AJAN 3 — PROJEKTÖR  (Monte Carlo, yönsüz)
# Önümüzdeki N günün OLASI fiyat aralığı + stop'a değme olasılığı.
# ══════════════════════════════════════════════════════════════
def projektor(df, gun=5, stop_fiyat=None, yol_sayisi=4000, tohum=42):
    """
    Yönsüz (drift=0) Monte Carlo. Kehanet değil — belirsizliğin genişliği.
    Dönen:
      band: her gün için {gun, alt80, alt50, orta, ust50, ust80}  (fiyat seviyeleri)
      stop_olasilik: stop verilmişse, N gün içinde stop'a değme olasılığı (%)
      gunluk_vol_pct: kullanılan günlük oynaklık
    """
    if df is None or len(df) < 30:
        return {"band": [], "stop_olasilik": None, "gunluk_vol_pct": 0.0}

    close = df["Close"]
    son_fiyat = _son(close)
    log_get = np.log(close / close.shift(1)).dropna()
    sigma = float(log_get.std())  # günlük log-getiri std (yönsüz)
    if np.isnan(sigma) or sigma <= 0:
        sigma = 0.02

    # — Analitik bant (görselleştirme için temiz koni) —
    # log-fiyat ~ Normal(log S0, sigma*sqrt(t)), drift=0
    band = []
    for t in range(1, gun + 1):
        s = sigma * np.sqrt(t)
        band.append({
            "gun": t,
            "alt80": son_fiyat * np.exp(-1.282 * s),  # %80 bandın altı
            "alt50": son_fiyat * np.exp(-0.674 * s),  # %50 bandın altı
            "orta":  son_fiyat,                        # yönsüz → ortası düz
            "ust50": son_fiyat * np.exp(+0.674 * s),
            "ust80": son_fiyat * np.exp(+1.282 * s),
        })

    # — Stop'a değme olasılığı (simülasyon — gün-içi yol önemli) —
    stop_olasilik = None
    if stop_fiyat is not None and stop_fiyat > 0 and stop_fiyat < son_fiyat:
        rng = np.random.default_rng(tohum)
        # yönsüz GBM adımları: exp(sigma*Z - 0.5 sigma^2)  (martingale düzeltmesi)
        adimlar = rng.normal(loc=-0.5 * sigma**2, scale=sigma, size=(yol_sayisi, gun))
        yollar = son_fiyat * np.exp(np.cumsum(adimlar, axis=1))
        degen = (yollar.min(axis=1) <= stop_fiyat).mean()
        stop_olasilik = round(float(degen) * 100, 1)

    return {"band": band, "stop_olasilik": stop_olasilik,
            "gunluk_vol_pct": round(sigma * 100, 2), "son_fiyat": son_fiyat}


# ══════════════════════════════════════════════════════════════
# AJAN 4 — RİSK PARITY  (#12)
# Her pozisyon EŞİT TL risk taşısın diye lot dağıtır.
# Getiriye göre DEĞİL, riske göre ölçekler.
# ══════════════════════════════════════════════════════════════
def risk_parity(adaylar, toplam_risk_butcesi_tl):
    """
    adaylar: [{'kod','fiyat','stop'} ...]  (stop < fiyat olmalı)
    toplam_risk_butcesi_tl: tüm pozisyonların toplamda riske atacağı para.
    Mantık: her pozisyon eşit risk taşır → bütçe / N her birine düşer,
            lot = pozisyon_risk_payı / (fiyat - stop).
    Dönen: [{kod, lot, pozisyon_tl, risk_tl, risk_pay_pct} ...]
    """
    gecerli = []
    for a in adaylar:
        f = a.get("fiyat", 0)
        s = a.get("stop", 0)
        if f > 0 and 0 < s < f:
            gecerli.append({**a, "_risk_pay": f - s})
    if not gecerli or toplam_risk_butcesi_tl <= 0:
        return []

    n = len(gecerli)
    pozisyon_basi_risk = toplam_risk_butcesi_tl / n  # eşit risk = parite

    cikti = []
    for a in gecerli:
        risk_pay = a["_risk_pay"]
        lot = int(pozisyon_basi_risk / risk_pay)
        if lot <= 0:
            lot = 0
        pozisyon_tl = lot * a["fiyat"]
        risk_tl = lot * risk_pay
        cikti.append({
            "kod": a.get("kod", "?"),
            "lot": lot,
            "fiyat": a["fiyat"],
            "stop": a["stop"],
            "pozisyon_tl": round(pozisyon_tl, 2),
            "risk_tl": round(risk_tl, 2),
            "hisse_basi_risk": round(risk_pay, 4),
        })
    return cikti


# ══════════════════════════════════════════════════════════════
# KENDİ KENDİNE TEST (python ajanlar.py)
# ══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    # Sahte ama gerçekçi OHLCV üret
    rng = np.random.default_rng(7)
    n = 300
    getiriler = rng.normal(0.0005, 0.02, n)
    kapanis = 100 * np.exp(np.cumsum(getiriler))
    idx = pd.date_range("2024-01-01", periods=n, freq="D")
    df = pd.DataFrame({
        "Open": kapanis * (1 + rng.normal(0, 0.003, n)),
        "High": kapanis * (1 + np.abs(rng.normal(0, 0.01, n))),
        "Low":  kapanis * (1 - np.abs(rng.normal(0, 0.01, n))),
        "Close": kapanis,
        "Volume": rng.integers(1e6, 5e6, n),
    }, index=idx)

    print("═" * 55)
    print("AJAN 1 — GRAFİK ÖĞRETMEN")
    g = grafik_ogretmen(df)
    print("ÖZET:", g["ozet"])
    for m in g["maddeler"]:
        print(f"  • {m['baslik']}: {m['durum']}")

    print("═" * 55)
    print("AJAN 2 — KAÇINILACAK MI")
    k = kacinilacak_mi(df)
    print(f"  Tehlike skoru: {k['tehlike_skoru']}/100 → {k['karar']}")
    for ad, ac in k["bayraklar"]:
        print(f"    - {ad}: {ac}")

    print("═" * 55)
    print("AJAN 3 — PROJEKTÖR (5 gün)")
    son = float(df["Close"].iloc[-1])
    stop = son * 0.95
    p = projektor(df, gun=5, stop_fiyat=stop)
    print(f"  Günlük oynaklık: %{p['gunluk_vol_pct']}  | Son fiyat: {son:.2f}")
    for b in p["band"]:
        print(f"    Gün {b['gun']}: %80 bant [{b['alt80']:.2f} .. {b['ust80']:.2f}]")
    print(f"  Stop'a ({stop:.2f}) değme olasılığı (5 gün): %{p['stop_olasilik']}")

    print("═" * 55)
    print("AJAN 4 — RİSK PARITY")
    adaylar = [
        {"kod": "A_DUSUKVOL", "fiyat": 100, "stop": 97},
        {"kod": "B_ORTAVOL",  "fiyat": 50,  "stop": 46},
        {"kod": "C_YUKSEKVOL","fiyat": 20,  "stop": 17},
    ]
    rp = risk_parity(adaylar, toplam_risk_butcesi_tl=3000)
    for r in rp:
        print(f"    {r['kod']}: {r['lot']} lot | pozisyon {r['pozisyon_tl']}₺ | risk {r['risk_tl']}₺")
    print("  → Dikkat: her pozisyonun RİSK'i ~eşit, pozisyon TL'leri farklı. Parite budur.")
