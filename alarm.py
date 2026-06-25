"""
═══════════════════════════════════════════════════════════════
ALARM MOTORU — BIST Para Avcısı v4
═══════════════════════════════════════════════════════════════
Olaydan ÖNCE yakala. "Altın kesişim oldu" değil, "olmak üzere".
Kart kritik olaya yaklaştıkça canlanır, titreşir, alarm verir.

Cin fikir: GERİ SAYIM. MA'ların yaklaşma hızından, olaya kaç gün
kaldığını tahmin eder. "Altın kesişime ~2 gün."

Yaklaşan olaylar + renk kodu:
  ⚡ Yaklaşan Altın Kesişim → yeşil (fırsat geliyor)
  🔴 Yaklaşan Ölüm Kesişimi → kırmızı (tehlike geliyor)
  💥 Direnç Kırılımı Yakın  → mavi (patlama yakın)
  🟦 Dip Yakını             → turkuaz (dönüş fırsatı)
  🟠 Zirve Yakını           → turuncu (tepe, dikkat)
"""

import numpy as np
import pandas as pd


def _gun_yakinlik(gun):
    """Tahmini gün sayısını yakınlık yüzdesine çevirir (az gün = yüksek alarm)."""
    if gun <= 1: return 95
    if gun <= 2: return 88
    if gun <= 3: return 80
    if gun <= 5: return 68
    if gun <= 8: return 55
    if gun <= 12: return 42
    if gun <= 20: return 30
    return 15


