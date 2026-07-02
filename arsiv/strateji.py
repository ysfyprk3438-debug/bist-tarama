"""
═══════════════════════════════════════════════════════════════
STRATEJİ SEÇİCİ — BIST Para Avcısı v4 (Katman 4: Adaptif Meta-Beyin)
═══════════════════════════════════════════════════════════════
Sistemin zirvesi. Artık tek sabit beyin değil — DURUMA GÖRE kendini
değiştiren bir akıl. Yol haritasındaki "Strateji Ekosistemi".

Derin gerçek: Farklı piyasa koşulları farklı strateji ister.
  • Sakin + yükseliş + geniş katılım → MOMENTUM (trend avcısı)
  • Dalgalı/yatay + sakin → REVERSION (dip toplayıcı)
  • Sıkışma (düşük vol, patlama öncesi) → BREAKOUT (kırılım takipçisi)
  • Fırtına + zayıf katılım + düşüş → DEFANSİF (savunma, nakit)

Bir hissenin sinyali harika olabilir ama o strateji "sezon dışı"ysa
kenar zayıftır. Bu motor üç şeyi söyler:
  1. PİYASA STRATEJİSİ → şu an hangi oyun oynanıyor (sezon)
  2. HİSSE STRATEJİSİ → bu hisse hangi oyunu temsil ediyor
  3. UYUM → ikisi örtüşüyor mu? (sezon + uyumlu hisse = en güçlü)

Tek strateji her rejimde kaybeder; ekosistem ayakta kalır.
"""


# Strateji arketipleri
STRATEJILER = {
    "MOMENTUM": {"ad": "Momentum Avcısı", "ikon": "🚀", "renk": "#10B981",
                 "aciklama": "Trend takibi — güçlü yönü kovala, kırılımları al"},
    "REVERSION": {"ad": "Dip Toplayıcı", "ikon": "🎣", "renk": "#38BDF8",
                  "aciklama": "Ortalamaya dönüş — düşüşleri al, aşırılıkları sat"},
    "BREAKOUT": {"ad": "Kırılım Takipçisi", "ikon": "💥", "renk": "#F59E0B",
                 "aciklama": "Sıkışma sonrası patlama — kırılım yönünde gir"},
    "DEFANSIF": {"ad": "Savunma", "ikon": "🛡️", "renk": "#EF4444",
                 "aciklama": "Sermaye koru — nakitte kal, sadece en güçlüsü"},
}


def piyasa_stratejisi(genislik, rejim_metni, endeks_vol_rejim=None):
    """
    Şu an hangi strateji arketipi 'sezonda'? Piyasa geneline bakar.
    Dönen: {strateji, ad, ikon, renk, aciklama, gerekce}
    """
    dususte = "DÜŞÜŞ" in (rejim_metni or "")
    yuksekte = "YÜKSELİŞ" in (rejim_metni or "")
    ma200 = genislik.get("ma200_oran", 50) if genislik else 50
    zayif_katilim = ma200 < 40
    saglikli_katilim = ma200 >= 50

    # Öncelik sırası
    # 1. DEFANSİF: düşüş VEYA (fırtına + zayıf katılım)
    if dususte or (endeks_vol_rejim == "FIRTINA" and zayif_katilim):
        s = "DEFANSIF"
        gerekce = "Düşüş/zayıf katılım — sermaye koruma zamanı, agresif olma."
    # 2. BREAKOUT: sıkışma (patlama öncesi)
    elif endeks_vol_rejim == "SIKIŞMA":
        s = "BREAKOUT"
        gerekce = "Piyasa sıkışmış — büyük hareket yaklaşıyor, kırılım yönü izlenecek."
    # 3. MOMENTUM: yükseliş + sağlıklı katılım
    elif yuksekte and saglikli_katilim:
        s = "MOMENTUM"
        gerekce = "Yükseliş + geniş katılım — trend takibi en verimli strateji."
    # 4. REVERSION: yatay/dengeli, sakin
    else:
        s = "REVERSION"
        gerekce = "Yatay/dengeli piyasa — aşırılıklardan dönüş (dip al, tepe sat) çalışır."

    meta = STRATEJILER[s]
    return {"strateji": s, "ad": meta["ad"], "ikon": meta["ikon"],
            "renk": meta["renk"], "aciklama": meta["aciklama"], "gerekce": gerekce}


def hisse_stratejisi(r):
    """
    Bu hisse hangi strateji arketipini temsil ediyor?
    Karakter (Hurst) + niyet + alarm + volatiliteye bakar.
    Dönen: strateji kodu
    """
    karakter = r.get("karakter", {})
    hurst_k = karakter.get("hurst", {}).get("karakter", "")
    niyet = r.get("niyet", {}).get("sinif", "")
    alarm = r.get("alarm", {})
    vol = r.get("volatilite", {}).get("rejim", "")

    # Kırılım: sıkışma rejimi veya direnç kırılımı alarmı
    if vol == "SIKIŞMA" or (alarm.get("var") and alarm.get("tip") == "direnc_yakin"):
        return "BREAKOUT"
    # Dip toplama: salınım karakteri, dip oluşumu, veya dip alarmı
    if "SALINIM" in hurst_k or niyet == "DİP OLUŞUMU" or (alarm.get("var") and alarm.get("yon") == "firsat"):
        return "REVERSION"
    # Momentum: trend karakteri
    if "TREND" in hurst_k:
        return "MOMENTUM"
    # Sinyal tipine göre varsayılan
    sinyal = r.get("sinyal", "")
    if "DİP" in sinyal:
        return "REVERSION"
    return "MOMENTUM"


def strateji_analizi(r, piyasa_strat):
    """
    Hisse stratejisi ile piyasa sezonunu birleştirir — uyumu ölçer.
    piyasa_strat: piyasa_stratejisi çıktısı
    Dönen: {hisse_strateji, piyasa_strateji, uyum, uyum_yorum, karar_etkisi, ...}
    """
    h_strat = hisse_stratejisi(r)
    p_strat = piyasa_strat["strateji"]
    h_meta = STRATEJILER[h_strat]

    # ── UYUM DEĞERLENDİRMESİ ──
    if p_strat == "DEFANSIF":
        # Savunma sezonunda agresif strateji = tehlike
        if h_strat in ("MOMENTUM", "BREAKOUT"):
            uyum, etki = "SEZON DIŞI", -8
            yorum = f"Piyasa savunmada ama bu bir {h_meta['ad'].lower()} oyunu — akıntıya karşı, riskli."
        else:
            uyum, etki = "UYUMLU", 2
            yorum = "Savunma sezonunda temkinli strateji — uyumlu."
    elif h_strat == p_strat:
        uyum, etki = "SEZON İÇİ ✓", 8
        yorum = f"{h_meta['ad']} hem hissenin karakteri hem de piyasa sezonu — en güçlü uyum."
    else:
        # Farklı ama savunma değil — nötr/hafif
        uyum, etki = "FARKLI", -2
        yorum = f"Bu {h_meta['ad'].lower()} oyunu ama piyasa {piyasa_strat['ad'].lower()} sezonunda — kenar zayıf olabilir."

    return {
        "hisse_strateji": h_strat,
        "hisse_strateji_ad": h_meta["ad"],
        "hisse_ikon": h_meta["ikon"],
        "hisse_renk": h_meta["renk"],
        "piyasa_strateji": p_strat,
        "piyasa_strateji_ad": piyasa_strat["ad"],
        "uyum": uyum,
        "uyum_yorum": yorum,
        "karar_etkisi": etki,  # av skoruna eklenecek (-8 .. +8)
    }
