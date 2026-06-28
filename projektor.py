# projektor.py — Günlük bağlam özetini Telegram'a yollar (Projektör son tugla)
# Projektör yol haritası son adım (CLAUDE.md §7). Bağlam + nötr rejim notu;
# al/sat/tahmin/hedef/skor ASLA (CLAUDE.md §6 + §2).
# Varsayılan: kuru çalışma (basar, göndermez). --send veya PROJEKTOR_SEND=1 ile gönderir.

import logging
import os
import sys
import urllib.parse
import urllib.request
from datetime import date

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
_log = logging.getLogger(__name__)


def mesaj_kur(sonuc, hikaye, rejim) -> str:
    """Bağlam özetini saf metin olarak üretir (saf fonksiyon, yan etki yok).

    Yalnızca olgusal bilgi: gerçekleşen günlük %değişim + makro reel faiz.
    Al/sat/tahmin/hedef/skor içermez.
    """
    tarih = sonuc.get("tarih", date.today().isoformat())
    kap_durum = sonuc.get("kap_durum", "kapali")
    kayitlar = sonuc.get("kayitlar", [])
    hikayeler = hikaye.get("hikayeler", [])

    satirlar = []

    # 1. Başlık
    satirlar.append(f"APEX Baglam Ozeti — {tarih}")
    satirlar.append("")

    # 2. Rejim satırı (nötr olgu, yalnız gerçekleşen makro sayılar)
    durus = rejim.get("durus", "NOTR")
    reel = rejim.get("reel", 0.0)
    isaret = "+" if reel >= 0 else ""
    satirlar.append(f"Rejim: {durus} (reel %{isaret}{reel})")
    satirlar.append("")

    # 3. Görünür sebepli hareketler (hikaye_motor LLM yorumları)
    if hikayeler:
        satirlar.append("Gorunur sebepli hareketler:")
        for h in hikayeler:
            ch = h.get("ch", 0.0)
            tk = h.get("tk", "")
            yorum = h.get("yorum", "")
            satirlar.append(f"• {tk} %{ch:+.1f} — {yorum}")
        satirlar.append("")

    # 4. Sebepsiz sert hareketler (KAP açık ama açıklama yok)
    sebepsiz = [r for r in kayitlar if r.get("sinif") == "sebepsiz"]
    if sebepsiz:
        satirlar.append("Gorunur KAP sebebi olmayan hareketler (spekulatif olabilir):")
        for r in sebepsiz:
            ch = r.get("ch", 0.0)
            tk = r.get("tk", "")
            satirlar.append(f"• {tk} %{ch:+.1f} (gorunur KAP sebebi yok)")
        satirlar.append("")

    # 5. KAP erişilemedi uyarısı
    if kap_durum == "kapali":
        satirlar.append("KAP erisilemedi; sebep analizi bugun atlandi.")
        satirlar.append("")

    # Eşik üstü hareket yoksa bilgi notu (KAP açık ama hiç eşik geçilmemiş)
    hareketli_n = sum(1 for r in kayitlar if r.get("hareketli"))
    if not hikayeler and not sebepsiz and hareketli_n == 0:
        satirlar.append("Bugun esik ustu belirgin hareket gorunmuyor.")
        satirlar.append("")

    # 6. Kapanış damgası (her mesajda bulunur)
    satirlar.append(
        "Bu bir baglam ozetidir, yatirim tavsiyesi degildir. "
        "Pozisyon/risk disiplini ayridir."
    )

    return "\n".join(satirlar)


def gonder_telegram(metin) -> bool:
    """urllib.request ile Telegram'a POST atar. Token/chat env'den alınır.

    Çökme yok: secret eksikse veya API hatası olursa log + False döner.
    """
    token = os.environ.get("TELEGRAM_TOKEN", "")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")

    if not token or not chat_id:
        _log.warning(
            "TELEGRAM_TOKEN veya TELEGRAM_CHAT_ID ortamda tanimli degil — gonderim atlandi."
        )
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    veri = urllib.parse.urlencode({"chat_id": chat_id, "text": metin}).encode("utf-8")

    try:
        istek = urllib.request.Request(url, data=veri, method="POST")
        with urllib.request.urlopen(istek, timeout=15) as yanit:
            durum = yanit.getcode()
        if durum == 200:
            _log.info("Telegram mesaji basariyla gonderildi.")
            return True
        _log.error(f"Telegram API beklenmeyen durum kodu: {durum}")
        return False
    except Exception as e:
        _log.error(f"Telegram gonderimi basarisiz: {e}")
        return False


def main(send=False):
    """Baglamı toplar, hikayeler, mesaj kurar; send=True ise Telegram'a yollar.

    KORUMA KABUGU: ana akistaki herhangi bir adim patlarsa (baglam_motor /
    hikaye_motor / app importu, veri cekimi, KAP erisimi vb.) cron COKMEZ;
    hata loglanir ve None doner. Boylece GitHub Actions her gun kirmizi vermez.
    """
    try:
        _log.info("baglam_motor.topla() calistiriliyor...")
        from baglam_motor import topla

        sonuc = topla()

        _log.info("hikaye_motor.hikayele() calistiriliyor...")
        from hikaye_motor import hikayele

        hikaye = hikayele(sonuc=sonuc)

        _log.info("app.rejim_hesapla() calistiriliyor...")
        from app import rejim_hesapla

        rejim = rejim_hesapla(date.today())

        metin = mesaj_kur(sonuc, hikaye, rejim)
    except Exception as e:
        _log.error(f"Projektor ana akis basarisiz, bugun atlandi: {e}")
        return None

    if send:
        _log.info("--send modu: Telegram'a gonderiliyor...")
        basarili = gonder_telegram(metin)
        if not basarili:
            _log.warning("Gonderim basarisiz veya atlandi.")
    else:
        print(metin)

    return metin


if __name__ == "__main__":
    send = "--send" in sys.argv or os.environ.get("PROJEKTOR_SEND", "") == "1"
    try:
        main(send=send)
    except Exception as e:
        # Son kalkan: beklenmeyen her sey burada yutulur; cron temiz (exit 0) cikar.
        _log.error(f"Beklenmeyen hata; cron yine de temiz cikiyor: {e}")
        sys.exit(0)
