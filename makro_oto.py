"""
APEX · MAKRO OTO-BESLEME — OECD'den enflasyon+faiz çeker, statik tabloyla AKILLI birleştirir.
Kurallar (dürüstlük öncelikli):
  • Statik tablo (makro_veri.MAKRO) TEMEL ve ÖNCELİKLİ — en güncel olan kazanır.
  • OECD yalnızca statiğin SON çeyreğinden YENİ + MAKUL çeyrekleri ekler (oto-devralma).
  • Herhangi bir hata/format değişimi → tamamen statiğe düşer (sessiz-hata yok).
  • OECD verisi ~birkaç ay gecikmeli; rejim işareti yavaş olduğu için sorun değil.
"""
import datetime, json, urllib.request, ssl
import makro_veri as base

ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
UA = {"User-Agent": "Mozilla/5.0 APEX", "Accept": "application/vnd.sdmx.data+json"}
CPI_URL = ("https://sdmx.oecd.org/public/rest/data/OECD.SDD.TPS,DSD_PRICES@DF_PRICES_ALL,"
           "/TUR.M.N.CPI.PA._T.N.GY?startPeriod=2024-01&dimensionAtObservation=AllDimensions&format=jsondata")
FAIZ_URL = ("https://sdmx.oecd.org/public/rest/data/OECD.SDD.STES,DSD_STES@DF_FINMARK,"
            "/TUR.M.IRSTCI.PA.....?startPeriod=2024-01&dimensionAtObservation=AllDimensions&format=jsondata")
_cache = None


def _get(url, t=25):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=t, context=ctx) as r:
            if r.status != 200: return None
            return r.read().decode("utf-8", "replace")
    except Exception:
        return None


def _ayikla(body):
    """SDMX-JSON v2 → {'YYYY-MM': deger} (en güncel ay kazanır)."""
    root = json.loads(body)
    st = root["data"]["structures"][0]["dimensions"]["observation"]
    tpos = next(i for i, d in enumerate(st) if d["id"] == "TIME_PERIOD")
    tvals = st[tpos]["values"]
    out = {}
    for key, arr in root["data"]["dataSets"][0]["observations"].items():
        out[tvals[int(key.split(":")[tpos])]["id"]] = arr[0]
    return out


def _ceyrege(aylik):
    """{'YYYY-MM':v} → {(yil,ceyrek): v}  (çeyreğin SON mevcut ayı)."""
    cey = {}
    for ay, v in sorted(aylik.items()):
        try:
            y, m = int(ay[:4]), int(ay[5:7])
        except Exception:
            continue
        cey[(y, (m - 1) // 3 + 1)] = v   # sıralı gittiği için son ay üzerine yazar
    return cey


def _oecd_ceyrek():
    cb, fb = _get(CPI_URL), _get(FAIZ_URL)
    if not cb: return {}
    try:
        cpi = _ceyrege(_ayikla(cb))
    except Exception:
        return {}
    faiz = {}
    if fb:
        try: faiz = _ceyrege(_ayikla(fb))
        except Exception: faiz = {}
    out = {}
    for q, enf in cpi.items():
        pol = faiz.get(q)
        if pol is None: continue
        if 0 < enf < 200 and 0 < pol < 200:        # makullük
            out[q] = (round(pol, 1), round(enf, 1))
    return out


def birlesik_tablo():
    """Statik taban + OECD'nin SADECE daha yeni çeyrekleri."""
    global _cache
    if _cache is not None: return _cache
    tablo = dict(base.MAKRO)
    son_statik = max(tablo.keys())
    oecd = _oecd_ceyrek()
    eklenen = []
    for q, val in sorted(oecd.items()):
        if q > son_statik:
            tablo[q] = val; eklenen.append(q)
    _cache = (tablo, son_statik, max(oecd) if oecd else None, eklenen)
    return _cache


def makro_at(tarih, lag_gun=35):
    if isinstance(tarih, datetime.datetime): tarih = tarih.date()
    tablo, _, _, _ = birlesik_tablo()
    en_iyi = None
    for (y, c), (pol, enf) in tablo.items():
        mevcut = base._ceyrek_sonu(y, c) + datetime.timedelta(days=lag_gun)
        if mevcut <= tarih and (en_iyi is None or mevcut > en_iyi[0]):
            en_iyi = (mevcut, pol, enf)
    if en_iyi is None: return None
    _, pol, enf = en_iyi
    return {"politika": pol, "enflasyon": enf, "reel": pol - enf}


def kaynak_durumu():
    tablo, son_statik, oecd_max, eklenen = birlesik_tablo()
    if oecd_max is None:
        return f"OECD oto-besleme: **erişilemedi** → tamamen statik tablo ({son_statik[0]}Ç{son_statik[1]})."
    if eklenen:
        return (f"OECD oto-besleme: **aktif ve devrede** → statik {son_statik[0]}Ç{son_statik[1]}'in ötesine "
                f"{len(eklenen)} çeyrek ekledi (son: {eklenen[-1][0]}Ç{eklenen[-1][1]}).")
    return (f"OECD oto-besleme: **bağlı ama beklemede** → OECD son verisi {oecd_max[0]}Ç{oecd_max[1]}, "
            f"statik tablo daha güncel ({son_statik[0]}Ç{son_statik[1]}). Statik kullanılıyor.")


if __name__ == "__main__":
    print(kaynak_durumu())
    print("bugün:", makro_at(datetime.date.today()))
