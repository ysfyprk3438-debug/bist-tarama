"""
═══════════════════════════════════════════════════════════════
YOL HARİTASI — BIST Para Avcısı
═══════════════════════════════════════════════════════════════
Bu dosya projenin HAFIZASIDIR. "Sonra yaparız" denenler burada yaşar.
Yeni bir oturumda nereye gittiğimizi unutursak, buraya bakarız.

Felsefe:
  Piyasa uyarlanır bir sistemdir. Bir kenar (edge) bulunup kullanıldıkça
  aşınır. Bu yüzden "kalıcı zirve" yoktur — zirve, ona çıktıkça yer değiştirir.
  Asıl kazanan: zirveyi bulan değil, zirve kayınca en hızlı yeniden
  konumlanan sistemdir. Hedefimiz bitmiş mükemmel program değil,
  kendini sürekli yeniden icat eden bir organizmadır.

Durum kodları: ✅ yapıldı · 🔨 yapılıyor · 🎯 sıradaki · 🔭 ufuk · 🔒 veri/altyapı bekliyor
"""

# ══════════════════════════════════════════════════════════════
# TAMAMLANANLAR (v4.0 — bugüne kadar)
# ══════════════════════════════════════════════════════════════
TAMAMLANAN = [
    ("Çift kaynaklı veri katmanı (Yahoo + İş Yatırım, hata görünür)", "✅"),
    ("4 vade: gün içi / günlük / haftalık / aylık", "✅"),
    ("Analiz motoru (kendi göstergeleri, ta'ya bağımsız)", "✅"),
    ("Akıllı para skoru (OBV, CMF, büyük oyuncu)", "✅"),
    ("Sanal cüzdan — komisyonlu paper trading", "✅"),
    ("Av Panosu — günlük hedef + ilerleme takibi", "✅"),
    ("İzleme listesi + fiyat alarmı + 'keşke alsaydın'", "✅"),
    ("Backtest — geçmişe dönük strateji testi", "✅"),
    ("Sektör ısı haritası", "✅"),
    ("Robot — disiplinli/basit mod, dinamik rotasyon, cooldown", "✅"),
    ("Niyet Okuyucu — toplama/dağıtım/sürü/dip/olağandışı", "✅"),
    ("Güven Motoru — niyet + analiz + öz-ölçüm birleşik", "✅"),
    ("Öz-ölçüm — sinyal kaydı, otomatik sonuç takibi, başarı oranı", "✅"),
    ("Telegram bildirim entegrasyonu", "✅"),
    ("Tıklanır grafik — altın kesişim/destek/direnç işaretli + tek cümle yorum", "✅"),
    ("Alarm motoru — yaklaşan olaya geri sayım, kart titreşir/renk değiştirir", "✅"),
    ("Karar Sentezleyici — 5 sinyal → tek AV SKORU + net karar (emergent katman)", "✅"),
    ("Volatilite Rejimi — adaptif pozisyon/stop, rejime göre strateji (Katman 4 zemini)", "✅"),
    ("Karakter Motoru — Hurst (trend/salınım) + relatif güç (lider/takipçi) + strateji uyumu", "✅"),
    ("Hacim Profili & VWAP — POC, değer alanı, kurumsal destek/direnç seviyeleri", "✅"),
    ("Risk-Düzeltilmiş Kalite — Sharpe/Sortino/Max Drawdown, robotun gerçek kalitesi", "✅"),
    ("Çoklu Zaman Dilimi Onayı — üst trend teyidi, düşüşte sahte sıçrama tuzağı filtresi", "✅"),
    ("Piyasa Rejimi Freni — robot kötü piyasada savunmaya geçer (risk-off modu)", "✅"),
]

