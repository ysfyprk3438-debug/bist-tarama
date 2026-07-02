"""
═══════════════════════════════════════════════════════════════
PERFORMANS KARNESİ — BIST Para Avcısı v4
═══════════════════════════════════════════════════════════════
Robot kendini her gün puanlar. Sen günlük/haftalık/aylık/yıllık
başarısını görürsün — gerçek bir fon yöneticisi karnesi gibi.

Çalışma:
  1. Her tur/gün → portföy değeri kaydedilir (anlik_kaydet)
  2. Dönemsel getiri hesaplanır (donemsel_getiri)
  3. Robot kendine günlük not verir (oz_puanlama)

NOT: Gün gün birikmek için Supabase gerekir (kalıcı saklama).
Oturum içinde çalışır; Supabase bağlanınca günler boyu birikir.
"""

import datetime
import numpy as np


# ══════════════════════════════════════════════════════════════
# ANLIK GÖRÜNTÜ (SNAPSHOT) KAYDI
# ══════════════════════════════════════════════════════════════
def anlik_kaydet(gecmis_deger, toplam, nakit, pozisyon_sayisi, xu100_pct=0.0):
    """
    Robotun o anki değerini zaman damgasıyla kaydet.
    gecmis_deger: liste (session_state'te tutulur)
    Aynı güne birden çok kayıt olabilir; en sonuncusu o günü temsil eder.
    """
    simdi = datetime.datetime.now()
    gecmis_deger.append({
        "zaman": simdi.isoformat(),
        "tarih": simdi.date().isoformat(),
        "deger": float(toplam),
        "nakit": float(nakit),
        "pozisyon": int(pozisyon_sayisi),
        "xu100_pct": float(xu100_pct),
    })


def _gun_sonu_degerleri(gecmis_deger):
    """Her gün için son değeri al (gün sonu kapanışı gibi)."""
    gunluk = {}
    for kayit in gecmis_deger:
        gunluk[kayit["tarih"]] = kayit  # aynı gün tekrarsa sonuncusu kalır
    return sorted(gunluk.values(), key=lambda x: x["tarih"])


# ══════════════════════════════════════════════════════════════
# DÖNEMSEL GETİRİ (gün / hafta / ay / yıl)
# ══════════════════════════════════════════════════════════════
def _periyot_basi_deger(gun_degerleri, gun_once):
    """gun_once gün önceki (veya en yakın eski) değeri bul."""
    if not gun_degerleri:
        return None
    hedef = datetime.date.today() - datetime.timedelta(days=gun_once)
    # Hedeften önceki en son kayıt
    onceki = [g for g in gun_degerleri if datetime.date.fromisoformat(g["tarih"]) <= hedef]
    if onceki:
        return onceki[-1]["deger"]
    # Yoksa en eski kayıt (başlangıç)
    return gun_degerleri[0]["deger"]


def donemsel_getiri(gecmis_deger, baslangic_bakiye):
    """
    Günlük/haftalık/aylık/yıllık getiriyi hesaplar.
    Dönen: her dönem için {getiri_pct, getiri_tl}
    """
    gunler = _gun_sonu_degerleri(gecmis_deger)
    if not gunler:
        return None

    simdi = gunler[-1]["deger"]

    def _getiri(gecmis_deger_baz):
        if gecmis_deger_baz is None or gecmis_deger_baz <= 0:
            return 0.0, 0.0
        pct = (simdi - gecmis_deger_baz) / gecmis_deger_baz * 100
        tl = simdi - gecmis_deger_baz
        return pct, tl

    # Bugünün başı: bugünden önceki son kayıt (dün kapanışı)
    bugun = datetime.date.today()
    bugun_oncesi = [g for g in gunler if datetime.date.fromisoformat(g["tarih"]) < bugun]
    gun_baz = bugun_oncesi[-1]["deger"] if bugun_oncesi else gunler[0]["deger"]

    g_pct, g_tl = _getiri(gun_baz)
    h_pct, h_tl = _getiri(_periyot_basi_deger(gunler, 7))
    a_pct, a_tl = _getiri(_periyot_basi_deger(gunler, 30))
    y_pct, y_tl = _getiri(_periyot_basi_deger(gunler, 365))
    # Tüm zamanlar (başlangıç bakiyesine göre)
    t_pct = (simdi - baslangic_bakiye) / baslangic_bakiye * 100 if baslangic_bakiye > 0 else 0
    t_tl = simdi - baslangic_bakiye

    return {
        "gunluk": {"pct": g_pct, "tl": g_tl},
        "haftalik": {"pct": h_pct, "tl": h_tl},
        "aylik": {"pct": a_pct, "tl": a_tl},
        "yillik": {"pct": y_pct, "tl": y_tl},
        "tum": {"pct": t_pct, "tl": t_tl},
        "guncel_deger": simdi,
        "gun_sayisi": len(gunler),
    }


