"""
═══════════════════════════════════════════════════════════════
║                                                               ║
║   📍 APEX — DURUM PANOSU                                       ║
║   BURADAYIZ. Yeni oturumda ÖNCE BUNU OKU.                     ║
║                                                               ║
═══════════════════════════════════════════════════════════════

Bu dosya projenin KONTROL NOKTASIDIR.
Yeni bir sohbete başlarken önce bunu oku → tüm bağlamı al.

⚠️ GELECEK OTURUM İÇİN EN ÖNEMLİ UYARI:
Bu projede getiri-tahmin edge'i AVI RİGORLU OLARAK YAPILDI VE KAPANDI.
"Hadi bir strateji daha deneyelim" tuzağına DÜŞME. Aşağıdaki TEMEL_BULGU'ya bak.
Yeni backtest = daha fazla overfitting. Asıl iş artık kod değil, SABIR (ileri test).
"""

SURUM = "v5.0 — APEX Dürüst Çekirdek"
SON_GUNCELLEME = "28 Haz 2026: edge avı dürüstçe kapandı; risk + ileri-test ürünü canlıya alındı"

# ══════════════════════════════════════════════════════════════
# TEMEL BULGU (bu gecenin özü — her şeyin dayandığı gerçek)
# ══════════════════════════════════════════════════════════════
TEMEL_BULGU = {
    "soru": "15dk gecikmeli perakende BIST verisiyle mevduatı yenecek kanıtlanmış getiri-edge'i var mı?",
    "cevap": "HAYIR. 6 strateji ailesi (çok-vade, kesitsel seçim, momentum, MA200 rejim, "
             "temel-analiz, makro reel-faiz zamanlaması) sert testlerden geçirildi; hepsi düştü.",
    "en_sert_test": "Makro reel-faiz rejimi eşik+gecikme testlerine dayandı AMA plasebo B'de çöktü "
                    "(gerçek %55.7 yüzdelik = medyan). Mevduatı geçen şey zamanlama becerisi değil, "
                    "yükselen 8 yılda uzun hisse maruziyeti (beta, alfa kılığında).",
    "ayakta_kalan": "RİSK KONTROLÜ. Vol-hedefleme gerçek BIST'te doğrulandı: gerçekleşen MaxDD her "
                    "bütçenin altında (1.5→0.3, 5→2.1, 10→5.1, 20→11.4), all-in'in -%31.8'ini tek haneye kırptı.",
    "ders": "Getiri kehaneti ulaşılamaz; risk yönetimi ulaşılabilir. APEX'in değer ekseni budur.",
}

# ══════════════════════════════════════════════════════════════
# ŞU AN NEREDEYİZ
# ══════════════════════════════════════════════════════════════
SU_AN = {
    "asama": "CANLI — sistem her iş günü kendi kendine çalışıyor, gerçek ileri-test biriktiriyor",
    "siradaki_adim": "KOD DEĞİL, SABIR. Karne haftalarca dolsun. Tek gerçek doğrulama ileri test.",
    "bekleyen_karar": "Yok. Sistem tam ve çalışıyor.",
    "onemli_not": "Bu çekirdek dürüsttür — her ekranda kendi sınırını söyler ('kâhin değil, risk-farkında temkin').",
}

# ══════════════════════════════════════════════════════════════
# CANLI ÇEKİRDEK (şu an çalışan sistem — bunlara dokunurken dikkat)
# ══════════════════════════════════════════════════════════════
CANLI_DOSYALAR = [
    "backtest_runner.py — CANLI LOGGER (ileri_gunluk.py içeriği). Workflow bunu çalıştırır.",
    "ileri_gunluk.py    — logger kaynağı: rejim+pozisyon hesaplar, karne kurar, Telegram atar",
    "makro_veri.py      — statik çeyreklik faiz+enflasyon tablosu (TEMEL, elle güncellenir)",
    "makro_oto.py       — OECD'den enflasyon+faiz oto-besleme; statiğe fallback; statik öncelikli",
    "pozisyon.py        — vol-hedefli risk-ölçekleme (DD bütçesi→hisse ağırlığı, k=2.5)",
    "bildirim.py        — Telegram göndericisi (secrets: TELEGRAM_TOKEN + TELEGRAM_CHAT_ID)",
    "veri.py            — XU100 veri çekme (Yahoo→İş Yatırım fallback) [eski projeden, hâlâ kullanılır]",
    "ILERI_DURUM.md     — ÇIKTI: günlük duruş + risk pozisyonu + 4-çizgi karne (oku-panosu)",
    "ileri_gunluk.csv   — ÇIKTI: ham günlük kayıt (tarih,xu100,reel,durus,agirlik) — ileri-test verisi",
    ".github/workflows/backtest.yml — cron (her iş günü 07:00 UTC) + git add -A + Telegram env",
]

