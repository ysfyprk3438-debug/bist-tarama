"""
═══════════════════════════════════════════════════════════════════
backtest_runner.py — CI'da headless backtest + mevduat kıyası
═══════════════════════════════════════════════════════════════════
GitHub Actions bunu çağırır (.github/workflows/backtest.yml).
Üretir: BACKTEST_SONUC.md (repo köküne yazılır, sonra commit edilir).

Bu runner üç darboğazı kapatır:
  1) TAZELİK BAYPASI : analiz_et, son veri 10 günden eskiyse None döner.
     Backtest'te her geçmiş dilim "eski" olduğu için 0 işlem çıkıyordu.
     Burada her dilimin tarih indeksini bugüne kaydırıp filtreyi
     ŞEFFAFÇA baypas ediyoruz (analiz.py'ye dokunmadan).
  2) KOMİSYON       : ham getiriden gidiş-dönüş işlem maliyeti düşülür.
  3) DÜRÜST EŞİK    : strateji, yıllık mevduata (%45) göre kıyaslanır.
                      Mevduatı yenemiyorsa "edge YOK" denir — süsleme yok.
"""

import datetime
import pandas as pd

from veri import veri_al, VADE_AYAR
from analiz import analiz_et
from backtest import backtest_calistir

# ── Ayarlar (elle değiştirilebilir) ────────────────────────────────
VADE_KEY      = "haftalik"   # swing / orta vade — gerçekçi senaryo
BASLANGIC_GUN = 120          # ilk 120 bar "ısınma", işlem buradan sonra
MALIYET_RT    = 0.30         # gidiş-dönüş işlem maliyeti, % (BIST perakende ~0.2–0.4)
MEVDUAT_YILLIK = 0.45        # yıllık TL mevduat ~%45 (risk-ayarlı eşik)
ISLEM_GUNU    = 252          # yıllık işlem günü (yıllıklandırma için)

# ── BIST sektör/sembol listesi (app.py ile aynı) ───────────────────
BIST_SEKTORLER = {
    "Bankacilik":   ['AKBNK','GARAN','HALKB','ISCTR','VAKBN','YKBNK','TSKB','ALBRK','SKBNK','KLNMA'],
    "Enerji":       ['EUPWR','ODAS','ENJSA','AKSEN','ZOREN','AYEN','AYDEM','KCAER','CWENE','NATEN'],
    "Sanayi":       ['EREGL','KRDMD','ISDMR','CEMTS','CIMSA','AFYON','ARCLK','VESTL','BFREN','DOAS','OTKAR','FROTO','TOASO','TTRAK'],
    "Saglik_Kimya": ['ECILC','SELEC','MPARK','DEVA','ECZYT','GUBRF','HEKTS','PETKM','SASA','TRCAS','PRKAB'],
    "Perakende":    ['BIMAS','MGROS','SOKM','ULKER','CCOLA','AEFES','TATGD','PNSUT','BANVT','DARDL'],
    "Teknoloji":    ['TTKOM','TCELL','ASELS','NETAS','LOGO','INDES','ARENA','DGATE','KAREL','SMART','PAPIL'],
    "Ulasim":       ['THYAO','PGSUS','TAVHL','CLEBI','MAALT','RYSAS'],
    "Insaat_GYO":   ['EKGYO','ISGYO','TRGYO','KLGYO','VKGYO','SNGYO','HLGYO','ENKAI','TKFEN','GSDHO'],
    "Holding":      ['SAHOL','KCHOL','DOHOL','ALARK','BERA','GOLTS','ADEL','GESAN','MAVI','BRISA','KARSN','GLYHO'],
}
KOD_SEKTOR = {}
for _sek, _kodlar in BIST_SEKTORLER.items():
    for _k in _kodlar:
        KOD_SEKTOR.setdefault(_k, _sek)


# ── Tazelik baypası: dilimin son tarihini bugüne kaydır ────────────
def analiz_bypass(kod, df, vade_ayar, portfoy_tl, carpan, sektor,
                  detayli=False, endeks_close=None):
    """
    backtest_calistir bu fonksiyonu analiz_fonk olarak çağırır.
    Her geçmiş dilimin indeksini, son barı 'bugün' olacak şekilde
    tüm seriyi aynı miktarda öteleyerek kaydırır → tazelik filtresi
    geçer, bar aralıkları (dolayısıyla tüm teknik mantık) korunur.
    """
    try:
        if df is None or len(df) == 0:
            return None
        df2 = df.copy()
        son = df2.index[-1]
        bugun = pd.Timestamp.today().normalize()
        try:
            offset = bugun - son.normalize()
        except AttributeError:
            offset = bugun - pd.Timestamp(son).normalize()
        df2.index = df2.index + offset
        return analiz_et(kod, df2, vade_ayar, portfoy_tl, carpan,
                         sektor, detayli=detayli, endeks_close=endeks_close)
    except Exception:
        return None


