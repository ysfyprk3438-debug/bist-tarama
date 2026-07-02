# -*- coding: utf-8 -*-
"""
akd_cekici.py — ForInvest AKD (Aracı Kurum Dağılımı) çekici. BAĞIMSIZ modül.

Streamlit importu YOK. Sadece stdlib + requests.
Token GUVENLIGI: token yalnizca os.environ["FOREKS_AUTH"]'dan okunur; ASLA koda
gomulmez, ASLA dosyaya/log'a yazilmaz. Yoksa net hata ile durur.

Veri kaynagi (F12 ile kesfedildi):
  GET https://web-cloud-new.foreks.com/web-services/historical-data/akd/consolidate/
      code/{KOD}.E.BIST/type/E/from/{YYYYMMDD}/to/{YYYYMMDD}
  Baslik: "Foreks-Auth: <token>"
  Yanit: application/json — ustte ozet (gsa, gta, gbv, gsv, gna, gnv...),
         altta "i": [ {code, tsa, tv, c, ...} ] araci kurum dizisi.

FELSEFE (CLAUDE.md): bu SADECE veri girisidir. Yon tahmini / AL-SAT / skor YOK.
"Gecmiste su kurum su kadar net yapti" — gozlem, kehanet degil.
"""

import csv
import logging
import os
import sys
from datetime import date, datetime

import requests

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
_log = logging.getLogger("akd_cekici")

BASE_URL = ("https://web-cloud-new.foreks.com/web-services/historical-data/akd/"
            "consolidate/code/{kod}.E.BIST/type/E/from/{gun}/to/{gun}")
ZAMAN_ASIMI = 10  # saniye


# ── TOKEN (yalniz env; koda/dosyaya/log'a yazilmaz) ─────────────────
def _token():
    t = os.environ.get("FOREKS_AUTH", "").strip()
    if not t:
        raise RuntimeError(
            "FOREKS_AUTH ortam degiskeni tanimli degil. Once terminalde:\n"
            "    export FOREKS_AUTH='<token>'\n"
            "Token koda/repoya YAZILMAZ; yalnizca env'den okunur."
        )
    return t


# ── YARDIMCI ────────────────────────────────────────────────────────
def _sayi(x):
    """Guvenli float. Bos/bozuk -> None."""
    if x is None:
        return None
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def _ilk_var(d, adaylar):
    """d icinde adaylar listesinden ilk None-olmayan degeri dondur."""
    for a in adaylar:
        if a in d and d[a] is not None:
            return d[a]
    return None


def _gun_str(tarih):
    if tarih is None:
        tarih = date.today()
    return tarih.strftime("%Y%m%d") if hasattr(tarih, "strftime") else str(tarih)


# ── HAM CEKIM ───────────────────────────────────────────────────────
def akd_cek(kod, tarih=None):
    """
    Bir hissenin tek gunluk AKD JSON'unu getirir.
    Doner: dict (ham JSON) | None (hata/bos/timeout).
    Token yoksa RuntimeError yukseltir (cagiran karar versin).
    """
    gun = _gun_str(tarih)
    url = BASE_URL.format(kod=str(kod).upper().strip(), gun=gun)
    token = _token()  # yoksa RuntimeError

    try:
        r = requests.get(
            url,
            headers={"Foreks-Auth": token, "Accept": "application/json"},
            timeout=ZAMAN_ASIMI,
        )
    except requests.exceptions.Timeout:
        _log.error(f"{kod}: zaman asimi ({ZAMAN_ASIMI}s).")
        return None
    except requests.exceptions.RequestException as e:
        _log.error(f"{kod}: istek hatasi: {type(e).__name__}")
        return None

    if r.status_code == 401 or r.status_code == 403:
        _log.error(f"{kod}: yetki reddedildi (HTTP {r.status_code}) — token gecersiz/suresi dolmus olabilir.")
        return None
    if r.status_code != 200:
        _log.error(f"{kod}: beklenmeyen HTTP {r.status_code}.")
        return None

    try:
        data = r.json()
    except ValueError:
        _log.error(f"{kod}: yanit JSON degil.")
        return None

    if not data or not isinstance(data, dict):
        _log.error(f"{kod}: bos/gecersiz JSON yapisi.")
        return None
    return data


# ── NORMALIZE ───────────────────────────────────────────────────────
def _normalize(data):
    """
    Ham AKD JSON'undaki i[] dizisini sadelestir.
    Doner: [{kurum, net_lot, hacim}, ...]  (bos -> []).

    Alan eslemesi (canli GARAN testiyle DOGRULANDI — ham anahtarlar:
      bp c code na nv sp ta tba tbuv tbv tsa tsuv tsv tv):
      kurum   <- code
      net_lot <- 'na' (net adet, kaynak dogrudan verir; tum kurumlar toplami = 0).
                 na yoksa: tba (toplam alis adet) - tsa (toplam satis adet).
                 NOT: 'ta' KULLANILMAZ — o toplam adet (alis+satis), net degil.
      hacim   <- 'tv' (toplam deger).
    """
    if not isinstance(data, dict):
        return []
    kurumlar = data.get("i") or []
    out = []
    for it in kurumlar:
        if not isinstance(it, dict):
            continue
        kurum = _ilk_var(it, ["code", "c"])
        net = _sayi(it.get("na"))               # birincil: kaynagin net adedi
        if net is None:                          # yedek: alis adet - satis adet
            alis = _sayi(it.get("tba"))
            satis = _sayi(it.get("tsa"))
            if alis is not None and satis is not None:
                net = alis - satis
        hacim = _sayi(it.get("tv"))
        out.append({"kurum": kurum, "net_lot": net, "hacim": hacim})
    return out


