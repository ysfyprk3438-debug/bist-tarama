"""
═══════════════════════════════════════════════════════════════
║                                                               ║
║   📍 APEX — DURUM PANOSU                                       ║
║   BURADAYIZ. Yeni oturumda ÖNCE BUNU OKU, sonra yol_haritasi. ║
║                                                               ║
═══════════════════════════════════════════════════════════════

Bu dosya projenin KONTROL NOKTASIDIR.
Her geliştirme oturumunun SONUNDA güncellenir.
Yeni sohbete başlarken Claude önce bunu okur → bağlamı alır.

Repo: ysfyprk3438-debug/bist-tarama  (branch: main)
Canlı kod: TEK DOSYA app.py  (Streamlit Cloud)
"""

# ══════════════════════════════════════════════════════════════
# ŞU AN NEREDEYİZ
# ══════════════════════════════════════════════════════════════
SURUM = "app.py v2.5"
SON_GUNCELLEME = "Tek dosya kurumsal 'ölçüm aleti' arayüzü — Monte Carlo (#15) kapandı"

SU_AN = {
    "asama": "Canlı ve çalışıyor. app.py tek dosya, kendi HTML'ini taşıyor "
             "(artık apex_omurga_v1.html şablonuna bağımlı DEĞİL).",
    "siradaki_adim": "Risk Parity (#12) — bir sonraki yeşil aday.",
    "bekleyen_karar": "Yok.",
    "durustluk_cizgisi": "KORUNDU. Getiri tahmini ~yazı-tura, kanıtlanmış edge YOK. "
                         "Canlı veri yoksa fiyat UYDURULMAZ. Yön tahmini reddedildi "
                         "('akıllı para → seviye kırar' tipi drift KABUL EDİLMEDİ).",
}

# ══════════════════════════════════════════════════════════════
# CANLI ARAYÜZ (app.py v2.5 — ne var)
# ══════════════════════════════════════════════════════════════
ARAYUZ = [
    "Güven Kerterizi kadranı — başlık metriği 'sisteme ne kadar güvenmeli', sahte güven skoru değil.",
    "Havuz tablosu — taranan hisseler.",
    "Hisse Detay — üç sekme: Teknik / Bağlam / Sicil.",
    "Kesişim: MA50/MA200 altın/ölüm grafikte işaretli + 'N gün önce' + dürüst post-kesişim medyanı.",
    "  → Veri 2 yıl çekiliyor, grafik son 1 yılı gösteriyor.",
    "Karar Çerçevesi: seçim KULLANICIDA. Sistem verir: poz büyüklüğü + ATR stop + "
    "riskteki para + R/Ödül + senaryo. Cevap 'ne kadar / nereye kadar', 'AL' DEĞİL.",
    "Monte Carlo: yönsüz (drift=0) belirsizlik konisi + stop'a değme olasılığı. "
    "Kehanet değil — belirsizliğin genişliği.",
]

# ══════════════════════════════════════════════════════════════
# SON OTURUMDA NE YAPTIK (en yeni üstte)
# ══════════════════════════════════════════════════════════════
GECMIS_OTURUMLAR = [
    "#15 Monte Carlo kapandı: yönsüz belirsizlik konisi + stop'a değme olasılığı.",
    "#10 kapandı: delisted temizliği + projektör koruma kabuğu.",
    "app.py v1.9 → v2.5: tek dosyaya taşındı, kendi HTML'ini içinde taşıyor.",
    "Kurumsal 'ölçüm aleti' arayüzü: Güven Kerterizi + Havuz + Detay(Teknik/Bağlam/Sicil).",
    "Kesişim grafiği: altın/ölüm işareti + 'N gün önce' + post-kesişim medyanı; veri 2 yıl, grafik 1 yıl.",
    "Karar Çerçevesi: poz/stop/riskteki para/R-Ödül/senaryo — 'AL' demeyen yapı.",
    # --- daha eski (önceki mimari, arşiv) ---
    "Doğrulanmış varlık: pozisyon vol-target — gerçek BIST'te MaxDD bütçe altında kaldı.",
    "Honest core: hiçbir strateji OOS'ta mevduatı geçemedi; makro rejim placebo'da çöktü (beta).",
]

# ══════════════════════════════════════════════════════════════
# İŞ KUYRUĞU (numaralı)
# ══════════════════════════════════════════════════════════════
IS_KUYRUGU = [
    "#10  Delisted temizliği + projektör koruma kabuğu          → KAPANDI ✓",
    "#15  Monte Carlo (yönsüz belirsizlik konisi)               → KAPANDI ✓",
    "#12  Risk Parity                                           → SIRADAKİ yeşil aday",
    "ForInvest AKD/takas manuel görsel arşivi                   → bekliyor",
    "İleri-test (paper) birikimi — tek dürüst OOS               → sürüyor",
]

# ══════════════════════════════════════════════════════════════
# DEPLOY (değişmeyen kural)
# ══════════════════════════════════════════════════════════════
DEPLOY = [
    "Tek kaynak: GitHub repo ysfyprk3438-debug/bist-tarama, main. Gevşek dosya yükleme YOK.",
    "Canlı kod tek dosya: app.py. GitHub web editör → app.py → Edit → Ctrl+A → sil → yapıştır → Commit.",
    "Streamlit Cloud otomatik redeploy eder.",
    ".github/workflows/ altına token YAZAMAZ → workflow dosyalarını Yusuf web UI'dan elle açar.",
]

# ══════════════════════════════════════════════════════════════
# DEĞİŞMEZ İLKELER (dürüstlük çizgisi)
# ══════════════════════════════════════════════════════════════
ILKELER = [
    "Başlık metriği = 'ne kadar güvenmeli', sahte güven değil.",
    "Getiri tahmini ~yazı-tura; kanıtlanmış edge yok. Risk yönetimi çözülebilir problem.",
    "Canlı veri yoksa fiyat uydurulmaz.",
    "Yön tahmini (drift) reddedildi — Monte Carlo yönsüz.",
    "Dürüst ≠ seyrek: gerçek tarihsel veri hem dürüst hem zengindir.",
]


def durum_metni():
    s = ["📍 APEX — DURUM", "=" * 45]
    s.append(f"\nSÜRÜM: {SURUM} — {SON_GUNCELLEME}")
    s.append(f"\nŞU AN: {SU_AN['asama']}")
    s.append(f"SIRADAKİ: {SU_AN['siradaki_adim']}")
    s.append(f"\nDÜRÜSTLÜK ÇİZGİSİ:\n  {SU_AN['durustluk_cizgisi']}")
    s.append("\nİŞ KUYRUĞU:")
    for a in IS_KUYRUGU:
        s.append(f"  {a}")
    return "\n".join(s)


if __name__ == "__main__":
    print(durum_metni())
