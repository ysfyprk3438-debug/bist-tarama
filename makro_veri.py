"""
APEX · MAKRO VERİ (statik, kaynaklı) — TCMB politika faizi + yıllık TÜFE enflasyonu
EVDS coğrafi engeli yüzünden statik tablo (kamuya açık kaynaklardan, çeyreklik).
Reel faiz = politika faizi − yıllık enflasyon. Rejim sinyali bundan türetilir.
Değerler yaklaşıktır ama rejim İŞARETİ (negatif/pozitif) için fazlasıyla yeterli
(reel faiz −%60 ile +%10 arası salınıyor; birkaç puan hata işareti değiştirmez).
Kaynaklar: TCMB PPK kararları, TÜİK TÜFE, tradingeconomics/macrotrends.
"""
import datetime

# (yıl, çeyrek): (politika_faizi_%, yıllık_enflasyon_%)  — çeyrek sonu itibarıyla
MAKRO = {
    (2017, 1): (9.0, 11.3),  (2017, 2): (11.0, 10.9), (2017, 3): (12.0, 11.2), (2017, 4): (12.75, 11.9),
    (2018, 1): (12.75, 10.2),(2018, 2): (17.75, 15.4),(2018, 3): (24.0, 24.5), (2018, 4): (24.0, 20.3),
    (2019, 1): (24.0, 19.7), (2019, 2): (24.0, 15.7), (2019, 3): (16.5, 9.3),  (2019, 4): (12.0, 11.8),
    (2020, 1): (9.75, 11.9), (2020, 2): (8.25, 12.6), (2020, 3): (10.25, 11.8),(2020, 4): (17.0, 14.6),
    (2021, 1): (19.0, 16.2), (2021, 2): (19.0, 17.5), (2021, 3): (18.0, 19.6), (2021, 4): (14.0, 36.1),
    (2022, 1): (14.0, 61.1), (2022, 2): (14.0, 78.6), (2022, 3): (13.0, 83.5), (2022, 4): (9.0, 64.3),
    (2023, 1): (8.5, 50.5),  (2023, 2): (15.0, 38.2), (2023, 3): (30.0, 61.5), (2023, 4): (42.5, 64.8),
    (2024, 1): (50.0, 68.5), (2024, 2): (50.0, 71.6), (2024, 3): (50.0, 49.4), (2024, 4): (47.5, 44.4),
    (2025, 1): (42.5, 39.0), (2025, 2): (46.0, 35.4), (2025, 3): (40.5, 33.0), (2025, 4): (38.0, 31.5),
    (2026, 1): (37.0, 32.5), (2026, 2): (37.0, 33.0),
}


def _ceyrek_sonu(yil, ceyrek):
    ay = {1: 3, 2: 6, 3: 9, 4: 12}[ceyrek]
    return datetime.date(yil, ay, 28)


def makro_at(tarih, lag_gun=35):
    """tarih itibarıyla AÇIKLANMIŞ son çeyreğin (politika, enflasyon, reel) değeri.
       lag: enflasyon ~1 ay gecikmeli açıklanır → çeyrek sonu + lag geçmeden kullanma."""
    if isinstance(tarih, datetime.datetime):
        tarih = tarih.date()
    en_iyi = None
    for (yil, c), (pol, enf) in MAKRO.items():
        mevcut = _ceyrek_sonu(yil, c) + datetime.timedelta(days=lag_gun)
        if mevcut <= tarih:
            if en_iyi is None or mevcut > en_iyi[0]:
                en_iyi = (mevcut, pol, enf)
    if en_iyi is None:
        return None
    _, pol, enf = en_iyi
    return {"politika": pol, "enflasyon": enf, "reel": pol - enf}


if __name__ == "__main__":
    # reel faiz yolunu yazdır (doğrulama)
    for yil in range(2018, 2027):
        for c in [2, 4]:
            t = _ceyrek_sonu(yil, c) + datetime.timedelta(days=40)
            m = makro_at(t)
            if m:
                rej = "HİSSE" if m["reel"] < 0 else "MEVDUAT"
                print(f"{yil}-Ç{c}: politika %{m['politika']:.1f} enf %{m['enflasyon']:.1f} "
                      f"→ reel %{m['reel']:+.1f} → {rej}")
