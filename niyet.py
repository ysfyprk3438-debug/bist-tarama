"""
═══════════════════════════════════════════════════════════════
NİYET OKUYUCU — BIST Para Avcısı v4
═══════════════════════════════════════════════════════════════
Hisseye değil, HİSSEDEKİ PARANIN DAVRANIŞINA bakar.
Her hareketin arkasında bir aktör var — bunu fiyat+hacim gölgesinden
sınıflandırır:

  • SESSİZ TOPLAMA  → fiyat yatay, hacim sinsice artıyor (patlamadan önce)
  • DAĞITIM         → fiyat yükseliyor ama tepeden satılıyor (manipülasyon/tuzak)
  • PANİK/DİP       → sert düşüş + dev hacim + toparlama (dip oluşumu)
  • SÜRÜ/ZİRVE      → RSI uçmuş, hacim absürt (geç kalınmış)
  • NORMAL          → ayırt edici örüntü yok

DÜRÜSTLÜK NOTU:
Bu motor sadece fiyat+hacim ile çalışır → "niyet GÖLGESİ" okur, kesinlik değil.
Gerçek niyet okuma için AKD (aracı kurum dağılımı) + derinlik verisi gerekir.
Motor o veriyi kabul edecek şekilde tasarlandı: akd_verisi parametresi
ileride beslenince gölge → gerçeğe döner.
"""

import numpy as np


def _guvenli(seri, varsayilan=0.0):
    try:
        v = float(seri)
        return v if not (np.isnan(v) or np.isinf(v)) else varsayilan
    except (ValueError, TypeError):
        return varsayilan


def niyet_oku(df, rsi_son=None, akd_verisi=None):
    """
    Paranın davranışını sınıflandırır.
    df: OHLCV
    rsi_son: hesaplanmış RSI (yoksa None)
    akd_verisi: ileride aracı kurum dağılımı (şimdilik None → gölge modu)

    Dönen: {sinif, guven, aciklama, renk, uyari}
    """
    if df is None or len(df) < 20:
        return {"sinif": "BELİRSİZ", "guven": 0, "aciklama": "Yetersiz veri",
                "renk": "#64748B", "uyari": False}

    k = df["Close"]
    v = df["Volume"]
    h = df["High"]
    l = df["Low"]

    # ── Temel ölçümler ──
    hacim_ort20 = _guvenli(v.rolling(20).mean().iloc[-1], 1)
    hacim_son = _guvenli(v.iloc[-1], 0)
    hacim_son3 = _guvenli(v.iloc[-3:].mean(), 0)
    hacim_kat = hacim_son3 / hacim_ort20 if hacim_ort20 > 0 else 1

    # Son 5 ve 20 günlük fiyat değişimi
    fiyat_son = _guvenli(k.iloc[-1], 0)
    fiyat_5once = _guvenli(k.iloc[-5], fiyat_son)
    fiyat_20once = _guvenli(k.iloc[-20], fiyat_son)
    degisim_5 = ((fiyat_son - fiyat_5once) / fiyat_5once * 100) if fiyat_5once > 0 else 0
    degisim_20 = ((fiyat_son - fiyat_20once) / fiyat_20once * 100) if fiyat_20once > 0 else 0
    # 30 günlük dip mesafesi — düşüşten dönüş tespiti için
    dusuk_30 = _guvenli(k.iloc[-30:].min(), fiyat_son) if len(k) >= 30 else _guvenli(k.min(), fiyat_son)
    yuksek_30 = _guvenli(k.iloc[-30:].max(), fiyat_son) if len(k) >= 30 else _guvenli(k.max(), fiyat_son)
    dipten_yukseli = ((fiyat_son - dusuk_30) / dusuk_30 * 100) if dusuk_30 > 0 else 0
    tepeden_dusus = ((fiyat_son - yuksek_30) / yuksek_30 * 100) if yuksek_30 > 0 else 0

    # OBV eğimi (para birikimi yönü) — son 5 günün ortalaması, önceki 15 güne göre
    yon = np.sign(k.diff()).fillna(0)
    obv = (yon * v).cumsum()
    if len(obv) >= 15:
        obv_son = float(obv.iloc[-5:].mean())
        obv_onceki = float(obv.iloc[-15:-5].mean())
        obv_artiyor = obv_son > obv_onceki
    else:
        obv_artiyor = True

    # Kapanışın gün içi konumu (tepeden mi kapatıyor, dipten mi?)
    # Son 5 günde: yüksek hacimli günlerde kapanış nerede?
    son5 = df.iloc[-5:]
    kapanis_konum = []
    for _, g in son5.iterrows():
        aralik = g["High"] - g["Low"]
        if aralik > 0:
            konum = (g["Close"] - g["Low"]) / aralik  # 1=tepeden kapatış, 0=dipten
            kapanis_konum.append(konum)
    ort_kapanis_konum = np.mean(kapanis_konum) if kapanis_konum else 0.5

    # RSI
    rsi = rsi_son if rsi_son is not None else 50

    # ── SINIFLANDIRMA (öncelik sırasıyla) ──
    uyari = False

    # 1) DAĞITIM / MANİPÜLASYON: fiyat yükselmiş + yüksek hacim + tepeden satılıyor
    if degisim_20 > 6 and hacim_kat > 1.6 and ort_kapanis_konum < 0.4:
        return {
            "sinif": "DAĞITIM", "guven": min(90, int(45 + hacim_kat * 12)),
            "aciklama": "Fiyat yükseliyor ama yüksek hacimli günlerde tepeden satış var — büyük oyuncu malı dağıtıyor olabilir. Yukarısı tuzak.",
            "renk": "#EF4444", "uyari": True,
        }

    # 2) OLAĞANDIŞI / LİKİDİTE TUZAĞI: absürt hacim + ani sıçrama
    if hacim_kat > 2.5 and degisim_5 > 15:
        return {
            "sinif": "OLAĞANDIŞI HAREKET", "guven": min(88, int(45 + hacim_kat * 8)),
            "aciklama": "Hacim normalin 2.5+ katı, ani sıçrama — olağandışı. Çıkışta alıcı bulamama (likidite) riski. Temkinli ol.",
            "renk": "#EF4444", "uyari": True,
        }

    # 3) SÜRÜ / ZİRVE: RSI uçmuş + yüksek hacim + dikey çıkış
    if rsi > 76 and hacim_kat > 1.5 and degisim_5 > 12:
        return {
            "sinif": "SÜRÜ / ZİRVE", "guven": min(85, int(40 + rsi * 0.5)),
            "aciklama": "Dikey yükseliş, yüksek hacim, RSI uçmuş — sürü psikolojisi, geç kalınmış olabilir. Zirveye yakın.",
            "renk": "#F59E0B", "uyari": True,
        }

    # 4) PANİK / DİP OLUŞUMU: 30 günde tepeden ciddi düşmüş + yüksek hacim + son günlerde toparlama
    #    (TOPLAMA'dan önce kontrol — düşüşten dönüş, yatay birikimle karışmasın)
    if tepeden_dusus < -10 and hacim_kat > 1.4 and degisim_5 > -1:
        return {
            "sinif": "DİP OLUŞUMU", "guven": min(75, int(38 + abs(tepeden_dusus))),
            "aciklama": "Sert düşüş sonrası yüksek hacimle toparlama — panik satışı bitmiş, dip oluşuyor olabilir.",
            "renk": "#34D399", "uyari": False,
        }

    # 5) SESSİZ TOPLAMA: fiyat yatay/hafif + hacim artıyor + OBV yükseliyor + güçlü kapanış
    if abs(degisim_20) < 7 and hacim_kat > 1.25 and obv_artiyor and ort_kapanis_konum > 0.45:
        return {
            "sinif": "SESSİZ TOPLAMA", "guven": min(80, int(40 + hacim_kat * 15)),
            "aciklama": "Fiyat sakin ama hacim ve para birikimi (OBV) artıyor — birileri gürültüsüz topluyor olabilir. Patlamadan önceki birikim.",
            "renk": "#10B981", "uyari": False,
        }

    # 6) NORMAL — ayırt edici örüntü yok
    return {
        "sinif": "NORMAL", "guven": 40,
        "aciklama": "Belirgin bir toplama/dağıtım deseni yok — sıradan seyir.",
        "renk": "#94A3B8", "uyari": False,
    }


