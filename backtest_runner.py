"""
APEX · SAĞLAMLIK GEÇİDİ — makro reel-faiz rejimini KIRMAYA çalışır.
1) Eşik taraması: edge tüm makul gir/çık eşiklerinde yaşıyor mu, yoksa tek noktada mı?
2) Gecikme stresi: makro veri 60-90 gün geç gelse edge ölür mü?
3) Plasebo: aynı #geçiş + aynı %hisse-süresi RASTGELE yerleştirilen 4000 sahte strateji —
   gerçek rejim dağılımın neresinde? (top %5 → isabet; orta → şans/hindsight)
Geçit amacı edge'i POLİSHLEMEK değil KIRMAK. Sağ çıkarsa güven meşru artar.
"""
import datetime
import numpy as np, pandas as pd
import makro_veri as mk

BASLANGIC = 60
FETCH_GUN = 3000
REBAL = 21


def _mdd(navs):
    s = pd.Series(navs); return float((s / s.cummax() - 1).min() * 100)


def rejim_alloc(dates, lo, hi, gir, cik, lag):
    """Rejim kararlarını bool dizi olarak döndür (True=hisse). Histerezis + aylık gözden geçirme."""
    alloc = np.zeros(hi - lo, dtype=bool)
    in_eq = False
    for i, t in enumerate(range(lo, hi)):
        m = mk.makro_at(dates[t], lag_gun=lag)
        reel = m["reel"] if m else 5.0
        if i % REBAL == 0:
            if (not in_eq) and reel < gir: in_eq = True
            elif in_eq and reel > cik: in_eq = False
        alloc[i] = in_eq
    return alloc


def faktorler(xu, dates, lo, hi, lag):
    """Günlük brüt çarpanlar: hisse (endeks) ve mevduat (zamana göre faiz)."""
    eqf = np.ones(hi - lo); depf = np.ones(hi - lo)
    for i, t in enumerate(range(lo, hi)):
        gap = max((dates[t + 1] - dates[t]).days, 1)
        p0 = xu.iat[t]; p1 = xu.iat[t + 1]
        eqf[i] = (p1 / p0) if (p0 > 0 and np.isfinite(p0) and np.isfinite(p1)) else 1.0
        m = mk.makro_at(dates[t], lag_gun=lag); pol = m["politika"] if m else 40.0
        depf[i] = (1 + pol / 100.0) ** (gap / 365.0)
    return eqf, depf


def nav_of(alloc, eqf, depf):
    return float(np.prod(np.where(alloc, eqf, depf)))


def gecis_say(alloc):
    return int(np.sum(alloc[1:] != alloc[:-1]))


def statik_mevduat(depf):
    return float(np.prod(depf))


