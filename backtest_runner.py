"""
APEX · MAKRO KAYNAK SONDASI — otomatik güncelleme için ABD'den erişilebilir kaynak var mı?
EVDS coğrafi-engelli (kanıtlı). Keysiz/US-erişilebilir adayları test eder:
  1) Dünya Bankası — TR yıllık TÜFE (FP.CPI.TOTL.ZG)  [keysiz, kesin US-OK, ama YILLIK+gecikmeli]
  2) Dünya Bankası — TR reel faiz (FR.INR.RINR)        [keysiz, yıllık]
  3) OECD SDMX — TR aylık TÜFE (YoY)                    [keysiz, AYLIK olabilir]
  4) OECD SDMX — TR kısa-vade faiz (STIR)               [keysiz, AYLIK olabilir]
Her biri için: HTTP durumu, JSON mu, ve EN SON değer+tarih. Tek seferlik teşhis.
"""
import datetime, json, urllib.request, ssl

ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
UA = {"User-Agent": "Mozilla/5.0 APEX-probe"}


def _get(url, timeout=25):
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
            body = r.read().decode("utf-8", "replace")
            ct = r.headers.get("Content-Type", "?")
            return r.status, ct, body
    except Exception as e:
        return None, None, f"HATA: {type(e).__name__}: {e}"


def dunya_bankasi(ind):
    url = f"https://api.worldbank.org/v2/country/TUR/indicator/{ind}?format=json&date=2022:2026&per_page=20"
    st, ct, body = _get(url)
    if st != 200: return f"❌ {ind}: durum={st} · {body[:80]}"
    try:
        data = json.loads(body)
        seri = data[1] if isinstance(data, list) and len(data) > 1 else []
        son = next((d for d in seri if d.get("value") is not None), None)
        if son: return f"✅ {ind}: {son['date']} → {son['value']:.1f}  (JSON ok)"
        return f"⚠️ {ind}: JSON ok ama değer yok"
    except Exception as e:
        return f"❌ {ind}: JSON değil · CT={ct} · {str(e)[:50]}"


def oecd(ad, url):
    st, ct, body = _get(url)
    if st is None: return f"❌ {ad}: {body[:80]}"
    is_json = "json" in (ct or "").lower()
    kafa = body[:90].replace("\n", " ")
    return f"{'✅' if (st==200 and is_json) else '⚠️' if st==200 else '❌'} {ad}: durum={st} · CT={ct} · gövde: «{kafa}»"


def calistir():
    L = ["# APEX — Makro Kaynak Sondası", "",
         f"_{datetime.datetime.now():%Y-%m-%d %H:%M} · otomatik güncelleme için kaynak araması_", "",
         "## 1-2) Dünya Bankası (keysiz, US-OK, ama yıllık+gecikmeli)", ""]
    L.append("- " + dunya_bankasi("FP.CPI.TOTL.ZG"))    # yıllık TÜFE %
    L.append("- " + dunya_bankasi("FR.INR.RINR"))         # reel faiz %
    L += ["", "## 3-4) OECD SDMX (keysiz, aylık olabilir)", ""]
    # OECD SDMX-JSON dener (kesin değil; gerçek yanıtı göreceğiz)
    oecd_cpi = ("https://sdmx.oecd.org/public/rest/data/OECD.SDD.TPS,DSD_PRICES@DF_PRICES_ALL,"
                "/TUR.M.N.CPI.PA._T.N.GY?startPeriod=2025-01&dimensionAtObservation=AllDimensions&format=jsondata")
    oecd_stir = ("https://sdmx.oecd.org/public/rest/data/OECD.SDD.STES,DSD_STES@DF_FINMARK,"
                 "/TUR.M.IR3TIB....?startPeriod=2025-01&dimensionAtObservation=AllDimensions&format=jsondata")
    L.append("- " + oecd("TR aylık TÜFE", oecd_cpi))
    L.append("- " + oecd("TR kısa-vade faiz", oecd_stir))
    L += ["", "## Yorum", "",
          "- Dünya Bankası ✅ ama YILLIK → çeyreklik rejim için fazla kaba/gecikmeli (tek başına yetmez).",
          "- OECD ✅ + JSON ise → aylık TÜFE & faiz otomasyonun çekirdeği olabilir.",
          "- Hepsi ❌/⚠️ ise → güvenilir US-kaynak yok; otomasyon yerine **10 saniyelik güvenli elle-ekle "
          "+ tazelik hatırlatıcısı** doğru tasarım (sessiz-hata riski yok).", ""]
    with open("BACKTEST_SONUC.md", "w", encoding="utf-8") as f:
        f.write("\n".join(L))
    print("\n".join(L)); print("\n>>> yazıldı.")


if __name__ == "__main__":
    calistir()
