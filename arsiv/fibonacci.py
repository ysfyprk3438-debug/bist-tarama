"""
═══════════════════════════════════════════════════════════════
FİBONACCİ & PİVOT SEVİYELERİ — BIST Para Avcısı v4
═══════════════════════════════════════════════════════════════
Hacim profili paranın döndüğü yerleri gösterir. Bu modül onu
MATEMATİKSEL seviyelerle tamamlar — binlerce traderın izlediği,
bu yüzden kendini gerçekleştiren destek/direnç noktaları.

  PİVOT NOKTALARI → günlük/haftalık referans (floor trader pivots)
    P, R1/R2 (direnç), S1/S2 (destek)

  FİBONACCİ → son salınımın geri çekilme seviyeleri
    %23.6, %38.2, %50, %61.8, %78.6
    Yükselişte → pullback alım bölgeleri (destek)
    Düşüşte → satış/dönüş bölgeleri (direnç)

GÜÇ ONAYı: İki bağımsız yöntem (hacim + matematik) aynı fiyata
işaret ediyorsa, o seviye gerçekten güçlüdür. Sistem bunu yakalar.
"""

import numpy as np


def pivot_seviyeleri(df, pencere=20):
    """
    Floor trader pivot noktaları (son 'pencere' barın H/L/C'sinden).
    Dönen: {pivot, r1, r2, s1, s2}
    """
    if df is None or len(df) < 5:
        return None
    son = df.iloc[-pencere:] if len(df) > pencere else df
    H = float(son["High"].max())
    L = float(son["Low"].min())
    C = float(df["Close"].iloc[-1])

    P = (H + L + C) / 3
    return {
        "pivot": round(P, 2),
        "r1": round(2 * P - L, 2),
        "r2": round(P + (H - L), 2),
        "s1": round(2 * P - H, 2),
        "s2": round(P - (H - L), 2),
    }


def fibonacci_seviyeleri(df, pencere=90):
    """
    Son salınımın (pencere içindeki en yüksek-en düşük) Fibonacci
    geri çekilme seviyeleri.
    Dönen: {yon, seviyeler: [(oran, fiyat, etiket)], swing_high, swing_low}
    """
    if df is None or len(df) < 20:
        return None
    son = df.iloc[-pencere:] if len(df) > pencere else df
    kapanis = son["Close"]

    swing_high = float(kapanis.max())
    swing_low = float(kapanis.min())
    if swing_high <= swing_low:
        return None

    # Yön: zirve mi dip mi daha yakın zamanda? (trend yönü)
    high_idx = kapanis.idxmax()
    low_idx = kapanis.idxmin()
    yukselis = low_idx < high_idx  # dip önce geldiyse yükseliş trendi

    fark = swing_high - swing_low
    oranlar = [0.236, 0.382, 0.5, 0.618, 0.786]
    seviyeler = []
    for o in oranlar:
        # Yükselişte: tepeden aşağı geri çekilme (destek bölgeleri)
        fiyat = swing_high - fark * o
        seviyeler.append((o, round(fiyat, 2), f"%{o*100:.1f}"))

    return {
        "yon": "yükseliş" if yukselis else "düşüş",
        "seviyeler": seviyeler,
        "swing_high": round(swing_high, 2),
        "swing_low": round(swing_low, 2),
    }


def matematiksel_seviyeler(df, hacim_poc=None):
    """
    Pivot + Fibonacci'yi birleştirir, fiyata en yakın destek/direnci bulur.
    hacim_poc: hacim profilinden POC (varsa, onay kontrolü için)
    Dönen: {pivot, fib, yakin_destek, yakin_direnc, hacim_onayi}
    """
    piv = pivot_seviyeleri(df)
    fib = fibonacci_seviyeleri(df)
    if not piv and not fib:
        return None

    fiyat = float(df["Close"].iloc[-1])

    # Tüm seviyeleri topla (kaynak etiketiyle)
    tum = []
    if piv:
        tum += [("Pivot", piv["pivot"]), ("R1", piv["r1"]), ("R2", piv["r2"]),
                ("S1", piv["s1"]), ("S2", piv["s2"])]
    if fib:
        for o, f, et in fib["seviyeler"]:
            tum.append((f"Fib {et}", f))

    # Fiyatın altındakiler = destek, üstündekiler = direnç
    destekler = [(ad, f) for ad, f in tum if f < fiyat]
    direncler = [(ad, f) for ad, f in tum if f > fiyat]

    yakin_destek = max(destekler, key=lambda x: x[1]) if destekler else None
    yakin_direnc = min(direncler, key=lambda x: x[1]) if direncler else None

    # Hacim onayı: POC bir matematiksel seviyeye çok yakınsa, güçlü onay
    hacim_onayi = None
    if hacim_poc:
        for ad, f in tum:
            if f > 0 and abs(f - hacim_poc) / f < 0.015:  # %1.5 içinde
                hacim_onayi = {
                    "seviye": ad, "fiyat": f,
                    "mesaj": f"💪 {ad} ({f}₺) hacim yoğunluğuyla (POC) örtüşüyor — çok güçlü seviye.",
                }
                break

    return {
        "pivot": piv,
        "fib": fib,
        "yakin_destek": yakin_destek,
        "yakin_direnc": yakin_direnc,
        "hacim_onayi": hacim_onayi,
    }
