"""
═══════════════════════════════════════════════════════════════
║                                                               ║
║   📍 APEX — DURUM PANOSU                                       ║
║   BURADAYIZ. Yeni oturumda ÖNCE BUNU OKU (sonra yol_haritasi).║
║                                                               ║
═══════════════════════════════════════════════════════════════

Bu dosya projenin KONTROL NOKTASIDIR.
Her geliştirme oturumunun SONUNDA güncellenir.
Yeni bir sohbete başlarken Claude önce bunu okur → tüm bağlamı alır.
"""

# ══════════════════════════════════════════════════════════════
# ŞU AN NEREDEYİZ
# ══════════════════════════════════════════════════════════════
SURUM = "v4.4"
SON_GUNCELLEME = "Cihazdan bağımsız bulut kalıcılık (Google Sheets) canlı"

SU_AN = {
    "asama": "Canlı. APEX 5 modlu arayüz + Sanal Borsa sayfası gerçek BIST verisiyle çalışıyor.",
    "siradaki_adim": "apex_kare_prototip.html tasarımını gorsel_panel.py'ye portla "
                     "(kare tile grid + tek ekran detay, APEX okuma dili: yönsüz betim + 1 yıllık sicil).",
    "bekleyen_karar": "Yok.",
    "onemli_not": "Sanal cüzdan VE karar defteri artık Google Sheets'te (APEX HAFIZA). "
                  "Telefon = laptop, aynı hafıza. Manuel sıfırlanana kadar kalıcı.",
}

# ══════════════════════════════════════════════════════════════
# FELSEFE (değişmez çekirdek)
# ══════════════════════════════════════════════════════════════
FELSEFE = (
    "Getiri tahmini REDDEDİLDİ — 15 dk gecikmeli perakende veriyle kanıtlanmış bir kenar yok. "
    "Dürüst ve doğrulanmış eksen: RİSK YÖNETİMİ ve POZİSYON BÜYÜKLÜĞÜ. "
    "Sistem bir 'risk pusulası' / karar-destek aracıdır, getiri kâhini değil. "
    "Vol-hedefli pozisyon büyüklüğü (pozisyon.py) gerçek BIST verisinde doğrulandı: "
    "gerçekleşen düşüşü bütçe içinde tuttu. Geri kalan her şey (teknik/momentum/temel seçim, "
    "makro zamanlama) OOS ve plasebo testlerinde çöktü. "
    "Dil kuralı: hiçbir çıktıda al/sat/tahmin/hedef yok. Her sinyal kendi SİCİLİNİ taşır."
)

# ══════════════════════════════════════════════════════════════
# CANLI ALTYAPI (çalıştığı doğrulanmış)
# ══════════════════════════════════════════════════════════════
CANLI = [
    "app.py — ana APEX sayfası (Pusula/Havuz/Trade/Defter/Nabız), embedded HTML",
    "pages/01_Sanal_Borsa.py — sanal borsa, gerçek BIST verisi, native Streamlit",
    "kalici.py — Google Sheets bulut kalıcılık (yukle/kaydet/sil/tablo_yaz)",
    "  → Sheet: APEX HAFIZA · sayfalar: apex_durum + cuzdan_ozet",
    "  → Servis hesabı: apex-yazici@apex-501017.iam.gserviceaccount.com (Editor)",
    "pozisyon.py — vol-hedef sizing (k=2.5), DOĞRULANMIŞ değer ekseni",
    "gunluk_log.py + gunluk.yml — otonom günlük ileri-test logger (ileri_gunluk.csv)",
    "projektor.py + projektor.yml — Telegram boru hattı (64 hisse → Sonnet → Telegram)",
    "makro_guncel.json — yarı-otomatik makro (politika 37.0, enflasyon 32.61)",
    "temel_veri.json — 62 hisse temel veri",
    "karar_defteri — artık BULUTTA (eski CSV bir kez migrate edildi)",
]

# ══════════════════════════════════════════════════════════════
# BU OTURUMDA NE YAPTIK (en yeni üstte)
# ══════════════════════════════════════════════════════════════
GECMIS_OTURUMLAR = [
    "Bulut kalıcılık (kalici.py): Google Sheets'e cihazdan bağımsız kayıt. "
    "Sanal Borsa + karar defteri buluta taşındı. Telefon=laptop doğrulandı.",
    "Güvenlik: servis hesabı anahtarı rotasyonu (eski silindi, yeni aktif).",
    "Kullanılabilirlik: mobil navigasyon butonları, iOS ana ekran kısayolu "
    "'APEX Pusula', UptimeRobot keep-alive (Streamlit uyumuyor).",
    "— önceki oturumlar: ileri-test logger, projektör Telegram hattı, "
    "vol-hedef sizing doğrulaması, plasebo/OOS denetimleri —",
]

# ══════════════════════════════════════════════════════════════
# SIRADAKİ HEDEF
# ══════════════════════════════════════════════════════════════
SONRAKI_HEDEF = (
    "gorsel_panel.py: apex_kare_prototip.html portu. 2 sütun kare tile grid "
    "(sparkline arka plan) + slide-up tek ekran detay: tüm bilgi grafiğin üstünde "
    "etiketli (zirve/dip callout, son fiyat vs ortalama, 20G ortalama uçta, "
    "volatilite değişim işareti). Otomatik yapı tespiti (çift tepe/dip, "
    "konsolidasyon bandı, yükselen/düşen kanal) amber overlay + borsa terimi caption. "
    "KURAL: yalnız geometrik gözlem, yön/hedef YOK. Her okuma 1 yıllık sicilini taşır "
    "(kaç kez yaşandı, sonraki ~10 günde ▲kaç/▼kaç, isabet ~%). İsabet 40-60 ise nötr gri."
)


def durum_metni():
    s = ["📍 APEX — DURUM", "=" * 45]
    s.append(f"\nSÜRÜM: {SURUM} — {SON_GUNCELLEME}")
    s.append(f"\nŞU AN: {SU_AN['asama']}")
    s.append(f"SIRADAKİ: {SU_AN['siradaki_adim']}")
    s.append(f"\nCANLI ALTYAPI:")
    for c in CANLI:
        s.append(f"  {c}")
    s.append(f"\nSONRAKİ HEDEF:\n  {SONRAKI_HEDEF}")
    return "\n".join(s)


if __name__ == "__main__":
    print(durum_metni())
