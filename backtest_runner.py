"""
═══════════════════════════════════════════════════════════════
APEX · DÜRÜST BACKTEST KOŞUCUSU  (v5 — ÇOK VADELİ karşılaştırma)
═══════════════════════════════════════════════════════════════
Vizyon: sistem her fırsatı en uygun vadede değerlendirsin (gün içi /
günlük / haftalık). İLK ADIM: üç vadeyi de AYRI ÖLÇ, hangisinde
al-tut'u/mevduatı yenen bir edge var gör. Para ayırmadan önce kanıt.

Her vade kendi penceresinde, kendi al-tut'una karşı kıyaslanır.
Maliyet gerçekçi (komisyon+slippage+stop kayma). Walk-forward, leakage yok.

UYARILAR:
 - Gün içi (15dk): veri ~son 60 günle sınırlı (Yahoo). Kısa rejim penceresi.
 - Gün içi 15dk GECİKMEYİ modellemez → canlı için İYİMSER. Edge görünürse
   sonraki adım: 1-bar geç giriş ekleyip yeniden ölç.
"""

import datetime
import traceback
import numpy as np

STRATEJI    = "hibrit"
VADE_LISTE  = ["gun_ici", "gunluk", "haftalik"]
BASLANGIC   = 120
HISSE_SAYISI = 0
T_ESIK      = 2.0
N_MIN       = 100


def _fmt(x, n=2):
    try:
        return f"{x:.{n}f}"
    except Exception:
        return str(x)


def _fetch_gun(ayar):
    # 15dk veri Yahoo'da ~60 günle sınırlı; günlük vadelerde uzun geçmiş
    return 59 if ayar.get("aralik") == "15m" else 1500


