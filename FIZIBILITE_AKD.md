# FİZİBİLİTE — AKD / Takas Verisine Programatik Erişim

> **Durum:** ARAŞTIRMA raporu (2026-07-02). Kod yazılmadı, hiçbir hesaba giriş yapılmadı.
> **Karar insana aittir.** Bu belge seçenekleri, kırılganlıkları ve riskleri dürüstçe serer;
> hangisinin uygulanacağına Yusuf karar verir. APEX ilkesi: test edilmeden "çalışıyor" denmez,
> hesap/yasal risk küçümsenmez.

---

## 0. TL;DR (özet)
- **Tam otomatik, ücretsiz ve yasal bir yol pratikte YOK.** Üç eksenden (maliyet / yasallık / hesap riski)
  en az biri her seçenekte zorlanıyor.
- **En sert kısıt — 1 Ocak 2025:** BIST, **takas (settlement) verisini ücretli + veri-yayın lisansı
  aboneliği** gerektirecek şekilde düzenledi. Yani "takas" tarafı artık lisanssız serbestçe alınamaz.
  AKD (aracı kurum dağılımı) bazı kurumlarda hâlâ görülebiliyor ama takas kapılandı.
- **Resmî programatik yol (BIST VERDA REST API) yalnızca KURUMSAL** (aracı kurum / veri yayıncısı /
  endeks lisansçısı) — bireysel kullanıcıya kapalı.
- **ForInvest'in kendi iç ucu (`akdAt`) ile otomasyon = ToS ihlali + HESAP RİSKİ.** Teknik olarak
  mümkün görünse de sözleşmeye ("yalnızca bireysel kullanım") ve hesabın askıya alınmasına açık.
- **Bugünkü en düşük-riskli yol, zaten kurduğumuz yarı-otomatik görsel besleme hattı** (issue'ya
  ForInvest ekran görüntüsü → @claude okur → PR → insan doğrular). Yavaş ama yasal ve hesabı riske atmaz.
- **Tavsiye:** Kısa vadede görsel hattı kullan; kurumsal/ücretli API'yi ancak proje ciddileşirse değerlendir.

---

## 1. Bağlam ve kısıtlar
- **AKD (Aracı Kurum Dağılımı):** bir hissede hangi kurumun ne kadar net alıp sattığı.
- **Takas / saklama:** payların hangi kurumun Takasbank hesabında saklandığı; T+2 mutabakat.
- **Regülasyon kırılması (kritik):** *"Takas verileri 1 Ocak 2025'ten itibaren Borsa İstanbul
  tarafından ücretli ve veri yayın lisans aboneliği gerektirecek şekilde düzenlenmeye başlamıştır."*
  → Takas verisini lisanssız dağıtmak/otomatik çekmek artık gri/kırmızı alan.
- APEX tarafı: `app.py` içinde AKD şeması ve `akd-arsiv` hattı zaten var; manuel arşiv
  (`akd_manuel_arsiv.csv`) + `akd_sicil.py` çalışıyor. İhtiyaç: bu arşivi **düzenli, düşük
  emekle ve yasal** biçimde beslemek.

---

## 2. Seçenekler

### A) Resmî BIST VERDA HTTP-Rest API (kurumsal)
- **Ne:** BISTECH ailesinde "VERi DAğıtım" sistemi; kurumların veri dosyalarına REST ile eriştiği resmî yol.
- **Erişim:** BIST Dış Hizmetler Masası'ndan API kullanıcı hesabı açtırmak gerekir. **Kurumsal muhatap** şart
  (aracı kurum, veri yayıncısı, endeks lisansçısı). Bireysel geliştiriciye kapalı.
- **Maliyet:** BIST lisans ücretleri + kurumsal abonelik.
- **Yasallık:** En temiz yol — resmî. **Hesap riski yok** (sözleşmeli).
- **Kırılganlık:** Düşük (resmî). Ama bireysel APEX için **erişim eşiği pratikte aşılmaz** (kurumsal statü gerekir).

### B) Matriks Data API (REST / MQTT / XML web service)
- **Ne:** Gerçek zamanlı akış (MQTT) + tarihsel/hesaplanmış veri (REST). "Kurumsal dağılım (AKDE)" modülü var.
- **Erişim:** İletişim formuyla veri içeriği tanımlanıp test süreci başlatılıyor. Ürün olgun, dokümante.
- **Maliyet:** Kurumsal dağılım gerçek zamanlı veri (AKDE) ~**55 TL/ay** + **BIST lisans ücretleri** (içeriğe göre).
  Takas içeriği eklenince 1 Oca 2025 lisans kuralı devreye girer.
