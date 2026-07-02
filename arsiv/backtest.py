"""
═══════════════════════════════════════════════════════════════
BACKTEST v4 — DÜRÜST ÖLÇÜM ALETİ (audit'lenmiş)
═══════════════════════════════════════════════════════════════
Bu sürüm 4 audit sorusunu tek koşuda yanıtlar:
  (1) Look-ahead/leakage   → walk-forward (sinyal df[:i], sonuç i'den sonra). TEMİZ.
  (2) Komisyon + SLIPPAGE  → komisyon + kayma + stop'larda ekstra kötüleşme.
                              (Önceki sürüm çıkışı tam fiyattan dolduruyordu = iyimser.)
  (3) Al-tut benchmark     → strateji vs hisse al-tut vs endeks al-tut.
  (4) Timing/cash drag     → fund-NAV: nakitte beklenen gün mevduat kazanır;
                              böylece "trendi nakitte kaçırma" kaybı ölçülür.
"""

import numpy as np

# ── Dürüst ölçüm sabitleri (hepsi tunable) ──
KOMISYON_ORANI = 0.002      # işlem başına tek yön (%0.2)
SLIPAJ_ORANI   = 0.0015     # tek yön piyasa etkisi/kayma (%0.15)
STOP_EKSTRA    = 0.003      # stop dolumlarında ekstra kötüleşme (%0.3 — gap/kayma)
MEVDUAT_YILLIK = 0.45       # ~%45/yıl — nakit getirisi + kıyas ölçütü

_FR = KOMISYON_ORANI + SLIPAJ_ORANI                 # tek yön toplam sürtünme
_MEVDUAT_GUNLUK = (1 + MEVDUAT_YILLIK) ** (1/365.0) - 1


def backtest_calistir(df, vade_ayar, analiz_fonk, sektor="Test", baslangic_gun=120, endeks_df=None):
    """
    Walk-forward backtest + slippage + al-tut benchmark + cash-drag fund NAV.
    Dönen: özet (fazla_list, strateji_window, buyhold_window, ... dahil).
    """
    if df is None or len(df) < baslangic_gun + 20:
        return None

    islemler = []
    cash_gun = 0                 # sinyal olmayan (nakitte beklenen) gün sayısı
    i = baslangic_gun
    son_idx = len(df) - 5

    while i < son_idx:
        gecmis_df = df.iloc[:i].copy()
        endeks_slice = None
        if endeks_df is not None and "Close" in endeks_df:
            son_tarih = gecmis_df.index[-1]
            es = endeks_df["Close"].loc[:son_tarih]
            endeks_slice = es if len(es) >= 50 else None
        r = analiz_fonk("BT", gecmis_df, vade_ayar, 100000, 1.0, sektor,
                        detayli=False, backtest=True, endeks_close=endeks_slice)

        if r is None:
            cash_gun += 1        # bu gün nakitte beklendi
            i += 1
            continue

        giris = r["son"]; hedef = r["hedef"]; stop = r["stop"]
        sonuc = None; cikis_fiyat = giris; gun_sayisi = 0
        for j in range(i, min(i + 30, len(df))):
            gun = df.iloc[j]; gun_sayisi = j - i + 1
            if gun["Low"] <= stop:
                sonuc = "STOP"; cikis_fiyat = stop; break
            if gun["High"] >= hedef:
                sonuc = "HEDEF"; cikis_fiyat = hedef; break
        if sonuc is None:
            sonuc = "AÇIK"; cikis_fiyat = float(df.iloc[min(i + 30, len(df) - 1)]["Close"])

        # ── GERÇEKÇİ MALİYET: komisyon + slippage (+ stop'ta ekstra) ──
        brut_pct = ((cikis_fiyat - giris) / giris) * 100
        giris_eff = giris * (1 + _FR)
        ham_cikis = cikis_fiyat * (1 - STOP_EKSTRA) if sonuc == "STOP" else cikis_fiyat
        cikis_eff = ham_cikis * (1 - _FR)
        getiri_pct = ((cikis_eff - giris_eff) / giris_eff) * 100

        islemler.append({"sonuc": sonuc, "getiri_pct": getiri_pct,
                         "brut_pct": brut_pct, "gun": gun_sayisi})
        i += max(gun_sayisi, 1)

    if not islemler:
        return {"islem_sayisi": 0, "fazla_list": []}

    getiriler = [x["getiri_pct"] for x in islemler]
    kazanan = [x for x in islemler if x["getiri_pct"] > 0]

    # İşlemlerin bileşik getirisi (sadece piyasadayken)
    bilesik = 1.0
    for g in getiriler:
        bilesik *= (1 + g / 100)
    bilesik_pct = (bilesik - 1) * 100

    # ── MEVDUAT KIYASI (işlem başına) ──
    fazlalar = []
    for x in islemler:
        gun = max(x["gun"], 1)
        mevduat_pct = ((1 + MEVDUAT_YILLIK) ** (gun / 365.0) - 1) * 100
        fazlalar.append(x["getiri_pct"] - mevduat_pct)
    ort_fazla = float(np.mean(fazlalar))
    std_fazla = float(np.std(fazlalar)) if len(fazlalar) > 1 else 0.0
    fazla_sharpe = (ort_fazla / std_fazla) if std_fazla > 0 else 0.0
    toplam_gun = sum(max(x["gun"], 1) for x in islemler)

    # ── FUND NAV: nakitte beklenen günler mevduat kazanır (cash drag dahil) ──
    nakit_buyume = (1 + _MEVDUAT_GUNLUK) ** cash_gun
    strateji_nav = bilesik * nakit_buyume           # piyasadayken işlem + nakitteyken mevduat
    strateji_window_pct = (strateji_nav - 1) * 100

    # ── AL-TUT BENCHMARK (aynı pencere, tek gidiş-dönüş sürtünme) ──
    bas = float(df.iloc[baslangic_gun]["Close"])
    sonf = float(df.iloc[son_idx - 1]["Close"])
    if bas > 0:
        bh_giris = bas * (1 + _FR); bh_cikis = sonf * (1 - _FR)
        buyhold_window_pct = ((bh_cikis - bh_giris) / bh_giris) * 100
    else:
        buyhold_window_pct = 0.0

    # Şişik referans (karar dışı)
    if toplam_gun > 0 and bilesik > 0:
        strateji_yillik = ((bilesik) ** (365.0 / toplam_gun) - 1) * 100
    else:
        strateji_yillik = -100.0

    return {
        "islem_sayisi": len(islemler),
        "kazanan": len(kazanan),
        "kaybeden": len(islemler) - len(kazanan),
        "basari_pct": len(kazanan) / len(islemler) * 100,
        "ort_getiri": np.mean(getiriler),
        "ort_brut": np.mean([x["brut_pct"] for x in islemler]),
        "toplam_bilesik": bilesik_pct,
        "ort_gun": np.mean([x["gun"] for x in islemler]),
        # mevduat kıyası
        "ort_mevduat_ustu": ort_fazla,
        "mevduat_ustu_sharpe": fazla_sharpe,
        "strateji_yillik": strateji_yillik,
        "mevduati_yeniyor": (ort_fazla > 0),
        "fazla_list": fazlalar,
        # ── audit: benchmark + cash drag ──
        "strateji_window": strateji_window_pct,    # fund NAV (nakit dahil) pencere getirisi
        "buyhold_window": buyhold_window_pct,       # hisse al-tut pencere getirisi
        "cash_gun": cash_gun,
        "piyasa_gun": toplam_gun,
        "altut_yeniyor": (strateji_window_pct > buyhold_window_pct),
    }