# ══════════════════════════════════════════════════════════════
# ÖZ-PUANLAMA — robot kendine not verir
# ══════════════════════════════════════════════════════════════
def oz_puanlama(karne_ozet, donem, xu100_pct=0.0):
    """
    Robot kendine 0-100 not + harf notu verir.
    karne_ozet: gecmis.performans_ozet çıktısı (başarı oranı vs)
    donem: donemsel_getiri çıktısı
    xu100_pct: kıyas için endeks getirisi

    4 bileşen: getiri + başarı oranı + endeksi yenme + disiplin
    """
    puan = 0
    detay = []

    # 1) Getiri (bu dönem) — 40 puan
    if donem:
        d_getiri = donem["tum"]["pct"]
        if d_getiri >= 20: g = 40
        elif d_getiri >= 10: g = 32
        elif d_getiri >= 5: g = 24
        elif d_getiri >= 0: g = 16
        elif d_getiri >= -5: g = 8
        else: g = 0
        puan += g
        detay.append(("Getiri", g, 40, f"%{d_getiri:+.1f}"))

    # 2) Başarı oranı — 30 puan
    if karne_ozet:
        basari = karne_ozet["basari_pct"]
        g = int(basari / 100 * 30)
        puan += g
        detay.append(("Başarı oranı", g, 30, f"%{basari:.0f}"))
    else:
        detay.append(("Başarı oranı", 0, 30, "veri yok"))

    # 3) Endeksi yenme — 20 puan
    if donem:
        fark = donem["tum"]["pct"] - xu100_pct
        if fark >= 10: g = 20
        elif fark >= 5: g = 15
        elif fark >= 0: g = 10
        elif fark >= -5: g = 5
        else: g = 0
        puan += g
        detay.append(("Endeksi yenme", g, 20, f"%{fark:+.1f} fark"))

    # 4) Disiplin (stop kullanımı) — 10 puan
    if karne_ozet:
        toplam = karne_ozet["toplam"]
        if toplam > 0:
            # Stop yiyenler kontrollü kayıp demek (disiplin), süre dolan belirsiz
            stop = karne_ozet["stop_yiyen"]
            hedef = karne_ozet["hedef_tutan"]
            kapali_net = stop + hedef
            disiplin = (kapali_net / toplam) if toplam > 0 else 0
            g = int(disiplin * 10)
            puan += g
            detay.append(("Disiplin", g, 10, f"%{disiplin*100:.0f} net çıkış"))

    puan = max(0, min(100, puan))

    # Harf notu
    if puan >= 85: harf, renk, yorum = "A", "#10B981", "Mükemmel — usta gibi"
    elif puan >= 70: harf, renk, yorum = "B", "#34D399", "İyi — istikrarlı"
    elif puan >= 55: harf, renk, yorum = "C", "#F59E0B", "Orta — geliştirilebilir"
    elif puan >= 40: harf, renk, yorum = "D", "#FB923C", "Zayıf — gözden geçir"
    else: harf, renk, yorum = "F", "#EF4444", "Kötü — strateji değişmeli"

    return {
        "puan": puan, "harf": harf, "renk": renk, "yorum": yorum,
        "detay": detay,
    }


# ══════════════════════════════════════════════════════════════
# DEĞER GRAFİĞİ İÇİN VERİ (gün gün portföy değeri)
# ══════════════════════════════════════════════════════════════
def deger_serisi(gecmis_deger):
    """Grafik için (tarih, değer) listesi döner."""
    gunler = _gun_sonu_degerleri(gecmis_deger)
    return [(g["tarih"], g["deger"]) for g in gunler]


