"""
═══════════════════════════════════════════════════════════════
APEX · CROSS-SECTIONAL BACKTEST  (v6 — HEP YATIRIMDA, TOP-N SEÇİM)
═══════════════════════════════════════════════════════════════
Teşhis (çok-vadeli audit): hiçbir vade al-tut'u yenemedi çünkü strateji
NAKDE geçince, +%227 yapan piyasaya otomatik kaybediyor (cash drag).
AMA hisselerin ~%42'si tek tek endeksi geçiyor.

YENİ HİPOTEZ: piyasayı ZAMANLAMA bırak. HEP %100 yatırımda kal, sinyalin
en yüksek puanladığı top-N hisseyi tut, periyodik dengele. Soru: SEÇİM,
yatırımda kalarak XU100'ü yenebiliyor mu? (Fonların gerçekten oynadığı oyun.)

İki sıralama (scorer) kıyaslanır:
  • MOMENTUM : son 126 bar getirisi (klasik cross-sectional faktör)
  • SİNYAL   : bizim hibrit puanımız (ateşleyen hisseler; kalan ağırlık → endeks)
Kıyas çıtaları: XU100 al-tut · eşit-ağırlık-TÜM al-tut · mevduat.
Maliyet: devir başına komisyon+slippage. Leakage yok (skor t'de, getiri t+1).
"""

import datetime, traceback
import numpy as np
import pandas as pd

N_HOLD     = 12          # portföydeki hisse sayısı (top-N)
REBAL_GUN  = 21          # ~aylık dengeleme
BASLANGIC  = 130         # momentum/sinyal için ısınma
MOM_LB     = 126         # momentum geriye bakış (bar)
FETCH_GUN  = 1500


def _yillik(nav, gun):
    if gun <= 0 or nav <= 0: return -100.0
    return ((nav) ** (365.0 / gun) - 1) * 100


def _sharpe_mdd(nav_seri, mevduat_gunluk):
    r = nav_seri.pct_change().dropna()
    if len(r) < 5:
        return 0.0, 0.0
    ex = r - mevduat_gunluk
    sd = ex.std()
    sharpe = (ex.mean() / sd * np.sqrt(252)) if sd > 0 else 0.0
    huzme = nav_seri / nav_seri.cummax() - 1.0
    return float(sharpe), float(huzme.min() * 100)


def _devir_maliyet(eski, yeni, fr):
    syms = set(eski) | set(yeni)
    tt = sum(abs(yeni.get(s, 0.0) - eski.get(s, 0.0)) for s in syms)
    return fr * tt   # her birim devre tek-yön sürtünme (al+sat = abs fark toplamı)


def _topn(skor_seri, n):
    s = skor_seri.dropna()
    s = s[np.isfinite(s)]
    if len(s) == 0:
        return []
    return list(s.sort_values(ascending=False).head(n).index)


def portfoy_backtest(panel, xu, skorla, n_hold, rebal, baslangic, fr, mevduat_gunluk):
    """panel: dates×symbol Close (XU100 takvimine hizalı, ffill). xu: XU100 Close serisi.
       skorla(t_idx)->pd.Series{symbol:skor} (yalnız ≤t veri). Hep yatırımda; kalan ağ.→endeks."""
    dates = panel.index
    n = len(dates)
    nav = 1.0
    navs = [1.0]; out_dates = [dates[baslangic]]
    holdings = {}
    sinyal_sayac = []
    for t in range(baslangic, n - 1):
        if (t - baslangic) % rebal == 0:
            skor = skorla(t)
            picks = _topn(skor, n_hold)
            sinyal_sayac.append(len(picks))
            yeni = {s: 1.0 / n_hold for s in picks}   # picks<n_hold ise kalan ağırlık→endeks
            nav *= (1 - _devir_maliyet(holdings, yeni, fr))
            holdings = yeni
        # günlük getiri t→t+1
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
        nav *= (1 + r)
        navs.append(nav); out_dates.append(dates[t + 1])
    nav_seri = pd.Series(navs, index=out_dates)
    ort_sinyal = float(np.mean(sinyal_sayac)) if sinyal_sayac else 0.0
    return nav_seri, ort_sinyal


