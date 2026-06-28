# -*- coding: utf-8 -*-
"""
═══════════════════════════════════════════════════════════════
ajanlar.py — APEX AJAN KATMANI  (standalone + görsel)
═══════════════════════════════════════════════════════════════
Hiçbir mevcut dosyaya BAĞIMLI DEĞİL. numpy + pandas + matplotlib.
Tek girdi: bir hissenin OHLCV DataFrame'i (Open/High/Low/Close/Volume).
Canlı app.py'yi BOZMAZ — import edilip TEK fonksiyonla çağrılır:

    import ajanlar
    ajanlar.panel_goster(st, df, stop_fiyat=stop, kod="AKBNK")

İçindeki ajanlar:
  1) grafik_ogretmen(df)  → grafikteki her şeyi AÇIKLAR + O ANKİ durumu okur
  2) kacinilacak_mi(df)   → "buradan düşüş normal mi?" tehlike okuması (tersinden)
  3) projektor(df)        → Monte Carlo belirsizlik konisi + stop'a değme olasılığı
  4) risk_parity(...)     → her pozisyon EŞİT risk taşısın diye lot dağıtımı
  + panel_ciz / projektor_ciz / panel_goster → görsel

DÜRÜSTLÜK İLKESİ (değişmez):
  • Hiçbir fonksiyon "şu kadar kazanır" demez. Yön tahmini yok (drift=0).
  • Projektör KEHANET değil — belirsizliğin GENİŞLİĞİDİR.
  • Kaçınılacak ajanı "kesin düşer" demez; "buradan düşüş normal karşılanır" der.
"""

import io
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


# ══════════════════════════════════════════════════════════════
# ORTAK YARDIMCILAR
# ══════════════════════════════════════════════════════════════
def _ma(close, p):
    return close.rolling(p).mean()


def _atr(df, p=14):
    h, l, c = df["High"], df["Low"], df["Close"]
    onceki = c.shift(1)
    tr = pd.concat([h - l, (h - onceki).abs(), (l - onceki).abs()], axis=1).max(axis=1)
    return tr.rolling(p).mean()


def _son(x, varsayilan=np.nan):
    try:
        v = float(x.iloc[-1])
        return v if not np.isnan(v) else varsayilan
    except Exception:
        return varsayilan


def _kesisim_bul(ma_kisa, ma_uzun):
    """MA50/MA200 kesişimleri. 'altin'=yukarı keser, 'olum'=aşağı keser."""
    k = ma_kisa.values
    u = ma_uzun.values
    idx = ma_kisa.index
    olaylar = []
    for i in range(1, len(k)):
        if np.isnan(k[i]) or np.isnan(u[i]) or np.isnan(k[i - 1]) or np.isnan(u[i - 1]):
            continue
        if (k[i - 1] - u[i - 1]) <= 0 and (k[i] - u[i]) > 0:
            olaylar.append({"tip": "altin", "indeks": i, "tarih": idx[i]})
        elif (k[i - 1] - u[i - 1]) >= 0 and (k[i] - u[i]) < 0:
            olaylar.append({"tip": "olum", "indeks": i, "tarih": idx[i]})
    return olaylar