# ══════════════════════════════════════════════════════════════
# RİSK-DÜZELTİLMİŞ KALİTE — Sharpe, Sortino, Max Drawdown
# ══════════════════════════════════════════════════════════════
def risk_metrikleri(gecmis_deger, risksiz_yillik=45.0):
    """
    Robotun risk-düzeltilmiş kalitesini ölçer.
    "Şanslı mıydı yoksa gerçekten iyi mi?" sorusunun cevabı.

    Sharpe  → risk başına getiri (yüksek = iyi, dalgalanmadan kazanıyor)
    Sortino → sadece KÖTÜ dalgalanma başına getiri (Sharpe'tan dürüst)
    Max Drawdown → en kötü tepe-dip düşüşü (katlanılan acı)
    risksiz_yillik → TL mevduat ~%45; robot bunu yenmeli yoksa boşuna

    Dönen: {sharpe, sortino, max_dd, yillik_vol, yillik_getiri, kalite, renk, yorum}
    """
    gunler = _gun_sonu_degerleri(gecmis_deger)
    if len(gunler) < 10:
        return None  # anlamlı Sharpe için en az ~10 gün lazım

    degerler = np.array([g["deger"] for g in gunler], dtype=float)
    getiriler = np.diff(degerler) / (degerler[:-1] + 1e-10)  # günlük getiriler

    if len(getiriler) < 5 or np.std(getiriler) < 1e-10:
        return None

    # Risksiz günlük oran (yıllık → günlük)
    risksiz_gunluk = (1 + risksiz_yillik / 100) ** (1 / 252) - 1
    fazla = getiriler - risksiz_gunluk

    # Sharpe (yıllıklaştırılmış)
    sharpe = float(np.mean(fazla) / (np.std(getiriler) + 1e-10) * np.sqrt(252))

    # Sortino (sadece negatif getirilerin std'si = aşağı yönlü risk)
    negatifler = getiriler[getiriler < 0]
    if len(negatifler) >= 2:
        asagi_vol = np.std(negatifler)
        sortino = float(np.mean(fazla) / (asagi_vol + 1e-10) * np.sqrt(252))
    else:
        sortino = sharpe * 1.4  # neredeyse hiç negatif yok = çok iyi

    # Maksimum düşüş (peak-to-trough)
    tepe = np.maximum.accumulate(degerler)
    dususler = (degerler - tepe) / tepe
    max_dd = float(dususler.min() * 100)

    # Yıllıklaştırılmış volatilite ve getiri
    yillik_vol = float(np.std(getiriler) * np.sqrt(252) * 100)
    gun_sayisi = len(degerler)
    toplam_getiri = (degerler[-1] - degerler[0]) / degerler[0]
    yillik_getiri = float(((1 + toplam_getiri) ** (252 / gun_sayisi) - 1) * 100) if gun_sayisi > 0 else 0

    # ── KALİTE YARGISI ──
    # Sharpe yorumu (profesyonel eşikler)
    if sharpe >= 2.0:
        kalite, renk = "MÜKEMMEL", "#10B981"
        yorum = "Olağanüstü risk-getiri — istikrarlı, sürdürülebilir kazanç. Usta seviye."
    elif sharpe >= 1.0:
        kalite, renk = "İYİ", "#34D399"
        yorum = "Sağlam risk-getiri — aldığı riske değer kazanç üretiyor."
    elif sharpe >= 0.5:
        kalite, renk = "ORTA", "#F59E0B"
        yorum = "Kabul edilebilir ama dalgalı — getiri var ama risk de yüksek."
    elif sharpe >= 0:
        kalite, renk = "ZAYIF", "#FB923C"
        yorum = "Düşük kalite — getiri riski karşılamıyor, şans payı yüksek olabilir."
    else:
        kalite, renk = "KÖTÜ", "#EF4444"
        yorum = "Negatif risk-getiri — risksiz mevduatın altında, strateji değişmeli."

    # Mevduatı yeniyor mu?
    mevduati_yeniyor = yillik_getiri > risksiz_yillik

    return {
        "sharpe": round(sharpe, 2),
        "sortino": round(sortino, 2),
        "max_dd": round(max_dd, 1),
        "yillik_vol": round(yillik_vol, 1),
        "yillik_getiri": round(yillik_getiri, 1),
        "kalite": kalite, "renk": renk, "yorum": yorum,
        "mevduati_yeniyor": mevduati_yeniyor,
        "risksiz_yillik": risksiz_yillik,
    }
