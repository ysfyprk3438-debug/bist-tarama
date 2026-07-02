"""
═══════════════════════════════════════════════════════════════
ANALİZ MOTORU — BIST Tarama v4
═══════════════════════════════════════════════════════════════
Tek sorumluluk: bir hissenin OHLCV verisini alıp,
seçilen vadeye göre (günlük/haftalık/aylık) sinyal üretmek.

ta kütüphanesine BAĞIMLI DEĞİL — göstergeleri kendimiz hesaplıyoruz.
Sebep: ta kütüphanesi bazen NaN/sürüm sorunu çıkarıyor; kendi
hesabımız hem şeffaf hem sürümden bağımsız.
"""

import pandas as pd
import numpy as np
import datetime
import niyet as ny
import grafik as gf
import alarm as al
import karar as kr
import volatilite as vol
import karakter as kar
import hacim as hc
import zaman as zm
import fibonacci as fib


# ══════════════════════════════════════════════════════════════
# TEKNİK GÖSTERGELER (kendi hesabımız — şeffaf, sürümsüz)
# ══════════════════════════════════════════════════════════════
def _rsi(kapanis, periyot=14):
    delta = kapanis.diff()
    kazanc = delta.clip(lower=0).rolling(periyot).mean()
    kayip = (-delta.clip(upper=0)).rolling(periyot).mean()
    rs = kazanc / (kayip + 1e-10)
    return 100 - (100 / (1 + rs))


def _macd(kapanis, hizli=12, yavas=26, sinyal=9):
    ema_hizli = kapanis.ewm(span=hizli, adjust=False).mean()
    ema_yavas = kapanis.ewm(span=yavas, adjust=False).mean()
    macd_cizgi = ema_hizli - ema_yavas
    sinyal_cizgi = macd_cizgi.ewm(span=sinyal, adjust=False).mean()
    return macd_cizgi - sinyal_cizgi  # histogram (fark)


def _atr(high, low, close, periyot=14):
    onceki_kapanis = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - onceki_kapanis).abs(),
        (low - onceki_kapanis).abs(),
    ], axis=1).max(axis=1)
    return tr.rolling(periyot).mean()


def _bollinger_yuzde(kapanis, periyot=20, std=2):
    orta = kapanis.rolling(periyot).mean()
    sapma = kapanis.rolling(periyot).std()
    ust = orta + std * sapma
    alt = orta - std * sapma
    son = kapanis.iloc[-1]
    return float((son - alt.iloc[-1]) / (ust.iloc[-1] - alt.iloc[-1] + 1e-10) * 100)


# ══════════════════════════════════════════════════════════════
# AKILLI PARA (SMART MONEY) — OBV + hacim + para akışı
# ══════════════════════════════════════════════════════════════
def akilli_para(df):
    k, v, h, l = df["Close"], df["Volume"], df["High"], df["Low"]

    # OBV (On Balance Volume) — vektörel, hızlı
    yon = np.sign(k.diff()).fillna(0)
    obv = (yon * v).cumsum()
    obv_trend = bool(obv.iloc[-1] > obv.iloc[-10]) if len(obv) >= 10 else True

    # Fiyat-hacim uyumu (son 5 gün)
    fiyat_d = k.pct_change().iloc[-5:].mean()
    hacim_d = v.pct_change().iloc[-5:].mean()
    uyum = bool((fiyat_d > 0 and hacim_d > 0) or (fiyat_d < 0 and hacim_d < 0))

    # Büyük oyuncu — son 3 günde hacim patlaması
    hacim_ort = float(v.rolling(20).mean().iloc[-1]) if len(v) >= 20 else float(v.mean())
    hacim_max3 = float(v.iloc[-3:].max())
    buyuk_oyuncu = bool(hacim_max3 > hacim_ort * 2.5) if hacim_ort > 0 else False

    # CMF (Chaikin Money Flow) — para giriş/çıkış
    mf_carpan = ((k - l) - (h - k)) / (h - l + 1e-10)
    mf_hacim = mf_carpan * v
    cmf = float(mf_hacim.rolling(14).sum().iloc[-1] / (v.rolling(14).sum().iloc[-1] + 1e-10))

    # Skor 0-100
    skor = 50
    if obv_trend: skor += 20
    if uyum: skor += 15
    if buyuk_oyuncu: skor += 10
    if cmf > 0.1: skor += 15
    elif cmf < -0.1: skor -= 20
    skor = max(0, min(100, skor))

    if skor >= 80: yorum, renk = "Güçlü Alış · Akıllı para giriyor", "#10B981"
    elif skor >= 60: yorum, renk = "Alış baskısı", "#34D399"
    elif skor >= 40: yorum, renk = "Nötr", "#94A3B8"
    elif skor >= 20: yorum, renk = "Satış baskısı", "#F87171"
    else: yorum, renk = "Güçlü Satış · Akıllı para çıkıyor", "#EF4444"

    return {
        "skor": skor, "yorum": yorum, "renk": renk,
        "obv_trend": obv_trend, "uyum": uyum,
        "buyuk_oyuncu": buyuk_oyuncu, "cmf": round(cmf, 3),
    }


