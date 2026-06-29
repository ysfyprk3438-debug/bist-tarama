# -*- coding: utf-8 -*-
"""
telegram_alarm.py — APEX dürüst günlük bildirim.

FELSEFE (değişmez):
  • Al/sat sinyali YOK. Getiri/yön/hedef tahmini YOK. Güven skoru YOK.
  • Veri yoksa "—". Uydurma yok.
  • Sıralama NÖTR (izleme sırası) — "en iyi fırsat" sıralaması DEĞİL.
  • Tek doğrulanmış eksen: risk gözlemi (volatilite etiketi + ATR-stop mesafesi).
  • Çıktı "şimdi ne oluyor"u betimler; ne alınacağını söylemez. Karar kullanıcınındır.

Eski "KESİN AL · AV 92 · hedef +%2.8" formatının yerini alır.
Veriyi yalnızca veri.veri_al'dan çeker; karar.py / sinyal / skor ÇAĞIRMAZ.
"""

import os
import datetime as dt

import requests
import pandas as pd

from veri import veri_al, VADE_AYAR

# ── AYAR ───────────────────────────────────────────────────────────
# Kendi izleme listeni buraya yaz. Sıra önemsiz (alfabetik tutulur).
IZLEME = ["AKBNK", "ASELS", "EREGL", "GARAN", "THYAO", "TUPRS"]

# Opsiyonel portföy ağırlıkları (yüzde). Boşsa portföy satırı atlanır.
# Örn: {"GARAN": 40, "THYAO": 35, "EREGL": 25}
PORTFOY = {}

VADE_KEY = os.environ.get("AVCI_VADE", "gunluk")
TG_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
TG_CHAT = os.environ.get("TELEGRAM_CHAT_ID", "")


# ── METRİKLER (sadece betimleyici, ham df'ten) ─────────────────────
def metrikler(df, vade):
    """df: Open/High/Low/Close/Volume, tarih-indeksli, artan. Eksikte None döner."""
    if df is None or len(df) < 2:
        return None
    close = df["Close"].astype(float)
    high = df["High"].astype(float)
    low = df["Low"].astype(float)
    vol = df["Volume"].astype(float)

    son = float(close.iloc[-1])
    gun_pct = float(close.iloc[-1] / close.iloc[-2] - 1) * 100

    # VWAP konumu (son 20 bar) — alıcı/satıcı kontrolünün betimi
    n = min(20, len(df))
    tp = (high + low + close) / 3.0
    hac = vol.iloc[-n:].sum()
    vwap = float((tp.iloc[-n:] * vol.iloc[-n:]).sum() / hac) if hac > 0 else son
    vwap_pct = (son / vwap - 1) * 100 if vwap > 0 else None

    # ATR(14) → stop mesafesi (risk disiplini — tahmin değil)
    pc = close.shift(1)
    tr = pd.concat([(high - low), (high - pc).abs(), (low - pc).abs()], axis=1).max(axis=1)
    atr = float(tr.iloc[-14:].mean()) if len(tr.dropna()) >= 1 else None
    kat = float(vade.get("atr_stop", 1.0))
    stop_pct = (atr * kat / son) * 100 if (atr and son > 0) else None

    # Volatilite rejimi: hissenin KENDİ geçmişine göre yüzdelik (sihirli eşik yok)
    ret = close.pct_change().dropna()
    vol_etiket = "—"
    if len(ret) >= 30:
        kisa = ret.iloc[-20:].std()
        dagilim = ret.rolling(20).std().dropna()
        if len(dagilim) >= 5 and pd.notna(kisa):
            p = float((dagilim < kisa).mean())
            vol_etiket = "fırtına" if p > 0.66 else ("sakin" if p < 0.33 else "normal")

    return {"son": son, "gun_pct": gun_pct, "vwap_pct": vwap_pct,
            "stop_pct": stop_pct, "vol": vol_etiket}


