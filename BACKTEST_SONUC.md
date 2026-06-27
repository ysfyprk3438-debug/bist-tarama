# APEX — Audit Backtest · HİBRİT (eşik=60.0)

_Üretim: 2026-06-27 17:40 · vade: haftalik · maliyet: komisyon+slippage+stop-kayma · iki çıta: mevduat & al-tut_

## ÇITA 2 — Al-tut benchmark (asıl rakip: BIST-100 al ve tut)

**Strateji al-tut'u YENMİYOR — mevduat kıyasından daha sert mahkumiyet.** Fund getirisi (nakit dahil) ort **%134.24**, ama hisse al-tut **%214.73**, endeks al-tut **%227.54**. Seçici long-only teknik, yükselen piyasada zamanın çoğunu nakitte geçirip trendi KAÇIRIYOR → kayıp sinyalde değil, timing/execution varsayımında.

- Strateji (fund NAV, nakit dahil) ort. pencere getirisi: **%134.24**
- Hisse al-tut ort. pencere getirisi: **%214.73**
- Endeks (XU100) al-tut pencere getirisi: **%227.54**
- Strateji, hisse al-tut'u geçen sembol: **39/92**

> Not: Pencere uzun ve yükseliş içeriyorsa al-tut doğal olarak yüksek olur; strateji nakitte beklediği için geride kalması beklenir. Asıl soru: bu geride kalma kabul edilebilir mi, yoksa strateji ailesi piyasayı yenemiyor mu? Maliyet (komisyon+slippage+stop kayması) gerçekçi alındı; edge'i şişirmiyor.

## ÇITA 1 — Mevduat (havuz t-istatistiği)

**Mevduatı yenmiyor.** İşlem başı mevduat-üstü **%-0.89**, t=**-4.4** (N=687) — |t| eşiğin (2.0) altında.

- Test edilen sembol: **92/94** · havuz N: **687**
- Mevduat-üstü pozitif sembol: **31/92**
- Genel başarı (kazanan/işlem): **%41.0**

## Hisse Bazında

