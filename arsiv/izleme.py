"""
═══════════════════════════════════════════════════════════════
İZLEME + ALARM + "KEŞKE ALSAYDIN" — BIST Tarama v4
═══════════════════════════════════════════════════════════════
- İzleme listesi (watchlist): beğenilen hisseleri takip et
- Fiyat alarmı: "X fiyatı geçerse haber ver"
- Keşke analizi: "2 saat/gün önce alsaydın şu kadar kazanırdın"
"""

import datetime


# ══════════════════════════════════════════════════════════════
# FİYAT ALARMI
# ══════════════════════════════════════════════════════════════
def alarm_kontrol(alarmlar, guncel_fiyatlar):
    """
    Alarmları kontrol et, tetiklenenleri döndür.
    alarmlar: [{kod, yon, hedef_fiyat, tetiklendi, not}]
      yon: "ustu" (fiyat hedefin üstüne çıkarsa) veya "alti"
    Dönen: tetiklenen alarmların listesi
    """
    tetiklenen = []
    for a in alarmlar:
        if a.get("tetiklendi"):
            continue
        fiyat = guncel_fiyatlar.get(a["kod"])
        if fiyat is None:
            continue
        if a["yon"] == "ustu" and fiyat >= a["hedef_fiyat"]:
            a["tetiklendi"] = True
            a["tetik_fiyat"] = fiyat
            a["tetik_tarih"] = datetime.datetime.now().isoformat()
            tetiklenen.append(a)
        elif a["yon"] == "alti" and fiyat <= a["hedef_fiyat"]:
            a["tetiklendi"] = True
            a["tetik_fiyat"] = fiyat
            a["tetik_tarih"] = datetime.datetime.now().isoformat()
            tetiklenen.append(a)
    return tetiklenen


def alarm_ekle(alarmlar, kod, hedef_fiyat, yon, mevcut_fiyat=None):
    """Yeni alarm ekle. yon otomatik belirlenebilir."""
    if yon is None and mevcut_fiyat is not None:
        yon = "ustu" if hedef_fiyat > mevcut_fiyat else "alti"
    alarmlar.append({
        "kod": kod, "hedef_fiyat": hedef_fiyat, "yon": yon,
        "tetiklendi": False, "olusturma": datetime.datetime.now().isoformat(),
    })
    return f"{kod} için alarm: fiyat {hedef_fiyat:.2f}₺ {'üstüne çıkınca' if yon=='ustu' else 'altına inince'}"


# ══════════════════════════════════════════════════════════════
# "KEŞKE ALSAYDIN" ANALİZİ
# Bir sinyalin verildiği andan şimdiye kadar ne kazandırdığı
# ══════════════════════════════════════════════════════════════
def keske_analiz(giris_fiyat, guncel_fiyat, lot_ornegi=100):
    """
    "X önce alsaydın şu kadar kazanırdın" hesabı.
    Dönen: kazanç sözlüğü
    """
    degisim_pct = ((guncel_fiyat - giris_fiyat) / giris_fiyat) * 100
    ornek_maliyet = giris_fiyat * lot_ornegi
    ornek_kar = (guncel_fiyat - giris_fiyat) * lot_ornegi
    return {
        "degisim_pct": degisim_pct,
        "ornek_lot": lot_ornegi,
        "ornek_maliyet": ornek_maliyet,
        "ornek_kar": ornek_kar,
        "yon": "kazanç" if degisim_pct >= 0 else "kayıp",
    }


def keske_metni(kod, giris_fiyat, guncel_fiyat, ne_zaman="bugün"):
    """İnsan dilinde 'keşke' mesajı üretir."""
    k = keske_analiz(giris_fiyat, guncel_fiyat)
    if k["degisim_pct"] >= 0:
        return (f"{kod}: {ne_zaman} {giris_fiyat:.2f}₺'den alsaydın, "
                f"şimdi %{k['degisim_pct']:.1f} kârdaydın "
                f"({k['ornek_lot']} lot = {k['ornek_kar']:+,.0f}₺)")
    else:
        return (f"{kod}: {ne_zaman} {giris_fiyat:.2f}₺'den alsaydın, "
                f"şimdi %{abs(k['degisim_pct']):.1f} zarardaydın "
                f"({k['ornek_lot']} lot = {k['ornek_kar']:+,.0f}₺) — iyi ki almadın")


# ══════════════════════════════════════════════════════════════
# HEDEF İLERLEME (gün içi/günlük/haftalık/aylık kazanç hedefleri)
# Senin fikrin: program kendine hedef koyar, kalan % gösterir
# ══════════════════════════════════════════════════════════════
def hedef_ilerleme(gerceklesen_kar, hedef_kar):
    """
    Bir dönem kazanç hedefine ne kadar ulaşıldığı.
    Dönen: (yüzde, renk, durum_metni)
    """
    if hedef_kar <= 0:
        return 0, "#94A3B8", "Hedef tanımlı değil"
    yuzde = (gerceklesen_kar / hedef_kar) * 100
    yuzde_kirpik = max(0, min(100, yuzde))
    if yuzde >= 100:
        renk, durum = "#10B981", "Hedef tamamlandı! 🎯"
    elif yuzde >= 60:
        renk, durum = "#34D399", f"Hedefe %{100-yuzde:.0f} kaldı"
    elif yuzde >= 0:
        renk, durum = "#F59E0B", f"Hedefe %{100-yuzde:.0f} kaldı"
    else:
        renk, durum = "#EF4444", "Hedefin gerisinde (zararda)"
    return yuzde_kirpik, renk, durum
