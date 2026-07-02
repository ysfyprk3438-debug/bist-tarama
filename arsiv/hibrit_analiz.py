"""
═══════════════════════════════════════════════════════════════
HİBRİT ANALİZ MOTORU — APEX v3
═══════════════════════════════════════════════════════════════
Teşhis (N=1107, t=-1.9): saf teknik (RSI/MACD/trend), komisyon sonrası
mevduatı YENMİYOR. Sebep parametre değil, strateji ailesi.

Çözüm — üç katmanı HARMANLAYAN hibrit (kullanıcının istediği 3. yol):

  KATMAN A · MAKRO / REJİM  (NE ZAMAN piyasada olunur)
     - Endeksin (XU100) kendi trendi: boğa mı, ayı mı?
     - Göreli güç: hisse endeksi geçiyor mu? (lider/takipçi)
     - Hissenin kendi trend hizası
     → Backtest'te DÜRÜSTÇE ölçülür (nokta-zamanlı endeks dilimi).

  KATMAN B · KURUMSAL / "TERA TARZI" AKILLI PARA  (NE alınır)
     - Birikim ayak izi: OBV yükseliyor + CMF pozitif + büyük oyuncu
     - Sessiz toplama: OBV artarken fiyat henüz patlamamış
     → OHLCV'den hesaplanır, backtest'te dürüst.

  KATMAN C · TEKNİK TETİK  (GİRİŞ anı — mevcut motor)
     - RSI/MACD/trend sinyali. Artık ÖNCÜ değil, KAPI BEKÇİSİ.
     → Önce teknik sinyal olmalı; sonra A ve B onaylamalı.

  KATMAN D · FUNDAMENTAL  (CANLI-ONLY KANCA, backtest'te KAPALI)
     - F/K, ROE, yabancı oranı... Geçmiş nokta-zamanlı veri OLMADIĞI
       için backtest'e SOKULMAZ (lookahead'i geri getirmemek için).
     - Canlı taramada veri kaynağı bağlanınca açılır.

MANTIK: teknik tetik VAR + (makro × kurumsal) skoru EŞİĞİ geçerse → sinyal.
Aksi halde None. Yani saf teknikten daha SEÇİCİ; kötü işlemleri eler.
Hedef/stop mantığı taban motordan AYNEN alınır (tek değişkeni —
seçiciliği — izole etmek için; iyileşme ona atfedilebilsin).
"""

import numpy as np

# ── Ayarlar (tek bilinçli knob: seçicilik eşiği) ──
HIBRIT_ESIK = 60.0       # makro×kurumsal skoru bu eşiği geçmeli (0-100). Düşür → çok işlem.
W_MAKRO = 0.50           # birleşik skorda makro ağırlığı
W_KURUMSAL = 0.50        # birleşik skorda kurumsal ağırlığı


def _makro_skor(df, endeks_close, r):
    """Makro/rejim skoru 0-100: hisse trendi + endeks rejimi + göreli güç."""
    parcalar = []  # (agirlik, 0..1 skor)

    # 1) Hissenin kendi trend hizası (taban motordan: trend 0..4)
    trend = r.get("trend", 0) or 0
    parcalar.append((30.0, min(1.0, trend / 4.0)))

    if endeks_close is not None and len(endeks_close) >= 50:
        # 2) Endeks rejimi: endeks kendi 50'lik ortalamasının üstünde mi?
        ic = float(endeks_close.iloc[-1])
        ima = float(endeks_close.rolling(50).mean().iloc[-1])
        parcalar.append((35.0, 1.0 if ic > ima else 0.0))

        # 3) Göreli güç: hisse, endeksi son ~60 barda geçti mi?
        n = int(min(60, len(df) - 1, len(endeks_close) - 1))
        if n > 5:
            s_ret = float(df["Close"].iloc[-1] / df["Close"].iloc[-1 - n] - 1.0)
            i_ret = float(endeks_close.iloc[-1] / endeks_close.iloc[-1 - n] - 1.0)
            parcalar.append((35.0, 1.0 if s_ret > i_ret else 0.0))

    toplam_agirlik = sum(a for a, _ in parcalar)
    if toplam_agirlik <= 0:
        return 50.0
    skor = sum(a * s for a, s in parcalar) / toplam_agirlik * 100.0
    return float(max(0.0, min(100.0, skor)))


