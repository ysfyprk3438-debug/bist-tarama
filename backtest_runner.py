"""
APEX · İLERİ KAĞIT-TEST GÜNLÜĞÜ (forward paper-test logger)
Her koşuda: bugünün reel-faiz rejimini + XU100 seviyesini + duruşu CSV'ye EKLER (dedupe).
Sonra SADECE kayıtlı kararlardan ileri-getiri karnesini yeniden kurar:
  duruş(t) hisse ise t→t+1 endeks getirisi, değilse mevduat getirisi.
Bu, hindsight içermeyen TEK gerçek OOS — backtest taklit eder, bu biriktirir.
DÜRÜST ÇERÇEVE: bu bir DURUŞ/PUSULA göstergesidir, kanıtlanmış zamanlama edge'i DEĞİL.
(plasebo testi rejim-zamanlamasını şanstan ayıramadı; ileri karne zamanla gerçeği söyleyecek.)
NOT: makro_veri.py çeyreklik statik tablodur; her yeni PPK/TÜİK verisinde elle güncellenmeli.
"""
import os, csv, datetime
import numpy as np, pandas as pd
import makro_veri as mk

CSV = "ileri_gunluk.csv"
MD = "ILERI_DURUM.md"
GIR, CIK = -3.0, 3.0   # histerezis bandı: <-3 hisse-lehine, >+3 mevduat-lehine, arası nötr


def duruş(reel, onceki):
    if reel < GIR: return "HİSSE LEHİNE"
    if reel > CIK: return "MEVDUAT LEHİNE"
    return onceki or "MEVDUAT LEHİNE"   # nötr bandda önceki duruşu koru (yoksa temkinli)


def _oku():
    if not os.path.exists(CSV): return []
    with open(CSV, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _yaz(rows):
    with open(CSV, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["tarih", "xu100", "politika", "enflasyon", "reel", "durus"])
        w.writeheader(); w.writerows(rows)


def calistir():
    from veri import veri_al
    xu_df, durum = veri_al("XU100", gun=400, min_gun=30, aralik="1d")
    if xu_df is None or len(xu_df) < 2:
        print("XU100 yok:", durum); return
    veri_tarih = pd.Timestamp(xu_df.index[-1]).date()
    xu_son = float(xu_df["Close"].iloc[-1])
    m = mk.makro_at(veri_tarih)
    if m is None:
        print("makro veri yok (tablo güncel mi?)"); return

    rows = _oku()
    onceki = rows[-1]["durus"] if rows else None
    bugun_durus = duruş(m["reel"], onceki)
    tarih_str = veri_tarih.isoformat()

    if rows and rows[-1]["tarih"] == tarih_str:
        rows[-1] = {"tarih": tarih_str, "xu100": f"{xu_son:.2f}", "politika": f"{m['politika']:.1f}",
                    "enflasyon": f"{m['enflasyon']:.1f}", "reel": f"{m['reel']:+.1f}", "durus": bugun_durus}
        yeni = False
    else:
        rows.append({"tarih": tarih_str, "xu100": f"{xu_son:.2f}", "politika": f"{m['politika']:.1f}",
                     "enflasyon": f"{m['enflasyon']:.1f}", "reel": f"{m['reel']:+.1f}", "durus": bugun_durus})
        yeni = True
    _yaz(rows)

    # ---- İleri karne: SADECE kayıtlı kararlardan yeniden kur ----
    kr = []
    if len(rows) >= 2:
        nav_p = nav_e = nav_m = 1.0
        for i in range(len(rows) - 1):
            d0 = datetime.date.fromisoformat(rows[i]["tarih"]); d1 = datetime.date.fromisoformat(rows[i + 1]["tarih"])
            x0 = float(rows[i]["xu100"]); x1 = float(rows[i + 1]["xu100"])
            pol = float(rows[i]["politika"]); gap = max((d1 - d0).days, 1)
            r_eq = x1 / x0 - 1.0
            r_mv = (1 + pol / 100.0) ** (gap / 365.0) - 1.0
            nav_e *= (1 + r_eq); nav_m *= (1 + r_mv)
            nav_p *= (1 + (r_eq if rows[i]["durus"] == "HİSSE LEHİNE" else r_mv))
        gun = (datetime.date.fromisoformat(rows[-1]["tarih"]) - datetime.date.fromisoformat(rows[0]["tarih"])).days
        kr = [nav_p, nav_e, nav_m, gun]

    # ---- ILERI_DURUM.md ----
    L = ["# APEX — İleri Durum (Rejim Pusulası + Kağıt-Test)", "",
         f"_Son güncelleme: {datetime.datetime.now():%Y-%m-%d %H:%M} · veri tarihi {tarih_str}_", "",
         "## Bugünün duruşu", "",
         f"**Reel faiz: %{m['reel']:+.1f}**  (politika %{m['politika']:.1f} − enflasyon %{m['enflasyon']:.1f})", "",
         f"### → {bugun_durus}", "",
         "> Bu bir **duruş göstergesidir, kâhin değil.** Plasebo testi, reel-faiz rejiminin zamanlama "
         "becerisini şanstan ayıramadı — yani bu duruşu 'kanıtlanmış edge' değil, 'rejim-farkında temkin' "
         "olarak oku. Aşağıdaki ileri karne, zamanla gerçeği söyleyecek tek şeydir.", ""]
    if kr:
        nav_p, nav_e, nav_m, gun = kr
        kazanan = max([("Duruş", nav_p), ("Al-tut endeks", nav_e), ("Mevduat", nav_m)], key=lambda x: x[1])
        L += [f"## İleri karne — {gun} gündür biriken GERÇEK OOS", "",
              "| | Getiri |", "|---|---:|",
              f"| **Duruş stratejisi** | {(nav_p-1)*100:+.1f}% |",
              f"| Al-tut endeks | {(nav_e-1)*100:+.1f}% |",
              f"| Mevduat | {(nav_m-1)*100:+.1f}% |", "",
              f"_Şu ana dek önde: **{kazanan[0]}**. Bu sayılar her koşuda, sadece geçmişte kaydedilen "
              f"duruşlardan hesaplanır — geriye dönük düzeltme yok._", ""]
    else:
        L += ["## İleri karne", "",
              "_İlk kayıt alındı. Karne için en az 2 kayıt ve biraz zaman gerekiyor. "
              "Günlüğü düzenli çalıştırdıkça gerçek ileri-getiri burada birikecek._", ""]
    L += [f"## Günlük ({len(rows)} kayıt)", "",
          "| Tarih | XU100 | Reel % | Duruş |", "|---|---:|---:|---|"]
    for r in rows[-30:]:
        L.append(f"| {r['tarih']} | {float(r['xu100']):,.0f} | {r['reel']} | {r['durus']} |")
    L += ["", "---", "*makro_veri.py çeyreklik statik tablodur; yeni PPK/TÜİK verisinde güncellenmeli. "
          "Duruş = reel faiz histerezisi (gir<-3, çık>+3, nötr→önceki).*"]
    with open(MD, "w", encoding="utf-8") as f:
        f.write("\n".join(L))
    print(f"{'YENİ kayıt' if yeni else 'kayıt güncellendi'}: {tarih_str} · reel %{m['reel']:+.1f} · {bugun_durus}")
    print(f"Toplam {len(rows)} kayıt. ILERI_DURUM.md + {CSV} yazıldı.")


if __name__ == "__main__":
    calistir()
