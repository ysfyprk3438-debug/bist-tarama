# -*- coding: utf-8 -*-
"""
akd_oto_topla.py — ForInvest AKD ham verisini gunluk toplayip akd_oto_arsiv.csv'ye yazar.

BAGIMSIZ modul. akd_cekici.akd_cek (HAM JSON) uzerine kurulur — akd_ozet DEGIL, cunku
pct ve custodian icin ham grand alanlar (gbv/gsv) ve kurum ADI (c) gerekli.

FELSEFE (CLAUDE.md): SADECE veri girisi. Yon tahmini / AL-SAT / skor YOK.
"Gecmiste su kurum su kadar net yapti" — gozlem, kehanet degil.

GUVENLIK: token yalnizca os.environ["FOREKS_AUTH"] (akd_cek icinden). Token hicbir
dosyaya/log'a YAZILMAZ. Yoksa temiz hata + dur.

KAPSAM: manuel/lokal calisir (kullanici token export edip elle kosar). CRON/otomatik
dongu BU DOSYADA YOK — token omru olculmeden zamanlanmis is token'i canli tutamaz.
"""

import csv
import os
import sys
from datetime import date

from akd_cekici import akd_cek, _token

# ── SABITLER ────────────────────────────────────────────────────────
OTO_CSV = "akd_oto_arsiv.csv"
BASLIK = ["tarih_baslangic", "tarih_bitis", "hisse", "donem_tipi", "ilk5_net_lot",
          "lider_alici", "lider_alici_pct", "lider_satici", "lider_satici_pct",
          "custodian_net_lot", "not", "kaynak"]

# Sabit izleme listesi (token omru netlesince genisletilir — 97 DEGIL)
IZLEME = ["AKBNK", "ASELS", "EREGL", "GARAN", "THYAO", "TUPRS", "AKFGY"]

ILK5 = 5   # "ilk 5" = en aktif (tv'ye gore) 5 kurum

# Saklamaci (custodian) tespiti: kurum ADI (c) icinde gecen anahtar parcalar (kucuk harf).
# Canli veride gercek 'c' degerleri gorulunce ayarlanabilir.
CUSTODIAN_ANAHTAR = {
    "bofa", "bank of america", "merrill", "citi", "deutsche",
    "jp morgan", "jpmorgan", "morgan stanley", "barclays", "hsbc",
    "bnp", "ubs", "goldman", "credit suisse",
}


# ── YARDIMCI ────────────────────────────────────────────────────────
def _sayi(x):
    if x is None:
        return None
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def _ad(it):
    """Kurum adi: ham 'c' (isim) tercih; yoksa 'code'."""
    return (str(it.get("c") or it.get("code") or "")).strip()


def _custodian_mu(it):
    ad = _ad(it).lower()
    return any(k in ad for k in CUSTODIAN_ANAHTAR)


