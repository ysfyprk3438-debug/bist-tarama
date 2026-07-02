"""
═══════════════════════════════════════════════════════════════
SANAL CÜZDAN (PAPER TRADING) — BIST Tarama v4
═══════════════════════════════════════════════════════════════
Gerçek parasız alım-satım. Stratejini test etmenin tek güvenli yolu.
Robotlaştırmadan önce burada kusursuz çalıştığını görmelisin.

Tasarım:
- Komisyon gerçekçi (varsayılan %0.2, ayarlanabilir)
- Her işlem kaydedilir (al/sat, fiyat, komisyon, kar/zarar)
- Açık pozisyonların anlık değeri + hedef ilerlemesi
- Kapanan işlemlerin kar/zarar geçmişi
"""

import datetime


def cuzdan_olustur(baslangic_bakiye):
    """Yeni sanal cüzdan. Session state'e konur."""
    return {
        "baslangic": float(baslangic_bakiye),
        "nakit": float(baslangic_bakiye),
        "pozisyonlar": {},   # {kod: {lot, ort_maliyet, hedef, stop, acilis_tarih}}
        "islemler": [],      # tüm işlem geçmişi
        "komisyon_oran": 0.002,  # %0.2
    }


def alis_yap(cuzdan, kod, fiyat, lot, hedef=None, stop=None):
    """
    Sanal alım. Komisyon nakitten düşer.
    Dönen: (başarılı_mı, mesaj)
    """
    if lot <= 0:
        return False, "Lot 0'dan büyük olmalı"
    tutar = fiyat * lot
    komisyon = tutar * cuzdan["komisyon_oran"]
    toplam_maliyet = tutar + komisyon
    if toplam_maliyet > cuzdan["nakit"]:
        return False, f"Yetersiz bakiye. Gerekli: {toplam_maliyet:,.0f}₺, mevcut: {cuzdan['nakit']:,.0f}₺"

    cuzdan["nakit"] -= toplam_maliyet

    # Pozisyon ekle / ortalama maliyet güncelle
    if kod in cuzdan["pozisyonlar"]:
        poz = cuzdan["pozisyonlar"][kod]
        eski_tutar = poz["ort_maliyet"] * poz["lot"]
        yeni_lot = poz["lot"] + lot
        poz["ort_maliyet"] = (eski_tutar + tutar) / yeni_lot
        poz["lot"] = yeni_lot
        if hedef: poz["hedef"] = hedef
        if stop: poz["stop"] = stop
    else:
        cuzdan["pozisyonlar"][kod] = {
            "lot": lot, "ort_maliyet": fiyat,
            "hedef": hedef, "stop": stop,
            "acilis_tarih": datetime.datetime.now().isoformat(),
        }

    cuzdan["islemler"].append({
        "tip": "ALIŞ", "kod": kod, "fiyat": fiyat, "lot": lot,
        "tutar": tutar, "komisyon": komisyon,
        "tarih": datetime.datetime.now().isoformat(), "kar_zarar": None,
    })
    return True, f"{kod}: {lot:,} lot @ {fiyat:.2f}₺ alındı (komisyon {komisyon:,.0f}₺)"


