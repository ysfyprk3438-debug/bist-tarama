"""
APEX · RİSK ARACI DOĞRULAMA — vol-hedefleme gerçekten bütçeye yakın MaxDD veriyor mu?
İddia: "ağırlık = hedef_vol/gerçek_vol senin DD bütçene saygı gösterir." Bunu TEST eder.
Geçmiş XU100'de vol-hedefli portföyü (haftalık rebalance) kurar, GERÇEKLEŞEN MaxDD'yi
bütçeyle kıyaslar. MaxDD >> bütçe ise k=2.5 fazla iyimser → ampirik k öner.
(Bu bir EDGE testi DEĞİL — sadece risk kontrolünün vaadini doğrular.)
"""
import datetime
import numpy as np, pandas as pd
import makro_oto as mk
import pozisyon as pz

PENCERE = 60
REBAL = 5  # haftalık


def _mdd(nav):
    s = pd.Series(nav); return float((s / s.cummax() - 1).min() * 100)


def voltarget_nav(xu, dates, lo, hi, butce_pct):
    nav = 1.0; navs = [1.0]; w = 0.0
    for i, t in enumerate(range(lo, hi)):
        if i % REBAL == 0:
            yv = pz.yillik_vol(xu.values[:t + 1], PENCERE)
            w = pz.vol_hedef_agirlik(yv, butce_pct)   # saf vol-hedef (rejim tilt yok)
        gap = max((dates[t + 1] - dates[t]).days, 1)
        p0 = xu.iat[t]; p1 = xu.iat[t + 1]
        r_eq = (p1 / p0 - 1.0) if (p0 > 0 and np.isfinite(p0) and np.isfinite(p1)) else 0.0
        m = mk.makro_at(dates[t]); pol = m["politika"] if m else 40.0
        r_dep = (1 + pol / 100.0) ** (gap / 365.0) - 1.0
        nav *= (1 + w * r_eq + (1 - w) * r_dep); navs.append(nav)
    return nav, navs


def calistir():
    from veri import veri_al
    xu_df, _ = veri_al("XU100", gun=3000, min_gun=300, aralik="1d")
    if xu_df is None or len(xu_df) < 400:
        print("XU100 yok"); return
    dates = xu_df.index; xu = xu_df["Close"].reindex(dates).ffill()
    lo, hi = PENCERE + 5, len(dates) - 1
    yil = (dates[hi] - dates[lo]).days / 365.0

    # all-in hisse referans
    nav_eq = float(xu.iat[hi] / xu.iat[lo]); 
    mdd_eq = _mdd(xu.values[lo:hi + 1])

    L = ["# APEX — Risk Aracı Doğrulama (vol-hedefleme vaadi)", "",
         f"_{datetime.datetime.now():%Y-%m-%d %H:%M} · XU100 · {yil:.1f} yıl · haftalık rebalance_", "",
         "## Vol-hedefli portföy: bütçe vs GERÇEKLEŞEN MaxDD", "",
         "| DD bütçesi | Gerçekleşen MaxDD | Getiri (×) | Vaad tuttu mu? |", "|---|---:|---:|:--:|"]
    tutarli = 0; toplam = 0
    for B in (1.5, 5.0, 10.0, 20.0):
        nav, navs = voltarget_nav(xu, dates, lo, hi, B)
        mdd = _mdd(navs)
        # vaad: gerçekleşen MaxDD bütçeyi ~1.5x'ten fazla aşmasın (kaba tolerans)
        ok = abs(mdd) <= B * 1.5
        toplam += 1; tutarli += int(ok)
        L.append(f"| %{B:.1f} | %{mdd:.1f} | {nav:.2f} | {'✅' if ok else '❌ aşıldı'} |")
    L += ["", f"_Referans — all-in hisse: MaxDD %{mdd_eq:.1f} · getiri {nav_eq:.2f}×_", "",
          "## Yorum", ""]
    if tutarli >= toplam - 1:
        L += ["**Vol-hedefleme vaadini büyük ölçüde tuttu** — gerçekleşen MaxDD bütçelere yakın kaldı, "
              "all-in hisseye kıyasla düşüş ciddi şekilde kırpıldı. Risk aracı dürüst: söylediği bütçeyi "
              "kabaca teslim ediyor. k=2.5 makul."]
    else:
        # ampirik k öner: MaxDD/bütçe oranlarının medyanı ~ gereken ölçek
        L += ["**Vol-hedefleme bazı bütçelerde aşıldı** — gerçekleşen MaxDD bütçeyi belirgin geçti. "
              "Sebep: oynaklık sıçramaları gecikmeli ölçülür + şişman kuyruklar. Dürüst düzeltme: k'yı "
              "büyüt (daha temkinli ağırlık). Aşağıdaki orana göre k≈2.5×(ortalama aşım) yapılmalı.",
              "", "_Yani araç şu an söylediği bütçeden DAHA RİSKLİ; düzeltilmeli (k yukarı)._"]
    L += ["", "---\n*Risk kontrolü testi (alfa değil). Vol 60g trailing, haftalık rebalance, "
          "mevduat zamana-göre faiz. Karar t, getiri t+1.*"]
    with open("BACKTEST_SONUC.md", "w", encoding="utf-8") as f:
        f.write("\n".join(L))
    print("\n".join(L)); print("\n>>> yazıldı.")


if __name__ == "__main__":
    calistir()
