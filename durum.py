"""
═══════════════════════════════════════════════════════════════
║   APEX — DURUM PANOSU                                         ║
║   Yeni oturumda ÖNCE BUNU + yol_haritasi.py OKU.              ║
═══════════════════════════════════════════════════════════════

Bu dosya projenin KONTROL NOKTASIDIR. Her oturum sonunda güncellenir.
Claude yeni sohbette önce bunu okur → tüm bağlamı ve DÜSTURU alır.
"""

# ══════════════════════════════════════════════════════════════
# DÜSTUR — ASLA ÖDÜN VERİLMEZ (her özellikte uygulanır)
# ══════════════════════════════════════════════════════════════
DUSTUR = [
    "Yön tahmini REDDEDİLDİ: 15 dk gecikmeli perakende veriyle getiri tahmini yazı-tura. Backtest'te kanıtlandı.",
    "Doğrulanmış tek eksen: RİSK YÖNETİMİ — vol-target pozisyon boyutlama. Gerçek BIST'te MaxDD bütçe içinde kaldı.",
    "Hiçbir çıktıda al/sat/tahmin/hedef DİLİ yok. Her okuma yönsüz betim + KENDİ SİCİLİNİ taşır.",
    "Kaçınma lensi ('hangi hisseden kaçınmalı') dürüst ve daha güvenilir — 'hangisini al'dan üstün.",
    "Sistemin hesaplayamadığı şey UYDURULMAZ, açıkça söylenir. Placebo ile beta ayrıştırılır.",
    "Kâr AMACI olabilir ama kâr GARANTİSİ asla verilmez. Kazanç yön bilmekten değil, elemeden + risk asimetrisinden gelir.",
]

# ══════════════════════════════════════════════════════════════
# ŞU AN NEREDEYİZ
# ══════════════════════════════════════════════════════════════
SURUM = "Sanal Borsa v9 · APEX ana panel v4.4"
SON_GUNCELLEME = (
    "pages/01_Sanal_Borsa.py'ye Kural-Tabanlı İşlem Planı Motoru kuruldu: "
    "AL Sinyali (çoklu süzgeç) + Beklenen Değer/Placebo (edge) + kural-tetikli "
    "Oto-simülasyon + Forward-test paneli."
)

SU_AN = {
    "asama": "APEX çok sayfalı, canlı (Streamlit Cloud). Sanal Borsa büyük evrim geçirdi.",
    "siradaki_adim": "Forward-test biriktir (tek gerçek OOS). İstersen oto sonuçlarını ana APEX paneline bağla.",
    "bekleyen_karar": "Yok. Kural motoru + oto test edilip deploy edildi.",
    "onemli_not": "Oto forward-test paneli backtest'in VAADİNİ (beklenen değer) gerçekleşenle yüzleştirir. "
                  "Anlamlı yorum için haftalar-aylar gerçek veri birikmeli. Sabır = tek dürüst yol.",
}

# ══════════════════════════════════════════════════════════════
# MİMARİ (canlı)
# ══════════════════════════════════════════════════════════════
MIMARI = [
    "app.py            — ana APEX 'Güven Kerterizi' (tek dosya, gömülü HTML, 5 mod: Pusula/Havuz/Trade/Defter/Nabız). REPODA STALE, canlı sürüm farklı.",
    "apex_app.html     — ana panelin HTML iskeleti (app.py bellekte yamalar).",
    "pages/01_Sanal_Borsa.py — SANAL BORSA (native Streamlit, gerçek BIST). Kural motoru + oto burada. v9.",
    "kalici.py         — BULUT kalıcılık (Google Sheets 'APEX HAFIZA'). Cüzdan + karar defteri bulutta, cihazdan bağımsız. CANLI.",
    "veri.py           — yfinance veri katmanı: veri_al(kod,gun,min_gun,aralik) → (OHLCV df, durum).",
    "pozisyon.py       — vol-target sizing (doğrulanmış eksen). k=2.5.",
    "temel_veri.json   — 62 hisse temel veri (sıfır transkripsiyon hatası).",
    "makro_guncel.json — yarı-otomatik makro (politika/enflasyon, ~çeyreklik elle).",
    "karar_defteri.csv — MANUEL karar günlüğü (girdim/ekledim/almadım/sattım). Oto BURAYA YAZMAZ (kirletmez).",
    "gunluk_log.py + .github/workflows/gunluk.yml — otonom günlük ileri-test (ileri_gunluk.csv).",
    "projektor.py + projektor.yml — Telegram hikaye pipeline (Sonnet, §6/§2 uyumlu).",
    "ui_app.py         — ÖLÜ MODÜL, asla dokunma.",
]

