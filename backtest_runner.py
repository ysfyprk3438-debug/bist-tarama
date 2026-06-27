"""
═══════════════════════════════════════════════════════════════
APEX · DÜRÜST BACKTEST KOŞUCUSU  (v4 — audit + al-tut çıtası)
═══════════════════════════════════════════════════════════════
İki çıtaya birden bakar:
  ÇITA 1 (mevduat): işlem başına mevduat-üstü getiri, havuz t-istatistiği.
  ÇITA 2 (al-tut) : strateji (fund NAV, nakit dahil) vs hisse al-tut vs
                    ENDEKS (XU100) al-tut. Asıl rakip "BIST-100 al ve tut".

Maliyet artık gerçekçi: komisyon + slippage + stop ekstra kayma (backtest.py v4).
"""

import datetime
import traceback
import numpy as np

STRATEJI     = "hibrit"     # "hibrit" | "teknik"
VADE_KEY     = "haftalik"
FETCH_GUN    = 1500
BASLANGIC    = 120
HISSE_SAYISI = 0
T_ESIK       = 2.0
N_MIN        = 100


def _fmt(x, n=2):
    try:
        return f"{x:.{n}f}"
    except Exception:
        return str(x)


def calistir():
    from veri import veri_al, VADE_AYAR
    from backtest import backtest_calistir, _FR, STOP_EKSTRA, MEVDUAT_YILLIK
    from tarama_core import BIST_TUM, KOD_SEKTOR

    if STRATEJI == "hibrit":
        from hibrit_analiz import analiz_et as motor, HIBRIT_ESIK
        strateji_ad = f"HİBRİT (eşik={HIBRIT_ESIK})"
    else:
        from analiz import analiz_et as motor
        strateji_ad = "TEKNİK (saf)"

    ayar = VADE_AYAR[VADE_KEY]
    kodlar = BIST_TUM if HISSE_SAYISI <= 0 else BIST_TUM[:HISSE_SAYISI]

    endeks_df = None
    try:
        endeks_df, edurum = veri_al("XU100", gun=FETCH_GUN, min_gun=ayar["min_gun"], aralik=ayar["aralik"])
        print(f"Endeks (XU100): {edurum if endeks_df is not None else 'ÇEKİLEMEDİ'}")
    except Exception as e:
        print(f"Endeks çekilemedi ({e})")

    # Endeks al-tut (aynı pencere mantığı: baslangic → son-5), tek gidiş-dönüş sürtünme
    endeks_altut = None
    if endeks_df is not None and len(endeks_df) > BASLANGIC + 10:
        b = float(endeks_df["Close"].iloc[BASLANGIC])
        s = float(endeks_df["Close"].iloc[-5])
        if b > 0:
            endeks_altut = ((s * (1 - _FR) - b * (1 + _FR)) / (b * (1 + _FR))) * 100

    satirlar = []
    havuz_fazla = []
    tum_islem = tum_kazanan = test_edilen = poz_sembol = 0
    altut_yenen = 0
    strateji_win_list = []
    buyhold_win_list = []

    for idx, kod in enumerate(kodlar, 1):
        try:
            df, _ = veri_al(kod, gun=FETCH_GUN, min_gun=ayar["min_gun"], aralik=ayar["aralik"])
            if df is None or len(df) < BASLANGIC + 25:
                satirlar.append((kod, "veri yetersiz", None)); continue
            r = backtest_calistir(df, ayar, motor, KOD_SEKTOR.get(kod, "Diğer"),
                                  baslangic_gun=BASLANGIC, endeks_df=endeks_df)
            if not r or r.get("islem_sayisi", 0) == 0:
                satirlar.append((kod, "sinyal yok", None)); continue
            test_edilen += 1
            tum_islem += r["islem_sayisi"]; tum_kazanan += r["kazanan"]
            havuz_fazla.extend(r.get("fazla_list", []))
            if r.get("mevduati_yeniyor"): poz_sembol += 1
            if r.get("altut_yeniyor"): altut_yenen += 1
            strateji_win_list.append(r["strateji_window"])
            buyhold_win_list.append(r["buyhold_window"])
            satirlar.append((kod, "ok", r))
            print(f"[{idx}/{len(kodlar)}] {kod}: {r['islem_sayisi']} işlem | "
                  f"strateji %{_fmt(r['strateji_window'])} vs al-tut %{_fmt(r['buyhold_window'])}")
        except Exception as e:
            satirlar.append((kod, f"hata: {e}", None))
            print(f"[{idx}/{len(kodlar)}] {kod}: HATA {e}"); traceback.print_exc()

    # ── ÇITA 1: mevduat (havuz t) ──
    X = np.asarray(havuz_fazla, dtype=float)
    N = int(X.size)
    mu = float(np.mean(X)) if N else 0.0
    sd = float(np.std(X, ddof=1)) if N > 1 else 0.0
    t  = (mu / (sd / np.sqrt(N))) if (N > 1 and sd > 0) else 0.0
    genel_basari = (tum_kazanan / tum_islem * 100) if tum_islem else 0.0
    yeterli_n = N >= N_MIN
    mevduat_edge = yeterli_n and (mu > 0) and (t >= T_ESIK)

    # ── ÇITA 2: al-tut ──
    ort_strateji_win = float(np.mean(strateji_win_list)) if strateji_win_list else 0.0
    ort_buyhold_win = float(np.mean(buyhold_win_list)) if buyhold_win_list else 0.0
    altut_geciyor = ort_strateji_win > ort_buyhold_win
    endeks_geciyor = (endeks_altut is not None) and (ort_strateji_win > endeks_altut)

    # ── RAPOR ──
    L = []
    L.append(f"# APEX — Audit Backtest · {strateji_ad}")
    L.append("")
    L.append(f"_Üretim: {datetime.datetime.now():%Y-%m-%d %H:%M} · vade: {VADE_KEY} · "
             f"maliyet: komisyon+slippage+stop-kayma · iki çıta: mevduat & al-tut_")
    L.append("")

    # ÇITA 2 önce — asıl mahkumiyet/temize çıkış burada
    L.append("## ÇITA 2 — Al-tut benchmark (asıl rakip: BIST-100 al ve tut)")
    L.append("")
    if altut_geciyor and endeks_geciyor:
        L.append(f"**Strateji al-tut'u GEÇİYOR.** Fund getirisi (nakit dahil) ort **%{_fmt(ort_strateji_win)}**; "
                 f"hisse al-tut **%{_fmt(ort_buyhold_win)}**, endeks al-tut **%{_fmt(endeks_altut) if endeks_altut is not None else '—'}**. "
                 f"Timing değer katıyor.")
    else:
        L.append(f"**Strateji al-tut'u YENMİYOR — mevduat kıyasından daha sert mahkumiyet.** "
                 f"Fund getirisi (nakit dahil) ort **%{_fmt(ort_strateji_win)}**, ama hisse al-tut "
                 f"**%{_fmt(ort_buyhold_win)}**" +
                 (f", endeks al-tut **%{_fmt(endeks_altut)}**" if endeks_altut is not None else "") + ". "
                 f"Seçici long-only teknik, yükselen piyasada zamanın çoğunu nakitte geçirip trendi "
                 f"KAÇIRIYOR → kayıp sinyalde değil, timing/execution varsayımında.")
    L.append("")
    L.append(f"- Strateji (fund NAV, nakit dahil) ort. pencere getirisi: **%{_fmt(ort_strateji_win)}**")
    L.append(f"- Hisse al-tut ort. pencere getirisi: **%{_fmt(ort_buyhold_win)}**")
    L.append(f"- Endeks (XU100) al-tut pencere getirisi: **{('%'+_fmt(endeks_altut)) if endeks_altut is not None else '—'}**")
    L.append(f"- Strateji, hisse al-tut'u geçen sembol: **{altut_yenen}/{test_edilen}**")
    L.append("")
    L.append("> Not: Pencere uzun ve yükseliş içeriyorsa al-tut doğal olarak yüksek olur; strateji nakitte "
             "beklediği için geride kalması beklenir. Asıl soru: bu geride kalma kabul edilebilir mi, yoksa "
             "strateji ailesi piyasayı yenemiyor mu? Maliyet (komisyon+slippage+stop kayması) gerçekçi alındı; "
             "edge'i şişirmiyor.")

    # ÇITA 1 — mevduat
    L.append("")
    L.append("## ÇITA 1 — Mevduat (havuz t-istatistiği)")
    L.append("")
    if not yeterli_n:
        L.append(f"**KARAR VERİLEMEZ.** N={N} < {N_MIN}.")
    elif mevduat_edge:
        L.append(f"**Ön elemeyi geçti (kanıt değil).** İşlem başı mevduat-üstü **%{_fmt(mu)}**, t=**{_fmt(t,1)}** (N={N}).")
    else:
        L.append(f"**Mevduatı yenmiyor.** İşlem başı mevduat-üstü **%{_fmt(mu)}**, t=**{_fmt(t,1)}** (N={N}) — "
                 f"|t| eşiğin ({T_ESIK}) altında.")
    L.append("")
    L.append(f"- Test edilen sembol: **{test_edilen}/{len(kodlar)}** · havuz N: **{N}**")
    L.append(f"- Mevduat-üstü pozitif sembol: **{poz_sembol}/{test_edilen}**")
    L.append(f"- Genel başarı (kazanan/işlem): **%{_fmt(genel_basari,1)}**")

    # ── Sembol tablosu ──
    L.append("")
    L.append("## Hisse Bazında")
    L.append("")
    L.append("| Hisse | İşlem | Başarı% | Strateji%(NAV) | Al-tut% | Mevduat-üstü% | Al-tut'u geçti? |")
    L.append("|---|---:|---:|---:|---:|---:|:--:|")

    def _key(t3):
        _, _, r = t3
        return (r["strateji_window"] - r["buyhold_window"]) if r else -1e9

    for kod, durum, r in sorted(satirlar, key=_key, reverse=True):
        if r is None:
            L.append(f"| {kod} | – | – | – | – | – | _{durum}_ |"); continue
        ok = "✓" if r.get("altut_yeniyor") else "✗"
        L.append(f"| {kod} | {r['islem_sayisi']} | {_fmt(r['basari_pct'],1)} | "
                 f"{_fmt(r['strateji_window'])} | {_fmt(r['buyhold_window'])} | "
                 f"{_fmt(r['ort_mevduat_ustu'])} | {ok} |")

    L.append("")
    L.append("---")
    L.append(f"*Strateji: {strateji_ad}. Maliyet: komisyon %{_fmt(0.2,1)}+slippage %0.15 (tek yön), "
             f"stop'ta ekstra %{_fmt(STOP_EKSTRA*100,1)} kayma. Nakitteyken mevduat (~%{int(MEVDUAT_YILLIK*100)}) "
             f"kazanılır (cash drag modeli). Walk-forward, leakage yok. Strateji%(NAV)=nakit dahil fund getirisi.*")

    metin = "\n".join(L)
    with open("BACKTEST_SONUC.md", "w", encoding="utf-8") as f:
        f.write(metin)
    print("\n" + metin)
    print("\n>>> BACKTEST_SONUC.md yazıldı.")


if __name__ == "__main__":
    calistir()
