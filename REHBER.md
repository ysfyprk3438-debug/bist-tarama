# 📖 BIST Para Avcısı — Kullanım Rehberi

Bu rehber, uygulamanın **tüm özelliklerini** tek yerde toplar. Her özelliğin ne yaptığını, hangi sekmede olduğunu ve nasıl kullanılacağını anlatır.

---

## 🧠 Sistem Nasıl Düşünüyor? (Her hissenin geçtiği akıl zinciri)

Sen bir hisseye baktığında, sistem arka planda şu katmanlardan geçiriyor:

1. **Veri** → Çift kaynaklı (Yahoo + İş Yatırım), gecikmeli olabilir
2. **Teknik analiz** → RSI, MACD, hareketli ortalamalar, ATR, Bollinger
3. **Akıllı para** → Büyük oyuncu giriyor mu? (OBV, CMF, hacim analizi)
4. **Niyet okuma** → Paranın davranışı: sessiz toplama mı, dağıtım mı, sürü mü?
5. **Rüzgar yönü** → Borsa + sektör + hisse aynı yönde mi? (kuyruk/karşı rüzgar)
6. **Alarm** → Yaklaşan kritik olay var mı? (geri sayımlı)
7. **Volatilite rejimi** → Piyasanın hava durumu (sakin/fırtına) → pozisyon ve stop ayarı
8. **Karakter (DNA)** → Hisse trend mi yapar, salınır mı? (Hurst) + lider mi, takipçi mi?
9. **Hacim profili** → Paranın en çok döndüğü kurumsal seviyeler (POC, değer alanı, VWAP)
10. **Zaman dilimi onayı** → Üst zaman dilimi (haftalık/aylık) sinyali teyit ediyor mu?
11. **KARAR** → Tüm bunlar tek "AV SKORU" ve net karara indirgenir

Yani her hisse 10 boyutta incelenip tek net karara dönüşüyor.

---

## 📱 Sekmeler ve Ne İşe Yaradıkları

### 📡 Radar (ilk sekme — nişan ekranı)
Tüm taramadan **sadece şu an aksiyon gerektiren** hisseleri gösterir. Gürültü yok.
- En üstte **🩺 Piyasa Sağlığı** şeridi: kaç hisse katılıyor, içi boş yükseliş var mı (ıraksama uyarısı)
- **🔴 ŞİMDİ** → fırsat penceresi açık (ŞİMDİ AL kararı + çakan alarmlar)
- **⚡ YAKLAŞAN** → pozitif olay yaklaşıyor, hazırlan
- **👁 İZLE** → takipte tut
- Fırsat yoksa "🌙 Radar temiz" der — sakin kalmak da stratejidir

**Nasıl kullan:** Güne buradan başla. Sistem sana "buraya bak" diyor.

### 🎯 Av Panosu
Senin kişisel durumun ve günün özeti.
- Günlük hedef ve ilerleme takibi
- Açık pozisyonların ve **sektör yığılma uyarısı** (tek sektöre fazla yüklenince uyarır)
- Cüzdan karnesi

### 📊 Tarama
BIST'i tarayıp tüm fırsatları gösteren ana ekran.
- Vade seç (Gün İçi / Günlük / Haftalık / Aylık), **BIST'İ TARA**'ya bas
- Her hisse bir **kart** olarak gelir (kartı nasıl okuyacağın aşağıda)
- Her kartın altında **📈 Grafik & Teknik Analiz** açılır bölümü
- ☆ ile izleme listesine ekle

### 💼 Cüzdan
Sanal cüzdan (paper trading) — gerçek para riski olmadan deneme.
- Komisyonlu alım-satım
- Kâr/zarar takibi, günlük karne

### ⭐ İzleme
Takip ettiğin hisseler + fiyat alarmları.
- "Keşke alsaydın" analizi (kaçırdığın fırsatları gösterir)
- Hedef ilerleme takibi

### 📈 Backtest
"Bu strateji geçmişte çalışsaydı ne kazandırırdı?"
- **Sinyal Geçmişi & Karne**: sistemin geçmiş sinyallerinin başarı oranı (öz-ölçüm)
- **Strateji Backtest**: bir hissede stratejinin tarihsel performansı

### 🔥 Isı Haritası
Paranın hangi sektöre aktığını tek bakışta gösterir.
- **🧭 Para Akış Yönü**: hangi sektöre para giriyor/çıkıyor, lider hisse
- Sektör ısı çubukları

### 🤖 Robot
Otomatik strateji robotu — kendi başına alım-satım yapar.
- İki mod: Disiplinli / Basit
- Dinamik rotasyon (zayıf pozisyonu güçlüyle değiştirir)
- **🛡️ Piyasa Rejimi Freni**: borsa kötüyken robot savunmaya geçer (risk-off)
- **🎓 Robot Karnesi**: öz-puanlama (A-F notu), günlük/haftalık/aylık/yıllık getiri
- **🎯 Risk-Düzeltilmiş Kalite**: Sharpe, Sortino, Max Düşüş — "şanslı mıydı yoksa iyi mi", mevduatı yeniyor mu