| Hisse | İşlem | Başarı% | Strateji%(NAV) | Al-tut% | Mevduat-üstü% | Al-tut'u geçti? |
|---|---:|---:|---:|---:|---:|:--:|
| DARDL | 2 | 100.0 | 187.44 | -56.78 | 7.11 | ✓ |
| TATGD | 10 | 70.0 | 205.94 | -34.39 | 2.13 | ✓ |
| HEKTS | 2 | 50.0 | 147.84 | -88.88 | -0.42 | ✓ |
| SASA | 3 | 66.7 | 168.20 | -64.70 | 2.40 | ✓ |
| ADEL | 1 | 100.0 | 171.50 | -47.06 | 8.22 | ✓ |
| BFREN | 9 | 66.7 | 177.49 | -31.05 | 1.22 | ✓ |
| CCOLA | 12 | 50.0 | 152.08 | -53.89 | 0.22 | ✓ |
| VESTL | 3 | 33.3 | 134.47 | -45.58 | -2.07 | ✓ |
| ZOREN | 6 | 33.3 | 126.42 | -23.15 | -1.59 | ✓ |
| PRKAB | 9 | 44.4 | 161.48 | 14.80 | 0.64 | ✓ |
| KLNMA | 11 | 36.4 | 112.37 | -26.05 | -1.42 | ✓ |
| ODAS | 4 | 25.0 | 120.62 | -8.46 | -3.07 | ✓ |
| BERA | 6 | 50.0 | 149.35 | 21.87 | 0.07 | ✓ |
| AYEN | 8 | 50.0 | 138.37 | 13.62 | -0.49 | ✓ |
| CEMTS | 4 | 25.0 | 125.14 | 12.94 | -2.59 | ✓ |
| ALARK | 6 | 50.0 | 145.37 | 33.17 | -0.24 | ✓ |
| NATEN | 3 | 66.7 | 173.39 | 66.88 | 3.04 | ✓ |
| KARSN | 8 | 50.0 | 146.47 | 41.68 | -0.07 | ✓ |
| DEVA | 7 | 57.1 | 160.18 | 56.62 | 0.64 | ✓ |
| DOAS | 5 | 40.0 | 141.47 | 42.78 | -0.62 | ✓ |
| GESAN | 8 | 37.5 | 131.34 | 37.23 | -0.83 | ✓ |
| KAREL | 3 | 33.3 | 133.29 | 41.76 | -2.26 | ✓ |
| ARCLK | 10 | 30.0 | 98.42 | 27.91 | -2.23 | ✓ |
| BRISA | 6 | 50.0 | 146.90 | 84.20 | -0.13 | ✓ |
| PNSUT | 5 | 40.0 | 145.87 | 83.49 | -0.23 | ✓ |
| GSDHO | 12 | 50.0 | 164.06 | 103.18 | 0.56 | ✓ |
| AYDEM | 10 | 30.0 | 97.64 | 46.11 | -2.24 | ✓ |
| KLGYO | 1 | 0.0 | 136.78 | 88.96 | -5.59 | ✓ |
| EUPWR | 2 | 0.0 | 78.86 | 32.46 | -5.08 | ✓ |
| ISDMR | 12 | 58.3 | 153.23 | 108.22 | 0.19 | ✓ |
| BANVT | 4 | 50.0 | 156.09 | 111.10 | 0.68 | ✓ |
| EREGL | 9 | 44.4 | 142.11 | 111.73 | -0.26 | ✓ |
| PETKM | 13 | 23.1 | 67.79 | 37.98 | -2.98 | ✓ |
| TTRAK | 12 | 41.7 | 119.22 | 92.97 | -1.02 | ✓ |
| KCAER | 8 | 25.0 | 95.08 | 76.03 | -2.63 | ✓ |
| TRCAS | 4 | 25.0 | 122.06 | 104.91 | -2.85 | ✓ |
| INDES | 5 | 60.0 | 160.14 | 146.04 | 0.86 | ✓ |
| NETAS | 1 | 0.0 | 136.46 | 123.09 | -5.71 | ✓ |
| AKSEN | 7 | 14.3 | 82.78 | 82.34 | -4.39 | ✓ |
| LOGO | 5 | 60.0 | 168.36 | 168.45 | 1.54 | ✗ |
| SOKM | 9 | 22.2 | 92.63 | 95.20 | -2.81 | ✗ |
| AFYON | 12 | 33.3 | 101.06 | 112.07 | -1.72 | ✗ |
| SNGYO | 10 | 30.0 | 102.47 | 116.35 | -1.99 | ✗ |
| GUBRF | 10 | 60.0 | 187.50 | 207.57 | 1.57 | ✗ |
| ISGYO | 10 | 50.0 | 152.62 | 177.25 | 0.22 | ✗ |
| FROTO | 8 | 37.5 | 120.83 | 145.83 | -1.48 | ✗ |
| HLGYO | 13 | 53.8 | 186.38 | 216.27 | 1.17 | ✗ |
| VKGYO | 12 | 25.0 | 79.45 | 122.59 | -2.71 | ✗ |
| THYAO | 8 | 50.0 | 141.50 | 186.13 | -0.36 | ✗ |
| GOLTS | 5 | 20.0 | 110.88 | 173.46 | -3.37 | ✗ |
| OTKAR | 8 | 25.0 | 95.00 | 159.19 | -2.98 | ✗ |
| AEFES | 8 | 75.0 | 209.82 | 281.60 | 2.79 | ✗ |
| KRDMD | 9 | 44.4 | 137.58 | 213.68 | -0.44 | ✗ |
| TCELL | 10 | 60.0 | 169.04 | 247.34 | 0.82 | ✗ |
| CLEBI | 7 | 14.3 | 99.69 | 186.47 | -3.16 | ✗ |
| ECZYT | 7 | 28.6 | 114.46 | 206.54 | -2.08 | ✗ |
| ECILC | 12 | 50.0 | 155.92 | 248.87 | 0.33 | ✗ |
| SAHOL | 9 | 11.1 | 76.49 | 171.27 | -3.77 | ✗ |
| PGSUS | 15 | 13.3 | 34.04 | 130.80 | -4.07 | ✗ |
| TOASO | 10 | 30.0 | 96.49 | 195.34 | -2.30 | ✗ |
| KCHOL | 14 | 35.7 | 100.16 | 203.03 | -1.49 | ✗ |
| ALBRK | 8 | 37.5 | 119.08 | 238.89 | -1.55 | ✗ |
| DOHOL | 7 | 28.6 | 110.52 | 232.04 | -2.39 | ✗ |
| TAVHL | 7 | 42.9 | 138.35 | 259.89 | -0.61 | ✗ |
| TKFEN | 3 | 33.3 | 135.62 | 271.57 | -1.94 | ✗ |
| TSKB | 9 | 55.6 | 156.28 | 293.40 | 0.38 | ✗ |
| ENJSA | 8 | 75.0 | 207.48 | 354.40 | 2.72 | ✗ |
| MAVI | 2 | 0.0 | 122.37 | 272.18 | -5.99 | ✗ |
| ISCTR | 5 | 40.0 | 142.67 | 305.66 | -0.50 | ✗ |
| SMART | 2 | 0.0 | 120.54 | 288.97 | -6.28 | ✗ |
| VAKBN | 9 | 33.3 | 102.99 | 274.93 | -2.22 | ✗ |
| MAALT | 7 | 28.6 | 116.42 | 294.78 | -1.96 | ✗ |
| ULKER | 11 | 54.5 | 165.59 | 347.96 | 0.65 | ✗ |
| EKGYO | 8 | 25.0 | 101.62 | 304.96 | -2.57 | ✗ |
| TTKOM | 9 | 33.3 | 114.48 | 322.24 | -1.57 | ✗ |
| MGROS | 9 | 55.6 | 162.38 | 387.64 | 0.64 | ✗ |
| YKBNK | 11 | 36.4 | 95.65 | 340.92 | -2.13 | ✗ |
| HALKB | 15 | 53.3 | 178.78 | 425.04 | 0.89 | ✗ |
| PAPIL | 3 | 66.7 | 170.77 | 417.75 | 2.78 | ✗ |
| BIMAS | 13 | 61.5 | 186.82 | 434.52 | 1.15 | ✗ |
| CIMSA | 9 | 33.3 | 109.91 | 358.44 | -1.84 | ✗ |
| ENKAI | 9 | 22.2 | 85.21 | 338.86 | -3.24 | ✗ |
| AKBNK | 4 | 0.0 | 99.52 | 426.76 | -5.57 | ✗ |
| GARAN | 11 | 36.4 | 124.72 | 471.71 | -0.87 | ✗ |
| MPARK | 3 | 33.3 | 138.73 | 523.90 | -1.48 | ✗ |
| SELEC | 6 | 33.3 | 124.95 | 541.60 | -1.63 | ✗ |
| GLYHO | 9 | 44.4 | 127.25 | 607.29 | -0.96 | ✗ |
| SKBNK | 6 | 16.7 | 102.37 | 594.67 | -3.45 | ✗ |
| DGATE | 2 | 50.0 | 155.27 | 661.30 | 1.13 | ✗ |
| TRGYO | 6 | 33.3 | 115.28 | 653.79 | -2.56 | ✗ |
| RYSAS | 5 | 80.0 | 209.29 | 1178.49 | 4.43 | ✗ |
| ASELS | 9 | 55.6 | 162.91 | 2001.43 | 0.69 | ✗ |
| CWENE | – | – | – | – | – | _sinyal yok_ |
| ARENA | – | – | – | – | – | _sinyal yok_ |

---
*Strateji: HİBRİT (eşik=60.0). Maliyet: komisyon %0.2+slippage %0.15 (tek yön), stop'ta ekstra %0.3 kayma. Nakitteyken mevduat (~%45) kazanılır (cash drag modeli). Walk-forward, leakage yok. Strateji%(NAV)=nakit dahil fund getirisi.*