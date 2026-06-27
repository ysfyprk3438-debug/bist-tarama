"""
APEX · TEMEL VERİ (İş Yatırım mali tablo) — point-in-time temel faktörler
Sonda bulguları: sanayi=XI_29 (net kâr 3L, özkaynak 2N, satış 3C),
banka=UFRS (net kâr 3Z, özkaynak 2O). Endpoint (yıl,dönem) alır → geçmiş çeyrek tek tek.
Point-in-time: bir çeyrek ancak açıklanma tarihinden SONRA kullanılır (lookahead yok).
"""
import datetime
import requests

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
URL = "https://www.isyatirim.com.tr/_layouts/15/Isyatirim.Website/Common/Data.aspx/MaliTablo"

# kalem kodları (sondadan)
SANAYI = {"net_kar": "3L", "ozkaynak": "2N", "satis": "3C", "grup": "XI_29"}
BANKA  = {"net_kar": "3Z", "ozkaynak": "2O", "satis": None,  "grup": "UFRS"}


def donem_aciklanma(yil, period):
    """Bir çeyreğin verisinin GÜVENLE elde olduğu tarih (çeyrek sonu + ~75 gün lag)."""
    son_ay = {3: 3, 6: 6, 9: 9, 12: 12}[period]
    ceyrek_sonu = datetime.date(yil, son_ay, 28)
    return ceyrek_sonu + datetime.timedelta(days=75)


def mevcut_donemler(tarih, geri=8):
    """tarih itibarıyla AÇIKLANMIŞ son `geri` çeyreği (yeni→eski) döndürür."""
    out = []
    y = tarih.year + 1
    p_list = [12, 9, 6, 3]
    yy = y
    while len(out) < geri and yy > tarih.year - 6:
        for p in p_list:
            if donem_aciklanma(yy, p) <= tarih:
                out.append((yy, p))
                if len(out) >= geri:
                    break
        yy -= 1
    return out


def _fetch(kod, donemler, grup):
    p = {"companyCode": kod, "exchange": "TRY", "financialGroup": grup}
    for i, (yil, don) in enumerate(donemler[:4], 1):
        p[f"year{i}"] = yil; p[f"period{i}"] = don
    h = {"User-Agent": UA, "Referer": "https://www.isyatirim.com.tr/"}
    r = requests.get(URL, params=p, headers=h, timeout=20)
    if r.status_code != 200:
        return None
    val = r.json().get("value", [])
    if not val:
        return None
    # {itemCode: [v1,v2,v3,v4]}
    d = {}
    for it in val:
        kodu = it.get("itemCode")
        if kodu:
            d[kodu] = [it.get(f"value{i}") for i in range(1, 5)]
    return d


def _say(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def mali_al(kod, donemler):
    """(tip, data) — sanayi mi banka mı otomatik. donemler: en yeni 4 (yıl,period)."""
    for tip, M in [("sanayi", SANAYI), ("banka", BANKA)]:
        try:
            d = _fetch(kod, donemler, M["grup"])
        except Exception:
            d = None
        if d and M["net_kar"] in d and M["ozkaynak"] in d:
            return tip, d, M
    return None, None, None


def faktor_hesapla(kod, tarih):
    """tarih'te AÇIKLANMIŞ veriyle temel faktörler. Lookahead yok.
       Döner: {tip, net_kar_kumulatif, ozkaynak, roe, kar_buyume_yoy} | None."""
    donemler = mevcut_donemler(tarih, geri=8)
    if len(donemler) < 5:
        return None
    # en yeni 4 çeyrek tek fetch
    tip, d, M = mali_al(kod, donemler[:4])
    if d is None:
        return None
    nk = _say(d[M["net_kar"]][0])       # en yeni dönem kümülatif net kâr
    oz = _say(d[M["ozkaynak"]][0])      # en yeni özkaynak
    if nk is None or oz is None or oz == 0:
        return None
    roe = nk / oz                        # kümülatif (yıllıklaştırma backtest'te yapılır)
    # YoY kâr büyümesi: aynı dönem, 1 yıl önce (4 çeyrek geriden ayrı fetch)
    kar_yoy = None
    try:
        gecmis = donemler[4:8] if len(donemler) >= 8 else None
        if gecmis:
            _, d2, M2 = mali_al(kod, gecmis[:4])
            if d2 and M2["net_kar"] in d2:
                nk_eski = _say(d2[M2["net_kar"]][0])
                if nk_eski not in (None, 0):
                    kar_yoy = (nk / nk_eski - 1.0) if nk_eski > 0 else None
    except Exception:
        pass
    return {"tip": tip, "net_kar": nk, "ozkaynak": oz, "roe": roe, "kar_yoy": kar_yoy}


if __name__ == "__main__":
    # hızlı manuel sonda
    for k in ["EREGL", "GARAN", "ASELS"]:
        print(k, faktor_hesapla(k, datetime.date.today()))
