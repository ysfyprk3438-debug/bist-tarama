"""
═══════════════════════════════════════════════════════════════
APEX · REJİM TAHSİSİ BACKTEST  (v7 — HİSSE mi MEVDUAT mı, NE ZAMAN?)
═══════════════════════════════════════════════════════════════
Cross-sectional audit'in keşfi: son ~3.6 yılda MEVDUAT her şeyi yendi —
stratejiler bir yana, BORSANIN KENDİSİ bile (%45 faiz > %35 endeks).
Ama o pencere yüksek-faiz dönemi; 2020-21 borsa patlamasını görmüyor.

ASIL SORU artık "hangi hisse?" değil: "HİSSE mi MEVDUAT mı, NE ZAMAN?"
Edge muhtemelen REJİM TAHSİSİNDE: faiz cezalandırıcı + borsa zayıfken
mevduatta otur; döngü borsaya dönünce gir.

TEST (tam döngüde, en uzun veri):
  • REJİM ANAHTARI : XU100 > MA200 → endeks, değilse mevduat (takvim-doğru faiz)
  • Momentum top-N · Hibrit Sinyal top-N  (full-cycle kıyas)
  • Çıtalar: sabit XU100 al-tut · eşit-ağırlık · sabit mevduat
Soru: Rejim anahtarı HEM mevduatı HEM endeksi geçiyor mu? Leakage yok.
"""

import datetime, traceback
import numpy as np
import pandas as pd

N_HOLD     = 12
REBAL_GUN  = 21
BASLANGIC  = 210         # MA200 + momentum ısınması
MOM_LB     = 126
MA_REJIM   = 200
FETCH_GUN  = 3000        # tam döngü hedefi (~8 yıl; veri_al elindekini döndürür)


def _yillik(nav, gun):
    if gun <= 0 or nav <= 0: return -100.0
    return ((nav) ** (365.0 / gun) - 1) * 100


def _sharpe_mdd(nav_seri, mevduat_gunluk):
    r = nav_seri.pct_change().dropna()
    if len(r) < 5: return 0.0, 0.0
    ex = r - mevduat_gunluk
    sd = ex.std()
    sharpe = (ex.mean() / sd * np.sqrt(252)) if sd > 0 else 0.0
    huzme = nav_seri / nav_seri.cummax() - 1.0
    return float(sharpe), float(huzme.min() * 100)


def _devir_maliyet(eski, yeni, fr):
    syms = set(eski) | set(yeni)
    return fr * sum(abs(yeni.get(s, 0.0) - eski.get(s, 0.0)) for s in syms)


def _topn(skor_seri, n):
    s = skor_seri.dropna(); s = s[np.isfinite(s)]
    if len(s) == 0: return []
    return list(s.sort_values(ascending=False).head(n).index)


def portfoy_backtest(panel, xu, skorla, n_hold, rebal, baslangic, fr):
    dates = panel.index; n = len(dates)
    nav = 1.0; navs = [1.0]; out = [dates[baslangic]]
    holdings = {}; sayac = []
    for t in range(baslangic, n - 1):
        if (t - baslangic) % rebal == 0:
            picks = _topn(skorla(t), n_hold)
            sayac.append(len(picks))
            yeni = {s: 1.0 / n_hold for s in picks}
            nav *= (1 - _devir_maliyet(holdings, yeni, fr)); holdings = yeni
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
        nav *= (1 + r); navs.append(nav); out.append(dates[t + 1])
    return pd.Series(navs, index=out), (float(np.mean(sayac)) if sayac else 0.0)


