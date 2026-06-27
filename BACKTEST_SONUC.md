# APEX — Rejim Tahsisi Audit · Hisse mi Mevduat mı, Ne Zaman?

_Üretim: 2026-06-27 19:44 · 94 hisse · 7.4 yıl · maliyet: komisyon+slippage · mevduat takvim-doğru · leakage yok_

## Soru: Rejim anahtarı HEM mevduatı HEM endeksi geçiyor mu?

| Strateji | Son NAV (×) | Getiri% | Yıllık% | Sharpe | MaxDD% | Mevduatı geçti? | Endeksi geçti? |
|---|---:|---:|---:|---:|---:|:--:|:--:|
| Rejim Anahtarı (MA200) | 9.90 | 890.4 | 36.5 | 0.36 | -22.3 | ❌ | ❌ |
| Momentum (top-N) | 32.83 | 3183.5 | 60.6 | 0.83 | -49.8 | ✅ | ✅ |
| Hibrit Sinyal (top-N) | 16.55 | 1554.7 | 46.3 | 0.61 | -32.4 | ✅ | ✅ |
| _XU100 al-tut_ | 13.94 | 1294.5 | 43.0 | 0.53 | -31.8 | ❌ | — |
| _Eşit-ağırlık TÜM_ | 25.30 | 2429.7 | 55.0 | — | — | ✅ | ✅ |
| _Mevduat (~%45)_ | 15.46 | 1446.2 | 45.0 | — | — | — | ✅ |

## Karar

**Rejim anahtarı mevduatı bile geçemedi** (NAV 9.90 < mevduat 15.46). Bu basit MA kuralı edge üretmiyor. Ama tabloda asıl mesaj: bu dönemde sabit mevduat çoğu şeyi yeniyorsa, dürüst ürün 'çoğunlukla mevduat, seçili fırsatta hisse' olabilir — ya da farklı rejim sinyali (faiz yönü, enflasyon, breadth) gerekiyor.

> Rejim: 59 geçiş · %83 hissede. MA200 penceresi. Geçişte tek-yön sürtünme.

---
*Mevduat takvim-günü doğru bileşik (hafta sonu dahil). Skor/karar t kapanışında, getiri t+1 — leakage yok.*