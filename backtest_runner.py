"""
APEX · TEMEL-SEÇİM BACKTEST (v9 — Tera'nın oynadığı oyun)
Hisseleri TTM ROE + kâr büyümesiyle sırala (rank-normalize → aykırı dirençli),
top-N tut, çeyreklik dengele, HEP yatırımda. Point-in-time (lookahead yok).
ASIL SORU: Temel-seçim, momentum'un çöktüğü yerde — OOS / yüksek-faiz yarısında —
mevduatı+endeksi geçiyor mu? (Temel faktör, fiyat-momentumundan daha kalıcı olmalı.)
"""
import datetime
import numpy as np, pandas as pd
import temel_veri as tv

BASLANGIC = 260
FETCH_GUN = 3000
REBAL = 63            # ~çeyreklik
N_HOLD = 12
MOM_LB = 126


def _devir(eski, yeni, fr):
    syms = set(eski) | set(yeni)
    return fr * sum(abs(yeni.get(s, 0.0) - eski.get(s, 0.0)) for s in syms)


def _rank_pct(d):
    if not d: return {}
    ks = list(d.keys()); vs = np.array([d[k] for k in ks], float)
    order = vs.argsort().argsort()           # 0..n-1
    n = len(ks)
    return {ks[i]: (order[i] / (n - 1) if n > 1 else 0.5) for i in range(n)}


def portfoy(panel, xu, skorla, n_hold, rebal, fr, lo, hi):
    nav = 1.0; navs = [1.0]; holdings = {}
    for t in range(lo, hi):
        if (t - lo) % rebal == 0:
            picks = skorla(t, n_hold)
            yeni = {s: 1.0 / n_hold for s in picks}
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
    s = pd.Series(navs); mdd = float((s / s.cummax() - 1).min() * 100)
    return nav, mdd


def ew_nav(panel, cols, fr, lo, hi):
    v = [(panel[k].iat[hi]*(1-fr))/(panel[k].iat[lo]*(1+fr))
         for k in cols if panel[k].iat[lo] > 0 and np.isfinite(panel[k].iat[hi])]
    return float(np.mean(v)) if v else 1.0

def dep_nav(dates, mev, lo, hi):
    nav = 1.0
    for t in range(lo, hi):
        nav *= (1+mev)**(max((dates[t+1]-dates[t]).days,1)/365.0)
    return nav

def idx_nav(xu, fr, lo, hi):
    xb = xu.iat[lo]; xs = xu.iat[hi]
    return (xs*(1-fr))/(xb*(1+fr)) if xb > 0 else 1.0