- **Yasallık:** Sözleşmeli, meşru. **Hesap riski düşük** (abonelik).
- **Kırılganlık:** Düşük-orta (sağlayıcıya bağımlılık; fiyat/şart değişebilir). **Bireysel için en gerçekçi ücretli API.**
- **Not:** Tam API maliyeti/kapsamı **teyit edilmeli** (arama fiyatı gösterge; net teklif iletişim formuyla alınır).

### C) Fintables (Pro/Trade + BIST lisansı)
- **Ne:** Web platformu; günlük AKD dağılımı, kurum hacimleri, takas değişimi, tarih aralığı filtresi.
  **Excel'e aktarma özelliği VAR.**
- **Erişim:** Fintables Pro/Trade + Fintables üzerinden BIST lisansı alınınca AKD/takas ekranları açılır.
- **Maliyet:** Fintables abonelik + BIST lisansı.
- **Yasallık:** Platform içi kullanım meşru. **Dokümante public API görülmedi** → otomasyon ancak
  "Excel export → elle/işlenmiş içe aktarma" düzeyinde; sayfa kazıma yine ToS'a tabi.
- **Kırılganlık:** Orta (API yoksa export'a veya kazımaya bağımlı; kazıma ToS riski taşır).

### D) ForInvest Pro GUI + yarı-otomatik görsel besleme (MEVCUT HAT — GÖREV 2)
- **Ne:** ForInvest Pro'da AKD ekranı görülür; ekran görüntüsü issue'ya yapıştırılır; @claude okuyup
  `akd_manuel_arsiv.csv`'ye PR açar; insan rakamı doğrulayıp merge eder.
- **Erişim:** Zaten var olan ForInvest Pro aboneliği + kurduğumuz `[AKD]` issue şablonu.
- **Maliyet:** Ek maliyet yok (mevcut abonelik + insan emeği).
- **Yasallık:** **En temiz.** Kişi kendi ekranına bakıp veriyi elle taşıyor; otomatik toplu çekim yok →
  ToS ihlali yok, hesap riski yok.
- **Kırılganlık:** Düşük (dış bağımlılık yok). **Dezavantaj: emek/yavaşlık** — her dönem elle görsel.
- **Uydurma koruması:** Okunamayan alan boş; rakam doğrulaması insanda (protokol CLAUDE.md §11).

### E) ForInvest iç ucu (`akdAt`) ile programatik çekim / scraping
- **Ne:** Uygulamanın AKD'yi çektiği dahili JSON ucu (APEX'te Desktop Claude ile elle kullanılıyor).
- **Erişim:** Teknik olarak mümkün görünür (kimlik/oturum gerektirir; **auth detayı doğrulanmadı**).
- **Maliyet:** Görünürde ücretsiz — ama gizli maliyet risk.
- **Yasallık:** **ToS İHLALİ RİSKİ.** ForInvest lisanslı ürünü "yalnızca müşterinin bireysel kullanımı için"
  sunuyor; borsa anlaşmalarıyla sınırlı. Otomatik toplu veri toplama tipik olarak sözleşme ihlali.
- **HESAP RİSKİ: YÜKSEK.** Otomatik/anormal trafik hesabın **askıya alınması/kapatılması** ile sonuçlanabilir;
  1 Oca 2025 takas lisans kuralı ek hukuki katman ekler.
