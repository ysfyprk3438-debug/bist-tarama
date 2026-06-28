# baglam_motor.py — APEX bağlam katmanı: hareket eden hisseleri KAP ile eşleştir
# Projektör yol haritası 1. tuğlası (CLAUDE.md §7). Deterministik, LLM yok.
#
# DÜRÜST SINIR (CLAUDE.md §5):
#   KAP erişilemezse kap_durum="kapali" döner; hareketli hisselere "sebepsiz"
#   damgası vurulmaz (yanlış spekülatif uyarı olur). Sahte veri üretilmez.
#   fetch_bist() boş dönerse kayitlar=[] ve kısa uyarı; çökme olmaz.

from datetime import date

from app import fetch_bist, BIST
from kap_oku import kap_eslesir


def topla(esik=3.0, gun=2):
    """Günün hareket eden hisselerini KAP açıklamalarıyla eşleştirir.

    Dönüş: dict
      {
        "tarih": "YYYY-MM-DD",
        "kap_durum": "acik" | "kapali",
        "esik": 3.0,
        "kayitlar": [
          {"tk","nm","ch","hareketli":bool,"kap_var":bool,"kap_n":int,
           "aciklamalar":[{"tarih","konu","link"}...],
           "sinif":"sebepli|sebepsiz|aciklama_tepkisiz|sakin|kap_kapali"}
          ...   # |ch| büyükten küçüğe sıralı
        ]
      }

    Sınıf tanımları:
      sebepli           — hareketli (|ch| >= esik) VE KAP'ta açıklama var
      sebepsiz          — hareketli ama KAP'ta açıklama yok (KAP erişilebilir)
      aciklama_tepkisiz — KAP'ta açıklama var ama fiyat hareketsiz
      sakin             — hareket yok, açıklama yok
      kap_kapali        — hareketli ama KAP erişilemedi; "sebepsiz" damgası VURULMAZ
    """
    # 1. Fiyat verisini çek
    fiyatlar = fetch_bist()
    if not fiyatlar:
        print("UYARI: fetch_bist() bos dondu — yfinance/internet yok veya veri eksik.")
        return {
            "tarih": date.today().isoformat(),
            "kap_durum": "kapali",
            "esik": esik,
            "kayitlar": [],
        }

    # Ad (nm) için BIST listesinden sözlük
    bist_ad = {sym: ad for sym, ad in BIST}

    # 2. KAP açıklamalarını çek (sadece fiyat verisi olan semboller için)
    semboller = [sym for sym, _ in BIST if sym in fiyatlar]
    kap = kap_eslesir(semboller, gun=gun)
    kap_durum = kap.get("_durum", "kapali")
    kap_acik = (kap_durum == "acik")

    # 3. Her hisse için kayıt oluştur
    kayitlar = []
    for sym in semboller:
        veri = fiyatlar.get(sym)
        if veri is None:
            continue
        ch = veri.get("ch", 0.0) or 0.0
        hareketli = abs(ch) >= esik

        # KAP açıklamaları — KAP kapalıysa boş liste (sahte veri üretme)
        ham_aciklamalar = kap.get(sym, []) if kap_acik else []
        aciklamalar = [
            {
                "tarih": a.get("tarih", ""),
                "konu": a.get("konu", ""),
                "link": a.get("link", ""),
            }
            for a in ham_aciklamalar
        ]
        kap_var = bool(aciklamalar)
        kap_n = len(aciklamalar)

        # Sınıf belirleme
        if not kap_acik and hareketli:
            # KAP erişilemedi; yanlış "sebepsiz" damgası vurma
            sinif = "kap_kapali"
        elif hareketli and kap_var:
            sinif = "sebepli"
        elif hareketli and not kap_var:
            sinif = "sebepsiz"
        elif not hareketli and kap_var:
            sinif = "aciklama_tepkisiz"
        else:
            sinif = "sakin"

        kayitlar.append({
            "tk": sym,
            "nm": bist_ad.get(sym, sym),
            "ch": ch,
            "hareketli": hareketli,
            "kap_var": kap_var,
            "kap_n": kap_n,
            "aciklamalar": aciklamalar,
            "sinif": sinif,
        })

    # |ch|'ye göre büyükten küçüğe sırala
    kayitlar.sort(key=lambda r: abs(r["ch"]), reverse=True)

    return {
        "tarih": date.today().isoformat(),
        "kap_durum": kap_durum,
        "esik": esik,
        "kayitlar": kayitlar,
    }


if __name__ == "__main__":
    import json as _json
    from datetime import datetime

    print("baglam_motor tani calisiyor (esik=%%3.0, gun=2)...\n")
    sonuc = topla(esik=3.0, gun=2)
    kayitlar = sonuc["kayitlar"]

    # Özet sayaçlar
    hareketli_n = sum(1 for r in kayitlar if r["hareketli"])
    sinif_say = {}
    for r in kayitlar:
        sinif_say[r["sinif"]] = sinif_say.get(r["sinif"], 0) + 1

    print(f"  tarih       : {sonuc['tarih']}")
    print(f"  kap_durum   : {sonuc['kap_durum']}")
    print(f"  esik        : +/-%%{sonuc['esik']}")
    print(f"  toplam hisse: {len(kayitlar)}")
    print(f"  hareketli   : {hareketli_n}")
    print("  sinif dagilimi:")
    for sinif, say in sorted(sinif_say.items()):
        print(f"    {sinif:<22}: {say}")

    print("\nIlk 5 kayit (|ch| buyukten kucuge):")
    for r in kayitlar[:5]:
        konu = r["aciklamalar"][0]["konu"][:40] if r["aciklamalar"] else "—"
        print(f"  {r['tk']:<8}  %{r['ch']:+.1f}  {r['sinif']:<22}  {konu}")

    # Opsiyonel: denetim/sonraki tugla icin JSON'a yaz
    cikti_dosya = "baglam_gunluk.json"
    cikti = {
        "guncelleme": datetime.now().isoformat(timespec="seconds"),
        "tarih": sonuc["tarih"],
        "kap_durum": sonuc["kap_durum"],
        "esik": sonuc["esik"],
        "kayitlar": sonuc["kayitlar"],
    }
    try:
        with open(cikti_dosya, "w", encoding="utf-8") as f:
            _json.dump(cikti, f, ensure_ascii=False, indent=2)
        print(f"\nDenetim dosyasi yazildi: {cikti_dosya}")
    except Exception as e:
        print(f"\nUYARI: {cikti_dosya} yazılamadi: {e}")
