"""
═══════════════════════════════════════════════════════════════
FIRSAT RADARI — BIST Para Avcısı v4
═══════════════════════════════════════════════════════════════
23 modül müthiş analiz üretiyor — ama av sırasında "şu an nereye
bakayım?" sorusunun TEK ekranda cevabı lazım.

Radar, tüm taramadan SADECE aksiyon gerektirenleri süzer ve
aciliyet sırasına dizer:
  • ŞİMDİ → ŞİMDİ AL kararı veya kritik pozitif alarm (titreşen)
  • YAKLAŞAN → yaklaşan pozitif olay (altın kesişim/kırılım/dip)
  • İZLE → AL/İZLE kararı, tetik bekliyor

Bu, avcının nişan ekranı. Gürültüyü eler, sadece önemliyi gösterir.
Yeni analiz değil — mevcut her şeyi kullanılır kılan sentez.
"""


def firsat_radari(sonuclar):
    """
    Tarama sonuçlarından aksiyon gerektirenleri kategorize eder + sıralar.
    Dönen: {simdi, yaklasan, izle, toplam_firsat}
    """
    if not sonuclar:
        return {"simdi": [], "yaklasan": [], "izle": [], "toplam_firsat": 0}

    simdi, yaklasan, izle = [], [], []

    for r in sonuclar:
        karar = r.get("karar", {})
        alarm = r.get("alarm", {})
        k_metin = karar.get("karar", "")

        # Aciliyet skoru: av skoru + pozitif alarm yakınlığı
        aciliyet = karar.get("skor", 0)
        pozitif_alarm = alarm.get("var") and alarm.get("yon") in ("pozitif", "firsat")
        if pozitif_alarm:
            aciliyet += alarm.get("yakinlik", 0) * 0.35

        # Kategorize et
        if k_metin == "ŞİMDİ AL" or (pozitif_alarm and alarm.get("titresim")):
            simdi.append((aciliyet, r))
        elif pozitif_alarm:
            yaklasan.append((aciliyet, r))
        elif k_metin in ("AL / İZLE", "İZLE"):
            izle.append((aciliyet, r))

    # Her kategoriyi aciliyete göre sırala
    simdi.sort(key=lambda x: x[0], reverse=True)
    yaklasan.sort(key=lambda x: x[0], reverse=True)
    izle.sort(key=lambda x: x[0], reverse=True)

    return {
        "simdi": [r for _, r in simdi],
        "yaklasan": [r for _, r in yaklasan],
        "izle": [r for _, r in izle][:8],  # izle listesi uzayabilir, sınırla
        "toplam_firsat": len(simdi) + len(yaklasan),
    }


def radar_satir_bilgi(r):
    """Bir hisse için radar satırında gösterilecek özet bilgi."""
    karar = r.get("karar", {})
    alarm = r.get("alarm", {})
    olay = ""
    if alarm.get("var"):
        gun = f" ~{alarm['gun']}g" if alarm.get("gun") is not None else ""
        olay = f"{alarm['etiket']}{gun}"
    elif r.get("teknik_olay"):
        olay = r["teknik_olay"][0]["etiket"]
    return {
        "kod": r["kod"],
        "karar": karar.get("karar", ""),
        "karar_renk": karar.get("renk", "#94A3B8"),
        "ikon": karar.get("ikon", ""),
        "av_skoru": karar.get("skor", 0),
        "son": r.get("son", 0),
        "olay": olay,
        "olay_renk": alarm.get("renk", "#94A3B8") if alarm.get("var") else "#64748B",
        "sektor": r.get("sektor", ""),
        "kazanc_pct": r.get("kazanc_pct", 0),
    }
