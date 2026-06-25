"""
═══════════════════════════════════════════════════════════════
ÇOKLU ZAMAN DİLİMİ ONAYI — BIST Para Avcısı v4
═══════════════════════════════════════════════════════════════
Borsanın temel kuralı: "Üst zaman diliminin yönünde işlem yap."

Günlük grafikte güçlü görünen bir AL sinyali, HAFTALIK trend tersse
genellikle TUZAKTIR — düşüşte kısa bir sıçramadır. Tersine, hem günlük
hem haftalık aynı yönü gösteriyorsa sinyal çok daha güvenilir.

Yöntem: Eldeki günlük veriyi üst zaman dilimine çevirir (resample),
ekstra veri çekmeden onay kontrolü yapar:
  • Gün içi (15dk) sinyali → GÜNLÜK trendle teyit
  • Günlük/Haftalık sinyali → HAFTALIK trendle teyit
  • Aylık sinyali → AYLIK trendle teyit

Sonuç: ONAY / NÖTR / ÇELİŞKİ — kararı güçlendirir veya uyarır.
"""

import numpy as np
import pandas as pd


def _ust_trend(df_ust):
    """Üst zaman dilimi df'inden trend yönü (-2..+2)."""
    if df_ust is None or len(df_ust) < 8:
        return None
    k = df_ust["Close"]
    n = len(k)
    kisa = k.rolling(min(4, n - 1)).mean()
    uzun = k.rolling(min(8, n - 1)).mean()
    if pd.isna(kisa.iloc[-1]) or pd.isna(uzun.iloc[-1]):
        return None

    skor = 0
    fiyat = float(k.iloc[-1])
    # 1) Fiyat kısa ortalamanın üstünde mi?
    if fiyat > float(kisa.iloc[-1]): skor += 1
    else: skor -= 1
    # 2) Kısa ortalama uzunun üstünde mi? (trend yönü)
    if float(kisa.iloc[-1]) > float(uzun.iloc[-1]): skor += 1
    else: skor -= 1

    return max(-2, min(2, skor))


def zaman_dilimi_onayi(df, aralik, gun, sinyal_tip):
    """
    Sinyalin üst zaman dilimi tarafından onaylanıp onaylanmadığını kontrol eder.
    df: günlük (veya 15dk) OHLCV
    aralik: "15m" (gün içi) veya "1d" (günlük+)
    gun: bakış ufku (gün) — haftalık/aylık ayrımı için
    sinyal_tip: sinyal metni

    Dönen: {durum, skor, renk, etiket, aciklama, ust_dilim}
    """
    if df is None or len(df) < 30:
        return None

    # Hangi üst zaman dilimine çevrilecek?
    if aralik == "15m":
        kural, ust_ad = "D", "günlük"      # 15dk → günlük
    elif gun >= 300:
        kural, ust_ad = "ME", "aylık"      # aylık vade → aylık teyit
    else:
        kural, ust_ad = "W", "haftalık"    # günlük/haftalık → haftalık

    # Resample (üst zaman dilimine çevir)
    try:
        df_ust = df.resample(kural).agg({
            "Open": "first", "High": "max", "Low": "min",
            "Close": "last", "Volume": "sum",
        }).dropna()
    except Exception:
        return None

    trend = _ust_trend(df_ust)
    if trend is None:
        return None

    # Sinyal yönü: DİP/AL = yukarı beklentisi (boğa)
    # (Sistemdeki tüm sinyaller alım yönlü olduğu için boğa varsayıyoruz)
    sinyal_bogamı = True

    # ── ONAY MANTIĞI ──
    if sinyal_bogamı:
        if trend >= 2:
            durum, renk = "GÜÇLÜ ONAY", "#10B981"
            etiket = f"✓✓ {ust_ad.capitalize()} trend güçlü yukarı"
            aciklama = f"Sinyal {ust_ad} trendle TAM UYUMLU — üst zaman dilimi de yukarı, güvenilir."
        elif trend == 1:
            durum, renk = "ONAY", "#34D399"
            etiket = f"✓ {ust_ad.capitalize()} trend yukarı"
            aciklama = f"{ust_ad.capitalize()} trend destekliyor — olumlu teyit."
        elif trend == 0:
            durum, renk = "NÖTR", "#94A3B8"
            etiket = f"~ {ust_ad.capitalize()} trend yatay"
            aciklama = f"{ust_ad.capitalize()} trend kararsız — net onay yok, temkinli ol."
        elif trend == -1:
            durum, renk = "ZAYIF ÇELİŞKİ", "#F59E0B"
            etiket = f"⚠ {ust_ad.capitalize()} trend zayıf"
            aciklama = f"{ust_ad.capitalize()} trend hafif aşağı — sinyalle çelişiyor, dikkatli ol."
        else:
            durum, renk = "ÇELİŞKİ", "#EF4444"
            etiket = f"⚠⚠ {ust_ad.capitalize()} trend aşağı"
            aciklama = f"Sinyal {ust_ad} trende TERS — düşüşte sıçrama olabilir (tuzak riski). Üst zaman dilimi aşağı."

    return {
        "durum": durum, "skor": trend, "renk": renk,
        "etiket": etiket, "aciklama": aciklama, "ust_dilim": ust_ad,
    }
