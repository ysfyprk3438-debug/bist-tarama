# kap_oku.py — APEX bağlam katmanı · 1. tuğla (deterministik, LLM yok)
# Amaç: günün hareket eden hisselerini KAP açıklamalarıyla eşleştir.
#   "bu hareketin görünür sebebi var (KAP: ...)" / "sebep yok → spekülatif"
#
# DÜRÜST SINIR (CLAUDE.md §5, §7):
#   - Dış kaynak. Bağlanamazsa zarif fallback döner; SAHTE VERİ ASLA üretilmez.
#   - Sadece standart kütüphane (urllib) — ekstra kurulum gerekmez, her yerde çalışır.
#   - Kaynak: KAP byCriteria API (recon 2026-05-28). relatedStocks alanıyla eşleşir.

import json
import urllib.request
import http.cookiejar
from datetime import date, timedelta

KAP_URL = "https://www.kap.org.tr/tr/api/disclosure/members/byCriteria"
KAP_ISITMA = "https://www.kap.org.tr/tr/bildirim-sorgu"
UA = "apex-bist/0.1 (kisisel-arastirma)"
BASLIK = {
    "Content-Type": "application/json",
    "Referer": KAP_ISITMA,
    "User-Agent": UA,
    "Accept": "application/json",
}

# WAF, ısıtma GET'i ile çerez ister; opener çerezi taşısın diye tek opener kullanıyoruz.
_cj = http.cookiejar.CookieJar()
_opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(_cj))


def _isit(zaman_asimi=8):
    """KAP'a önce bir GET atıp oturum çerezini al (WAF zaman aşımını azaltır).
    Başarısız olsa da POST yine denenir; sessizce geç."""
    try:
        istek = urllib.request.Request(KAP_ISITMA, headers={"User-Agent": UA})
        _opener.open(istek, timeout=zaman_asimi).read()
    except Exception:
        pass


def kap_cek(gun=2, zaman_asimi=8):
    """Son `gun` günün TÜM KAP açıklamalarını çeker (liste döner).
    Başarısızsa istisna fırlatır — çağıran zarifçe yakalamalı."""
    _isit(zaman_asimi)
    bugun = date.today()
    govde = json.dumps({
        "fromDate": (bugun - timedelta(days=gun)).isoformat(),
        "toDate": bugun.isoformat(),
        "mkkMemberOidList": [],
        "subjectList": [],
    }).encode("utf-8")
    istek = urllib.request.Request(KAP_URL, data=govde, headers=BASLIK, method="POST")
    with _opener.open(istek, timeout=zaman_asimi) as cevap:
        ham = cevap.read().decode("utf-8", "replace")
    veri = json.loads(ham)
    if not isinstance(veri, list):
        raise ValueError("Beklenmeyen format: liste değil")
    return veri


def _tickerlar(kayit):
    """Bir KAP kaydındaki ilgili hisse kodlarını set olarak çıkarır."""
    kodlar = set()
    for alan in ("relatedStocks", "stockCodes"):
        deger = kayit.get(alan)
        if deger:
            for parca in str(deger).replace(";", ",").split(","):
                parca = parca.strip().upper()
                if parca:
                    kodlar.add(parca)
    return kodlar


def kap_eslesir(hisseler, gun=2):
    """hisseler: ['AKBNK','THYAO',...]. Dönüş:
       {hisse: [{tarih, konu, ozet, link}, ...], ..., '_durum':'acik'/'kapali', '_n':N}
    Bağlanamazsa {'_durum':'kapali','_hata':...} — sahte veri yok."""
    hedef = {str(h).strip().upper() for h in hisseler if h and str(h).strip()}
    try:
        kayitlar = kap_cek(gun=gun)
    except Exception as e:
        return {"_durum": "kapali", "_hata": f"{type(e).__name__}: {e}", "_n": 0}

    sonuc = {h: [] for h in hedef}
    for k in kayitlar:
        if not isinstance(k, dict):
            continue
        ortak = _tickerlar(k) & hedef
        if not ortak:
            continue
        idx = k.get("disclosureIndex")
        kayit = {
            "tarih": (k.get("publishDate") or "").strip(),
            "konu": (k.get("subject") or k.get("disclosureCategory") or "").strip(),
            "ozet": (k.get("summary") or "").strip(),
            "link": f"https://www.kap.org.tr/tr/Bildirim/{idx}" if idx else "",
        }
        for h in ortak:
            sonuc[h].append(kayit)
    sonuc["_durum"] = "acik"
    sonuc["_n"] = len(kayitlar)
    return sonuc


if __name__ == "__main__":
    # TANI MODU — yerelde çalıştır: python kap_oku.py
    print("KAP baglanti testi (son 2 gun)...")
    try:
        kayitlar = kap_cek(gun=2)
        print(f"  ✓ BAGLANDI · {len(kayitlar)} aciklama")
        if kayitlar:
            print("  Ilk kaydin alanlari:", sorted(kayitlar[0].keys()))
            print("  Ornek kayitlar:")
            for k in kayitlar[:5]:
                print("   -", k.get("publishDate"), "|",
                      k.get("relatedStocks"), "|",
                      (k.get("subject") or "")[:45])
        test = kap_eslesir(["THYAO", "AKBNK", "GARAN", "ASELS", "SASA", "EREGL"], gun=2)
        bulunan = {h: len(v) for h, v in test.items() if not h.startswith("_")}
        print("  Eslesme testi:", bulunan)
    except Exception as e:
        print(f"  ✗ BAGLANAMADI: {type(e).__name__}: {e}")
        print("  Not: WAF/ag/IP engeli olabilir. Ciktiyi bana ilet, ona gore ayarlariz.")
