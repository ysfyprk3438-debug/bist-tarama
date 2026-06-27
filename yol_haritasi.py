# -*- coding: utf-8 -*-
"""
═══════════════════════════════════════════════════════════════
YOL HARİTASI — APEX (BİST)
═══════════════════════════════════════════════════════════════
Bu dosya projenin VİZYON HAFIZASIDIR. durum.py "neredeyiz"i, bu dosya
"nereye ve neden"i tutar.

Felsefe:
  Piyasa uyarlanır bir sistemdir. Bir kenar (edge) bulunup kullanıldıkça
  aşınır. "Kalıcı zirve" yoktur. Asıl kazanan zirveyi bulan değil, zirve
  kayınca en hızlı yeniden konumlanandır. Hedef bitmiş mükemmel program
  değil, kendini sürekli yeniden icat eden bir organizmadır.

  EK İLKE (27 Haz 2026 bakımından): Karmaşıklık ≠ edge. Katman eklemek
  doğrulanmamış bir stratejiye kenar KAZANDIRMAZ; sadece overfit yüzeyini
  büyütür. Önce DÜRÜST ÖLÇÜM, sonra strateji. Dürüstlük lükse değil temel.

Durum kodları: ✅ yapıldı · 🔨 yapılıyor · 🎯 sıradaki · 🔭 ufuk · 🔒 veri/altyapı bekliyor
"""

# ══════════════════════════════════════════════════════════════
# TAMAMLANANLAR
# ══════════════════════════════════════════════════════════════
TAMAMLANAN = [
    ("Çift kaynaklı veri (Yahoo + İş Yatırım, hata görünür)", "✅"),
    ("Analiz motoru (kendi göstergeleri, ta'ya bağımsız)", "✅"),
    ("Akıllı para skoru (OBV, CMF, büyük oyuncu)", "✅"),
    ("Sanal cüzdan — komisyonlu paper trading", "✅"),
    ("Niyet Okuyucu + Güven Motoru", "✅"),
    ("Karar Sentezleyici (av skoru → tek karar)", "✅"),
    ("Volatilite rejimi / Karakter (Hurst) / Hacim profili / Zaman dilimi onayı", "✅"),
    ("AI/ML katmanı (walk-forward + kalibrasyon, F1 ile sahte-sıfır bug giderildi)", "✅"),
    ("NOVA otomatik robot motoru — cron'da canlı, sanal, komisyonlu (robot_durum.json)", "✅"),
    ("Mobil native UI (APEX/Pro/Trade) + Streamlit gömme", "✅"),
    ("Telegram bildirim + GitHub Actions zamanlanmış görevler", "✅"),
    ("UI dürüstlük Pas-1: winRate→kalibre olasılık, sahte emir defteri→dürüst not (CANLI)", "✅"),
    ("UI dürüstlük Pas-2: demo bakiye/pozisyon → gerçek APP.robot verisi (HAZIR, deploy bekliyor)", "🔨"),
    ("Komple kod bakımı + dürüst teşhis (27 Haz 2026)", "✅"),
]

# ══════════════════════════════════════════════════════════════
# KATMAN 0 — DÜRÜSTLÜK & ÖLÇÜM HATTI  (YENİ EN ÖNCELİK)
# Teşhis: dürüst bileşenler kodda VAR ama canlı yola zayıf olan bağlı;
# ve edge'i ölçecek backtest kırık. Strateji tartışmasından ÖNCE bu gelir.
# ══════════════════════════════════════════════════════════════
KATMAN_0_DURUSTLUK = {
    "no": 0,
    "ad": "Dürüstlük & Ölçüm Hattı",
    "durum": "🎯",
    "ozet": "Sistemi 'dürüstçe ölçülebilir' yap. Önce hangi sinyalin gerçek olduğunu "
            "bilmeden strateji tartışmak anlamsız.",
    "isler": [
        "BASELINE: konsolide hatasız v1.0 temel → GitHub (her şeyin üstüne bineceği zemin).",
        "Pas-2 cüzdanı canlıya al (gerçek portföy + 8 pozisyon).",
        "Göstergeyi/av_skoru'nu ML ile barıştır (kural-skoru ile kalibre olasılık çelişmesin).",
        "UI risk metriğini doğru motora bağla (performans.risk_metrikleri; günlüğe resample, mevduat %45 kıyas).",
        "UI öz-puanı oz_puanlama'ya bağla (endeksi yenmeyi ölçen sürüm).",
        "backtest.py onar: tazelik bypass + komisyon + mevduat eşiği → edge DÜRÜSTÇE ölçülsün.",
        "Sessiz bozulmayı görünür yap: veri-kalite etiketi + katman çökme logu.",
    ],
    "onkosul": "Yok — hemen yapılabilir. Hepsi mevcut kodun düzeltilmesi/bağlanması.",
}

