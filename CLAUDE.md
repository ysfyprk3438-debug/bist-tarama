# CLAUDE.md — APEX Proje Talimatlari (KONSOLIDE · 28 Haz 2026)

Bu dosya, bu repoda otomatik calisan Claude (@claude GitHub Action) ve sohbetteki
Claude icin TEK dogruluk kaynagidir. Iki ayri oturumun kararlari burada birlestirildi.
Bir kural ile anlik istek celisirse: **dur ve sor.** Varsayma.

> Bu surum, onceki "solo dogrudan-main" taslagini DUZELTIR. Repoda @claude/PR akisi
> fiilen kuruldu ve calisiyor; akis artik PR-onceliklidir (bkz. Bolum 3).

---

## 1. Proje Kimligi
- **Ad:** APEX — Borsa Istanbul (BIST) icin analiz/baglam terminali. Solo gelistirici, Turkce.
- **Yigin (canli):** Python · Streamlit Community Cloud · GitHub Actions (cron + dosya kaliciligi) · yfinance.
- **Otomasyon:** Claude Code GitHub Action (`.github/workflows/claude.yml`), secret `CLAUDE_CODE_OAUTH_TOKEN`,
  Claude GitHub App kurulu. @claude ile tetiklenir; her PR'da otomatik inceleme calisir.
- **Opsiyonel/gelecek:** Telegram (gunluk rapor hedefi), Supabase (su an yok).
- **Kisit:** SPK lisansi yok. Veri 15 dk gecikmeli/EOD. Swing/pozisyonel — gun-ici execution DEGIL.

## 2. AMAC (en onemli bolum)
Eski hedef ("mevduati her gun yenen robot") test edildi, CURUTULDU. Yeni amac:
> **Kullaniciya kendi gozuyle goremedigi BAGLAMI gostermek.**

Metrik "getiri" degil: **"manuel olarak kacirilacak gercek bir seyi gosterdim mi?"**
Bir hisse hareket ediyorsa gorunur sebep (KAP, haber, makro) var mi — soyle.
Sebepsiz sert hareket = spekulatif/temkin uyarisi. **Asla gelecek fiyat tahmini uydurma;**
baglam goster, karari kullanici verir. (Uygulamadaki "tahmin" listesi momentum proxy'sidir,
±%40 tavanli, "sicil ~%49 ≈ yazi-tura" damgali — getiri vaadi DEGIL.)

Iki gercek deger ekseni:
1. **Risk disiplini (DOGRULANMIS):** hisseye-ozel vol-target Poz + ATR(14) stop. Gercek BIST'te MaxDD butce alti.
2. **Baglam (AKTIF, kanitlanmamis):** KAP/haber/makro'yu kullanici yerine tarayip "gorunur sebep" cikarmak.

## 3. NASIL CALISILACAK (sert kurallar)
1. **Kod degisikligi = @claude/PR akisi.** Kucuk net issue → @claude branch'te yazar, PR acar →
   otomatik inceleme (leakage / sessiz bozulma / para-risk / uydurma sonuc) → **kullanici diff'e bakip MERGE eder.**
   Gercek onay kapisi = insan merge. Otomatik inceleme yardimcidir, ONAYLAYICI DEGIL (§5 yanki-odasi riski).
2. **Para/risk mantigina dokunan her degisiklik** (poz boyutu, stop, drawdown, esikler, vol/ATR, backtest citasi)
   PR aciklamasinda ACIKCA isaretlenir; merge oncesi ekstra dikkat.
