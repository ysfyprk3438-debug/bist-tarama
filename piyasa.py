"""
═══════════════════════════════════════════════════════════════
PİYASANIN DOKUSU — BIST Para Avcısı v4 (Katman 2)
═══════════════════════════════════════════════════════════════
Tek hisseden sermayenin haritasına. Büyük para tek hisse seçmez,
paranın aktığı yönü okur.

İki ana yetenek:
  1. YIĞILMA UYARISI: portföy tek bir bahse mi yığıldı?
     (15 hissenin 8'i bankaysa, aslında tek bahse 8 kez girilmiş —
      banka düşerse hepsi düşer. Gerçek risk yönetiminin kalbi.)
  2. SEKTÖR ROTASYONU: para hangi sektörden çıkıp hangisine giriyor?
     ('Bankalar zirve yaptı, para enerjiye dönüyor, lideri şu hisse.')
"""

import numpy as np


# ══════════════════════════════════════════════════════════════
# YIĞILMA / KONSANTRASYON UYARISI
# ══════════════════════════════════════════════════════════════
def yigilma_analiz(pozisyonlar, kod_sektor):
    """
    Bir portföyün sektör dağılımını ve yığılma riskini ölçer.
    pozisyonlar: [{kod, deger}] veya [{kod, pozisyon_tl}] veya sadece [kod...]
    kod_sektor: {kod: sektor} haritası

    Dönen: {dagilim, en_yuksek_sektor, en_yuksek_pct, risk_seviye, uyari, mesaj}
    """
    if not pozisyonlar:
        return None

    # Pozisyonları normalize et (değer varsa değere göre, yoksa eşit ağırlık)
    sektor_deger = {}
    toplam = 0.0
    for p in pozisyonlar:
        if isinstance(p, dict):
            kod = p.get("kod")
            deger = p.get("deger") or p.get("pozisyon_tl") or 1.0
        else:
            kod = p
            deger = 1.0
        sek = kod_sektor.get(kod, "Diğer")
        sektor_deger[sek] = sektor_deger.get(sek, 0) + deger
        toplam += deger

    if toplam <= 0:
        return None

    # Yüzde dağılım
    dagilim = [(sek, deg, deg / toplam * 100) for sek, deg in sektor_deger.items()]
    dagilim.sort(key=lambda x: x[2], reverse=True)

    en_yuksek_sek, _, en_yuksek_pct = dagilim[0]

    # Herfindahl benzeri konsantrasyon (0-100, yüksek = riskli)
    konsantrasyon = sum((pct / 100) ** 2 for _, _, pct in dagilim) * 100

    # Risk seviyesi
    if en_yuksek_pct >= 50:
        risk, uyari = "YÜKSEK", True
        mesaj = f"Portföyün %{en_yuksek_pct:.0f}'i {en_yuksek_sek} sektöründe. Bu tek bir bahis — sektör düşerse hepsi birlikte düşer. Dağıt."
    elif en_yuksek_pct >= 35:
        risk, uyari = "ORTA", True
        mesaj = f"{en_yuksek_sek} ağırlığı %{en_yuksek_pct:.0f} — biraz yüksek. Çeşitlendirmeyi düşün."
    else:
        risk, uyari = "DÜŞÜK", False
        mesaj = f"Sektör dağılımı dengeli (en yüksek {en_yuksek_sek} %{en_yuksek_pct:.0f})."

    return {
        "dagilim": dagilim,
        "en_yuksek_sektor": en_yuksek_sek,
        "en_yuksek_pct": en_yuksek_pct,
        "konsantrasyon": konsantrasyon,
        "risk_seviye": risk,
        "uyari": uyari,
        "mesaj": mesaj,
        "sektor_sayisi": len(dagilim),
    }


