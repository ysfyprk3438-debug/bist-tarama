# APEX — EVDS Teşhis

_2026-06-27 21:44_

Anahtar: 10 karakter (…EpG)

İki yöntem deneniyor (basit USD serisiyle):

**1) Anahtar HEADER'da:** ❌ HTTP 200 · text/html; charset=utf-8 · mesaj: «--> EVDS»

**2) Anahtar URL'de:** ❌ HTTP 200 · text/html; charset=utf-8 · mesaj: «--> EVDS»

> ✅ olan yöntem varsa onu kullanırız. İkisi de ❌ ve mesaj 'anahtar/key/invalid' diyorsa EVDS profilinden anahtarı tam kopyalamak gerekiyor (kısaltılmış olabilir).