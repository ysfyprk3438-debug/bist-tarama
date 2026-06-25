"""
═══════════════════════════════════════════════════════════════
KARAR SENTEZLEYİCİ — BIST Para Avcısı v4 (Emergent Katman)
═══════════════════════════════════════════════════════════════
Baş analist. Bütün bölüm raporlarını (teknik, güven, niyet, rüzgar,
alarm) dinler, sana TEK net karar verir.

NEDEN: Çok sinyal = karmaşa. Kullanıcı 5 göstergeyi kafasında
birleştirmek zorunda kalmasın. Sistem birleştirsin, tek şey desin.

Çıktı: AV SKORU (0-100) + KARAR (4 kademe) + tek cümle gerekçe.
Detaylar yine açılır bölümde durur — ama üstte net karar olur.

Bu hem EMERGENT (her şeyi birleştirir) hem SADELEŞTİRİCİ (5→1).
"""


def av_skoru(r):
    """
    Tüm sinyalleri tek bir av skoru + karara sentezler.
    r: analiz_et sonucu (puan, guven, niyet, ruzgar, alarm içerir)
    Dönen: {skor, karar, renk, ikon, gerekce, aciliyet}
    """
    puan = r.get("puan", 0)
    guven = r.get("guven", {})
    niyet = r.get("niyet", {})
    ruzgar = r.get("ruzgar", {})
    alarm = r.get("alarm", {})
    zaman = r.get("zaman_onay", {})

    guven_yuzde = guven.get("yuzde", 50)
    ruzgar_skor = ruzgar.get("skor", 0)  # -3..+3
    zaman_skor = zaman.get("skor", 0) if zaman else 0  # -2..+2 (üst zaman dilimi)

    # ── TEMEL AV SKORU ──
    # Güven zaten teknik+akıllı para+niyet+rüzgarı içeriyor; onu çekirdek al
    skor = guven_yuzde

    # Aciliyet: yaklaşan pozitif olay skoru yükseltir, negatif düşürür
    aciliyet = 0
    if alarm.get("var"):
        yon = alarm.get("yon")
        yakinlik = alarm.get("yakinlik", 0)
        if yon == "pozitif":          # yaklaşan altın kesişim / kırılım
            skor = min(100, skor + yakinlik * 0.12)
            aciliyet = yakinlik
        elif yon == "firsat":         # dip bölgesi
            skor = min(100, skor + yakinlik * 0.08)
            aciliyet = yakinlik * 0.7
        elif yon == "negatif":        # yaklaşan ölüm kesişimi
            skor = max(0, skor - yakinlik * 0.20)
            aciliyet = -yakinlik
        elif yon == "dikkat":         # zirve bölgesi
            skor = max(0, skor - yakinlik * 0.12)
            aciliyet = -yakinlik * 0.7

    skor = int(max(0, min(100, skor)))

    # Üst zaman dilimi etkisi: çelişki skoru düşürür, güçlü onay yükseltir
    if zaman_skor <= -2:
        skor = int(max(0, skor - 12))   # üst zaman dilimi ters → ciddi uyarı
    elif zaman_skor == -1:
        skor = int(max(0, skor - 5))
    elif zaman_skor >= 2:
        skor = int(min(100, skor + 6))  # üst zaman dilimi güçlü onay

    # ── KARAR (4 kademe) ──
    # Üst zaman dilimi ÇELİŞKİSİ ciddi manipülasyon gibi değerlendirilir
    ust_celiski = zaman_skor <= -2

    # Ciddi manipülasyon desenleri (dağıtım/sürü/olağandışı) skordan BAĞIMSIZ uzak dur
    ciddi_manipulasyon = niyet.get("sinif") in ("DAĞITIM", "SÜRÜ / ZİRVE", "OLAĞANDIŞI HAREKET")

    # Diğer negatif uyarılar (skor düşükse uzak dur)
    negatif_uyari = (
        (alarm.get("var") and alarm.get("yon") in ("negatif", "dikkat") and alarm.get("yakinlik", 0) >= 75)
        or ruzgar_skor <= -2
        or ust_celiski
    )

    if ciddi_manipulasyon:
        karar, renk, ikon = "UZAK DUR", "#EF4444", "🔴"
        gerekce = _gerekce_uzak(r)
    elif negatif_uyari and skor < 65:
        karar, renk, ikon = "UZAK DUR", "#EF4444", "🔴"
        gerekce = _gerekce_uzak(r)
    elif skor >= 75 and aciliyet >= 60:
        karar, renk, ikon = "ŞİMDİ AL", "#10B981", "🟢"
        gerekce = _gerekce_simdi(r)
    elif skor >= 70:
        karar, renk, ikon = "AL / İZLE", "#34D399", "🟢"
        gerekce = _gerekce_al(r)
    elif skor >= 55:
        karar, renk, ikon = "İZLE", "#38BDF8", "🔵"
        gerekce = _gerekce_izle(r)
    elif skor >= 40:
        karar, renk, ikon = "BEKLE", "#F59E0B", "🟡"
        gerekce = "Karışık sinyaller — net bir avantaj yok, beklemek daha güvenli."
    else:
        karar, renk, ikon = "UZAK DUR", "#EF4444", "🔴"
        gerekce = _gerekce_uzak(r)

    return {
        "skor": skor, "karar": karar, "renk": renk, "ikon": ikon,
        "gerekce": gerekce, "aciliyet": int(aciliyet),
    }


# ── Gerekçe üreticileri (tek cümle, en güçlü argümanı seçer) ──
def _gerekce_simdi(r):
    alarm = r.get("alarm", {})
    if alarm.get("var") and alarm.get("gun") is not None:
        return f"{alarm['etiket'].lower()} (~{alarm['gun']} gün) + güçlü teknik + uygun rüzgar — fırsat penceresi açık."
    return "Yüksek güven + yaklaşan pozitif olay + uygun rüzgar — şartlar hizalandı."


def _gerekce_al(r):
    ruzgar = r.get("ruzgar", {})
    niyet = r.get("niyet", {})
    parcalar = []
    if r.get("puan", 0) >= 70: parcalar.append("teknik güçlü")
    if niyet.get("sinif") == "SESSİZ TOPLAMA": parcalar.append("sessiz toplama var")
    if ruzgar.get("skor", 0) >= 2: parcalar.append("rüzgar arkada")
    return (", ".join(parcalar) if parcalar else "şartlar olumlu") + " — alım için uygun zemin."


def _gerekce_izle(r):
    return "Olumlu ama henüz tetik yok — yakın takibe al, alarm beklenebilir."


def _gerekce_uzak(r):
    niyet = r.get("niyet", {})
    ruzgar = r.get("ruzgar", {})
    alarm = r.get("alarm", {})
    if niyet.get("sinif") == "DAĞITIM":
        return "Dağıtım deseni — yukarıdan satış var, tuzak olabilir. Uzak dur."
    if niyet.get("sinif") in ("SÜRÜ / ZİRVE", "OLAĞANDIŞI HAREKET"):
        return "Aşırı/olağandışı hareket — geç kalınmış, riskli. Uzak dur."
    if alarm.get("var") and alarm.get("yon") == "negatif":
        return f"Ölüm kesişimi yaklaşıyor (~{alarm.get('gun','?')} gün) — düşüş riski. Uzak dur."
    if ruzgar.get("skor", 0) <= -2:
        return "Karşı rüzgar — borsa/sektör/hisse aleyhte. Akıntıya karşı kürek."
    return "Zayıf skor + olumsuz sinyaller — şartlar uygun değil."
