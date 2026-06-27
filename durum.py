# -*- coding: utf-8 -*-
"""
═══════════════════════════════════════════════════════════════
║                                                               ║
║   📍 APEX (BİST) — DURUM PANOSU / KONTROL NOKTASI            ║
║   YENİ OTURUMDA ÖNCE BUNU OKU. Tüm bağlam burada.            ║
║                                                               ║
═══════════════════════════════════════════════════════════════

Bu dosya projenin HAFIZASIDIR. Her oturumun sonunda güncellenir.
Yeni bir sohbet açıldığında Claude önce bunu + yol_haritasi.py'yi okur,
böylece geçmiş bağlamı sıfırdan kurmadan kaldığı yerden devam eder.
"""

SURUM = "v5.0 — APEX (komple bakım + dürüstlük hattı)"
SON_GUNCELLEME = "27 Haziran 2026 — komple kod bakımı yapıldı, teşhis çıkarıldı, baseline'a geçiliyor"

# ══════════════════════════════════════════════════════════════
# PROJE KİMLİĞİ (değişmez çerçeve)
# ══════════════════════════════════════════════════════════════
KIMLIK = {
    "ad": "APEX — BIST-100 AI tarama + sanal (paper) ticaret terminali",
    "veri": "15 dk gecikmeli günlük OHLCV (Yahoo birincil + İş Yatırım yedek)",
    "basari_kriteri": "Risk-düzeltilmiş bazda Türk mevduat faizini (~%45 yıllık) yenmek. "
                      "Citadel/Renaissance KIYASI DEĞİL — 15dk gecikme hız-bağımlı stratejileri yapısal olarak dışlar.",
    "max_dd_hedef": "~%1.5 (uzun vade modu)",
    "repo": "github.com/ysfyprk3438-debug/bist-tarama (branch: main)",
    "deploy": "Streamlit Community Cloud (app: arayuz.py mobil native UI) + GitHub Actions cron (NOVA robot + Telegram)",
    "calisma_modu": "Claude proje lideri gibi davranır: 'şu mu bu mu' diye sormaz, "
                    "ne yapılacağını söyler ve ekranda adım adım yönlendirir. Türkçe çalışılır. "
                    "Dürüst, süssüz değerlendirme tercih edilir.",
}

# ══════════════════════════════════════════════════════════════
# ŞU AN NEREDEYİZ
# ══════════════════════════════════════════════════════════════
SU_AN = {
    "asama": "Komple bakım TAMAM → teşhis TAMAM → yeni yol haritası + hafıza yazıldı → "
             "sıradaki: konsolide v1.0 BASELINE'ı kur ve GitHub'a yükle (temel sürüm).",
    "robot": "NOVA cron'da canlı çalışıyor (robot_durum.json). 8 açık pozisyon "
             "(TCELL, TAVHL, KLNMA, DEVA, AKBNK, YKBNK, TRGYO, EKGYO), başlangıç 100.000₺, "
             "portföy ~başabaşa yakın (~99.9k). Komisyon modellenmiş (%0.2).",
    "ui_durustluk": "Mobil şablonda uydurma yeşil sayılar temizleniyor. "
                    "Pas-1 (canlı): winRate→kalibre model olasılığı, sahte emir defteri→dürüst not. "
                    "Pas-2 (HAZIR, deploy bekliyor): 124.500₺ demo bakiye + sahte pozisyonlar → "
                    "gerçek APP.robot verisine bağlandı (renderBalance + renderCuzdan gerçek pozisyonlar).",
    "bekleyen_karar": "Yok — baseline'ı kur.",
}

