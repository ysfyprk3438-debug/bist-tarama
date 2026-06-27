# APEX — Momentum Stres Testi (OOS + parametre + beceri)

_2026-06-27 19:52 · 94 hisse · 7.2 yıl_

## 1) Out-of-Sample — momentum SON yarıda da kazanıyor mu?

| Dönem | Momentum | Eşit-ağırlık | Mevduat | Endeks | Mom>hepsi? |
|---|---:|---:|---:|---:|:--:|
| İlk yarı (IS) | 18.92 | 12.51 | 3.79 | 5.10 | ✅ |
| İkinci yarı (OOS) | 2.23 | 2.76 | 3.79 | 2.92 | ❌ |
| TÜM dönem | 36.96 | 26.12 | 14.37 | 14.98 | ✅ |

## 2) Parametre taraması — 126/12 şanslı mı? (TÜM dönem, çita: mevduat & endeks)

| lookback \ N | N=8 | N=12 | N=16 |
|---|---:|---:|---:|
| 63 | 20.9 (✅) | 24.2 (✅) | 26.6 (✅) |
| 126 | 26.2 (✅) | 37.0 (✅) | 30.5 (✅) |
| 189 | 23.5 (✅) | 23.1 (✅) | 26.6 (✅) |
| 252 | 28.9 (✅) | 30.4 (✅) | 34.5 (✅) |

_Çıta: mevduat 14.4× · endeks 15.0×. ✅ = ikisini de geçti._

## Karar

**Parametre-sağlam ama OOS zayıf.** Çoğu ayar tüm dönemde kazanıyor fakat ikinci yarıda (yüksek-faiz) momentum hepsini geçemiyor — edge boom-dönemine yaslı. Bugünkü rejimde dikkatli ol; kısmi tahsis şart.

> Uyarı: survivorship (bugün yaşayan 94 hisse) momentum'u olumlu yanlı gösterir. Kesin yargı için delist olmuş hisseler de gerek.

---
*Maliyet komisyon+slippage. Skor t, getiri t+1 — leakage yok. Mevduat takvim-doğru.*