def yaklasan_olaylar(df, bak=10):
    """
    Yaklaşan kritik olayları tespit eder + geri sayım hesaplar.
    Dönen: liste [{tip, etiket, yakinlik(0-100), gun, renk, yon, mesaj}]
    """
    if df is None or len(df) < 60:
        return []

    k = df["Close"]
    h = df["High"]
    l = df["Low"]
    fiyat = float(k.iloc[-1])
    olaylar = []

    ma50 = k.rolling(50).mean()
    ma200 = k.rolling(200).mean() if len(k) >= 200 else k.rolling(min(100, len(k)//2)).mean()

    # ── YAKLAŞAN ALTIN / ÖLÜM KESİŞİMİ (geri sayım) ──
    if len(k) > bak and not pd.isna(ma50.iloc[-1]) and not pd.isna(ma200.iloc[-1]) \
       and not pd.isna(ma50.iloc[-1-bak]) and not pd.isna(ma200.iloc[-1-bak]):
        gap_simdi = float(ma50.iloc[-1] - ma200.iloc[-1])
        gap_once = float(ma50.iloc[-1-bak] - ma200.iloc[-1-bak])
        hiz = (gap_simdi - gap_once) / bak  # günlük gap değişimi

        if gap_simdi < 0 and hiz > 0:
            # MA50 altta ama yaklaşıyor → ALTIN KESİŞİM geliyor
            gun = -gap_simdi / hiz if hiz > 1e-9 else 999
            if gun <= 25:
                yk = _gun_yakinlik(gun)
                olaylar.append({
                    "tip": "yaklasan_altin", "etiket": "Altın Kesişim Yakın",
                    "yakinlik": yk, "gun": int(round(gun)), "renk": "#10B981", "yon": "pozitif",
                    "mesaj": f"MA50, MA200'e yaklaşıyor — altın kesişime tahmini {int(round(gun))} gün. Yükseliş sinyali hazırlanıyor.",
                })
        elif gap_simdi > 0 and hiz < 0:
            # MA50 üstte ama düşüyor → ÖLÜM KESİŞİMİ geliyor
            gun = gap_simdi / -hiz if hiz < -1e-9 else 999
            if gun <= 25:
                yk = _gun_yakinlik(gun)
                olaylar.append({
                    "tip": "yaklasan_olum", "etiket": "Ölüm Kesişimi Yakın",
                    "yakinlik": yk, "gun": int(round(gun)), "renk": "#EF4444", "yon": "negatif",
                    "mesaj": f"MA50 aşağı dönüyor — ölüm kesişimine tahmini {int(round(gun))} gün. Zayıflık yaklaşıyor, dikkat.",
                })

    # ── DİRENÇ KIRILIMI YAKIN (fiyat direncin hemen altında, GÜÇLÜ yükseliyor) ──
    if len(k) >= 25:
        direnc = float(h.iloc[-21:-1].max())
        mesafe_pct = (direnc - fiyat) / fiyat * 100 if fiyat > 0 else 99
        son5_egim_pct = (float(k.iloc[-1] - k.iloc[-5]) / fiyat * 100) if (len(k) >= 5 and fiyat > 0) else 0
        # Dar mesafe (%1.5) + anlamlı yükseliş (son 5 günde >%2) gerekli
        if 0 < mesafe_pct <= 1.5 and son5_egim_pct > 2:
            yk = int(95 - mesafe_pct * 25)
            olaylar.append({
                "tip": "direnc_yakin", "etiket": "Direnç Kırılımı Yakın",
                "yakinlik": max(50, yk), "gun": None, "renk": "#38BDF8", "yon": "pozitif",
                "mesaj": f"Fiyat dirence %{mesafe_pct:.1f} mesafede ve güçlü yükseliyor — kırılım çok yakın, patlama olabilir.",
            })

    # ── DİP YAKINI (aşırı satım + destek bölgesi) ──
    delta = k.diff()
    kazanc = delta.clip(lower=0).rolling(14).mean()
    kayip = (-delta.clip(upper=0)).rolling(14).mean()
    rs = kazanc / (kayip + 1e-10)
    rsi_son = float((100 - 100/(1+rs)).iloc[-1])
    if np.isnan(rsi_son):
        rsi_son = 50.0

    if len(k) >= 25:
        destek = float(l.iloc[-21:-1].min())
        dip_mesafe = (fiyat - destek) / destek * 100 if destek > 0 else 99
        if dip_mesafe <= 3 and rsi_son < 35:
            olaylar.append({
                "tip": "dip_yakin", "etiket": "Dip Bölgesi",
                "yakinlik": int(min(90, 70 + (35 - rsi_son))), "gun": None, "renk": "#06B6D4", "yon": "firsat",
                "mesaj": f"Fiyat destekte (RSI {rsi_son:.0f}, aşırı satım) — dipten dönüş fırsatı oluşuyor olabilir.",
            })

    # ── ZİRVE YAKINI (aşırı alım + direnç) — sadece RSI gerçekten yüksekse ──
    if len(k) >= 25:
        direnc2 = float(h.iloc[-21:-1].max())
        zirve_mesafe = abs(direnc2 - fiyat) / fiyat * 100 if fiyat > 0 else 99
        if zirve_mesafe <= 2 and rsi_son > 75:
            olaylar.append({
                "tip": "zirve_yakin", "etiket": "Zirve Bölgesi",
                "yakinlik": int(min(92, 70 + (rsi_son - 75))), "gun": None, "renk": "#F59E0B", "yon": "dikkat",
                "mesaj": f"Fiyat dirençte (RSI {rsi_son:.0f}, aşırı alım) — zirve yakını, geri çekilme riski.",
            })

    # Yakınlığa göre sırala (en kritik üstte)
    olaylar.sort(key=lambda x: x["yakinlik"], reverse=True)
    return olaylar


def alarm_ozeti(yaklasanlar):
    """
    Bir hissenin genel alarm durumunu döner.
    Dönen: {seviye, yakinlik, renk, etiket, mesaj, titresim}
    titresim: True ise kart titreşmeli (yüksek alarm)
    """
    if not yaklasanlar:
        return {"seviye": "YOK", "yakinlik": 0, "renk": "#1E293B",
                "etiket": "", "mesaj": "", "titresim": False, "var": False}

    en = yaklasanlar[0]  # en yüksek yakınlıklı olay
    yk = en["yakinlik"]

    if yk >= 80:
        seviye, titresim = "KRİTİK", True
    elif yk >= 60:
        seviye, titresim = "YÜKSEK", False
    else:
        seviye, titresim = "ORTA", False

    return {
        "seviye": seviye, "yakinlik": yk, "renk": en["renk"],
        "etiket": en["etiket"], "mesaj": en["mesaj"],
        "gun": en.get("gun"), "yon": en["yon"],
        "titresim": titresim, "var": True,
        "tum": yaklasanlar,
    }
