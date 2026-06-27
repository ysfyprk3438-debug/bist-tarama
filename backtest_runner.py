"""
APEX · OECD AYIKLAMA SONDASI — bağlanmak değil, SAYIYI doğru çıkarmak.
OECD SDMX-JSON v2'den TR aylık YoY TÜFE'yi çekip son 4 (dönem, değer)'i yazdırır.
Değer ~%20-80 bandındaysa = doğru seri (YoY enflasyon). ~2000 ise = endeks (yanlış seri).
Faiz için düzeltilmiş 2 sorgu denenir, sadece durum/şekil raporlanır (ikincil).
"""
import datetime, json, urllib.request, ssl
ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
UA = {"User-Agent": "Mozilla/5.0 APEX-probe", "Accept": "application/vnd.sdmx.data+json"}


def _get(url, t=30):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=t, context=ctx) as r:
            return r.status, r.headers.get("Content-Type", "?"), r.read().decode("utf-8", "replace")
    except Exception as e:
        return None, None, f"{type(e).__name__}: {e}"


def ayikla(body):
    """SDMX-JSON v2 (dimensionAtObservation=AllDimensions) → [(donem, deger)] sıralı."""
    root = json.loads(body)
    struct = root["data"]["structures"][0]
    obsdims = struct["dimensions"]["observation"]
    tpos = next(i for i, d in enumerate(obsdims) if d["id"] == "TIME_PERIOD")
    tvals = obsdims[tpos]["values"]
    obs = root["data"]["dataSets"][0]["observations"]
    pairs = []
    for key, arr in obs.items():
        idx = int(key.split(":")[tpos])
        pairs.append((tvals[idx]["id"], arr[0]))
    pairs.sort()
    return pairs


def calistir():
    L = ["# APEX — OECD Ayıklama Sondası", "",
         f"_{datetime.datetime.now():%Y-%m-%d %H:%M} · sayıyı çıkarabiliyor muyuz?_", "",
         "## Enflasyon (TR aylık YoY TÜFE) — ASIL TEST", ""]
    cpi = ("https://sdmx.oecd.org/public/rest/data/OECD.SDD.TPS,DSD_PRICES@DF_PRICES_ALL,"
           "/TUR.M.N.CPI.PA._T.N.GY?startPeriod=2025-06&dimensionAtObservation=AllDimensions&format=jsondata")
    st, ct, body = _get(cpi)
    if st == 200 and "json" in (ct or "").lower():
        try:
            pairs = ayikla(body)[-4:]
            son_donem, son_deger = pairs[-1]
            makul = 10 <= son_deger <= 90
            L.append(f"Durum 200 · JSON ✅ · ayıklama **çalıştı**:")
            L.append("")
            L.append("| Dönem | YoY % |")
            L.append("|---|---:|")
            for d, v in pairs:
                L.append(f"| {d} | {v:.1f} |")
            L.append("")
            L.append(f"**Son: {son_donem} → %{son_deger:.1f}** · "
                     + ("✅ makul aralıkta (gerçek YoY enflasyon, doğru seri)" if makul
                        else "⚠️ aralık dışı — yanlış seri (endeks?) olabilir, kontrol gerek"))
        except Exception as e:
            L.append(f"Bağlantı 200 ama AYIKLAMA HATASI: {type(e).__name__}: {e}")
            try:
                root = json.loads(body)
                L.append(f"_kök anahtarlar: {list(root.keys())} · data: {list(root.get('data',{}).keys())}_")
            except Exception:
                L.append(f"_gövde başı: {body[:200]}_")
    else:
        L.append(f"❌ durum={st} · CT={ct} · {body[:120]}")

    L += ["", "## Faiz (TR kısa-vade) — ikincil, düzeltilmiş denemeler", ""]
    faiz_denemeler = [
        ("STES IR3TIB", "https://sdmx.oecd.org/public/rest/data/OECD.SDD.STES,DSD_STES@DF_FINMARK,"
         "/TUR.M.IRSTCI.PA.....?startPeriod=2025-06&dimensionAtObservation=AllDimensions&format=jsondata"),
        ("MEI STINT", "https://sdmx.oecd.org/public/rest/data/OECD.SDD.STES,DSD_STES@DF_FINMARK,/"
         "TUR.M.IR3TIB.?startPeriod=2025-06&dimensionAtObservation=AllDimensions&format=jsondata"),
    ]
    for ad, url in faiz_denemeler:
        st, ct, body = _get(url)
        if st == 200 and "json" in (ct or "").lower():
            try:
                pairs = ayikla(body)[-2:]
                L.append(f"- ✅ {ad}: ayıklandı → {pairs[-1][0]} = %{pairs[-1][1]:.1f}")
            except Exception as e:
                L.append(f"- ⚠️ {ad}: 200 ama ayıklama hatası ({type(e).__name__})")
        else:
            L.append(f"- ❌ {ad}: durum={st}")

    L += ["", "## Sonuç", "",
          "- Enflasyon ayıklaması ✅ + makul ise → otomasyonu logger'a bağlarız (enflasyon-oto + faiz-manuel hibrit).",
          "- Faiz denemelerinden biri ✅ ise bonus: onu da otomatiğe alırız.",
          "- Enflasyon ayıklaması bozuksa → format değişti, statik tablo + 10sn elle-ekle kalır (sistem zaten çalışıyor)."]
    with open("BACKTEST_SONUC.md", "w", encoding="utf-8") as f:
        f.write("\n".join(L))
    print("\n".join(L)); print("\n>>> yazıldı.")


if __name__ == "__main__":
    calistir()
