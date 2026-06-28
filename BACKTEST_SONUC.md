# APEX — Telegram Test

_2026-06-28 00:28_

- TELEGRAM_TOKEN: VAR (46 karakter)
- TELEGRAM_CHAT_ID: VAR (8881374940)

**Gönderim sonucu:** HTTP 200 · {"ok":true,"result":{"message_id":2,"from":{"id":8355634877,"is_bot":true,"first_name":"APEX Pusula","username":"apex_pusula_3438_bot"},"chat":{"id":8881374940,"first_name":"Yusuf","last_name":"Yaprak

- `"ok":true` görüyorsan → telefonuna mesaj düştü, boru tamam.
- `chat not found` → CHAT_ID yanlış ya da bota hiç /start atmadın.
- `Unauthorized` → TOKEN yanlış/eski.
- TOKEN/CHAT_ID **YOK** → workflow env'i ya da secret ismi tutmuyor.