3. **Dogrudan-main istisnasi (PR'siz):** SADECE otomasyon botunun veri commit'leri
   (`ileri_gunluk.csv`, ileride `kap_gunluk.json` vb. cron ciktilari). Insan kodu daima PR.
4. **Belirsizsen sor.** Kucuk/odakli degisiklik; mevcut dosya ismi ve desenine uy; isimleri kendiliginden duzeltme.

## 4. NE ONERME / TEKRAR DENEME (aci yoldan ogrenildi)
Hepsi backtest'te mevduat + endeks citasini BIRLIKTE gecemedi:
- Per-stock ML · Pooled/cross-sectional ML (AUC ~0.55, yillik net −8.4%)
- Ham teknik sinyaller (RSI/MACD/CMF tek basina) · Vade secimi · MA200 rejim anahtari
- **Makro reel-faiz zamanlamasi:** esik taramasini gecti ama PLASEBO'da coktu — yukselen 8 yilin
  uzun-hisse betasi, zamanlama becerisi degil. "Kanitlanmis edge" deme; "ileri-test edilmeye deger aday" de.

Ortak kusur: hepsi YALNIZCA fiyat-hacme bakiyor. Edge varsa fiyatin DISINDA (metin: KAP, haber, makro, takas).

## 5. OTOMASYON FELSEFESI (kapali dongu KURULMAZ)
**KURULMAZ:** Onaysiz main'e commit eden, kendi sorusunu kendi onaylayan kapali dongu.
- Sessiz bug felaketi (gecmisteki "sahte sifir" bug'i gibi — kimse bakmasa fark edilmezdi).
- Kendi ciktisini onaylayan LLM hata bulmaz, varsayimini pekistirir (yanki odasi).
- Asil amaca ters: kara kutu korlestirir.

**KURULUR — "onayli otomasyon":** gunluk baglam taramasi otomatik · gunluk rapor otomatik
(Telegram: "su hissede aciklama var, sunda sebepsiz hareket") · kod gelistirme = @claude PR onerir,
kullanici merge eder · kritik kararda kullanici kapida, gerisi otomatik.

## 6. LLM'IN YERI (net sinir)
- LLM cekirdek sayisal hatta GIRMEZ: sinyal matematigi, Sharpe/Sortino, vol-target, ATR, backtest,
  walk-forward → deterministik NumPy/pandas.
- LLM yalniz METIN/BAGLAM katmaninda deger katar: KAP ozeti, haber sentiment, makro baglam,
  "bu hareketin gorunur sebebi var mi".
- Metin katmani: Claude Sonnet 4.6. Kritik/karmasik kod: Claude Opus 4.8.

## 7. YOL HARITASI: Projektor (parca parca, kucuk @claude issue'lari)
```
baglam_motor.py  → KAP + hareket eden hisseleri tara        [SIRADAKI]
      ↓
hikaye_motor.py  → sebep var mi, ne anlama geliyor (Sonnet/Opus)
      ↓
projektor.py     → gunluk ozet (sinyal + baglam + risk notu)
      ↓
Telegram         → gunluk tek mesaj
```
- **KAP temeli HAZIR:** `kap_oku.py` — `POST kap.org.tr/tr/api/disclosure/members/byCriteria`,
  alanlar `relatedStocks`/`stockCodes`/`subject`/`publishDate`/`disclosureIndex`. Hem TR hem ABD-IP'den
  calistigi dogrulandi (368 aciklama). Baglanamazsa zarif fallback (`_durum: kapali`), SAHTE VERI YOK.
  `baglam_motor.py` bunu yeniden kullanir — sifirdan KAP cozmez.
- **Dis kaynak kurali:** test edilmeden "calisiyor" deme; gercek calistirmayla dogrula, basarisizsa fallback.

## 8. CANLI SISTEM (mevcut durum)
- **app.py** (tek dosya, v1.8 canli): 5 mod Pusula/Havuz/Trade/Defter/Nabiz; `apex_omurga_v1.html`
  sablonuna `__APP_DATA__` enjekte. Risk ekseni (hisse-basi vol-target Poz + ATR stop) + ileri-test egrisi calisir.
- **Ileri-test (tek durust OOS):** `gunluk_log.py` + `.github/workflows/gunluk.yml` (hafta-ici 18:30 TR)
  → `ileri_gunluk.csv`; app `ileri_seri()` ile okur. Risk/rejim-durus disiplinini olcer, getiriyi OLCMEZ.
- **Makro:** `makro_guncel.json` (varsa rejim onu okur, yoksa statik tablo). Ceyrekte bir 2 sayi elle.
- **ESKI cok-modullu dosyalar** (analiz.py, karar.py, robot.py ...): arsiv/referans; canli sistem KULLANMIYOR.

## 9. DEPLOYMENT PROTOKOLU
- **Kod git ile gelir** (@claude PR merge) — kopyala-yapistir YOK. Streamlit, main'e push'ta yeniden yayinlar.
- **Tazeleme:** app.py icindeki `SURUM` sabiti artirilir (`_veri(_surum=SURUM)` cache anahtari);
  bu oturumda reboot GEREKMEDEN tazeledigi dogrulandi. Cache takilirsa tam reboot (share.streamlit.io → Reboot).
- **Workflow dosyalari (`.github/workflows/`):** GITHUB_TOKEN buraya yazamaz → bunlar kullanici tarafindan
  web UI'dan ELLE olusturulur (claude.yml, gunluk.yml boyle eklendi).
- **Sirlar** (token/API key) ASLA koda yazilmaz; GitHub Secrets'ta (`CLAUDE_CODE_OAUTH_TOKEN` orn.).
- Repo: `ysfyprk3438-debug/bist-tarama` (main).

## 10. KODLAMA STANDARTLARI
- Python, okunabilir, Turkce degisken/yorum. Saf fonksiyon tercih; yan etkiyi izole et.
- Her yeni sinyal/strateji leakage'siz + maliyetli (komisyon+slippage) backtest'te test edilebilir olmali.
- Karar t kapanisinda, getiri t+1 (gelecege bakma yok). "Iyilestirdim" demeden once: olculur mu, hangi citaya karsi, kanit ne?

## 11. AKD GORSEL ISLEME PROTOKOLU (yari-otomatik besleme)
Amac: ForInvest AKD ekranlarini elle CSV'ye gecirme yukunu azaltmak — ama RAKAM DOGRULAMASI insanda kalir.

**Tetik:** Kullanici bir issue'ya (tercihen `[AKD]` onekli, `akd-besleme` sablonu) ForInvest AKD ekran
goruntulerini yapistirir + hisse adi ve donem tipini (gunluk/haftalik/aylik/3aylik) yazar + `@claude`'u etiketler.

**@claude gorevi:**
1. Goruntulerden OKU: donem (`tarih_baslangic`/`tarih_bitis`), `ilk5_net_lot` (Ilk-5 net lot),
   `lider_alici` + `lider_alici_pct`, `lider_satici` + `lider_satici_pct`, varsa `custodian_net_lot`
   (BofA/Citi/Deutsche gibi saklamacilarin net toplami).
2. `akd_manuel_arsiv.csv` semasina YENI SATIR(lar) olarak ekle — mevcut kolon sirasi birebir korunur.
3. OKUNAMAYAN alani BOS birak — TAHMIN ETME, uydurma YOK. Bulanik/kesik ise bos + `not` alanina "gorsel belirsiz".
4. **PR AC — DOGRUDAN main'e YAZMA.** Rakamlarin dogrulugu insan gozuyle diff'te kontrol edilir, sonra insan merge eder.
5. Idempotent ol: ayni (`hisse`, `tarih_bitis`) zaten arsivde varsa tekrar EKLEME; PR aciklamasinda belirt.
6. PR aciklamasina okudugun her satiri "gorselden su okundu" seklinde YAZ ki insan hizli dogrulayabilsin.

**Sinir:** Bu hat SADECE veri girisi. `akd_sicil.py` mantigina/desenlere DOKUNMA — sicil, arsiv + canli
fiyattan otomatik yeniden hesaplanir. Yon tahmini / AL-SAT dili YOK (bkz. Bolum 2). Bekci, arsiv 35+ gun
bayatlarsa SARI uyarir (besleme hatirlatmasi).

---
> Ozet: Insan kodu PR'dan gecer, insan merge eder (kapi). Bot veri commit'leri main'e dogrudan.
> Cekirdek matematik deterministik; LLM yalniz baglam/metin. Sonuc uydurma, test edemedigini
> "otomatik" diye sunma, bug gorunce soyle. Siradaki: baglam_motor.py (@claude issue) — kap_oku.py uzerine.
