# APEX — Temel Veri Sondası (İş Yatırım mali tablo)

_2026-06-27 20:21 · endpoint format keşfi_

Denenen dönemler (yıl/dönem): [(2026, 3), (2025, 12), (2025, 9), (2025, 6)]

## EREGL (sanayi)
- financialGroup=`XI_29` → OK 147 kalem
- financialGroup=`UFRS` → boş value
- financialGroup=`UFRS_K` → boş value
- financialGroup=`boş` → boş value

**Çalışan grup: `XI_29`. İlk 25 kalem:**

| itemCode | açıklama | d1 | d2 | d3 | d4 |
|---|---|---:|---:|---:|---:|
| 1A | Dönen Varlıklar | 257051476000 | 275790750346 | 229845844000 | 212417591000 |
| 1AA |   Nakit ve Nakit Benzerleri | 123933482000 | 127070780476 | 97706053000 | 83896762000 |
| 1AB |   Finansal Yatırımlar | 222299000 | 0 | 0 | 0 |
| 1AC |   Ticari Alacaklar | 27036031000 | 30203469998 | 26581146000 | 26111297000 |
| 1AD |   Finans Sektörü Faaliyetlerinden Alacak | 0 | 0 | 0 | 0 |
| 1AE |   Diğer Alacaklar | 282679000 | 303915540 | 267627000 | 435250000 |
| 1AEA |   Müşteri Sözleşmelerinden Doğan Varlıkl | 0 | 0 | 0 | 0 |
| 1AF |   Stoklar | 88430422000 | 98360024069 | 87652119000 | 84456730000 |
| 1AG |   Canlı Varlıklar | 0 | 0 | 0 | 0 |
| 1AH |   Diğer Dönen Varlıklar | 17146563000 | 19852560263 | 17638899000 | 17517552000 |
| 1AI |     (Ara Toplam) | 257051476000 | 275790750346 | 229845844000 | 212417591000 |
| 1AJ |   Satış Amacıyla Elde Tutulan Duran Varl | 0 | 0 | 0 | 0 |
| 1AK | Duran Varlıklar | 319694560000 | 338817917315 | 293800584000 | 279946971000 |
| 1B |   Ticari Alacaklar | 0 | 0 | 0 | 0 |
| 1BA |   Finans Sektörü Faaliyetlerinden Alacak | 0 | 0 | 0 | 0 |
| 1BB |   Diğer Alacaklar | 221456000 | 203161661 | 175409000 | 167507000 |
| 1BBA |   Müşteri Sözleşmelerinden Doğan Varlıkl | 0 | 0 | 0 | 0 |
| 1BC |   Finansal Yatırımlar | 183427000 | 204944312 | 179802000 | 179144000 |
| 1BD |   Özkaynak Yöntemiyle Değerlenen Yatırım | 1588214000 | 1618917560 | 1398891000 | 1298154000 |
| 1BE |   Canlı Varlıklar | 0 | 0 | 0 | 0 |
| 1BF |   Yatırım Amaçlı Gayrimenkuller | 1443766000 | 1534590478 | 1352181000 | 1295787000 |
| 1BFA |   Stoklar | 0 | 0 | 0 | 0 |
| 1BFAA |   Kullanım Hakkı Varlıkları | 1515086000 | 1586442506 | 1417857000 | 1424602000 |
| 1BG |   Maddi Duran Varlıklar | 291729983000 | 305141152646 | 263528176000 | 250362169000 |
| 1BGA |   Şerefiye | 833814000 | 885488834 | 779550000 | 746382000 |

**Anahtar kalem araması (net kâr / özkaynak / satış):**
- `1AJ`   Satış Amacıyla Elde Tutulan Duran Varlıklar = 0
- `1BD`   Özkaynak Yöntemiyle Değerlenen Yatırımlar = 1588214000
- `1BL` TOPLAM VARLIKLAR = 576746036000
- `2AAGD`   Dönem Karı Vergi Yükümlülüğü = 613376000
- `2AAGH`   Satış Amaçlı Elde Tutulan Duran Varlıklara  = 0
- `2N` Özkaynaklar = 304848442000
- `2O`   Ana Ortaklığa Ait Özkaynaklar = 295496351000
- `2OCE`   Geçmiş Yıllar Kar/Zararları = 165487141000
- `2OCF`   Dönem Net Kar/Zararı = 383856000
- `3C` Satış Gelirleri = 59684847000
- `3CA` Satışların Maliyeti (-) = -54879228000
- `3DA` Pazarlama, Satış ve Dağıtım Giderleri (-) = -705628000
- `3H` Net Faaliyet Kar/Zararı = 2143859000
- `3HAC` Özkaynak Yöntemiyle Değerlenen Yatırımların K = 62615000
- `3HACA` Finansman Gideri Öncesi Faaliyet Karı/Zararı = 2498709000
- `3J` SÜRDÜRÜLEN FAALİYETLER DÖNEM KARI/ZARARI = 405786000
- `3KA` Durdurulan Faaliyetler Vergi Sonrası Dönem Ka = 0
- `3L` DÖNEM KARI (ZARARI) = 405786000
- `3LA` Dönem Kar/Zararının Dağılımı = 0
- `4BC` Yurtiçi Satışlar = 48394620000
- `4BD` Yurtdışı Satışlar = 9325184000

## GARAN (banka)
- financialGroup=`XI_29` → boş value
- financialGroup=`UFRS` → OK 192 kalem
- financialGroup=`UFRS_K` → OK 192 kalem
- financialGroup=`boş` → boş value

**Çalışan grup: `UFRS`. İlk 25 kalem:**

