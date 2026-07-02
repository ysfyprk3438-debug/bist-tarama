---
name: AKD Besleme
about: ForInvest AKD ekran goruntulerinden akd_manuel_arsiv.csv'ye veri isle
title: "[AKD] HISSE - donem"
labels: akd-besleme
---

## AKD gorsel besleme

ForInvest AKD ekran goruntulerini asagiya yapistir, alanlari doldur, sonra @claude'u cagir.
Rakam dogrulamasi SANA ait: @claude PR acar, sen diff'te kontrol edip merge edersin (main'e dogrudan YAZMAZ).

### 1. Hisse
<!-- Ornek: AKFGY -->
HISSE:

### 2. Donem tipi
<!-- gunluk / haftalik / aylik / 3aylik -->
DONEM TIPI:

### 3. Donem araligi (biliniyorsa)
<!-- Ornek: 2026-07-01 .. 2026-07-31. Bilinmiyorsa bos birak, @claude gorselden okur. -->
BASLANGIC:
BITIS:

### 4. AKD ekran goruntuleri
<!-- Goruntuleri BURAYA yapistir (surukle-birak veya Ctrl+V). Birden fazla ay/donem varsa hepsini ekle. -->


### 5. Not (opsiyonel)
<!-- Bulanik/kesik gorsel, ozel durum vb. -->


---

@claude — Yukaridaki AKD gorsellerinden Ilk-5 net lot, lider alici/satici ve yuzdeleri oku;
`akd_manuel_arsiv.csv` semasina yeni satir(lar) olarak isle (CLAUDE.md Bolum 11 protokolu).
Okunamayan alani BOS birak (uydurma yok). PR ac — main'e dogrudan yazma, rakam dogrulamasi bende.
