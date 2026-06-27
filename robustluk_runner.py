"""
APEX · MOMENTUM STRES TESTİ (v7.1 — kazananı doğrula)
Tam döngüde (7.4yıl) momentum mevduatı+endeksi geçti (Sharpe 0.83). Ama in-sample.
SORU 1 (OOS): dönemi İKİYE böl. Momentum SON yarıda (yüksek-faiz) da kazanıyor mu,
              yoksa sadece eski boom'da mı? Gerçek edge HER İKİ yarıda kazanır.
SORU 2 (parametre): 126/12/21 şanslı mı? lookback×N taraması — çoğu ayarda kazanmalı.
SORU 3 (beceri mi maruziyet mi): momentum, eşit-ağırlığı (sadece 'hissede ol') geçiyor mu?
Hızlı: sadece fiyat paneli, sinyal çağrısı yok.
"""
import datetime
import numpy as np, pandas as pd

BASLANGIC = 260
FETCH_GUN = 3000
LB_LISTE  = [63, 126, 189, 252]
N_LISTE   = [8, 12, 16]
REBAL     = 21


def _devir(eski, yeni, fr):
    syms = set(eski) | set(yeni)
    return fr * sum(abs(yeni.get(s, 0.0) - eski.get(s, 0.0)) for s in syms)


def momentum_nav(panel, xu, lookback, N, rebal, fr, lo, hi):
    nav = 1.0; navs = [1.0]; holdings = {}
    for t in range(lo, hi):
        if (t - lo) % rebal == 0:
            if t - lookback >= 0:
                sc = (panel.iloc[t] / panel.iloc[t - lookback] - 1.0)
                sc = sc.replace([np.inf, -np.inf], np.nan).dropna()
                picks = list(sc.sort_values(ascending=False).head(N).index)
            else:
                picks = []
            yeni = {s: 1.0 / N for s in picks}
            nav *= (1 - _devir(holdings, yeni, fr)); holdings = yeni
        r = 0.0; wsum = 0.0
        for s, w in holdings.items():
            p0 = panel[s].iat[t]; p1 = panel[s].iat[t + 1]
            if p0 > 0 and np.isfinite(p0) and np.isfinite(p1):
                r += w * (p1 / p0 - 1.0); wsum += w
        wrem = 1.0 - wsum
        if wrem > 1e-9:
            i0 = xu.iat[t]; i1 = xu.iat[t + 1]
            if i0 > 0 and np.isfinite(i0) and np.isfinite(i1):
                r += wrem * (i1 / i0 - 1.0)
        nav *= (1 + r); navs.append(nav)
    huzme = pd.Series(navs); mdd = float((huzme / huzme.cummax() - 1).min() * 100)
    return nav, mdd


def ew_nav(panel, cols, fr, lo, hi):
    v = [(panel[k].iat[hi] * (1 - fr)) / (panel[k].iat[lo] * (1 + fr))
         for k in cols if panel[k].iat[lo] > 0 and np.isfinite(panel[k].iat[hi])]
    return float(np.mean(v)) if v else 1.0


def dep_nav(dates, mev, lo, hi):
    nav = 1.0
    for t in range(lo, hi):
        nav *= (1 + mev) ** (max((dates[t + 1] - dates[t]).days, 1) / 365.0)
    return nav


def idx_nav(xu, fr, lo, hi):
    xb = xu.iat[lo]; xs = xu.iat[hi]
    return (xs * (1 - fr)) / (xb * (1 + fr)) if xb > 0 else 1.0