| itemCode | açıklama | d1 | d2 | d3 | d4 |
|---|---|---:|---:|---:|---:|
| 1A | I. NAKİT DEĞERLER VE MERKEZ BANKASI | 566760075000 | 632437890000 | 569655583000 | 529760307000 |
| 1AA | II. GERÇEĞE UYGUN DEĞ./ZAR. YANS.(Net) | 20245538000 | 10142204000 | 9028439000 | 6961032000 |
| 1AAA | 2.1 Alım Satım Amaçlı Finansal Varlıklar | 0 | 0 | 0 | 0 |
| 1AAB | 2.1.1 Devlet Borçlanma Senetleri | 0 | 0 | 0 | 0 |
| 1AAC | 2.1.2 Sermayede Payı Temsil Eden Menkul  | 0 | 0 | 0 | 0 |
| 1AAD | 2.1.3 Alım Satım Amaçlı Türev Finansal V | 0 | 0 | 0 | 0 |
| 1AAE | 2.1.4 Diğer Menkul Değerler | 0 | 0 | 0 | 0 |
| 1AB | 2.2 Gerçeğe Uyg. Değ. Kar/Zarara Yans. | 20245538000 | 10142204000 | 9028439000 | 6961032000 |
| 1ABA | 2.2.1 Devlet Borçlanma Senetleri | 13382529000 | 4385383000 | 3867170000 | 5329778000 |
| 1ABB | 2.2.2 Sermayede Payı Temsil Eden Menkul  | 546588000 | 335262000 | 477122000 | 336747000 |
| 1ABC | 2.2.3 Krediler | 0 | 0 | 0 | 0 |
| 1ABD | 2.2.4 Diğer Menkul Değerler | 6316421000 | 5421559000 | 4684147000 | 1294507000 |
| 1AC | III. BANKALAR | 111126868000 | 165445635000 | 131693351000 | 159177861000 |
| 1AD | IV. PARA PİYASALARINDAN ALACAKLAR | 15470945000 | 15017011000 | 14525284000 | 13925165000 |
| 1ADA | 4.1 Bankalararası Para Piyasasından Alac | 0 | 0 | 0 | 0 |
| 1ADB | 4.2 İMKB Takasbank Piyasasından Alacakla | 0 | 0 | 0 | 0 |
| 1ADC | 4.3 Ters Repo İşlemlerinden Alacaklar | 0 | 0 | 0 | 0 |
| 1AE | V. SATILMAYA HAZIR FİNANSAL VARLIKLAR (N | 0 | 0 | 0 | 0 |
| 1AEA | 5.1 Sermayede Payı Temsil Eden Menkul De | 0 | 0 | 0 | 0 |
| 1AEB | 5.2 Devlet Borçlanma Senetleri | 0 | 0 | 0 | 0 |
| 1AEC | 5.3 Diğer Menkul Değerler | 0 | 0 | 0 | 0 |
| 1AF | VI. KREDİLER | 243673180600 | 228161269800 | 208487802000 | 189568469800 |
| 1AFA | 6.1 Krediler | 243673180600 | 228161269800 | 208487802000 | 189568469800 |
| 1AFB | 6.1.1 Bankanın Dahil Olduğu Risk Grubuna | 0 | 0 | 0 | 0 |
| 1AFC | 6.1.2 Diğer | 0 | 0 | 0 | 0 |

**Anahtar kalem araması (net kâr / özkaynak / satış):**
- `1AB` 2.2 Gerçeğe Uyg. Değ. Kar/Zarara Yans. = 20245538000
- `1AIA` 9.1 Özkaynak Yöntemine Göre Muhasebeleştirile = 0
- `1AKA` 11.1 Özkaynak Yöntemine Göre Muhasebeleştiril = 0
- `1AS` XVIII. SATIŞ AMAÇLI  FAALİYETLERE İLİŞKİN DUV = 6284922000
- `1ASA` 18.1 Satış Amaçlı = 6284922000
- `2N` XIV. SATIŞ AMAÇLI ELDE TUTULAN  DUV  BORÇ. = 0
- `2NA` 14.1 Satış Amaçlı = 0
- `2O` XVI. ÖZKAYNAKLAR = 451315838000
- `2OK` 16.2.9 Satış Amaçlı Elde Tut. Dur. DUV Farkla = 0
- `2OU` 16.4.1 Geçmiş Yıllar Kar/Zararı = 191240000
- `2OV` 16.4.2 Dönem Net Kar/Zararı = 33316462000
- `3CCA` 6.1 Sermaye Piyasası İşlemleri Karı/Zararı = 4200980000
- `3CCB` 6.2 Türev Finansal İşlemlerden Kar/Zarar = -24719080000
- `3CCC` 6.3 Kambiyo İşlemleri Karı/Zararı = 15687039000
- `3CH` XI. NET FAALİYET KARI/ZARARI (VIII-IX-X) = 35194476000
- `3CJ` XIII. ÖZKAYNAK YÖNTEMİ UYGULANAN ORTAKLIKLARD = 8762269000
- `3CK` XIV. NET PARASAL POZİSYON KARI/ZARARI = 0
- `3COA` 18.1 Satış Amaçlı Elde Tutulan Duran Varlık G = 0
- `3CPA` 19.1 Satış Amaçlı Elde Tutulan Duran Varlık G = 0
- `3CPB` 19.2 İştirak, Bağlı Ortaklık ve Bir. Satış Za = 0
- `3D` DİĞER KAR/ZARAR = 0
- `3Z` XXIII. NET DÖNEM KARI/ZARARI (XVII+XXII) = 33316462000
- `3ZA` 23.1 Grubun Karı/Zararı = 33316462000
- `3ZB` 23.2 Azınlık Hakları Karı/Zararı (-) = 0
- `3ZC` Hisse Başına Kar/Zarar = 0

---
*Bu bir sonda: format doğrulanınca point-in-time temel-seçim backtest'ini buna göre kuracağız.*