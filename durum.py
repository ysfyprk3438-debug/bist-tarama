"""
═══════════════════════════════════════════════════════════════
║                                                               ║
║   📍 BIST PARA AVCISI — DURUM PANOSU                          ║
║   BURADAYIZ. Yeni oturumda ÖNCE BUNU OKU.                     ║
║                                                               ║
═══════════════════════════════════════════════════════════════

Bu dosya projenin KONTROL NOKTASIDIR.
Her geliştirme oturumunun SONUNDA güncellenir.
Yeni bir sohbete başlarken Claude önce bunu okur → tüm bağlamı alır.
"""

# ══════════════════════════════════════════════════════════════
# ŞU AN NEREDEYİZ
# ══════════════════════════════════════════════════════════════
SURUM = "v4.1"
SON_GUNCELLEME = "İlk tam sürüm — 12 modül tamamlandı"

SU_AN = {
    "asama": "Canlıya çıkış öncesi — tüm kod hazır ve test edildi",
    "siradaki_adim": "GitHub'a 12 dosyayı yükle → Streamlit deploy → ilk taramayı gerçek veriyle izle",
    "bekleyen_karar": "Yok — deploy'a hazır",
    "onemli_not": "Robot karnesinin gün gün birikmesi için Supabase bağlanmalı (kalıcı saklama). Oturum içinde çalışır.",
}

# ══════════════════════════════════════════════════════════════
# DOSYA LİSTESİ (GitHub'a yüklenecekler)
# ══════════════════════════════════════════════════════════════
DOSYALAR = [
    "app.py            — ana uygulama, 8 sekme",
    "veri.py           — çift kaynaklı veri katmanı",
    "analiz.py         — vade bazlı analiz motoru",
    "cuzdan.py         — sanal cüzdan (paper trading)",
    "arayuz.py         — kart/HTML bileşenleri (render sorunu çözüldü)",
    "izleme.py         — watchlist + alarm + keşke analizi",
    "backtest.py       — backtest + sektör ısı haritası",
    "robot.py          — otomatik strateji robotu",
    "niyet.py          — niyet okuyucu + güven motoru",
    "gecmis.py         — öz-ölçüm, sinyal takibi",
    "piyasa.py         — piyasa dokusu (yığılma, rotasyon, korelasyon)",
    "ruzgar.py         — rüzgar yönü (trend uyumu, kuyruk/karşı rüzgar)",
    "performans.py     — robot karnesi (öz-puan, dönemsel getiri)",
    "grafik.py         — tıklanır grafik + teknik olay tespiti (altın kesişim vb)",
    "alarm.py          — yaklaşan olay alarmı + geri sayım (kart titreşir)",
    "karar.py          — baş analist: tüm sinyalleri tek karara sentezler",
    "volatilite.py     — volatilite rejimi (adaptif pozisyon/stop, strateji seçimi)",
    "karakter.py       — Hurst üssü + relatif güç + strateji uyumu (DNA, Katman 4 tohumu)",
    "hacim.py          — VWAP + hacim profili (POC, değer alanı, kurumsal seviyeler)",
    "zaman.py          — çoklu zaman dilimi onayı (üst trend teyidi, tuzak filtresi)",
    "yol_haritasi.py   — vizyon + katmanlar (projenin hafızası)",
    "durum.py          — BU DOSYA (kontrol noktası)",
    "requirements.txt  — streamlit, pandas, numpy, requests, matplotlib",
]