# ══════════════════════════════════════════════════════════════
# POZİSYON YÖNETİMİ — risk tabanlı boyutlama
# ══════════════════════════════════════════════════════════════
def pozisyon_hesapla(portfoy_tl, son_fiyat, stop_fiyat, kelly_pct=None, max_pozisyon_pct=20.0):
    if son_fiyat <= 0 or portfoy_tl <= 0:
        return None
    risk_yuzde = min(kelly_pct * 0.5 if kelly_pct else 2.0, 5.0)
    max_risk_tl = portfoy_tl * (risk_yuzde / 100)
    hisse_basi_risk = son_fiyat - stop_fiyat
    if hisse_basi_risk <= 0:
        return None
    risk_lot = int(max_risk_tl / hisse_basi_risk)
    # Pozisyon büyüklüğü tavanı: tek hissede portföyün en fazla %X'i (%984 hatasının çözümü)
    tavan_lot = int((portfoy_tl * (max_pozisyon_pct / 100.0)) / son_fiyat)
    lot = max(0, min(risk_lot, tavan_lot))
    if lot <= 0:
        return None
    pozisyon_tl = lot * son_fiyat
    return {
        "lot": lot,
        "pozisyon_tl": pozisyon_tl,
        "pozisyon_yuzde": (pozisyon_tl / portfoy_tl) * 100,
        "max_kayip_tl": lot * hisse_basi_risk,
        "risk_yuzde": risk_yuzde,
        "tavan_uygulandi": risk_lot > tavan_lot,
    }


