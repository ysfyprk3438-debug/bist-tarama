"""
═══════════════════════════════════════════════════════════════
KALABALIK PSİKOLOJİSİ — BIST Para Avcısı v4 (Katman 5: Zirve)
═══════════════════════════════════════════════════════════════
Yol haritasının en tepesi. En baştaki vizyonun gerçeği:

  Piyasa, insan psikolojisinin toplamıdır — korku, açgözlülük, sürü,
  panik, umut. "Yazılı olmayan kurallar" çoğunlukla kalabalığın
  TAHMİN EDİLEBİLİR İRRASYONELLİĞİDİR.

En derin contrarian gerçek: KALABALIK AŞIRILIKTA HEP YANILIR.
  • Herkes öforikken → tepe yakın (dağıtım zamanı)
  • Herkes panikteyken → dip yakın (toplama fırsatı)
  "Başkaları açgözlüyken korkma, korkarken açgözlü ol." — Buffett

Bu motor piyasanın DUYGU DURUMUNU okur:
  KORKU/AÇGÖZLÜLÜK ENDEKSİ (0-100): breadth + momentum + volatilite +
  yeni zirve/dip dengesinden hesaplanır.

  0-20  → AŞIRI KORKU (contrarian ALIM bölgesi)
  20-40 → KORKU
  40-60 → NÖTR/DENGE
  60-80 → AÇGÖZLÜLÜK
  80-100→ AŞIRI AÇGÖZLÜLÜK (tepe riski, temkinli ol)
"""


def _clamp(x, a, b):
    return max(a, min(b, x))


def korku_acgozluluk(genislik, endeks_vol_rejim=None, xu100_pct=0.0):
    """
    Piyasanın duygu durumunu 0-100 arası ölçer.
    0 = aşırı korku, 100 = aşırı açgözlülük.
    Dönen: {skor, bolge, renk, ikon, yorum, contrarian, bilesenler}
    """
    if not genislik:
        return None

    skor = 50.0  # nötr başlangıç
    bilesenler = []

    # ── 1. KATILIM (breadth) — yüksek = açgözlülük ──
    ma200 = genislik.get("ma200_oran", 50)
    katki = (ma200 - 50) * 0.40  # ±20
    skor += katki
    bilesenler.append(("Katılım", f"%{ma200:.0f} hisse MA200 üstü", katki))

    # ── 2. MOMENTUM — endeks yükselişi = açgözlülük ──
    mom_katki = _clamp(xu100_pct * 1.5, -15, 15)
    skor += mom_katki
    bilesenler.append(("Momentum", f"Endeks %{xu100_pct:+.1f}", mom_katki))

    # ── 3. VOLATİLİTE — fırtına = korku, sakin = rahatlık/açgözlülük ──
    if endeks_vol_rejim == "FIRTINA":
        vol_katki = -12
        vol_aciklama = "Fırtına (korku)"
    elif endeks_vol_rejim == "SAKİN":
        vol_katki = 8
        vol_aciklama = "Sakin (rahatlık)"
    else:
        vol_katki = 0
        vol_aciklama = "Normal"
    skor += vol_katki
    bilesenler.append(("Volatilite", vol_aciklama, vol_katki))

    # ── 4. YENİ ZİRVE/DİP DENGESİ — zirveler = açgözlülük ──
    zirve = genislik.get("yeni_zirve", 0)
    dip = genislik.get("yeni_dip", 0)
    if zirve + dip > 0:
        zd_katki = (zirve - dip) / (zirve + dip) * 12
        skor += zd_katki
        bilesenler.append(("Zirve/Dip", f"{zirve} zirve, {dip} dip", zd_katki))

    skor = _clamp(skor, 0, 100)

    # ── BÖLGE + CONTRARIAN YORUM ──
    if skor <= 20:
        bolge, renk, ikon = "AŞIRI KORKU", "#10B981", "😱"
        yorum = "Kalabalık panikte — tarihsel olarak dip bölgeleri böyle hissettirir."
        contrarian = "✓ CONTRARIAN FIRSAT: Herkes korkarken cesur ol. Kaliteli hisselerde toplama zamanı olabilir."
    elif skor <= 40:
        bolge, renk, ikon = "KORKU", "#34D399", "😟"
        yorum = "Piyasada tedirginlik var — temkinli iyimserlik bölgesi."
        contrarian = "Korku hakim — seçici alım için fırsatlar oluşabilir, ama acele etme."
    elif skor <= 60:
        bolge, renk, ikon = "DENGE", "#94A3B8", "😐"
        yorum = "Duygular dengeli — ne aşırı korku ne aşırı açgözlülük."
        contrarian = "Nötr bölge — sinyallere normal güven, contrarian baskı yok."
    elif skor <= 80:
        bolge, renk, ikon = "AÇGÖZLÜLÜK", "#F59E0B", "😏"
        yorum = "Piyasada iyimserlik/açgözlülük artıyor — geç aşama olabilir."
        contrarian = "Açgözlülük yükseliyor — kâr realizasyonunu düşün, yeni alımlarda seçici ol."
    else:
        bolge, renk, ikon = "AŞIRI AÇGÖZLÜLÜK", "#EF4444", "🤑"
        yorum = "Kalabalık öforide — tarihsel olarak tepe bölgeleri böyle hissettirir."
        contrarian = "⚠ TEPE RİSKİ: Herkes açgözlüyken kork. Yeni alımlar riskli, kâr korumayı düşün."

    return {
        "skor": int(round(skor)),
        "bolge": bolge, "renk": renk, "ikon": ikon,
        "yorum": yorum, "contrarian": contrarian,
        "bilesenler": bilesenler,
    }


def psikoloji_karar_etkisi(psikoloji, hisse_strateji=None):
    """
    Kalabalık psikolojisinin karara contrarian etkisi.
    Aşırı açgözlülükte momentum alımları riskli (geç aşama),
    aşırı korkuda dip fırsatları değerli.
    Dönen: {etki, not} — etki av skoruna eklenir (-6..+6)
    """
    if not psikoloji:
        return {"etki": 0, "not": ""}

    skor = psikoloji["skor"]

    # Aşırı açgözlülük: yeni alımlar (özellikle momentum) cezalandırılır
    if skor > 80:
        if hisse_strateji == "MOMENTUM":
            return {"etki": -6, "not": "Aşırı açgözlülükte momentum alımı = geç aşama riski"}
        return {"etki": -3, "not": "Aşırı açgözlülük — tepe riski, temkinli"}
    # Aşırı korku: dip/reversion fırsatları ödüllendirilir (contrarian)
    elif skor < 20:
        if hisse_strateji == "REVERSION":
            return {"etki": 6, "not": "Aşırı korkuda dip toplama = contrarian fırsat"}
        return {"etki": 3, "not": "Aşırı korku — kaliteli hisselerde fırsat oluşabilir"}
    # Açgözlülük: hafif temkin
    elif skor > 65:
        return {"etki": -2, "not": "Açgözlülük bölgesi — hafif temkin"}
    # Korku: hafif fırsat
    elif skor < 35:
        return {"etki": 2, "not": "Korku bölgesi — seçici fırsat"}

    return {"etki": 0, "not": ""}
