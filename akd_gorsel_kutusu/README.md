# akd_gorsel_kutusu — AKD toplu görsel kutusu

ForInvest AKD / takas ekran görüntülerini **doğrudan bu klasöre** koy (yüzlerce olabilir),
sonra bir `[AKD-TOPLU]` issue açıp `@claude görselleri işle` de.

- **Buraya at:** işlenecek görseller (`.png` / `.jpg`). Alt klasör açma.
- **`islenmis/`:** @claude işlediği görselleri buraya TAŞIR — tekrar işlenmez. İşlem sırasında dokunma.
  Görseller repoda kalır (işlenebilmesi için gerekli). **Repo şişmesine karşı:** bir parti işlenip PR merge
  edildikten sonra, istersen `islenmis/` altındaki taşınmış görselleri ELLE silip commit'leyebilirsin
  (`.gitkeep` kalsın). Veri `akd_manuel_arsiv.csv`'de kalıcıdır; görseller yalnızca işleme kanıtıdır.
- **Çıktı:** takas/AKD ekranları `akd_manuel_arsiv.csv`'ye; okunamayan/şüpheli olanlar
  `kontrol_gerekli.csv`'ye düşer (uydurma YOK). @claude PR açar, rakamı SEN doğrulayıp merge edersin.
- Bir seferde ~50 görsel önerilir (bağlam sınırı). 500 görsel → ~10 parti.

Detaylı protokol: CLAUDE.md "Bölüm 12 — AKD Toplu Görsel Protokolü".
