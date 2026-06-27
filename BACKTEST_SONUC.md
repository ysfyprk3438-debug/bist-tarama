# APEX — Temel Faktör Doğrulama

_2026-06-27 20:38 · temel_veri.py gerçek-veri testi_

## 1) Bugün itibarıyla temel faktörler (point-in-time)

| Hisse | Tip | Net Kâr (küm.) | Özkaynak | ROE (küm.)% | YoY Kâr% |
|---|---|---:|---:|---:|---:|
| EREGL | sanayi | 0.41 mlr | 304.85 mlr | 0.1 | -9 |
| GARAN | banka | 33.32 mlr | 451.32 mlr | 7.4 | 32 |
| ASELS | sanayi | 5.55 mlr | 282.74 mlr | 2.0 | 99 |
| THYAO | sanayi | 9.86 mlr | 966.36 mlr | 1.0 | — |
| BIMAS | sanayi | 6.55 mlr | 190.79 mlr | 3.4 | 85 |
| AKBNK | banka | 19.18 mlr | 302.60 mlr | 6.3 | 40 |
| SISE | sanayi | 1.45 mlr | 286.04 mlr | 0.5 | -17 |
| TUPRS | sanayi | 3.82 mlr | 360.08 mlr | 1.1 | 2,327 |

_8/8 hisse faktör üretti._

## 2) Point-in-time kanıtı — geçmiş tarihte de çalışıyor mu?

Aynı hisse (EREGL), farklı tarihlerde o gün AÇIKLANMIŞ veriyle:

| Tarih | Açıklanmış son çeyrek | Net Kâr (küm.) | ROE% |
|---|---|---:|---:|
| 2022-06-01 | 2021/Q4 | 16.08 mlr | 19.0 |
| 2023-06-01 | 2022/Q4 | 18.65 mlr | 15.7 |
| 2024-06-01 | 2023/Q4 | 4.33 mlr | 2.3 |
| 2025-06-01 | 2024/Q4 | 18.58 mlr | 5.8 |

> Farklı tarihlerde farklı çeyrek/sayı görünüyorsa, geçmiş point-in-time çalışıyor demektir — temel-seçim backtest'i kurabiliriz.

---
*Sonraki: bu faktörlerle 94-hisse top-N temel-seçim backtest'i (OOS + maliyet + mevduat çıtası).*