# ══════════════════════════════════════════════════════════════
# BU OTURUMDA NE YAPTIK (Sanal Borsa v5→v9 evrim)
# ══════════════════════════════════════════════════════════════
BU_OTURUM = [
    "Havuz 8 hisse → BIST100 (KOZAA/KOZAL/KZBGY borsada yok, çıkarıldı → 97 hisse). Paralel veri çekimi (ThreadPool), toleranslı hizalama (ffill/bfill).",
    "Mobil nav düzeltmesi: st.columns dikey yığılması → CSS nowrap ile tek yatay şerit.",
    "Havuz skor önbelleği (aynı gün 97 hisse yeniden hesaplanmaz).",
    "KURAL-TABANLI İŞLEM PLANI MOTORU (yönsüz, sicilli): plan_uret() → durum (Giriş Aktif/Bekle/Risk Filtresi/Kâr-Alma/Stop/Anormal) + destek/direnç (pivot) + ATR + giriş/stop/hedef/R-R + vol-target pozisyon.",
    "SİCİL + BEKLENEN DEĞER: kurulum_analiz() → bu kurulumun bu hissedeki geçmişi (isabet) + expectancy (R, komisyon dahil) + PLACEBO (rastgele girişle karşılaştırma) → EDGE = kurulumun piyasa yönünün ÜSTÜNE kattığı (beta/alpha ayrımı).",
    "AL SİNYALİ kademesi: giriş aktif + sicil>=%52 + R/R>=1.5 + edge>0.03 kesişimi. Çoğu hissede çıkmaz. Her zaman 'n kez oldu, garanti değil' der.",
    "OTO-SİMÜLASYON kural-tetikli: her gün AL sinyali → sanal gir (vol-target, %50 sermaye, yarı nakit); her gün stop/hedef → çık; 21 günde bir vol-target dengele. Gerçek para yok. Her işlem deftere.",
    "FORWARD-TEST paneli (Muhasebe→Otomatik): oto gerçek sonuçları (hedef/stop/isabet/gerçekleşen K/Z) — backtest vaadi ile gerçekleşen yüzleşir. karar_defteri kirletilmedi.",
    "Test: 97 hisse build 48ms, plan/oto NaN sızdırmıyor, expectancy medyanı ~0 (dürüst), oto sim isabet %48 ama R/R asimetrisiyle K/Z pozitif.",
]

# ══════════════════════════════════════════════════════════════
# KURAL MOTORU — İÇ MİMARİ (Sanal_Borsa.py, hızlı hatırlatma)
# ══════════════════════════════════════════════════════════════
MOTOR_HARITASI = [
    "atr_at / _pivotlar / sd_seviye → destek, direnç, ATR (Close-only, pivot w=4 look=70).",
    "plan_uret(k,gun) → durum + giriş/stop/hedef/R-R/pozisyon/neden. Stop=destek-1ATR, Hedef=direnç.",
    "kurulum_analiz(k) → sicil (isabet) + exp + placebo + EDGE (komisyon 2*COM dahil). UFUK_PLAN=10 gün.",
    "al_sinyali(k,gun) → 4 süzgeç kesişimi {olgun, sicil>=52, rr>=1.5, edge>0.03}.",
    "plan_html(k,gun) → hisse sekmesindeki İşlem Planı kartı (AL rozeti + beklenen değer + sicil).",
    "oto_giris_kontrol (günlük) / oto_cikis_kontrol (günlük stop-hedef) / apex_reb (21g vol-target dengele).",
    "Oto pozisyonda stop+hedef GİRİŞ anında sabitlenir (posA[k]['stop'/'hedef']).",
]

# ══════════════════════════════════════════════════════════════
# DEPLOY YÖNTEMİ (Yusuf geliştirici değil — bu akış sabit)
# ══════════════════════════════════════════════════════════════
DEPLOY = [
    "Repo: ysfyprk3438-debug/bist-tarama (main). Streamlit Community Cloud.",
    "Yöntem: GitHub web editör → dosyayı aç → kalem (Edit) → Ctrl+A → Delete → yapıştır → Commit.",
    "Yeni dosya: Add file → Create new file. Workflow (.github/workflows/) SADECE elle (App token yazamaz).",
    "Deploy sonrası: share.streamlit.io → Reboot.",
    "Modül cache: dosya güncellenince '# surum N' yorumunu ARTIR (Streamlit re-import).",
    "app.py 1. satırı DAİMA '# -*- coding: utf-8 -*-' (shebang yok — yapıştırma kırıyor).",
    "Doğrulama: mobil ekran görüntüsü.",
]

# ══════════════════════════════════════════════════════════════
# SIRADAKİ HEDEFLER
# ══════════════════════════════════════════════════════════════
SONRAKI = [
    "Forward-test accumulation — tek gerçek OOS. Sabır. Oto paneldeki edge olgunlaşınca gerçek mi beta mı BELLİ olur.",
    "İstersen: oto forward-test sonuçlarını ana APEX paneline (Nabız/Defter) bağla — ölç, uydurma.",
    "Doğrulanabilir makro oto-kaynak (TCMB coğrafi bloklu, OECD kırılgan) — bulunursa cron'a ekle.",
    "Karar Günlüğü outcome resolution (placebo baz %50; %42 altı ters-seçim uyarısı).",
    "ForInvest AKD/takas manuel arşiv besleme (yinelenen açık kalem).",
]


def durum_metni():
    s = ["APEX — DURUM", "=" * 45, f"\nSÜRÜM: {SURUM}", f"{SON_GUNCELLEME}\n"]
    s.append("DÜSTUR:")
    for d in DUSTUR:
        s.append(f"  • {d}")
    s.append(f"\nŞU AN: {SU_AN['asama']}")
    s.append(f"SIRADAKİ: {SU_AN['siradaki_adim']}")
    s.append(f"NOT: {SU_AN['onemli_not']}")
    s.append("\nSONRAKİ HEDEFLER:")
    for h in SONRAKI:
        s.append(f"  → {h}")
    return "\n".join(s)


if __name__ == "__main__":
    print(durum_metni())