# ══════════════════════════════════════════════════════════════
# ESKİ / TERK EDİLMİŞ (edge-avı dönemi — artık aktif DEĞİL, silinebilir)
# ══════════════════════════════════════════════════════════════
ESKI_DOSYALAR = (
    "robot.py, karar.py, niyet.py, gecmis.py, piyasa.py, ruzgar.py, performans.py, grafik.py, "
    "alarm.py, volatilite.py, karakter.py, hacim.py, zaman.py, izleme.py, strateji.py, radar.py, "
    "genislik.py, psikoloji.py, seffaflik.py, kalibrasyon.py, ai_model.py, fibonacci.py, analiz.py, "
    "tarama_core.py, app.py, arayuz.py, cuzdan.py, backtest.py — eski Streamlit/robot mimarisi. "
    "Bunların ürettiği teknik/momentum/temel sinyaller rigorlu testte mevduata yenildi. "
    "Referans için durabilir ama CANLI yola bağlı değiller."
)

# ══════════════════════════════════════════════════════════════
# BAKIM (yavaş, küçük işler)
# ══════════════════════════════════════════════════════════════
BAKIM = [
    "makro_veri.py: yeni PPK faiz kararı / TÜİK enflasyonu çıkınca MAKRO tablosuna bir çeyrek ekle. "
    "Eklemezsen OECD birkaç ay gecikmeyle devralır; sistem durmaz.",
    "Karne: birkaç hafta sonra 4 çizginin (risk-ölçekli/duruş/endeks/mevduat) ayrışmasına bak.",
    "Cron: günlük commit repo'yu aktif tutar → GitHub 60-gün durdurma kuralı tetiklenmez.",
    "Güvenlik: BotFather token'ı sohbette geçti — ciddi kullanımda /revoke ile yenile.",
    "Temizlik: telegram_test.py ölü (silinebilir). .gitignore __pycache__'i durdurur.",
]

# ══════════════════════════════════════════════════════════════
# SONRAKİ (eğer gerçekten bir şey eklenecekse — sırayla, yorgunken DEĞİL)
# ══════════════════════════════════════════════════════════════
SONRAKI_HEDEF = (
    "Önce ileri test birikecek (takvim işi). Sonra OPSİYONEL, hepsi dürüst kalmak şartıyla: "
    "(1) DD bütçesini ayarlanabilir yap. (2) Karne yeterince dolunca risk-ölçekli stratejinin "
    "gerçek ileri-Sharpe'ını ölç. (3) makro_oto faiz vekilini (IR3TIB) politika faizine kalibre et. "
    "ASLA: yeni getiri-stratejisi backtest'i — o soru kapandı, cevabı TEMEL_BULGU'da."
)


def durum_metni():
    s = ["📍 APEX — DURUM", "=" * 50]
    s.append(f"\nSÜRÜM: {SURUM}\n{SON_GUNCELLEME}")
    s.append(f"\n── TEMEL BULGU ──\n{TEMEL_BULGU['soru']}\n→ {TEMEL_BULGU['cevap']}\n"
             f"Ayakta kalan: {TEMEL_BULGU['ayakta_kalan']}\nDers: {TEMEL_BULGU['ders']}")
    s.append(f"\nŞU AN: {SU_AN['asama']}\nSIRADAKİ: {SU_AN['siradaki_adim']}")
    s.append("\n── CANLI ÇEKİRDEK ──")
    for d in CANLI_DOSYALAR:
        s.append(f"  {d}")
    s.append(f"\n── BAKIM ──")
    for b in BAKIM:
        s.append(f"  • {b}")
    s.append(f"\nSONRAKİ:\n  {SONRAKI_HEDEF}")
    return "\n".join(s)


if __name__ == "__main__":
    print(durum_metni())
