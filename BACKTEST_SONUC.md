# APEX — Dürüst Backtest Sonucu

*Üretim: 2026-06-27 14:07 · vade: haftalik · komisyon dahil · mevduat kıyası ~%45/yıl*

## SORU: Strateji mevduatı yeniyor mu?

**EVET (bu örneklemde).** Test edilen 18 hissede ortalama, işlem başına mevduatın **%0.75** üstünde; piyasada-iken yıllık ~%2669.0 (mevduat %45).

- Mevduatı yenen hisse: **10/18**
- Toplam işlem: **49** · genel başarı: **%51.0**
- İşlem başı ort. mevduat üstü net getiri: **%0.75**

> Not: "piyasada-iken yıllık" boş/nakit zamanı saymaz — iyimser tavandır. Gerçek performans bunun altındadır. Brüt getiri kâğıt üstünde güzel görünür; asıl gerçeği komisyon-sonrası NET getiri söyler.

## Hisse Bazında

| Hisse | İşlem | Başarı% | Brüt% | Net% | Mevduat üstü% | Yıllık%* | Mevduatı yener? |
|---|---|---|---|---|---|---|---|
| AKBNK | 2 | 50.0 | 2.54 | 2.14 | 1.93 | 2864.0 | ✅ |
| GARAN | 4 | 50.0 | 1.82 | 1.41 | 1.18 | 682.6 | ✅ |
| HALKB | 2 | 100.0 | 9.01 | 8.60 | 8.08 | 41034.5 | ✅ |
| ISCTR | 1 | 0.0 | -3.49 | -3.88 | -4.19 | -99.2 | ❌ |
| VAKBN | 3 | 33.3 | -0.68 | -1.08 | -1.83 | -45.2 | ❌ |
| YKBNK | 3 | 66.7 | 3.51 | 3.10 | 2.01 | 171.2 | ✅ |
| TSKB | 4 | 25.0 | -1.03 | -1.43 | -2.12 | -55.6 | ❌ |
| ALBRK | 2 | 50.0 | 0.13 | -0.27 | -2.03 | -7.1 | ❌ |
| SKBNK | 4 | 75.0 | 3.47 | 3.06 | 2.63 | 1144.2 | ✅ |
| KLNMA | 2 | 50.0 | 1.36 | 0.96 | 0.65 | 202.4 | ✅ |
| EUPWR | — | — | — | — | — | — | _sinyal yok_ |
| ODAS | — | — | — | — | — | — | _sinyal yok_ |
| ENJSA | 2 | 100.0 | 7.26 | 6.84 | 5.77 | 898.1 | ✅ |
| AKSEN | 2 | 0.0 | -4.22 | -4.61 | -4.87 | -99.9 | ❌ |
| ZOREN | 4 | 25.0 | -1.63 | -2.03 | -2.75 | -67.3 | ❌ |
| AYEN | 2 | 50.0 | -0.30 | -0.70 | -1.10 | -51.8 | ❌ |
| AYDEM | 3 | 33.3 | -0.84 | -1.24 | -1.62 | -73.8 | ❌ |
| KCAER | 6 | 66.7 | 3.85 | 3.45 | 2.56 | 293.0 | ✅ |
| CWENE | 1 | 100.0 | 9.53 | 9.11 | 7.78 | 1056.1 | ✅ |
| NATEN | 2 | 50.0 | 2.52 | 2.11 | 1.45 | 196.4 | ✅ |

---
*Komisyon: işlem başına tek yön %0.2 (gidiş-dönüş ~%0.4). Bypass yalnızca backtest=True yolunda — canlı tarama/robot davranışı değişmedi.*