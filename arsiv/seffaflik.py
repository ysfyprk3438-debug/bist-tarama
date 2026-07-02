"""
═══════════════════════════════════════════════════════════════
ŞEFFAFLIK PANELİ — BIST Para Avcısı v4
═══════════════════════════════════════════════════════════════
Gerçek güven, sistemin "kusursuz" hissettirmesinden DEĞİL, sana karşı
DÜRÜST olmasından doğar. Sana %100 eminmiş gibi davranan sistem, asıl
güvenmemen gereken sistemdir — çünkü borsa belirsizdir.

Bu panel kararı KARA KUTU'dan CAM KUTU'ya çevirir:
  • LEHTE olanlar → kararı destekleyen her faktör
  • ALEYHTE / RİSKLER → asla gizlenmez, hep gösterilir
  • BELİRSİZLİKLER → sistemin bilmediği/emin olmadığı şeyler
  • DÜRÜSTLÜK NOTU → bu karara ne kadar güvenebilirsin (gerçekçi)

Güven, "ne zaman güveneceğini VE ne zaman güvenmeyeceğini" bilmekten
doğar. Bu yüzden bu panel parayla satın alınamayan güveni inşa eder.
"""


def karar_defteri(r):
    """
    Bir hissenin kararının arkasındaki HER ŞEYİ şeffafça açar.
    Dönen: {lehte, aleyhte, belirsiz, dengeli_mi}
    """
    lehte, aleyhte, belirsiz = [], [], []

    # ── TEKNİK PUAN ──
    puan = r.get("puan", 0)
    if puan >= 70:
        lehte.append(("Teknik güç", f"Teknik puan {puan}/100 — göstergeler güçlü hizalı"))
    elif puan <= 45:
        aleyhte.append(("Zayıf teknik", f"Teknik puan {puan}/100 — göstergeler zayıf"))

    # ── AKILLI PARA ──
    sm = r.get("sm", {})
    if sm.get("buyuk_oyuncu"):
        lehte.append(("Büyük oyuncu", "Hacim/akış büyük oyuncu girişine işaret ediyor"))
    if sm.get("skor", 50) >= 70:
        lehte.append(("Para girişi", f"Akıllı para skoru {sm.get('skor')}/100 — alım baskısı"))
    elif sm.get("skor", 50) <= 35:
        aleyhte.append(("Para çıkışı", f"Akıllı para skoru {sm.get('skor')}/100 — satış baskısı"))

    # ── NİYET ──
    niyet = r.get("niyet", {})
    ns = niyet.get("sinif", "NORMAL")
    if ns in ("SESSİZ TOPLAMA", "DİP OLUŞUMU"):
        lehte.append(("Olumlu niyet", f"{ns} — paranın davranışı alım yönlü"))
    elif ns in ("DAĞITIM", "SÜRÜ / ZİRVE", "OLAĞANDIŞI HAREKET"):
        aleyhte.append(("⚠ Tehlikeli niyet", f"{ns} — manipülasyon/tuzak riski, ciddi uyarı"))
    elif ns in ("NORMAL", "BELİRSİZ"):
        belirsiz.append(("Niyet net değil", "Paranın davranışında belirgin desen yok"))

    # ── RÜZGAR ──
    ruzgar = r.get("ruzgar", {})
    rs = ruzgar.get("skor", 0)
    if rs >= 2:
        lehte.append(("Kuyruk rüzgarı", "Borsa + sektör + hisse aynı yönde, rüzgar arkanda"))
    elif rs <= -2:
        aleyhte.append(("⚠ Karşı rüzgar", "Borsa/sektör aleyhte — akıntıya karşı kürek"))
    elif rs == 0:
        belirsiz.append(("Rüzgar yatay", "Borsa/sektör net yön vermiyor"))

    # ── VOLATİLİTE REJİMİ ──
    vol = r.get("volatilite", {})
    if vol.get("rejim") == "FIRTINA":
        aleyhte.append(("Fırtına rejimi", "Yüksek oynaklık — risk büyük, pozisyon küçültüldü"))
    elif vol.get("rejim") == "SAKİN":
        lehte.append(("Sakin rejim", "Düşük oynaklık — kontrollü ortam"))

    # ── KARAKTER / STRATEJİ UYUMU ──
    krk = r.get("karakter", {})
    uyum = krk.get("uyum_skoru", 50)
    if uyum >= 70:
        lehte.append(("Strateji uyumu", krk.get("uyum_yorum", "Sinyal hissenin karakterine uyuyor")))
    elif uyum <= 35:
        aleyhte.append(("⚠ Strateji uyumsuz", krk.get("uyum_yorum", "Sinyal karaktere ters — tuzak riski")))
    if krk.get("hurst", {}).get("karakter") == "RASTGELE":
        belirsiz.append(("Karakter rastgele", "Hisse net trend/salınım göstermiyor (Hurst≈0.5) — kenar belirsiz"))

    # ── HACİM YAPISI ──
    hac = r.get("hacim", {})
    if hac.get("yapi_skoru", 50) >= 70:
        lehte.append(("Güçlü hacim yapısı", "Fiyat değerin üstünde, alıcılar kontrolde"))
    elif hac.get("yapi_skoru", 50) <= 40:
        aleyhte.append(("Zayıf hacim yapısı", "Fiyat değerin altında, satıcılar kontrolde"))

    # ── ZAMAN DİLİMİ ONAYI ──
    ztd = r.get("zaman_onay", {})
    zs = ztd.get("skor", 0) if ztd else 0
    if zs >= 2:
        lehte.append(("Üst zaman dilimi onayı", f"{ztd.get('ust_dilim','haftalık')} trend de yukarı — güçlü teyit"))
    elif zs <= -2:
        aleyhte.append(("⚠ Zaman dilimi çelişkisi", f"{ztd.get('ust_dilim','haftalık')} trend ters — sahte sıçrama olabilir"))

    # ── ALARM ──
    alarm = r.get("alarm", {})
    if alarm.get("var"):
        if alarm.get("yon") in ("pozitif", "firsat"):
            gun = f" (~{alarm['gun']} gün)" if alarm.get("gun") is not None else ""
            lehte.append(("Yaklaşan fırsat", f"{alarm['etiket']}{gun}"))
        elif alarm.get("yon") in ("negatif", "dikkat"):
            aleyhte.append(("⚠ Yaklaşan risk", alarm["etiket"]))

    return {
        "lehte": lehte,
        "aleyhte": aleyhte,
        "belirsiz": belirsiz,
        "lehte_sayi": len(lehte),
        "aleyhte_sayi": len(aleyhte),
        "belirsiz_sayi": len(belirsiz),
    }


