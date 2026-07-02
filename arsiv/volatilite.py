"""
═══════════════════════════════════════════════════════════════
VOLATİLİTE REJİMİ — BIST Para Avcısı v4 (Adaptif Zemin)
═══════════════════════════════════════════════════════════════
Derin gerçek: VOLATİLİTE KÜMELENİR. Sakin günler sakin günleri,
fırtınalı günler fırtınalı günleri doğurur (ARCH/GARCH — Nobel'lik).

NEDEN KRİTİK:
  • SAKİN rejimde → dipten alım (mean-reversion) çalışır
  • FIRTINA rejiminde → momentum/trend takibi çalışır, stoplar genişler
Aynı strateji yanlış rejimde para kaybettirir.

Sistem rejimi bilince:
  - Pozisyon boyutunu ayarlar (fırtınada küçült)
  - Stop mesafesini ayarlar (fırtınada genişlet, sakurda daralt)
  - Hangi stratejinin çalışacağını seçer (Katman 4 zemini)

Üç ölçüt birleşir: ATR%, Bollinger genişliği, gerçekleşen vol yönü.
"""

import numpy as np
import pandas as pd


def _atr_yuzde(df, periyot=14):
    """ATR'yi fiyata oran olarak (günlük % oynaklık)."""
    h, l, c = df["High"], df["Low"], df["Close"]
    onceki = c.shift(1)
    tr = pd.concat([h - l, (h - onceki).abs(), (l - onceki).abs()], axis=1).max(axis=1)
    atr = tr.rolling(periyot).mean()
    fiyat = float(c.iloc[-1])
    return float(atr.iloc[-1] / fiyat * 100) if fiyat > 0 else 0


def _bollinger_genislik(df, periyot=20):
    """Bollinger bant genişliği (sıkışma/patlama göstergesi)."""
    k = df["Close"]
    orta = k.rolling(periyot).mean()
    sapma = k.rolling(periyot).std()
    genislik = (4 * sapma) / orta * 100  # (üst-alt)/orta
    son = float(genislik.iloc[-1])
    # Son genişliğin, son 60 güne göre yüzdelik konumu (sıkışık mı geniş mi?)
    son60 = genislik.iloc[-60:].dropna()
    if len(son60) >= 10:
        yuzdelik = float((son60 < son).sum() / len(son60) * 100)
    else:
        yuzdelik = 50.0
    return son, yuzdelik


def _gerceklesen_vol(df, kisa=10, uzun=30):
    """Gerçekleşen volatilite (getiri std) — kısa vadeli artıyor mu?"""
    getiri = df["Close"].pct_change()
    vol_kisa = float(getiri.iloc[-kisa:].std() * 100) if len(getiri) >= kisa else 0
    vol_uzun = float(getiri.iloc[-uzun:].std() * 100) if len(getiri) >= uzun else vol_kisa
    artiyor = vol_kisa > vol_uzun * 1.1  # kısa vol, uzun voldan %10+ yüksekse artıyor
    return vol_kisa, vol_uzun, artiyor


def volatilite_rejimi(df):
    """
    Bir hissenin (veya endeksin) volatilite rejimini ölçer.
    Dönen: {rejim, renk, atr_pct, bb_yuzdelik, vol_yon, strateji_onerisi,
            poz_carpani, stop_carpani, aciklama}
    """
    if df is None or len(df) < 30:
        return {"rejim": "BELİRSİZ", "renk": "#94A3B8", "atr_pct": 0,
                "strateji_onerisi": "Yetersiz veri", "poz_carpani": 1.0,
                "stop_carpani": 1.0, "aciklama": "", "bb_yuzdelik": 50, "vol_yon": "—"}

    atr_pct = _atr_yuzde(df)
    bb_son, bb_yuzdelik = _bollinger_genislik(df)
    vol_kisa, vol_uzun, vol_artiyor = _gerceklesen_vol(df)

    # ── REJİM SINIFLANDIRMA ──
    # ATR% BIST için: <2 sakin, 2-4 normal, >4 fırtına (yaklaşık)
    # Bollinger yüzdelik: düşük=sıkışma, yüksek=geniş/patlama
    if atr_pct < 2.0 and bb_yuzdelik < 35:
        rejim = "SAKİN"
        renk = "#10B981"
        strateji = "Dipten alım (mean-reversion) çalışır — geri çekilmeleri al, destekten sıçramaları topla."
        poz_carpani = 1.2   # sakin = daha büyük pozisyon güvenli
        stop_carpani = 0.85  # daralt
        aciklama = "Düşük oynaklık, bantlar sıkışmış. Sakin sular — ama sıkışma sonrası patlama gelebilir."
    elif atr_pct > 4.0 or (bb_yuzdelik > 75 and vol_artiyor):
        rejim = "FIRTINA"
        renk = "#EF4444"
        strateji = "Momentum/trend takibi çalışır — güçlü yönü takip et, dipten almaya kalkma. Stopları genişlet."
        poz_carpani = 0.6   # fırtına = pozisyon küçült (risk yüksek)
        stop_carpani = 1.4   # genişlet (gürültüye takılma)
        aciklama = "Yüksek oynaklık. Sert hareketler — fırsat büyük ama risk de büyük. Disiplin şart."
    elif bb_yuzdelik < 25:
        rejim = "SIKIŞMA"
        renk = "#F59E0B"
        strateji = "Patlama öncesi sıkışma — yön belirsiz. Kırılım yönünde pozisyon al, erken girme."
        poz_carpani = 0.8
        stop_carpani = 1.0
        aciklama = "Bantlar çok sıkışmış — büyük hareket yaklaşıyor olabilir, ama yönü henüz belli değil."
    else:
        rejim = "NORMAL"
        renk = "#38BDF8"
        strateji = "Dengeli koşullar — trend ve geri çekilme stratejileri birlikte çalışabilir."
        poz_carpani = 1.0
        stop_carpani = 1.0
        aciklama = "Tipik oynaklık. Standart strateji ve risk yönetimi geçerli."

    return {
        "rejim": rejim, "renk": renk,
        "atr_pct": round(atr_pct, 2),
        "bb_yuzdelik": round(bb_yuzdelik, 0),
        "vol_yon": "artıyor" if vol_artiyor else "sabit/azalıyor",
        "vol_kisa": round(vol_kisa, 2),
        "strateji_onerisi": strateji,
        "poz_carpani": poz_carpani,
        "stop_carpani": stop_carpani,
        "aciklama": aciklama,
    }


def piyasa_volatilite_ozeti(df_endeks):
    """
    Endeks (XU100) için volatilite rejimi — piyasa geneli hava durumu.
    Tarama başında bir kez hesaplanır, tüm kararları etkiler.
    """
    rej = volatilite_rejimi(df_endeks)
    return rej
