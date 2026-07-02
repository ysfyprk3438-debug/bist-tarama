# -*- coding: utf-8 -*-
"""
═══════════════════════════════════════════════════════════════════════════
backtest_v2.py — APEX DÜRÜST BACKTEST (portföy + maliyet + risk + mevduat kıyası)
═══════════════════════════════════════════════════════════════════════════

NEDEN GEREKLİ:
  Eski backtest.py 3 sebeple "edge gerçek mi?" sorusuna cevap veremiyordu:
    1) analiz_et içindeki "son veri 10 günden eski" filtresi backtest'te
       neredeyse her gün None döndürüyordu → ~0 işlem.
    2) Komisyon/slippage yoktu → getiriler şişik.
    3) Portföy yoktu → max drawdown / Sharpe / mevduat kıyası ölçülemiyordu.

  Bu dosya üçünü de çözer ve SENİN DOSYALARINI DEĞİŞTİRMEZ. Freshness filtresini
  "index kaydırma" hilesiyle güvenle atlar (değerlere dokunmaz, sadece tarihleri
  bugüne çeker; göstergeler değer-bazlı olduğu için sonuç bozulmaz).

NASIL ÇALIŞTIRILIR (PowerShell, repo klasörünün İÇİNDE):
    cd C:\\Users\\yusuf\\Downloads\\<repo-klasoru>
    pip install pandas numpy requests scikit-learn
    python backtest_v2.py

  ÖNEMLİ: Bu dosyayı veri.py, analiz.py, tarama_core.py ile AYNI klasöre koy,
  yoksa import çalışmaz.

NOT: Bu bir v1'dir. İlk çalıştırmada hata çıkarsa bana ekran çıktısını gönder,
     birlikte düzeltiriz. İnternet gerekir (Yahoo'dan veri çeker).
"""

import sys
import datetime
import numpy as np
import pandas as pd

# ─────────────────────────────────────────────────────────────────────────
# AYARLAR — buradan oyna
# ─────────────────────────────────────────────────────────────────────────
CONFIG = {
    "vade": "haftalik",          # "gunluk" / "haftalik" / "aylik"
    "gun": 1095,                 # kaç günlük geçmiş çekilsin (~3 yıl). Yahoo verirse alır.
    "baslangic_sermaye": 1_000_000,   # TL

    # Maliyetler (TEK YÖN — al ve sat ayrı ayrı uygulanır)
    "komisyon_pct": 0.02,        # %0.02 / yön  (Deniz Yatırım tarifenle değiştir)
    "slippage_pct": 0.05,        # %0.05 / yön  (likiditeye göre; muhafazakâr başla)

    # Portföy
    "max_pozisyon": 5,           # aynı anda en fazla kaç açık işlem
    "max_takip_gun": 30,         # bir işlem en fazla kaç gün açık kalır (sonra kapat)

    # Mevduat kıyası (yıllık brüt) — KENDİ bankanın oranını yaz
    "mevduat_yillik": 0.40,      # %40 (politika faizi ~%37, Haziran 2026)

    # ML katmanı
    "ml_kullan": False,          # True yaparsan ai_model sinyali de şart koşulur (YAVAŞ)
    "ml_olasilik_esik": 56,      # ml_kullan=True ise: ai olasılık >= bu değer olmalı

    # Hangi hisseler? boş bırak → tarama_core'daki tüm liste. Test için kısalt:
    "hisseler": None,            # örn: ["GARAN","ASELS","EREGL","BIMAS","THYAO"]
}


# ─────────────────────────────────────────────────────────────────────────
# Senin modüllerin
# ─────────────────────────────────────────────────────────────────────────
try:
    from veri import veri_al, VADE_AYAR
    from analiz import analiz_et
    import tarama_core as tc
except Exception as e:
    print("HATA: veri.py / analiz.py / tarama_core.py bulunamadı.")
    print("Bu dosyayı onlarla AYNI klasöre koyup öyle çalıştır.")
    print("Detay:", e)
    sys.exit(1)

AI = None
if CONFIG["ml_kullan"]:
    try:
        import ai_model as AI
    except Exception:
        print("UYARI: ai_model yüklenemedi, ML kapalı devam ediliyor.")
        AI = None