def calistir():
    from veri import veri_al, VADE_AYAR
    from backtest import _FR, MEVDUAT_YILLIK, _MEVDUAT_GUNLUK
    from tarama_core import BIST_TUM, KOD_SEKTOR
    from hibrit_analiz import analiz_et as hibrit, HIBRIT_ESIK

    ayar = VADE_AYAR["gunluk"]
    kodlar = list(dict.fromkeys(BIST_TUM))

    # XU100 ana takvim
    xu_df, _ = veri_al("XU100", gun=FETCH_GUN, min_gun=200, aralik="1d")
    if xu_df is None or len(xu_df) < BASLANGIC + 60:
        print("XU100 verisi yok — durdu."); return
    takvim = xu_df.index
    xu = xu_df["Close"].reindex(takvim).ffill()

    # Fiyat paneli + tam df'ler (sinyal scorer için)
    paneller = {}
    seriler = {}
    for kod in kodlar:
        try:
            df, _ = veri_al(kod, gun=FETCH_GUN, min_gun=200, aralik="1d")
            if df is None or len(df) < BASLANGIC + 60:
                continue
            paneller[kod] = df
            seriler[kod] = df["Close"].reindex(takvim).ffill()
        except Exception as e:
            print(f"  {kod}: {e}")
    if len(seriler) < N_HOLD + 5:
        print(f"Yeterli hisse yok ({len(seriler)}) — durdu."); return
    panel = pd.DataFrame(seriler)
    gecerli = [k for k in paneller if k in panel.columns]
    print(f"Panel: {len(gecerli)} hisse × {len(takvim)} gün")

    toplam_gun = (takvim[-1] - takvim[BASLANGIC]).days
    yil = toplam_gun / 365.0

    # ── SCORER 1: MOMENTUM ──
    def skor_momentum(t):
        if t - MOM_LB < 0:
            return pd.Series(dtype=float)
        now = panel.iloc[t]; then = panel.iloc[t - MOM_LB]
        return (now / then - 1.0)

    # ── SCORER 2: HİBRİT SİNYAL PUANI ──
    def skor_sinyal(t):
        tarih = takvim[t]
        xs = xu.loc[:tarih]
        out = {}
        for kod in gecerli:
            sdf = paneller[kod].loc[:tarih]
            if len(sdf) < 60:
                continue
            try:
                r = hibrit(kod, sdf, ayar, 100000, 1.0, KOD_SEKTOR.get(kod, "Diğer"),
                           detayli=False, backtest=True, endeks_close=xs)
                if r and r.get("puan") is not None:
                    out[kod] = float(r["puan"])
            except Exception:
                pass
        return pd.Series(out, dtype=float)

    sonuc = {}
    for ad, fn in [("Momentum (top-N)", skor_momentum), ("Hibrit Sinyal (top-N)", skor_sinyal)]:
        print(f"\n=== {ad} ===")
        try:
            nav_seri, ort_sin = portfoy_backtest(panel, xu, fn, N_HOLD, REBAL_GUN,
                                                 BASLANGIC, _FR, _MEVDUAT_GUNLUK)
            son = float(nav_seri.iloc[-1])
            sh, mdd = _sharpe_mdd(nav_seri, _MEVDUAT_GUNLUK)
            sonuc[ad] = {"nav": son, "yillik": _yillik(son, toplam_gun),
                         "sharpe": sh, "mdd": mdd, "ort_sinyal": ort_sin}
            print(f"  NAV={son:.3f} yıllık={sonuc[ad]['yillik']:.1f}% Sharpe={sh:.2f} mdd={mdd:.1f}%")
        except Exception as e:
            print(f"  HATA {ad}: {e}"); traceback.print_exc()

    # ── ÇITALAR ──
    # XU100 al-tut
    xb = float(xu.iloc[BASLANGIC]); xs = float(xu.iloc[-1])
    xu_nav = (xs * (1 - _FR)) / (xb * (1 + _FR)) if xb > 0 else 1.0
    xu_seri = (xu.iloc[BASLANGIC:] / xb)
    xu_sh, xu_mdd = _sharpe_mdd(xu_seri, _MEVDUAT_GUNLUK)
    # Eşit ağırlık TÜM hisse al-tut
    ew_carp = []
    for k in gecerli:
        p0 = panel[k].iloc[BASLANGIC]; p1 = panel[k].iloc[-1]
        if p0 > 0 and np.isfinite(p0) and np.isfinite(p1):
            ew_carp.append((p1 * (1 - _FR)) / (p0 * (1 + _FR)))
    ew_nav = float(np.mean(ew_carp)) if ew_carp else 1.0
    # Mevduat
    mev_nav = (1 + MEVDUAT_YILLIK) ** yil

    # ── RAPOR ──
    L = []
    L.append("# APEX — Cross-Sectional Audit · Hep Yatırımda, Top-N Seçim")
    L.append("")
    L.append(f"_Üretim: {datetime.datetime.now():%Y-%m-%d %H:%M} · {len(gecerli)} hisse · "
             f"{yil:.1f} yıl · top-{N_HOLD}, ~{REBAL_GUN}g dengeleme · maliyet: komisyon+slippage · leakage yok_")
    L.append("")
    L.append("## Soru: Seçim, yatırımda kalarak XU100'ü yeniyor mu?")
    L.append("")
    L.append("| Strateji | Son NAV (×) | Getiri% | Yıllık% | Sharpe | MaxDD% | XU100'ü geçti? |")
    L.append("|---|---:|---:|---:|---:|---:|:--:|")
    for ad, d in sonuc.items():
        gecti = "✅" if d["nav"] > xu_nav else "❌"
        L.append(f"| {ad} | {d['nav']:.2f} | {(d['nav']-1)*100:.1f} | {d['yillik']:.1f} | "
                 f"{d['sharpe']:.2f} | {d['mdd']:.1f} | {gecti} |")
    L.append(f"| _XU100 al-tut_ | {xu_nav:.2f} | {(xu_nav-1)*100:.1f} | {_yillik(xu_nav,toplam_gun):.1f} | "
             f"{xu_sh:.2f} | {xu_mdd:.1f} | — |")
    L.append(f"| _Eşit-ağırlık TÜM al-tut_ | {ew_nav:.2f} | {(ew_nav-1)*100:.1f} | "
             f"{_yillik(ew_nav,toplam_gun):.1f} | — | — | "
             f"{'✅' if ew_nav>xu_nav else '❌'} |")
    L.append(f"| _Mevduat (~%{int(MEVDUAT_YILLIK*100)})_ | {mev_nav:.2f} | {(mev_nav-1)*100:.1f} | "
             f"{int(MEVDUAT_YILLIK*100)}.0 | — | — | "
             f"{'✅' if mev_nav>xu_nav else '❌'} |")
    L.append("")

    # ── KARAR ──
    kazanan = [ad for ad, d in sonuc.items() if d["nav"] > xu_nav]
    L.append("## Karar")
    L.append("")
    if kazanan:
        L.append(f"**XU100'ü yatırımda kalarak geçen seçim: {', '.join(kazanan)}.** Cash drag olmadan "
                 f"seçim alfa üretiyor. KANIT değil ön sinyal — sonraki: out-of-sample (veriyi ikiye böl), "
                 f"N ve dengeleme sıklığı duyarlılığı, Sharpe'ın mevduatı geçmesi.")
    else:
        L.append("**Hiçbir seçim XU100'ü geçemedi.** Bu evrende cross-sectional seçim de endeksi yenmiyor — "
                 "muhtemelen hisseler fazla korele ve endeks birkaç dev hisseyle taşınıyor. Sonraki kaldıraç: "
                 "(a) farklı faktör (değer/kalite/düşük-volatilite), (b) fundamental veri, ya da hedefi "
                 "değiştir: 'endeksi yenmek' yerine 'benzer getiri + daha düşük MaxDD' (risk-ayarlı).")
    L.append("")
    if "Hibrit Sinyal (top-N)" in sonuc:
        os_ = sonuc["Hibrit Sinyal (top-N)"]["ort_sinyal"]
        L.append(f"> Sinyal scorer dengeleme başına ort. {os_:.1f} hisse işaretledi (top-{N_HOLD} hedefi). "
                 f"{N_HOLD}'in altındaysa kalan ağırlık endekste tutuldu (hep yatırımda).")
    L.append("")
    L.append("---")
    L.append(f"*Hep %100 yatırımda. Komisyon %0.2+slippage %0.15 (tek yön, devirde). "
             f"Skor t kapanışında, getiri t+1 — leakage yok.*")

    metin = "\n".join(L)
    with open("BACKTEST_SONUC.md", "w", encoding="utf-8") as f:
        f.write(metin)
    print("\n" + metin)
    print("\n>>> BACKTEST_SONUC.md yazıldı.")


if __name__ == "__main__":
    calistir()