def durustluk_notu(r, gecmis_basari=None, gecmis_ornek=0):
    """
    Bu karara NE KADAR güvenebilirsin? Dürüst, gerçekçi değerlendirme.
    Riski saklamaz, belirsizliği itiraf eder.

    gecmis_basari: bu sinyal tipinin geçmiş başarı oranı (None = yeterli veri yok)
    gecmis_ornek: kaç örnekten hesaplandı
    Dönen: {seviye, renk, notlar, sicil_metni}
    """
    notlar = []
    defter = karar_defteri(r)

    # Veri kalitesi
    df = r.get("df_grafik")
    if df is not None and len(df) < 60:
        notlar.append("⚠ Sınırlı veri geçmişi — analiz daha az güvenilir")

    # Çelişen sinyaller
    if defter["aleyhte_sayi"] >= 2 and defter["lehte_sayi"] >= 2:
        notlar.append(f"Karışık tablo: {defter['lehte_sayi']} olumlu, {defter['aleyhte_sayi']} olumsuz faktör çekişiyor")

    # Belirsizlik
    if defter["belirsiz_sayi"] >= 2:
        notlar.append(f"{defter['belirsiz_sayi']} faktör belirsiz — sistem bu yönlerde emin değil")

    # Geçmiş sicil (en önemli dürüstlük göstergesi)
    if gecmis_basari is None or gecmis_ornek < 5:
        sicil_metni = "Bu sinyal tipi için henüz yeterli geçmiş yok — sicil oluşana kadar temkinli ol."
        notlar.append("Geçmiş sicil henüz güvenilir değil (az örnek)")
    else:
        sicil_metni = f"Bu tip sinyal geçmişte %{gecmis_basari:.0f} hedefe ulaştı ({gecmis_ornek} örnek)."

    # ── GENEL GÜVEN SEVİYESİ (dürüst) ──
    karar = r.get("karar", {})
    skor = karar.get("skor", 50)
    aleyhte_var = defter["aleyhte_sayi"] >= 1
    ciddi_uyari = any("⚠" in ad for ad, _ in defter["aleyhte"])

    if ciddi_uyari:
        seviye, renk = "DİKKATLİ OL", "#EF4444"
        notlar.insert(0, "Ciddi bir uyarı var — yüksek skora rağmen riski tartmadan girme")
    elif skor >= 75 and defter["aleyhte_sayi"] == 0 and defter["belirsiz_sayi"] <= 1:
        seviye, renk = "GÜÇLÜ ZEMİN", "#10B981"
        notlar.insert(0, "Faktörlerin çoğu hizalı, ciddi çelişki yok — sağlam zemin")
    elif skor >= 60:
        seviye, renk = "MAKUL", "#F59E0B"
        notlar.insert(0, "Olumlu ama mükemmel değil — gerekçeleri tartarak karar ver")
    else:
        seviye, renk = "ZAYIF", "#94A3B8"
        notlar.insert(0, "Zemin zayıf — acele etme")

    return {
        "seviye": seviye, "renk": renk,
        "notlar": notlar,
        "sicil_metni": sicil_metni,
    }