# ─────────────────────────────────────────────────────────────────────────
# Freshness filtresini güvenle atla: df'i kopyala, index'i bugüne kaydır.
# Değerler (OHLCV) aynı kalır; analiz_et yalnızca tarih kontrolünde index'in
# son gününe bakıyor, göstergeler değer-bazlı → sonuç bozulmaz.
# ─────────────────────────────────────────────────────────────────────────
def _bt_sinyal(gecmis_df, ayar, sektor):
    g = gecmis_df.copy()
    try:
        delta = pd.Timestamp(datetime.date.today()) - g.index[-1]
        g.index = g.index + delta
    except Exception:
        pass
    return analiz_et("BT", g, ayar, 100000, 1.0, sektor, detayli=False)


# ─────────────────────────────────────────────────────────────────────────
# Tek hisse için işlem listesi üret (point-in-time, maliyetli)
#  - Giriş: sinyal günü i'nin BİR SONRAKİ günü AÇILIŞ (gerçekçi)
#  - Çıkış: stop/hedef (aynı barda ikisi de varsa STOP önce — muhafazakâr)
#  - Maliyet: giriş ve çıkışta ayrı uygulanır
# ─────────────────────────────────────────────────────────────────────────
def _hisse_islemleri(kod, df, ayar):
    s = CONFIG["slippage_pct"] / 100.0
    c = CONFIG["komisyon_pct"] / 100.0
    sektor = tc.KOD_SEKTOR.get(kod, "Diğer")

    islemler = []
    n = len(df)
    bas = max(ayar["min_gun"], 120)
    i = bas
    son_idx = n - 2  # giriş için en az 1 sonraki bar lazım

    while i < son_idx:
        gecmis_df = df.iloc[:i]
        r = _bt_sinyal(gecmis_df, ayar, sektor)
        if r is None:
            i += 1
            continue

        # ML şartı (opsiyonel)
        if AI is not None:
            try:
                ai = AI.ai_analiz(gecmis_df)
                if ai.get("durum") != "model" or ai.get("olasilik", 0) < CONFIG["ml_olasilik_esik"] or ai.get("yon") != "AL":
                    i += 1
                    continue
            except Exception:
                i += 1
                continue

        hedef = r["hedef"]
        stop = r["stop"]

        # Giriş: bir sonraki bar açılışı (lookahead yok)
        giris_bar = df.iloc[i]  # i = gecmis_df'in bittiği günün BİR SONRASI
        giris_ham = float(giris_bar["Open"])
        if giris_ham <= 0:
            i += 1
            continue
        giris_net = giris_ham * (1 + s + c)   # alışta slippage+komisyon

        # Çıkışı sonraki günlerde ara
        sonuc, cikis_ham, gun = "ACIK", None, 0
        for j in range(i, min(i + CONFIG["max_takip_gun"], n)):
            bar = df.iloc[j]
            gun = j - i + 1
            if float(bar["Low"]) <= stop:
                sonuc, cikis_ham = "STOP", stop
                break
            if float(bar["High"]) >= hedef:
                sonuc, cikis_ham = "HEDEF", hedef
                break
        if cikis_ham is None:
            son_j = min(i + CONFIG["max_takip_gun"], n - 1)
            cikis_ham = float(df.iloc[son_j]["Close"])
            gun = son_j - i + 1

        cikis_net = cikis_ham * (1 - s - c)   # satışta slippage+komisyon
        net_getiri = (cikis_net / giris_net - 1) * 100

        islemler.append({
            "kod": kod,
            "giris_tarih": df.index[i],
            "cikis_tarih": df.index[min(i + gun - 1, n - 1)],
            "giris_net": giris_net,
            "cikis_net": cikis_net,
            "sonuc": sonuc,
            "net_getiri_pct": net_getiri,
            "gun": gun,
        })

        i += max(gun, 1)  # üst üste binmeyi önle

    return islemler


