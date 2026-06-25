"""
═══════════════════════════════════════════════════════════════
ROBOT SİMÜLATÖRÜ — BIST Para Avcısı v4
═══════════════════════════════════════════════════════════════
Sanal parayla otomatik al-sat. Robotlaştırmadan önceki güvenli prototip.

İki mod:
- "disiplinli": risk kuralı + max kadro + dinamik rotasyon + oto çıkış
- "basit": çıkan her sinyali al, hedef/stopta sat

Çalışma:
- simulasyon_kostur(): geçmiş veride gün gün koştur → "ne kazandırdı"
- canli_adim(): mevcut taramaya göre tek karar turu (canlı mod)

Dinamik rotasyon (kullanıcının fikri):
Portföy hep "o anın en iyi N hissesi" olur. Eldeki zayıflarsa ve
dışarıda belirgin daha iyi aday varsa → takas. Gereksiz takas için
eşik var (komisyon yememek için).
"""

import datetime


ROBOT_VARSAYILAN = {
    "mod": "disiplinli",      # "disiplinli" | "basit"
    "max_pozisyon": 15,       # hedef kadro
    "min_puan": 50,           # bu puanın altını alma
    "rotasyon_esigi": 10,     # yeni aday, en zayıf pozisyondan bu kadar iyiyse takas
    "pozisyon_risk": 0.02,    # disiplinli modda pozisyon başına portföy %2
    "cooldown_tur": 3,        # satılan hisse bu kadar tur tekrar alınmaz (komisyon koruması)
}


def _poz_buyuklugu(mod, nakit, toplam_deger, fiyat, stop, ayar, bos_slot):
    """Bir alım için kaç lot? Moda göre."""
    if mod == "disiplinli" and stop and stop < fiyat:
        # Risk tabanlı: portföyün %2'sini riske et
        risk_tl = toplam_deger * ayar["pozisyon_risk"]
        hisse_risk = fiyat - stop
        lot = int(risk_tl / hisse_risk) if hisse_risk > 0 else 0
        # Nakdi aşmasın
        max_lot_nakit = int(nakit / fiyat) if fiyat > 0 else 0
        return max(0, min(lot, max_lot_nakit))
    else:
        # Basit mod: boş slot başına eşit nakit dağıt
        if bos_slot <= 0 or fiyat <= 0:
            return 0
        pay = nakit / bos_slot
        return int(pay / fiyat)


