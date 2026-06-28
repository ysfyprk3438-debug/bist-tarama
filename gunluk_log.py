#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
APEX — gunluk_log.py · ILERI-TEST KAYDEDICI
Her is gunu BIST kapanisindan sonra GitHub Actions ile calisir, CSV'ye 1 satir ekler.

NE TEST EDILIYOR: Sistemin RISK / REJIM-DURUS disiplini (dogrulanmis eksen).
NE TEST EDILMIYOR: Getiri tahmini (yazi-tura, sicil %49) -- onu forward-test'e sokmuyoruz.

Her satir: tarih, endeks_gun%, mevduat_gun%, rejim, stance_frac, stance_gun%
  endeks_gun%  = XU100 o gunku getirisi (tam hisse karsiligi)
  mevduat_gun% = TL mevduatin gunluk getirisi (~%45 yillik)
  rejim        = MEVDUAT/HISSE/NOTR LEHINE
  stance_frac  = rejimin onerdigi hisse agirligi (mevduat 0.5 / notr 0.75 / hisse 1.0)
  stance_gun%  = sistemin o gunku getirisi = endeks*frac + mevduat*(1-frac)

Zamanla bu CSV sunu gosterir: rejim-duruslu durmak, duz endeksi VE mevduati yendi mi?
Beceri mi, sadece beta mi? (Placebo'da cokmustu -- gercek ileri-test bunu canli olcer.)
"""
import csv, datetime, os
from app import rejim_hesapla          # ayni rejim mantigi, tek kaynak (app.py)

CSV = "ileri_gunluk.csv"
MEVDUAT_YILLIK = 45.0                  # TL mevduat ~ %45 yillik
STANCE = {"mevduat": 0.5, "notr": 0.75, "hisse": 1.0}

def endeks_gun():
    """XU100 gunluk getirisi (%). Cekilemezse None."""
    try:
        import yfinance as yf
        df = yf.download("XU100.IS", period="7d", interval="1d",
                         auto_adjust=True, progress=False)
        c = df["Close"].dropna().values.astype(float)
        if len(c) >= 2:
            return (float(c[-1]) / float(c[-2]) - 1) * 100
    except Exception as e:
        print("endeks cekilemedi:", e)
    return None

def main():
    bugun = datetime.date.today()
    rej = rejim_hesapla(bugun)
    frac = STANCE.get(rej["lehte"], 0.75)
    e = endeks_gun()
    mev = ((1 + MEVDUAT_YILLIK / 100) ** (1 / 252) - 1) * 100
    stance = (e * frac + mev * (1 - frac)) if e is not None else None

    row = [bugun.isoformat(),
           round(e, 3) if e is not None else "",
           round(mev, 4),
           rej["durus"],
           frac,
           round(stance, 3) if stance is not None else ""]
    head = ["tarih", "endeks_gun%", "mevduat_gun%", "rejim", "stance_frac", "stance_gun%"]

    yeni = not os.path.exists(CSV)
    if not yeni:  # ayni gun ikinci kez calisirsa tekrar yazma (idempotent)
        with open(CSV, encoding="utf-8") as f:
            if any(line.startswith(bugun.isoformat()) for line in f):
                print("bugun zaten kayitli, atlandi:", bugun.isoformat())
                return
    with open(CSV, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if yeni:
            w.writerow(head)
        w.writerow(row)
    print("eklendi:", row)

if __name__ == "__main__":
    main()
