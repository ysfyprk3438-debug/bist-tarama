# hikaye_motor.py — KAP açıklamalarını sade Türkçeye çevir (Projektör 2. tuğla)
# LLM (Claude Sonnet 4.6) YALNIZCA metin katmanında çalışır — sayı/tahmin/al-sat/skor ASLA (CLAUDE.md §6).

import json
import logging
import os
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
_log = logging.getLogger(__name__)

_SISTEM_PROMPT = """Sen bir Türk finans haberi editörüsün. Görevin KAP (Kamuyu Aydınlatma Platformu)
açıklamalarını sade, kısa, tarafsız Türkçeyle özetlemek.

SERT KURALLAR — HİÇ İSTİSNA YOK:
- Hiçbir sayı, yüzde (%), fiyat, hedef fiyat, stop değeri, olasılık YAZMA.
- Hiçbir al/sat/tut tavsiyesi verme.
- "Yükselir", "düşer", "artacak", "azalacak" gibi yön tahmini YAPMA.
- Hiçbir skor, sinyal, güven değeri, performans değerlendirmesi YAZMA.
- Yatırım tavsiyesi olarak yorumlanabilecek hiçbir ifade kullanma.

SADECE YAP:
- Açıklamanın NE OLDUĞUNU 1 kısa cümlede sade dille anlat. ("Şirket X karar açıkladı." gibi)
- Ton: tarafsız, bilgilendirici, gazete haberi gibi.
- Cümle uzunluğu: maksimum 20 kelime.

Yanıtı SADECE JSON dizisi olarak ver, başka hiçbir metin ekleme:
[{"tk": "THYAO", "yorum": "Şirket olağanüstü genel kurul toplantısı yapacağını duyurdu."}, ...]"""


