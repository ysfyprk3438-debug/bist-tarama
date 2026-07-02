"""
═══════════════════════════════════════════════════════════════
YOL HARİTASI — APEX
═══════════════════════════════════════════════════════════════
Bu dosya projenin HAFIZASIDIR. "Sonra yaparız" denenler burada yaşar.

KİMLİK:
  APEX bir BIST risk & analiz terminalidir, tahmin motoru değil.
  15 dk gecikmeli perakende veriyle kanıtlanmış yön edge'i yoktur.
  Değer eksenimiz RİSK DİSİPLİNİ: vol-hedefli pozisyon, ATR stop, dürüst sicil.

OKUMA DİLİ (kalıcı — projenin ruhu):
  Hiçbir okuma yön vermez. Her okuma "piyasa bunu nasıl okur, neye vurgu
  yapar" der ve KENDİ 1-yıl sicilini taşır: kaç kez oldu, sonraki ~10 gün
  ▲kaç/ort% · ▼kaç/ort%, isabet oranı. İsabet %40–60 → gri "≈ yazı-tura".
  Bu kural her sinyale uygulanır: altın/ölüm kesişimi, fiyat-MA kesişimi,
  yeni zirve/dip, RSI aşırı, geri çekilme, Bollinger sıkışma, boşluk,
  destek/direnç ve AKD/takas desenleri. Yıldız veri; tahmin değil.

FELSEFE:
  Bir edge bulunup kullanıldıkça aşınır; kalıcı zirve yoktur. Ama biz zirve
  kovalamıyoruz — kanıtlanmamış getiri tahmininin peşine düşmüyoruz. Kovaladığımız
  şey: hangi piyasada olursa olsun riski bütçe içinde tutan, ne HESAPLAYAMADIĞINI
  dürüstçe söyleyen bir sistem.

Durum kodları: ✅ yapıldı · 🔨 yapılıyor · 🎯 sıradaki · 🔭 ufuk · 🔒 veri bekliyor
"""

# ══════════════════════════════════════════════════════════════
# DOĞRULANMIŞ ÇEKİRDEK (rigorlu OOS + placebo'dan geçen)
# ══════════════════════════════════════════════════════════════
DOGRULANAN = [
    ("Vol-hedefli pozisyon (pozisyon.py) — gerçekleşen MaxDD bütçe altında", "✅"),
    ("ATR(14)×2 stop — 60-gün-dip sezgisini yener", "✅"),
    ("Placebo baseline zorunluluğu — edge, rastgele tabanı geçmeli", "✅"),
    ("Look-ahead bias yokluğu (veri-kesme testi) + temiz para muhasebesi", "✅"),
    ("Okuma dili + 1-yıl sicil altyapısı (yön yok, sadece doku + sicil)", "✅"),
    ("İşlem Planı Motoru — ATR giriş/stop/hedef, pivot destek/direnç", "✅"),
    ("Beklenen Değer + Placebo (R-katları, komisyon dahil, edge = beklenti − placebo)", "✅"),
    ("AL Sinyali çok-filtreli kapı (aktif bölge + sicil≥%55 + R/R≥1,5 + edge>0,12R + n≥15)", "✅"),
]

# ══════════════════════════════════════════════════════════════
# EDGE ARADIK, BULAMADIK (dürüstlük kaydı — tekrar denenmesin)
# ══════════════════════════════════════════════════════════════
CURUYEN_EDGE = [
    "Çok-vadeli teknik / momentum / MA200 rejimi / temel / makro reel-faiz zamanlaması: "
    "hepsi OOS + placebo'da düştü.",
    "Makro reel-faiz rejimi: eşik taraması + lag stresini geçti AMA placebo B'de %55,7 "
    "(medyan) — performans beta'ydı, zamanlama becerisi değil.",
    "AKD/takas 'yabancı/kurum alıyor → al': manuel doğrulamada (AKFGY) da yön vermedi. "
    "Akış saklamacı-ağırlıklı (BofA YB), niyet okunamıyor.",
]

# ══════════════════════════════════════════════════════════════
# KATMANLAR
# ══════════════════════════════════════════════════════════════
KATMANLAR = [
    {
        "no": 3,
        "ad": "Niyetin İzi — AKD / Takas (MANUEL köprü)",
        "durum": "🔨",
        "ozet": "Fiyat+hacim gölgesinden gerçek aracı kurum dağılımı + takas verisine. "
                "Ama bu veri SİNYAL değil, ETİKET olarak girer: her desen kendi "
                "sicilini taşır, yön iddiası taşımaz.",
        "nasil": "ForInvest AKD/takas elle arşivlenir. Sıradaki: desen→sicil "
                 "etiketleyici — 'yabancı 3 ay üst-5 net alıcı' → sonraki ~10 gün "
                 "dağılımı; %40–60 isabette gri yazı-tura.",
        "ders": "AKFGY: temiz manuel veriyle bile yön edge'i çıkmadı. Custodian "
                "akışı niyet değil; 'ucuz F/K' rayiç kazancına yaslı sahte olabilir. "
                "Doku iyi, alfa yok — bu katman betimler, çağırmaz.",
    },
    {
        "no": 1,
        "ad": "Kendini Kalibre Eden Sicil",
        "durum": "🔭",
        "ozet": "Hangi okuma tipinin son dönemde çürüdüğünü sicilden görüp o okumanın "
                "vurgusunu kısar. Kural değişimini kuralın kendisinden öğrenir.",
        "nasil": "İleri-test verisi (ileri_gunluk.csv) eşiğe ulaşınca sicil ağırlıkları "
                 "son N günün isabetine göre güncellenir.",
        "onkosul": "İleri-test log birikimi (tek gerçek OOS).",
    },
]

# ══════════════════════════════════════════════════════════════
# AÇIK FİKİRLER (kaybolmasın)
# ══════════════════════════════════════════════════════════════
EK_FIKIRLER = [
    "Komuta Merkezi per-hisse sekmesi: tüm okumalar sicil paneliyle hisse içinde",
    "Makro yarı-manuel makro_guncel.json (çeyreklik 2 sayı) — tam otomatik TCMB reddedildi (doğrulanamaz)",
    "İleri-test grafiği Endeks/Mevduat renk ayrımı (kozmetik)",
]


def yol_haritasi_metni():
    s = ["APEX — YOL HARİTASI\n" + "=" * 50]
    s.append(f"\nDOĞRULANAN ({len(DOGRULANAN)}):")
    for ad, d in DOGRULANAN:
        s.append(f"  {d} {ad}")
    s.append("\nEDGE ÇIKMAYAN (tekrar deneme):")
    for c in CURUYEN_EDGE:
        s.append(f"  ✗ {c}")
    s.append("\nKATMANLAR:")
    for k in KATMANLAR:
        s.append(f"  {k['durum']} K{k['no']}: {k['ad']}")
    return "\n".join(s)


if __name__ == "__main__":
    print(yol_haritasi_metni())