# ══════════════════════════════════════════════════════════════
# ÜST KATMANLAR — ZİRVE KAYDIKÇA KOVALAMAK İÇİN
# ══════════════════════════════════════════════════════════════
KATMANLAR = [
    {
        "no": 1,
        "ad": "Kendini Yeniden Kalibre Eden Sistem",
        "durum": "🔒",
        "ozet": "Sistem hangi sinyal tipinin çürüdüğünü öz-ölçümden görüp KENDİ ağırlıklarını "
                "ayarlar. Statik kurallı bottan, rejimi kuraldan öğrenen sisteme geçiş.",
        "nasil": "Öz-ölçüm + Supabase sicili eşiğe ulaşınca son N günün başarı oranına göre "
                 "sinyal ağırlıkları dinamik güncellensin. (kalibrasyon.py zemini hazır.)",
        "onkosul": "🔒 Katman 0 + Supabase'e birkaç hafta GERÇEK sinyal/işlem sicili.",
    },
    {
        "no": 2,
        "ad": "Strateji Sorgusu — Edge Gerçekten Var mı?",
        "durum": "🔭",
        "ozet": "Katman 0 dürüst backtest verince asıl soru: mevcut teknik strateji ailesinin "
                "mevduata karşı kenarı VAR MI? Yoksa kabul et ve değiştir.",
        "nasil": "Dürüst backtest + gerçek sicil negatifse: (a) kanıtlanmış Türk fon yöneticisi "
                 "giriş/çıkış şablonunu reverse-engineer et, ya da (b) temel/makro özellik katmanı "
                 "ekle (sistem şu an %100 teknik/fiyat-türevli = en kalabalık alan).",
        "onkosul": "Katman 0'ın dürüst ölçümü.",
    },
    {
        "no": 3,
        "ad": "Gerçek Mikroyapı — Niyetin İzi",
        "durum": "🔒",
        "ozet": "Niyet Okuyucu'nun fiyat-gölgesinden gerçek emir defteri + AKD (aracı kurum "
                "dağılımı) + takas verisine olgunlaşması.",
        "nasil": "niyet.py akd_verisi parametresini kabul edecek şekilde tasarlandı; veri bağlanınca "
                 "gölge → gerçeğe döner. UI'de bu katman zaten 'kilitli, sahte göstermiyoruz' diyor.",
        "onkosul": "🔒 AKD/derinlik verisi (ForInvest lisansı / broker API).",
    },
    {
        "no": 4,
        "ad": "Strateji Ekosistemi & Kalabalık Psikolojisi",
        "durum": "🔨",
        "ozet": "Tek model yerine rejime göre yarışan stratejiler (momentum/dip/kırılım/defansif) + "
                "kalabalığın tahmin edilebilir irrasyonelliği. Zemin (strateji.py, psikoloji.py) yazılı.",
        "nasil": "Meta-katman rejime göre strateji ağırlığı dağıtır; gerçek sicille olgunlaşır.",
        "onkosul": "Katman 1 (öz-kalibrasyon) + gerçek sicil.",
    },
]

# ══════════════════════════════════════════════════════════════
# AKLA GELEN EK FİKİRLER (kaybolmasın)
# ══════════════════════════════════════════════════════════════
EK_FIKIRLER = [
    "Robot equity eğrisini günlüğe resample edip tek tutarlı risk motoru kullan (iki motoru birleştir).",
    "Telegram otomatik alarm (uygulama kapalıyken bildirim) — zaten cron'da, izle.",
    "Korelasyon/yığılma uyarısı gerçek veriyle olgunlaştır.",
    "Sat-geri al cooldown'unu rejime göre dinamikleştir.",
]


def yol_haritasi_metni():
    s = ["APEX — YOL HARİTASI\n" + "=" * 50]
    s.append(f"\nTAMAMLANAN ({len(TAMAMLANAN)}):")
    for ad, durum in TAMAMLANAN:
        s.append(f"  {durum} {ad}")
    s.append(f"\n  {KATMAN_0_DURUSTLUK['durum']} KATMAN 0: {KATMAN_0_DURUSTLUK['ad']} (EN ÖNCELİK)")
    for i in KATMAN_0_DURUSTLUK["isler"]:
        s.append(f"      • {i}")
    s.append("\nÜST KATMANLAR:")
    for k in KATMANLAR:
        s.append(f"  {k['durum']} K{k['no']}: {k['ad']}")
    return "\n".join(s)


if __name__ == "__main__":
    print(yol_haritasi_metni())
