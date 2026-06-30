"""
═══════════════════════════════════════════════════════════════
VERİ KATMANI — BIST Tarama v4   (sürüm: duzeltme-1)
═══════════════════════════════════════════════════════════════
Tek sorumluluk: bir hissenin OHLCV verisini en sağlam şekilde getirmek.

Tasarım ilkeleri:
- Çift kaynak: Yahoo (birincil) → İş Yatırım (yedek)
- Sessiz hata YOK: her başarısızlığın sebebi kaydedilir
- Anlık veriye geçiş: sadece veri_al() değişir, gerisi aynı kalır

DÜZELTME (duzeltme-1):
- Yahoo'dan artık BÖLÜNME/TEMETTÜ DÜZELTİLMİŞ seri çekiyoruz: adjclose
  oranıyla tüm OHLC geriye düzeltiliyor. Böylece bedelsiz/temettü günlerinde
  yapay sıçrama olmuyor → vol ve ATR doğru hesaplanıyor (risk ekseni güvende).
- Her DataFrame'e bir not düşülüyor (df.attrs):
    duzeltme : "adjclose" (düzeltilmiş) | "ham" (düzeltme yok)
    ohlc     : "tam" (gerçek H/L var) | "kapanis" (yedek, H/L=Close -> ATR vekili)
  Bu not durum mesajına da yansır; yedeğe düşersek ekranda görünür.
"""

import requests
import pandas as pd
import time
from datetime import datetime, timedelta

UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15"


# ==============================================================
# KAYNAK 1 - YAHOO (doğrudan JSON, kütüphane değil)
# ==============================================================
def _yahoo(kod, gun, aralik="1d"):
    sembol = f"{kod}.IS"
    bitis = int(time.time())
    baslangic = bitis - (gun * 86400)
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{sembol}"
    params = {
        "period1": baslangic, "period2": bitis, "interval": aralik,
        "events": "div,splits", "includeAdjustedClose": "true",
    }
    r = requests.get(url, params=params, headers={"User-Agent": UA}, timeout=15)
    if r.status_code != 200:
        raise RuntimeError(f"yahoo HTTP {r.status_code}")
    j = r.json()
    res = j["chart"]["result"][0]
    ts = res["timestamp"]
    q = res["indicators"]["quote"][0]
    df = pd.DataFrame({
        "Open": q["open"], "High": q["high"], "Low": q["low"],
        "Close": q["close"], "Volume": q["volume"],
    }, index=pd.to_datetime(ts, unit="s"))

    # -- BÖLÜNME/TEMETTÜ DÜZELTMESİ --------------------------------
    # adjclose = bölünme + temettü düzeltilmiş kapanış. Oran (adjclose/close)
    # ile TÜM OHLC'yi geriye düzeltiriz -> seri sürekli olur, vol/ATR şişmez.
    # Hacim ham bırakılır (sadece görsel; risk hesabına girmez).
    duz = "ham"
    try:
        adj = res["indicators"]["adjclose"][0]["adjclose"]
        s_adj = pd.Series(adj, index=df.index)
        oran = (s_adj / df["Close"]).where(df["Close"].notna() & (df["Close"] != 0))
        oran = oran.fillna(1.0)
        for kol in ("Open", "High", "Low", "Close"):
            df[kol] = df[kol] * oran
        duz = "adjclose"
    except (KeyError, TypeError, IndexError, ValueError):
        duz = "ham"

    df = df.dropna()
    df.attrs["duzeltme"] = duz
    df.attrs["ohlc"] = "tam"
    df.attrs["kaynak"] = "yahoo"
    return df