# ══════════════════════════════════════════════════════════════
# KOMPLE BAKIM TEŞHİSİ (27 Haz 2026) — DÜRÜST
# ══════════════════════════════════════════════════════════════
# Kısa hüküm: Sistem mühendislik olarak olgun ama KANITLANMIŞ EDGE YOK.
# Daha derin kalıp: en dürüst bileşenler canlı karar yolundan DIŞLANMIŞ.
TESHIS = {
    "1_tutarlilik_defekti": (
        "Dürüst motorlar canlı yola bağlı değil. (a) karar.py av_skoru kalibre ML'i "
        "(ai_model) HİÇ kullanmıyor; skor = kural-bazlı güven → gösterge 'AV 91/KESİN AL' "
        "derken ML 'NÖTR %50' diyebiliyor; robot da av'a göre alıyor, yani dürüst ML'i değil "
        "şişmiş kural-skorunu trade ediyor. (b) İki risk motoru: performans.risk_metrikleri "
        "DOĞRU (günlüğe resample + mevduat %45 kıyas) ama UI'yi besleyen robot_motor._risk "
        "YANLIŞ zaman tabanı (günde ~5 örneği günlük sayıp √252) → gösterilen Sortino güvenilmez. "
        "(c) İki öz-puan: oz_puanlama (endeksi yenmeyi ölçer, sağlam) ama UI karne.skor'u "
        "(taban+2 vanity metrik) gösteriyor."
    ),
    "2_yapisal_edge": (
        "EN KRİTİK. Robot, backtest'te negatif Sharpe veren strateji ailesini sadakatle "
        "uyguluyor. Robot temiz uygulayıcı — sorun ona NE trade ettirdiğimiz. Katman eklemek çözmez."
    ),
    "3_backtest_kirik": (
        "backtest.py edge ölçemiyor: analiz_et'teki tazelik filtresi (bugün-son_tarih>10→None) "
        "dilimlenmiş geçmişi öldürüyor + komisyon yok + mevduat eşiği yok. backtest_v2.py var ama "
        "ana backtest.py kırık."
    ),
    "4_sessiz_bozulma": (
        "İş Yatırım fallback'te O=H=L=Close → ATR/destek/direnç/Bollinger çöküyor, uyarı yok. "
        "tarama_core'daki 'except: pass' katman çökmelerini yutuyor → sistem zannettiğinden zayıf "
        "çalışıyor olabilir."
    ),
    "saglam_olan": (
        "ai_model (F1 ile temiz, walk-forward + kalibrasyon, bilmediğinde NÖTR der), seffaflik.py "
        "(aleyhte/belirsiz saklamaz), performans.risk_metrikleri (doğru), cuzdan.py + robot_motor "
        "gerçekçi komisyon, güvenli yukle/kaydet, temiz modüler ayrım. İskelet iyi."
    ),
    "tek_cumle": (
        "Darboğaz kod kalitesi değil: (a) stratejinin kanıtlanmış kenarı yok, (b) olan dürüst "
        "sinyaller (ML, doğru risk metriği, oz_puanlama) karara bağlı değil."
    ),
}

# ══════════════════════════════════════════════════════════════
# SÜRÜM MUTABAKATI (baseline kurarken DİKKAT)
# ══════════════════════════════════════════════════════════════
# Elimizdeki repo ZIP'i birkaç dosyada eski. Baseline = repo ZIP + şu güncellemeler:
SURUM_MUTABAKAT = [
    "ui_app_template.html → 573 satırlık Pas-1+Pas-2 sürümü kullan (repo 572, eski).",
    "ai_model.py → F1 düzeltmeli sürümü kullan (walk-forward sahte sıfır giderildi; repo eski).",
    "ÇÖP TEMİZLE: boşluklu 'ai model.py', 'arayuz kartlar.py', 'bist kartlar.py' workflow/eski kart kalıntısı.",
    "UYARI: Tek tek 'loose' dosya yüklemeleri isim-içerik karışık geliyor — TEK doğru kaynak repo ZIP'i.",
]

# ══════════════════════════════════════════════════════════════
# SIRADAKİ ADIMLAR (öncelik sırasına göre)
# ══════════════════════════════════════════════════════════════
SIRADAKI = [
    "0) BASELINE: repo + yukarıdaki mutabakat → konsolide, hatasız v1.0 temel → GitHub'a yükle. "
    "Bundan sonraki her şey bunun üstüne PARÇA PARÇA biner.",
    "1) Pas-2 cüzdan dosyasını canlıya al (hazır): gerçek 8 pozisyon + portföy değeri görünsün.",
    "2) DÜRÜST YOLU BAĞLA (teşhis #1): (a) av_skoru'na ai_model olasılığını dahil et / göstergeyi "
    "ML ile barıştır; (b) UI'yi robot_motor._risk yerine performans.risk_metrikleri'ne bağla; "
    "(c) karne.skor yerine oz_puanlama'yı göster.",
    "3) BACKTEST'İ ONAR (teşhis #3): analiz_et'e backtest=True (tazelik bypass) + komisyon + "
    "mevduat eşiği → edge'i DÜRÜSTÇE ölçebil. Sonra stratejiyi bu dürüst ölçüye göre yargıla.",
    "4) SESSİZ BOZULMAYI GÖRÜNÜR YAP (teşhis #4): veri-kaynağı/kalite etiketi + katman çökme logu.",
    "5) SUPABASE kalıcılığı: sinyal + robot işlemleri kalıcı kaydedilsin → gerçek doğrulanabilir sicil.",
    "6) Sicil birikince (Katman 1 öz-kalibrasyon): edge yoksa stratejiyi değiştir — "
    "reverse-engineering (ör. Tera Yatırım giriş/çıkış şablonu) veya temel/makro özellik katmanı. "
    "Şu an sistem %100 teknik/fiyat-türevli; 15dk gecikmeli günlük veride en kalabalık, en düşük-edge alan.",
]


def durum_metni():
    s = ["📍 APEX — DURUM", "=" * 50, f"\nSÜRÜM: {SURUM}", f"GÜNCELLEME: {SON_GUNCELLEME}"]
    s.append(f"\nŞU AN: {SU_AN['asama']}")
    s.append("\nTEŞHİS (kısa):\n  " + TESHIS["tek_cumle"])
    s.append("\nSIRADAKİ:")
    for a in SIRADAKI:
        s.append(f"  {a}")
    return "\n".join(s)


if __name__ == "__main__":
    print(durum_metni())