# ══════════════════════════════════════════════════════════════
# SEKTÖR ROTASYONU — para nereden nereye akıyor
# ══════════════════════════════════════════════════════════════
def sektor_rotasyon(sonuclar):
    """
    Tarama sonuçlarından sektörel para akışını ve momentum yönünü çıkarır.
    Her sektör için: ortalama dönem getirisi (momentum) + akıllı para + fırsat yoğunluğu.

    'Para giren' sektör: yüksek momentum + güçlü akıllı para + çok fırsat.
    'Para çıkan' sektör: düşük/negatif momentum.

    Dönen: {giren: [...], cikan: [...], liderler: {sektor: lider_hisse}}
    """
    if not sonuclar:
        return None

    sektor_veri = {}
    for r in sonuclar:
        sek = r["sektor"]
        if sek not in sektor_veri:
            sektor_veri[sek] = {
                "momentum": [], "ap": [], "adet": 0,
                "en_iyi_hisse": None, "en_iyi_puan": -1,
            }
        s = sektor_veri[sek]
        s["momentum"].append(r.get("donem_getiri", 0))
        s["ap"].append(r["sm"]["skor"])
        s["adet"] += 1
        if r["puan"] > s["en_iyi_puan"]:
            s["en_iyi_puan"] = r["puan"]
            s["en_iyi_hisse"] = r["kod"]

    # Sektör akış skoru
    liste = []
    for sek, s in sektor_veri.items():
        ort_mom = float(np.mean(s["momentum"]))
        ort_ap = float(np.mean(s["ap"]))
        # Akış skoru: momentum (para yönü) + akıllı para + fırsat yoğunluğu
        akis = ort_mom * 1.5 + (ort_ap - 50) * 0.8 + s["adet"] * 2
        liste.append({
            "sektor": sek,
            "momentum": ort_mom,
            "ort_ap": ort_ap,
            "adet": s["adet"],
            "akis": akis,
            "lider": s["en_iyi_hisse"],
            "lider_puan": s["en_iyi_puan"],
        })

    liste.sort(key=lambda x: x["akis"], reverse=True)

    # Para giren (üst) ve çıkan (alt) sektörler
    giren = [x for x in liste if x["akis"] > 0 and x["momentum"] > 0][:3]
    cikan = [x for x in liste if x["akis"] < 0][-3:]

    return {
        "tum": liste,
        "giren": giren,
        "cikan": cikan,
        "en_guclu": liste[0] if liste else None,
        "en_zayif": liste[-1] if liste else None,
    }


def rotasyon_yorum(rotasyon):
    """Sektör rotasyonunu insan diline çevirir."""
    if not rotasyon or not rotasyon["giren"]:
        return "Belirgin sektör rotasyonu yok."
    en_guclu = rotasyon["giren"][0]
    yorum = f"Para en çok {en_guclu['sektor']} sektörüne akıyor"
    if en_guclu["lider"]:
        yorum += f" (lider: {en_guclu['lider']}, puan {en_guclu['lider_puan']})"
    if rotasyon["cikan"]:
        en_zayif = rotasyon["en_zayif"]
        yorum += f". {en_zayif['sektor']} zayıflıyor."
    return yorum


# ══════════════════════════════════════════════════════════════
# KORELASYON — hangi hisseler birlikte hareket ediyor
# ══════════════════════════════════════════════════════════════
def korelasyon_grubu(fiyat_serileri, esik=0.7):
    """
    Hisselerin getiri korelasyonunu hesaplar, yüksek korele grupları bulur.
    fiyat_serileri: {kod: pandas.Series (kapanış)}

    Yüksek korelasyon = birlikte hareket = aynı riski paylaşıyor.
    Dönen: yüksek korele hisse çiftleri
    """
    import pandas as pd
    kodlar = list(fiyat_serileri.keys())
    if len(kodlar) < 2:
        return []

    # Getirilere çevir, ortak tarihlerde hizala
    getiriler = {}
    for kod, seri in fiyat_serileri.items():
        getiriler[kod] = seri.pct_change().dropna()

    df = pd.DataFrame(getiriler).dropna()
    if len(df) < 10:
        return []

    korr = df.corr()
    ciftler = []
    for i in range(len(kodlar)):
        for j in range(i + 1, len(kodlar)):
            k1, k2 = kodlar[i], kodlar[j]
            if k1 in korr.index and k2 in korr.columns:
                deger = korr.loc[k1, k2]
                if not np.isnan(deger) and abs(deger) >= esik:
                    ciftler.append({"hisse1": k1, "hisse2": k2, "korelasyon": float(deger)})

    ciftler.sort(key=lambda x: abs(x["korelasyon"]), reverse=True)
    return ciftler


