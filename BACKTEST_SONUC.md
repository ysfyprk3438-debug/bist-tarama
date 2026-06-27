# APEX — Cross-Sectional Audit · Hep Yatırımda, Top-N Seçim

_Üretim: 2026-06-27 18:54 · 94 hisse · 3.6 yıl · top-12, ~21g dengeleme · maliyet: komisyon+slippage · leakage yok_

## Soru: Seçim, yatırımda kalarak XU100'ü yeniyor mu?

| Strateji | Son NAV (×) | Getiri% | Yıllık% | Sharpe | MaxDD% | XU100'ü geçti? |
|---|---:|---:|---:|---:|---:|:--:|
| Momentum (top-N) | 2.55 | 154.7 | 29.8 | 0.19 | -36.1 | ❌ |
| Hibrit Sinyal (top-N) | 2.06 | 106.4 | 22.4 | -0.04 | -28.3 | ❌ |
| _XU100 al-tut_ | 2.92 | 191.8 | 34.8 | 0.31 | -22.9 | — |
| _Eşit-ağırlık TÜM al-tut_ | 2.72 | 172.4 | 32.2 | — | — | ❌ |
| _Mevduat (~%45)_ | 3.79 | 279.5 | 45.0 | — | — | ✅ |

## Karar

**Hiçbir seçim XU100'ü geçemedi.** Bu evrende cross-sectional seçim de endeksi yenmiyor — muhtemelen hisseler fazla korele ve endeks birkaç dev hisseyle taşınıyor. Sonraki kaldıraç: (a) farklı faktör (değer/kalite/düşük-volatilite), (b) fundamental veri, ya da hedefi değiştir: 'endeksi yenmek' yerine 'benzer getiri + daha düşük MaxDD' (risk-ayarlı).

> Sinyal scorer dengeleme başına ort. 3.2 hisse işaretledi (top-12 hedefi). 12'in altındaysa kalan ağırlık endekste tutuldu (hep yatırımda).

---
*Hep %100 yatırımda. Komisyon %0.2+slippage %0.15 (tek yön, devirde). Skor t kapanışında, getiri t+1 — leakage yok.*