def calistir():
    from veri import veri_al
    from backtest import _FR

    xu_df, _ = veri_al("XU100", gun=FETCH_GUN, min_gun=300, aralik="1d")
    if xu_df is None or len(xu_df) < BASLANGIC + 200:
        print("XU100 yok"); return
    dates = xu_df.index; xu = xu_df["Close"].reindex(dates).ffill()
    n = len(dates); son = n - 1; orta = (BASLANGIC + son) // 2
    yil = (dates[son] - dates[BASLANGIC]).days / 365.0
    rng = np.random.default_rng(42)

    L = ["# APEX — Sağlamlık Geçidi (rejimi KIRMA testi)", "",
         f"_{datetime.datetime.now():%Y-%m-%d %H:%M} · XU100 · {yil:.1f} yıl · brüt çarpan bazlı_", ""]

    # ---- 1) EŞİK TARAMASI ----
    L += ["## 1) Eşik taraması — edge tek noktada mı, her yerde mi?", "",
          "| gir / çık | TÜM | OOS | mev(OOS) | end(OOS) | OOS geçti? |", "|---|---:|---:|---:|---:|:--:|"]
    gecen = 0; toplam = 0
    for gir in (-1.0, -3.0, -5.0, -8.0):
        for cik in (1.0, 3.0, 5.0):
            eqf_f, depf_f = faktorler(xu, dates, BASLANGIC, son, 35)
            al_full = rejim_alloc(dates, BASLANGIC, son, gir, cik, 35)
            al_oos = rejim_alloc(dates, orta, son, gir, cik, 35)
            eqf_o, depf_o = faktorler(xu, dates, orta, son, 35)
            nav_full = nav_of(al_full, eqf_f, depf_f)
            nav_oos = nav_of(al_oos, eqf_o, depf_o)
            mev_o = statik_mevduat(depf_o)
            end_o = float(xu.iat[son] / xu.iat[orta])
            ok = nav_oos > mev_o and nav_oos > end_o
            toplam += 1; gecen += int(ok)
            L.append(f"| {gir:.0f} / {cik:.0f} | {nav_full:.2f} | {nav_oos:.2f} | {mev_o:.2f} | {end_o:.2f} | {'✅' if ok else '❌'} |")
    L += ["", f"**{toplam} eşik kombinasyonunun {gecen}'i OOS'ta mevduat+endeksi geçti.** "
          + ("Edge geniş eşik aralığında yaşıyor → kırılgan değil." if gecen >= toplam * 0.7
             else "Edge sadece dar eşik bandında → KIRILGAN, şüpheli."), ""]

    # ---- 2) GECİKME STRESİ ----
    L += ["## 2) Gecikme stresi — makro veri geç gelirse?", "",
          "| lag (gün) | TÜM | OOS | OOS geçti? |", "|---|---:|---:|:--:|"]
    lag_ok = 0
    for lag in (35, 60, 90):
        al_full = rejim_alloc(dates, BASLANGIC, son, -3.0, 3.0, lag)
        eqf_f, depf_f = faktorler(xu, dates, BASLANGIC, son, lag)
        al_oos = rejim_alloc(dates, orta, son, -3.0, 3.0, lag)
        eqf_o, depf_o = faktorler(xu, dates, orta, son, lag)
        nav_full = nav_of(al_full, eqf_f, depf_f); nav_oos = nav_of(al_oos, eqf_o, depf_o)
        mev_o = statik_mevduat(depf_o); end_o = float(xu.iat[son] / xu.iat[orta])
        ok = nav_oos > mev_o and nav_oos > end_o; lag_ok += int(ok)
        L.append(f"| {lag} | {nav_full:.2f} | {nav_oos:.2f} | {'✅' if ok else '❌'} |")
    L += ["", f"**3 gecikme senaryosunun {lag_ok}'i OOS'ta geçti.** "
          + ("90 güne kadar gecikmeye dayanıklı." if lag_ok == 3
             else "Gecikmeye duyarlı — gerçek hayatta zayıflayabilir."), ""]

    # ---- 3) PLASEBO ----
    eqf, depf = faktorler(xu, dates, BASLANGIC, son, 35)
    al_real = rejim_alloc(dates, BASLANGIC, son, -3.0, 3.0, 35)
    nav_real = nav_of(al_real, eqf, depf)
    frac = float(al_real.mean()); gec = gecis_say(al_real)
    Ln = hi_len = son - BASLANGIC
    blok = max(1, int(round(frac * Ln)))
    N = 4000
    # Plasebo B: tek hisse-bloğu (D-E-D), uzunluk=frac*L, rastgele konum
    pb = np.empty(N)
    for k in range(N):
        start = rng.integers(0, Ln - blok + 1)
        a = np.zeros(Ln, dtype=bool); a[start:start + blok] = True
        pb[k] = nav_of(a, eqf, depf)
    perc_b = float((pb < nav_real).mean() * 100)
    # Plasebo A: aylık rastgele in/out, hedef oran=frac
    pa = np.empty(N)
    nblk = int(np.ceil(Ln / REBAL))
    for k in range(N):
        flags = rng.random(nblk) < frac
        a = np.repeat(flags, REBAL)[:Ln]
        pa[k] = nav_of(a, eqf, depf)
    perc_a = float((pa < nav_real).mean() * 100)
    L += ["## 3) Plasebo — 2 geçiş + %{:.0f} hisse-süresi rastgele yerleşseydi?".format(frac * 100), "",
          f"Gerçek rejim brüt: **{nav_real:.2f}×** · {gec} geçiş · %{frac*100:.0f} hissede", "",
          f"| Plasebo | 4000 sahte ortalama | Gerçek yüzdelik |", "|---|---:|---:|",
          f"| B: rastgele tek blok (D-E-D) | {pb.mean():.2f}× | **%{perc_b:.1f}** |",
          f"| A: aylık rastgele (oran eşli) | {pa.mean():.2f}× | **%{perc_a:.1f}** |", "",
          ("**Plasebo B yorumu:** "
           + ("gerçek rejim top %5'te → 2 geçişin yeri şans değil, isabet." if perc_b >= 95
              else "gerçek rejim üst bantta (%90+) → güçlü ama kesin değil sinyal." if perc_b >= 90
              else "gerçek rejim ortanın üstünde (%80+) → zayıf sinyal, şanstan tam ayrışmıyor." if perc_b >= 80
              else "gerçek rejim ortalarda → zamanlama şanstan ayırt edilemiyor (kötü işaret).")), ""]

    # ---- DERECELİ KARAR ----
    esik_skor = gecen / toplam            # eşik sağlamlığı 0-1
    lag_skor = lag_ok / 3                  # gecikme sağlamlığı 0-1
    pb_skor = (perc_b >= 95) * 1.0 + (90 <= perc_b < 95) * 0.6 + (80 <= perc_b < 90) * 0.3
    L += ["## Geçit Kararı (dereceli)", "",
          f"Eşik sağlamlığı: %{esik_skor*100:.0f} · Gecikme sağlamlığı: %{lag_skor*100:.0f} · "
          f"Plasebo-B ayrışması: {'güçlü' if pb_skor>=1 else 'orta' if pb_skor>=0.6 else 'zayıf' if pb_skor>=0.3 else 'yok'}", ""]
    if esik_skor >= 0.7 and lag_skor >= 0.66 and pb_skor >= 0.6:
        L += ["**Rejim üç kırma testinden de büyük ölçüde sağ çıktı** — geniş eşik bandında yaşıyor, gecikmeye "
              "dayanıyor, plasebodan ayrışıyor. Bulgu 'aday'dan 'kırılmayı reddeden sağlam aday'a yükseldi. "
              "**Tek kalan ve tek gerçek sınav: ileri test** (kuralı sonu bilerek tasarladım; bunu sadece zaman çürütür).",
              "", "**Seviye atlama:** (a) ileri kağıt-test günlüğünü kur, (b) hissedeyken endeks yerine "
              "momentum/temel-seçim koyup geçidi ONUN üstünde tekrarla, (c) volatilite-hedefiyle MaxDD'yi %1.5'e indir."]
    elif esik_skor >= 0.7 and lag_skor >= 0.66:
        L += ["**Rejim eşik+gecikmeye dayanıklı ama plasebodan net ayrışmıyor.** Mekanizma sağlam, ama 2 geçişin "
              "tam yeri kısmen şans olabilir. Mantıklı sonuç: ileri teste değer, ama tek başına 'kanıt' sayma — "
              "hissedeyken seçim ekleyip (momentum/temel) plasebo ayrışmasını güçlendirmeyi dene."]
    else:
        L += ["**Rejim en az bir kırma testinde çatladı.** ❌ satırlara bak: eşikte dar bant → tesadüf; "
              "gecikmede ölüm → gerçek-zaman uygulanamaz. Dürüst sonuç: bulgu göründüğü kadar sağlam değil."]
    L += ["", "---\n*Brüt çarpan bazlı (zamanlama becerisini izole etmek için sürtünme hariç; "
          "gerçek rejim 2 geçişte sürtünme ihmal edilebilir). Karar t, getiri t+1; enflasyon lag'li — leakage yok.*"]

    metin = "\n".join(L)
    with open("BACKTEST_SONUC.md", "w", encoding="utf-8") as f:
        f.write(metin)
    print(metin); print("\n>>> yazıldı.")


if __name__ == "__main__":
    calistir()
