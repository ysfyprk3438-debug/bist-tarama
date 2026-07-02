# 🚀 APEX — Deploy Kontrol Listesi

APEX canlıya nasıl alınır. Güncel mimari: **app.py tek dosya** (Streamlit Community Cloud),
kod git ile gelir.

## Mimari (güncel)
- **Canlı çekirdek:** `app.py` (tek dosya) + `apex_omurga_v1.html` şablonu (`__APP_DATA__` enjekte).
- **Canlı modüller:** `veri.py`, `skor_motoru.py`, `pozisyon.py`, `sektor_map.py`, `gunluk_log.py`,
  `projektor.py`, `telegram_alarm.py`, `bekci.py`, `akd_cekici.py`, `akd_oto_topla.py`,
  `akd_sicil.py`, `baglam_motor.py`, `hikaye_motor.py`, `kap_oku.py`, `makro_*`.
- **Sayfalar:** `pages/01_Sanal_Borsa.py`, `pages/02_Gorsel_Panel.py`.
- **Eski 30-modüllü mimari** (analiz.py, karar.py, robot.py …): **`arsiv/` altında, canlı sistem KULLANMIYOR.**

## Deploy akışı (değişmez)
1. **Kod git ile gelir** — @claude PR merge (insan kodu) veya GitHub web editor. Kopyala-yapıştır 30 dosya YOK.
2. **Streamlit otomatik yeniden yayınlar** — main'e push'ta 1–2 dk içinde derler.
3. **Tazeleme:** `app.py`'deki `SURUM` sabitini artır → cache reboot'suz tazelenir.
4. **Cache takılırsa:** share.streamlit.io → uygulaman → **Manage app → Reboot**.
5. **Workflow dosyaları** (`.github/workflows/*.yml`): @claude App token'ıyla YAZILAMAZ;
   laptop'tan `gh` (workflow scope) ile push edilir.
6. **Sırlar** (token/API key): ASLA koda yazılmaz; GitHub Secrets (ör. `CLAUDE_CODE_OAUTH_TOKEN`, `FOREKS_AUTH`).

> Tek doğruluk kaynağı: **CLAUDE.md §9 (Deployment Protokolü).**

## Bağımlılıklar
`requirements.txt`: streamlit, pandas, numpy, requests, matplotlib, openpyxl, scikit-learn,
yfinance, anthropic, gspread, google-auth.

## ⚠️ Hatırlatma
Karar destek aracıdır, yatırım tavsiyesi değildir. SPK lisanslı değildir. Kararlar kullanıcıya aittir.