# ══════════════════════════════════════════════════════════════
# SON OTURUMDA NE YAPTIK (kronolojik — en yeni üstte)
# ══════════════════════════════════════════════════════════════
GECMIS_OTURUMLAR = [
    "Piyasa Rejimi Freni (piyasa.py + robot.py): borsa düşüşte/fırtınalı ise robot savunmaya geçer (alım eşiği yükselir, pozisyon/slot küçülür). Risk-off modu.",
    "Çoklu Zaman Dilimi Onayı (zaman.py): üst zaman dilimi (haftalık/aylık) sinyali teyit ediyor mu? Düşüşte sahte sıçrama tuzağını yakalar. Karara beslenir.",
    "Risk-Düzeltilmiş Kalite (performans.py): Sharpe, Sortino, Max Drawdown — robot 'şanslı mıydı yoksa iyi mi', mevduatı yeniyor mu",
    "Hacim Profili & VWAP (hacim.py): kurumsal seviyeler — POC (en güçlü destek), değer alanı (%70 hacim), VWAP konumu (alıcı/satıcı kontrolü). Güveni çarpmaz, yapısal bilgi.",
    "Karakter & Strateji Motoru (karakter.py): Hurst üssü (trend/salınım karakteri) + relatif güç (lider/takipçi) + STRATEJİ UYUMU (sinyal karaktere uyuyor mu? tuzak tespiti). Katman 4 tohumu.",
    "Volatilite Rejimi (volatilite.py): piyasa hava durumu (SAKİN/NORMAL/FIRTINA/SIKIŞMA), adaptif pozisyon+stop, strateji önerisi",
    "KOD DENETİMİ: backtest/robot için hızlı mod eklendi (gereksiz grafik/alarm hesabı atlanır), df_grafik güvenli erişim",
    "Karar Sentezleyici (karar.py): 5 sinyali tek AV SKORU + karara indirger (ŞİMDİ AL/İZLE/BEKLE/UZAK DUR) — emergent + sadeleştirici",
    "Alarm Motoru (alarm.py): yaklaşan kritik olay + GERİ SAYIM (altın kesişime ~2 gün), kart titreşir/renk değiştirir",
    "Tıklanır grafik (grafik.py): hisseye basınca grafik açılır, altın/ölüm kesişimi+destek/direnç işaretli, tek cümle yorum",
    "Robot Karnesi (performans.py): öz-puanlama (A-F notu), günlük/haftalık/aylık/yıllık getiri, değer grafiği",
    "Rüzgar Yönü (ruzgar.py): makro+sektör+hisse trend uyumu, kuyruk/karşı rüzgar, güvene etki",
    "Katman 2 (Piyasa Dokusu): yığılma uyarısı + sektör rotasyon oku + korelasyon analizi (piyasa.py)",
    "Yol haritası + durum panosu eklendi (proje kendi hafızasını taşıyor)",
    "Öz-ölçüm motoru (gecmis.py) — sinyal kaydı, otomatik sonuç takibi, başarı oranı",
    "Niyet Okuyucu + Güven Motoru — toplama/dağıtım/sürü/dip ayrımı, manipülasyon uyarısı",
    "Robot — disiplinli/basit mod, dinamik rotasyon, cooldown kuralı",
    "Sanal cüzdan, av panosu, izleme/alarm, backtest, ısı haritası",
    "Çekirdek yeniden yazım: tek dosyadan 13 modüle, render sorunu çözüldü",
]

# ══════════════════════════════════════════════════════════════
# DEPLOY ADIMLARI (eve gidince)
# ══════════════════════════════════════════════════════════════
DEPLOY_ADIMLARI = [
    "1. GitHub repo: ysfyprk3438-debug/bist-tarama (branch: main)",
    "2. requirements.txt'i güncelle (eski içeriği sil, yenisini yapıştır)",
    "3. app.py'yi güncelle (eski içeriği tamamen sil, yenisini yapıştır)",
    "4. 9 yeni .py dosyasını tek tek ekle (Create new file)",
    "5. Streamlit Cloud otomatik deploy etsin, bekle",
    "6. İlk taramayı yap — veri kaynağı çalışıyor mu kontrol et",
    "7. Tarama raporu sekmesinde 'veri gelmeyen hisseler' azsa → başarı",
    "8. Sorun çıkarsa veri.py'deki veri_al() ayarını birlikte düzeltiriz",
]

# ══════════════════════════════════════════════════════════════
# SIRADAKİ HEDEF (deploy sonrası)
# ══════════════════════════════════════════════════════════════
SONRAKI_HEDEF = (
    "Deploy başarılı olunca → Katman 1: Kendini Kalibre Eden Sistem. "
    "Sistem birkaç hafta gerçek sinyal biriktirsin, sonra öz-ölçüme göre "
    "kendi ağırlıklarını otomatik ayarlamaya başlasın. Detay: yol_haritasi.py"
)


def durum_metni():
    s = ["📍 BIST PARA AVCISI — DURUM", "=" * 45]
    s.append(f"\nSÜRÜM: {SURUM} — {SON_GUNCELLEME}")
    s.append(f"\nŞU AN: {SU_AN['asama']}")
    s.append(f"SIRADAKİ: {SU_AN['siradaki_adim']}")
    s.append(f"\nDEPLOY ADIMLARI:")
    for a in DEPLOY_ADIMLARI:
        s.append(f"  {a}")
    s.append(f"\nSONRAKİ HEDEF:\n  {SONRAKI_HEDEF}")
    return "\n".join(s)


if __name__ == "__main__":
    print(durum_metni())
