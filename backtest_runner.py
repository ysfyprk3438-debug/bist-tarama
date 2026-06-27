"""
APEX · MAKRO REJİM BACKTEST (v11) — REEL FAİZ rejim anahtarı
Hipotez: reel faiz NEGATİF (faiz<enflasyon) → hisse rejimi → endekste ol;
         reel faiz POZİTİF → mevduat rejimi → mevduata çekil.
Mevduat ZAMANA GÖRE DEĞİŞEN gerçek faizle (sabit %45 değil — dürüst düzeltme).
Histerezis (gir<-3, çık>+3) → whipsaw azalır. Point-in-time (enflasyon ~1ay gecikmeli).
Soru: makro rejim HEM zamana-göre mevduatı HEM endeksi geçiyor mu? (boom yakala + kuraklıktan kaç)
"""
import datetime
import numpy as np, pandas as pd
import makro_veri as mk

BASLANGIC = 60
FETCH_GUN = 3000
REBAL = 21
ESIK_GIR = -3.0     # reel faiz bunun altına inince hisseye gir
ESIK_CIK = 3.0      # reel faiz bunun üstüne çıkınca mevduata çık


def _mdd(navs):
    s = pd.Series(navs); return float((s / s.cummax() - 1).min() * 100)


def makro_rejim(xu, dates, lo, hi, fr):
    nav = 1.0; navs = [1.0]; in_eq = False; gecis = 0; eq = 0
    for t in range(lo, hi):
        m = mk.makro_at(dates[t])
        reel = m["reel"] if m else 5.0
        pol = m["politika"] if m else 40.0
        if (t - lo) % REBAL == 0:                  # rejim kararını ayda bir gözden geçir
            if (not in_eq) and reel < ESIK_GIR:
                in_eq = True; nav *= (1 - fr); gecis += 1
            elif in_eq and reel > ESIK_CIK:
                in_eq = False; nav *= (1 - fr); gecis += 1
        gap = max((dates[t + 1] - dates[t]).days, 1)
        if in_eq:
            p0 = xu.iat[t]; p1 = xu.iat[t + 1]
            r = (p1 / p0 - 1.0) if (p0 > 0 and np.isfinite(p0) and np.isfinite(p1)) else 0.0
            eq += 1
        else:
            r = (1 + pol / 100.0) ** (gap / 365.0) - 1.0
        nav *= (1 + r); navs.append(nav)
    return nav, gecis, eq / max(1, hi - lo), navs


def statik_mevduat(dates, lo, hi):
    """Zamana göre değişen gerçek faizle sürekli mevduat."""
    nav = 1.0
    for t in range(lo, hi):
        m = mk.makro_at(dates[t]); pol = m["politika"] if m else 40.0
        nav *= (1 + pol / 100.0) ** (max((dates[t + 1] - dates[t]).days, 1) / 365.0)
    return nav


def sabit45(dates, lo, hi):
    yil = (dates[hi] - dates[lo]).days / 365.0
    return 1.45 ** yil


def statik_endeks(xu, lo, hi, fr):
    xb = xu.iat[lo]; xs = xu.iat[hi]
    return (xs * (1 - fr)) / (xb * (1 + fr)) if xb > 0 else 1.0


def calistir():
    from veri import veri_al
    from backtest import _FR

    xu_df, _ = veri_al("XU100", gun=FETCH_GUN, min_gun=300, aralik="1d")
    if xu_df is None or len(xu_df) < BASLANGIC + 200:
        print("XU100 yok"); return
    dates = xu_df.index; xu = xu_df["Close"].reindex(dates).ffill()
    n = len(dates); son = n - 1; orta = (BASLANGIC + son) // 2
    yil = (dates[son] - dates[BASLANGIC]).days / 365.0

    L = ["# APEX — Makro Rejim Backtest (Reel Faiz Anahtarı)", "",
         f"_{datetime.datetime.now():%Y-%m-%d %H:%M} · XU100 · {yil:.1f} yıl · "
         f"mevduat ZAMANA GÖRE değişen gerçek faiz · histerezis ({ESIK_GIR}/{ESIK_CIK})_", "",
         "## Reel-faiz rejimi: boom'da hissede, kuraklıkta mevduatta?", "",
         "| Dönem | Makro Rejim | Statik Mevduat | Sabit %45 | Endeks | Rejim>mev&end? |",
         "|---|---:|---:|---:|---:|:--:|"]
    oos_ok = True
    for ad, lo, hi in [("İlk yarı (IS)", BASLANGIC, orta), ("İkinci yarı (OOS)", orta, son),
                       ("TÜM dönem", BASLANGIC, son)]:
        rn, gec, eqp, navs = makro_rejim(xu, dates, lo, hi, _FR)
        sm = statik_mevduat(dates, lo, hi)
        s45 = sabit45(dates, lo, hi)
        ix = statik_endeks(xu, lo, hi, _FR)
        gecti = rn > sm and rn > ix
        if "yarı" in ad and not gecti: oos_ok = False
        L.append(f"| {ad} | {rn:.2f} | {sm:.2f} | {s45:.2f} | {ix:.2f} | {'✅' if gecti else '❌'} |")
    rn_all, gec_all, eqp_all, navs_all = makro_rejim(xu, dates, BASLANGIC, son, _FR)
    L.append("")
    L.append(f"_Makro rejim: {gec_all} geçiş · %{eqp_all*100:.0f} zaman hissede · MaxDD %{_mdd(navs_all):.1f}_")
    L.append("")
    L.append("## Karar")
    L.append("")
    if oos_ok:
        L.append("**Makro rejim HER İKİ yarıda mevduatı+endeksi geçti.** Reel faiz işareti, boom'da hisseye "
                 "girip kuraklıkta mevduata kaçarak gerçek bir edge üretiyor — gecenin ilk OOS-sağlam sonucu. "
                 "Sonraki: hissedeyken endeks yerine temel-seçim/momentum koy (alfa üstüne alfa), eşik duyarlılığı, ileri test.")
    else:
        L.append("**Makro rejim her iki yarıda geçemedi.** Reel-faiz anahtarı tek başına yetmiyor "
                 "(geçişler geç/erken, ya da histerezis eşiği yanlış). Eşik taramasıyla rafine edilebilir; "
                 "geçemezse dürüst sonuç: bu araçlarla mevduatı yenmek bu rejimde mümkün değil, APEX'i pusula yap.")
    L.append("")
    L.append("> Mevduat artık sabit %45 değil, o dönemin gerçek faizi (2020-21'de ~%12, 2024-25'te ~%45-50). "
             "Bu, boom'da hisseyi haksız cezalandıran eski varsayımı düzeltir.")
    L.append("")
    L.append("---\n*Reel faiz = politika faizi − yıllık enflasyon (statik kaynaklı tablo). "
             "Karar t, getiri t+1; enflasyon ~1 ay gecikmeli — leakage yok.*")
    metin = "\n".join(L)
    with open("BACKTEST_SONUC.md", "w", encoding="utf-8") as f:
        f.write(metin)
    print("\n" + metin); print("\n>>> yazıldı.")


if __name__ == "__main__":
    calistir()
