# APEX — İleri Durum (Rejim Pusulası + Kağıt-Test)

_Son güncelleme: 2026-06-28 00:30 · veri tarihi 2026-06-25_

## Bugünün duruşu

**Reel faiz: %+4.5**  (politika %37.0 − enflasyon %32.5)

### → MEVDUAT LEHİNE

> Bu bir **duruş göstergesidir, kâhin değil.** Plasebo testi, reel-faiz rejiminin zamanlama becerisini şanstan ayıramadı — yani bu duruşu 'kanıtlanmış edge' değil, 'rejim-farkında temkin' olarak oku. Aşağıdaki ileri karne, zamanla gerçeği söyleyecek tek şeydir.

_Makro kaynak: OECD oto-besleme: **bağlı ama beklemede** → OECD son verisi 2025Ç4, statik tablo daha güncel (2026Ç2). Statik kullanılıyor._

## Önerilen pozisyon (risk-ölçekli)

XU100 yıllık oynaklık (60g): **%29**

### → %1.0 hisse · %99.0 mevduat
_(saf vol-hedef %2.1 × rejim tilt 0.5 · DD bütçesi %1.5)_

| DD bütçesi | İmâ edilen hisse % (saf vol-hedef) |
|---|---:|
| %1.5 | %2.1 |
| %5.0 | %6.9 |
| %10.0 | %13.8 |
| %20.0 | %27.7 |

> **Vol-hedefleme risk yönetimidir, getiri tahmini DEĞİL.** Pozisyonu oynaklığa göre ölçekler, 'ya hep ya hiç'i önler. DD→vol dönüşümü kaba kuraldır (k=2.5), garanti değil. Tablo acı gerçeği gösterir: dar DD bütçesi = küçük hisse maruziyeti. Bütçeyi gevşetmek daha çok hisse demek — ama daha çok da düşüş riski.

## İleri karne — 0 gündür biriken GERÇEK OOS

| Strateji | Getiri |
|---|---:|
| **Risk-ölçekli (önerilen)** | +0.2% |
| Duruş (ikili) | +0.2% |
| Al-tut endeks | +0.0% |
| Mevduat | +0.2% |

_Şu ana dek önde: **Duruş**. Risk-ölçekli = her gün kaydedilen ağırlıkla; sadece geçmiş kararlardan hesaplanır, geriye dönük düzeltme yok._

## Günlük (3 kayıt)

| Tarih | XU100 | Reel % | Duruş | Hisse % |
|---|---:|---:|---|---:|
| 2026-06-25 | 14,260 | +4.5 | MEVDUAT LEHİNE | 0.0 |
| 2026-06-26 | 14,274 | +4.5 | MEVDUAT LEHİNE | 1.0 |
| 2026-06-25 | 14,260 | +4.5 | MEVDUAT LEHİNE | 1.0 |

---
*makro_veri.py çeyreklik statik tablodur; yeni PPK/TÜİK verisinde güncellenmeli. Duruş = reel faiz histerezisi (gir<-3, çık>+3, nötr→önceki).*