# ══════════════════════════════════════════════════════════════
# AJAN 1 — GRAFİK ÖĞRETMEN
# ══════════════════════════════════════════════════════════════
def grafik_ogretmen(df):
    if df is None or len(df) < 30:
        return {"maddeler": [], "son_kesisim": None, "ozet": "Yeterli veri yok."}

    close = df["Close"]
    son_fiyat = _son(close)
    ma50 = _ma(close, 50)
    ma200 = _ma(close, 200)
    ma50_son = _son(ma50, son_fiyat)
    ma200_son = _son(ma200, son_fiyat)
    maddeler = []

    if son_fiyat >= ma50_son:
        d50 = f"Fiyat MA50'nin ÜSTÜNDE (%{(son_fiyat/ma50_son-1)*100:+.1f}) — kısa vadeli görünüm pozitif."
        r50 = "#10B981"
    else:
        d50 = f"Fiyat MA50'nin ALTINDA (%{(son_fiyat/ma50_son-1)*100:+.1f}) — kısa vadeli görünüm zayıf."
        r50 = "#EF4444"
    maddeler.append({"baslik": "MA50 (mavi çizgi)",
        "nedir": "Son 50 günün ortalama kapanışı. Günlük dalgalanmayı temizler, KISA vadeli yönü gösterir.",
        "durum": d50, "renk": r50})

    if son_fiyat >= ma200_son:
        d200 = f"Fiyat MA200'ün ÜSTÜNDE (%{(son_fiyat/ma200_son-1)*100:+.1f}) — uzun vadeli trend sağlam."
        r200 = "#10B981"
    else:
        d200 = f"Fiyat MA200'ün ALTINDA (%{(son_fiyat/ma200_son-1)*100:+.1f}) — uzun vadeli trend zayıf, dikkat."
        r200 = "#EF4444"
    maddeler.append({"baslik": "MA200 (turuncu çizgi)",
        "nedir": "Son 200 günün ortalama kapanışı. Piyasanın UZUN vadeli ana yönü. Üstündeyse 'boğa', altındaysa 'ayı' tarafı.",
        "durum": d200, "renk": r200})

    olaylar = _kesisim_bul(ma50, ma200)
    son_kesisim = olaylar[-1] if olaylar else None
    if son_kesisim:
        gun_once = len(df) - 1 - son_kesisim["indeks"]
        if son_kesisim["tip"] == "altin":
            dk = f"En son ALTIN KESİŞİM oldu ({gun_once} gün önce). MA50, MA200'ü yukarı kesti — yapısal yükseliş işareti."
            rk = "#10B981"
        else:
            dk = f"En son ÖLÜM KESİŞİMİ oldu ({gun_once} gün önce). MA50, MA200'ü aşağı kesti — yapısal zayıflık işareti."
            rk = "#EF4444"
    else:
        dk = "Son dönemde MA50/MA200 kesişimi yok — iki ortalama henüz kesişmedi."
        rk = "#94A3B8"
    maddeler.append({"baslik": "Altın / Ölüm Kesişimi (yıldız işaretleri)",
        "nedir": ("ALTIN KESİŞİM: MA50, MA200'ü aşağıdan yukarı keser → yükseliş başlangıcı sayılır. "
                  "ÖLÜM KESİŞİMİ: tam tersi → düşüş başlangıcı sayılır. Grafikte yıldızla işaretlenir."),
        "durum": dk, "renk": rk})

    maddeler.append({"baslik": "Projektör (sağ uçtaki huni)",
        "nedir": ("Önümüzdeki günlerin OLASI fiyat aralığı. Yön TAHMİN ETMEZ (ortası düz gider). "
                  "Sadece 'nereye kadar çıkabilir / nereye kadar düşebilir' belirsizliğini gösterir. Huni genişse oynaklık yüksek."),
        "durum": "Aşağıdaki yakın-plan projektör panelinde 5 günlük bant ve stop'a değme olasılığı var.",
        "renk": "#38BDF8"})

    if son_fiyat > ma50_son > ma200_son:
        ozet = "Fiyat her iki ortalamanın da üstünde ve MA50 > MA200 — teknik tablo güçlü/pozitif."
    elif son_fiyat < ma50_son < ma200_son:
        ozet = "Fiyat her iki ortalamanın da altında ve MA50 < MA200 — teknik tablo zayıf/negatif."
    else:
        ozet = "Karışık tablo — fiyat ortalamalar arasında, net trend yok. Temkinli izle."
    return {"maddeler": maddeler, "son_kesisim": son_kesisim, "ozet": ozet}


