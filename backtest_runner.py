"""
═══════════════════════════════════════════════════════════════
APEX · DÜRÜST BACKTEST KOŞUCUSU  (v2 — istatistiksel karar)
═══════════════════════════════════════════════════════════════
Tek soruyu dürüstçe yanıtlar:
  "Bu strateji, komisyon düşülünce, mevduatı (~%45/yıl)
   GÜVENİLİR biçimde yeniyor mu?"

v1'den farkı (neden):
  - Karar artık ŞİŞİK 'piyasada-iken yıllık' sayısına bağlı DEĞİL.
    O sayı nakit/boş zamanı saymaz, gerçeği abartır → karar dışı.
  - Karar, TÜM işlemlerin mevduat-üstü getirilerini HAVUZLAYIP
    t-istatistiği ile verilir. Ek olarak sembol-bazlı yayılım da
    raporlanır (edge geniş mi, birkaç sembolden mi geliyor?).
  - Örneklem büyütüldü: tüm liste + daha uzun geçmiş → anlamlı N.

  - Tazelik filtresi backtest=True ile bypass edilir (CANLI YOL DEĞİŞMEZ).
  - Her işleme gidiş-dönüş komisyon uygulanır.
  - Sonuç BACKTEST_SONUC.md olarak yazılır (GitHub'da commit edilir).

GitHub Actions içinde çalışır (internet + canlı veri orada var).
Yerelde de çalışır: python backtest_runner.py
"""

import datetime
import traceback
import numpy as np

# ── Ayarlar ──
VADE_KEY     = "haftalik"   # swing — ana strateji vadesi
FETCH_GUN    = 1500         # uzun geçmiş = çok işlem = anlamlı istatistik (~10-15 dk sürebilir)
BASLANGIC    = 120          # ilk 120 günü ısınma olarak bırak
HISSE_SAYISI = 0            # 0 = TÜM liste; >0 ise ilk N sembol (hız için)
T_ESIK       = 2.0          # havuz t-istatistiği eşiği (~%98 tek yönlü güven)
N_MIN        = 100          # t-istatistiğinin anlamlı olması için min toplam işlem


def _fmt(x, n=2):
    try:
        return f"{x:.{n}f}"
    except Exception:
        return str(x)


