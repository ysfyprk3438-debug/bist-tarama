"""
═══════════════════════════════════════════════════════════════
║                                                               ║
║   APEX — DURUM PANOSU                                          ║
║   BURADAYIZ. Yeni oturumda ÖNCE BUNU OKU.                     ║
║                                                               ║
═══════════════════════════════════════════════════════════════

APEX bir BIST risk & analiz terminalidir — TAHMİN MOTORU DEĞİL.
15 dk gecikmeli perakende veriyle kanıtlanmış bir yön (getiri) edge'i YOK.
Doğrulanmış tek eksen: RİSK DİSİPLİNİ.
  - volatilite-hedefli pozisyon boyutu
  - ATR(14)×2 stop
  - her okumanın kendi dürüst sicili (kaç kez oldu, sonraki ~10 gün ne yaptı)

Her okuma YÖN VERMEZ; "piyasa bunu nasıl okur / neye vurgu yapar" der.
İsabet %40–60 ise → gri "≈ yazı-tura". Yıldız veri, tahmin değil.

Bu dosya projenin KONTROL NOKTASIDIR. Her oturum SONUNDA güncellenir.
Yeni sohbette Claude önce bunu + yol_haritasi.py'yi okur.
"""

# ══════════════════════════════════════════════════════════════
# ŞU AN NEREDEYİZ
# ══════════════════════════════════════════════════════════════
SURUM = "v17"
AKTIF_DOSYA = "akd_sicil.py + akd_manuel_arsiv.csv (AKD Sicil) · app.py Sanal Borsa canlı"
REPO = "ysfyprk3438-debug/bist-tarama (main)"
# KİMLİK (değişmez): APEX tahmin motoru DEĞİLDİR; doğrulanmış eksen RİSK DİSİPLİNİdir
# (volatilite-hedefli pozisyon boyutlama, ATR(14)×2 stop, dürüst sicil takibi).
# Eski av/skor/al-sat/yön-tahmini dili kalıcı olarak çıkarıldı.
KIMLIK = ("APEX tahmin motoru değildir; doğrulanmış eksen risk disiplinidir "
          "(volatilite-hedefli pozisyon boyutlama, ATR(14)×2 stop, dürüst sicil takibi).")
SON_GUNCELLEME = "Mühürleme: tarama_core.py arsiv'e taşındı (ölü çekirdek); durum/yol_haritası dürüst risk-yönetimi kimliğiyle yeniden mühürlendi. AKD Sicil + Bekçi AKD alarmı + görsel/toplu besleme + FIZIBILITE_AKD canlı."

SU_AN = {
    "asama": "Katman 3 (Niyetin İzi — AKD/takas): AKD SİCİL hattı CANLI; "
             "manuel/görsel besleme + fizibilite kararı bekliyor",
    "son_is": (
        "AKD Sicil canlı: akd_manuel_arsiv.csv (AKFGY 6 aylık ilk5 net) + akd_sicil.py "
        "(3 desen, çapa=dönem bitişi, sonraki 10 işlem günü getirisi, mühürleme tutarlı; "
        "%40–60 → «≈ yazı-tura», n<5 → yetersiz örneklem). Bugün: n=1 tek olgun instance "
        "(Mar−→Nis+, gerçek +%2,8) — dürüstçe 'yetersiz örneklem' damgalı. Bekçi'ye AKD "
        "tazelik alarmı eklendi (arşiv 35+ gün bayatsa SARI). Yarı-otomatik görsel besleme "
        "protokolü CLAUDE.md §11'de + [AKD] issue şablonu. Tam otomatik için FIZIBILITE_AKD.md "
        "hazır (karar bekliyor)."
    ),
    "cikan_sonuc": (
        "AKFGY: Üst-5'te net alım (~+30,9M lot ≈ serbest dolaşımın %1,8'i) ve yabancı "
        "(BofA custodian) alıcı VAR; fiyat aylık YATAY. Alfa değil, renk. YÖN ÇIKMIYOR — "
        "tez doğrulandı. Sicil MAKİNESİ artık çalışıyor ama örneklem 1 = anlamsız; "
        "arşiv büyümeden sicil konuşmaz (dürüst duruş)."
    ),
    "siradaki_adim": (
        "(1) MAVI 6 aylık AKD görselleriyle arşivi büyüt — ilk [AKD] issue testi "
        "(@claude görselden okur → PR → insan doğrular). "
        "(2) Fizibilite kararı (FIZIBILITE_AKD.md: görsel hat / Matriks API / scraping-hayır). "
        "(3) AKD sicilinin Sanal Borsa hisse görünümüne entegrasyonu."
    ),
    "bekleyen_karar": "Fizibilite: AKD beslemesi manuel-görsel mi kalsın, ücretli API'ye mi geçilsin (FIZIBILITE_AKD.md).",
}