# ══════════════════════════════════════════════════════════════
# PİYASA REJİMİ FRENİ — robotun "risk-off" modu
# ══════════════════════════════════════════════════════════════
def piyasa_rejimi_freni(rejim, xu100_pct, endeks_vol_rejim=None):
    """
    Piyasanın genel havasına göre robotun risk iştahını ayarlar.
    "Borsa çökerken iştahla alma — akıntıya karşı kürek çekme."

    rejim: piyasa_durumu rejim metni ("YÜKSELİŞ TRENDİ" vs)
    xu100_pct: endeksin dönemsel değişimi (%)
    endeks_vol_rejim: endeksin volatilite rejimi ("FIRTINA" vs, opsiyonel)

    Dönen: {mod, min_skor_ek, poz_carpani, maxpoz_carpani, renk, mesaj}
      min_skor_ek: alım eşiğine eklenecek puan (kötü piyasada yükselir)
      poz_carpani: pozisyon boyutu çarpanı
      maxpoz_carpani: maksimum pozisyon sayısı çarpanı
    """
    dususte = "DÜŞÜŞ" in (rejim or "")
    yuksekte = "YÜKSELİŞ" in (rejim or "")
    firtina = endeks_vol_rejim == "FIRTINA"

    # Risk-off: düşüş trendi VEYA fırtına + negatif endeks
    if dususte or (firtina and xu100_pct < 0):
        return {
            "mod": "RISK-OFF (Savunma)",
            "min_skor_ek": 20,      # alım eşiği +20 (sadece çok güçlüleri al)
            "poz_carpani": 0.5,     # pozisyonları yarıya indir
            "maxpoz_carpani": 0.5,  # slot sayısını yarıya indir
            "renk": "#EF4444",
            "mesaj": "Piyasa düşüşte/fırtınalı — robot savunmada. Sadece en güçlü sinyaller, küçük pozisyon. Nakitte kal.",
        }
    # Temkinli: yatay VEYA fırtına (ama endeks negatif değil)
    elif firtina or (not yuksekte and not dususte):
        return {
            "mod": "TEMKİNLİ",
            "min_skor_ek": 10,
            "poz_carpani": 0.75,
            "maxpoz_carpani": 0.75,
            "renk": "#F59E0B",
            "mesaj": "Piyasa kararsız/oynak — robot temkinli. Eşik yükseldi, pozisyonlar küçüldü.",
        }
    # Risk-on: yükseliş trendi, sakin
    else:
        return {
            "mod": "RISK-ON (Normal)",
            "min_skor_ek": 0,
            "poz_carpani": 1.0,
            "maxpoz_carpani": 1.0,
            "renk": "#10B981",
            "mesaj": "Piyasa elverişli — robot normal iştahla çalışıyor.",
        }


# ══════════════════════════════════════════════════════════════
# ÇEŞİTLENDİRME KONTROLÜ — sahte çeşitlendirme tuzağını yakalar
# ══════════════════════════════════════════════════════════════
def cesitlendirme_kontrol(sonuclar, esik=0.75, max_hisse=14):
    """
    Aday hisselerin gerçekten bağımsız mı yoksa birlikte mi hareket
    ettiğini bulur. "Sahte çeşitlendirme" tuzağını yakalar:
    3 fırsat al ama üçü de aynı yönde oynuyorsa = tek bahsi 3'e katlamak.

    sonuclar: df_grafik içeren analiz sonuçları (en iyiler)
    esik: korelasyon eşiği (>0.75 = birlikte hareket ediyor)
    Dönen: {kumeler, uyari, mesaj} veya None
    """
    import pandas as pd

    # df_grafik olan en iyi adayları al
    adaylar = [r for r in sonuclar if r.get("df_grafik") is not None][:max_hisse]
    if len(adaylar) < 2:
        return None

    # Ortak tarihli kapanış DataFrame'i kur
    seriler = {}
    for r in adaylar:
        try:
            seriler[r["kod"]] = r["df_grafik"]["Close"]
        except Exception:
            continue
    if len(seriler) < 2:
        return None

    getiriler = {}
    for kod, seri in seriler.items():
        getiriler[kod] = seri.pct_change()
    df = pd.DataFrame(getiriler).dropna()
    if len(df) < 15:
        return None

    korr = df.corr()
    kodlar = list(df.columns)

    # Union-Find ile yüksek korele hisseleri kümele
    ebeveyn = {k: k for k in kodlar}
    def bul(x):
        while ebeveyn[x] != x:
            ebeveyn[x] = ebeveyn[ebeveyn[x]]
            x = ebeveyn[x]
        return x
    def birlestir(a, b):
        ra, rb = bul(a), bul(b)
        if ra != rb:
            ebeveyn[ra] = rb

    for i in range(len(kodlar)):
        for j in range(i + 1, len(kodlar)):
            k1, k2 = kodlar[i], kodlar[j]
            deger = korr.loc[k1, k2]
            if not pd.isna(deger) and deger >= esik:
                birlestir(k1, k2)

    # Kümeleri topla
    kume_map = {}
    for k in kodlar:
        kok = bul(k)
        kume_map.setdefault(kok, []).append(k)

    # 2+ üyeli kümeler = birlikte hareket eden gruplar
    kumeler = [uyeler for uyeler in kume_map.values() if len(uyeler) >= 2]

    if not kumeler:
        return {
            "kumeler": [], "uyari": False,
            "mesaj": "Adaylar birbirinden bağımsız hareket ediyor — gerçek çeşitlendirme mümkün.",
        }

    # Sektör bilgisini ekle (genelde aynı sektör çıkar)
    kod_sektor = {r["kod"]: r.get("sektor", "") for r in adaylar}
    detay = []
    for kume in kumeler:
        sektorler = set(kod_sektor.get(k, "") for k in kume)
        detay.append({"hisseler": kume, "sektor": list(sektorler)[0] if len(sektorler) == 1 else "karışık"})

    return {
        "kumeler": detay,
        "uyari": True,
        "mesaj": f"{len(kumeler)} grup birlikte hareket ediyor — her gruptan BİR hisse yeterli, hepsini almak riski yığar.",
    }
