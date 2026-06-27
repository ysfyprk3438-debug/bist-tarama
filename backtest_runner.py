"""APEX · EVDS TEŞHİS SONDASI (v10.2) — HTML mesajını oku + header/url anahtarı dene."""
import os, datetime, json, re, traceback
from urllib.parse import urlencode
import requests

EVDS_KEY = "GN8apnSEpG"
TEST = "TP.DK.USD.A.YTL"   # basit bilinen seri (USD alış) — değişkeni azaltmak için


def _temiz_html(s):
    s = re.sub(r"<script.*?</script>", " ", s, flags=re.S | re.I)
    s = re.sub(r"<style.*?</style>", " ", s, flags=re.S | re.I)
    s = re.sub(r"<[^>]+>", " ", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()[:280]


def dene(yontem):
    params = {"series": TEST, "startDate": "01-01-2024", "endDate": "01-06-2024",
              "type": "json", "frequency": "5", "aggregationTypes": "avg"}
    base = "https://evds2.tcmb.gov.tr/service/evds/"
    if yontem == "header":
        url = base + urlencode(params)
        headers = {"key": EVDS_KEY, "User-Agent": "Mozilla/5.0", "Accept": "application/json"}
    else:  # url-param (eski stil)
        p2 = dict(params); p2["key"] = EVDS_KEY
        url = base + urlencode(p2)
        headers = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}
    try:
        r = requests.get(url, headers=headers, timeout=30, verify=False)
        ct = r.headers.get("Content-Type", "")
        if "json" in ct.lower() or r.text.strip().startswith("{"):
            try:
                j = r.json(); n = len(j.get("items", []))
                return f"✅ JSON · {n} kayıt · HTTP {r.status_code}"
            except Exception:
                pass
        return f"❌ HTTP {r.status_code} · {ct} · mesaj: «{_temiz_html(r.text)}»"
    except Exception as e:
        return f"❌ {type(e).__name__}: {e}"


def calistir():
    import urllib3
    try: urllib3.disable_warnings()
    except Exception: pass
    L = ["# APEX — EVDS Teşhis", "", f"_{datetime.datetime.now():%Y-%m-%d %H:%M}_", "",
         f"Anahtar: {len(EVDS_KEY)} karakter (…{EVDS_KEY[-3:]})", "",
         "İki yöntem deneniyor (basit USD serisiyle):", ""]
    try:
        L.append(f"**1) Anahtar HEADER'da:** {dene('header')}")
        L.append("")
        L.append(f"**2) Anahtar URL'de:** {dene('url')}")
    except Exception:
        L.append("```"); L.append(traceback.format_exc()[:1200]); L.append("```")
    L.append("")
    L.append("> ✅ olan yöntem varsa onu kullanırız. İkisi de ❌ ve mesaj 'anahtar/key/invalid' diyorsa "
             "EVDS profilinden anahtarı tam kopyalamak gerekiyor (kısaltılmış olabilir).")
    m = "\n".join(L)
    with open("BACKTEST_SONUC.md", "w", encoding="utf-8") as f:
        f.write(m)
    print(m)


if __name__ == "__main__":
    calistir()