def rejim_backtest(xu, dates, ma_window, fr, mevduat_yillik, baslangic):
    """XU100 > MA(ma_window) → endekste; değilse mevduatta (takvim-günü doğru faiz)."""
    ma = xu.rolling(ma_window).mean()
    n = len(xu)
    nav = 1.0; navs = [1.0]; out = [dates[baslangic]]
    in_eq = False; gecis = 0; eq_gun = 0
    for t in range(baslangic, n - 1):
        istek = bool(np.isfinite(ma.iat[t]) and xu.iat[t] > ma.iat[t])
        if istek != in_eq:
            nav *= (1 - fr); gecis += 1; in_eq = istek
        gap = max((dates[t + 1] - dates[t]).days, 1)
        if in_eq:
            p0 = xu.iat[t]; p1 = xu.iat[t + 1]
            r = (p1 / p0 - 1.0) if (p0 > 0 and np.isfinite(p0) and np.isfinite(p1)) else 0.0
            eq_gun += 1
        else:
            r = (1 + mevduat_yillik) ** (gap / 365.0) - 1.0
        nav *= (1 + r); navs.append(nav); out.append(dates[t + 1])
    pay = eq_gun / max(1, (n - 1 - baslangic))
    return pd.Series(navs, index=out), gecis, pay


def mevduat_nav(dates, mevduat_yillik, baslangic, son_idx):
    nav = 1.0
    for t in range(baslangic, son_idx):
        gap = max((dates[t + 1] - dates[t]).days, 1)
        nav *= (1 + mevduat_yillik) ** (gap / 365.0)
    return nav


