# 🤖 Telegram Otomatik Alarm — Kurulum (5 dk)

Robot, uygulama **kapalıyken bile** belirli saatlerde taramayı çalıştırıp
Telegram'dan alarm atar. Bunun için 2 gizli bilgi gerekir. **Koda yazılmaz.**

## 1) Bot token'ı al
- Telegram'da **@BotFather** → `/mybots` → botunu seç (@bist_tarama_2025_bot) → **API Token**.
- Örnek: `7123456789:AAH...`

## 2) Chat ID'ni al
- Kendi botuna bir mesaj at ("merhaba").
- Tarayıcıda aç: `https://api.telegram.org/bot<TOKEN>/getUpdates`
- Çıkan metinde `"chat":{"id":123456789` → bu sayı senin **chat ID**'in.
  (Alternatif: Telegram'da **@userinfobot**'a yaz, ID'ni söyler.)

## 3) GitHub'a gizli olarak ekle
GitHub deposu → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**:
- `TELEGRAM_TOKEN`  = (1. adımdaki token)
- `TELEGRAM_CHAT_ID` = (2. adımdaki sayı)

## 4) Hazır!
- Alarm otomatik çalışır: hafta içi **09:50 / 12:00 / 15:00 / 17:30** (İstanbul).
- Hemen denemek için: GitHub → **Actions** sekmesi → "BIST Telegram Alarm" → **Run workflow**.
- Saatleri değiştirmek: `.github/workflows/telegram_alarm.yml` içindeki `cron` satırları (UTC!).

> Not: GitHub'ın zamanlayıcısı bazen 5–15 dk gecikebilir (normaldir).
> Robot şu an **sanal (paper)** çalışır — gerçek emir vermez, sadece bildirir.
