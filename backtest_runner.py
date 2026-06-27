"""
APEX · TEMEL VERİ SONDASI (v8-probe)
Amaç: İş Yatırım mali-tablo endpoint'i ÇALIŞIYOR mu, format ne? GÖRELİM.
Büyük backtest'i kurmadan önce veri borusunu kanıtla (banka + sanayi).
Çıktı: hangi financialGroup işe yaradı + ilk ~25 kalem (kod | açıklama | son 4 dönem).
~30 saniye. Bunu görünce gerçek parser'ı yazarız.
"""
import datetime, json
import requests

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
URL = "https://www.isyatirim.com.tr/_layouts/15/Isyatirim.Website/Common/Data.aspx/MaliTablo"

# son 4 çeyrek (yıl, dönem) — dönem: 3/6/9/12 (kümülatif çeyrek)
def son_donemler():
    bugun = datetime.date.today()
    y = bugun.year
    # kabaca son 4 çeyreği geriye doğru üret
    cer = [(y, 3), (y - 1, 12), (y - 1, 9), (y - 1, 6)]
    return cer

GRUPLAR = ["XI_29", "UFRS", "UFRS_K", ""]   # sanayi / genel / banka / boş(auto)
TESTLER = [("EREGL", "sanayi"), ("GARAN", "banka")]


def dene(kod, grup, donemler):
    p = {"companyCode": kod, "exchange": "TRY", "financialGroup": grup}
    for i, (yil, don) in enumerate(donemler, 1):
        p[f"year{i}"] = yil
        p[f"period{i}"] = don
    h = {"User-Agent": UA, "Referer": "https://www.isyatirim.com.tr/"}
    try:
        r = requests.get(URL, params=p, headers=h, timeout=20)
        if r.status_code != 200:
            return None, f"HTTP {r.status_code}"
        j = r.json()
        val = j.get("value", [])
        return (val, f"OK {len(val)} kalem") if val else (None, "boş value")
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"


def calistir():
    L = ["# APEX — Temel Veri Sondası (İş Yatırım mali tablo)", "",
         f"_{datetime.datetime.now():%Y-%m-%d %H:%M} · endpoint format keşfi_", ""]
    donemler = son_donemler()
    L.append(f"Denenen dönemler (yıl/dönem): {donemler}")
    L.append("")

    for kod, tip in TESTLER:
        L.append(f"## {kod} ({tip})")
        basarili_grup = None; veri = None
        for grup in GRUPLAR:
            val, durum = dene(kod, grup, donemler)
            L.append(f"- financialGroup=`{grup or 'boş'}` → {durum}")
            if val and basarili_grup is None:
                basarili_grup = grup; veri = val
        L.append("")
        if veri:
            L.append(f"**Çalışan grup: `{basarili_grup or 'boş'}`. İlk 25 kalem:**")
            L.append("")
            L.append("| itemCode | açıklama | d1 | d2 | d3 | d4 |")
            L.append("|---|---|---:|---:|---:|---:|")
            for it in veri[:25]:
                kodu = str(it.get("itemCode", ""))[:14]
                ack = str(it.get("itemDescTr", ""))[:40].replace("|", "/")
                v = [it.get(f"value{i}") for i in range(1, 5)]
                vv = [("" if x is None else (f"{float(x):,.0f}" if isinstance(x, (int, float)) else str(x)[:12])) for x in v]
                L.append(f"| {kodu} | {ack} | {vv[0]} | {vv[1]} | {vv[2]} | {vv[3]} |")
            L.append("")
            # kâr/özkaynak/satış kalemlerini ara (parser ipucu)
            L.append("**Anahtar kalem araması (net kâr / özkaynak / satış):**")
            anahtar = ["NET KAR", "DÖNEM KAR", "KAR/ZARAR", "KARI/ZARARI", "ÖZKAYNAK",
                       "SATIŞ", "HASILAT", "ESAS FAALİYET", "FAVÖK", "TOPLAM VARLIK"]
            for it in veri:
                ad = str(it.get("itemDescTr", "")).upper()
                if any(a in ad for a in anahtar):
                    v1 = it.get("value1")
                    L.append(f"- `{it.get('itemCode','')}` {str(it.get('itemDescTr',''))[:45]} = {v1}")
            L.append("")
        else:
            L.append("**Hiçbir grup veri döndürmedi — endpoint/param değişmiş olabilir, formatı revize edeceğiz.**")
            L.append("")

    L.append("---\n*Bu bir sonda: format doğrulanınca point-in-time temel-seçim backtest'ini buna göre kuracağız.*")
    metin = "\n".join(L)
    with open("BACKTEST_SONUC.md", "w", encoding="utf-8") as f:
        f.write(metin)
    print(metin); print("\n>>> yazıldı.")


if __name__ == "__main__":
    calistir()