def calistir():
    from veri import veri_al, VADE_AYAR
    from analiz import analiz_et
    from backtest import backtest_calistir
    from tarama_core import BIST_TUM, KOD_SEKTOR

    ayar = VADE_AYAR[VADE_KEY]
    kodlar = BIST_TUM if HISSE_SAYISI <= 0 else BIST_TUM[:HISSE_SAYISI]

    satirlar = []        # (kod, durum, r) — her sembol için
    havuz_fazla = []     # TÜM işlemlerin mevduat-üstü getirileri (havuz)
    tum_islem = 0
    tum_kazanan = 0
    test_edilen = 0
    poz_sembol = 0       # ort. mevduat-üstü > 0 olan sembol sayısı

    for idx, kod in enumerate(kodlar, 1):
        try:
            df, _ = veri_al(kod, gun=FETCH_GUN, min_gun=ayar["min_gun"], aralik=ayar["aralik"])
            if df is None or len(df) < BASLANGIC + 25:
                satirlar.append((kod, "veri yetersiz", None))
                print(f"[{idx}/{len(kodlar)}] {kod}: veri yetersiz")
                continue
            r = backtest_calistir(df, ayar, analiz_et,
                                  KOD_SEKTOR.get(kod, "Diğer"), baslangic_gun=BASLANGIC)
            if not r or r.get("islem_sayisi", 0) == 0:
                satirlar.append((kod, "sinyal yok", None))
                print(f"[{idx}/{len(kodlar)}] {kod}: sinyal yok")
                continue
            test_edilen += 1
            tum_islem += r["islem_sayisi"]
            tum_kazanan += r["kazanan"]
            havuz_fazla.extend(r.get("fazla_list", []))
            if r.get("mevduati_yeniyor"):
                poz_sembol += 1
            satirlar.append((kod, "ok", r))
            print(f"[{idx}/{len(kodlar)}] {kod}: {r['islem_sayisi']} işlem, "
                  f"mevduat-üstü ort %{_fmt(r['ort_mevduat_ustu'])}")
        except Exception as e:
            satirlar.append((kod, f"hata: {e}", None))
            print(f"[{idx}/{len(kodlar)}] {kod}: HATA {e}")
            traceback.print_exc()

    # ── HAVUZ İSTATİSTİĞİ (asıl karar) ──
    X = np.asarray(havuz_fazla, dtype=float)
    N = int(X.size)
    mu = float(np.mean(X)) if N else 0.0
    sd = float(np.std(X, ddof=1)) if N > 1 else 0.0
    t  = (mu / (sd / np.sqrt(N))) if (N > 1 and sd > 0) else 0.0
    poz_oran = float(np.mean(X > 0) * 100) if N else 0.0
    genel_basari = (tum_kazanan / tum_islem * 100) if tum_islem else 0.0

    yeterli_n = N >= N_MIN
    edge_var = yeterli_n and (mu > 0) and (t >= T_ESIK)

    # ── RAPOR ──
    L = []
    L.append("# APEX — Dürüst Backtest Sonucu (istatistiksel karar)")
    L.append("")
    L.append(f"_Üretim: {datetime.datetime.now():%Y-%m-%d %H:%M} · vade: {VADE_KEY} · "
             f"komisyon dahil · karar eşiği: havuz t ≥ {T_ESIK} ve N ≥ {N_MIN}_")
    L.append("")
    L.append("## SORU: Strateji mevduatı GÜVENİLİR biçimde yeniyor mu?")
    L.append("")
    if not yeterli_n:
        L.append(f"**KARAR VERİLEMEZ.** Toplam işlem N={N} < {N_MIN}. Örneklem, t-istatistiği için "
                 f"yetersiz. FETCH_GUN'u artır ya da daha çok sembol kullan.")
    elif edge_var:
        L.append(f"**ÖN ELEMEYİ GEÇTİ — ama kesin kanıt DEĞİL.** İşlem başına mevduat-üstü net getiri "
                 f"ortalaması **%{_fmt(mu)}**, havuz t-istatistiği **{_fmt(t,1)}** (N={N}). "
                 f"Mevduat-üstü fark, pozitif yönde istatistiksel olarak ayırt ediliyor.")
        L.append("")
        L.append("> UYARI: t-istatistiği işlemlerin bağımsız olduğunu varsayar; aynı sembolde ardışık "
                 "işlemler ilişkili olabileceği için güveni bir miktar ABARTIR. Ayrıca çoklu-test ve "
                 "backtest seçim yanlılığını düzeltmez. Bu bir ELEME sinyalidir, kanıtlanmış canlı edge "
                 "değil. Sonraki adım: görülmemiş dönemde (out-of-sample) ve başka vadelerde teyit.")
    else:
        L.append(f"**HAYIR — kanıtlanmış edge YOK.** İşlem başına mevduat-üstü ortalama **%{_fmt(mu)}**, "
                 f"havuz t-istatistiği **{_fmt(t,1)}** (N={N}). |t|, eşiğin ({T_ESIK}) altında → fark "
                 f"istatistiksel gürültüden ayırt edilemiyor. Bu, parametre ayarı değil, strateji "
                 f"ailesi sorunudur.")
    L.append("")
    L.append(f"- Test edilen sembol: **{test_edilen}/{len(kodlar)}**")
    L.append(f"- Toplam işlem (havuz N): **{N}**")
    L.append(f"- Mevduat-üstü pozitif olan sembol: **{poz_sembol}/{test_edilen}** "
             f"(yayılım — edge geniş mi, birkaç sembolden mi?)")
    L.append(f"- Mevduatı geçen işlem oranı: **%{_fmt(poz_oran,1)}**")
    L.append(f"- İşlem başı ort. mevduat-üstü net getiri: **%{_fmt(mu)}**")
    L.append(f"- Havuz t-istatistiği: **{_fmt(t,1)}**  (karar eşiği {T_ESIK})")
    L.append(f"- Genel başarı (kazanan/işlem): **%{_fmt(genel_basari,1)}**")
    L.append("")
    L.append("> Not (KARAR DIŞI): Tablodaki 'Yıllık%(ref)' = 'piyasada-iken yıllık' sayısıdır; nakit/boş "
             "zamanı saymadığı için ŞİŞİKTİR ve KARARDA KULLANILMAZ, yalnızca referanstır.")

    # ── Sembol tablosu ──
    L.append("")
    L.append("## Hisse Bazında")
    L.append("")
    L.append("| Hisse | İşlem | Başarı% | Net% | Mevduat-üstü% | Yıllık%(ref) | M-üstü>0? |")
    L.append("|---|---:|---:|---:|---:|---:|:--:|")

    def _key(t3):
        _, _, r = t3
        return r["ort_mevduat_ustu"] if r else -1e9

    for kod, durum, r in sorted(satirlar, key=_key, reverse=True):
        if r is None:
            L.append(f"| {kod} | – | – | – | – | – | _{durum}_ |")
            continue
        ok = "✓" if r.get("mevduati_yeniyor") else "✗"
        L.append(f"| {kod} | {r['islem_sayisi']} | {_fmt(r['basari_pct'],1)} | "
                 f"{_fmt(r['toplam_bilesik'])} | {_fmt(r['ort_mevduat_ustu'])} | "
                 f"{_fmt(r['strateji_yillik'],1)} | {ok} |")

    L.append("")
    L.append("---")
    L.append(f"*Komisyon: işlem başına tek yön ~%0.2 (gidiş-dönüş ~%0.4). Tazelik bypass'ı yalnızca "
             f"backtest=True yolunda — canlı tarama/robot davranışı değişmedi. 'M-üstü>0?' sütunu "
             f"sembol-bazında ort. mevduat-üstü>0 demektir (ZAYIF, tek-sembol N düşük). GERÇEK karar, "
             f"yukarıdaki havuz t-istatistiğidir.*")

    metin = "\n".join(L)
    with open("BACKTEST_SONUC.md", "w", encoding="utf-8") as f:
        f.write(metin)
    print("\n" + metin)
    print("\n>>> BACKTEST_SONUC.md yazıldı.")


if __name__ == "__main__":
    calistir()
