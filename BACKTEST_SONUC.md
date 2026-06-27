# APEX — OECD Ayıklama Sondası

_2026-06-27 22:56 · sayıyı çıkarabiliyor muyuz?_

## Enflasyon (TR aylık YoY TÜFE) — ASIL TEST

Durum 200 · JSON ✅ · ayıklama **çalıştı**:

| Dönem | YoY % |
|---|---:|
| 2025-09 | 33.3 |
| 2025-10 | 32.9 |
| 2025-11 | 31.1 |
| 2025-12 | 30.9 |

**Son: 2025-12 → %30.9** · ✅ makul aralıkta (gerçek YoY enflasyon, doğru seri)

## Faiz (TR kısa-vade) — ikincil, düzeltilmiş denemeler

- ✅ STES IR3TIB: ayıklandı → 2026-03 = %35.5
- ❌ MEI STINT: durum=None

## Sonuç

- Enflasyon ayıklaması ✅ + makul ise → otomasyonu logger'a bağlarız (enflasyon-oto + faiz-manuel hibrit).
- Faiz denemelerinden biri ✅ ise bonus: onu da otomatiğe alırız.
- Enflasyon ayıklaması bozuksa → format değişti, statik tablo + 10sn elle-ekle kalır (sistem zaten çalışıyor).