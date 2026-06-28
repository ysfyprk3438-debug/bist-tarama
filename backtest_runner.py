"""APEX · TELEGRAM TEST — secrets→env→bot→telefon borusunu anında doğrular.
Telefona test mesajı atar; atamazsa NEDENİNİ BACKTEST_SONUC.md'ye yazar."""
import os, json, urllib.request, datetime

tok = os.environ.get("TELEGRAM_TOKEN") or os.environ.get("TELEGRAM_BOT_TOKEN")
chat = os.environ.get("TELEGRAM_CHAT_ID")
L = ["# APEX — Telegram Test", "", f"_{datetime.datetime.now():%Y-%m-%d %H:%M}_", ""]
L.append(f"- TELEGRAM_TOKEN: {'VAR ('+str(len(tok))+' karakter)' if tok else '**YOK**'}")
L.append(f"- TELEGRAM_CHAT_ID: {'VAR ('+chat+')' if chat else '**YOK**'}")

sonuc = "denenmedi"
if tok and chat:
    url = f"https://api.telegram.org/bot{tok}/sendMessage"
    veri = json.dumps({"chat_id": chat,
                       "text": "✅ APEX test mesajı — boru çalışıyor. Artık her iş günü duruş+pozisyon buraya düşecek."}).encode()
    try:
        req = urllib.request.Request(url, data=veri, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=15) as r:
            body = r.read().decode("utf-8", "replace")
            sonuc = f"HTTP {r.status} · {body[:200]}"
    except Exception as e:
        try: sonuc = f"HATA: {e.read().decode('utf-8','replace')[:200]}"
        except Exception: sonuc = f"HATA: {type(e).__name__}: {e}"
L += ["", f"**Gönderim sonucu:** {sonuc}", "",
      "- `\"ok\":true` görüyorsan → telefonuna mesaj düştü, boru tamam.",
      "- `chat not found` → CHAT_ID yanlış ya da bota hiç /start atmadın.",
      "- `Unauthorized` → TOKEN yanlış/eski.",
      "- TOKEN/CHAT_ID **YOK** → workflow env'i ya da secret ismi tutmuyor."]
with open("BACKTEST_SONUC.md", "w", encoding="utf-8") as f:
    f.write("\n".join(L))
print("\n".join(L))