# ══════════════════════════════════════════════════════════════
# AJAN 2 — KAÇINILACAK HİSSE
# ══════════════════════════════════════════════════════════════
def kacinilacak_mi(df):
    if df is None or len(df) < 60:
        return {"tehlike_skoru": 0, "karar": "VERİ YOK", "renk": "#94A3B8",
                "bayraklar": [], "aciklama": "Yeterli geçmiş veri yok."}
    close = df["Close"]
    son_fiyat = _son(close)
    getiri = close.pct_change().dropna()
    ma50 = _ma(close, 50); ma200 = _ma(close, 200)
    ma50_son = _son(ma50, son_fiyat); ma200_son = _son(ma200, son_fiyat)
    bayraklar = []; skor = 0

    if ma50_son < ma200_son:
        skor += 30
        bayraklar.append(("Ölüm kesişimi bölgesi", "MA50, MA200'ün altında — yapısal düşüş trendi."))
    if son_fiyat < ma200_son:
        skor += 20
        bayraklar.append(("Uzun vade kırık", "Fiyat MA200'ün altında — ana trend ayı tarafında."))
    olaylar = _kesisim_bul(ma50, ma200)
    if olaylar and olaylar[-1]["tip"] == "olum":
        gun_once = len(df) - 1 - olaylar[-1]["indeks"]
        if gun_once <= 20:
            skor += 15
            bayraklar.append(("Taze ölüm kesişimi", f"{gun_once} gün önce ölüm kesişimi — bozulma yeni."))
    neg = getiri[getiri < 0]
    asagi_vol = float(neg.std() * 100) if len(neg) > 5 else 0.0
    if asagi_vol > 3.5:
        skor += 15
        bayraklar.append(("Yüksek düşüş oynaklığı", f"Düşüş günlerinde ~%{asagi_vol:.1f} oynaklık — sert kayıp riski."))
    if len(close) >= 22:
        aylik = (son_fiyat / float(close.iloc[-22]) - 1) * 100
        if aylik < -8:
            skor += 20
            bayraklar.append(("Negatif momentum", f"Son 1 ayda %{aylik:.1f} — düşüş ivmesi var."))

    skor = int(min(100, skor))
    if skor >= 60:
        karar, renk = "KAÇIN — buradan düşüş normal karşılanır", "#EF4444"
    elif skor >= 30:
        karar, renk = "DİKKATLİ — zayıflık işaretleri var", "#F59E0B"
    else:
        karar, renk = "TEKNİK TABLO TEMİZ — bariz düşüş sinyali yok", "#10B981"
    aciklama = ("Bu skor 'kesin düşer' demez. Geçmiş örüntüye göre buradan AŞAĞI hareketin ne kadar "
                "'normal/beklenir' olduğunu söyler. Yüksek skor = aşağı risk yüksek.")
    return {"tehlike_skoru": skor, "karar": karar, "renk": renk,
            "bayraklar": bayraklar, "asagi_vol": round(asagi_vol, 2), "aciklama": aciklama}


# ══════════════════════════════════════════════════════════════
# AJAN 3 — PROJEKTÖR (Monte Carlo, yönsüz)
# ══════════════════════════════════════════════════════════════
def projektor(df, gun=5, stop_fiyat=None, yol_sayisi=4000, tohum=42):
    if df is None or len(df) < 30:
        return {"band": [], "stop_olasilik": None, "gunluk_vol_pct": 0.0, "son_fiyat": None}
    close = df["Close"]
    son_fiyat = _son(close)
    log_get = np.log(close / close.shift(1)).dropna()
    sigma = float(log_get.std())
    if np.isnan(sigma) or sigma <= 0:
        sigma = 0.02
    band = []
    for t in range(1, gun + 1):
        s = sigma * np.sqrt(t)
        band.append({"gun": t,
            "alt80": son_fiyat * np.exp(-1.282 * s), "alt50": son_fiyat * np.exp(-0.674 * s),
            "orta": son_fiyat,
            "ust50": son_fiyat * np.exp(+0.674 * s), "ust80": son_fiyat * np.exp(+1.282 * s)})
    stop_olasilik = None
    if stop_fiyat is not None and stop_fiyat > 0 and stop_fiyat < son_fiyat:
        rng = np.random.default_rng(tohum)
        adimlar = rng.normal(loc=-0.5 * sigma**2, scale=sigma, size=(yol_sayisi, gun))
        yollar = son_fiyat * np.exp(np.cumsum(adimlar, axis=1))
        stop_olasilik = round(float((yollar.min(axis=1) <= stop_fiyat).mean()) * 100, 1)
    return {"band": band, "stop_olasilik": stop_olasilik,
            "gunluk_vol_pct": round(sigma * 100, 2), "son_fiyat": son_fiyat}


