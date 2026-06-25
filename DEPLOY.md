# 🚀 DEPLOY KONTROL LİSTESİ — BIST Para Avcısı v4.1

Akşam canlıya almak için adım adım. Sırayla takip et.

---

## 📦 YÜKLENECEK 30 DOSYA

GitHub'a (`github.com/ysfyprk3438-debug/bist-tarama`, main branch) bu dosyaların **en güncel hallerini** koyacaksın. Hepsi `/mnt/user-data/outputs/` içinde hazır.

### Ana uygulama (1)
- `app.py` — ana uygulama, 9 sekme

### Veri & analiz çekirdeği (4)
- `veri.py` — çift kaynaklı veri (Yahoo + İş Yatırım)
- `analiz.py` — ana analiz motoru (tüm katmanları birleştirir)
- `karar.py` — karar sentezleyici (av skoru)
- `cuzdan.py` — sanal cüzdan

### Arayüz (1)
- `arayuz.py` — kart bileşenleri, HTML

### Analiz katmanları (16)
- `niyet.py` — niyet okuma + güven motoru
- `ruzgar.py` — rüzgar yönü
- `alarm.py` — yaklaşan olay + geri sayım
- `volatilite.py` — volatilite rejimi
- `karakter.py` — Hurst + relatif güç + strateji uyumu
- `hacim.py` — VWAP + hacim profili
- `zaman.py` — çoklu zaman dilimi onayı
- `grafik.py` — grafik + teknik olay
- `genislik.py` — piyasa genişliği (breadth)
- `seffaflik.py` — şeffaflık paneli (neden bu karar?)
- `strateji.py` — strateji seçici (Katman 4)
- `psikoloji.py` — kalabalık psikolojisi (Katman 5)
- `fibonacci.py` — Fibonacci + pivot seviyeleri
- `kalibrasyon.py` — kendini kalibre etme (Katman 1)
- `piyasa.py` — sektör rotasyonu + rejim freni + çeşitlendirme
- `radar.py` — fırsat radarı

### Araçlar & modüller (4)
- `backtest.py` — backtest + sektör ısı
- `robot.py` — otomatik robot
- `gecmis.py` — sinyal geçmişi + öz-ölçüm + Supabase
- `performans.py` — robot karnesi + Sharpe/Sortino

### Hafıza & rehber (3)
- `yol_haritasi.py` — yol haritası sekmesi
- `durum.py` — kontrol noktası
- `REHBER.md` — kullanım rehberi

### Bağımlılıklar (1)
- `requirements.txt` — streamlit, pandas, numpy, requests, matplotlib

---

## ✅ ADIM ADIM DEPLOY

### 1. requirements.txt'i güncelle (ilk!)
GitHub'da `requirements.txt` aç → içeriğini şununla değiştir:
```
streamlit
pandas
numpy
requests
matplotlib
```

### 2. app.py'i güncelle
GitHub'da `app.py` aç → tüm içeriği sil → yeni app.py'i yapıştır → commit.

### 3. Diğer 28 .py dosyasını ekle/güncelle
Her biri için: "Add file" veya mevcut dosyayı aç → içeriği değiştir → commit.
**İpucu:** Tek tek yapmak yorucuysa, Claude'a "şu dosyayı ver" diyerek her dosyayı sırayla alabilirsin.

### 4. REHBER.md'i ekle
Kullanım kılavuzu — uygulamada Yol Haritası sekmesinde özeti var, tam hali bu dosyada.

### 5. Streamlit otomatik deploy
Commit'ler bitince Streamlit Community Cloud otomatik yeniden derler (1-2 dk). Hata olursa "Manage app → Logs"a bak.

---

## 🔬 İLK CANLI TEST (Claude ile birlikte)

Deploy bitince, **birlikte dikkatle inceleyeceğiz:**

1. **İlk taramayı yap** (Haftalık vade öner) → kaç saniyede bitiyor?
2. **"Veri gelmeyen hisse" sayısı** → çoğu hisse veri çekebiliyor mu? (Tarama log'una bak)
3. **Eşikler mantıklı mı?** → Kaç sinyal çıktı? Çok mu az, çok mu fazla?
4. **Radar dolu mu?** → ŞİMDİ/YAKLAŞAN fırsatlar görünüyor mu?
5. **Bir kartı aç** → karar, güven, DNA, kurumsal seviyeler, şeffaflık paneli düzgün mü?
6. **Piyasa sağlığı + bugünün oyunu + korku/açgözlülük** → gerçek veriyle mantıklı mı?

### Gerçek veride ayar gerekebilecek eşikler (normal!):
- RSI sinyal aralıkları (35-65)
- Hurst trend/salınım eşikleri
- Volatilite rejim sınırları
- Alarm geri sayım hassasiyeti
- Korku/açgözlülük bileşen ağırlıkları

Bunları **birlikte canlı veriye göre kalibre edeceğiz** — modüler yapı sayesinde kolay.

---

## 🗄️ SUPABASE BAĞLAMA (test sonrası)

Sinyal geçmişi + robot karnesi + kalibrasyonun kalıcı olması için:
1. Supabase projesinde tablo hazır mı kontrol et
2. `gecmis.py` içindeki Supabase URL/key ayarını gir
3. İlk sinyaller kaydedilsin → kalibrasyon (Katman 1) zamanla devreye girecek

**Önemli:** Şeffaflık panelindeki "sicil" (%X hedefe ulaştı) ve sistem olgunluğu, ancak gerçek sinyaller biriktikçe dolacak. Güven, kanıtla gelecek.

---

## ⚠️ HATIRLATMA
Bu bir karar destek aracıdır, yatırım tavsiyesi değildir. SPK lisanslı değildir. Tüm kararlar kullanıcıya aittir.

---

*30 modül, 6 katmanın 5'i tamamlandı. Motor hazır — şimdi yola çıkma zamanı. 🚀*
