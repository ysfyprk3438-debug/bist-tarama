# APEX — Çok Vadeli Audit · HİBRİT (eşik=60.0)

_Üretim: 2026-06-27 18:33 · maliyet: komisyon+slippage+stop-kayma · her vade KENDİ penceresi & KENDİ al-tut'una karşı_

## Vade Karşılaştırması (hangi vadede edge var?)

| Vade | Aralık | N | Mevduat-üstü% | t | Strateji(NAV)% | Al-tut% | Endeks al-tut% | Al-tut'u geçen |
|---|---|---:|---:|---:|---:|---:|---:|:--:|
| Gün İçi (15dk) | 15m | 928 | -1.33 | -32.0 | 162.25 | -2.44 | -5.58 | 89/90 |
| Günlük (Scalp) | 1d | 2042 | -0.68 | -8.3 | 115.52 | 211.08 | 227.54 | 40/94 |
| Haftalık (Swing) | 1d | 687 | -0.89 | -4.4 | 134.24 | 214.73 | 227.54 | 39/92 |

## Karar

**Hiçbir vade her iki çıtayı geçemedi.** Hiçbiri al-tut'u + mevduatı birlikte yenmiyor. Yani 'doğru vadeyi seç' yaklaşımı tek başına edge üretmiyor — sorun vade seçimi değil, sinyal ailesi. Sonraki kaldıraç: farklı alfa kaynağı (fundamental/makro veya order-flow) ya da 'al-tut'a yakın kal' (daha az gir-çık) varyantı.

> Not: Gün içi (15dk) penceresi ~60 günle sınırlı (Yahoo) ve 15dk GECİKMEYİ modellemez → canlı için İYİMSER. Eğer gün içi edge gösterirse, bir bar geç giriş ekleyip yeniden ölçeceğiz.

---
*Strateji: HİBRİT (eşik=60.0). Komisyon %0.2+slippage %0.15 (tek yön), stop ekstra %0.3. Nakitte mevduat (~%45). Walk-forward, leakage yok.*