def tek_sembol(kod, ayar):
    """Bir sembol için backtest çalıştır, net (komisyonlu) sonucu döndür."""
    df, durum = veri_al(kod, gun=max(ayar["gun"], 400),
                        min_gun=ayar["min_gun"], aralik=ayar["aralik"])
    if df is None or len(df) < BASLANGIC_GUN + 20:
        return None

    sektor = KOD_SEKTOR.get(kod, "Diger")
    r = backtest_calistir(df, ayar, analiz_bypass, sektor,
                          baslangic_gun=BASLANGIC_GUN)
    if not r or r.get("islem_sayisi", 0) == 0:
        return None

    n = r["islem_sayisi"]
    brut_ort = r["ort_getiri"]                 # işlem başına ortalama ham getiri (%)
    net_ort  = brut_ort - MALIYET_RT           # komisyon düşülmüş ortalama
    # Yaklaşık net bileşik getiri (ortalama üzerinden — şeffaflık için brüt de raporlanır)
    net_bilesik = ((1 + net_ort / 100) ** n - 1) * 100

    # Test penceresi (işlem günü) ve aynı pencerede mevduatın getirisi
    aktif_gun = max(1, len(df) - BASLANGIC_GUN - 5)
    mevduat_pencere = ((1 + MEVDUAT_YILLIK) ** (aktif_gun / ISLEM_GUNU) - 1) * 100

    return {
        "kod": kod, "sektor": sektor, "islem": n,
        "basari": r["basari_pct"], "brut": r["toplam_bilesik"],
        "net": net_bilesik, "mevduat": mevduat_pencere,
        "yener": net_bilesik > mevduat_pencere,
        "aktif_gun": aktif_gun,
    }


def main():
    ayar = VADE_AYAR[VADE_KEY]
    print(f"Backtest başlıyor — vade: {ayar['ad']} | maliyet: %{MALIYET_RT} "
          f"gidiş-dönüş | eşik: yıllık %{int(MEVDUAT_YILLIK*100)} mevduat")

    semboller = list(KOD_SEKTOR.keys())
    sonuclar = []
    for i, kod in enumerate(semboller, 1):
        try:
            s = tek_sembol(kod, ayar)
            if s:
                sonuclar.append(s)
                bayrak = "✓ yener" if s["yener"] else "✗ yenemez"
                print(f"[{i}/{len(semboller)}] {kod}: {s['islem']} işlem, "
                      f"net %{s['net']:.1f} vs mevduat %{s['mevduat']:.1f} → {bayrak}")
            else:
                print(f"[{i}/{len(semboller)}] {kod}: yeterli işlem yok, atlandı")
        except Exception as e:
            print(f"[{i}/{len(semboller)}] {kod}: HATA {e}")

    yaz_rapor(sonuclar, ayar)


def yaz_rapor(sonuclar, ayar):
    """BACKTEST_SONUC.md üret."""
    bugun = datetime.date.today().isoformat()
    satirlar = []
    satirlar.append("# APEX Backtest Sonucu — Mevduat Kıyası\n")
    satirlar.append(f"_Oluşturulma: {bugun} · Vade: {ayar['ad']} · "
                    f"Maliyet: %{MALIYET_RT} gidiş-dönüş · "
                    f"Eşik: yıllık %{int(MEVDUAT_YILLIK*100)} mevduat_\n")

    if not sonuclar:
        satirlar.append("\n**Hiç işlem üretilemedi.** Veri çekilemedi ya da "
                        "strateji sinyal vermedi. (CI'da ağ/veri kaynağını kontrol et.)\n")
        _kaydet(satirlar)
        return

    # Portföy (eşit ağırlık) ortalamaları
    n = len(sonuclar)
    ort_net     = sum(s["net"] for s in sonuclar) / n
    ort_mevduat = sum(s["mevduat"] for s in sonuclar) / n
    yenen       = sum(1 for s in sonuclar if s["yener"])
    edge_var    = ort_net > ort_mevduat

    satirlar.append("\n## Özet (dürüst)\n")
    satirlar.append(f"- Test edilen sembol: **{n}**\n")
    satirlar.append(f"- Mevduatı yenen sembol: **{yenen}/{n}** "
                    f"(%{yenen/n*100:.0f})\n")
    satirlar.append(f"- Portföy ort. NET getiri: **%{ort_net:.1f}**\n")
    satirlar.append(f"- Aynı pencerede mevduat: **%{ort_mevduat:.1f}**\n")
    if edge_var:
        satirlar.append(f"- **SONUÇ: Strateji mevduatı yeniyor "
                        f"(+%{ort_net-ort_mevduat:.1f} fark).** Edge sinyali VAR — "
                        f"ileri doğrulama gerek (out-of-sample, daha çok pencere).\n")
    else:
        satirlar.append(f"- **SONUÇ: Strateji mevduatı YENEMİYOR "
                        f"({ort_net-ort_mevduat:+.1f} puan geride).** "
                        f"Kanıtlanmış edge YOK — parametre ayarı değil, "
                        f"strateji ailesi sorunu.\n")

    # Tablo
    satirlar.append("\n## Sembol Bazında\n")
    satirlar.append("| Kod | Sektör | İşlem | Başarı % | Brüt % | NET % | Mevduat % | Sonuç |\n")
    satirlar.append("|---|---|---:|---:|---:|---:|---:|:--:|\n")
    for s in sorted(sonuclar, key=lambda x: x["net"], reverse=True):
        ok = "✓" if s["yener"] else "✗"
        satirlar.append(f"| {s['kod']} | {s['sektor']} | {s['islem']} | "
                        f"{s['basari']:.0f} | {s['brut']:.1f} | {s['net']:.1f} | "
                        f"{s['mevduat']:.1f} | {ok} |\n")

    satirlar.append("\n---\n_NET getiri yaklaşıktır (işlem başına ortalama "
                    "üzerinden komisyon düşülmüştür); brüt sütunu ham bileşik "
                    "getiridir. Maliyet/eşik varsayımları runner başında "
                    "değiştirilebilir._\n")
    _kaydet(satirlar)


def _kaydet(satirlar):
    with open("BACKTEST_SONUC.md", "w", encoding="utf-8") as f:
        f.write("".join(satirlar))
    print("BACKTEST_SONUC.md yazıldı.")


if __name__ == "__main__":
    main()