# ══════════════════════════════════════════════════════════════
# ANA ANALİZ — vade bazlı sinyal üretimi
# ══════════════════════════════════════════════════════════════
def analiz_et(kod, df, vade_ayar, portfoy_tl, carpan, sektor, detayli=True, endeks_close=None, backtest=False):
    """
    Bir hissenin verisini alıp sinyal üretir.
    Sinyal yoksa None döner (sebep önemli değil — eleme normal).

    detayli=True: grafik + alarm + niyet + karakter (tarama ekranı için)
    detayli=False: sadece sinyal/hedef/stop (backtest ve robot için — HIZLI)
    endeks_close: XU100 kapanış serisi (relatif güç için, opsiyonel)
    """
    if df is None or len(df) < vade_ayar["min_gun"]:
        return None

    # Veri tazeliği — son veri 10 günden eskiyse atla
    # backtest=True iken atlanır: geçmiş dilimlerle test yapılabilsin (canlı yol DEĞİŞMEZ).
    son_tarih = df.index[-1]
    if hasattr(son_tarih, "date"):
        son_tarih = son_tarih.date()
    if not backtest and (datetime.date.today() - son_tarih).days > 10:
        return None

    k, h, l, v = df["Close"], df["High"], df["Low"], df["Volume"]
    son = float(k.iloc[-1])
    if son <= 0:
        return None

    # Hareketli ortalamalar (vadeye göre)
    mk, mo, mu = vade_ayar["ma_kisa"], vade_ayar["ma_orta"], vade_ayar["ma_uzun"]
    ma_kisa = float(k.rolling(mk).mean().iloc[-1]) if len(k) >= mk else son
    ma_orta = float(k.rolling(mo).mean().iloc[-1]) if len(k) >= mo else son
    ma_uzun = float(k.rolling(mu).mean().iloc[-1]) if len(k) >= mu else son
    trend = sum([son > ma_kisa, son > ma_orta, son > ma_uzun, ma_kisa > ma_orta])

    # Göstergeler
    rsi = float(_rsi(k, vade_ayar["rsi_periyot"]).iloc[-1])
    if np.isnan(rsi):
        rsi = 50.0
    macd_pozitif = bool(_macd(k).iloc[-1] > 0)
    atr = float(_atr(h, l, k).iloc[-1])
    if np.isnan(atr) or atr <= 0:
        atr = son * 0.02
    bb_yuzde = _bollinger_yuzde(k)

    # Destek / direnç
    direnc = float(h.rolling(20).max().iloc[-1])
    destek = float(l.rolling(20).min().iloc[-1])
    if direnc <= son:
        direnc = son * (1 + vade_ayar["atr_hedef"] * 0.02)
    if destek >= son:
        destek = son * 0.95

    # Volatilite rejimi — stop mesafesini ve pozisyonu ayarlar (adaptif risk)
    vrej = vol.volatilite_rejimi(df)

    # Hedef / stop (vadeye göre genişlik × volatilite rejimi)
    hedef = min(direnc, son + atr * vade_ayar["atr_hedef"]) if direnc > son else son + atr * vade_ayar["atr_hedef"]
    stop = son - atr * vade_ayar["atr_stop"] * vrej["stop_carpani"]  # fırtınada genişler, sakurda daralır
    if stop <= 0:
        stop = son * 0.95
    kazanc_pct = ((hedef - son) / son) * 100
    kayip_pct = ((son - stop) / son) * 100
    rr = kazanc_pct / (kayip_pct + 1e-10)

    # Akıllı para
    sm = akilli_para(df)

    # Niyet okuma — sadece detaylı modda (tarama ekranı)
    if detayli:
        niyet = ny.niyet_oku(df, rsi_son=rsi)
    else:
        niyet = {"sinif": "NORMAL", "guven": 0, "aciklama": "", "renk": "#94A3B8", "uyari": False}

    # 3 dönemlik getiri
    geri = min(63, len(k) - 1)
    onceki = float(k.iloc[-geri]) if geri > 0 else son
    donem_getiri = ((son - onceki) / onceki) * 100

    # ── SİNYAL MANTIĞI ──
    if rsi > 72:
        return None  # aşırı alım — eleme
    elif rsi < 35 and macd_pozitif and sm["skor"] >= 50:
        sinyal, renk = "DİP FIRSATI", "yesil"
    elif trend >= 3 and macd_pozitif and rsi < 65 and sm["skor"] >= 60:
        sinyal, renk = "AL · Güçlü", "yesil"
    elif trend >= 3 and macd_pozitif and rsi < 65:
        sinyal, renk = "AL · Trend", "yesil"
    elif trend >= 2 and macd_pozitif:
        sinyal, renk = "Takipte Tut", "sari"
    else:
        return None

    # Kalite filtresi
    if rr < 1.5 or kazanc_pct < vade_ayar["min_kazanc"]:
        return None

    # Puan (0-100)
    puan = int(min(100, (
        trend * 8
        + min(20, rr * 6)
        + (10 if macd_pozitif else 0)
        + (8 if sm["skor"] >= 70 else 4 if sm["skor"] >= 50 else 0)
        + (5 if rsi < 55 else 0)
        + (5 if sm["buyuk_oyuncu"] else 0)
        + (8 if "DİP" in sinyal or "Güçlü" in sinyal else 4)
    ) * carpan))

    # Kelly + pozisyon
    kelly_pct = max(0, min(25, (rr - 1) / rr * 100 * 0.5))
    # Volatilite rejimi pozisyonu ölçekler: fırtınada küçült, sakurda büyüt
    kelly_pct_ayarli = kelly_pct * vrej["poz_carpani"]
    pozisyon = pozisyon_hesapla(portfoy_tl, son, stop, kelly_pct_ayarli)

    # Güveni nihai puanla yeniden hesapla
    guven = ny.guven_birlestir(puan, sm["skor"], niyet)

    # Hızlı mod (backtest/robot): grafik+alarm+niyet detayı atlanır
    if not detayli:
        return {
            "kod": kod, "son": son, "puan": puan,
            "sinyal": sinyal, "renk": renk,
            "hedef": hedef, "stop": stop, "rr": rr,
            "kazanc_pct": kazanc_pct, "kayip_pct": kayip_pct,
            "rsi": rsi, "destek": destek, "direnc": direnc,
            "donem_getiri": donem_getiri, "trend": trend,
            "sm": sm, "niyet": niyet, "guven": guven,
            "kelly_pct": kelly_pct, "pozisyon": pozisyon,
            "sektor": sektor, "bb_yuzde": bb_yuzde,
            "tarih": datetime.date.today().isoformat(),
        }

    # Detaylı mod (tarama ekranı): zengin grafik + teknik olaylar + alarm
    ma50_seri = k.rolling(50).mean()
    ma200_seri = k.rolling(200).mean() if len(k) >= 200 else k.rolling(min(100, len(k)//2)).mean()
    grafik_df = pd.DataFrame({
        "Close": k, "MA50": ma50_seri, "MA200": ma200_seri,
        "High": h, "Low": l,
    }).iloc[-120:]
    teknik_olay = gf.teknik_olaylar(df, son_gun=120)
    grafik_yorum_txt = gf.grafik_yorum(teknik_olay, {"trend": trend})

    # Yaklaşan kritik olaylar (alarm + geri sayım)
    yaklasan = al.yaklasan_olaylar(df)
    alarm = al.alarm_ozeti(yaklasan)

    # Karakter & strateji uyumu (Hurst + relatif güç + sinyal uyumu)
    karakter = kar.karakter_profili(k.values, endeks_close, sinyal, vrej)

    # Hacim yapısı (VWAP + hacim profili = kurumsal seviyeler)
    # NOT: Güveni çarpmaz (zaten niyet×rüzgar×karakter var) — yapısal bilgi olarak sunulur
    hacim_yap = hc.hacim_yapisi(df)

    # Çoklu zaman dilimi onayı (üst zaman dilimi sinyali teyit ediyor mu?)
    ztd = zm.zaman_dilimi_onayi(df, vade_ayar.get("aralik", "1d"), vade_ayar.get("gun", 180), sinyal)

    # Matematiksel seviyeler (Fibonacci + pivot, hacim POC ile onay)
    _poc = hacim_yap.get("profil", {}).get("poc") if hacim_yap else None
    mat_seviye = fib.matematiksel_seviyeler(df, hacim_poc=_poc)
    # Karakter uyumu güveni etkiler (uyumsuz sinyal = tuzak riski → güven düşer)
    if guven.get("yuzde"):
        yeni = max(0, min(100, int(guven["yuzde"] * karakter["guven_etkisi"])))
        guven["yuzde"] = yeni
        if yeni >= 75: guven["seviye"], guven["renk"] = "YÜKSEK", "#10B981"
        elif yeni >= 55: guven["seviye"], guven["renk"] = "ORTA", "#F59E0B"
        elif yeni >= 35: guven["seviye"], guven["renk"] = "DÜŞÜK", "#FB923C"
        else: guven["seviye"], guven["renk"] = "ZAYIF", "#EF4444"

    # Sonuç sözlüğünü oluştur, sonra av skorunu (tüm sinyalleri sentezleyen karar) ekle
    sonuc = {
        "kod": kod, "son": son, "puan": puan,
        "sinyal": sinyal, "renk": renk,
        "hedef": hedef, "stop": stop, "rr": rr,
        "kazanc_pct": kazanc_pct, "kayip_pct": kayip_pct,
        "rsi": rsi, "destek": destek, "direnc": direnc,
        "donem_getiri": donem_getiri, "trend": trend,
        "sm": sm, "niyet": niyet, "guven": guven, "alarm": alarm,
        "kelly_pct": kelly_pct, "pozisyon": pozisyon, "volatilite": vrej,
        "karakter": karakter, "hacim": hacim_yap, "zaman_onay": ztd, "mat_seviye": mat_seviye,
        "sektor": sektor, "bb_yuzde": bb_yuzde,
        "df_grafik": grafik_df, "teknik_olay": teknik_olay, "grafik_yorum": grafik_yorum_txt,
        "tarih": datetime.date.today().isoformat(),
    }
    sonuc["karar"] = kr.av_skoru(sonuc)
    return sonuc
