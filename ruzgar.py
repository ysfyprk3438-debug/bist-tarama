"""
═══════════════════════════════════════════════════════════════
RÜZGAR YÖNÜ — BIST Para Avcısı v4 (Bağlam Katmanı)
═══════════════════════════════════════════════════════════════
Borsanın en eski yazılı kuralı: "Trend dostundur, ona karşı durma."

Bir sinyalin BÜYÜK RESİMLE uyumlu olup olmadığını ölçer.
Üç rüzgarı birleştirir:

  1. MAKRO RÜZGAR  → XU100 (borsa geneli) yükselişte mi?
  2. SEKTÖR RÜZGARI → hissenin sektörüne para giriyor mu?
  3. HİSSE TRENDİ   → fiyat kendi uzun ortalamasının üstünde mi?

Üçü de arkadan eserse: KUYRUK RÜZGARI (güven artar).
Üçü de karşıdan eserse: KARŞI RÜZGAR (uyarı, güven düşer).

Hepsi ELDEKİ VERİYLE hesaplanır — ekstra veri çekmez.
"""


def ruzgar_hesapla(r, rejim, rotasyon=None):
    """
    Bir analiz sonucu için rüzgar yönünü hesaplar.
    r: analiz_et sonucu (trend, sektor, sm içerir)
    rejim: piyasa rejimi metni ("YÜKSELİŞ TRENDİ" vs)
    rotasyon: piyasa.sektor_rotasyon çıktısı (None olabilir)

    Dönen: {skor, yon, seviye, renk, bilesenler, aciklama, uyari}
    """
    bilesenler = []
    skor = 0  # -3 ... +3

    # ── 1. MAKRO RÜZGAR (XU100 rejimi) ──
    if "YÜKSELİŞ" in rejim:
        skor += 1
        bilesenler.append(("Borsa", "arkadan", "#10B981"))
    elif "DÜŞÜŞ" in rejim:
        skor -= 1
        bilesenler.append(("Borsa", "karşıdan", "#EF4444"))
    else:
        bilesenler.append(("Borsa", "yatay", "#94A3B8"))

    # ── 2. SEKTÖR RÜZGARI (rotasyondan) ──
    sektor = r.get("sektor")
    sektor_yon = "nötr"
    if rotasyon and rotasyon.get("tum"):
        # Bu sektör para girenler arasında mı, çıkanlar arasında mı?
        giren_sektorler = {s["sektor"] for s in rotasyon.get("giren", [])}
        cikan_sektorler = {s["sektor"] for s in rotasyon.get("cikan", [])}
        if sektor in giren_sektorler:
            skor += 1
            sektor_yon = "arkadan"
            bilesenler.append(("Sektör", "arkadan", "#10B981"))
        elif sektor in cikan_sektorler:
            skor -= 1
            sektor_yon = "karşıdan"
            bilesenler.append(("Sektör", "karşıdan", "#EF4444"))
        else:
            bilesenler.append(("Sektör", "nötr", "#94A3B8"))
    else:
        bilesenler.append(("Sektör", "—", "#94A3B8"))

    # ── 3. HİSSE TRENDİ (analiz zaten hesapladı: 0-4) ──
    trend = r.get("trend", 0)
    if trend >= 3:
        skor += 1
        bilesenler.append(("Hisse trendi", "arkadan", "#10B981"))
    elif trend <= 1:
        skor -= 1
        bilesenler.append(("Hisse trendi", "karşıdan", "#EF4444"))
    else:
        bilesenler.append(("Hisse trendi", "yatay", "#94A3B8"))

    # ── SONUÇ ──
    if skor >= 2:
        yon, seviye, renk, uyari = "KUYRUK RÜZGARI", "GÜÇLÜ", "#10B981", False
        aciklama = "Borsa, sektör ve hisse aynı yönde — rüzgar arkanda."
    elif skor == 1:
        yon, seviye, renk, uyari = "Hafif Kuyruk", "ZAYIF", "#34D399", False
        aciklama = "Genel yön lehte ama tam destek yok."
    elif skor == 0:
        yon, seviye, renk, uyari = "Nötr", "—", "#94A3B8", False
        aciklama = "Karışık sinyaller — net rüzgar yok."
    elif skor == -1:
        yon, seviye, renk, uyari = "Hafif Karşı", "DİKKAT", "#F59E0B", True
        aciklama = "Büyük resim kısmen aleyhte — temkinli ol."
    else:
        yon, seviye, renk, uyari = "KARŞI RÜZGAR", "RİSKLİ", "#EF4444", True
        aciklama = "Borsa/sektör/hisse aleyhte — akıntıya karşı kürek. Dikkat."

    return {
        "skor": skor,
        "yon": yon,
        "seviye": seviye,
        "renk": renk,
        "bilesenler": bilesenler,
        "aciklama": aciklama,
        "uyari": uyari,
    }


def ruzgar_guven_etkisi(ruzgar):
    """
    Rüzgarın güven skoruna etkisi (çarpan).
    Kuyruk rüzgarı güveni artırır, karşı rüzgar düşürür.
    Dönen: çarpan (0.6 - 1.2 arası)
    """
    skor = ruzgar["skor"]
    # -3→0.6, 0→1.0, +3→1.2 civarı
    return max(0.6, min(1.2, 1.0 + skor * 0.08))