# ══════════════════════════════════════════════════════════════
# SEKTÖR ISI HARİTASI
# ══════════════════════════════════════════════════════════════
def sektor_isi(sonuclar):
    sektorler = {}
    for r in sonuclar:
        sek = r["sektor"]
        if sek not in sektorler:
            sektorler[sek] = {"sektor": sek, "adet": 0, "toplam_puan": 0,
                              "toplam_ap": 0, "buyuk_oyuncu": 0, "kazanc_top": 0}
        s = sektorler[sek]
        s["adet"] += 1
        s["toplam_puan"] += r["puan"]
        s["toplam_ap"] += r["sm"]["skor"]
        s["kazanc_top"] += r["kazanc_pct"]
        if r["sm"]["buyuk_oyuncu"]:
            s["buyuk_oyuncu"] += 1
    liste = []
    for sek, s in sektorler.items():
        adet = s["adet"]
        ort_puan = s["toplam_puan"] / adet
        ort_ap = s["toplam_ap"] / adet
        guc = adet * 5 + ort_puan * 0.5 + ort_ap * 0.3 + s["buyuk_oyuncu"] * 8
        liste.append({"sektor": sek, "adet": adet, "ort_puan": ort_puan,
                      "ort_ap": ort_ap, "buyuk_oyuncu": s["buyuk_oyuncu"],
                      "ort_kazanc": s["kazanc_top"] / adet, "guc": guc})
    liste.sort(key=lambda x: x["guc"], reverse=True)
    return liste


def isi_renk(guc, max_guc):
    if max_guc <= 0:
        return "#1E293B"
    oran = guc / max_guc
    if oran >= 0.8: return "#10B981"
    elif oran >= 0.6: return "#34D399"
    elif oran >= 0.4: return "#F59E0B"
    elif oran >= 0.2: return "#FB923C"
    else: return "#64748B"