def calistir():
    from veri import veri_al
    from backtest import _FR, MEVDUAT_YILLIK
    from tarama_core import BIST_TUM

    xu_df, _ = veri_al("XU100", gun=FETCH_GUN, min_gun=300, aralik="1d")
    if xu_df is None or len(xu_df) < BASLANGIC + 200:
        print("XU100 yok"); return
    takvim = xu_df.index; xu = xu_df["Close"].reindex(takvim).ffill()
    n = len(takvim); son = n - 1; orta = (BASLANGIC + son) // 2

    fseri = {}; pser = {}; tipler = {"sanayi":0,"banka":0}
    print("Faktör + fiyat çekiliyor...")
    for kod in dict.fromkeys(BIST_TUM):
        try:
            seri, tip = tv.faktor_zaman_serisi(kod, 2017)
            if not seri: continue
            df, _ = veri_al(kod, gun=FETCH_GUN, min_gun=300, aralik="1d")
            if df is None or len(df) < BASLANGIC + 200: continue
            fseri[kod] = sorted(seri.items())     # [(tarih,{roe,buyume})]
            pser[kod] = df["Close"].reindex(takvim).ffill()
            if tip in tipler: tipler[tip] += 1
        except Exception as e:
            print(f"  {kod}: {e}")
    panel = pd.DataFrame(pser); cols = list(panel.columns)
    print(f"{len(cols)} hisse (sanayi {tipler['sanayi']}, banka {tipler['banka']})")
    if len(cols) < N_HOLD + 5:
        print("yetersiz hisse"); return

    def faktor_at(kod, tarih):
        best = None
        for ad, f in fseri[kod]:
            if ad <= tarih: best = f
            else: break
        return best

    def skorla(t, n_hold):
        tarih = takvim[t].date() if hasattr(takvim[t], "date") else takvim[t]
        roe = {}; gro = {}
        for kod in cols:
            f = faktor_at(kod, tarih)
            if not f: continue
            if f.get("roe") is not None: roe[kod] = f["roe"]
            if f.get("buyume") is not None: gro[kod] = f["buyume"]
        rr = _rank_pct(roe); gr = _rank_pct(gro)
        skor = {}
        for kod in cols:
            parts = []
            if kod in rr: parts.append(rr[kod])
            if kod in gr: parts.append(gr[kod])
            if parts: skor[kod] = sum(parts) / len(parts)
        if not skor: return []
        return [k for k, _ in sorted(skor.items(), key=lambda x: -x[1])[:n_hold]]

    def skor_mom(t, n_hold):
        if t - MOM_LB < 0: return []
        sc = (panel.iloc[t] / panel.iloc[t - MOM_LB] - 1.0).replace([np.inf,-np.inf],np.nan).dropna()
        return list(sc.sort_values(ascending=False).head(n_hold).index)

    yil = (takvim[son]-takvim[BASLANGIC]).days/365.0
    L = ["# APEX — Temel-Seçim Backtest (TTM ROE + kâr büyümesi)", "",
         f"_{datetime.datetime.now():%Y-%m-%d %H:%M} · {len(cols)} hisse · {yil:.1f} yıl · "
         f"top-{N_HOLD}, çeyreklik · rank-normalize · point-in-time_", "",
         "## Temel-seçim, momentum'un çöktüğü yerde (OOS) tutuyor mu?", "",
         "| Dönem | Temel-Seçim | Momentum | Eşit-ağ. | Mevduat | Endeks | Temel>mev&end? |",
         "|---|---:|---:|---:|---:|---:|:--:|"]
    oos_ok = True
    for ad, lo, hi in [("İlk yarı (IS)", BASLANGIC, orta), ("İkinci yarı (OOS)", orta, son),
                       ("TÜM dönem", BASLANGIC, son)]:
        tf, tmdd = portfoy(panel, xu, skorla, N_HOLD, REBAL, _FR, lo, hi)
        mf, _ = portfoy(panel, xu, skor_mom, N_HOLD, REBAL, _FR, lo, hi)
        e = ew_nav(panel, cols, _FR, lo, hi); d = dep_nav(takvim, MEVDUAT_YILLIK, lo, hi)
        ix = idx_nav(xu, _FR, lo, hi)
        gec = tf > d and tf > ix
        if "yarı" in ad and not gec: oos_ok = False
        L.append(f"| {ad} | {tf:.2f} | {mf:.2f} | {e:.2f} | {d:.2f} | {ix:.2f} | {'✅' if gec else '❌'} |")
    L.append("")
    # tüm dönem MaxDD
    tf_all, tmdd_all = portfoy(panel, xu, skorla, N_HOLD, REBAL, _FR, BASLANGIC, son)
    L.append(f"_Temel-seçim TÜM dönem MaxDD: %{tmdd_all:.1f}_")
    L.append("")
    L.append("## Karar")
    L.append("")
    if oos_ok:
        L.append("**Temel-seçim OOS'ta da tutuyor — momentum'un başaramadığını başardı.** Yüksek-faiz yarısında da "
                 "mevduatı+endeksi geçiyor. Bu, fiyat değil TEMEL veriye dayandığı için daha kalıcı bir edge adayı. "
                 "Sonraki: F/K/değer faktörü ekle, N & dengeleme duyarlılığı, drawdown overlay, ileri paper-test.")
    else:
        L.append("**Temel-seçim de OOS'ta zayıf.** İlk yarıda iyi olsa bile yüksek-faiz yarısında mevduatı+endeksi "
                 "geçemiyor. Demek bu rejimde tek başına temel-seçim de yetmiyor; ya değer/kalite faktörü eklenmeli "
                 "ya da rejim-tahsisi (mevduat tabanı) ile birleştirilmeli.")
    L.append("")
    L.append("> Survivorship uyarısı sürüyor (bugünkü hisseler). Kesin yargı için delist'ler de gerek.")
    L.append("")
    L.append("---\n*TTM ROE + YoY büyüme, rank-normalize (aykırı dirençli). Maliyet komisyon+slippage. "
             "Faktör açıklanma-tarihinde, getiri sonrasında — leakage yok.*")
    metin = "\n".join(L)
    with open("BACKTEST_SONUC.md", "w", encoding="utf-8") as f:
        f.write(metin)
    print("\n"+metin); print("\n>>> yazıldı.")


if __name__ == "__main__":
    calistir()
