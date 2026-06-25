"""
═══════════════════════════════════════════════════════════════
PİYASA GENİŞLİĞİ (Market Breadth) — BIST Para Avcısı v4
═══════════════════════════════════════════════════════════════
Derin gerçek: Endeks YÖNÜ yanıltıcıdır. Asıl önemli olan KAÇ HİSSE
katılıyor? Endeks birkaç dev hisseyle yukarı giderken çoğu hisse
düşüyorsa, o yükseliş İÇİ BOŞTUR — çöküş yakındır.

Genişlik, piyasanın yönünü değil SAĞLIĞINI ölçer:
  • MA200 üstü oranı → uzun vadeli katılım (>%50 = sağlıklı boğa)
  • MA50 üstü oranı  → kısa/orta vadeli katılım
  • Yükselen/düşen oranı → günlük momentum genişliği
  • Yeni zirve/dip → liderlik sağlığı

EN KRİTİK: IRAKSAMA (divergence). Endeks yukarı ama genişlik
daralıyorsa → içi boş yükseliş, uyarı. Profesyonellerin en
güvendiği erken uyarı sinyallerinden biri.

Not: Genişlik TÜM taranan hisselerden hesaplanır (sadece sinyal
verenlerden değil) — bu yüzden tarama sırasında ayrıca toplanır.
"""

import numpy as np


def genislik_katki(df):
    """
    Tek bir hissenin genişlik katkısını çıkarır (sinyal versin vermesin).
    Dönen: {ma50_ustu, ma200_ustu, yukseldi, zirve_yakin, dip_yakin} veya None
    """
    if df is None or len(df) < 50:
        return None
    k = df["Close"]
    fiyat = float(k.iloc[-1])

    ma50 = float(k.rolling(50).mean().iloc[-1])
    ma200 = float(k.rolling(200).mean().iloc[-1]) if len(k) >= 200 else float(k.rolling(min(150, len(k))).mean().iloc[-1])

    # Günlük yön
    yukseldi = bool(len(k) >= 2 and k.iloc[-1] > k.iloc[-2])

    # 52 hafta (≈252 gün) zirve/dip yakınlığı
    pencere = k.iloc[-252:] if len(k) >= 252 else k
    en_yuksek = float(pencere.max())
    en_dusuk = float(pencere.min())
    zirve_yakin = bool(en_yuksek > 0 and (en_yuksek - fiyat) / en_yuksek < 0.03)
    dip_yakin = bool(en_dusuk > 0 and (fiyat - en_dusuk) / en_dusuk < 0.03)

    return {
        "ma50_ustu": bool(fiyat > ma50),
        "ma200_ustu": bool(fiyat > ma200),
        "yukseldi": yukseldi,
        "zirve_yakin": zirve_yakin,
        "dip_yakin": dip_yakin,
    }


def genislik_ozeti(katkilar, endeks_pct=0.0):
    """
    Tüm hisselerin katkılarını birleştirip piyasa sağlığını çıkarır.
    katkilar: genislik_katki çıktılarının listesi (None'lar atlanır)
    endeks_pct: endeksin dönemsel değişimi (ıraksama tespiti için)

    Dönen: {ma50_oran, ma200_oran, yukselen_oran, yeni_zirve, yeni_dip,
            saglik, renk, mesaj, iraksama, toplam}
    """
    gecerli = [k for k in katkilar if k is not None]
    n = len(gecerli)
    if n < 5:
        return None

    ma50_oran = sum(1 for k in gecerli if k["ma50_ustu"]) / n * 100
    ma200_oran = sum(1 for k in gecerli if k["ma200_ustu"]) / n * 100
    yukselen_oran = sum(1 for k in gecerli if k["yukseldi"]) / n * 100
    yeni_zirve = sum(1 for k in gecerli if k["zirve_yakin"])
    yeni_dip = sum(1 for k in gecerli if k["dip_yakin"])

    # ── SAĞLIK YARGISI (MA200 üstü oranı ana ölçüt) ──
    if ma200_oran >= 60:
        saglik, renk = "GÜÇLÜ", "#10B981"
        mesaj = f"Hisselerin %{ma200_oran:.0f}'i uzun vadeli ortalamasının üstünde — geniş, sağlıklı katılım. Boğa piyasası gövdeli."
    elif ma200_oran >= 45:
        saglik, renk = "SAĞLIKLI", "#34D399"
        mesaj = f"%{ma200_oran:.0f} katılım — piyasa dengeli, yükseliş tabana yayılmış."
    elif ma200_oran >= 30:
        saglik, renk = "ZAYIF", "#F59E0B"
        mesaj = f"Sadece %{ma200_oran:.0f} katılım — yükseliş dar tabanlı, kırılgan. Dikkatli ol."
    else:
        saglik, renk = "ZAYIF/AYI", "#EF4444"
        mesaj = f"Hisselerin sadece %{ma200_oran:.0f}'i uzun ortalamasının üstünde — geniş zayıflık, ayı baskısı."

    # ── IRAKSAMA (en kritik erken uyarı) ──
    iraksama = None
    if endeks_pct > 1 and ma50_oran < 40:
        iraksama = {
            "var": True, "renk": "#EF4444",
            "mesaj": "⚠ IRAKSAMA: Endeks yükseliyor ama hisselerin çoğu katılmıyor — içi boş yükseliş, dönüş riski yüksek.",
        }
    elif endeks_pct < -1 and ma50_oran > 60:
        iraksama = {
            "var": True, "renk": "#10B981",
            "mesaj": "✓ POZİTİF IRAKSAMA: Endeks düşüyor ama hisseler dayanıyor — satış tükeniyor olabilir, dipten dönüş sinyali.",
        }
    else:
        iraksama = {"var": False, "renk": "#94A3B8", "mesaj": ""}

    return {
        "ma50_oran": round(ma50_oran, 0),
        "ma200_oran": round(ma200_oran, 0),
        "yukselen_oran": round(yukselen_oran, 0),
        "yeni_zirve": yeni_zirve,
        "yeni_dip": yeni_dip,
        "saglik": saglik, "renk": renk, "mesaj": mesaj,
        "iraksama": iraksama,
        "toplam": n,
    }