def calistir():
    from veri import veri_al, VADE_AYAR
    from backtest import _FR, MEVDUAT_YILLIK, _MEVDUAT_GUNLUK
    from tarama_core import BIST_TUM, KOD_SEKTOR
    from hibrit_analiz import analiz_et as hibrit

    ayar = VADE_AYAR["gunluk"]
    kodlar = list(dict.fromkeys(BIST_TUM))

    xu_df, _ = veri_al("XU100", gun=FETCH_GUN, min_gun=300, aralik="1d")
    if xu_df is None or len(xu_df) < BASLANGIC + 60:
        print("XU100 verisi yok — durdu."); return
    takvim = xu_df.index
    xu = xu_df["Close"].reindex(takvim).ffill()
    n = len(takvim); son_idx = n - 1

    paneller = {}; seriler = {}
    for kod in kodlar:
        try:
            df, _ = veri_al(kod, gun=FETCH_GUN, min_gun=300, aralik="1d")
            if df is None or len(df) < BASLANGIC + 60: continue
            paneller[kod] = df; seriler[kod] = df["Close"].reindex(takvim).ffill()
        except Exception as e:
            print(f"  {kod}: {e}")
    panel = pd.DataFrame(seriler)
    gecerli = [k for k in paneller if k in panel.columns]
    toplam_gun = (takvim[son_idx] - takvim[BASLANGIC]).days
    yil = toplam_gun / 365.0
    print(f"Panel: {len(gecerli)} hisse × {n} gün · {yil:.1f} yıl")

    def skor_momentum(t):
        if t - MOM_LB < 0: return pd.Series(dtype=float)
        return (panel.iloc[t] / panel.iloc[t - MOM_LB] - 1.0)

    def skor_sinyal(t):
        tarih = takvim[t]; xs = xu.loc[:tarih]; out = {}
        for kod in gecerli:
            sdf = paneller[kod].loc[:tarih]
            if len(sdf) < 60: continue
            try:
                r = hibrit(kod, sdf, ayar, 100000, 1.0, KOD_SEKTOR.get(kod, "Diğer"),
                           detayli=False, backtest=True, endeks_close=xs)
                if r and r.get("puan") is not None: out[kod] = float(r["puan"])
            except Exception: pass
        return pd.Series(out, dtype=float)

    sonuc = {}
    # REJİM ANAHTARI
    print("\n=== Rejim Anahtarı (XU100 vs MA200) ===")
    rej_seri, gecis, eq_pay = rejim_backtest(xu, takvim, MA_REJIM, _FR, MEVDUAT_YILLIK, BASLANGIC)
    rs = float(rej_seri.iloc[-1]); rsh, rmdd = _sharpe_mdd(rej_seri, _MEVDUAT_GUNLUK)
    sonuc["Rejim Anahtarı (MA200)"] = {"nav": rs, "yillik": _yillik(rs, toplam_gun),
        "sharpe": rsh, "mdd": rmdd, "ek": f"{gecis} geçiş · %{eq_pay*100:.0f} hissede"}
    print(f"  NAV={rs:.3f} yıllık={sonuc['Rejim Anahtarı (MA200)']['yillik']:.1f}% "
          f"Sharpe={rsh:.2f} mdd={rmdd:.1f}% geçiş={gecis} eq%={eq_pay*100:.0f}")

    # SEÇİM STRATEJİLERİ
    for ad, fn in [("Momentum (top-N)", skor_momentum), ("Hibrit Sinyal (top-N)", skor_sinyal)]:
        print(f"\n=== {ad} ===")
        try:
            ns, osin = portfoy_backtest(panel, xu, fn, N_HOLD, REBAL_GUN, BASLANGIC, _FR)
            son = float(ns.iloc[-1]); sh, mdd = _sharpe_mdd(ns, _MEVDUAT_GUNLUK)
            sonuc[ad] = {"nav": son, "yillik": _yillik(son, toplam_gun), "sharpe": sh,
                         "mdd": mdd, "ek": f"ort {osin:.1f} sinyal" if "Sinyal" in ad else ""}
            print(f"  NAV={son:.3f} yıllık={sonuc[ad]['yillik']:.1f}% Sharpe={sh:.2f} mdd={mdd:.1f}%")
        except Exception as e:
            print(f"  HATA {ad}: {e}"); traceback.print_exc()

    # ÇITALAR
    xb = float(xu.iloc[BASLANGIC]); xsf = float(xu.iloc[son_idx])
    xu_nav = (xsf * (1 - _FR)) / (xb * (1 + _FR)) if xb > 0 else 1.0
    xu_seri = xu.iloc[BASLANGIC:] / xb
    xu_sh, xu_mdd = _sharpe_mdd(xu_seri, _MEVDUAT_GUNLUK)
    ew = [(panel[k].iloc[son_idx] * (1 - _FR)) / (panel[k].iloc[BASLANGIC] * (1 + _FR))
          for k in gecerli if panel[k].iloc[BASLANGIC] > 0 and np.isfinite(panel[k].iloc[son_idx])]
    ew_nav = float(np.mean(ew)) if ew else 1.0
    mev_nav = mevduat_nav(takvim, MEVDUAT_YILLIK, BASLANGIC, son_idx)

    # RAPOR
    L = []
    L.append("# APEX — Rejim Tahsisi Audit · Hisse mi Mevduat mı, Ne Zaman?")
    L.append("")
    L.append(f"_Üretim: {datetime.datetime.now():%Y-%m-%d %H:%M} · {len(gecerli)} hisse · {yil:.1f} yıl · "
             f"maliyet: komisyon+slippage · mevduat takvim-doğru · leakage yok_")
    L.append("")
    L.append("## Soru: Rejim anahtarı HEM mevduatı HEM endeksi geçiyor mu?")
    L.append("")
    L.append("| Strateji | Son NAV (×) | Getiri% | Yıllık% | Sharpe | MaxDD% | Mevduatı geçti? | Endeksi geçti? |")
    L.append("|---|---:|---:|---:|---:|---:|:--:|:--:|")

    def satir(ad, nav, yillik, sh, mdd):
        mg = "✅" if nav > mev_nav else "❌"
        eg = "✅" if nav > xu_nav else "❌"
        return (f"| {ad} | {nav:.2f} | {(nav-1)*100:.1f} | {yillik:.1f} | "
                f"{sh if sh is not None else '—'} | {mdd if mdd is not None else '—'} | {mg} | {eg} |")

    for ad in ["Rejim Anahtarı (MA200)", "Momentum (top-N)", "Hibrit Sinyal (top-N)"]:
        if ad in sonuc:
            d = sonuc[ad]
            L.append(satir(ad, d["nav"], d["yillik"], f"{d['sharpe']:.2f}", f"{d['mdd']:.1f}"))
    L.append(f"| _XU100 al-tut_ | {xu_nav:.2f} | {(xu_nav-1)*100:.1f} | {_yillik(xu_nav,toplam_gun):.1f} | "
             f"{xu_sh:.2f} | {xu_mdd:.1f} | {'✅' if xu_nav>mev_nav else '❌'} | — |")
    L.append(f"| _Eşit-ağırlık TÜM_ | {ew_nav:.2f} | {(ew_nav-1)*100:.1f} | {_yillik(ew_nav,toplam_gun):.1f} | "
             f"— | — | {'✅' if ew_nav>mev_nav else '❌'} | {'✅' if ew_nav>xu_nav else '❌'} |")
    L.append(f"| _Mevduat (~%{int(MEVDUAT_YILLIK*100)})_ | {mev_nav:.2f} | {(mev_nav-1)*100:.1f} | "
             f"{int(MEVDUAT_YILLIK*100)}.0 | — | — | — | {'✅' if mev_nav>xu_nav else '❌'} |")
    L.append("")

    # KARAR
    rej = sonuc.get("Rejim Anahtarı (MA200)", {})
    rej_nav = rej.get("nav", 0)
    L.append("## Karar")
    L.append("")
    if rej_nav > mev_nav and rej_nav > xu_nav:
        L.append(f"**Rejim anahtarı HEM mevduatı HEM endeksi geçti** (NAV {rej_nav:.2f} > mevduat {mev_nav:.2f}, "
                 f"> endeks {xu_nav:.2f}). İLK gerçek edge adayı: ne zaman hissede/ne zaman mevduatta olunacağını "
                 f"basit bir rejim kuralı yakalıyor. Sonraki: out-of-sample (dönemi ikiye böl), MA penceresi "
                 f"duyarlılığı (100/150/200), ve faizi sabit değil gerçek-zamanlı besle.")
    elif rej_nav > mev_nav:
        L.append(f"**Rejim anahtarı mevduatı geçti ama endeksi geçemedi** (NAV {rej_nav:.2f}). Borsanın iyi olduğu "
                 f"dönemde anahtar geç kalıyor/yanlış çıkıyor. Yön doğru (mevduat tabanını aştı); kural rafine "
                 f"edilmeli: daha hızlı sinyal ya da kısmi tahsis (hep ya hep-yok yerine).")
    else:
        L.append(f"**Rejim anahtarı mevduatı bile geçemedi** (NAV {rej_nav:.2f} < mevduat {mev_nav:.2f}). Bu basit "
                 f"MA kuralı edge üretmiyor. Ama tabloda asıl mesaj: bu dönemde sabit mevduat çoğu şeyi yeniyorsa, "
                 f"dürüst ürün 'çoğunlukla mevduat, seçili fırsatta hisse' olabilir — ya da farklı rejim sinyali "
                 f"(faiz yönü, enflasyon, breadth) gerekiyor.")
    L.append("")
    L.append(f"> Rejim: {rej.get('ek','')}. MA{MA_REJIM} penceresi. Geçişte tek-yön sürtünme.")
    L.append("")
    L.append("---")
    L.append("*Mevduat takvim-günü doğru bileşik (hafta sonu dahil). Skor/karar t kapanışında, getiri t+1 — leakage yok.*")

    metin = "\n".join(L)
    with open("BACKTEST_SONUC.md", "w", encoding="utf-8") as f:
        f.write(metin)
    print("\n" + metin)
    print("\n>>> BACKTEST_SONUC.md yazıldı.")


if __name__ == "__main__":
    calistir()
