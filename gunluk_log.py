#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
APEX — gunluk_log.py · ILERI-TEST KAYDEDICI (v2)
Her is gunu BIST kapanisindan sonra GitHub Actions ile calisir, CSV'ye 1 satir ekler.

NE TEST EDILIYOR: Sistemin RISK / REJIM-DURUS disiplini (dogrulanmis eksen).
NE TEST EDILMIYOR: Getiri tahmini (yazi-tura, sicil %49).

v2 farklari:
  - endeks artik ESIT-AGIRLIK BIST64 sepeti (app.fetch_bist -> her hissenin gunluk %'si).
    XU100.IS'e bagimli degil; o calismazsa yedek olarak XU100 denenir.
  - KENDI KENDINI ONARIR: eski/uyumsuz baslik gorurse arsivler, temiz baslar.

Sutunlar: tarih, endeks_gun%, kaynak, mevduat_gun%, rejim, stance_frac, stance_gun%
"""
import csv, datetime, os, shutil
from app import rejim_hesapla          # tek kaynak: app.py

CSV  = "ileri_gunluk.csv"
HEAD = ["tarih", "endeks_gun%", "kaynak", "mevduat_gun%", "rejim", "stance_frac", "stance_gun%"]
MEVDUAT_YILLIK = 45.0
STANCE = {"mevduat": 0.5, "notr": 0.75, "hisse": 1.0}

def endeks_gun():
    """(deger%, kaynak) doner. Cekilemezse (None, 'yok')."""
    # 1) Esit-agirlik BIST64 sepeti — uygulamanin guvendigi yol
    try:
        from app import fetch_bist
        veri = fetch_bist()
        chs = [d["ch"] for d in veri.values() if isinstance(d.get("ch"), (int, float))]
        if len(chs) >= 20:
            return round(sum(chs) / len(chs), 3), "BIST64-sepet"
    except Exception as ex:
        print("sepet hatasi:", ex)
    # 2) Yedek: XU100 endeksi
    try:
        import yfinance as yf
        df = yf.download("XU100.IS", period="7d", interval="1d", auto_adjust=True, progress=False)
        c = df["Close"].dropna().values.astype(float)
        if len(c) >= 2:
            return round((float(c[-1]) / float(c[-2]) - 1) * 100, 3), "XU100"
    except Exception as ex:
        print("xu100 hatasi:", ex)
    return None, "yok"

def temizle():
    """CSV varsa ve basligi beklenenden farkliysa arsivle (veri kaybi yok)."""
    if os.path.exists(CSV):
        with open(CSV, encoding="utf-8") as f:
            ilk = f.readline().strip()
        if ilk != ",".join(HEAD):
            arsiv = "ileri_gunluk_eski_{}.csv".format(datetime.date.today().isoformat())
            shutil.move(CSV, arsiv)
            print("eski/uyumsuz CSV arsivlendi ->", arsiv)

def zaten_var(gun):
    if not os.path.exists(CSV):
        return False
    with open(CSV, encoding="utf-8") as f:
        return any(line.startswith(gun) for line in f)

def main():
    bugun = datetime.date.today().isoformat()
    temizle()
    if zaten_var(bugun):
        print("bugun zaten kayitli, atlandi:", bugun); return

    rej = rejim_hesapla(datetime.date.today())
    frac = STANCE.get(rej["lehte"], 0.75)
    e, kaynak = endeks_gun()
    mev = ((1 + MEVDUAT_YILLIK / 100) ** (1 / 252) - 1) * 100
    stance = (e * frac + mev * (1 - frac)) if e is not None else None

    row = [bugun,
           e if e is not None else "",
           kaynak,
           round(mev, 4),
           rej["durus"],
           frac,
           round(stance, 3) if stance is not None else ""]

    yeni = not os.path.exists(CSV)
    with open(CSV, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if yeni:
            w.writerow(HEAD)
        w.writerow(row)
    print("eklendi:", row)

if __name__ == "__main__":
    main()
