"""
═══════════════════════════════════════════════════════════════
HACİM PROFİLİ & VWAP — BIST Para Avcısı v4 (Kurumsal Seviyeler)
═══════════════════════════════════════════════════════════════
Derin gerçek: Gerçek destek/direnç, fiyatın en yüksek/düşük noktası
DEĞİL — PARANIN en çok döndüğü seviyelerdir. Oralar mıknatıs gibidir.

Kurumsal masaların referansı:
  VWAP → hacim ağırlıklı ortalama fiyat. "Adil değer".
         Fiyat üstünde = alıcılar kontrolde, altında = satıcılar.
  POC  → en çok işlem gören fiyat. En güçlü mıknatıs/destek.
  DEĞER ALANI → işlemlerin %70'inin döndüğü bölge. "Adil aralık".

Bu, basit destek/direnci kurumsal seviyelerle güçlendirir:
  - Daha güvenilir giriş/çıkış noktaları
  - "Fiyat değer alanının üstünde, boşlukta, hızlı hareket edebilir"
  - Karar motoruna yapısal bilgi besler
"""

import numpy as np
import pandas as pd


# ══════════════════════════════════════════════════════════════
# VWAP — hacim ağırlıklı ortalama fiyat (adil değer)
# ══════════════════════════════════════════════════════════════
def vwap_hesapla(df, periyot=20):
    """
    Rolling VWAP. Fiyatın VWAP'a göre konumu = alıcı/satıcı kontrolü.
    Dönen: {vwap, konum, fark_pct, renk, aciklama}
    """
    if df is None or len(df) < periyot:
        return None
    tipik = (df["High"] + df["Low"] + df["Close"]) / 3
    pv = tipik * df["Volume"]
    vwap_seri = pv.rolling(periyot).sum() / (df["Volume"].rolling(periyot).sum() + 1e-10)
    vwap = float(vwap_seri.iloc[-1])
    fiyat = float(df["Close"].iloc[-1])
    if vwap <= 0:
        return None
    fark_pct = (fiyat - vwap) / vwap * 100

    if fark_pct > 1:
        konum, renk = "VWAP ÜSTÜ", "#10B981"
        aciklama = f"Fiyat VWAP'ın %{fark_pct:.1f} üstünde — alıcılar kontrolde."
    elif fark_pct < -1:
        konum, renk = "VWAP ALTI", "#EF4444"
        aciklama = f"Fiyat VWAP'ın %{abs(fark_pct):.1f} altında — satıcılar kontrolde."
    else:
        konum, renk = "VWAP'TA", "#94A3B8"
        aciklama = "Fiyat VWAP'a yakın — denge bölgesi, yön belirsiz."

    return {"vwap": round(vwap, 2), "konum": konum, "fark_pct": round(fark_pct, 1),
            "renk": renk, "aciklama": aciklama}


