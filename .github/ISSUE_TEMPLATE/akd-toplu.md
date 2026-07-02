---
name: AKD Toplu Görsel İşleme
about: akd_gorsel_kutusu/ klasörüne yüklenen yüzlerce AKD görselini toplu işle
title: "[AKD-TOPLU] parti - tarih"
labels: akd-toplu
---

## AKD toplu görsel işleme

ForInvest AKD/takas ekran görüntülerini `akd_gorsel_kutusu/` klasörüne yükledikten sonra bu issue'yu aç.
@claude görselleri okuyup takas ekranlarını `akd_manuel_arsiv.csv`'ye işler; okunamayan/şüpheli olanları
`kontrol_gerekli.csv`'ye ayırır (uydurma YOK). PR açar — **rakam doğrulaması sende**, sen merge edersin.

### Onay
- [ ] Görselleri `akd_gorsel_kutusu/` klasörüne yükledim (alt klasör açmadan, doğrudan içine).
- [ ] Bu partide ~40 görsel var (daha fazlaysa birden fazla issue açacağım).

### Not (opsiyonel)
<!-- Özel durum, belli hisseler, bilinen bulanık görseller vb. -->


---

@claude görselleri işle — `akd_gorsel_kutusu/` (islenmis/ hariç) içindeki görselleri oku,
CLAUDE.md Bölüm 12 (AKD Toplu Görsel Protokolü) adımlarını izle: takas ekranlarını
`akd_manuel_arsiv.csv`'ye yaz, okunamayan alanı boş bırak, şüpheli/okunamaz görseli
`kontrol_gerekli.csv`'ye at, işlenenleri `islenmis/`'e taşı, özet çıkar ve PR aç
(main'e doğrudan yazma).

> Hatırlatma: Bir seferde ~40 görsel işlenir (bağlam sınırı). 500 görsel ≈ 13 parti/issue.
