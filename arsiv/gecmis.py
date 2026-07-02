"""
═══════════════════════════════════════════════════════════════
GEÇMİŞ + ÖZ-ÖLÇÜM — BIST Para Avcısı v4
═══════════════════════════════════════════════════════════════
Sistem kendi sinyallerini takip eder, başarısını ölçer,
bu bilgiyi Güven Motoru'na geri besler.

Döngü:
  1. Sinyal üret → kaydet (sinyal_kaydet)
  2. X gün sonra → sonuç kontrol (sonuc_kontrol)
  3. Başarı oranı → güven motoruna besle (basari_orani)

Depolama: Supabase varsa orada, yoksa session_state'te.
"""

import datetime


# ══════════════════════════════════════════════════════════════
# SİNYAL KAYIT
# ══════════════════════════════════════════════════════════════
def sinyal_kaydet(gecmis, r):
    """
    Analiz sonucunu geçmiş listesine ekle.
    gecmis: session_state["gecmis"] (liste)
    r: analiz_et sonucu
    """
    # Aynı hisse bugün zaten kayıtlıysa güncelle
    bugun = datetime.date.today().isoformat()
    for kayit in gecmis:
        if kayit["kod"] == r["kod"] and kayit["giris_tarih"] == bugun:
            return  # zaten var

    gecmis.append({
        "kod": r["kod"],
        "sinyal_tip": r["sinyal"],       # "AL · Güçlü", "DİP FIRSATI" vs
        "niyet_sinif": r.get("niyet", {}).get("sinif", "NORMAL"),
        "giris_fiyat": r["son"],
        "hedef": r["hedef"],
        "stop": r["stop"],
        "puan": r["puan"],
        "guven_yuzde": r.get("guven", {}).get("yuzde", 50),
        "giris_tarih": bugun,
        "kontrol_tarih": None,           # sonuç kontrol edildiğinde dolar
        "sonuc": None,                   # "HEDEF" | "STOP" | "BEKLEMEDE" | "SURE_DOLDU"
        "cikis_fiyat": None,
        "getiri_pct": None,
        "gun_sayisi": None,
    })


# ══════════════════════════════════════════════════════════════
# SONUÇ KONTROL
# ══════════════════════════════════════════════════════════════
def sonuc_kontrol(gecmis, guncel_fiyatlar, max_gun=30):
    """
    Açık kayıtları kontrol et:
    - Fiyat hedefe ulaştıysa → HEDEF
    - Fiyat stopa düştüyse → STOP
    - max_gun geçtiyse → SURE_DOLDU (fiyat ne olursa olsun)
    Dönen: yeni kapatılan kayıt sayısı
    """
    bugun = datetime.date.today()
    kapatilan = 0

    for k in gecmis:
        if k["sonuc"] is not None:
            continue  # zaten kapanmış

        fiyat = guncel_fiyatlar.get(k["kod"])
        giris = datetime.date.fromisoformat(k["giris_tarih"])
        gun = (bugun - giris).days

        if fiyat is None:
            continue

        k["gun_sayisi"] = gun
        k["kontrol_tarih"] = bugun.isoformat()

        if fiyat >= k["hedef"]:
            k["sonuc"] = "HEDEF"
            k["cikis_fiyat"] = fiyat
        elif fiyat <= k["stop"]:
            k["sonuc"] = "STOP"
            k["cikis_fiyat"] = fiyat
        elif gun >= max_gun:
            k["sonuc"] = "SURE_DOLDU"
            k["cikis_fiyat"] = fiyat
        else:
            continue  # hâlâ açık

        k["getiri_pct"] = ((k["cikis_fiyat"] - k["giris_fiyat"]) / k["giris_fiyat"]) * 100
        kapatilan += 1

    return kapatilan