# ══════════════════════════════════════════════════════════════
# AJAN 4 — RİSK PARITY
# ══════════════════════════════════════════════════════════════
def risk_parity(adaylar, toplam_risk_butcesi_tl):
    gecerli = []
    for a in adaylar:
        f = a.get("fiyat", 0); s = a.get("stop", 0)
        if f > 0 and 0 < s < f:
            gecerli.append({**a, "_risk_pay": f - s})
    if not gecerli or toplam_risk_butcesi_tl <= 0:
        return []
    pozisyon_basi_risk = toplam_risk_butcesi_tl / len(gecerli)
    cikti = []
    for a in gecerli:
        lot = max(0, int(pozisyon_basi_risk / a["_risk_pay"]))
        cikti.append({"kod": a.get("kod", "?"), "lot": lot, "fiyat": a["fiyat"], "stop": a["stop"],
            "pozisyon_tl": round(lot * a["fiyat"], 2), "risk_tl": round(lot * a["_risk_pay"], 2),
            "hisse_basi_risk": round(a["_risk_pay"], 4)})
    return cikti


# ══════════════════════════════════════════════════════════════
# GÖRSEL 1 — ANA GRAFİK (fiyat + MA50/MA200 + yıldız + sağ uç koni)
# ══════════════════════════════════════════════════════════════
def panel_ciz(df, stop_fiyat=None, goster_gun=252, ileri_gun=5):
    if df is None or len(df) < 60:
        return None
    close = df["Close"]
    ma50 = close.rolling(50).mean(); ma200 = close.rolling(200).mean()
    n = len(df); bas = max(0, n - goster_gun)
    t = np.arange(bas, n)
    fig, ax = plt.subplots(figsize=(9, 3.6))
    fig.patch.set_facecolor("#0D1117"); ax.set_facecolor("#0D1117")
    c = close.values[bas:]
    renk = "#10B981" if c[-1] >= c[0] else "#EF4444"
    ax.plot(t, c, color=renk, linewidth=1.6, label="Fiyat", zorder=3)
    ax.plot(t, ma50.values[bas:], color="#38BDF8", linewidth=1.1, label="MA50", zorder=2)
    ax.plot(t, ma200.values[bas:], color="#F59E0B", linewidth=1.1, label="MA200", zorder=2)
    for o in _kesisim_bul(ma50, ma200):
        i = o["indeks"]
        if i >= bas:
            yr = "#10B981" if o["tip"] == "altin" else "#EF4444"
            ax.scatter([i], [close.values[i]], s=160, marker="*", color=yr,
                       edgecolors="white", linewidths=1.2, zorder=6)
    p = projektor(df, gun=ileri_gun, stop_fiyat=stop_fiyat)
    if p["band"]:
        sf = p["son_fiyat"]; fx = [n-1] + [n-1+b["gun"] for b in p["band"]]
        ax.fill_between(fx, [sf]+[b["alt80"] for b in p["band"]], [sf]+[b["ust80"] for b in p["band"]],
                        color="#38BDF8", alpha=0.12, zorder=1)
        ax.fill_between(fx, [sf]+[b["alt50"] for b in p["band"]], [sf]+[b["ust50"] for b in p["band"]],
                        color="#38BDF8", alpha=0.20, zorder=1)
        ax.plot(fx, [sf]+[b["orta"] for b in p["band"]], color="#94A3B8",
                linewidth=1.0, linestyle="--", zorder=2)
        ax.axvline(n-1, color="#475569", linewidth=0.7, linestyle=":", zorder=1)
        if stop_fiyat:
            ax.axhline(stop_fiyat, color="#EF4444", linewidth=0.8, linestyle="--", alpha=0.7, zorder=1)
    ax.legend(loc="upper left", fontsize=7, facecolor="#0D1117", edgecolor="#1E293B", labelcolor="#94A3B8")
    ax.tick_params(colors="#475569", labelsize=7)
    for s in ax.spines.values(): s.set_edgecolor("#1E293B")
    ax.grid(axis="y", color="#1E293B", linewidth=0.5, alpha=0.5); ax.set_xticks([])
    plt.tight_layout(pad=0.4)
    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=110, facecolor="#0D1117", bbox_inches="tight")
    plt.close(); buf.seek(0); return buf