- **Kırılganlık: YÜKSEK.** Dokümante değil → uç adı/şeması/oturum akışı habersiz değişir, sessizce bozulur
  (APEX'in en korktuğu "sessiz bug" sınıfı). **Önerilmez.**

### F) Diğer ücretsiz broker AKD ekranları (Finnet, Halk, Gedik vb.)
- **Ne:** Bazı kurumların web ekranlarında AKD/takas görünümü (ör. Finnet "Kurum Bazında Değişim").
- **Erişim:** Ücretsiz GUI; genelde export/API yok.
- **Yasallık:** Görüntüleme serbest; otomatik kazıma her sitenin ToS'una tabi + 1 Oca 2025 takas kuralı.
- **Kırılganlık:** Orta-yüksek (kazımaya bağlı, kırılır). AKD serbest olabilir; **takas kapılı.**

---

## 3. Karşılaştırma (özet tablo)

| Seçenek | Erişim eşiği | Maliyet | Yasallık | Hesap riski | Kırılganlık | APEX'e uygunluk |
|---|---|---|---|---|---|---|
| A · BIST VERDA API | Kurumsal (kapalı) | Yüksek (lisans) | Temiz | Yok | Düşük | Bireysel için ulaşılmaz |
| B · Matriks API | Orta (abonelik) | ~55 TL/ay + lisans | Meşru | Düşük | Düşük-orta | En gerçekçi ücretli otomasyon |
| C · Fintables | Orta (abonelik) | Abonelik + lisans | Meşru (API yok) | Düşük | Orta | Export'la yarı-otomatik olabilir |
| D · Görsel besleme (mevcut) | Yok (kurulu) | Ek yok + emek | En temiz | Yok | Düşük | **Bugün için en uygun** |
| E · ForInvest `akdAt` scraping | Düşük (teknik) | "Ücretsiz" (riskli) | ToS ihlali | **Yüksek** | **Yüksek** | **Önerilmez** |
| F · Ücretsiz broker ekranları | Düşük | Ücretsiz (AKD) | Gri (kazıma/takas) | Orta | Orta-yüksek | Takas kapalı, kısmi |

---

## 4. Kırılganlık, hesap riski, uyum notları
- **Sessiz bozulma (APEX'in kâbusu):** Dokümante olmayan uçlar (E, F) habersiz değişir; otomasyon veri
  üretmeye devam eder ama **yanlış/eski** — kimse bakmazsa fark edilmez. Bu, projenin açıkça reddettiği risk sınıfı.
- **Hesap riski:** Yalnızca E (ve kısmen F) gerçek askıya-alma riski taşır. A/B/C/D sözleşmeli veya insan-elli → risk yok/düşük.
- **Regülasyon:** 1 Oca 2025 sonrası **takas** verisi lisanslı. Herhangi bir otomasyon takas içeriyorsa
  lisans olmadan dağıtım/çekim hukuki risk. **AKD ile takas'ı ayrı düşün** — AKD daha serbest, takas gated.
- **Doğrulanmamış noktalar (teyit gerek):** ForInvest ToS'un tam maddesi; `akdAt` kimlik/oturum akışı;
  Matriks'in APEX kapsamı için net fiyatı; Fintables'ta public API'nin gerçekten yokluğu. Bunlar
  "çalışıyor" denmeden önce doğrudan sağlayıcıdan teyit edilmeli (dış-kaynak kuralı, CLAUDE.md §7).

---

## 5. Tavsiye (karar insana ait)
1. **Kısa vade (şimdi):** **Seçenek D** — kurduğumuz görsel besleme hattını kullan. Sıfır ek maliyet,
   sıfır hesap riski, yasal. Arşivi AKFGY dışına (ör. MAVI, izlenen 5-10 hisse) elle büyüt; `akd_sicil.py`
   örneklem arttıkça anlam kazanır. Bekçi 35 günde bir bayatlığı hatırlatır.
2. **Otomasyon ciddileşirse:** **Seçenek B (Matriks)** için iletişim formundan **net kapsam + fiyat teklifi al**
   (AKD; takas isteniyorsa lisans dahil). Ücret makulse tek meşru "tam otomatik" yol budur.
3. **Seçenek E'yi (ForInvest scraping) UYGULAMA.** Kazanç (biraz hız) < risk (hesap kaybı + ToS ihlali +
   sessiz bozulma). Gerekiyorsa önce ForInvest destek'e (destek@forinvest.com) **resmî veri/entegrasyon izni**
   sorulur; yazılı izin yoksa girilmez.
4. **Her durumda takas ≠ AKD:** takas otomasyonu lisans ister; AKD'de kal, takası manuel/ayrı tut.

---

## Kaynaklar
- [ForInvest Destek / SSS](https://www.forinvest.com/destek) · [ForInvest Pro Plan](https://www.forinvest.com/pro-plan) · [ForInvest Nasıl Kullanılır](https://www.forinvest.com/nasil-kullanilir)
- [BISTECH VERDA HTTP-Rest API Entegrasyon Dokümanı (PDF)](https://www.borsaistanbul.com/files/bistech-verda-http-rest-api-integration-manual_tr.pdf)
- [Matriks Data — Veri & İçerik Kaynakları](https://www.matriksdata.com/website/urunlerimiz/kurumsal-hizmet-ve-servisler/veri-ve-icerik-saglayici-servisler) · [Matriks — Aracı Kurum Dağılımı ve Kurum Temelli Analizler (PDF)](https://www.matriksdata.com/website/uploads/araci-kurum-dagilimi-ve-kurum-temelli-analizler.pdf)
- [Fintables — Aracı Kurumlar](https://fintables.com/araci-kurumlar) · [Fintables — Takas ve Aracı Kurum Dağılımı Nedir](https://fintables.com/arastirma/yazilar/takas-analizi/takas-ve-araci-kurum-dagilimi-nedir) (1 Oca 2025 takas lisans notu) · [Fintables PRO](https://fintables.com/abone-ol)
- [Finnet — Kurum Bazında Hisse Değişimleri](https://www.finnet.com.tr/f2000/takas/KurumBazindaDegisim.aspx)
- [Gedik — Takas Analizi Nedir](https://gedik.com/yazilar/yatirim/takas-analizi-nedir)
