"""
═══════════════════════════════════════════════════════════════
SAĞLIK — APEX Hazırlık Kerterizi  (sürüm: saglik-1)
═══════════════════════════════════════════════════════════════
Sistemin KENDİ sağlığını ölçer. Piyasayı bilme skoru DEĞİL.

İki eksen:
  • Veri Kalitesi   (anlık)  — hata verince düşer  → depo + veri.py bayrakları
  • Kanıt Olgunluğu (zaman)   — birikince dolar     → ileri-test / karar / kalibrasyon

Hazırlık = Kanıt Olgunluğu × Veri Kalitesi  (kanıt dolmadan hazır olamazsın).

Saf mantık: hesapla(girdi, gecmis) → tüm dökümü döner. UI sadece çizer.
Eşikleri buradan değiştir.
"""

# ── EŞİKLER (tek yerden ayarla) ───────────────────────────────
ILK_OKUMA_GUN = 125     # ileri-test: ilk dürüst okuma
SAGLAM_GUN    = 250     # ileri-test: sağlam okuma
KARAR_HEDEF   = 30      # placebo testi için gereken kapalı karar


def _durum(oran, ok, warn):
    return "ok" if oran >= ok else ("warn" if oran >= warn else "bad")


def _bilesen(ad, deger, oran, agirlik, ok, warn, aciklama=""):
    oran = max(0.0, min(1.0, oran))
    return {"ad": ad, "deger": deger, "oran": round(oran, 3),
            "agirlik": agirlik, "durum": _durum(oran, ok, warn), "not": aciklama}


def veri_kalitesi(g):
    """g: ölçülen ham sayılar (app tarama sırasında doldurur)."""
    toplam = max(1, g["toplam_hisse"])
    bas    = max(1, g["basarili"])
    b = []
    b.append(_bilesen("Kapsama", f"{g['basarili']}/{g['toplam_hisse']}",
                       g["basarili"] / toplam, .25, .98, .90))
    b.append(_bilesen("Düzeltme (adjclose)", f"{g['adjclose']}/{g['basarili']}",
                       g["adjclose"] / bas, .20, .97, .85,
                       "ham gelen hisselerde bedelsiz/temettü düzeltmesi yok"))
    b.append(_bilesen("Kaynak (tam OHLC)", f"{g['yahoo']} Yahoo · {g['isyatirim']} İş Y.",
                       g["yahoo"] / bas, .15, .95, .80,
                       "İş Yatırım yedeğinde gerçek H/L yok → ATR vekil"))
    b.append(_bilesen("Tazelik", f"{g['guncel']}/{g['basarili']} güncel",
                       g["guncel"] / bas, .20, .98, .90))
    makro_oran = 1.0 - max(0, g["makro_gun"] - 90) / 90.0
    b.append(_bilesen("Makro tazeliği", f"{g['makro_gun']} gün",
                       makro_oran, .10, .99, .60, "~3 ayda bir elle güncellenir"))
    b.append(_bilesen("Temel kapsama", f"{g['temel_kapsam']}/{g['temel_hedef']}",
                       g["temel_kapsam"] / max(1, g["temel_hedef"]), .10, .95, .80))
    skor = round(100 * sum(x["oran"] * x["agirlik"] for x in b))
    return {"skor": skor, "bilesenler": b}


def kanit_olgunlugu(g):
    b = []
    b.append(_bilesen("İleri-test", f"{g['ileri_gun']}/{SAGLAM_GUN} gün",
                      min(1.0, g["ileri_gun"] / SAGLAM_GUN), .55,
                      SAGLAM_GUN / SAGLAM_GUN, ILK_OKUMA_GUN / SAGLAM_GUN,
                      "tek gerçek OOS · kalan = zaman"))
    b.append(_bilesen("Kapalı karar", f"{g['kapali_karar']}/{KARAR_HEDEF}",
                      min(1.0, g["kapali_karar"] / KARAR_HEDEF), .25, 1.0, .34,
                      f"placebo testi için ≥{KARAR_HEDEF} gerek"))
    b.append(_bilesen("Kalibrasyon", f"çözülen %{round(g['kalib_cozulen']*100)}",
                      g["kalib_cozulen"], .20, .70, .30))
    skor = round(100 * sum(x["oran"] * x["agirlik"] for x in b))
    return {"skor": skor, "bilesenler": b}


