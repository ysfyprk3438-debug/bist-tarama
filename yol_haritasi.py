"""
═══════════════════════════════════════════════════════════════
YOL HARİTASI — APEX
═══════════════════════════════════════════════════════════════
Bu dosya projenin HAFIZASIDIR. Vizyon ve "sonra" denenler burada yaşar.
Yeni oturumda nereye gittiğimizi unutursak buraya bakarız. (Önce durum.py.)

⚠️ ESKİ FELSEFE GÖMÜLDÜ (28 Haz 2026):
  Eski yol haritası "piyasa uyarlanır, bir edge bul ve kayan zirveyi kovala,
  kendini yeniden icat eden bir getiri-organizması kur" diyordu. Bu anlatı
  baştan çıkarıcıdır ve bizi tam da overfitting'e çeker. RİGORLU TEST ETTİK:
  15dk gecikmeli perakende BIST verisiyle kovalanacak bir getiri-zirvesi YOK.
  6 strateji ailesi + plasebo testi bunu kapattı (bkz. durum.py TEMEL_BULGU).

DÜRÜST FELSEFE (yenisi):
  Getiri kehaneti ulaşılamaz; RİSK YÖNETİMİ ulaşılabilir. Perakendenin asıl
  para kaybettiği yer kötü risk/pozisyon kararlarıdır — çözülebilir, dürüst
  problem. APEX bir getiri-oracle'ı değil, REJİM-FARKINDA RİSK PUSULASI'dır.
  Uzun vadeli hedef (regüle fon) hâlâ geçerli — ama temeli risk disiplini ve
  mevduatı RİSK-AYARLI mütevazı geçmek, bir kâhin değil.

Durum kodları: ✅ yapıldı · 🎯 sıradaki · 🔭 ufuk (şartlı) · ⚰️ gömüldü (test edip elendi)
"""

# ══════════════════════════════════════════════════════════════
# TAMAMLANAN — CANLI DÜRÜST ÇEKİRDEK (v5.0, 28 Haz 2026)
# ══════════════════════════════════════════════════════════════
TAMAMLANAN = [
    ("İleri kağıt-test günlüğü — her iş günü otonom (cron), gerçek OOS biriktirir", "✅"),
    ("Reel-faiz rejim pusulası — politika−enflasyon, duruş (mevduat/hisse lehine)", "✅"),
    ("Vol-hedefli risk-ölçekleme — DD bütçesi→hisse ağırlığı; gerçek BIST'te DOĞRULANDI", "✅"),
    ("Makro oto-besleme — OECD enflasyon+faiz, statiğe fallback, statik öncelikli", "✅"),
    ("4-çizgi karne — risk-ölçekli/duruş/endeks/mevduat, sadece kayıtlı kararlardan", "✅"),
    ("Telegram bildirimi — günlük duruş+pozisyon telefona (yeni kayıtta)", "✅"),
    ("Dürüstlük katmanı — her ekran kendi sınırını söyler ('kâhin değil')", "✅"),
    ("Dayanıklılık — veri tarihi geri gitse/mükerrer gelse dedupe+sıralama düzeltir", "✅"),
]

# ══════════════════════════════════════════════════════════════
# TEST EDİLİP ELENEN (bir daha açma — kanıt burada)
# ══════════════════════════════════════════════════════════════
ELENEN = [
    "Çok-vade teknik sinyal — gün içi/günlük/haftalık; mevduatı+endeksi geçemedi",
    "Kesitsel seçim (hibrit skor) — full-cycle kazanır ama OOS yüksek-faiz yarısında kaybetti",
    "Momentum seçimi — parametre-sağlam AMA OOS-kırılgan, boom-bağımlı, MaxDD -%50",
    "MA200 rejim zamanlaması — 59 whipsaw, en kötüsü; zamanlama kaybettirir",
    "Temel-analiz seçimi (ROE+büyüme, point-in-time) — OOS en kötü, rejim-bağımlı",
    "Makro reel-faiz zamanlaması — eşik+gecikmeye dayandı AMA plasebo B'de çöktü "
    "(%55.7=medyan); mevduatı geçen şey beta, alfa değil",
]

