# APEX — Telegram Test

_2026-06-28 00:24_

- TELEGRAM_TOKEN: VAR (46 karakter)
- TELEGRAM_CHAT_ID: VAR (8355634877:AAHQXyCTFOH71497drwRSPWtIl07HSyqpHs)

**Gönderim sonucu:** HATA: {"ok":false,"error_code":403,"description":"Forbidden: the bot can't send messages to the bot"}

- `"ok":true` görüyorsan → telefonuna mesaj düştü, boru tamam.
- `chat not found` → CHAT_ID yanlış ya da bota hiç /start atmadın.
- `Unauthorized` → TOKEN yanlış/eski.
- TOKEN/CHAT_ID **YOK** → workflow env'i ya da secret ismi tutmuyor.