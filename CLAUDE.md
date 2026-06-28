# CLAUDE.md — APEX Proje Talimatları

Bu dosya, bu repoda otomatik çalışan Claude için tek doğruluk kaynağıdır.
Her kod değişikliği, her öneri bu kurallara uymak zorundadır.
Bir kural ile kullanıcının anlık isteği çelişirse, **dur ve sor** — varsayma.

> NOT (28 Haz 2026): Bu belge canlı sisteme göre güncellendi. Eski sürüm "Projektör"ü
> Supabase + Telegram + 4 ayrı motorlu bir mimari olarak tarif ediyordu; o mimari KURULMADI.
> Canlı sistem tek dosyalık `app.py`'dir (aşağıya bakın). İlkeler korundu, mimari/akış/deploy
> bölümleri gerçeğe çekildi.

---

## 1. Proje Kimliği

- **Ad:** APEX — BIST (Borsa İstanbul) için analiz terminali.
- **Geliştirici:** Tek kişilik (solo). Türkçe konuşur; kod, değişken ve yorumlar Türkçe.
- **Yığın (canlı):** Python · Streamlit Community Cloud · GitHub Actions (cron + CSV ile kalıcılık) · yfinance.
- **Yığın (opsiyonel/gelecek, ŞU AN KULLANILMIYOR):** Supabase, Telegram. Kod bunlara bağımlı değildir;
  birini eklemek ayrı bir karardır, varsayılan değildir.
- **Kısıt:** SPK lisansı yok. Veri 15 dk gecikmeli/EOD. Strateji swing/pozisyonel — gün içi execution DEĞİL.

---

## 2. AMAÇ (en önemli bölüm — önce bunu oku)

APEX'in amacı **"mevduatı her gün yenen sihirli robot" DEĞİLDİR.** Bu hedef test edildi ve
çürütüldü (bkz. Bölüm 4). İki gerçek değer ekseni var:

1. **Risk disiplini (DOĞRULANMIŞ).** Hisseye-özel vol-target pozisyon boyutlama gerçek BIST
   verisinde test edildi: gerçekleşen MaxDD her bütçenin altında kaldı. Perakendenin asıl para
   kaybettiği yer burası; APEX'in kanıtlanmış değeri budur.
2. **Bağlam — göremediğini göstermek (AKTİF YÖN, kanıtlanmamış).** Kullanıcı 94 hissenin KAP'ını,
   haberini, makro bağlantısını aynı anda izleyemez. APEX bunu onun yerine yapar.

Metrik "getiri" değil. Yeni metrik: **"Kullanıcının manuel kaçıracağı gerçek bir şeyi gösterdim mi?"**
Bir hisse hareket ediyorsa arkasında görünür sebep (KAP, haber, makro) var mı — bunu söyle.
Sebepsiz hareket = spekülatif/manipülatif uyarısı.

