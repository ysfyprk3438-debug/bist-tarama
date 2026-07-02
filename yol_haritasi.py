"""
═══════════════════════════════════════════════════════════════
YOL HARİTASI — APEX
═══════════════════════════════════════════════════════════════
Bu dosya projenin HAFIZASI ve PUSULASIDIR. "Sonra yaparız"lar burada yaşar.
Yeni oturumda nereye gittiğimizi unutursak buraya bakarız.

═══ FELSEFE (projenin kalbi) ═══
APEX bir getiri kâhini DEĞİL, bir RİSK PUSULASI ve karar-destek aracıdır.
Yıllarca süren rigorlu backtest tek bir şeyi öğretti: teknik/momentum/temel
seçim ve makro zamanlama HEPSİ out-of-sample ve placebo testlerinde çöktü.
Geriye doğrulanmış TEK eksen kaldı: volatilite-hedefli pozisyon boyutlama —
gerçekleşen düşüşü (drawdown) bütçe içinde tutan risk yönetimi.

Bu yüzden APEX'in amacı "zengin olmak" değil; KAYBETMEMEYİ, DİSİPLİNİ,
ALDANMAMAYI öğrenmek ve uygulamaktır. Kâr aranırsa, yön tahmininden değil,
iki dürüst kaynaktan aranır: (1) ELEME — çoğu fırsatı reddedip sadece
istatistiğin lehe eğildiği nadir anlarda işlem, (2) RİSK ASİMETRİSİ — kaybı
stop'la küçük, kazancı R/R ile büyük tutmak. Kazanılırsa, geleceği bildiği
için değil, yanlış yerde durmadığı ve kaybını yönettiği için kazanılır.

Durum kodları: ✅ yapıldı · 🔨 olgunlaşıyor · 🎯 sıradaki · 🔭 ufuk · 🔒 veri/altyapı bekliyor
"""

# ══════════════════════════════════════════════════════════════
# DOĞRULANMIŞ BULGULAR (pahalı öğrenilen gerçekler — asla unutma)
# ══════════════════════════════════════════════════════════════
DOGRULANAN = [
    "Vol-target pozisyon boyutlama ÇALIŞIR: tüm parametrelerde gerçekleşen MaxDD bütçe altında kaldı (gerçek BIST).",
    "Getiri tahmini = yazı-tura. Çok sayıda göstergeyi üst üste koymak sonucu değiştirmez, sadece daha ikna edici bir yazı-tura yapar.",
    "Makro rejim sinyali placebo B'de çöktü (55.7 persentil = medyan). Görülen üstün getiri ALPHA değil BETA'ydı (yükselen 8 yılda uzun kalmak).",
    "Multi-timeframe, seçim, momentum, MA200 zamanlama, temel, makro zamanlama: hepsi OOS ve/veya placebo'da başarısız.",
    "Dürüst lens: 'hangisinden kaçınmalı' > 'hangisini al'. Herkesin sinyal sandığının yön VERMEDİĞİNİ göstermek asıl değerdir.",
]

# ══════════════════════════════════════════════════════════════
# TAMAMLANANLAR
# ══════════════════════════════════════════════════════════════
TAMAMLANAN = [
    ("APEX ana panel — 5 mod (Pusula/Havuz/Trade/Defter/Nabız), gömülü HTML", "✅"),
    ("Vol-target pozisyon boyutlama (pozisyon.py) — doğrulanmış eksen", "✅"),
    ("Bulut kalıcılık (Google Sheets) — cüzdan + karar defteri, cihazdan bağımsız", "✅"),
    ("Otonom günlük ileri-test loglayıcı (gunluk_log.py + cron)", "✅"),
    ("Telegram hikaye pipeline (projektor.py, yön/hedef içermez)", "✅"),
    ("Sanal Borsa — native Streamlit, gerçek BIST, BIST100 havuz", "✅"),
    ("Kural-Tabanlı İşlem Planı Motoru — yönsüz durum + destek/direnç + R/R + sicil", "✅"),
    ("Beklenen Değer + PLACEBO — edge = kurulumun piyasa yönünün üstüne kattığı (beta/alpha ayrımı)", "✅"),
    ("AL Sinyali — çoklu süzgeç kesişimi (giriş+sicil+R/R+edge), seçici, her zaman sicil taşır", "✅"),
    ("Oto-simülasyon — kural-tetikli gir/çık, vol-target, yarı nakit, stop/hedef sabit, forward-test paneli", "✅"),
    ("veri.py taze-kapanış yaması canlı; Sanal Borsa fiyatları 2 ondalık Türk formatı", "✅"),
    ("@claude GitHub Actions akışı — issue/PR + otomatik PR incelemesi (CLAUDE_CODE_OAUTH_TOKEN)", "✅"),
    ("Repo temizliği — PR #14 merge, 42 ölü dosya arsiv/'e taşındı", "✅"),
    ("Bekçi — gece sağlık kontrolü (bekci.py + bekci.yml, hafta içi 18:45 TR): sözdizimi+fiyat "
     "tazeliği+CSV; yeşilse Telegram tek satır, bulguda BEKCI_PAT ile bekci etiketli issue + "
     "@claude görevlendirme, merge insanda", "✅"),
]

