"""
═══════════════════════════════════════════════════════════════
KENDİNİ KALİBRE ETME — BIST Para Avcısı v4 (Katman 1: Olgunlaşma)
═══════════════════════════════════════════════════════════════
En baştaki vizyonun gerçeği: "kendini geliştiren sistem".

Sistem gerçek sicilinden ÖĞRENİR. Hangi sinyal tipleri, hangi
koşullarda gerçekten kazandırdı? Geçmişte tutmayan kombinasyonların
güvenini kısar, tutanları ödüllendirir.

DÜRÜSTLÜK İLKESİ: Az veriyle öğrenmek tehlikelidir (aşırı uyum).
Bu yüzden sistem yeterli örnek yoksa "henüz öğrenemedim" der ve
hiçbir ayarlama yapmaz. Güven, uydurulmuş değil KANITLANMIŞ olmalı.

Bu motor canlı veride sinyal geçmişi biriktikçe DEVREYE GİRER.
Başta dormanttır — çünkü öğrenecek gerçek deneyim henüz yoktur.
Bu, sistemin en dürüst yanı: bilmediğini bilir.
"""

import numpy as np


# Anlamlı kalibrasyon için gereken minimum örnek sayısı
MIN_ORNEK = 10


def kalibrasyon_durumu(gecmis):
    """
    Sistem öğrenmeye hazır mı? Ne kadar deneyim birikti?
    Dönen: {hazir, kapali_sinyal, mesaj, olgunluk_yuzde}
    """
    kapalilar = [k for k in gecmis if k.get("sonuc") in ("HEDEF", "STOP", "SURE_DOLDU")]
    n = len(kapalilar)

    if n == 0:
        return {"hazir": False, "kapali_sinyal": 0, "olgunluk_yuzde": 0,
                "mesaj": "Henüz kapanmış sinyal yok — sistem deneyim biriktirmeye başlamadı. Canlı kullanımla öğrenecek."}
    elif n < MIN_ORNEK:
        return {"hazir": False, "kapali_sinyal": n, "olgunluk_yuzde": int(n / MIN_ORNEK * 100),
                "mesaj": f"{n}/{MIN_ORNEK} kapanmış sinyal — öğrenmek için yeterli değil. Az veriyle ayar yapmak tehlikeli (aşırı uyum), bekliyorum."}
    else:
        return {"hazir": True, "kapali_sinyal": n, "olgunluk_yuzde": min(100, int(n / 30 * 100)),
                "mesaj": f"{n} kapanmış sinyalden öğrenildi — kalibrasyon aktif. Sistem kendi sicilinden ders çıkarıyor."}


def sinyal_tipi_kalibrasyonu(gecmis, min_ornek=MIN_ORNEK):
    """
    Her sinyal tipinin gerçek başarısını ölçer.
    Dönen: {sinyal_tip: {basari, ornek, ayar}} — yeterli veri olanlar
    ayar: gelecekteki skora eklenecek düzeltme (-10..+10)
    """
    kapalilar = [k for k in gecmis if k.get("sonuc") in ("HEDEF", "STOP", "SURE_DOLDU")]
    if len(kapalilar) < min_ornek:
        return {}

    tipler = {}
    for k in kapalilar:
        t = k.get("sinyal_tip", "?")
        tipler.setdefault(t, []).append(k)

    sonuc = {}
    for t, kayitlar in tipler.items():
        if len(kayitlar) < max(3, min_ornek // 3):
            continue  # bu tip için yeterli örnek yok
        hedef = sum(1 for k in kayitlar if k["sonuc"] == "HEDEF")
        basari = hedef / len(kayitlar) * 100
        # Başarı %50'den ne kadar saparsa o kadar ayar (kademeli)
        ayar = int(np.clip((basari - 50) * 0.2, -10, 10))
        sonuc[t] = {"basari": round(basari, 0), "ornek": len(kayitlar), "ayar": ayar}

    return sonuc


def kalibrasyon_ayari(gecmis, sinyal_tip):
    """
    Verilen sinyal tipi için skor düzeltmesi döner (gerçek sicile dayalı).
    Yeterli veri yoksa 0 (ayar yok — dürüst davranış).
    Dönen: {ayar, gerekce} — ayar av skoruna eklenir
    """
    durum = kalibrasyon_durumu(gecmis)
    if not durum["hazir"]:
        return {"ayar": 0, "gerekce": None}

    kalib = sinyal_tipi_kalibrasyonu(gecmis)
    if sinyal_tip not in kalib:
        return {"ayar": 0, "gerekce": None}

    k = kalib[sinyal_tip]
    if k["ayar"] > 0:
        gerekce = f"Bu sinyal tipi geçmişte iyi çalıştı (%{k['basari']:.0f}, {k['ornek']} örnek) → güven artırıldı"
    elif k["ayar"] < 0:
        gerekce = f"Bu sinyal tipi geçmişte zayıf çalıştı (%{k['basari']:.0f}, {k['ornek']} örnek) → güven kısıldı"
    else:
        gerekce = None

    return {"ayar": k["ayar"], "gerekce": gerekce}
