# APEX — Temel-Seçim Backtest (TTM ROE + kâr büyümesi)

_2026-06-27 21:01 · 94 hisse · 7.2 yıl · top-12, çeyreklik · rank-normalize · point-in-time_

## Temel-seçim, momentum'un çöktüğü yerde (OOS) tutuyor mu?

| Dönem | Temel-Seçim | Momentum | Eşit-ağ. | Mevduat | Endeks | Temel>mev&end? |
|---|---:|---:|---:|---:|---:|:--:|
| İlk yarı (IS) | 10.19 | 15.87 | 12.53 | 3.79 | 5.11 | ✅ |
| İkinci yarı (OOS) | 1.78 | 1.85 | 2.72 | 3.79 | 2.92 | ❌ |
| TÜM dönem | 19.57 | 31.57 | 26.29 | 14.38 | 15.00 | ✅ |

_Temel-seçim TÜM dönem MaxDD: %-40.2_

## Karar

**Temel-seçim de OOS'ta zayıf.** İlk yarıda iyi olsa bile yüksek-faiz yarısında mevduatı+endeksi geçemiyor. Demek bu rejimde tek başına temel-seçim de yetmiyor; ya değer/kalite faktörü eklenmeli ya da rejim-tahsisi (mevduat tabanı) ile birleştirilmeli.

> Survivorship uyarısı sürüyor (bugünkü hisseler). Kesin yargı için delist'ler de gerek.

---
*TTM ROE + YoY büyüme, rank-normalize (aykırı dirençli). Maliyet komisyon+slippage. Faktör açıklanma-tarihinde, getiri sonrasında — leakage yok.*