### 🧭 Yol Haritası
Projenin hafızası ve vizyonu.
- **📍 ŞU AN BURADAYIZ** şeridi: sürüm ve sıradaki adım
- 6 katmanlık gelişim planı
- Tamamlanan tüm özellikler

---

## 🃏 Bir Hisse Kartını Nasıl Okurum?

Kart yukarıdan aşağıya şöyle:

1. **Alarm bandı** (varsa) → kart titreşiyorsa kritik olay yakın. Renk anlamı:
   - 🟢 Yeşil titreşim = altın kesişim/kırılım yakın (fırsat)
   - 🔴 Kırmızı titreşim = ölüm kesişimi yakın (tehlike)
   - 🟦 Turkuaz = dip bölgesi, 🟠 Turuncu = zirve bölgesi

2. **Karar şeridi** → En önemli satır. Baş analistin verdiği:
   - 🟢 **ŞİMDİ AL** = şartlar hizalandı, fırsat penceresi açık
   - 🟢 **AL / İZLE** = alım için uygun zemin
   - 🔵 **İZLE** = olumlu ama tetik yok
   - 🟡 **BEKLE** = karışık sinyaller
   - 🔴 **UZAK DUR** = tuzak/tehlike (gerekçesiyle)
   - Yanında **AV SKORU** (0-100) ve tek cümle gerekçe
   - Altında **zaman dilimi onayı** (✓✓ haftalık trend yukarı / ⚠⚠ ters)

3. **Hisse kodu + sektör + 🐋 büyük oyuncu** rozeti

4. **Güven bandı** → Güven yüzdesi + niyet + rüzgar rozeti

5. **Hedef / Stop / Risk-Ödül** → Nereden çık

6. **Pozisyon yönetimi** → Kaç lot, ne kadar TL, max kayıp + 🌡️ volatilite rejimi

**📈 Grafik açılır bölümünde** (karta dokun):
- 🌡️ Volatilite rejimi + strateji önerisi
- 📊 Kurumsal seviyeler (POC, değer alanı, VWAP)
- 🧬 DNA (karakter + rol + sinyal uyumu)
- Grafik (altın kesişim vb. işaretli) + tek cümle yorum

---

## 🔍 Neden Bu Karar? (Şeffaflık Paneli)

Her hissenin grafik açılır bölümünde **"Neden bu karar?"** paneli var. Bu, güvenin kalbidir:
- **✓ LEHTE**: kararı destekleyen her faktör
- **✗ ALEYHTE / RİSK**: riskler asla gizlenmez, hep gösterilir
- **? BELİRSİZ**: sistemin emin olmadığı şeyler
- **📊 Sicil**: bu tip sinyal geçmişte yüzde kaç hedefe ulaştı (dürüst)
- **Dürüstlük seviyesi**: GÜÇLÜ ZEMİN / MAKUL / DİKKATLİ OL

Sistem sana %100 eminmiş gibi davranmaz — emin olmadığında söyler. Gerçek güven buradan doğar: ne zaman güveneceğini **ve ne zaman güvenmeyeceğini** bilirsin.

---

## 🛡️ Seni Koruyan Özellikler (Risk Yönetimi)

Sistem sadece "al" demiyor, seni tuzaklardan da koruyor:

- **Manipülasyon tespiti** → Dağıtım/sürü deseni varsa skoru yüksek olsa bile "UZAK DUR"
- **Karşı rüzgar uyarısı** → Borsa/sektör aleyhteyse güven düşer
- **Zaman dilimi çelişkisi** → Düşüşte sahte sıçramayı yakalar
- **Sektör yığılma uyarısı** → Tek sektöre fazla yüklenince uyarır
- **Volatilite adaptasyonu** → Fırtınada pozisyon küçülür, stop genişler
- **Piyasa rejimi freni** → Robot kötü piyasada savunmaya geçer
- **Genişlik/ıraksama uyarısı** → İçi boş yükselişi önceden görür
- **Strateji uyumu** → Salınım hissesine momentum sinyali = tuzak uyarısı

---

## 💡 Kullanım İpuçları

- **Güne Radar'dan başla** — sistem sana nereye bakacağını söyler
- **Karar şeridine güven ama gerekçesini oku** — neden öyle dediğini anla
- **Kart titreşiyorsa** önce ona bak — kritik olay yakın
- **UZAK DUR'a saygı göster** — sistem seni bir sebepten uyarıyor
- **Robot karnesinde Sharpe'a bak** — yüksek getiri tek başına yetmez, kaliteli mi?
- **Piyasa sağlığı zayıfsa** temkinli ol — birkaç hisse iyi olsa bile genel hava kötü olabilir

---

## ⚠️ Önemli Hatırlatma

Bu uygulama bir **karar destek aracıdır**, yatırım tavsiyesi değildir. Tüm analizler teknik veriye dayanır ve veriler gecikmeli olabilir. Kararların sonuçları sana aittir. SPK lisanslı bir yatırım danışmanı değildir.

---

*Bu rehber, sistemin o anki tüm özelliklerini yansıtır. Yeni özellik eklendikçe güncellenir.*
