"""
═══════════════════════════════════════════════════════════════
APEX · DÜRÜST BACKTEST KOŞUCUSU
═══════════════════════════════════════════════════════════════
Tek soruyu dürüstçe yanıtlar: "Bu strateji, komisyon düşülünce,
mevduat faizini (~%45/yıl) yeniyor mu?"

- Tazelik filtresi backtest=True ile bypass edilir (canlı yol DEĞİŞMEZ).
- Her işleme gidiş-dönüş komisyon uygulanır.
- Her işlem, tutulduğu gün kadar mevduata karşı kıyaslanır.
- Sonuç BACKTEST_SONUC.md olarak yazılır (GitHub'da commit edilir).

GitHub Actions içinde çalışır (orada internet + canlı veri var).
Yerelde de çalışır: python backtest_runner.py
"""
import datetime
import traceback

VADE_KEY = "haftalik"     # swing — ana strateji vadesi
FETCH_GUN = 400           # backtest'e yeterince geçmiş (≈270 işlem günü)
BASLANGIC = 120           # ilk 120 günü ısınma olarak bırak
HISSE_SAYISI = 20         # likit ilk N hisse (hız için)


def _fmt(x, n=2):
    try:
        return f"{x:.{n}f}"
    except Exception:
        return str(x)


def calistir():
    from veri import veri_al, VADE_AYAR
    from analiz import analiz_et
    from backtest import backtest_calistir
    from tarama_core import BIST_TUM, KOD_SEKTOR

    ayar = VADE_AYAR[VADE_KEY]
    kodlar = BIST_TUM[:HISSE_SAYISI]

    satirlar = []        # her hisse için sonuç
    tum_islem = 0
    tum_kazanan = 0
    fazla_list = []      # hisse bazında ort. mevduat üstü
    yillik_list = []
    yenen = 0
    test_edilen = 0

    for kod in kodlar:
        try:
            df, _ = veri_al(kod, gun=FETCH_GUN, min_gun=ayar["min_gun"], aralik=ayar["aralik"])
            if df is None or len(df) < BASLANGIC + 25:
                satirlar.append((kod, "veri yetersiz", None))
                continue
            r = backtest_calistir(df, ayar, analiz_et,
                                  KOD_SEKTOR.get(kod, "Diğer"), baslangic_gun=BASLANGIC)
            if not r or r.get("islem_sayisi", 0) == 0:
                satirlar.append((kod, "sinyal yok", None))
                continue

            test_edilen += 1
            tum_islem += r["islem_sayisi"]
            tum_kazanan += r["kazanan"]
            fazla_list.append(r["ort_mevduat_ustu"])
            yillik_list.append(r["strateji_yillik"])
            if r["mevduati_yeniyor"]:
                yenen += 1
            satirlar.append((kod, "ok", r))
        except Exception as e:
            satirlar.append((kod, f"hata: {e}", None))
            traceback.print_exc()

    # ── Özet ──
    import numpy as np
    ort_fazla = float(np.mean(fazla_list)) if fazla_list else 0.0
    ort_yillik = float(np.mean(yillik_list)) if yillik_list else -100.0
    genel_basari = (tum_kazanan / tum_islem * 100) if tum_islem else 0.0
    genel_verdikt = (ort_fazla > 0 and ort_yillik > 45)

    L = []
    L.append("# APEX — Dürüst Backtest Sonucu")
    L.append("")
    L.append(f"*Üretim: {datetime.datetime.now():%Y-%m-%d %H:%M} · vade: {VADE_KEY} · "
             f"komisyon dahil · mevduat kıyası ~%45/yıl*")
    L.append("")
    L.append("## SORU: Strateji mevduatı yeniyor mu?")
    L.append("")
    if genel_verdikt:
        L.append(f"**EVET (bu örneklemde).** Test edilen {test_edilen} hissede ortalama, "
                 f"işlem başına mevduatın **%{_fmt(ort_fazla)}** üstünde; "
                 f"piyasada-iken yıllık ~%{_fmt(ort_yillik,1)} (mevduat %45).")
    else:
        L.append(f"**HAYIR (bu örneklemde).** Test edilen {test_edilen} hissede ortalama, "
                 f"işlem başına mevduatın **%{_fmt(ort_fazla)}** "
                 f"{'üstünde' if ort_fazla>0 else 'ALTINDA'}; "
                 f"piyasada-iken yıllık ~%{_fmt(ort_yillik,1)} (mevduat %45). "
                 f"Komisyon + mevduat eşiği birlikte, stratejinin kanıtlanmış bir edge'i "
                 f"olmadığını gösteriyor — teşhisle uyumlu.")
    L.append("")
    L.append(f"- Mevduatı yenen hisse: **{yenen}/{test_edilen}**")
    L.append(f"- Toplam işlem: **{tum_islem}** · genel başarı: **%{_fmt(genel_basari,1)}**")
    L.append(f"- İşlem başı ort. mevduat üstü net getiri: **%{_fmt(ort_fazla)}**")
    L.append("")
    L.append("> Not: \"piyasada-iken yıllık\" boş/nakit zamanı saymaz — iyimser tavandır. "
             "Gerçek performans bunun altındadır. Brüt getiri kâğıt üstünde güzel görünür; "
             "asıl gerçeği komisyon-sonrası NET getiri söyler.")
    L.append("")
    L.append("## Hisse Bazında")
    L.append("")
    L.append("| Hisse | İşlem | Başarı% | Brüt% | Net% | Mevduat üstü% | Yıllık%* | Mevduatı yener? |")
    L.append("|---|---|---|---|---|---|---|---|")
    for kod, durum, r in satirlar:
        if r is None:
            L.append(f"| {kod} | — | — | — | — | — | — | _{durum}_ |")
            continue
        L.append(
            f"| {kod} | {r['islem_sayisi']} | {_fmt(r['basari_pct'],1)} | "
            f"{_fmt(r['ort_brut'])} | {_fmt(r['ort_getiri'])} | {_fmt(r['ort_mevduat_ustu'])} | "
            f"{_fmt(r['strateji_yillik'],1)} | {'✅' if r['mevduati_yeniyor'] else '❌'} |"
        )
    L.append("")
    L.append("---")
    L.append("*Komisyon: işlem başına tek yön %0.2 (gidiş-dönüş ~%0.4). "
             "Bypass yalnızca backtest=True yolunda — canlı tarama/robot davranışı değişmedi.*")

    metin = "\n".join(L)
    with open("BACKTEST_SONUC.md", "w", encoding="utf-8") as f:
        f.write(metin)
    print(metin)
    print("\n>>> BACKTEST_SONUC.md yazıldı.")


if __name__ == "__main__":
    calistir()