def _hisse_satiri(kod, m):
    if m is None:
        return f"*{kod}* —  _veri yok_"
    p = f"{m['son']:.2f}₺"
    g = f"gün {m['gun_pct']:+.1f}%"
    if m["vwap_pct"] is None:
        v = "VWAP —"
    else:
        yon = "üstü" if m["vwap_pct"] >= 0 else "altı"
        v = f"VWAP {yon} %{abs(m['vwap_pct']):.1f}"
    vol = f"vol: {m['vol']}"
    s = "ATR-stop —" if m["stop_pct"] is None else f"ATR-stop −%{m['stop_pct']:.1f}"
    return f"*{kod}* {p} · {g} · {v} · {vol} · {s}"


# ── PORTFÖY RİSK (opsiyonel, betimleyici) ──────────────────────────
def _portfoy_satiri():
    if not PORTFOY:
        return None
    toplam = sum(PORTFOY.values())
    if toplam <= 0:
        return None
    en_buyuk_kod = max(PORTFOY, key=PORTFOY.get)
    en_buyuk_pct = PORTFOY[en_buyuk_kod] / toplam * 100
    parcalar = [f"en büyük tek pozisyon: {en_buyuk_kod} %{en_buyuk_pct:.0f}"]
    # sektör yoğunlaşması (varsa)
    try:
        from tarama_core import KOD_SEKTOR
        sek = {}
        for k, w in PORTFOY.items():
            s = KOD_SEKTOR.get(k, "Diğer")
            sek[s] = sek.get(s, 0) + w
        en_sek = max(sek, key=sek.get)
        en_sek_pct = sek[en_sek] / toplam * 100
        bayrak = " ⚠" if en_sek_pct >= 40 else ""
        parcalar.append(f"yoğunlaşma: {en_sek.strip()} %{en_sek_pct:.0f}{bayrak}")
    except Exception:
        pass
    return "Portföy: " + " · ".join(parcalar)


# ── MESAJ ──────────────────────────────────────────────────────────
def mesaj_kur():
    vade = VADE_AYAR.get(VADE_KEY, VADE_AYAR["gunluk"])
    bugun = dt.date.today().strftime("%d.%m.%Y")

    # XU100 günlük değişimi (betimleyici bağlam — yön çağrısı değil)
    edf, _ = veri_al("XU100", gun=vade["gun"], min_gun=vade["min_gun"], aralik=vade["aralik"])
    if edf is None or len(edf) < 2:
        endeks = "XU100 —"
    else:
        xpct = float(edf["Close"].iloc[-1] / edf["Close"].iloc[-2] - 1) * 100
        endeks = f"XU100 {xpct:+.1f}%"

    satirlar = [f"📋 *APEX — {bugun} kapanış durumu*",
                f"{endeks} · betimleyici, yön değil", ""]

    pf = _portfoy_satiri()
    if pf:
        satirlar.append(pf)
        satirlar.append("")

    satirlar.append("*İzleme* (sıra nötr — fırsat sıralaması DEĞİL):")
    for kod in sorted(IZLEME):
        df, _ = veri_al(kod, gun=vade["gun"], min_gun=vade["min_gun"], aralik=vade["aralik"])
        satirlar.append(_hisse_satiri(kod, metrikler(df, vade)))

    satirlar.append("")
    satirlar.append("_Sinyal yok · hedef/getiri yok · güven skoru yok._")
    satirlar.append("_Sadece şu an ne olduğu. Karar senin. Yatırım tavsiyesi değildir._")
    return "\n".join(satirlar)


def telegram_gonder(token, chat_id, mesaj):
    if not token or not chat_id:
        print("UYARI: TELEGRAM_TOKEN / TELEGRAM_CHAT_ID yok — gönderilmedi.")
        print(mesaj)
        return False
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": mesaj, "parse_mode": "Markdown",
                  "disable_web_page_preview": True},
            timeout=20,
        )
        ok = r.status_code == 200
        print("Gönderildi" if ok else f"Hata {r.status_code}: {r.text[:200]}")
        return ok
    except Exception as e:
        print(f"Gönderim hatası: {e}")
        return False


if __name__ == "__main__":
    m = mesaj_kur()
    telegram_gonder(TG_TOKEN, TG_CHAT, m)