# ══════════════════════════════════════════════════════════════
# GÖRSEL 2 — YAKIN PLAN PROJEKTÖR (son 30 gün + 5 gün ileri büyük huni)
# ══════════════════════════════════════════════════════════════
def projektor_ciz(df, stop_fiyat=None, gecmis_gun=30, ileri_gun=5):
    if df is None or len(df) < 40:
        return None
    close = df["Close"]; n = len(df); bas = max(0, n - gecmis_gun)
    t = np.arange(bas, n)
    fig, ax = plt.subplots(figsize=(9, 3.4))
    fig.patch.set_facecolor("#0D1117"); ax.set_facecolor("#0D1117")
    ax.plot(t, close.values[bas:], color="#E2E8F0", linewidth=1.8, zorder=4, label="Fiyat (son 30g)")
    p = projektor(df, gun=ileri_gun, stop_fiyat=stop_fiyat)
    if p["band"]:
        sf = p["son_fiyat"]; fx = [n-1] + [n-1+b["gun"] for b in p["band"]]
        ax.fill_between(fx, [sf]+[b["alt80"] for b in p["band"]], [sf]+[b["ust80"] for b in p["band"]],
                        color="#38BDF8", alpha=0.15, label="%80 olası bant")
        ax.fill_between(fx, [sf]+[b["alt50"] for b in p["band"]], [sf]+[b["ust50"] for b in p["band"]],
                        color="#38BDF8", alpha=0.28, label="%50 olası bant")
        ax.plot(fx, [sf]+[b["orta"] for b in p["band"]], color="#94A3B8",
                linewidth=1.2, linestyle="--", label="Yönsüz orta")
        ax.axvline(n-1, color="#475569", linewidth=0.8, linestyle=":")
        if stop_fiyat:
            ax.axhline(stop_fiyat, color="#EF4444", linewidth=1.0, linestyle="--",
                       alpha=0.8, label=f"Stop {stop_fiyat:.2f}")
    ax.legend(loc="upper left", fontsize=7, facecolor="#0D1117", edgecolor="#1E293B", labelcolor="#94A3B8")
    ax.tick_params(colors="#475569", labelsize=7)
    for s in ax.spines.values(): s.set_edgecolor("#1E293B")
    ax.grid(axis="y", color="#1E293B", linewidth=0.5, alpha=0.5); ax.set_xticks([])
    plt.tight_layout(pad=0.4)
    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=110, facecolor="#0D1117", bbox_inches="tight")
    plt.close(); buf.seek(0); return buf