def _delta(simdi, gecmis, anahtar, geri=7):
    if not gecmis or len(gecmis) < 2:
        return None
    ref = gecmis[max(0, len(gecmis) - 1 - geri)]
    return round(simdi - ref.get(anahtar, simdi))


def hesapla(girdi, gecmis=None):
    vk = veri_kalitesi(girdi)
    ko = kanit_olgunlugu(girdi)
    hazirlik = round(ko["skor"] * vk["skor"] / 100)

    # düzeltilebilir vs zaman ayrımı
    eksik_temel = girdi["temel_hedef"] - girdi["temel_kapsam"]
    if eksik_temel > 0:
        kazanim = round((eksik_temel / max(1, girdi["temel_hedef"])) * .10 * 100)
        duzeltilebilir = f"{eksik_temel} hisse temel verisi eksik (+~%{kazanim})"
    elif girdi["adjclose"] < girdi["basarili"]:
        duzeltilebilir = f"{girdi['basarili']-girdi['adjclose']} hisse ham geldi — kaynağı kontrol et"
    else:
        duzeltilebilir = "yok — kalan mesafe tamamen zaman"

    eta = max(0, ILK_OKUMA_GUN - girdi["ileri_gun"])

    return {
        "hazirlik": hazirlik,
        "hazirlik_delta": _delta(hazirlik, gecmis, "hazirlik"),
        "veri_kalitesi": {**vk, "delta": _delta(vk["skor"], gecmis, "veri_kalitesi")},
        "kanit_olgunlugu": {**ko, "delta": _delta(ko["skor"], gecmis, "kanit_olgunlugu")},
        "eta_ilk_okuma_gun": eta,
        "ilk_okuma_gun": ILK_OKUMA_GUN,
        "saglam_gun": SAGLAM_GUN,
        "ileri_gun": girdi["ileri_gun"],
        "duzeltilebilir": duzeltilebilir,
        "gecmis_hazirlik": [x.get("hazirlik") for x in (gecmis or [])] + [hazirlik],
    }


# ── CANLI TOPLAYICI (app.py bunu çağırır) ─────────────────────
def topla(veri_durumlari, depo=None, makro_gun=None):
    """
    veri_durumlari: app taraması sırasında her hisse için veri_al() durum
                    etiketi listesi, örn ["yahoo:128:adjclose:tam", ...].
    depo: depo modülü (ileri_gunluk/karar sayıları için). Yoksa 0 sayılır.
    Tek tarama, çift iş yok — sayıları string etiketten çıkarır.
    """
    toplam = len(veri_durumlari)
    bas = adj = yah = isy = guncel = 0
    for d in veri_durumlari:
        if not d or ":" not in d:
            continue
        p = d.split(":")
        kaynak = p[0]
        if kaynak in ("yahoo", "isyatirim"):
            bas += 1
            if kaynak == "yahoo":
                yah += 1
            else:
                isy += 1
            if len(p) >= 3 and p[2] == "adjclose":
                adj += 1
            if len(p) >= 4 and p[3] == "tam":
                guncel += 1  # tam OHLC'yi tazelik vekili sayıyoruz (yedekte H/L yok)
    g = {
        "toplam_hisse": toplam or 1, "basarili": bas, "adjclose": adj,
        "yahoo": yah, "isyatirim": isy, "guncel": bas,  # tazelik ayrı ölçülebilir
        "makro_gun": makro_gun if makro_gun is not None else 999,
        "temel_kapsam": 0, "temel_hedef": 1,
        "ileri_gun": 0, "kapali_karar": 0, "kalib_cozulen": 0.0,
    }
    if depo is not None:
        try:
            il = depo.yukle("ileri_gunluk"); g["ileri_gun"] = len(il)
        except Exception:
            pass
        try:
            kd = depo.yukle("karar_defteri")
            if "sonuc" in getattr(kd, "columns", []):
                g["kapali_karar"] = int(kd["sonuc"].notna().sum())
        except Exception:
            pass
        try:
            tv = depo.yukle("temel_veri")
            g["temel_kapsam"] = len(tv) if hasattr(tv, "__len__") else 0
            g["temel_hedef"] = max(g["temel_kapsam"], 68)
        except Exception:
            pass
    return g
