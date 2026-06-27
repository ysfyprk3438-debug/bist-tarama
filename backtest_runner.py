"""
APEX · TEMEL FAKTÖR DOĞRULAMA SONDASI (v8.1)
temel_veri.py'nin gerçek İş Yatırım verisinde doğru faktör (ROE, YoY kâr) ürettiğini
ve point-in-time'ın GEÇMİŞTE de çalıştığını kanıtlar. Büyük backtest'ten önce son kontrol.
~1-2 dk. Çıktıyı görünce 94-hisse temel-seçim backtest'ini kurarız.
"""
import datetime
import temel_veri as tv

HISSELER = ["EREGL", "GARAN", "ASELS", "THYAO", "BIMAS", "AKBNK", "SISE", "TUPRS"]


def calistir():
    bugun = datetime.date.today()
    L = ["# APEX — Temel Faktör Doğrulama", "",
         f"_{datetime.datetime.now():%Y-%m-%d %H:%M} · temel_veri.py gerçek-veri testi_", ""]

    # 1) BUGÜN itibarıyla faktörler
    L.append("## 1) Bugün itibarıyla temel faktörler (point-in-time)")
    L.append("")
    L.append("| Hisse | Tip | Net Kâr (küm.) | Özkaynak | ROE (küm.)% | YoY Kâr% |")
    L.append("|---|---|---:|---:|---:|---:|")
    basarili = 0
    for kod in HISSELER:
        try:
            f = tv.faktor_hesapla(kod, bugun)
        except Exception as e:
            L.append(f"| {kod} | HATA | {type(e).__name__} | | | |"); continue
        if not f:
            L.append(f"| {kod} | — | veri yok | | | |"); continue
        basarili += 1
        nk = f"{f['net_kar']/1e9:,.2f} mlr" if f['net_kar'] else "—"
        oz = f"{f['ozkaynak']/1e9:,.2f} mlr" if f['ozkaynak'] else "—"
        roe = f"{f['roe']*100:,.1f}" if f['roe'] is not None else "—"
        yoy = f"{f['kar_yoy']*100:,.0f}" if f['kar_yoy'] is not None else "—"
        L.append(f"| {kod} | {f['tip']} | {nk} | {oz} | {roe} | {yoy} |")
    L.append("")
    L.append(f"_{basarili}/{len(HISSELER)} hisse faktör üretti._")
    L.append("")

    # 2) POINT-IN-TIME GEÇMİŞ KANITI: aynı hisse, farklı tarihlerde farklı veri
    L.append("## 2) Point-in-time kanıtı — geçmiş tarihte de çalışıyor mu?")
    L.append("")
    L.append("Aynı hisse (EREGL), farklı tarihlerde o gün AÇIKLANMIŞ veriyle:")
    L.append("")
    L.append("| Tarih | Açıklanmış son çeyrek | Net Kâr (küm.) | ROE% |")
    L.append("|---|---|---:|---:|")
    for t in [datetime.date(2022, 6, 1), datetime.date(2023, 6, 1),
              datetime.date(2024, 6, 1), datetime.date(2025, 6, 1)]:
        try:
            dons = tv.mevcut_donemler(t, geri=4)
            son_ceyrek = f"{dons[0][0]}/Q{dons[0][1]//3}" if dons else "—"
            f = tv.faktor_hesapla("EREGL", t)
            if f:
                nk = f"{f['net_kar']/1e9:,.2f} mlr"
                roe = f"{f['roe']*100:,.1f}"
                L.append(f"| {t} | {son_ceyrek} | {nk} | {roe} |")
            else:
                L.append(f"| {t} | {son_ceyrek} | veri yok | — |")
        except Exception as e:
            L.append(f"| {t} | HATA {type(e).__name__} | | |")
    L.append("")
    L.append("> Farklı tarihlerde farklı çeyrek/sayı görünüyorsa, geçmiş point-in-time çalışıyor demektir — "
             "temel-seçim backtest'i kurabiliriz.")
    L.append("")
    L.append("---\n*Sonraki: bu faktörlerle 94-hisse top-N temel-seçim backtest'i (OOS + maliyet + mevduat çıtası).*")

    metin = "\n".join(L)
    with open("BACKTEST_SONUC.md", "w", encoding="utf-8") as f:
        f.write(metin)
    print(metin); print("\n>>> yazıldı.")


if __name__ == "__main__":
    calistir()
