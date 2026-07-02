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
SURUM = "v15"
AKTIF_DOSYA = "pages/01_Sanal_Borsa.py (Sanal Borsa v15)"
REPO = "ysfyprk3438-debug/bist-tarama (main)"
SON_GUNCELLEME = "Altyapı turu: BEKÇİ canlı + veri taze-kapanış yaması + @claude/CI akışı + repo temizliği (PR #14)"

SU_AN = {
    "asama": "Katman 3 (Niyetin İzi — AKD/takas) MANUEL köprü aşamasında; "
             "altyapı (Bekçi + @claude akışı) canlı",
    "son_is": (
        "Altyapı turu: veri.py taze-kapanış yaması canlıda; Sanal Borsa fiyatları "
        "2 ondalık Türk formatında; Claude Code + gh laptop'ta kurulu; @claude GitHub "
        "Actions aktif (issue/PR + otomatik PR incelemesi, CLAUDE_CODE_OAUTH_TOKEN); "
        "repo temizliği PR #14 merge (42 dosya arsiv/'e); BEKÇİ CANLI (bekci.py + "
        "bekci.yml, hafta içi 18:45 TR): yeşilse Telegram tek satır, bulguda BEKCI_PAT "
        "ile bekci etiketli issue açıp @claude'u görevlendirir — merge insanda."
    ),
    "cikan_sonuc": (
        "Üst-5'te net alım (~+30,9M lot ≈ serbest dolaşımın %1,8'i, ağırlığı Ocak'ta) "
        "ve belirgin yabancı (BofA custodian) alıcı VAR; fiyat aylık YATAY. "
        "Bu bir alfa değil, renk. Custodian akışı niyet değil; 'ucuz F/K' 2025-3 "
        "rayiç kazancına (%328 net marj) yaslı sahte. YÖN ÇIKMIYOR — tez doğrulandı."
    ),
    "siradaki_adim": (
        "(1) Bekçi'nin ilk gerçek gece turunu izle. "
        "(2) AKD desen→sicil etiketleyicisi (AKFGY manuel arşivi ilk kayıt): her manuel "
        "arşiv desenine ('yabancı 3 ay üst-5 net alıcı' gibi) 1-yıl sicili iliştir; "
        "%40–60 isabette gri yazı-tura."
    ),
    "bekleyen_karar": "Yok — sıralı ilerliyoruz.",
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
    "Bekçi CANLI (bekci.py + bekci.yml, hafta içi 18:45 TR) — ilk gerçek gece turunu izle",
    "AKD desen→sicil etiketleyici (sıradaki iş; AKFGY manuel arşivi ilk kayıt)",
    "AKD/takas manuel arşiv entegrasyonu (ForInvest, elle) — süregelen açık kalem",
    "İleri-test log birikimi: ileri_gunluk.csv (gunluk.yml, hafta içi 15:30 UTC) — tek gerçek OOS",
    "Makro: makro_guncel.json yarı-manuel (çeyreklik 2 sayı)",
    "Kozmetik: ileri-test grafiği Endeks/Mevduat renkleri ayırt edilemiyor",
]


def durum_metni():
    s = ["APEX — DURUM", "=" * 45]
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