# ══════════════════════════════════════════════════════════════
# SIRADAKİ KATMANLAR
# ══════════════════════════════════════════════════════════════
KATMANLAR = [
    {
        "no": 0,
        "ad": "Forward-Test Birikimi — Tek Gerçek OOS",
        "durum": "🎯",
        "ozet": "Kural motoru + oto artık gerçek BIST verisinde ileri koşuyor. "
                "Backtest'in vaadi (beklenen değer/edge) ile gerçekleşenin yüzleştiği "
                "yer forward-test panelidir. Anlamlı yorum için haftalar-aylar veri şart.",
        "nasil": "Oto'yu açık tut, ilerlet. Paneldeki edge yeterli işlemle olgunlaşınca "
                 "gerçek mi yoksa yine beta mı BELLİ olur. Veri konuşur, biz tahmin etmeyiz.",
        "onkosul": "Yok — çalışıyor. Tek gereken: SABIR.",
    },
    {
        "no": 1,
        "ad": "Oto Sonuçlarını Ana Panele Bağlama",
        "durum": "🎯",
        "ozet": "Sanal Borsa oto forward-test sonuçlarını ana APEX paneline (Nabız/Defter) "
                "taşı. Ölçülmüş gerçek getiri — vaat değil, gerçekleşen. Uydurma yok.",
        "nasil": "Oto ledger özetini (isabet, gerçekleşen R, naif/mevduata göre) ana panele "
                 "bağla. karar_defteri (manuel) KİRLETİLMEZ — ayrı tutulur.",
        "onkosul": "Katman 0'dan bir miktar veri birikimi.",
    },
    {
        "no": 2,
        "ad": "Kendini Kalibre Eden Eşikler",
        "durum": "🔭",
        "ozet": "Kural motorunun eşikleri (sicil≥52, R/R≥1.5, edge>0.03) şu an SABİT. "
                "Yeterli forward-test verisi birikince, hangi kurulumun gerçekten edge "
                "taşıdığını öz-ölçümden görüp eşikleri veri-temelli ayarla. DİKKAT: bu "
                "overfit tuzağıdır — sadece placebo'yu geçen ayarlamalar meşrudur.",
        "nasil": "Forward-test biriktikçe edge'i gerçekleşenle doğrula. Eşik değişikliği "
                 "ancak placebo + OOS'ta korunuyorsa kabul. Aksi = eğip bükme, reddedilir.",
        "onkosul": "🔒 Katman 0 — anlamlı örneklem (aylar).",
    },
    {
        "no": 3,
        "ad": "Gerçek Mikroyapı — AKD/Takas",
        "durum": "🔨",
        "ozet": "Fiyat+hacim gölgesinden gerçek emir defteri + aracı kurum dağılımı (AKD) "
                "+ takas verisine. Toplama/dağıtım burada gölge değil somut iz bırakır. "
                "Ama yine YÖN TAHMİNİ DEĞİL — sadece risk/kaçınma lensini zenginleştirir. "
                "MANUEL köprü aşamasında: AKFGY doğrulaması yön VERMEDİ (tez teyit).",
        "nasil": "ForInvest AKD/takas manuel arşivini besle (yinelenen açık kalem). "
                 "Sıradaki somut adım: AKD desen→sicil etiketleyici — AKFGY manuel arşivi "
                 "ilk kayıt; her desene 1-yıl sicili iliştir, %40–60 isabette gri yazı-tura. "
                 "stockScreener çalışıyor; settlement/order-book backend şu an kapalı.",
        "onkosul": "🔒 ForInvest AKD/takas verisi (backend down — manuel arşiv).",
    },
]

# ══════════════════════════════════════════════════════════════
# AÇIK KALEMLER (kaybolmasın)
# ══════════════════════════════════════════════════════════════
ACIK_KALEMLER = [
    "Bekçi'nin ilk gerçek gece turunu izle (bekci.yml, hafta içi 18:45 TR).",
    "AKD desen→sicil etiketleyici (AKFGY manuel arşivi ilk kayıt).",
    "Doğrulanabilir makro oto-kaynak (TCMB coğrafi bloklu, OECD API kırılgan). Bulunursa cron'a ekle.",
    "Karar Günlüğü outcome resolution — kararlar olgunlaştıkça sonuç işle (placebo baz %50; %42 altı ters-seçim uyarısı).",
    "ForInvest AKD/takas manuel arşiv besleme.",
    "TG_TOKEN/SUPABASE_KEY rotasyonu (kritik değil).",
]


def yol_haritasi_metni():
    s = ["APEX — YOL HARİTASI\n" + "=" * 50]
    s.append(f"\nDOĞRULANAN ({len(DOGRULANAN)}):")
    for d in DOGRULANAN:
        s.append(f"  ✓ {d}")
    s.append(f"\nTAMAMLANAN ({len(TAMAMLANAN)}):")
    for ad, durum in TAMAMLANAN:
        s.append(f"  {durum} {ad}")
    s.append("\nKATMANLAR:")
    for k in KATMANLAR:
        s.append(f"  {k['durum']} K{k['no']}: {k['ad']}")
    s.append("\nAÇIK KALEMLER:")
    for a in ACIK_KALEMLER:
        s.append(f"  • {a}")
    return "\n".join(s)


if __name__ == "__main__":
    print(yol_haritasi_metni())