# ══════════════════════════════════════════════════════════════
# BAŞARI ORANLARI (Güven Motoru'na geri besleme)
# ══════════════════════════════════════════════════════════════
def basari_orani(gecmis, sinyal_tip=None, min_ornek=5):
    """
    Kapatılmış kayıtlardan başarı oranı hesapla.
    sinyal_tip: None ise tümü, string ise o tipe özel
    min_ornek: yeterli örnek yoksa None döner (güvenilmez tahmin verme)

    Dönen: başarı yüzdesi (0-100) veya None
    """
    kapalilar = [k for k in gecmis if k["sonuc"] is not None]
    if sinyal_tip:
        kapalilar = [k for k in kapalilar if sinyal_tip in k["sinyal_tip"]]

    if len(kapalilar) < min_ornek:
        return None  # yeterli örnek yok, güvenilmez

    kazanan = [k for k in kapalilar if (k.get("getiri_pct") or 0) > 0]
    return len(kazanan) / len(kapalilar) * 100


def niyet_basari_orani(gecmis, niyet_sinif, min_ornek=5):
    """Niyet sınıfına göre başarı oranı."""
    kapalilar = [k for k in gecmis if k["sonuc"] is not None and k.get("niyet_sinif") == niyet_sinif]
    if len(kapalilar) < min_ornek:
        return None
    kazanan = [k for k in kapalilar if (k.get("getiri_pct") or 0) > 0]
    return len(kazanan) / len(kapalilar) * 100


# ══════════════════════════════════════════════════════════════
# PERFORMANS KARNESI (günlük/haftalık/tüm zamanlar)
# ══════════════════════════════════════════════════════════════
def performans_ozet(gecmis):
    """Tüm geçmişin özet istatistiği."""
    kapalilar = [k for k in gecmis if k["sonuc"] is not None and k.get("getiri_pct") is not None]
    if not kapalilar:
        return None

    getiriler = [k["getiri_pct"] for k in kapalilar]
    kazanan = [k for k in kapalilar if k["getiri_pct"] > 0]
    hedef_tutan = [k for k in kapalilar if k["sonuc"] == "HEDEF"]
    stop_yiyen = [k for k in kapalilar if k["sonuc"] == "STOP"]

    # Sinyal tipine göre kırılım
    tip_karne = {}
    for k in kapalilar:
        tip = k["sinyal_tip"]
        if tip not in tip_karne:
            tip_karne[tip] = {"adet": 0, "kazanan": 0, "ort_getiri": []}
        tip_karne[tip]["adet"] += 1
        if k["getiri_pct"] > 0:
            tip_karne[tip]["kazanan"] += 1
        tip_karne[tip]["ort_getiri"].append(k["getiri_pct"])

    for tip, v in tip_karne.items():
        v["basari_pct"] = v["kazanan"] / v["adet"] * 100
        import numpy as np
        v["ort_getiri"] = float(np.mean(v["ort_getiri"]))

    import numpy as np
    return {
        "toplam": len(kapalilar),
        "kazanan": len(kazanan),
        "basari_pct": len(kazanan) / len(kapalilar) * 100,
        "hedef_tutan": len(hedef_tutan),
        "stop_yiyen": len(stop_yiyen),
        "ort_getiri": float(np.mean(getiriler)),
        "en_iyi": float(max(getiriler)),
        "en_kotu": float(min(getiriler)),
        "beklemede": len([k for k in gecmis if k["sonuc"] is None]),
        "tip_karne": tip_karne,
    }


# ══════════════════════════════════════════════════════════════
# SUPABASE ENTEGRASYONU (opsiyonel — yoksa session_state yeter)
# ══════════════════════════════════════════════════════════════
def supabase_kaydet(url, key, gecmis):
    """Geçmişi Supabase'e kaydet."""
    if not url or not key:
        return False
    try:
        import requests
        headers = {"apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "application/json"}
        for k in gecmis:
            r = requests.post(f"{url}/rest/v1/sinyaller", json=k, headers=headers, timeout=8)
        return True
    except Exception:
        return False


def supabase_cek(url, key):
    """Supabase'den geçmişi çek."""
    if not url or not key:
        return []
    try:
        import requests
        headers = {"apikey": key, "Authorization": f"Bearer {key}"}
        r = requests.get(f"{url}/rest/v1/sinyaller?order=giris_tarih.desc&limit=500",
                         headers=headers, timeout=8)
        return r.json() if r.status_code == 200 else []
    except Exception:
        return []
