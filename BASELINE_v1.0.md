# APEX — BASELINE v1.0 (TEMEL SÜRÜM)

Tarih: 27 Haziran 2026
Bu, bundan sonraki tüm geliştirmenin üstüne **parça parça** bineceği temizlenmiş temeldir.

## Bu baseline'da repo'ya göre ne değişti
- `ui_app_template.html` → 573 satır: UI dürüstlük Pas-1 (winRate→kalibre olasılık,
  sahte emir defteri→dürüst not) + Pas-2 (demo bakiye/pozisyon→gerçek APP.robot verisi).
- `ai_model.py` → F1 düzeltmesi (walk-forward "sahte sıfır" padding kaldırıldı).
- `durum.py` + `yol_haritasi.py` → komple bakım teşhisi + yeni yol haritası yazıldı (proje hafızası).
- ÇÖP TEMİZLENDİ: boşluklu `ai model.py`, `arayuz kartlar.py`, `bist kartlar.py` (import edilemez kalıntılar).

## Doğrulama
- 38 .py dosyasının tamamı sözdizimi geçerli.
- Yerel import'lar bütün (kırık yok).
- Streamlit girişi: `app.py` (mobil native UI'yi gömer).

## Sıradaki işler (durum.py'deki Katman 0 — üstüne parça parça)
1. Pas-2 cüzdanı canlıya al.
2. Dürüst yolu bağla: av_skoru↔ML barıştır, UI'yi performans.risk_metrikleri + oz_puanlama'ya bağla.
3. backtest'i onar (tazelik bypass + komisyon + mevduat %45 eşiği) → edge'i dürüstçe ölç.
4. Sessiz veri bozulmasını görünür yap.
5. Supabase kalıcı sicil.

Detay: `durum.py` ve `yol_haritasi.py`.
