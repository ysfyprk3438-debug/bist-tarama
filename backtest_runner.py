"""
APEX · TELEGRAM BİLDİRİM — günlük duruş + önerilen pozisyonu telefona yollar.
Token/chat yoksa SESSİZCE atlar (logger asla bozulmaz). Secrets:
  TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID  (GitHub repo Secrets → workflow env ile geçilir).
"""
import os, json, urllib.request


def gonder(metin):
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat:
        return False  # kurulmamış → sessiz no-op
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    veri = json.dumps({"chat_id": chat, "text": metin, "parse_mode": "Markdown",
                       "disable_web_page_preview": True}).encode("utf-8")
    try:
        req = urllib.request.Request(url, data=veri, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status == 200
    except Exception:
        return False


def mesaj_kur(tarih, durus, reel, pol, enf, w, yvol):
    return (f"*APEX · {tarih}*\n"
            f"Reel faiz: %{reel:+.1f}  (pol %{pol:.1f} − enf %{enf:.1f})\n"
            f"Duruş: *{durus}*\n"
            f"Önerilen: %{w*100:.1f} hisse / %{(1-w)*100:.1f} mevduat  (vol %{(yvol or 0)*100:.0f})\n"
            f"_Duruş göstergesidir, kâhin değil — risk-farkında temkin._")


if __name__ == "__main__":
    print("gonder (token yok):", gonder("test"))
    print(mesaj_kur("2026-06-26", "MEVDUAT LEHİNE", 4.5, 37.0, 32.5, 0.012, 0.29))
