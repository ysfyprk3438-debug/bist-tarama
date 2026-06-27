"""
APEX · EVDS MAKRO SONDASI (v10-probe)
TCMB'den fonlama faizi (TP.APIFON4) + enflasyon (TP.FG.J0) geliyor mu, 2017'ye uzanıyor mu?
Reel faiz = fonlama faizi − yıllık TÜFE. Rejim sinyalimizin ham maddesi.
ANAHTAR GEREKLİ: evds2.tcmb.gov.tr → ücretsiz kayıt → profil → API anahtarı.
Anahtarı aşağıdaki EVDS_KEY'e yapıştır (ya da ortam değişkeni EVDS_API_KEY).
"""
import os, datetime, json
from urllib.parse import urlencode
import requests

EVDS_KEY = "GN8apnSEpG"    # <<< BURAYA EVDS API ANAHTARINI YAPIŞTIR (tırnak içinde)

FONLAMA = "TP.APIFON4"   # Ağırlıklı Ortalama Fonlama Maliyeti (politika faizi vekili)
TUFE    = "TP.FG.J0"     # TÜFE Genel Endeks (2003=100)


def _key():
    return EVDS_KEY or os.environ.get("EVDS_API_KEY", "")


def cek(seriler, bas="01-01-2017", bit=None, frekans="5", agg="avg"):
    bit = bit or datetime.date.today().strftime("%d-%m-%Y")
    params = {"series": "-".join(seriler), "startDate": bas, "endDate": bit,
              "type": "json", "frequency": frekans, "aggregationTypes": agg}
    url = "https://evds2.tcmb.gov.tr/service/evds/" + urlencode(params)
    r = requests.get(url, headers={"key": _key(), "User-Agent": "Mozilla/5.0"}, timeout=25)
    if r.status_code != 200:
        return None, f"HTTP {r.status_code}: {r.text[:120]}"
    j = json.loads(r.content)
    items = j.get("items", [])
    return (items, f"OK {len(items)} ay") if items else (None, "boş items")


def calistir():
    L = ["# APEX — EVDS Makro Sondası (TCMB faiz + enflasyon)", "",
         f"_{datetime.datetime.now():%Y-%m-%d %H:%M}_", ""]
    if not _key():
        L += ["**API ANAHTARI YOK.**", "",
              "1. evds2.tcmb.gov.tr → sağ üst Giriş Yap → Kayıt Ol (ücretsiz, 2 dk).",
              "2. Mail onayı → profil → 'API Anahtarı' → kopyala.",
              "3. backtest_runner.py'de `EVDS_KEY = \"\"` satırına anahtarı yapıştır → commit → tekrar çalıştır.", ""]
        _yaz(L); return

    items, durum = cek([FONLAMA, TUFE])
    L.append(f"Çekme durumu: **{durum}**")
    L.append("")
    if not items:
        L += ["Veri gelmedi — anahtar yanlış olabilir ya da seri kodu değişmiş.", ""]
        _yaz(L); return

    # kolon adlarını tespit et (nokta → alt çizgi)
    f_col = FONLAMA.replace(".", "_"); t_col = TUFE.replace(".", "_")
    def g(d, c):
        for k in d:
            if k.replace(".", "_") == c:
                try: return float(d[k])
                except (TypeError, ValueError): return None
        return None

    satir = []
    for it in items:
        tar = it.get("Tarih", "")
        fon = g(it, f_col); tufe = g(it, t_col)
        satir.append((tar, fon, tufe))

    ilk = satir[0][0] if satir else "—"; sonn = satir[-1][0] if satir else "—"
    L.append(f"**Aralık: {ilk} → {sonn} · {len(satir)} ay**")
    L.append("")

    # yıllık enflasyon = TÜFE[t]/TÜFE[t-12]-1 ; reel faiz = fonlama - enflasyon
    L.append("Son 8 ay (fonlama faizi, yıllık TÜFE enflasyonu, reel faiz):")
    L.append("")
    L.append("| Ay | Fonlama % | Yıllık Enf. % | Reel Faiz % |")
    L.append("|---|---:|---:|---:|")
    tufe_seri = [s[2] for s in satir]
    for i in range(max(0, len(satir) - 8), len(satir)):
        tar, fon, tufe = satir[i]
        enf = None
        if i >= 12 and tufe_seri[i] and tufe_seri[i - 12]:
            enf = (tufe_seri[i] / tufe_seri[i - 12] - 1) * 100
        reel = (fon - enf) if (fon is not None and enf is not None) else None
        L.append(f"| {tar} | {fon:.1f} | {enf:.1f} | {reel:.1f} |"
                 if (fon is not None and enf is not None)
                 else f"| {tar} | {fon} | {enf} | — |")
    L.append("")
    # rejim örneği: tarih boyunca reel faiz işareti
    poz = sum(1 for i in range(12, len(satir))
              if satir[i][1] is not None and tufe_seri[i] and tufe_seri[i-12]
              and (satir[i][1] - (tufe_seri[i]/tufe_seri[i-12]-1)*100) > 0)
    top = len(satir) - 12
    L.append(f"> Reel faiz POZİTİF olan ay: {poz}/{top}. (Pozitif=mevduat cazip rejim, negatif=hisse rejimi hipotezi.)")
    L.append("")
    L.append("---\n*Format doğrulanınca: reel-faiz rejim anahtarı + temel-seçim backtest'i kurulacak (point-in-time).*")
    _yaz(L)


def _yaz(L):
    metin = "\n".join(L)
    with open("BACKTEST_SONUC.md", "w", encoding="utf-8") as f:
        f.write(metin)
    print(metin); print("\n>>> yazıldı.")


if __name__ == "__main__":
    calistir()