**Asla gelecek fiyat tahmini uydurma. Asla "şu hisse %X yapacak" deme.** Bağlam göster, karar kullanıcının.
(Uygulamadaki "Modelin tahmini" listesi bir momentum proxy'sidir, ±%40 tavanlı ve "sicil ~%49 ≈
yazı-tura" damgalıdır — getiri vaadi DEĞİL, dürüstçe etiketli bir göstergedir.)

---

## 3. NASIL ÇALIŞACAKSIN (sert kurallar)

1. **Para/risk dokunan mantığı tek başına değiştirme.** Pozisyon büyüklüğü, stop, drawdown,
   sinyal eşikleri, vol-target/ATR parametreleri, backtest çıtaları — bunlara dokunan her
   değişikliği AÇIKÇA özetle ve "bu sayıyı/mantığı değiştiriyorum, onayla" diye işaretle. Onaysız değiştirme.
2. **Belirsizsen sor.** Çok yorumlu görevde varsayım yapma; kod yerine açıklayıcı yorum bırak.
3. **Küçük, odaklı değişiklikler.** Tek seferde bir şey. Dev refactor'lardan kaçın.
4. **Mevcut kod desenine ve dosya isimlerine uy.** İsimleri kendiliğinden "düzeltme".
5. **Commit akışı (solo, tek-dosya gerçeği):** İnsan kod değişiklikleri GitHub web editöründen
   doğrudan `main`'e gider (bu projede PR zorunlu değil; akış hızlı ve tek kişilik). ANCAK §1-§2
   ve Bölüm 5 dürüstlük kuralları + yukarıdaki "para mantığında onay iste" kuralı her zaman geçerli.
6. **Otomasyon istisnası:** GitHub Actions cron'u (`gunluk_log.py`) `ileri_gunluk.csv`'yi her iş günü
   doğrudan `main`'e commit eder — bu SERBESTtir ve sistemin çalışması için gereklidir. Bot
   commit'lerini engelleme.

---

## 4. NE ÖNERME / TEKRAR DENEME (acı yoldan öğrenildi)

Aşağıdakilerin hepsi backtest'te mevduat + endeks çıtasını birlikte geçemedi.
**Bunları yeni fikirmiş gibi tekrar önerme:**

- Per-stock ML · Pooled/cross-sectional ML (AUC ~0.55, yıllık net −8.4%)
- Ham teknik sinyaller (RSI/MACD/CMF tek başına)
- "Doğru vadeyi seç" (gün içi/günlük/haftalık ayrımı)
- MA200 rejim anahtarı
- **Makro reel-faiz zamanlaması:** eşik taramasını ve gecikme stresini GEÇTİ ama **plasebo testinde
  çöktü** — mevduatı/endeksi geçen şey zamanlama becerisi değil, yükselen 8 yılda uzun-hisse betası.
  "Kanıtlanmış edge" diye sunma; "ileri-test edilmeye değer aday" de.

Ortak kusur: **hepsi yalnızca fiyat-hacim serisine bakıyor.** Edge varsa fiyatın DIŞINDADIR
(metin: KAP, haber, makro, takas akışı). Yeni öneriler bu kuralı dikkate almalı.

---

## 5. DÜRÜST MÜHENDİSLİK İLKELERİ

- **Sonuç uydurma.** Backtest/getiri/AUC — gerçek çalıştırma çıktısı olmadan rakam yazma. Tahminse "tahmin" de.
- **Test edemediğin dış kaynağı "otomatik" diye sunma.** (Örn: tam-oto makro feed test edilemedi diye
  YAPILMADI; makro `makro_guncel.json` ile yarı-oto bırakıldı. Bu dürüstlüğü koru.)
- **Bug'ı söyle, gizleme.** Geçmişte `ai_model.py`'da sessiz "sahte sıfır" bug'ı vardı. Böyle bir şey
  görürsen DUR ve bildir — üstünü örtme.
- **Overfit'e karşı şüpheci ol.** Komşu parametre değerlerinde de dayanıklı mı? Eğri uydurma ≠ edge.
- **Leakage yok.** Karar t kapanışında, getiri t+1. Geleceğe bakan hesap kabul edilmez.
- **Maliyet gerçekçi.** Komisyon + slippage + stop kayması her backtest'te dahil.

---

## 6. LLM'İN YERİ (çok net sınır)

- **LLM çekirdek sayısal hatta GİRMEZ.** Sinyal matematiği, Sharpe/Sortino, vol-target, ATR,
  backtest, walk-forward → deterministik NumPy/pandas işidir. LLM'e yaptırma.
- **LLM yalnızca METİN/BAĞLAM katmanında değer katar:** KAP özeti, haber sentiment, makro bağlam,
  "bu hareketin görünür sebebi var mı". Yeni değer buradan gelir.
- Metin katmanı için varsayılan **Claude Sonnet 4.6**; kritik/karmaşık kod için **Claude Opus 4.8**.

---

## 7. AKTİF YÖN: "Projektör" — YALIN sürüm (app.py üstüne)

Eski belge bunu ağır bir mimari (Supabase + Telegram + 4 motor) olarak tarif ediyordu. **O yol
seçilmedi** — solo bir projede karmaşa/maliyet/arıza üretir. Yön doğru ama uygulaması yalın:

- **Mevcut `app.py`'ye EK ÖZELLİK olarak gir.** Re-platform YOK. Supabase/Telegram opsiyonel, sonra.
- **İlk tuğla = KAP** (Kamuyu Aydınlatma Platformu). Ücretsiz, lisanssız, en yüksek sinyalli metin.
- **Deterministik başla:** günün hareket eden hisselerini KAP açıklamalarıyla eşleştir →
  "bu hareketin görünür sebebi var (KAP: …)" ya da "sebep yok → spekülatif uyarı". LLM özetleme SONRA.
- **Dürüst sınır:** Bağlam katmanının değeri KANITLANMAMIŞ. Metrik §2'deki gibi "kaçıracağını
  gösterdim mi" — getiri değil, karar-desteği. Risk çekirdeğindeki aynı disiplinle parça parça kur, ölç.
- **Dış kaynak kuralı:** KAP fetch'i test edilmeden "çalışıyor" deme; gerçek çalıştırmayla doğrula,
  başarısızsa zarif fallback ("KAP bağlanamadı"), sahte veri ASLA.

---

## 8. CANLI SİSTEM (otonom Claude bunu bilmeli)

- **Canlı kod = tek dosya `app.py`** (28 Haz 2026 itibarıyla v1.8). 5 mod: Pusula/Havuz/Trade/Defter/Nabız.
  HTML arayüz `apex_omurga_v1.html` şablonuna `__APP_DATA__` enjekte edilerek render edilir; `build_html`
  şablonu bellekte yamalar (örn. Defter eğrisi). **Şablonu elle düzenleme; app.py üstünden yama yeterli.**
- **Kalıcılık & otomasyon:** `gunluk_log.py` + `.github/workflows/gunluk.yml` (hafta içi 15:30 UTC) →
  `ileri_gunluk.csv` (ileri-test = tek dürüst OOS). Defter eğrisi bunu çizer.
- **Makro:** `makro_guncel.json` varsa rejim onu okur, yoksa app.py içindeki statik tabloya düşer.
  Güncellemek = JSON'daki 2 sayıyı değiştirmek (çeyreklik, elle).
- **Çıkarılmış edge'ler:** Getiri tahmini kanıtlanmadı. Doğrulanmış tek eksen = risk disiplini
  (vol-target Poz + ATR(14) stop). Tahmin listesi ±%40 tavanlı, "sicil %49" damgalı.
- **ESKİ DOSYALAR (analiz.py, karar.py, robot.py, ai_model.py vb.):** Önceki çok-modüllü snapshot'tan.
  Canlı sistem bunları KULLANMIYOR — referans/arşiv. `app.py` tek kaynak.

---

## 9. DEPLOYMENT PROTOKOLÜ

- **Deploy:** Tek dosya `app.py`, GitHub web editöründen güncellenir (Ctrl+A → yapıştır → Commit).
  Bu projede kopyala-yapıştır test edildi, encoding/girinti sorunu çıkmadı.
- **Tazeleme:** `app.py` içindeki `SURUM` sabiti artırılır (v1.9, v2.0…). `_veri(_surum=SURUM)` cache
  anahtarı sayesinde Streamlit **reboot gerekmeden** tazelenir. Reboot SADECE cache takılırsa gerekir
  (share.streamlit.io → Reboot). "Tam reboot zorunlu" kuralı artık geçerli değil — cache anahtarı daha iyi.
- **Workflow dosyaları (`.github/workflows/`):** GitHub güvenlik kuralı GITHUB_TOKEN'ın buraya yazmasını
  engeller — bu dosyalar kullanıcı tarafından web UI'dan ELLE oluşturulur.
- Gizli anahtarlar (API key, token) ASLA koda yazılmaz; Streamlit Secrets'ta tutulur.
- Repo: `ysfyprk3438-debug/bist-tarama` (main).

---

## 10. KODLAMA STANDARTLARI

- Python, okunabilir, Türkçe değişken/yorum. Saf fonksiyonlar tercih; yan etkileri izole et.
- Her yeni sinyal/strateji leakage'sız + maliyetli backtest'te test edilebilir olmalı.
- "İyileştirdim" demeden önce: ölçülebilir mi, hangi çıtaya karşı, kanıt ne?
- Yeni bağımlılık eklerken gerekçesini commit mesajında belirt.

---

> Özet: Para mantığına dokunurken onay iste, sonuç uydurma, test edemediğini "otomatik" diye sunma,
> bug gördüğünde söyle, çekirdek matematiği LLM'e verme. Canlı sistem = tek dosya app.py + Actions/CSV.
> Aktif yön = app.py üstüne YALIN KAP bağlam katmanı. Ve her zaman gerçek amacı hatırla:
> **kullanıcıya göremediği bağlamı göstermek + riskini disipline etmek.**