def canli_adim(cuzdan, sonuclar, guncel_fiyatlar, ayar, cz, cooldown=None, fren=None):
    """
    Tek karar turu (canlı mod). Mevcut taramaya göre:
    1. Açık pozisyonları kontrol et: hedef/stop değdi mi? → sat
    2. Dinamik rotasyon: zayıf pozisyonu güçlü adayla değiştir
    3. Boş slot varsa en iyi adayları al (cooldown'dakiler hariç)

    cooldown: {kod: kalan_tur} sözlüğü.
    fren: piyasa.piyasa_rejimi_freni çıktısı — piyasa kötüyse robot savunmaya geçer
          (alım eşiği yükselir, pozisyon/slot sayısı azalır). None ise fren yok.
    Dönen: yapılan işlemlerin metin listesi
    """
    olaylar = []
    mod = ayar["mod"]
    maxp = ayar["max_pozisyon"]
    cd_tur = ayar.get("cooldown_tur", 0)
    if cooldown is None:
        cooldown = {}

    # Piyasa rejimi freni: kötü piyasada eşik yükselir, slot sayısı azalır
    min_puan_etkin = ayar["min_puan"]
    if fren:
        min_puan_etkin = ayar["min_puan"] + fren.get("min_skor_ek", 0)
        maxp = max(1, int(round(maxp * fren.get("maxpoz_carpani", 1.0))))
        if olaylar is not None and fren.get("mod", "").startswith("RISK-OFF"):
            olaylar.append(f"🛡️ {fren['mod']}: robot savunmada, alım eşiği yükseldi")

    # Tur başında cooldown sayaçlarını azalt
    for kod in list(cooldown.keys()):
        cooldown[kod] -= 1
        if cooldown[kod] <= 0:
            del cooldown[kod]

    def _sat(kod, fiyat):
        """Satış yap ve cooldown'a ekle."""
        ok, msg = cz.satis_yap(cuzdan, kod, fiyat)
        if ok and cd_tur > 0:
            cooldown[kod] = cd_tur
        return ok, msg

    # Sonuçları puana göre sırala, sözlüğe çevir (etkin eşik = fren uygulanmış)
    aday = {r["kod"]: r for r in sonuclar if r["puan"] >= min_puan_etkin}
    sirali = sorted(aday.values(), key=lambda x: x["puan"], reverse=True)

    # ── 1. ÇIKIŞ KONTROLÜ (hedef/stop) ──
    for kod in list(cuzdan["pozisyonlar"].keys()):
        poz = cuzdan["pozisyonlar"][kod]
        fiyat = guncel_fiyatlar.get(kod)
        if fiyat is None:
            continue
        if poz.get("hedef") and fiyat >= poz["hedef"]:
            ok, msg = _sat(kod, fiyat)
            if ok: olaylar.append(f"🟢 HEDEF: {msg}")
        elif poz.get("stop") and fiyat <= poz["stop"]:
            ok, msg = _sat(kod, fiyat)
            if ok: olaylar.append(f"🔴 STOP: {msg}")

    # ── 2. DİNAMİK ROTASYON (disiplinli modda) ──
    if mod == "disiplinli" and len(cuzdan["pozisyonlar"]) >= maxp:
        elde_puan = {}
        for kod in cuzdan["pozisyonlar"]:
            elde_puan[kod] = aday[kod]["puan"] if kod in aday else 0
        if elde_puan:
            en_zayif_kod = min(elde_puan, key=elde_puan.get)
            en_zayif_puan = elde_puan[en_zayif_kod]
            # Portföyde olmayan VE cooldown'da olmayan en iyi aday
            dis_adaylar = [r for r in sirali
                           if r["kod"] not in cuzdan["pozisyonlar"] and r["kod"] not in cooldown]
            if dis_adaylar:
                en_iyi_dis = dis_adaylar[0]
                if en_iyi_dis["puan"] - en_zayif_puan >= ayar["rotasyon_esigi"]:
                    f = guncel_fiyatlar.get(en_zayif_kod)
                    if f:
                        ok, msg = _sat(en_zayif_kod, f)
                        if ok: olaylar.append(f"🔄 ROTASYON-SAT: {msg} (puan {en_zayif_puan})")

    # ── 3. BOŞ SLOTLARI DOLDUR (cooldown'dakiler hariç) ──
    bos = maxp - len(cuzdan["pozisyonlar"])
    if bos > 0:
        ozet = cz.portfoy_degeri(cuzdan, guncel_fiyatlar)
        for r in sirali:
            if bos <= 0:
                break
            if r["kod"] in cuzdan["pozisyonlar"]:
                continue
            if r["kod"] in cooldown:
                continue  # soğuma süresinde, alma
            fiyat = guncel_fiyatlar.get(r["kod"], r["son"])
            lot = _poz_buyuklugu(mod, cuzdan["nakit"], ozet["toplam"], fiyat, r.get("stop"), ayar, bos)
            if lot > 0:
                ok, msg = cz.alis_yap(cuzdan, r["kod"], fiyat, lot, r.get("hedef"), r.get("stop"))
                if ok:
                    olaylar.append(f"🛒 AL: {msg} (puan {r['puan']})")
                    bos -= 1

    if not olaylar:
        olaylar.append("Bu turda işlem yok (kadro dolu, rotasyon eşiği aşılmadı).")
    return olaylar


def simulasyon_kostur(tarihsel_sinyaller, ayar, cz, baslangic_bakiye, komisyon=0.002):
    """
    Geçmiş sinyallerle robotu gün gün koştur.
    tarihsel_sinyaller: [{tarih, sonuclar:[...], fiyatlar:{...}}] (kronolojik)
    Dönen: simülasyon özeti

    NOT: Bu fonksiyon tarihsel veri hazırlandığında app tarafından beslenir.
    Burada robotun gün gün nasıl davrandığını simüle eder.
    """
    cuzdan = cz.cuzdan_olustur(baslangic_bakiye)
    cuzdan["komisyon_oran"] = komisyon
    gunluk_deger = []
    cooldown = {}  # turlar arası taşınır

    for gun in tarihsel_sinyaller:
        canli_adim(cuzdan, gun["sonuclar"], gun["fiyatlar"], ayar, cz, cooldown)
        ozet = cz.portfoy_degeri(cuzdan, gun["fiyatlar"])
        gunluk_deger.append({"tarih": gun["tarih"], "deger": ozet["toplam"]})

    son_ozet = cz.portfoy_degeri(cuzdan, tarihsel_sinyaller[-1]["fiyatlar"] if tarihsel_sinyaller else {})
    satislar = [i for i in cuzdan["islemler"] if i["tip"] == "SATIŞ"]
    kazanan = len([i for i in satislar if (i.get("kar_zarar", 0) or 0) > 0])

    return {
        "baslangic": baslangic_bakiye,
        "son_deger": son_ozet["toplam"],
        "toplam_getiri_pct": son_ozet["toplam_kar_pct"],
        "islem_sayisi": len(cuzdan["islemler"]),
        "satis_sayisi": len(satislar),
        "kazanan": kazanan,
        "basari_pct": (kazanan / len(satislar) * 100) if satislar else 0,
        "gunluk_deger": gunluk_deger,
        "acik_pozisyon": len(cuzdan["pozisyonlar"]),
    }
