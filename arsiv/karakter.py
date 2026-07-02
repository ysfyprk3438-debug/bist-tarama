"""
═══════════════════════════════════════════════════════════════
KARAKTER & STRATEJİ MOTORU — BIST Para Avcısı v4 (Katman 4 Tohumu)
═══════════════════════════════════════════════════════════════
İki derin aracı birleştirip üçüncüsünü doğurur:

  HURST ÜSSÜ → hissenin KARAKTERİ (trend mi yapar, salınım mı?)
    H > 0.55 : trend (biner, sürersin — momentum çalışır)
    H < 0.45 : salınım/mean-reversion (tepeden sat, dipten al)
    H ≈ 0.50 : rastgele (dokunma, kenar yok)

  RELATİF GÜÇ → hissenin ROLÜ (lider mi, takipçi mi?)
    Endeksten hızlı yükselen = lider, kurumsal para orada.
    Endeksten yavaş = takipçi, gücü yapay olabilir.

  ÜÇÜNCÜ (emergent) → STRATEJİ UYUMU
    Karakter + rol + volatilite rejimi birleşir.
    "Verdiğim AL sinyali bu hissenin karakterine UYUYOR mu?"
    Mean-reversion hissesine momentum sinyali = TUZAK (fiyat geri döner).
    Bu motor o uyumsuzluğu yakalar, güveni ona göre ayarlar.
"""

import numpy as np