# ══════════════════════════════════════════════════════════════
# GERÇEKÇİ YOL — buradan sonrası (hepsi dürüst kalmak şartıyla)
# ══════════════════════════════════════════════════════════════
GERCEKCI_YOL = [
    {
        "no": 0, "ad": "İleri Test Birikimi", "durum": "🎯",
        "ozet": "Sistem canlı, her iş günü gerçek karar kaydediyor. Tek gerçek "
                "doğrulama bu — geçmişe uydurulamaz. Asıl iş kod değil, SABIR.",
        "nasil": "Haftalarca/aylarca biriksin. 4-çizgi karnenin ayrışmasını izle. "
                 "Beklenti: pozitif reel-faiz rejiminde risk-ölçekli≈mevduat, düşük DD.",
        "onkosul": "Yok — çalışıyor. Sadece zaman.",
    },
    {
        "no": 1, "ad": "Risk Aracını Olgunlaştır", "durum": "🔭",
        "ozet": "Doğrulanmış tek değer ekseni risk kontrolü. Onu keskinleştir.",
        "nasil": "DD bütçesini ayarlanabilir yap; k=2.5'i ileri-veriyle kalibre et; "
                 "makro_oto faiz vekilini (IR3TIB) politika faizine yaklaştır.",
        "onkosul": "Biraz ileri-veri.",
    },
    {
        "no": 2, "ad": "Rejim Pusulasının Değerini ÖLÇ", "durum": "🔭",
        "ozet": "Rejim duruşu ileri-testte risk-ayarlı fayda katıyor mu? Karne yeterince "
                "dolunca DÜRÜSTÇE ölç — katmıyorsa pusulayı sade tut, zorlama.",
        "nasil": "Risk-ölçekli stratejinin gerçek ileri-Sharpe'ını mevduata karşı ölç. "
                 "Plasebo dersini unutma: beta'yı alfa sanma.",
        "onkosul": "Aylarca ileri-veri.",
    },
    {
        "no": 3, "ad": "Regüle Fon (uzun vade)", "durum": "🔭",
        "ozet": "Asıl hedef duruyor. Ama temeli RİSK DİSİPLİNİ + mevduatı risk-ayarlı "
                "mütevazı geçmek — bir getiri-oracle değil. Kanıt = uzun ileri-test günlüğü.",
        "nasil": "Yıllara yayılan dürüst karne + tutarlı risk kontrolü = anlatılabilir "
                 "track record. Önce o, sonra yapısal adımlar.",
        "onkosul": "Uzun, kesintisiz ileri-test geçmişi.",
    },
]

# ══════════════════════════════════════════════════════════════
# GÖMÜLEN KATMANLAR (eski vizyon — neden öldüğü açık olsun)
# ══════════════════════════════════════════════════════════════
GOMULEN = [
    ("K1 Kendini kalibre eden getiri-sistemi", "⚰️",
     "Önkoşulu 'çürüyen edge'i tespit edip ağırlık ayarla' idi. Ama ortada kalibre "
     "edilecek bir edge yok (TEMEL_BULGU). Kalibrasyon overfitting'i hızlandırır."),
    ("K4 Strateji ekosistemi (rakip beyinler)", "⚰️",
     "Birden çok getiri-stratejisini yarıştırmak — her biri tek tek elendi. "
     "Eleneni çoğaltmak edge yaratmaz, sadece overfitting yüzeyini büyütür."),
    ("K3/K5 Mikroyapı + kalabalık psikolojisi", "⚰️",
     "AKD/emir-defteri verisi + davranış modelleme. 15dk gecikmeli perakende "
     "erişimle yapısal olarak ulaşılamaz; pro araçları gerektirir (Tera örneği)."),
    ("Av skoru / robot / niyet okuyucu", "⚰️",
     "Eski karar.py av_skoru ve teknik sinyal yığını — rigorlu testte mevduata yenildi."),
]


def yol_haritasi_metni():
    s = ["APEX — YOL HARİTASI (dürüst sürüm)\n" + "=" * 50]
    s.append(f"\nCANLI ÇEKİRDEK ({len(TAMAMLANAN)}):")
    for ad, d in TAMAMLANAN:
        s.append(f"  {d} {ad}")
    s.append(f"\nTEST EDİLİP ELENEN ({len(ELENEN)}) — bir daha açma:")
    for e in ELENEN:
        s.append(f"  ⚰️ {e}")
    s.append("\nGERÇEKÇİ YOL:")
    for k in GERCEKCI_YOL:
        s.append(f"  {k['durum']} {k['no']}: {k['ad']} — {k['ozet']}")
    s.append("\nGÖMÜLEN ESKİ KATMANLAR:")
    for ad, d, neden in GOMULEN:
        s.append(f"  {d} {ad}")
    return "\n".join(s)


if __name__ == "__main__":
    print(yol_haritasi_metni())
