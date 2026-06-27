"""
APEX · EVDS MAKRO SONDASI (v10.1 — hata-dayanıklı + SSL yedekli)
TCMB fonlama faizi (TP.APIFON4) + enflasyon (TP.FG.J0). Asla çökmez; hatayı rapora yazar.
"""
import os, datetime, json, traceback
from urllib.parse import urlencode
import requests

EVDS_KEY = "GN8apnSEpG"

FONLAMA = "TP.APIFON4"
TUFE    = "TP.FG.J0"


def _key():
    return EVDS_KEY or os.environ.get("EVDS_API_KEY", "")


def cek(seriler, bas="01-01-2017", bit=None, frekans="5", agg="avg"):
    bit = bit or datetime.date.today().strftime("%d-%m-%Y")
    params = {"series": "-".join(seriler), "startDate": bas, "endDate": bit,
              "type": "json", "frequency": frekans, "aggregationTypes": agg}
    url = "https://evds2.tcmb.gov.tr/service/evds/" + urlencode(params)
    h = {"key": _key(), "User-Agent": "Mozilla/5.0", "Accept": "application/json"}
    son_hata = None
    for ssl_dogrula in (True, False):       # SSL hatası olursa verify=False ile yeniden dene
        try:
            r = requests.get(url, headers=h, timeout=30, verify=ssl_dogrula)
            ct = r.headers.get("Content-Type", "")
            ham = r.text[:300]
            if r.status_code != 200:
                return None, f"HTTP {r.status_code} · CT={ct} · gövde: {ham}", url
            try:
                j = r.json()
            except Exception:
                return None, f"JSON değil · CT={ct} · gövde: {ham}", url
            items = j.get("items", [])
            return (items, f"OK {len(items)} kayıt", url) if items else (None, f"boş items · gövde: {ham}", url)
        except requests.exceptions.SSLError as e:
            son_hata = f"SSL: {e}"; continue
        except Exception as e:
            return None, f"{type(e).__name__}: {e}", url
    return None, son_hata or "bilinmeyen", url


def calistir():
    L = ["# APEX — EVDS Makro Sondası", "", f"_{datetime.datetime.now():%Y-%m-%d %H:%M}_", ""]
    try:
        k = _key()
        L.append(f"Anahtar uzunluğu: {len(k)} karakter " + (f"(…{k[-3:]})" if len(k) >= 3 else ""))
        L.append("")
        if not k:
            L.append("**Anahtar yok.**"); _yaz(L); return

        items, durum, url = cek([FONLAMA, TUFE])
        L.append(f"Durum: **{durum}**")
        L.append("")
        if not items:
            L.append("Veri gelmedi. Yukarıdaki gövde mesajı sebebi gösteriyor "
                     "(401/403 → anahtar; HTML → endpoint; SSL → sertifika).")
            _yaz(L); return

        f_col = FONLAMA.replace(".", "_"); t_col = TUFE.replace(".", "_")
        def g(d, c):
            for kk in d:
                if kk.replace(".", "_") == c:
                    try: return float(d[kk])
                    except (TypeError, ValueError): return None
            return None
        satir = [(it.get("Tarih", ""), g(it, f_col), g(it, t_col)) for it in items]
        L.append(f"**Aralık: {satir[0][0]} → {satir[-1][0]} · {len(satir)} ay**")
        L.append("")
        L.append("Son 8 ay (fonlama, yıllık enflasyon, reel faiz):")
        L.append("")
        L.append("| Ay | Fonlama % | Yıllık Enf. % | Reel Faiz % |")
        L.append("|---|---:|---:|---:|")
        ts = [s[2] for s in satir]
        for i in range(max(0, len(satir) - 8), len(satir)):
            tar, fon, tufe = satir[i]
            enf = (ts[i] / ts[i - 12] - 1) * 100 if (i >= 12 and ts[i] and ts[i - 12]) else None
            if fon is not None and enf is not None:
                L.append(f"| {tar} | {fon:.1f} | {enf:.1f} | {fon - enf:.1f} |")
            else:
                L.append(f"| {tar} | {fon} | {enf} | — |")
        L.append("")
        poz = sum(1 for i in range(12, len(satir))
                  if satir[i][1] is not None and ts[i] and ts[i-12]
                  and (satir[i][1] - (ts[i]/ts[i-12]-1)*100) > 0)
        L.append(f"> Reel faiz pozitif ay: {poz}/{len(satir)-12}. Veri 2017'ye uzanıyorsa rejim testi kurulabilir.")
    except Exception:
        L.append("```")
        L.append(traceback.format_exc()[:1500])
        L.append("```")
    _yaz(L)


def _yaz(L):
    m = "\n".join(L)
    with open("BACKTEST_SONUC.md", "w", encoding="utf-8") as f:
        f.write(m)
    print(m)


if __name__ == "__main__":
    calistir()
