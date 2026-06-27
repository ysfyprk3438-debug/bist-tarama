# APEX — Makro Kaynak Sondası

_2026-06-27 22:49 · otomatik güncelleme için kaynak araması_

## 1-2) Dünya Bankası (keysiz, US-OK, ama yıllık+gecikmeli)

- ❌ FP.CPI.TOTL.ZG: durum=None · HATA: TimeoutError: The read operation timed out
- ❌ FR.INR.RINR: durum=None · HATA: TimeoutError: The read operation timed out

## 3-4) OECD SDMX (keysiz, aylık olabilir)

- ✅ TR aylık TÜFE: durum=200 · CT=application/vnd.sdmx.data+json; version=2; charset=utf-8 · gövde: «{"meta":{"schema":"https://raw.githubusercontent.com/sdmx-twg/sdmx-json/master/data-messag»
- ❌ TR kısa-vade faiz: HATA: HTTPError: HTTP Error 422: Unprocessable Entity

## Yorum

- Dünya Bankası ✅ ama YILLIK → çeyreklik rejim için fazla kaba/gecikmeli (tek başına yetmez).
- OECD ✅ + JSON ise → aylık TÜFE & faiz otomasyonun çekirdeği olabilir.
- Hepsi ❌/⚠️ ise → güvenilir US-kaynak yok; otomasyon yerine **10 saniyelik güvenli elle-ekle + tazelik hatırlatıcısı** doğru tasarım (sessiz-hata riski yok).