def _kurumsal_skor(df, r):
    """Kurumsal/Tera-tarzı birikim skoru 0-100: OBV+CMF+büyük oyuncu+sessiz toplama."""
    sm = r.get("sm", {}) or {}
    skor = 50.0
    if sm.get("obv_trend"):
        skor += 15
    if sm.get("uyum"):
        skor += 10
    if sm.get("buyuk_oyuncu"):
        skor += 10
    cmf = float(sm.get("cmf", 0.0) or 0.0)
    if cmf > 0.10:
        skor += 15
    elif cmf < -0.10:
        skor -= 20

    # Sessiz toplama: OBV yükselirken fiyat henüz patlamamış (kurumsal birikim izi)
    k = df["Close"]
    if len(k) >= 11:
        p_chg = float(k.iloc[-1] / k.iloc[-11] - 1.0)
        if sm.get("obv_trend") and (0.0 <= p_chg < 0.06):
            skor += 10

    return float(max(0.0, min(100.0, skor)))


def fundamental_skor(kod, tarih=None, backtest=False):
    """
    CANLI-ONLY KANCA. Backtest'te DAİMA None döner (nokta-zamanlı geçmiş
    fundamental veri olmadığı için — lookahead'i geri getirmemek adına).
    Canlıda ileride İş Yatırım/Fintables vb. bağlanınca 0-100 skor döndürür.
    """
    if backtest:
        return None
    # TODO(canlı): F/K, ROE, yabancı takas oranı, net borç/FAVÖK çek → 0-100 skor
    return None


def analiz_et(kod, df, vade_ayar, portfoy_tl, carpan, sektor,
              detayli=True, endeks_close=None, backtest=False):
    """
    Taban (teknik) motoru çağırır; sinyal varsa makro×kurumsal ile FİLTRELER.
    İmza, analiz.analiz_et ile birebir aynı (backtest harness sorunsuz çağırsın).
    """
    # Lazy import: ağır bağımlılıkları (matplotlib vs) modül yüklenirken çekme
    import analiz as teknik

    # KATMAN C — teknik tetik (kapı bekçisi). Sinyal yoksa zaten aday yok.
    r = teknik.analiz_et(kod, df, vade_ayar, portfoy_tl, carpan, sektor,
                         detayli=detayli, endeks_close=endeks_close, backtest=backtest)
    if r is None:
        return None

    # KATMAN A & B — makro × kurumsal
    makro = _makro_skor(df, endeks_close, r)
    kurumsal = _kurumsal_skor(df, r)
    hibrit = W_MAKRO * makro + W_KURUMSAL * kurumsal

    # KATMAN D — fundamental (canlıda; backtest'te None → etkisiz)
    fnd = fundamental_skor(kod, r.get("tarih"), backtest=backtest)
    if fnd is not None:
        # canlıda fundamental'i de harmanla (üçe böl), backtest'te bu dal çalışmaz
        hibrit = (makro + kurumsal + fnd) / 3.0

    # Seçicilik: eşik geçilmezse işlem YOK
    if hibrit < HIBRIT_ESIK:
        return None

    # Hedef/stop taban motordan AYNEN korunur. Yalnızca hibrit alanları eklenir.
    r["makro_skor"] = round(makro, 1)
    r["kurumsal_skor"] = round(kurumsal, 1)
    r["hibrit_skor"] = round(hibrit, 1)
    r["fundamental_skor"] = fnd
    return r