# ══════════════════════════════════════════════════════════════
# KATMANLAR — ZİRVE KAYDIKÇA KOVALAMAK İÇİN
# ══════════════════════════════════════════════════════════════
KATMANLAR = [
    {
        "no": 0,
        "ad": "Canlıya Çıkış & Veri Birikimi",
        "durum": "🎯",
        "ozet": "Mevcut sistemi gerçek BIST verisiyle ayağa kaldır. Tüm üst "
                "katmanlar gerçek geçmiş veri ister — o da ancak sistem canlı "
                "çalışınca birikir. Bu yüzden ilk adım budur.",
        "nasil": "11 dosyayı GitHub'a koy, Streamlit deploy et, ilk taramayı izle, "
                 "veri kaynağı ayarını gerçek veriyle kalibre et. Sinyaller "
                 "geçmişe kaydolmaya başlasın.",
        "onkosul": "Yok — bugün yapılabilir.",
    },
    {
        "no": 1,
        "ad": "Kendini Yeniden Kalibre Eden Sistem",
        "durum": "🔭",
        "ozet": "Sistem hangi sinyal tipinin son dönemde çürüdüğünü öz-ölçümden "
                "görüp KENDİ ağırlıklarını otomatik ayarlar. Statik kurallı bottan, "
                "rejim değişimini kuralın kendisinden öğrenen sisteme geçiş.",
        "nasil": "Öz-ölçüm verisi (gecmis.py) belli eşiğe ulaşınca, son N günün "
                 "başarı oranına göre sinyal puanı ağırlıkları dinamik güncellensin. "
                 "'DİP FIRSATI son 2 ayda %70→%45 düştü → ağırlığını kıs.'",
        "onkosul": "Katman 0 + en az birkaç hafta gerçek sinyal geçmişi.",
    },
    {
        "no": 2,
        "ad": "Piyasanın Dokusu — İlişki Ağı",
        "durum": "🔨",
        "ozet": "Tek hisseden sermayenin haritasına. Hangi hisseler birlikte "
                "hareket ediyor, hangi sektörden hangisine para akıyor, liderlik "
                "rotasyonu var mı? Mikroskoptan uydu görüntüsüne.",
        "nasil": "[YAPILDI] Yığılma uyarısı (portföy tek sektöre yığılınca uyarır) + "
                 "sektör rotasyon oku (para giren/çıkan sektör + lider hisse) + "
                 "korelasyon analizi (birlikte hareket eden hisseler) eklendi. "
                 "[KALAN] Gerçek veriyle canlı test, daha derin ağ analizi.",
        "onkosul": "Çekirdek tamam. Gerçek veriyle olgunlaşacak.",
    },
    {
        "no": 3,
        "ad": "Gerçek Mikroyapı — Niyetin İzi",
        "durum": "🔒",
        "ozet": "Niyet Okuyucu'nun olgunlaşması. Fiyat+hacim GÖLGESİNDEN, gerçek "
                "emir defteri + AKD (aracı kurum dağılımı) + takas verisine. "
                "Manipülasyon/toplama/dağıtım burada gölge değil, somut iz bırakır. "
                "'Yazılı olmayan kuralları okumak' asıl burada gerçekleşir.",
        "nasil": "niyet.py zaten akd_verisi parametresini kabul edecek şekilde "
                 "tasarlandı. Veri kaynağı bağlanınca gölge → gerçeğe döner.",
        "onkosul": "🔒 AKD/derinlik verisi gerekli (ForInvest lisansı, broker API'si). "
                   "NOT: Hacim Profili & VWAP, mikroyapının FİYAT-bazlı kısmını (POC, değer alanı) "
                   "zaten karşıladı — kalan kısım emir defteri + aracı kurum dağılımı.",
    },
    {
        "no": 4,
        "ad": "Strateji Ekosistemi — Rakip Beyinler",
        "durum": "✅",
        "ozet": "Tek 'doğru model' yerine birbiriyle yarışan birden çok strateji. "
                "Momentum avcısı, dip alıcı, kırılım takipçisi aynı anda yaşar; "
                "sistem hangisi o rejimde kazanıyorsa ona ağırlık verir. Tek "
                "strateji her rejimde kaybeder; ekosistem ayakta kalır.",
        "nasil": "Her strateji ayrı modül + ortak öz-ölçüm. Meta-katman gerçek "
                 "zamanlı olarak rejime göre strateji ağırlıklarını dağıtır.",
        "onkosul": "Katman 1 + Volatilite Rejimi (zemin HAZIR) — rejime göre strateji seçimi bu temele oturacak.",
    },
    {
        "no": 5,
        "ad": "Kalabalık Psikolojisi — Yazılı Olmayan Kural",
        "durum": "✅",
        "ozet": "Piyasa, insan psikolojisinin toplamıdır: korku, açgözlülük, sürü, "
                "panik, umut. 'Yazılı olmayan kurallar' çoğunlukla kalabalığın "
                "tahmin edilebilir irrasyonelliğidir. Sistem ne kadar çok 'şu "
                "noktada panik satar', 'şu seviyede FOMO yapar' davranışı "
                "modellerse, o kadar yazılı olmayanı okur.",
        "nasil": "Niyet Okuyucu'yu onlarca davranış desenine genişlet. Duygu "
                 "göstergeleri (korku/açgözlülük endeksi), aşırılık tespiti, "
                 "dönüm noktası psikolojisi.",
        "onkosul": "Katman 3 (mikroyapı verisi) + Katman 4 (ekosistem) zemini.",
    },
]

# ══════════════════════════════════════════════════════════════
# AKLA GELEN EK FİKİRLER (kaybolmasın diye)
# ══════════════════════════════════════════════════════════════
EK_FIKIRLER = [
    "Tam otomatik geçmiş simülasyonu (robot.py simulasyon_kostur — tarihsel veri beslenince aktif)",
    "Korelasyon uyarısı: portföyün %X'i tek sektörde → risk dağıt",
    "Piyasa rejimi freni: düşüş trendinde robot alım iştahını kıssın",
    "Telegram otomatik alarm robotu (sunucu/zamanlanmış görev — uygulama kapalıyken bildirim)",
    "Sat-geri al optimizasyonu: cooldown'u rejime göre dinamik ayarla",
]


def yol_haritasi_metni():
    """Konsol/log için düz metin çıktı."""
    s = ["BIST PARA AVCISI — YOL HARİTASI\n" + "=" * 50]
    s.append(f"\nTAMAMLANAN ({len(TAMAMLANAN)}):")
    for ad, durum in TAMAMLANAN:
        s.append(f"  {durum} {ad}")
    s.append("\nKATMANLAR:")
    for k in KATMANLAR:
        s.append(f"  {k['durum']} K{k['no']}: {k['ad']}")
    s.append("\nEK FİKİRLER:")
    for f in EK_FIKIRLER:
        s.append(f"  • {f}")
    return "\n".join(s)