def calistir():
    from veri import veri_al
    from backtest import _FR, MEVDUAT_YILLIK
    from tarama_core import BIST_TUM

    xu_df, _ = veri_al("XU100", gun=FETCH_GUN, min_gun=300, aralik="1d")
    if xu_df is None or len(xu_df) < BASLANGIC + 200:
        print("XU100 yok — durdu."); return
    dates = xu_df.index; xu = xu_df["Close"].reindex(dates).ffill()
    n = len(dates); son = n - 1; orta = (BASLANGIC + son) // 2

    seriler = {}
    for kod in dict.fromkeys(BIST_TUM):
        try:
            df, _ = veri_al(kod, gun=FETCH_GUN, min_gun=300, aralik="1d")
            if df is not None and len(df) >= BASLANGIC + 200:
                seriler[kod] = df["Close"].reindex(dates).ffill()
        except Exception:
            pass
    panel = pd.DataFrame(seriler); cols = list(panel.columns)
    yil = (dates[son] - dates[BASLANGIC]).days / 365.0
    yil_is = (dates[orta] - dates[BASLANGIC]).days / 365.0
    yil_oos = (dates[son] - dates[orta]).days / 365.0
    print(f"{len(cols)} hisse · {yil:.1f}yıl · IS {yil_is:.1f}y / OOS {yil_oos:.1f}y")

    L = ["# APEX — Momentum Stres Testi (OOS + parametre + beceri)", "",
         f"_{datetime.datetime.now():%Y-%m-%d %H:%M} · {len(cols)} hisse · {yil:.1f} yıl_", ""]

    # ── OOS: momentum(base) vs EW vs çıtalar, İKİ yarı ──
    L.append("## 1) Out-of-Sample — momentum SON yarıda da kazanıyor mu?")
    L.append("")
    L.append("| Dönem | Momentum | Eşit-ağırlık | Mevduat | Endeks | Mom>hepsi? |")
    L.append("|---|---:|---:|---:|---:|:--:|")
    oos_ok = True
    for ad, lo, hi in [("İlk yarı (IS)", BASLANGIC, orta), ("İkinci yarı (OOS)", orta, son),
                       ("TÜM dönem", BASLANGIC, son)]:
        m, _ = momentum_nav(panel, xu, 126, 12, REBAL, _FR, lo, hi)
        e = ew_nav(panel, cols, _FR, lo, hi)
        d = dep_nav(dates, MEVDUAT_YILLIK, lo, hi)
        ix = idx_nav(xu, _FR, lo, hi)
        kazandi = m > d and m > ix and m > e
        if "yarı" in ad and not kazandi:
            oos_ok = False
        L.append(f"| {ad} | {m:.2f} | {e:.2f} | {d:.2f} | {ix:.2f} | {'✅' if kazandi else '❌'} |")
    L.append("")

    # ── PARAMETRE TARAMASI (tüm dönem) ──
    L.append("## 2) Parametre taraması — 126/12 şanslı mı? (TÜM dönem, çita: mevduat & endeks)")
    L.append("")
    L.append("| lookback \\ N | " + " | ".join(f"N={x}" for x in N_LISTE) + " |")
    L.append("|---|" + "|".join("---:" for _ in N_LISTE) + "|")
    d_all = dep_nav(dates, MEVDUAT_YILLIK, BASLANGIC, son)
    ix_all = idx_nav(xu, _FR, BASLANGIC, son)
    kazanan_hucre = 0; toplam_hucre = 0
    for lb in LB_LISTE:
        hucreler = []
        for N in N_LISTE:
            m, mdd = momentum_nav(panel, xu, lb, N, REBAL, _FR, BASLANGIC, son)
            toplam_hucre += 1
            ok = m > d_all and m > ix_all
            if ok: kazanan_hucre += 1
            hucreler.append(f"{m:.1f} ({'✅' if ok else '❌'})")
        L.append(f"| {lb} | " + " | ".join(hucreler) + " |")
    L.append("")
    L.append(f"_Çıta: mevduat {d_all:.1f}× · endeks {ix_all:.1f}×. ✅ = ikisini de geçti._")
    L.append("")

    # ── KARAR ──
    L.append("## Karar")
    L.append("")
    oran = kazanan_hucre / max(1, toplam_hucre)
    if oos_ok and oran >= 0.7:
        L.append(f"**Momentum GERÇEK edge.** Her iki yarıda da (boom + yüksek-faiz) mevduatı, endeksi ve "
                 f"eşit-ağırlığı geçti; parametrelerin {kazanan_hucre}/{toplam_hucre}'i kazandı. Curve-fit değil, "
                 f"'sadece hissede ol' değil — seçim becerisi. Sonraki ASIL iş: −%50 drawdown'ı tolere edilebilir "
                 f"seviyeye indirmek (momentum + kısmi mevduat karışımı / volatilite hedefleme).")
    elif oos_ok:
        L.append(f"**Momentum out-of-sample tutuyor ama parametreye duyarlı** ({kazanan_hucre}/{toplam_hucre} kazandı). "
                 f"Yön sağlam; tek parametreye güvenme, geniş ayar bandında çalışanı seç.")
    elif oran >= 0.7:
        L.append(f"**Parametre-sağlam ama OOS zayıf.** Çoğu ayar tüm dönemde kazanıyor fakat ikinci yarıda (yüksek-faiz) "
                 f"momentum hepsini geçemiyor — edge boom-dönemine yaslı. Bugünkü rejimde dikkatli ol; kısmi tahsis şart.")
    else:
        L.append(f"**Momentum kırılgan.** Ne OOS ne parametre sağlam ({kazanan_hucre}/{toplam_hucre}). Tüm-dönem kazancı "
                 f"büyük ölçüde tek boom + survivorship olabilir. Forward paper-test'ten önce güvenme.")
    L.append("")
    L.append("> Uyarı: survivorship (bugün yaşayan 94 hisse) momentum'u olumlu yanlı gösterir. "
             "Kesin yargı için delist olmuş hisseler de gerek.")
    L.append("")
    L.append("---\n*Maliyet komisyon+slippage. Skor t, getiri t+1 — leakage yok. Mevduat takvim-doğru.*")

    metin = "\n".join(L)
    with open("BACKTEST_SONUC.md", "w", encoding="utf-8") as f:
        f.write(metin)
    print("\n" + metin); print("\n>>> yazıldı.")


if __name__ == "__main__":
    calistir()