# ─────────────────────────────────────────────────────────────────────────
# Portföy simülasyonu: tüm hisselerin işlemlerini tek sermayede birleştir
#  - max_pozisyon kadar eşzamanlı işlem
#  - her pozisyon: o anki toplam özsermaye / max_pozisyon kadar tahsis (bileşik)
#  - günlük MTM (mark-to-market) ile gerçek equity eğrisi
# ─────────────────────────────────────────────────────────────────────────
def _portfoy_simulasyon(tum_islemler, kapanis_ff, takvim):
    sermaye0 = CONFIG["baslangic_sermaye"]
    maxp = CONFIG["max_pozisyon"]

    # Girişe göre sırala
    bekleyen = sorted(tum_islemler, key=lambda x: x["giris_tarih"])
    bi = 0
    acik = []   # {kod, giris_tarih, cikis_tarih, giris_net, cikis_net, lot}
    nakit = sermaye0
    equity_seri = []

    def _mtm(tarih):
        deger = nakit
        for p in acik:
            px = kapanis_ff[p["kod"]].get(tarih, p["giris_net"])
            deger += p["lot"] * px
        return deger

    for tarih in takvim:
        # 1) Bugün kapanacak pozisyonları kapat
        kalan = []
        for p in acik:
            if p["cikis_tarih"] == tarih:
                nakit += p["lot"] * p["cikis_net"]   # net çıkış
            else:
                kalan.append(p)
        acik = kalan

        # 2) Bugün girişi olan yeni işlemleri aç (slot varsa)
        while bi < len(bekleyen) and bekleyen[bi]["giris_tarih"] == tarih:
            islem = bekleyen[bi]
            bi += 1
            if len(acik) >= maxp:
                continue
            ozsermaye = _mtm(tarih)
            tahsis = min(ozsermaye / maxp, nakit)
            if tahsis <= 0:
                continue
            lot = tahsis / islem["giris_net"]   # kesirli "lot" (TL/birim fiyat)
            nakit -= tahsis
            acik.append({
                "kod": islem["kod"],
                "giris_tarih": islem["giris_tarih"],
                "cikis_tarih": islem["cikis_tarih"],
                "giris_net": islem["giris_net"],
                "cikis_net": islem["cikis_net"],
                "lot": lot,
            })

        equity_seri.append((tarih, _mtm(tarih)))

    return pd.Series(dict(equity_seri)).sort_index()


# ─────────────────────────────────────────────────────────────────────────
# Metrikler
# ─────────────────────────────────────────────────────────────────────────
def _metrikler(equity, islemler, gun_sayisi):
    e = equity.values.astype(float)
    if len(e) < 2:
        return None
    toplam_getiri = e[-1] / e[0] - 1
    yil = gun_sayisi / 252.0
    cagr = (e[-1] / e[0]) ** (1 / yil) - 1 if yil > 0 else 0.0

    # Max drawdown
    zirve = np.maximum.accumulate(e)
    dd = (e - zirve) / zirve
    max_dd = float(dd.min())

    # Günlük getiriler
    g = np.diff(e) / e[:-1]
    rf_gunluk = (1 + CONFIG["mevduat_yillik"]) ** (1 / 252) - 1
    fazla = g - rf_gunluk
    sharpe = (np.mean(fazla) / (np.std(g) + 1e-12)) * np.sqrt(252) if np.std(g) > 0 else 0.0
    dusuk = g[g < 0]
    sortino = (np.mean(fazla) / (np.std(dusuk) + 1e-12)) * np.sqrt(252) if len(dusuk) > 0 else 0.0

    kazanan = [x for x in islemler if x["net_getiri_pct"] > 0]
    basari = len(kazanan) / len(islemler) * 100 if islemler else 0
    ort_kazanc = np.mean([x["net_getiri_pct"] for x in kazanan]) if kazanan else 0
    kaybeden = [x for x in islemler if x["net_getiri_pct"] <= 0]
    ort_kayip = np.mean([x["net_getiri_pct"] for x in kaybeden]) if kaybeden else 0

    # Mevduat: aynı süre, sıfır drawdown
    mevduat_son = e[0] * (1 + CONFIG["mevduat_yillik"]) ** yil
    mevduat_getiri = mevduat_son / e[0] - 1

    return {
        "toplam_getiri": toplam_getiri, "cagr": cagr, "max_dd": max_dd,
        "sharpe": sharpe, "sortino": sortino,
        "islem": len(islemler), "basari_pct": basari,
        "ort_kazanc": ort_kazanc, "ort_kayip": ort_kayip,
        "son_equity": e[-1], "mevduat_getiri": mevduat_getiri, "mevduat_son": mevduat_son,
        "yil": yil,
    }


