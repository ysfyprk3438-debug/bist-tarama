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
SURUM = "v19"
AKTIF_DOSYA = "akd_sicil.py + akd_manuel_arsiv.csv (AKD Sicil) · app.py Sanal Borsa canlı"
REPO = "ysfyprk3438-debug/bist-tarama (main)"
# KİMLİK (değişmez): APEX tahmin motoru DEĞİLDİR; doğrulanmış eksen RİSK DİSİPLİNİdir
# (volatilite-hedefli pozisyon boyutlama, ATR(14)×2 stop, dürüst sicil takibi).
# Eski av/skor/al-sat/yön-tahmini dili kalıcı olarak çıkarıldı.
KIMLIK = ("APEX tahmin motoru değildir; doğrulanmış eksen risk disiplinidir "
          "(volatilite-hedefli pozisyon boyutlama, ATR(14)×2 stop, dürüst sicil takibi).")
SON_GUNCELLEME = "İleri-test 3-çizgi SVG grafiği canlı (drawIleriChart, renk-körü dostu palet). AKD çekici doğrulandı — token ömrü ölçümü bekliyor."

# ══════════════════════════════════════════════════════════════
# GEÇMİŞ OTURUMLAR (en yeni üstte) — kısa, ne yapıldı
# ══════════════════════════════════════════════════════════════
GECMIS_OTURUMLAR = [
    "2026-07-02/03 · Kimlik temizliği: REHBER.md + DEPLOY.md canlı APEX mimarisine göre "
    "yeniden yazıldı; Para Avcısı/AV SKORU/Av Panosu/Avcı dili tamamen çıkarıldı (grep temiz), "
    "Güven Kerterizi/Pusula terimlerine hizalandı, yönsüz sicil dili korundu.",
    "2026-07-02 · OTURUM KAPANIŞI — tarama_core arsiv'e + dürüst kimlik mühürlemesi; "
    "KOD_SEKTOR bağımsız sektor_map.py'ye koparıldı; AKD çekici (akd_cekici.py) kuruldu ve "
    "canlı doğrulandı (GARAN 200/54 kurum); --tokentest token ölçüm günlüğü (token_gunluk.csv, "
    "gitignore'lu); ileri-test 3-çizgi SVG grafiği canlı. Hepsi main'de.",
    "2026-07-02 · İleri-test 3-çizgi SVG grafiği kuruldu (app.py drawIleriChart): Sistem "
    "(koyu mavi düz) / Endeks (amber kesikli) / Mevduat (gri-yeşil noktalı) + legend, "
    "renk-körü dostu. Sadece görselleştirme; ileri_seri() hesabı değişmedi.",
    "2026-07-02 · AKD çekici (akd_cekici.py) kuruldu: ForInvest web-cloud AKD hattı, "
    "token yalnız FOREKS_AUTH env, net_lot=na, --tokentest teşhis modu. Canlı doğrulandı "
    "(GARAN HTTP 200, 54 kurum, net_lot toplamı=0). Token ömrü ölçümü sıradaki.",
    "2026-07-02 · Mühürleme: tarama_core.py arsiv'e; KOD_SEKTOR → bağımsız sektor_map.py; "
    "dürüst risk-yönetimi kimliği yeniden mühürlendi (av/skor/al-sat dili yok).",
    "2026-07-02 · AKD Sicil canlı (akd_manuel_arsiv.csv + akd_sicil.py); Bekçi'ye AKD "
    "tazelik alarmı; yarı-otomatik + toplu görsel besleme protokolü; FIZIBILITE_AKD.md; "
    "Node20 workflow sürümleri güncellendi.",
]

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
    "AKD OTO custodian düzeltmesi (YARIN) — (1) akd_oto_topla.py _ad(it)=it.get('code') (c=fiyat, "
    "isim değil); lider_alici/satici KOD tutsun. (2) CUSTODIAN_KODLARI sözlüğü: ham item'da "
    "custodian/yabancı FLAG YOK → ancak KOD bazlı tanınır; gerçek kodları ForInvest AKD kod "
    "listesinden kullanıcıyla netleştir, UYDURMA. (3) akd_oto_arsiv.csv'deki hatalı 7 test satırını "
    "sil, temiz veriyle yeniden topla.",
    "AKD ham alan haritası (02.07, GARAN 54 kurum, KESİN): code=aracı kurum kodu (ZRY.B/TVM.B/…); "
    "c=fiyat; na=net adet; ta/tsa=alış/satış adet; tv/tsv/tbv=değer; bp/sp=alış/satış fiyat. "
    "custodian FLAG'i YOK.",
    "AKD arşivini büyüt — MAVI 6 aylık AKD görselleriyle ilk [AKD] issue testi (görsel→PR→insan)",
    "Fizibilite kararı — AKD beslemesi: manuel-görsel mi, ücretli API mi (FIZIBILITE_AKD.md)",
    "AKD sicilini Sanal Borsa hisse görünümüne entegre et (sonraki UI adımı)",
    "Bekçi CANLI (bekci.py + bekci.yml, hafta içi 18:45 TR) — ilk gerçek gece turunu izle",
    "AKD Sicil CANLI (akd_sicil.py + akd_manuel_arsiv.csv) — arşiv büyüdükçe anlam kazanır",
    "İleri-test log birikimi: ileri_gunluk.csv (gunluk.yml, hafta içi 15:30 UTC) — tek gerçek OOS",
    "Makro: makro_guncel.json yarı-manuel (çeyreklik 2 sayı)",
    "İleri-test 3-çizgi SVG grafiği CANLI (drawIleriChart) — Sistem/Endeks/Mevduat, renk-körü dostu palet",
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
    s.append("\nGEÇMİŞ OTURUMLAR (son 3):")
    for o in GECMIS_OTURUMLAR[:3]:
        s.append(f"  • {o}")
    return "\n".join(s)


if __name__ == "__main__":
    print(durum_metni())