def _vade_calistir(vkey, motor, veri_al, VADE_AYAR, backtest_calistir, KOD_SEKTOR, BIST_TUM):
    from backtest import _FR
    ayar = VADE_AYAR[vkey]
    fg = _fetch_gun(ayar)
    kodlar = BIST_TUM if HISSE_SAYISI <= 0 else BIST_TUM[:HISSE_SAYISI]

    endeks_df = None
    try:
        endeks_df, _ = veri_al("XU100", gun=fg, min_gun=ayar["min_gun"], aralik=ayar["aralik"])
    except Exception:
        pass
    endeks_altut = None
    if endeks_df is not None and len(endeks_df) > BASLANGIC + 10:
        b = float(endeks_df["Close"].iloc[BASLANGIC]); s = float(endeks_df["Close"].iloc[-5])
        if b > 0:
            endeks_altut = ((s * (1 - _FR) - b * (1 + _FR)) / (b * (1 + _FR))) * 100

    havuz = []; s_win = []; b_win = []
    test_edilen = altut_yenen = 0
    for idx, kod in enumerate(kodlar, 1):
        try:
            df, _ = veri_al(kod, gun=fg, min_gun=ayar["min_gun"], aralik=ayar["aralik"])
            if df is None or len(df) < BASLANGIC + 25:
                continue
            r = backtest_calistir(df, ayar, motor, KOD_SEKTOR.get(kod, "Diğer"),
                                  baslangic_gun=BASLANGIC, endeks_df=endeks_df)
            if not r or r.get("islem_sayisi", 0) == 0:
                continue
            test_edilen += 1
            havuz.extend(r.get("fazla_list", []))
            s_win.append(r["strateji_window"]); b_win.append(r["buyhold_window"])
            if r.get("altut_yeniyor"):
                altut_yenen += 1
        except Exception as e:
            print(f"  {vkey}/{kod}: HATA {e}")

    X = np.asarray(havuz, dtype=float)
    N = int(X.size)
    mu = float(np.mean(X)) if N else 0.0
    sd = float(np.std(X, ddof=1)) if N > 1 else 0.0
    t = (mu / (sd / np.sqrt(N))) if (N > 1 and sd > 0) else 0.0
    return {
        "vade": vkey, "ad": ayar["ad"], "aralik": ayar.get("aralik"),
        "N": N, "mu": mu, "t": t, "test_edilen": test_edilen,
        "strateji_win": float(np.mean(s_win)) if s_win else 0.0,
        "buyhold_win": float(np.mean(b_win)) if b_win else 0.0,
        "endeks_altut": endeks_altut, "altut_yenen": altut_yenen,
    }


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

    sonuclar = []
    for vkey in VADE_LISTE:
        print(f"\n=== VADE: {vkey} ===")
        try:
            s = _vade_calistir(vkey, motor, veri_al, VADE_AYAR, backtest_calistir, KOD_SEKTOR, BIST_TUM)
            sonuclar.append(s)
            print(f"  N={s['N']} mu={_fmt(s['mu'])} t={_fmt(s['t'],1)} "
                  f"strateji={_fmt(s['strateji_win'])} al-tut={_fmt(s['buyhold_win'])}")
        except Exception as e:
            print(f"  VADE HATA {vkey}: {e}"); traceback.print_exc()

    # ── RAPOR ──
    L = []
    L.append(f"# APEX — Çok Vadeli Audit · {strateji_ad}")
    L.append("")
    L.append(f"_Üretim: {datetime.datetime.now():%Y-%m-%d %H:%M} · maliyet: komisyon+slippage+stop-kayma · "
             f"her vade KENDİ penceresi & KENDİ al-tut'una karşı_")
    L.append("")
    L.append("## Vade Karşılaştırması (hangi vadede edge var?)")
    L.append("")
    L.append("| Vade | Aralık | N | Mevduat-üstü% | t | Strateji(NAV)% | Al-tut% | Endeks al-tut% | Al-tut'u geçen |")
    L.append("|---|---|---:|---:|---:|---:|---:|---:|:--:|")
    for s in sonuclar:
        ea = _fmt(s["endeks_altut"]) if s["endeks_altut"] is not None else "—"
        L.append(f"| {s['ad']} | {s['aralik']} | {s['N']} | {_fmt(s['mu'])} | {_fmt(s['t'],1)} | "
                 f"{_fmt(s['strateji_win'])} | {_fmt(s['buyhold_win'])} | {ea} | "
                 f"{s['altut_yenen']}/{s['test_edilen']} |")
    L.append("")

    # Manşet: herhangi bir vade her iki çıtayı da geçiyor mu?
    kazanan = []
    for s in sonuclar:
        mevduat_ok = (s["N"] >= N_MIN) and (s["mu"] > 0) and (s["t"] >= T_ESIK)
        altut_ok = s["strateji_win"] > s["buyhold_win"]
        if mevduat_ok and altut_ok:
            kazanan.append(s["ad"])
    L.append("## Karar")
    L.append("")
    if kazanan:
        L.append(f"**Edge sinyali olan vade(ler): {', '.join(kazanan)}** — hem mevduatı (t≥{T_ESIK}) "
                 f"hem al-tut'u geçti. KANIT değil, ön eleme. Sonraki: out-of-sample + (gün içiyse) "
                 f"15dk gecikme modeli.")
    else:
        L.append("**Hiçbir vade her iki çıtayı geçemedi.** Hiçbiri al-tut'u + mevduatı birlikte yenmiyor. "
                 "Yani 'doğru vadeyi seç' yaklaşımı tek başına edge üretmiyor — sorun vade seçimi değil, "
                 "sinyal ailesi. Sonraki kaldıraç: farklı alfa kaynağı (fundamental/makro veya order-flow) "
                 "ya da 'al-tut'a yakın kal' (daha az gir-çık) varyantı.")
    L.append("")
    L.append("> Not: Gün içi (15dk) penceresi ~60 günle sınırlı (Yahoo) ve 15dk GECİKMEYİ modellemez → "
             "canlı için İYİMSER. Eğer gün içi edge gösterirse, bir bar geç giriş ekleyip yeniden ölçeceğiz.")
    L.append("")
    L.append("---")
    L.append(f"*Strateji: {strateji_ad}. Komisyon %0.2+slippage %0.15 (tek yön), stop ekstra "
             f"%{_fmt(STOP_EKSTRA*100,1)}. Nakitte mevduat (~%{int(MEVDUAT_YILLIK*100)}). "
             f"Walk-forward, leakage yok.*")

    metin = "\n".join(L)
    with open("BACKTEST_SONUC.md", "w", encoding="utf-8") as f:
        f.write(metin)
    print("\n" + metin)
    print("\n>>> BACKTEST_SONUC.md yazıldı.")


if __name__ == "__main__":
    calistir()