# ══════════════════════════════════════════════════════════════
# HACİM PROFİLİ — paranın en çok döndüğü seviyeler
# ══════════════════════════════════════════════════════════════
def hacim_profili(df, bin_sayisi=24, son_gun=120):
    """
    Fiyat aralığını binlere böler, her bine düşen hacmi toplar.
    POC (en çok işlem gören fiyat) ve değer alanını (%70 hacim) bulur.
    Dönen: {poc, va_ust, va_alt, profil, konum, aciklama}
    """
    if df is None or len(df) < 30:
        return None
    pencere = df.iloc[-son_gun:] if len(df) > son_gun else df
    fiyatlar = pencere["Close"].values
    hacimler = pencere["Volume"].values

    dusuk, yuksek = float(fiyatlar.min()), float(fiyatlar.max())
    if yuksek <= dusuk:
        return None

    # Binlere hacim dağıt
    hacim_bin = np.zeros(bin_sayisi)
    bin_genislik = (yuksek - dusuk) / bin_sayisi
    for f, h in zip(fiyatlar, hacimler):
        idx = min(int((f - dusuk) / (yuksek - dusuk) * bin_sayisi), bin_sayisi - 1)
        hacim_bin[idx] += h

    toplam_hacim = hacim_bin.sum()
    if toplam_hacim <= 0:
        return None

    # POC — en yüksek hacimli bin
    poc_idx = int(np.argmax(hacim_bin))
    poc = dusuk + (poc_idx + 0.5) * bin_genislik

    # Değer Alanı — POC'tan başlayıp %70 hacme ulaşana kadar genişlet
    hedef_hacim = toplam_hacim * 0.70
    secili = {poc_idx}
    biriken = hacim_bin[poc_idx]
    alt, ust = poc_idx, poc_idx
    while biriken < hedef_hacim and (alt > 0 or ust < bin_sayisi - 1):
        # Hangi yöne genişlemek daha çok hacim ekler?
        alt_hacim = hacim_bin[alt - 1] if alt > 0 else -1
        ust_hacim = hacim_bin[ust + 1] if ust < bin_sayisi - 1 else -1
        if ust_hacim >= alt_hacim:
            ust += 1
            biriken += hacim_bin[ust]
            secili.add(ust)
        else:
            alt -= 1
            biriken += hacim_bin[alt]
            secili.add(alt)

    va_alt = dusuk + min(secili) * bin_genislik
    va_ust = dusuk + (max(secili) + 1) * bin_genislik

    # Fiyatın değer alanına göre konumu
    fiyat = float(df["Close"].iloc[-1])
    if fiyat > va_ust:
        konum, renk = "DEĞER ÜSTÜ", "#10B981"
        aciklama = "Fiyat değer alanının üstünde — boşlukta, momentum güçlü ama destek uzak."
    elif fiyat < va_alt:
        konum, renk = "DEĞER ALTI", "#EF4444"
        aciklama = "Fiyat değer alanının altında — ucuz bölge ama zayıf, dikkat."
    else:
        konum, renk = "DEĞER İÇİ", "#38BDF8"
        aciklama = "Fiyat adil değer aralığında — denge, kırılım yönü izlenmeli."

    return {
        "poc": round(poc, 2),
        "va_ust": round(va_ust, 2),
        "va_alt": round(va_alt, 2),
        "konum": konum, "renk": renk, "aciklama": aciklama,
        "poc_mesafe_pct": round((fiyat - poc) / poc * 100, 1) if poc > 0 else 0,
    }


# ══════════════════════════════════════════════════════════════
# BİRLEŞİK HACİM YAPISI — VWAP + Profil tek değerlendirmede
# ══════════════════════════════════════════════════════════════
def hacim_yapisi(df):
    """
    VWAP + hacim profilini birleştirip yapısal bir değerlendirme verir.
    Dönen: {vwap, profil, yapi_skoru, yapi_yorum, renk}
    """
    vw = vwap_hesapla(df)
    hp = hacim_profili(df)

    if not vw and not hp:
        return None

    # Yapı skoru (0-100): VWAP üstü + değer üstü/içi = güçlü yapı
    skor = 50
    if vw:
        if vw["konum"] == "VWAP ÜSTÜ": skor += 18
        elif vw["konum"] == "VWAP ALTI": skor -= 18
    if hp:
        if hp["konum"] == "DEĞER ÜSTÜ": skor += 12
        elif hp["konum"] == "DEĞER İÇİ": skor += 5
        elif hp["konum"] == "DEĞER ALTI": skor -= 15
    skor = max(0, min(100, skor))

    if skor >= 70:
        yorum, renk = "Güçlü yapı — alıcılar kontrolde, fiyat değerin üstünde.", "#10B981"
    elif skor >= 55:
        yorum, renk = "Olumlu yapı — denge alıcı lehine.", "#34D399"
    elif skor >= 45:
        yorum, renk = "Nötr yapı — net kontrol yok.", "#94A3B8"
    else:
        yorum, renk = "Zayıf yapı — satıcılar kontrolde, fiyat değerin altında.", "#EF4444"

    return {"vwap": vw, "profil": hp, "yapi_skoru": skor,
            "yapi_yorum": yorum, "renk": renk}