def guven_birlestir(puan, sm_skor, niyet, gecmis_basari=None):
    """
    GÜVEN MOTORU: teknik puan + akıllı para + niyet + geçmiş başarıyı
    tek bir güven seviyesi + gerekçeye birleştirir.

    gecmis_basari: bu sinyal tipinin geçmiş başarı oranı (varsa)
    Dönen: {seviye, yuzde, gerekce, renk}
    """
    # Temel güven: teknik puan + akıllı para ortalaması
    taban = (puan * 0.5 + sm_skor * 0.5)

    # Niyet ayarı
    if niyet["uyari"]:
        taban *= 0.55  # manipülasyon/zirve şüphesi → güveni ciddi düşür
    elif niyet["sinif"] in ("SESSİZ TOPLAMA", "DİP OLUŞUMU"):
        taban = min(100, taban * 1.15)  # değerli desen → güveni artır

    # Geçmiş başarı ayarı (öz-ölçüm)
    if gecmis_basari is not None:
        # %50 nötr; üstü artırır, altı düşürür
        taban *= (0.7 + gecmis_basari / 100 * 0.6)

    yuzde = max(0, min(100, int(taban)))

    if yuzde >= 75:
        seviye, renk = "YÜKSEK", "#10B981"
    elif yuzde >= 55:
        seviye, renk = "ORTA", "#F59E0B"
    elif yuzde >= 35:
        seviye, renk = "DÜŞÜK", "#FB923C"
    else:
        seviye, renk = "ZAYIF", "#EF4444"

    # Gerekçe cümlesi
    parcalar = []
    if puan >= 70: parcalar.append("teknik güçlü")
    elif puan >= 50: parcalar.append("teknik orta")
    if sm_skor >= 70: parcalar.append("akıllı para girişi")
    elif sm_skor < 40: parcalar.append("akıllı para zayıf")
    if niyet["sinif"] not in ("NORMAL", "BELİRSİZ"):
        parcalar.append(niyet["sinif"].lower())
    if gecmis_basari is not None:
        parcalar.append(f"bu tip geçmişte %{gecmis_basari:.0f} tuttu")

    gerekce = ", ".join(parcalar) if parcalar else "ayırt edici sinyal yok"
    if niyet["uyari"]:
        gerekce = "⚠️ " + gerekce

    return {"seviye": seviye, "yuzde": yuzde, "gerekce": gerekce, "renk": renk}