# ==============================================================
# KAYNAK 2 - İŞ YATIRIM (yedek)
# UYARI: Sadece KAPANIŞ verir (gerçek High/Low yok) ve DÜZELTİLMEMİŞTİR.
#        OHLC'yi kapanıştan türettiğimiz için ATR, gün içi aralığı göremez;
#        |Δkapanış| üzerinden bir VEKİL (genelde gerçekten düşük) üretir.
#        Bu yüzden df.attrs['ohlc']='kapanis' işaretlenir; tüketici bilsin.
# ==============================================================
def _isyatirim(kod, gun):
    url = "https://www.isyatirim.com.tr/_layouts/15/Isyatirim.Website/Common/Data.aspx/HisseTekil"
    bugun = datetime.now()
    gecmis = bugun - timedelta(days=gun)
    params = {
        "hisse": kod,
        "startdate": gecmis.strftime("%d-%m-%Y"),
        "enddate": bugun.strftime("%d-%m-%Y"),
    }
    headers = {"User-Agent": UA, "Referer": "https://www.isyatirim.com.tr/"}
    r = requests.get(url, params=params, headers=headers, timeout=15)
    if r.status_code != 200:
        raise RuntimeError(f"isyatirim HTTP {r.status_code}")
    kayitlar = r.json().get("value", [])
    if not kayitlar:
        raise RuntimeError("isyatirim boş")
    # İş Yatırım sadece kapanış + hacim verir; OHLC'yi kapanıştan türetiriz
    satirlar = []
    for k in kayitlar:
        try:
            tarih = pd.to_datetime(k["HGDG_TARIH"], format="%d-%m-%Y")
            kapanis = float(k["HGDG_KAPANIS"])
            hacim = float(k.get("HGDG_HACIM", 0) or 0)
            satirlar.append((tarih, kapanis, hacim))
        except (KeyError, ValueError, TypeError):
            continue
    if not satirlar:
        raise RuntimeError("isyatirim parse edilemedi")
    df = pd.DataFrame(satirlar, columns=["tarih", "Close", "Volume"]).set_index("tarih")
    df = df.sort_index()
    # OHLC yoksa kapanışı baz al (teknik göstergeler yine çalışır; ATR vekildir)
    df["Open"] = df["Close"]
    df["High"] = df["Close"]
    df["Low"] = df["Close"]
    df = df[["Open", "High", "Low", "Close", "Volume"]]
    df.attrs["duzeltme"] = "ham"        # İş Yatırım HisseTekil düzeltilmemiş kapanıştır
    df.attrs["ohlc"] = "kapanis"        # gerçek High/Low YOK -> ATR vekil (düşük olabilir)
    df.attrs["kaynak"] = "isyatirim"
    return df


# ==============================================================
# ANA FONKSİYON - veri_al()
# Anlık veriye geçmek istersen SADECE bu fonksiyonu değiştir.
# Dönen: (DataFrame | None, durum_mesajı)
# durum örn: "yahoo:128:adjclose:tam"  ya da  "isyatirim:96:ham:kapanis"
# ==============================================================
def veri_al(kod, gun=180, min_gun=60, aralik="1d"):
    """
    Bir hissenin OHLCV verisini getirir.
    aralik: "1d" günlük, "1h" saatlik, "15m" 15 dakikalık (gün içi)
    Önce Yahoo, olmazsa İş Yatırım. İkisi de patlarsa (None, sebep) döner.
    """
    sebepler = []

    def _etiket(df):
        return f"{df.attrs.get('kaynak','?')}:{len(df)}:{df.attrs.get('duzeltme','?')}:{df.attrs.get('ohlc','?')}"

    # 1) Yahoo
    try:
        df = _yahoo(kod, gun, aralik)
        if df is not None and len(df) >= min_gun:
            return df, _etiket(df)
        sebepler.append(f"yahoo:az({len(df) if df is not None else 0})")
    except Exception as e:
        sebepler.append(f"yahoo:{type(e).__name__}")

    # 2) İş Yatırım (yedek) - sadece günlük destekler, gün içinde atla
    if aralik == "1d":
        try:
            df = _isyatirim(kod, gun)
            if df is not None and len(df) >= min_gun:
                return df, _etiket(df)
            sebepler.append(f"isy:az({len(df) if df is not None else 0})")
        except Exception as e:
            sebepler.append(f"isy:{type(e).__name__}")

    return None, " | ".join(sebepler)


# ==============================================================
# VADE AYARLARI - günlük / haftalık / aylık trade
# Her vade kendi veri penceresi + gösterge periyodu kullanır
# ==============================================================
VADE_AYAR = {
    "gun_ici": {
        "ad": "Gün İçi (15dk)", "gun": 7, "min_gun": 30, "aralik": "15m",
        "rsi_periyot": 9, "ma_kisa": 8, "ma_orta": 21, "ma_uzun": 50,
        "atr_hedef": 1.2, "atr_stop": 0.7, "min_kazanc": 1.0,
    },
    "gunluk": {
        "ad": "Günlük (Scalp)", "gun": 90, "min_gun": 40, "aralik": "1d",
        "rsi_periyot": 7, "ma_kisa": 5, "ma_orta": 13, "ma_uzun": 21,
        "atr_hedef": 1.5, "atr_stop": 0.8, "min_kazanc": 2.0,
    },
    "haftalik": {
        "ad": "Haftalık (Swing)", "gun": 180, "min_gun": 60, "aralik": "1d",
        "rsi_periyot": 14, "ma_kisa": 20, "ma_orta": 50, "ma_uzun": 100,
        "atr_hedef": 2.5, "atr_stop": 1.2, "min_kazanc": 3.0,
    },
    "aylik": {
        "ad": "Aylık (Pozisyon)", "gun": 365, "min_gun": 120, "aralik": "1d",
        "rsi_periyot": 21, "ma_kisa": 50, "ma_orta": 100, "ma_uzun": 200,
        "atr_hedef": 4.0, "atr_stop": 2.0, "min_kazanc": 6.0,
    },
}