def satis_yap(cuzdan, kod, fiyat, lot=None):
    """
    Sanal satış. lot=None ise tümünü sat.
    Kar/zarar hesaplanıp kaydedilir.
    Dönen: (başarılı_mı, mesaj)
    """
    if kod not in cuzdan["pozisyonlar"]:
        return False, f"{kod} pozisyonu yok"
    poz = cuzdan["pozisyonlar"][kod]
    if lot is None:
        lot = poz["lot"]
    if lot > poz["lot"]:
        return False, f"Elde {poz['lot']:,} lot var, {lot:,} satılamaz"

    tutar = fiyat * lot
    komisyon = tutar * cuzdan["komisyon_oran"]
    net_gelir = tutar - komisyon
    maliyet = poz["ort_maliyet"] * lot
    # Alış komisyonu da kar/zarara dahil (gerçekçi)
    alis_komisyon = maliyet * cuzdan["komisyon_oran"]
    kar_zarar = net_gelir - maliyet - alis_komisyon
    kar_zarar_pct = (kar_zarar / (maliyet + alis_komisyon)) * 100

    cuzdan["nakit"] += net_gelir

    poz["lot"] -= lot
    if poz["lot"] <= 0:
        del cuzdan["pozisyonlar"][kod]

    cuzdan["islemler"].append({
        "tip": "SATIŞ", "kod": kod, "fiyat": fiyat, "lot": lot,
        "tutar": tutar, "komisyon": komisyon,
        "tarih": datetime.datetime.now().isoformat(),
        "kar_zarar": kar_zarar, "kar_zarar_pct": kar_zarar_pct,
    })
    durum = "kâr" if kar_zarar >= 0 else "zarar"
    return True, f"{kod}: {lot:,} lot @ {fiyat:.2f}₺ satıldı | {kar_zarar:+,.0f}₺ {durum} (%{kar_zarar_pct:+.1f})"


def portfoy_degeri(cuzdan, guncel_fiyatlar):
    """
    Cüzdanın anlık toplam değeri.
    guncel_fiyatlar: {kod: fiyat}
    Dönen: özet sözlük
    """
    pozisyon_degeri = 0.0
    pozisyon_detay = []
    for kod, poz in cuzdan["pozisyonlar"].items():
        fiyat = guncel_fiyatlar.get(kod, poz["ort_maliyet"])
        deger = fiyat * poz["lot"]
        maliyet = poz["ort_maliyet"] * poz["lot"]
        kar = deger - maliyet
        kar_pct = (kar / maliyet) * 100 if maliyet > 0 else 0
        pozisyon_degeri += deger

        # Hedef ilerlemesi (girişten hedefe ne kadar yol alındı)
        hedef_ilerleme = None
        if poz.get("hedef") and poz["hedef"] > poz["ort_maliyet"]:
            yol = fiyat - poz["ort_maliyet"]
            toplam = poz["hedef"] - poz["ort_maliyet"]
            hedef_ilerleme = max(0, min(100, (yol / toplam) * 100))

        pozisyon_detay.append({
            "kod": kod, "lot": poz["lot"], "ort_maliyet": poz["ort_maliyet"],
            "guncel": fiyat, "deger": deger, "kar": kar, "kar_pct": kar_pct,
            "hedef": poz.get("hedef"), "stop": poz.get("stop"),
            "hedef_ilerleme": hedef_ilerleme,
        })

    toplam = cuzdan["nakit"] + pozisyon_degeri
    toplam_kar = toplam - cuzdan["baslangic"]
    toplam_kar_pct = (toplam_kar / cuzdan["baslangic"]) * 100 if cuzdan["baslangic"] > 0 else 0

    return {
        "nakit": cuzdan["nakit"],
        "pozisyon_degeri": pozisyon_degeri,
        "toplam": toplam,
        "toplam_kar": toplam_kar,
        "toplam_kar_pct": toplam_kar_pct,
        "pozisyonlar": pozisyon_detay,
    }


def gunluk_karne(cuzdan):
    """Bugün yapılan işlemlerin özeti (performans karnesi)."""
    bugun = datetime.date.today().isoformat()
    bugun_islemler = [i for i in cuzdan["islemler"] if i["tarih"].startswith(bugun)]
    satislar = [i for i in bugun_islemler if i["tip"] == "SATIŞ"]
    realize_kar = sum(i.get("kar_zarar", 0) or 0 for i in satislar)
    kazanan = len([i for i in satislar if (i.get("kar_zarar", 0) or 0) > 0])
    return {
        "islem_sayisi": len(bugun_islemler),
        "satis_sayisi": len(satislar),
        "realize_kar": realize_kar,
        "kazanan": kazanan,
        "kaybeden": len(satislar) - kazanan,
        "basari_pct": (kazanan / len(satislar) * 100) if satislar else 0,
    }