def hikayele(sonuc=None, model="claude-sonnet-4-6", max_hisse=15):
    """sonuc: baglam_motor.topla() çıktısı (None ise kendi çağırır).
    Sadece 'sebepli' kayıtlar için KAP konusunu LLM ile 1 cümleye çevirir.
    Dönüş: {"tarih", "model", "hikayeler":[{"tk","nm","ch","konu","yorum"}...]}
    """
    from baglam_motor import topla

    if sonuc is None:
        sonuc = topla()

    tarih = sonuc.get("tarih", datetime.now().strftime("%Y-%m-%d"))
    kayitlar = sonuc.get("kayitlar", [])

    bos_cikti = {"tarih": tarih, "model": model, "hikayeler": []}

    # Sadece sebepli kayıtları al (açıklaması olan + hareketli)
    sebepli = [r for r in kayitlar if r.get("sinif") == "sebepli"]

    if not sebepli:
        _log.info("Sebepli kayıt yok — LLM çağrılmadı.")
        _yaz_json(bos_cikti)
        return bos_cikti

    # API anahtarı yoksa çökme yok: log + boş çıktı
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        _log.warning("ANTHROPIC_API_KEY ortamda yok — LLM çağrılmadı, boş çıktı döndürülüyor.")
        _yaz_json(bos_cikti)
        return bos_cikti

    # max_hisse sınırı
    hedefler = sebepli[:max_hisse]
    _log.info(
        f"{len(sebepli)} sebepli kayıt bulundu, {len(hedefler)} tanesi işlenecek (max_hisse={max_hisse})."
    )

    # Tek API çağrısı için mesaj — hisse başına ilk KAP konusunu kullan
    istek_satirlari = []
    for r in hedefler:
        aciklamalar = r.get("aciklamalar", [])
        if not aciklamalar:
            continue
        konu = aciklamalar[0].get("konu", "").strip()
        if not konu:
            continue
        istek_satirlari.append(f'- Hisse: {r["tk"]} | KAP konusu: "{konu}"')

    if not istek_satirlari:
        _log.info("İşlenecek açıklama konusu yok — LLM çağrılmadı.")
        _yaz_json(bos_cikti)
        return bos_cikti

    kullanici_mesaji = (
        "Aşağıdaki KAP açıklamalarını özetle. Her biri için 1 kısa Türkçe cümle yaz.\n"
        "Yanıtı sadece JSON dizisi olarak ver:\n\n"
        + "\n".join(istek_satirlari)
    )

    # LLM çağrısı (tek çağrı, hisse başına değil)
    from anthropic import Anthropic

    istemci = Anthropic(api_key=api_key)
    try:
        yanit = istemci.messages.create(
            model=model,
            max_tokens=1024,
            system=_SISTEM_PROMPT,
            messages=[{"role": "user", "content": kullanici_mesaji}],
        )
        ham_yanit = yanit.content[0].text.strip()
    except Exception as e:
        _log.error(f"API çağrısı başarısız: {e}")
        _yaz_json(bos_cikti)
        return bos_cikti

    # JSON parse — başarısız olursa boş çıktı (uydurma yorum yok)
    try:
        # Yanıt bazen ```json ... ``` bloğu içerebilir, temizle
        temiz = ham_yanit
        if temiz.startswith("```"):
            satirlar = temiz.split("\n")
            temiz = "\n".join(s for s in satirlar if not s.startswith("```")).strip()
        llm_liste = json.loads(temiz)
        if not isinstance(llm_liste, list):
            raise ValueError("LLM yanıtı liste değil")
    except Exception as e:
        _log.error(f"LLM yanıtı parse edilemedi: {e}. Ham yanıt: {ham_yanit[:300]}")
        _yaz_json(bos_cikti)
        return bos_cikti

    # Hisse → yorum eşleştirmesi
    yorum_harita = {}
    for item in llm_liste:
        if not isinstance(item, dict):
            _log.warning(f"Beklenmeyen öğe atlandı: {item}")
            continue
        tk = str(item.get("tk", "")).strip()
        yorum = str(item.get("yorum", "")).strip()
        if tk and yorum:
            yorum_harita[tk] = yorum

    # Sonucu birleştir; yorumu olmayan hisse atlanır
    hikayeler = []
    for r in hedefler:
        tk = r["tk"]
        yorum = yorum_harita.get(tk)
        if not yorum:
            _log.warning(f"{tk}: LLM yorumu bulunamadı veya parse edilemedi, atlandı.")
            continue
        hikayeler.append({
            "tk": tk,
            "nm": r.get("nm", tk),
            "ch": r.get("ch", 0.0),
            "konu": r["aciklamalar"][0].get("konu", "") if r.get("aciklamalar") else "",
            "yorum": yorum,
        })

    cikti = {"tarih": tarih, "model": model, "hikayeler": hikayeler}
    _yaz_json(cikti)
    return cikti


def _yaz_json(cikti, dosya="hikaye_gunluk.json"):
    """Çıktıyı guncelleme damgasıyla JSON'a yazar; hata olursa log, çökme yok."""
    tam = {"guncelleme": datetime.now().isoformat(timespec="seconds"), **cikti}
    try:
        with open(dosya, "w", encoding="utf-8") as f:
            json.dump(tam, f, ensure_ascii=False, indent=2)
        _log.info(f"Yazıldı: {dosya}")
    except Exception as e:
        _log.warning(f"{dosya} yazılamadı: {e}")


if __name__ == "__main__":
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        print("anahtar yok, LLM cagrilmadi — ANTHROPIC_API_KEY ortamda tanımlı değil.")
    else:
        from baglam_motor import topla

        print("baglam_motor.topla() çalıştırılıyor...")
        sonuc = topla()
        sebepli_n = sum(1 for r in sonuc.get("kayitlar", []) if r.get("sinif") == "sebepli")
        print(f"  Sebepli kayıt sayısı: {sebepli_n}")

        print("hikayele() çalıştırılıyor...")
        cikti = hikayele(sonuc=sonuc)
        hikayeler = cikti.get("hikayeler", [])
        print(f"  Yorum üretilen hisse sayısı: {len(hikayeler)}")

        if hikayeler:
            print("\nİlk 3 yorum:")
            for h in hikayeler[:3]:
                print(f"  [{h['tk']}] %{h['ch']:+.1f}  {h['yorum']}")
