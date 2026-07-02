# 📖 APEX — Kullanım Rehberi

APEX, Borsa İstanbul (BIST) için bir **risk & bağlam terminalidir — tahmin motoru DEĞİL.**
Yıllarca süren backtest tek şeyi öğretti: yön/getiri seçimi ve makro zamanlama out-of-sample
ve placebo testlerinde çöktü. Doğrulanmış TEK eksen kaldı: **risk disiplini.** APEX'in amacı
"zengin olmak" değil; kaybetmemeyi, disiplini, aldanmamayı öğrenmek.

## APEX ne YAPAR, ne YAPMAZ
- **YAPAR:** hisseye-özel volatilite-hedefli pozisyon + ATR(14)×2 stop · her okumanın dürüst
  sicili · bağlam (KAP/haber/makro) · "şu an ne durumda" betimlemesi.
- **YAPMAZ:** yön/getiri tahmini · "kesin al" · hedef fiyat · güven-satışı. Bir okumanın isabeti
  %40–60 ise → gri **"≈ yazı-tura"** damgası: yön vermiyor, bu normal ve dürüst.

## Ana ekran — Pusula (dashboard)
- **Güven Kerterizi** (0–100 gösterge): bir "al skoru" DEĞİL, bir belirsizlik/ölçü cihazı.
  Amber = güven (şüpheli), teal = risk-temiz.
- **İki eksen ayrımı:** *Risk (doğrulandı)* ↔ *Getiri (~yazı-tura, kanıtlanmış edge yok)*.
  Bilinçli ayrım — neye güvenip neye güvenmeyeceğini gösterir.
- **Rejim · reel faiz:** mevduat mı hisse mi lehte; temkin tilt.
- **Risk disiplini kartı:** vol-target + ATR stop, sicil.
- **İleri-test · önde + 3-çizgi grafik:** tek dürüst OOS. Sistem (koyu mavi düz) /
  Endeks (amber kesikli) / Mevduat (gri-yeşil noktalı) kümülatif seyir; "önde" hangisi.
  Getiriyi DEĞİL, risk/rejim-duruş disiplinini ölçer.
- **Havuz:** BIST havuzu, **Risk sütununa** göre sıralı (en kırılgan üstte) — kaçınma skoru
  (düşüş + tuzak + RSI/vol), yön içermez.

## Hisse detayı — Trade (karta tıkla)
- **Ölçülü plan:** stop = ATR(14)×katsayı, poz = hisseye-özel vol-target. "AL" değil, çerçeve.
- R/R, destek/direnç, gün-içi **akış paneli** ("şu an ne oluyor"), **belirsizlik konisi**
  (Monte Carlo — ortası düz, çünkü YÖN YOK; genişlik = belirsizliğin ölçüsü).

## Alt paneller
- **Görsel Özet:** grafikli, betimleyici (sinyal/hedef/yön yok).
- **Karar Çerçevesi:** düşündüğün hisse için ölçülü çerçeve + belirsizlik konisi.
- **Portföy Risk Paneli:** tek hisse değil "tüm kitap" — yoğunlaşma, sektör.
- **Kalibrasyon defteri:** sistem KENDİ sinyallerini sınar (öz-denetim). İsabet ~%50 ise
  yön vermiyor → Güven'i aşağı çeker. Amaç haklı çıkmak değil.
- **Karar Günlüğü:** SENİN kararlarını denetler (placebo %50; %42 altı ters-seçim uyarısı).

## AKD Sicil hattı (aracı kurum dağılımı)
- **Çekici** (`akd_cekici.py`): ForInvest AKD'sini çeker (net lot, hacim).
- **Sicil** (`akd_sicil.py`): manuel + otomatik arşivdeki davranış desenlerine
  (3-dönem net alıcı, custodian %40+, net yön değişimi) **sonraki 10 işlem günü getirisini**
  iliştirir. Çapa = dönem sonu (look-ahead yok); vade dolmadıysa "beklemede" (mühürleme).
  İsabet %40–60 → "≈ yazı-tura". Gözlem, kehanet DEĞİL. (Custodian kod tanıma sürüyor.)

## Sanal Borsa (ayrı sayfa)
Paper trading, gerçek BIST, BIST100 havuz. Kural-tabanlı işlem planı (yönsüz durum +
destek/direnç + R/R + sicil). **AL Sinyali** = çoklu süzgeç kesişimi (giriş + sicil ≥%55 +
R/R + edge); seçici, çoğu gün boş — bu normal. Bir "yükselir" tahmini DEĞİL; kuralların bu
hissede ne kadar sağlam durduğunu gösterir. Oto-simülasyon + mevduat kıyası (beta mı beceri mi).

## Arka planda (otomatik)
- **Bekçi:** gece sağlık kontrolü (sözdizimi + fiyat tazeliği + CSV + AKD arşivi);
  yeşilse Telegram tek satır, bulguda "bekci" issue + @claude.
- **İleri-test loglayıcı** (hafta içi): `ileri_gunluk.csv` birikir.
- **Projektör:** günlük Telegram bağlam özeti (yön/hedef YOK).

## Sicil felsefesi (çekirdek)
Her okuma kendi sicilini taşır: "geçmişte bu desenden/sinyalden sonra ne oldu". İsabet %40–60
ise → **gri "≈ yazı-tura"**: desen yön VERMİYOR — bu normal ve dürüst, APEX yön tahmini iddia
etmez. Değer, ne zaman güveneceğini VE ne zaman güvenmeyeceğini bilmekte.

## ⚠️ Önemli Hatırlatma
Karar destek aracıdır, **yatırım tavsiyesi değildir.** Veri 15 dk gecikmeli/EOD olabilir.
SPK lisanslı yatırım danışmanı değildir. Kararların sonuçları sana aittir.

---
*Bu rehber canlı sistemi (APEX / app.py) yansıtır. Eski çok-modüllü mimari arşivdedir
(`arsiv/`); bu rehber onu anlatmaz.*