# ── HISSE OZETI (ham JSON -> tek satir) ─────────────────────────────
def hisse_ozet(kod, fetch_tarih, iso_tarih):
    """
    Bir hissenin tek gunluk ham AKD'sini manuel-arsiv semasindaki TEK satira toplar.
    fetch_tarih: akd_cek'e verilecek date objesi (URL YYYYMMDD icin).
    iso_tarih:  CSV'ye yazilacak 'YYYY-MM-DD'.
    Doner: dict | None (veri yok).

    Alan tanimlari (seffaf, gerekince ayarlanabilir):
      ilk5_net_lot      = en aktif 5 kurumun (tv desc) net adet (na) toplami
      lider_alici       = en yuksek pozitif net adet (na) kurumu; pct = tbv/gbv
      lider_satici      = en dusuk negatif net adet (na) kurumu; pct = tsv/gsv
      custodian_net_lot = adi custodian anahtarina uyan kurumlarin na toplami
    """
    data = akd_cek(kod, fetch_tarih)
    if not data:
        return None
    kurumlar = [it for it in (data.get("i") or []) if isinstance(it, dict)]
    if not kurumlar:
        return None

    gbv = _sayi(data.get("gbv"))
    gsv = _sayi(data.get("gsv"))

    def na(it):
        return _sayi(it.get("na"))

    # ilk5: en aktif 5 kurum (tv'ye gore), net adet topla
    aktif = sorted(kurumlar, key=lambda it: (_sayi(it.get("tv")) or 0.0), reverse=True)[:ILK5]
    ilk5_net = sum((na(it) or 0.0) for it in aktif)

    # lider alici / satici (net adete gore)
    netli = [(it, na(it)) for it in kurumlar if na(it) is not None]
    lider_a = max(netli, key=lambda p: p[1], default=(None, None))
    lider_s = min(netli, key=lambda p: p[1], default=(None, None))

    def _pct(it, grand, key):
        v = _sayi(it.get(key))
        if v is None or not grand or grand <= 0:
            return ""
        return round(v / grand * 100, 2)

    if lider_a[0] is not None and lider_a[1] is not None and lider_a[1] > 0:
        la_ad = _ad(lider_a[0]); la_pct = _pct(lider_a[0], gbv, "tbv")
    else:
        la_ad = ""; la_pct = ""
    if lider_s[0] is not None and lider_s[1] is not None and lider_s[1] < 0:
        ls_ad = _ad(lider_s[0]); ls_pct = _pct(lider_s[0], gsv, "tsv")
    else:
        ls_ad = ""; ls_pct = ""

    cust = sum((na(it) or 0.0) for it in kurumlar if _custodian_mu(it))

    return {
        "tarih_baslangic": iso_tarih, "tarih_bitis": iso_tarih, "hisse": kod,
        "donem_tipi": "gunluk", "ilk5_net_lot": int(round(ilk5_net)),
        "lider_alici": la_ad, "lider_alici_pct": la_pct,
        "lider_satici": ls_ad, "lider_satici_pct": ls_pct,
        "custodian_net_lot": int(round(cust)),
        "not": "oto: ForInvest akd_cekici", "kaynak": "oto",
    }


# ── YAZIM (idempotent: ayni hisse+tarih tekrar yazilmaz) ────────────
def yaz(satirlar):
    mevcut = set()
    rows = []
    if os.path.exists(OTO_CSV):
        try:
            with open(OTO_CSV, encoding="utf-8") as f:
                for r in csv.DictReader(f):
                    rows.append(r)
                    mevcut.add((r.get("hisse"), r.get("tarih_bitis")))
        except Exception:
            rows = []; mevcut = set()
    eklenen = 0
    for s in satirlar:
        anahtar = (s["hisse"], s["tarih_bitis"])
        if anahtar in mevcut:
            continue
        rows.append(s); mevcut.add(anahtar); eklenen += 1
    if eklenen:
        with open(OTO_CSV, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=BASLIK)
            w.writeheader()
            for r in rows:
                w.writerow({k: r.get(k, "") for k in BASLIK})
    return eklenen


# ── ANA AKIS ────────────────────────────────────────────────────────
def main(tarih_arg=None):
    # Token yoksa 7 kez patlamak yerine bir kez kontrol et, temiz cik.
    try:
        _token()
    except RuntimeError as e:
        print(f"HATA: {e}")
        return 1

    if tarih_arg:
        try:
            d = date.fromisoformat(tarih_arg)
        except ValueError:
            print(f"HATA: tarih 'YYYY-MM-DD' olmali (verilen: {tarih_arg}).")
            return 1
    else:
        d = date.today()
    iso = d.isoformat()

    satirlar = []; atlanan = []
    for kod in IZLEME:
        try:
            oz = hisse_ozet(kod, d, iso)
        except Exception as e:
            oz = None
            print(f"{kod}: hata ({type(e).__name__}), atlandi")
        if oz:
            satirlar.append(oz)
            print(f"{kod}: ilk5_net={oz['ilk5_net_lot']:>12} · lider_al={oz['lider_alici'] or '—'} "
                  f"({oz['lider_alici_pct'] or '—'}) · lider_sat={oz['lider_satici'] or '—'} "
                  f"({oz['lider_satici_pct'] or '—'}) · custodian_net={oz['custodian_net_lot']:>12}")
        else:
            atlanan.append(kod)
            print(f"{kod}: veri alinamadi, atlandi")

    eklenen = yaz(satirlar)
    print(f"\n{eklenen} yeni satir -> {OTO_CSV} · {len(atlanan)} hisse atlandi · tarih {iso}")
    print("(Gozlem — yon tahmini/AL-SAT DEGIL. Yatirim tavsiyesi degildir.)")
    return 0


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else None
    sys.exit(main(arg))