# ══════════════════════════════════════════════════════════════
# HURST ÜSSÜ — hissenin karakteri (trend / salınım / rastgele)
# ══════════════════════════════════════════════════════════════
def hurst_ussu(close, max_lag=20):
    """
    Generalized Hurst (structure-function yöntemi).
    Log fiyat farklarının std'sinin lag ile ölçeklenme hızı = H.
    Dönen: H değeri (float) veya None
    """
    close = np.asarray(close, dtype=float)
    if len(close) < 60:
        return None
    logf = np.log(close + 1e-10)
    lags = range(2, min(max_lag, len(close) // 4))
    tau, gecerli = [], []
    for lag in lags:
        fark = logf[lag:] - logf[:-lag]
        s = np.std(fark)
        if s > 1e-12:
            tau.append(s)
            gecerli.append(lag)
    if len(gecerli) < 4:
        return None
    try:
        egim = np.polyfit(np.log(gecerli), np.log(tau), 1)[0]
        return float(egim)
    except Exception:
        return None


def hurst_yorum(H):
    """Hurst değerini karaktere çevirir (gerçek/gürültülü hisseler için kalibre)."""
    if H is None:
        return {"karakter": "BELİRSİZ", "renk": "#94A3B8", "aciklama": "Yetersiz veri"}
    if H >= 0.54:
        return {"karakter": "GÜÇLÜ TREND", "renk": "#10B981",
                "aciklama": "Hisse güçlü trend yapısında — momentum/trend takibi çalışır, dipten almaya kalkma."}
    elif H >= 0.495:
        return {"karakter": "TREND", "renk": "#34D399",
                "aciklama": "Trend eğilimli — yön takibi makul, kırılımlar güvenilir."}
    elif H > 0.45:
        return {"karakter": "RASTGELE", "renk": "#94A3B8",
                "aciklama": "Belirgin yön yok (rastgele yürüyüş) — net kenar yok, temkinli ol."}
    elif H > 0.38:
        return {"karakter": "SALINIM", "renk": "#F59E0B",
                "aciklama": "Ortalamaya dönme eğilimli — dipten al, tepeden sat (bant ticareti)."}
    else:
        return {"karakter": "GÜÇLÜ SALINIM", "renk": "#FB923C",
                "aciklama": "Güçlü mean-reversion — yükselişleri sat, düşüşleri al. Momentum sinyaline güvenme."}


# ══════════════════════════════════════════════════════════════
# RELATİF GÜÇ — hissenin rolü (lider / takipçi)
# ══════════════════════════════════════════════════════════════
def relatif_guc(hisse_close, endeks_close):
    """
    Hissenin endekse göre relatif gücü (çoklu ufuk).
    Lider = endeksten hızlı yükselen, kurumsal para orada.
    Dönen: {skor(0-100), rol, renk, getiri_farki, aciklama} veya None
    """
    if endeks_close is None:
        return None
    h = np.asarray(hisse_close, dtype=float)
    e = np.asarray(endeks_close, dtype=float)
    if len(h) < 30 or len(e) < 30:
        return None

    # Ortak uzunlukta hizala (son N)
    n = min(len(h), len(e))
    h, e = h[-n:], e[-n:]

    def _getiri(seri, gun):
        if len(seri) <= gun or seri[-gun-1] <= 0:
            return 0.0
        return (seri[-1] - seri[-gun-1]) / seri[-gun-1] * 100

    # Çoklu ufuk: ~1 ay (21), ~3 ay (63)
    fark_toplam = 0.0
    agirlik_toplam = 0.0
    for gun, agirlik in [(21, 0.6), (63, 0.4)]:
        if n > gun:
            hf = _getiri(h, gun)
            ef = _getiri(e, gun)
            fark_toplam += (hf - ef) * agirlik
            agirlik_toplam += agirlik
    getiri_farki = fark_toplam / agirlik_toplam if agirlik_toplam > 0 else 0

    # Skor: getiri farkını 0-100'e ölçekle (0 fark = 50)
    skor = int(max(0, min(100, 50 + getiri_farki * 5.5)))

    if skor >= 70:
        rol, renk = "LİDER", "#10B981"
        aciklama = f"Endeksten %{getiri_farki:+.1f} güçlü — kurumsal para burada, lider hisse."
    elif skor >= 55:
        rol, renk = "Güçlü", "#34D399"
        aciklama = f"Endeksten %{getiri_farki:+.1f} önde — pozitif ayrışma var."
    elif skor >= 45:
        rol, renk = "Nötr", "#94A3B8"
        aciklama = "Endeksle paralel — belirgin ayrışma yok."
    elif skor >= 30:
        rol, renk = "Zayıf", "#F59E0B"
        aciklama = f"Endeksin %{abs(getiri_farki):.1f} gerisinde — göreceli zayıf."
    else:
        rol, renk = "TAKİPÇİ", "#EF4444"
        aciklama = f"Endeksten %{getiri_farki:+.1f} geride — takipçi, gücü yapay olabilir."

    return {"skor": skor, "rol": rol, "renk": renk,
            "getiri_farki": round(getiri_farki, 1), "aciklama": aciklama}


# ══════════════════════════════════════════════════════════════
# STRATEJİ UYUMU (emergent) — sinyal hissenin karakterine uyuyor mu?
# ══════════════════════════════════════════════════════════════
def karakter_profili(hisse_close, endeks_close, sinyal_tip, volatilite_rejim=None):
    """
    Hurst + relatif güç + volatilite rejimini birleştirir.
    Sinyalin hissenin karakterine UYUP UYMADIĞINI ölçer.

    Dönen: {dna, hurst, H, rs, strateji, uyum_skoru, uyum_yorum, guven_etkisi}
    """
    H = hurst_ussu(hisse_close)
    hy = hurst_yorum(H)
    rs = relatif_guc(hisse_close, endeks_close)

    # DNA etiketi: karakter + rol
    rol_kisa = rs["rol"] if rs else "—"
    dna = f"{hy['karakter']} · {rol_kisa}"

    # ── STRATEJİ EŞLEŞTİRME ──
    # Hisse karakteri hangi stratejiyi ister?
    if H is not None and H >= 0.495:
        uygun_strateji = "momentum"   # trend → momentum/trend takibi
    elif H is not None and H <= 0.45:
        uygun_strateji = "reversion"  # salınım → dipten alım
    else:
        uygun_strateji = "belirsiz"

    # Sinyalimiz hangi stratejiye ait?
    # AL·Güçlü / AL·Trend / Takipte = momentum tarzı
    # DİP FIRSATI = reversion tarzı
    if sinyal_tip and "DİP" in sinyal_tip:
        sinyal_strateji = "reversion"
    else:
        sinyal_strateji = "momentum"

    # ── UYUM SKORU ──
    if uygun_strateji == "belirsiz":
        uyum_skoru = 50
        uyum_yorum = "Hisse karakteri belirsiz (rastgele) — sinyal-karakter uyumu net değil."
        guven_etkisi = 1.0
    elif uygun_strateji == sinyal_strateji:
        uyum_skoru = 85
        if sinyal_strateji == "momentum":
            uyum_yorum = "✓ Trend hissesine trend sinyali — karakterle UYUMLU, güvenilir."
        else:
            uyum_yorum = "✓ Salınım hissesine dip sinyali — karakterle UYUMLU, güvenilir."
        guven_etkisi = 1.12
    else:
        uyum_skoru = 30
        if sinyal_strateji == "momentum" and uygun_strateji == "reversion":
            uyum_yorum = "⚠ Salınım hissesine momentum sinyali — UYUMSUZ. Fiyat zıpladı, geri dönebilir (tuzak)."
        else:
            uyum_yorum = "⚠ Trend hissesine dip sinyali — UYUMSUZ. Trend devam edebilir, erken dip aramak riskli."
        guven_etkisi = 0.82

    # Lider hisse uyumu güçlendirir, takipçi zayıflatır
    if rs:
        if rs["skor"] >= 70:
            guven_etkisi *= 1.05
        elif rs["skor"] <= 30:
            guven_etkisi *= 0.92

    return {
        "dna": dna,
        "H": round(H, 3) if H is not None else None,
        "hurst": hy,
        "rs": rs,
        "uygun_strateji": uygun_strateji,
        "sinyal_strateji": sinyal_strateji,
        "uyum_skoru": uyum_skoru,
        "uyum_yorum": uyum_yorum,
        "guven_etkisi": round(guven_etkisi, 3),
    }