# ─────────────────────────────────────────────────────────────────────────
# ANA AKIŞ
# ─────────────────────────────────────────────────────────────────────────
def main():
    ayar = VADE_AYAR.get(CONFIG["vade"], VADE_AYAR["haftalik"])
    hisseler = CONFIG["hisseler"] or tc.BIST_TUM
    print("═" * 60)
    print(f"APEX BACKTEST v2 — vade={CONFIG['vade']}  hisse={len(hisseler)}  "
          f"ML={'AÇIK' if AI else 'kapalı'}")
    print(f"maliyet: %{CONFIG['komisyon_pct']}+%{CONFIG['slippage_pct']}/yön  "
          f"mevduat kıyas: %{CONFIG['mevduat_yillik']*100:.0f}")
    print("═" * 60)

    tum_islemler = []
    kapanis_ff = {}
    tarih_set = set()
    basarili_veri = 0

    for idx, kod in enumerate(hisseler, 1):
        try:
            df, durum = veri_al(kod, gun=CONFIG["gun"], min_gun=ayar["min_gun"], aralik=ayar["aralik"])
        except Exception as e:
            print(f"  [{idx}/{len(hisseler)}] {kod}: veri hatası ({type(e).__name__})")
            continue
        if df is None or len(df) < ayar["min_gun"] + 5:
            print(f"  [{idx}/{len(hisseler)}] {kod}: yetersiz veri ({durum})")
            continue

        basarili_veri += 1
        isl = _hisse_islemleri(kod, df, ayar)
        tum_islemler.extend(isl)
        kapanis_ff[kod] = df["Close"]
        tarih_set.update(df.index.tolist())
        print(f"  [{idx}/{len(hisseler)}] {kod}: {len(df)} bar, {len(isl)} işlem")

    if not tum_islemler:
        print("\n⚠ HİÇ İŞLEM ÜRETİLMEDİ. Veri çekilemedi ya da sinyal koşulları çok sıkı.")
        print("  Öneri: CONFIG['hisseler'] ile birkaç likit hisse dene, internet bağlantını kontrol et.")
        return

    # Ortak takvim + forward-fill kapanışlar (MTM için)
    takvim = sorted(tarih_set)
    for kod in kapanis_ff:
        kapanis_ff[kod] = kapanis_ff[kod].reindex(takvim, method="ffill")

    equity = _portfoy_simulasyon(tum_islemler, kapanis_ff, takvim)
    m = _metrikler(equity, tum_islemler, len(takvim))
    if m is None:
        print("Metrik hesaplanamadı (equity çok kısa).")
        return

    # ── RAPOR ──
    print("\n" + "═" * 60)
    print("SONUÇ")
    print("═" * 60)
    print(f"  Veri çekilen hisse   : {basarili_veri}/{len(hisseler)}")
    print(f"  Toplam işlem         : {m['islem']}")
    print(f"  Test süresi          : {m['yil']:.2f} yıl")
    print(f"  Başlangıç sermaye    : {CONFIG['baslangic_sermaye']:,.0f} TL")
    print(f"  Bitiş sermaye        : {m['son_equity']:,.0f} TL")
    print("  " + "-" * 56)
    print(f"  Toplam getiri        : {m['toplam_getiri']*100:>8.2f} %")
    print(f"  Yıllık (CAGR)        : {m['cagr']*100:>8.2f} %")
    print(f"  Max Drawdown         : {m['max_dd']*100:>8.2f} %   <-- en kötü düşüş")
    print(f"  Sharpe (mevduata göre): {m['sharpe']:>7.2f}   <-- >1 iyi, <0 kötü")
    print(f"  Sortino              : {m['sortino']:>8.2f}")
    print(f"  Başarı oranı         : {m['basari_pct']:>8.1f} %")
    print(f"  Ort. kazanç/kayıp    : +{m['ort_kazanc']:.2f}% / {m['ort_kayip']:.2f}%")
    print("  " + "-" * 56)
    print(f"  MEVDUAT (aynı süre)  : {m['mevduat_getiri']*100:>8.2f} %  → {m['mevduat_son']:,.0f} TL")
    print("  " + "-" * 56)

    # Dürüst hüküm
    fark = m["toplam_getiri"] - m["mevduat_getiri"]
    if m["sharpe"] < 0:
        hukum = "KÖTÜ: Sistem mevduatın çok altında, risk boşa alınmış."
    elif fark <= 0:
        hukum = "MEVDUAT DAHA İYİ: Getiri mevduatı geçmiyor — bu haliyle oynama."
    elif m["sharpe"] < 1:
        hukum = "ZAYIF EDGE: Mevduatı geçiyor ama risk/getiri zayıf (Sharpe<1)."
    else:
        hukum = "UMUT VAR: Riske göre mevduatı geçiyor. Daha uzun veri + ileri test şart."
    print(f"  HÜKÜM: {hukum}")
    print("═" * 60)

    # İşlemleri CSV'ye yaz
    try:
        pd.DataFrame(tum_islemler).to_csv("backtest_islemler.csv", index=False, encoding="utf-8-sig")
        equity.to_csv("backtest_equity.csv", encoding="utf-8-sig")
        print("Detay kaydedildi: backtest_islemler.csv  +  backtest_equity.csv")
    except Exception as e:
        print("CSV yazılamadı:", e)


if __name__ == "__main__":
    main()
