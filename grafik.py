"""
═══════════════════════════════════════════════════════════════
GRAFİK + TEKNİK OLAY TESPİTİ — BIST Para Avcısı v4
═══════════════════════════════════════════════════════════════
Hisseye "al" dendiğinde kullanıcı grafiği açıp KENDİ GÖZÜYLE görebilsin.
Grafikte olup bitenler işaretlenir + tek cümleyle özetlenir.

Tespit edilen olaylar:
  • ALTIN KESİŞİM   → MA50, MA200'ü yukarı keser (güçlü yükseliş)
  • ÖLÜM KESİŞİMİ   → MA50, MA200'ü aşağı keser (zayıflık)
  • DİRENÇ KIRILIMI → fiyat son direnci yukarı kırar
  • DESTEK TESTİ    → fiyat destek bölgesine yakın
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import io
import numpy as np
import pandas as pd


# ══════════════════════════════════════════════════════════════
# TEKNİK OLAY TESPİTİ (tam df üzerinde — MA200 için 200+ gün gerekir)
# ══════════════════════════════════════════════════════════════
def teknik_olaylar(df, son_gun=120):
    """
    Tam OHLCV df'inden teknik olayları çıkarır.
    Sadece son 'son_gun' içindeki olaylar döner (grafikte görünür olanlar).
    Dönen: liste [{tip, tarih, fiyat, etiket, renk, yon}]
    """
    if df is None or len(df) < 60:
        return []

    k = df["Close"]
    h = df["High"]
    l = df["Low"]
    olaylar = []

    # Hareketli ortalamalar (tam seri üzerinde)
    ma50 = k.rolling(50).mean()
    ma200 = k.rolling(200).mean() if len(k) >= 200 else k.rolling(min(100, len(k)//2)).mean()

    # Görünür pencere sınırı
    pencere_basi = len(df) - son_gun if len(df) > son_gun else 0

    # ── ALTIN / ÖLÜM KESİŞİMİ ──
    for i in range(max(1, pencere_basi), len(df)):
        if pd.isna(ma50.iloc[i]) or pd.isna(ma200.iloc[i]):
            continue
        if pd.isna(ma50.iloc[i-1]) or pd.isna(ma200.iloc[i-1]):
            continue
        onceki_fark = ma50.iloc[i-1] - ma200.iloc[i-1]
        simdi_fark = ma50.iloc[i] - ma200.iloc[i]
        if onceki_fark <= 0 and simdi_fark > 0:
            olaylar.append({
                "tip": "altin_kesisim", "tarih": df.index[i],
                "fiyat": float(k.iloc[i]), "etiket": "Altın Kesişim",
                "renk": "#10B981", "yon": "pozitif",
            })
        elif onceki_fark >= 0 and simdi_fark < 0:
            olaylar.append({
                "tip": "olum_kesisimi", "tarih": df.index[i],
                "fiyat": float(k.iloc[i]), "etiket": "Ölüm Kesişimi",
                "renk": "#EF4444", "yon": "negatif",
            })

    # ── DİRENÇ KIRILIMI (son fiyat, önceki 20 günün tepesini aştıysa) ──
    if len(df) >= 25:
        son_fiyat = float(k.iloc[-1])
        onceki_direnc = float(h.iloc[-21:-1].max())
        if son_fiyat > onceki_direnc:
            olaylar.append({
                "tip": "direnc_kirilim", "tarih": df.index[-1],
                "fiyat": son_fiyat, "etiket": "Direnç Kırıldı",
                "renk": "#38BDF8", "yon": "pozitif",
            })

    # ── DESTEK TESTİ (son fiyat, 20 günün dibine %3 yakınsa) ──
    if len(df) >= 25:
        son_fiyat = float(k.iloc[-1])
        destek = float(l.iloc[-21:-1].min())
        if destek > 0 and (son_fiyat - destek) / destek < 0.03:
            olaylar.append({
                "tip": "destek_testi", "tarih": df.index[-1],
                "fiyat": son_fiyat, "etiket": "Destek Bölgesi",
                "renk": "#F59E0B", "yon": "notr",
            })

    return olaylar


# ══════════════════════════════════════════════════════════════
# TEK CÜMLELİK YORUM (en önemli olayı özetler)
# ══════════════════════════════════════════════════════════════
def grafik_yorum(olaylar, r=None):
    """Grafikteki en önemli olayı tek cümleyle özetler."""
    if not olaylar:
        # Olay yoksa trend bazlı genel yorum
        if r:
            trend = r.get("trend", 0)
            if trend >= 3:
                return "Fiyat tüm ortalamaların üzerinde — trend güçlü ve yukarı yönlü."
            elif trend <= 1:
                return "Fiyat ortalamaların altında — trend zayıf, temkinli olunmalı."
            return "Yatay seyir — net bir yön sinyali yok."
        return "Belirgin teknik olay yok."

    # Öncelik sırası: altın kesişim > direnç kırılım > destek > ölüm kesişimi
    oncelik = {"altin_kesisim": 1, "direnc_kirilim": 2, "destek_testi": 3, "olum_kesisimi": 4}
    en_onemli = sorted(olaylar, key=lambda x: oncelik.get(x["tip"], 9))[0]

    yorumlar = {
        "altin_kesisim": "MA50, MA200'ü yukarı kesti (altın kesişim) — güçlü ve kalıcı yükseliş sinyali.",
        "direnc_kirilim": "Fiyat son direnci yukarı kırdı — yükseliş hareketi başlıyor olabilir.",
        "destek_testi": "Fiyat güçlü destek bölgesinde — buradan dönüş (sıçrama) bekleniyor.",
        "olum_kesisimi": "MA50, MA200'ü aşağı kesti (ölüm kesişimi) — zayıflık işareti, dikkatli ol.",
    }
    return yorumlar.get(en_onemli["tip"], "Teknik hareket tespit edildi.")


# ══════════════════════════════════════════════════════════════
# GRAFİK ÇİZ (fiyat + MA50 + MA200 + olay işaretleri)
# ══════════════════════════════════════════════════════════════
def grafik_ciz(grafik_df, olaylar=None, kod=""):
    """
    Zenginleştirilmiş grafik: fiyat + ortalamalar + olay işaretleri.
    grafik_df: Close, MA50, MA200 kolonları olan df (son ~120 gün)
    olaylar: teknik_olaylar çıktısı
    Dönen: png buffer
    """
    try:
        fig, ax = plt.subplots(figsize=(9, 3.2))
        fig.patch.set_facecolor("#0D1117")
        ax.set_facecolor("#0D1117")

        t = grafik_df.index
        k = grafik_df["Close"].values
        renk = "#10B981" if k[-1] >= k[0] else "#EF4444"

        # Fiyat
        ax.plot(t, k, color=renk, linewidth=1.6, label="Fiyat", zorder=3)
        ax.fill_between(t, k, np.nanmin(k), alpha=0.08, color=renk, zorder=1)

        # MA50 / MA200
        if "MA50" in grafik_df.columns:
            ma50 = grafik_df["MA50"].values
            if not np.all(np.isnan(ma50)):
                ax.plot(t, ma50, color="#38BDF8", linewidth=1.0, linestyle="-", label="MA50", alpha=0.9, zorder=2)
        if "MA200" in grafik_df.columns:
            ma200 = grafik_df["MA200"].values
            if not np.all(np.isnan(ma200)):
                ax.plot(t, ma200, color="#F59E0B", linewidth=1.0, linestyle="-", label="MA200", alpha=0.9, zorder=2)

        # Olay işaretleri
        if olaylar:
            for o in olaylar:
                if o["tarih"] in grafik_df.index:
                    ax.scatter([o["tarih"]], [o["fiyat"]], color=o["renk"], s=90,
                               zorder=5, edgecolors="white", linewidths=1.0, marker="*")
                    ax.annotate(o["etiket"], (o["tarih"], o["fiyat"]),
                                textcoords="offset points", xytext=(0, 12),
                                fontsize=7.5, color=o["renk"], fontweight="bold",
                                ha="center", zorder=6)

        ax.tick_params(colors="#475569", labelsize=7)
        for s in ax.spines.values():
            s.set_edgecolor("#1E293B")
        ax.grid(axis="y", color="#1E293B", linewidth=0.5, alpha=0.5)
        ax.legend(loc="upper left", fontsize=7, facecolor="#0D1117",
                  edgecolor="#1E293B", labelcolor="#94A3B8")
        plt.tight_layout(pad=0.4)

        buf = io.BytesIO()
        plt.savefig(buf, format="png", dpi=100, bbox_inches="tight", facecolor="#0D1117")
        plt.close()
        buf.seek(0)
        return buf
    except Exception:
        plt.close()
        return None
