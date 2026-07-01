# projektor.py — Gunluk durum ozetini Telegram'a yollar (SADE DIL surumu)
# al/sat/tahmin/hedef/skor ASLA. Sadece "bugun ne oldu" — olgu.
# Varsayilan: kuru calisma (basar, gondermez). --send veya PROJEKTOR_SEND=1 ile gonderir.

import logging
import os
import sys
import urllib.parse
import urllib.request
from datetime import date

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
_log = logging.getLogger(__name__)

# rejim durusunu HERKESIN anlayacagi dile cevir
_DURUS_SADE = {
    "MEVDUAT LEHINE": "faiz tarafi one cikiyor (mevduat cazip)",
    "HISSE LEHINE": "hisse tarafi one cikiyor",
    "NOTR": "belirgin bir taraf yok, dengeli",
}


def mesaj_kur(sonuc, hikaye, rejim) -> str:
    """Gunun durum ozetini SADE dille, saf metin uretir (yan etki yok).
    Sadece olgu: gerceklesen gunluk %degisim + makro reel faiz. Tavsiye YOK."""
    tarih = sonuc.get("tarih", date.today().isoformat())
    kap_durum = sonuc.get("kap_durum", "kapali")
    kayitlar = sonuc.get("kayitlar", [])
    hikayeler = hikaye.get("hikayeler", [])

    s = []
    s.append(f"APEX gunluk ozet — {tarih}")
    s.append("(Bu bir haber ozetidir; ne al ne sat demez.)")
    s.append("")

    # Piyasa ruzgari — sade
    durus = rejim.get("durus", "NOTR")
    reel = rejim.get("reel", 0.0)
    isaret = "+" if reel >= 0 else ""
    s.append(f"Piyasa ruzgari: {_DURUS_SADE.get(durus, durus.lower())}.")
    s.append(f"(Reel faiz %{isaret}{reel} — faizin enflasyondan farki.)")
    s.append("")

    # Sebebi belli hareketler
    if hikayeler:
        s.append("Bugun sebebi belli olan hareketler:")
        for h in hikayeler:
            ch = h.get("ch", 0.0); tk = h.get("tk", ""); yorum = h.get("yorum", "")
            s.append(f"• {tk} %{ch:+.1f} — {yorum}")
        s.append("")

    # Sebebi belli OLMAYAN sert hareketler
    sebepsiz = [r for r in kayitlar if r.get("sinif") == "sebepsiz"]
    if sebepsiz:
        s.append("Sebebi belli OLMAYAN sert hareketler (dikkat — dedikodu/spekulasyon olabilir):")
        for r in sebepsiz:
            ch = r.get("ch", 0.0); tk = r.get("tk", "")
            s.append(f"• {tk} %{ch:+.1f} (ortada acik bir haber yok)")
        s.append("")

    if kap_durum == "kapali":
        s.append("Haber kaynagina ulasilamadi — bugun sebep analizi yapilamadi.")
        s.append("")

    hareketli_n = sum(1 for r in kayitlar if r.get("hareketli"))
    if not hikayeler and not sebepsiz and hareketli_n == 0:
        s.append("Bugun dikkat cekecek belirgin bir hareket gorunmuyor. Sakin gun.")
        s.append("")

    s.append("Ozet bu kadar. APEX yon tahmini yapmaz, kazandirma vaadi vermez — "
             "sadece bugun ne oldugunu ozetler. Ne alacagina sen karar verirsin.")
    return "\n".join(s)


def gonder_telegram(metin) -> bool:
    """Telegram'a POST. Token/chat env'den. Cokme yok: eksikse log + False."""
    token = os.environ.get("TELEGRAM_TOKEN", "")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
    if not token or not chat_id:
        _log.warning("TELEGRAM_TOKEN veya TELEGRAM_CHAT_ID tanimli degil — gonderim atlandi.")
        return False
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    veri = urllib.parse.urlencode({"chat_id": chat_id, "text": metin}).encode("utf-8")
    try:
        istek = urllib.request.Request(url, data=veri, method="POST")
        with urllib.request.urlopen(istek, timeout=15) as yanit:
            durum = yanit.getcode()
        if durum == 200:
            _log.info("Telegram mesaji gonderildi.")
            return True
        _log.error(f"Telegram API beklenmeyen durum: {durum}")
        return False
    except Exception as e:
        _log.error(f"Telegram gonderimi basarisiz: {e}")
        return False


def main(send=False):
    """Baglami toplar, hikayeler, mesaj kurar; send=True ise yollar.
    KORUMA KABUGU: herhangi bir adim patlarsa cron COKMEZ; hata loglanir, None doner."""
    try:
        from baglam_motor import topla
        sonuc = topla()
        from hikaye_motor import hikayele
        hikaye = hikayele(sonuc=sonuc)
        from app import rejim_hesapla
        rejim = rejim_hesapla(date.today())
        metin = mesaj_kur(sonuc, hikaye, rejim)
    except Exception as e:
        _log.error(f"Projektor ana akis basarisiz, bugun atlandi: {e}")
        return None

    if send:
        _log.info("--send: Telegram'a gonderiliyor...")
        if not gonder_telegram(metin):
            _log.warning("Gonderim basarisiz veya atlandi.")
    else:
        print(metin)
    return metin


if __name__ == "__main__":
    send = "--send" in sys.argv or os.environ.get("PROJEKTOR_SEND", "") == "1"
    try:
        main(send=send)
    except Exception as e:
        _log.error(f"Beklenmeyen hata; cron yine de temiz cikiyor: {e}")
        sys.exit(0)
