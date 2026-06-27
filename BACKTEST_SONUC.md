# APEX — Sağlamlık Geçidi (rejimi KIRMA testi)

_2026-06-27 22:13 · XU100 · 8.0 yıl · brüt çarpan bazlı_

## 1) Eşik taraması — edge tek noktada mı, her yerde mi?

| gir / çık | TÜM | OOS | mev(OOS) | end(OOS) | OOS geçti? |
|---|---:|---:|---:|---:|:--:|
| -1 / 1 | 21.74 | 6.53 | 3.01 | 5.84 | ✅ |
| -1 / 3 | 21.93 | 6.53 | 3.01 | 5.84 | ✅ |
| -1 / 5 | 20.39 | 5.97 | 3.01 | 5.84 | ✅ |
| -3 / 1 | 18.72 | 6.53 | 3.01 | 5.84 | ✅ |
| -3 / 3 | 20.63 | 6.53 | 3.01 | 5.84 | ✅ |
| -3 / 5 | 19.18 | 5.97 | 3.01 | 5.84 | ✅ |
| -5 / 1 | 14.09 | 6.53 | 3.01 | 5.84 | ✅ |
| -5 / 3 | 14.09 | 6.53 | 3.01 | 5.84 | ✅ |
| -5 / 5 | 13.10 | 5.97 | 3.01 | 5.84 | ✅ |
| -8 / 1 | 14.09 | 6.53 | 3.01 | 5.84 | ✅ |
| -8 / 3 | 14.09 | 6.53 | 3.01 | 5.84 | ✅ |
| -8 / 5 | 13.10 | 5.97 | 3.01 | 5.84 | ✅ |

**12 eşik kombinasyonunun 12'i OOS'ta mevduat+endeksi geçti.** Edge geniş eşik aralığında yaşıyor → kırılgan değil.

## 2) Gecikme stresi — makro veri geç gelirse?

| lag (gün) | TÜM | OOS | OOS geçti? |
|---|---:|---:|:--:|
| 35 | 20.63 | 6.53 | ✅ |
| 60 | 21.51 | 6.74 | ✅ |
| 90 | 17.50 | 5.90 | ✅ |

**3 gecikme senaryosunun 3'i OOS'ta geçti.** 90 güne kadar gecikmeye dayanıklı.

## 3) Plasebo — 2 geçiş + %56 hisse-süresi rastgele yerleşseydi?

Gerçek rejim brüt: **20.63×** · 2 geçiş · %56 hissede

| Plasebo | 4000 sahte ortalama | Gerçek yüzdelik |
|---|---:|---:|
| B: rastgele tek blok (D-E-D) | 19.77× | **%55.7** |
| A: aylık rastgele (oran eşli) | 10.19× | **%97.4** |

**Plasebo B yorumu:** gerçek rejim ortalarda → zamanlama şanstan ayırt edilemiyor (kötü işaret).

## Geçit Kararı (dereceli)

Eşik sağlamlığı: %100 · Gecikme sağlamlığı: %100 · Plasebo-B ayrışması: yok

**Rejim eşik+gecikmeye dayanıklı ama plasebodan net ayrışmıyor.** Mekanizma sağlam, ama 2 geçişin tam yeri kısmen şans olabilir. Mantıklı sonuç: ileri teste değer, ama tek başına 'kanıt' sayma — hissedeyken seçim ekleyip (momentum/temel) plasebo ayrışmasını güçlendirmeyi dene.

---
*Brüt çarpan bazlı (zamanlama becerisini izole etmek için sürtünme hariç; gerçek rejim 2 geçişte sürtünme ihmal edilebilir). Karar t, getiri t+1; enflasyon lag'li — leakage yok.*