# ══════════════════════════════════════════════════════════════
# TEK ÇAĞRI — STREAMLIT PANELİ
# app.py'de hisse detayında: ajanlar.panel_goster(st, df, stop_fiyat=stop, kod=kod)
# ══════════════════════════════════════════════════════════════
def panel_goster(st, df, stop_fiyat=None, kod=""):
    if df is None or len(df) < 60:
        st.info("Bu hisse için grafik öğretmeni yeterli veri bulamadı (60+ gün gerekli).")
        return
    g = grafik_ogretmen(df)
    k = kacinilacak_mi(df)
    p = projektor(df, gun=5, stop_fiyat=stop_fiyat)

    # 1) Ana grafik
    buf = panel_ciz(df, stop_fiyat=stop_fiyat)
    if buf:
        st.image(buf, use_container_width=True)
    st.caption("🟢 Fiyat · 🔵 MA50 · 🟠 MA200 · ⭐ kesişim · sağ uç = projektör konisi")

    # 2) Tek cümle özet
    st.markdown(f"**Özet:** {g['ozet']}")

    # 3) Grafik Öğretmen — her baktığında açıklama (açılır panel)
    with st.expander("📘 Bu grafikte ne görüyorum? (her öğenin anlamı)", expanded=False):
        for m in g["maddeler"]:
            st.markdown(f"<div style='border-left:3px solid {m['renk']};padding-left:10px;margin-bottom:10px'>"
                        f"<b style='color:{m['renk']}'>{m['baslik']}</b><br>"
                        f"<span style='color:#94A3B8;font-size:0.85rem'>{m['nedir']}</span><br>"
                        f"<span style='font-size:0.85rem'>📍 {m['durum']}</span></div>",
                        unsafe_allow_html=True)

    # 4) Kaçınılacak mı? (tersinden risk)
    st.markdown(f"<div style='background:{k['renk']}18;border:1px solid {k['renk']}55;border-radius:10px;"
                f"padding:12px 14px;margin:8px 0'>"
                f"<div style='color:{k['renk']};font-weight:800;font-size:0.85rem'>⚠️ DÜŞÜŞ RİSKİ: "
                f"{k['tehlike_skoru']}/100 — {k['karar']}</div>", unsafe_allow_html=True)
    for ad, ac in k["bayraklar"]:
        st.markdown(f"<div style='color:#94A3B8;font-size:0.8rem;padding-left:6px'>• <b>{ad}:</b> {ac}</div>",
                    unsafe_allow_html=True)
    st.markdown(f"<div style='color:#64748B;font-size:0.74rem;margin-top:6px'>{k['aciklama']}</div></div>",
                unsafe_allow_html=True)

    # 5) Yakın plan projektör
    st.markdown("**🔭 Projektör — önümüzdeki 5 gün (yön değil, belirsizlik genişliği)**")
    buf2 = projektor_ciz(df, stop_fiyat=stop_fiyat)
    if buf2:
        st.image(buf2, use_container_width=True)
    sat = f"Günlük oynaklık ~%{p['gunluk_vol_pct']}."
    if p["stop_olasilik"] is not None:
        sat += f" Stop'a değme olasılığı (5 gün): **%{p['stop_olasilik']}**."
    st.caption(sat)


# ══════════════════════════════════════════════════════════════
# KENDİ KENDİNE TEST  (python ajanlar.py)
# ══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    rng = np.random.default_rng(3)
    n = 400
    trend = np.concatenate([np.linspace(0, -0.4, 200), np.linspace(-0.4, 0.2, 200)])
    kapanis = 100 * np.exp(trend + np.cumsum(rng.normal(0, 0.015, n)) * 0.3)
    idx = pd.date_range("2024-01-01", periods=n, freq="D")
    df = pd.DataFrame({"Open": kapanis, "High": kapanis*1.01, "Low": kapanis*0.99,
                       "Close": kapanis, "Volume": rng.integers(1e6, 5e6, n)}, index=idx)
    son = float(df["Close"].iloc[-1]); stop = son*0.95
    print("Öğretmen:", grafik_ogretmen(df)["ozet"])
    print("Kaçınılacak:", kacinilacak_mi(df)["karar"])
    pp = projektor(df, gun=5, stop_fiyat=stop)
    print(f"Projektör: vol %{pp['gunluk_vol_pct']} | stop'a değme %{pp['stop_olasilik']}")
    assert panel_ciz(df, stop) is not None
    assert projektor_ciz(df, stop) is not None
    print("✓ panel_ciz ve projektor_ciz PNG üretti — hepsi çalışıyor.")
