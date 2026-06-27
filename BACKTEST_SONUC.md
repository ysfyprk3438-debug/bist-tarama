# APEX — Makro Rejim Backtest (Reel Faiz Anahtarı)

_2026-06-27 21:57 · XU100 · 8.0 yıl · mevduat ZAMANA GÖRE değişen gerçek faiz · histerezis (-3.0/3.0)_

## Reel-faiz rejimi: boom'da hissede, kuraklıkta mevduatta?

| Dönem | Makro Rejim | Statik Mevduat | Sabit %45 | Endeks | Rejim>mev&end? |
|---|---:|---:|---:|---:|:--:|
| İlk yarı (IS) | 3.14 | 1.86 | 4.39 | 2.45 | ✅ |
| İkinci yarı (OOS) | 6.48 | 3.01 | 4.40 | 5.80 | ✅ |
| TÜM dönem | 20.48 | 5.61 | 19.32 | 14.28 | ✅ |

_Makro rejim: 2 geçiş · %56 zaman hissede · MaxDD %-22.9_

## Karar

**Makro rejim HER İKİ yarıda mevduatı+endeksi geçti.** Reel faiz işareti, boom'da hisseye girip kuraklıkta mevduata kaçarak gerçek bir edge üretiyor — gecenin ilk OOS-sağlam sonucu. Sonraki: hissedeyken endeks yerine temel-seçim/momentum koy (alfa üstüne alfa), eşik duyarlılığı, ileri test.

> Mevduat artık sabit %45 değil, o dönemin gerçek faizi (2020-21'de ~%12, 2024-25'te ~%45-50). Bu, boom'da hisseyi haksız cezalandıran eski varsayımı düzeltir.

---
*Reel faiz = politika faizi − yıllık enflasyon (statik kaynaklı tablo). Karar t, getiri t+1; enflasyon ~1 ay gecikmeli — leakage yok.*