# -*- coding: utf-8 -*-
"""
telegram_alarm.py — ZAMANLANMIŞ GÖREV (uygulama kapalıyken bile çalışır).

Taramayı çalıştırır, dikkat çeken sinyalleri (KESİN AL · Altın Kesişim ·
KESİN SAT · Manipülasyon) Telegram'dan bildirir.

Çalıştırma:
    TELEGRAM_TOKEN=xxx TELEGRAM_CHAT_ID=yyy python telegram_alarm.py

Token ve chat_id GitHub Secrets / Streamlit secrets içinde tutulur — KODA YAZILMAZ.
GitHub Actions cron'u .github/workflows/telegram_alarm.yml dosyasındadır.
"""
import os
import sys
import datetime

import requests

from tarama_core import tara
import payload as pl

TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
VADE = os.environ.get("AVCI_VADE", "haftalik")


def gonder(mesaj):
    if not TOKEN or not CHAT_ID:
        print("UYARI: TELEGRAM_TOKEN / TELEGRAM_CHAT_ID tanımlı değil — mesaj gönderilmedi.")
        print(mesaj)
        return False
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            json={"chat_id": CHAT_ID, "text": mesaj, "parse_mode": "Markdown", "disable_web_page_preview": True},
            timeout=20,
        )
        ok = r.status_code == 200
        print("Telegram:", "gönderildi ✓" if ok else f"HATA {r.status_code} {r.text[:200]}")
        return ok
    except Exception as e:
        print("Telegram gönderim hatası:", e)
        return False


def _satir(u):
    ok = "🟢" if u["side"] == "AL" else "🔴"
    etiket = {"simdi": "KESİN AL", "al": "AL", "izle": "İZLE", "kesinSat": "KESİN SAT"}.get(u["v"], "")
    rozet = ""
    if "altinKesisim" in u["lists"]:
        rozet += " 🌅"
    if "manip" in u["lists"]:
        rozet += " ⚠️"
    yon = "+" if u["kz"] >= 0 else ""
    bilgi = f"hedef ₺{u['hedef']:.2f} ({yon}%{u['kz']:.1f})" if u["side"] == "AL" else f"çıkış · düşüş -%{u['kz']:.1f}"
    return f"{ok} *{u['tk']}*{rozet} — {etiket} · ₺{u['px']:.2f} · AV {u['av']} · {bilgi}\n    🕐 {u['zaman']}"


def alarm_mesaji(sonuclar):
    """Dikkat çeken sinyalleri seç ve Türkçe mesaj kur. Yoksa None."""
    al, sat = [], []
    for r in sonuclar:
        try:
            u = pl.to_ui(r)
        except Exception:
            continue
        if u["side"] == "AL" and (u["v"] in ("simdi", "al") or "altinKesisim" in u["lists"]):
            al.append(u)
        elif u["side"] == "SAT":
            sat.append(u)
    al = al[:6]
    sat = sat[:5]
    if not al and not sat:
        return None
    saat = datetime.datetime.now().strftime("%d.%m %H:%M")
    bolum = [f"🎯 *BIST Para Avcısı* · {saat}"]
    if al:
        bolum.append("\n*🟢 Fırsatlar (al tarafı)*\n" + "\n".join(_satir(u) for u in al))
    if sat:
        bolum.append("\n*🔴 Uzak dur / çık*\n" + "\n".join(_satir(u) for u in sat))
    bolum.append("\n_Karar destek aracıdır · yatırım tavsiyesi değildir._")
    return "\n".join(bolum)


def main():
    print(f"[{datetime.datetime.now():%Y-%m-%d %H:%M}] Tarama başlıyor (vade={VADE})…")
    sonuclar, xu100 = tara(VADE)
    print(f"Sonuç: {len(sonuclar)} hisse, XU100 %{xu100:+.2f}")
    msg = alarm_mesaji(sonuclar)
    if not msg:
        print("Bildirilecek dikkat çeken sinyal yok — mesaj atılmadı.")
        return 0
    gonder(msg)
    return 0


if __name__ == "__main__":
    sys.exit(main())