def akd_ozet(kod, tarih=None):
    """kod icin normalize edilmis AKD listesi: [{kurum, net_lot, hacim}]. Bos -> []."""
    return _normalize(akd_cek(kod, tarih))


# ── KONSOL (test) ───────────────────────────────────────────────────
def _konsol(kod):
    try:
        data = akd_cek(kod)
    except RuntimeError as e:
        print(f"HATA: {e}")
        return 1
    if not data:
        print(f"{kod}: AKD verisi alinamadi (yukaridaki log'a bak).")
        return 1

    # Ust ozet alanlari (varsa) — kaynak seması dogrulamasi icin
    ozet_alan = {k: data[k] for k in ("gsa", "gta", "gbv", "gsv", "gna", "gnv") if k in data}
    kurumlar = data.get("i") or []
    print(f"=== AKD ozeti: {str(kod).upper()}  ({date.today().isoformat()}) ===")
    if ozet_alan:
        print("Genel ozet:", ozet_alan)
    print(f"Kurum sayisi: {len(kurumlar)}")
    if kurumlar and isinstance(kurumlar[0], dict):
        # Canli dogrulama icin: ilk kaydin HAM anahtarlari (alan eslemesini teyit ederiz)
        print("Ham item anahtarlari (dogrulama):", sorted(kurumlar[0].keys()))

    liste = _normalize(data)
    print("\nIlk 5 kurum:")
    for r in liste[:5]:
        nl = "—" if r["net_lot"] is None else f"{r['net_lot']:,.0f}"
        hc = "—" if r["hacim"] is None else f"{r['hacim']:,.0f}"
        print(f"  {str(r['kurum'] or '?'):<8}  net_lot={nl:>15}  hacim={hc:>18}")

    net_toplam = sum(r["net_lot"] for r in liste if r["net_lot"] is not None)
    hac_toplam = sum(r["hacim"] for r in liste if r["hacim"] is not None)
    print(f"\nTOPLAM ({len(liste)} kurum): net_lot={net_toplam:,.0f}  hacim={hac_toplam:,.0f}")
    print("\n(Gozlem — yon tahmini/AL-SAT DEGIL. Yatirim tavsiyesi degildir.)")
    return 0


# ── TOKEN TESHIS (--tokentest) ──────────────────────────────────────
GUNLUK_CSV = "token_gunluk.csv"          # yerel olcum gunlugu (gitignore'lu, repoya girmez)
GUNLUK_BASLIK = ["tarih", "saat", "durum", "http_kodu"]


def _gunluk_yaz(durum, http_kodu):
    """
    token_gunluk.csv'ye tek satir ekler: tarih, saat, durum, http_kodu.
    Dosya yoksa baslikla olusturur, varsa append eder.
    TOKEN ASLA YAZILMAZ — yalnizca sonuc. Yazim hatasi olcumu bozmaz (sessiz gec).
    """
    try:
        simdi = datetime.now()
        yeni = not os.path.exists(GUNLUK_CSV)
        with open(GUNLUK_CSV, "a", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            if yeni:
                w.writerow(GUNLUK_BASLIK)
            w.writerow([simdi.strftime("%Y-%m-%d"), simdi.strftime("%H:%M:%S"),
                        durum, "" if http_kodu is None else http_kodu])
    except Exception as e:
        _log.warning(f"token_gunluk yazilamadi: {type(e).__name__}")


def token_testi(kod="GARAN"):
    """
    Sadece token GECERLI mi diye bakar — VERI PARSE ETMEZ.
    HTTP durum kodunu ve GECERLI/GECERSIZ yazar. Token omru olcumu icin:
        python akd_cekici.py --tokentest
    Ek olarak sonucu token_gunluk.csv'ye tek satir kaydeder (token yazilmaz).
    Doner (exit): 0 gecerli · 1 gecersiz(401/403)/token-yok · 2 belirsiz.
    """
    try:
        token = _token()
    except RuntimeError as e:
        print(f"HATA: {e}")
        return 1                          # token yok = olcum degil, gunluge yazilmaz
    url = BASE_URL.format(kod=str(kod).upper().strip(), gun=_gun_str(None))
    try:
        r = requests.get(
            url,
            headers={"Foreks-Auth": token, "Accept": "application/json"},
            timeout=ZAMAN_ASIMI,
        )
    except requests.exceptions.RequestException as e:
        print(f"HTTP: istek gonderilemedi ({type(e).__name__}) — token durumu BELIRSIZ (ag sorunu?).")
        _gunluk_yaz("BELIRSIZ", "")
        return 2
    print(f"HTTP durum: {r.status_code}")
    if r.status_code == 200:
        print("token GECERLI")
        _gunluk_yaz("GECERLI", r.status_code)
        return 0
    if r.status_code in (401, 403):
        print(f"token GECERSIZ ({r.status_code})")
        _gunluk_yaz("GECERSIZ", r.status_code)
        return 1
    print(f"token durumu BELIRSIZ (HTTP {r.status_code}) — 200 degil, 401/403 da degil.")
    _gunluk_yaz("BELIRSIZ", r.status_code)
    return 2


if __name__ == "__main__":
    args = sys.argv[1:]
    if args and args[0] == "--tokentest":
        sys.exit(token_testi())
    kod = args[0] if args else "GARAN"
    sys.exit(_konsol(kod))