# ══════════════════════════════════════════════════════════════
# NE KANITLANDI / NE KANITLANMADI (çekirdek hafıza)
# ══════════════════════════════════════════════════════════════
KANITLANAN = [
    "RİSK KONTROLÜ çalışıyor: pozisyon.py vol-hedefte gerçekleşen MaxDD bütçe altında "
    "kaldı (örn. bütçe %1,5 → fiili %0,3). ATR(14)×2 stop, 60-gün-dip sezgisini yener.",
    "Look-ahead bias YOK (veri-kesme testi). Para muhasebesi temiz (yaratma/yok etme yok).",
    "Placebo baseline zorunlu: bir edge, rastgele tabanı geçmiyorsa beta'dır, alfa değil.",
]
KANITLANMAYAN_EDGE = [
    "Çok-vadeli teknik, momentum, MA200 rejimi, temel, makro reel-faiz zamanlaması — "
    "hepsi OOS + placebo'da düştü. Makro reel-faiz rejimi placebo B'de %55,7 (medyan) "
    "= performans beta'ydı, zamanlama becerisi değil.",
    "AKD/takas 'yabancı alıyor → al' okuması: manuel doğrulamada da yön vermedi. "
    "Akış saklamacı-ağırlıklı; niyet okunamıyor.",
]

# ══════════════════════════════════════════════════════════════
# DEPLOY (değişmez workflow)
# ══════════════════════════════════════════════════════════════
DEPLOY_ADIMLARI = [
    "1. GitHub web editor → dosyayı aç → Ctrl+A → Delete → yapıştır → Commit",
    "2. share.streamlit.io → Reboot",
    "3. SURUM sabitini artır → app reboot'suz cache tazelenir",
    "NOT: ui_app.py'ye DOKUNMA (ölü paralel modül).",
    "NOT: .github/workflows/*.yml GitHub App token'ıyla yazılamaz — Yusuf web UI'dan elle.",
    "NOT: laptop'tan gh (workflow scope) ile workflow push edilebiliyor — bekci.yml böyle eklendi.",
]

# ══════════════════════════════════════════════════════════════
# AÇIK KALEMLER
# ══════════════════════════════════════════════════════════════
ACIK_KALEMLER = [
    "AKD arşivini büyüt — MAVI 6 aylık AKD görselleriyle ilk [AKD] issue testi (görsel→PR→insan)",
    "Fizibilite kararı — AKD beslemesi: manuel-görsel mi, ücretli API mi (FIZIBILITE_AKD.md)",
    "AKD sicilini Sanal Borsa hisse görünümüne entegre et (sonraki UI adımı)",
    "Bekçi CANLI (bekci.py + bekci.yml, hafta içi 18:45 TR) — ilk gerçek gece turunu izle",
    "AKD Sicil CANLI (akd_sicil.py + akd_manuel_arsiv.csv) — arşiv büyüdükçe anlam kazanır",
    "İleri-test log birikimi: ileri_gunluk.csv (gunluk.yml, hafta içi 15:30 UTC) — tek gerçek OOS",
    "Makro: makro_guncel.json yarı-manuel (çeyreklik 2 sayı)",
    "Kozmetik: ileri-test grafiği Endeks/Mevduat renkleri ayırt edilemiyor",
]


def durum_metni():
    s = ["APEX — DURUM", "=" * 45]
    s.append(f"\nKİMLİK: {KIMLIK}")
    s.append(f"\nSÜRÜM: {SURUM}  ·  {AKTIF_DOSYA}")
    s.append(f"REPO: {REPO}")
    s.append(f"SON: {SON_GUNCELLEME}")
    s.append(f"\nŞU AN: {SU_AN['asama']}")
    s.append(f"ÇIKAN SONUÇ: {SU_AN['cikan_sonuc']}")
    s.append(f"SIRADAKİ: {SU_AN['siradaki_adim']}")
    s.append("\nKANITLANAN:")
    for k in KANITLANAN:
        s.append(f"  ✓ {k}")
    s.append("\nEDGE ÇIKMAYAN:")
    for k in KANITLANMAYAN_EDGE:
        s.append(f"  ✗ {k}")
    return "\n".join(s)


if __name__ == "__main__":
    print(durum_metni())
