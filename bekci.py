# -*- coding: utf-8 -*-
"""
bekci.py — APEX gece bekcisi (saglik kontrolu)

FELSEFE (CLAUDE.md ile uyumlu):
  • Bekci TESHIS koyar, TEDAVI etmez. Kod yazmaz, dosya silmez, tahmin uretmez.
  • Bulgu yoksa: Telegram'a tek satir "yesil" — gurultu yok.
  • Bulgu varsa: GitHub'a "bekci" etiketli TEK issue acar (spam korumasi) ve
    @claude'a "kok nedeni bul, minimal duzelt, test et, PR ac" gorevini birakir.
    Merge karari daima insanda (CLAUDE.md §3, §5).
  • Sir yok: token/telegram env'i yoksa o adim SESSIZCE atlanir, cron cokmez.
  • Sadece standart kutuphane + repodaki mevcut bagimliliklar (pandas, requests).

Kontroller:
  a) Sozdizimi (ast) — app.py, veri.py, skor_motoru.py, projektor.py, pages/*.py
  b) Fiyat tazeligi — THYAO, GARAN, AKFGY (veri.veri_al) son bar == son islem gunu mu
  c) CSV butunlugu — ileri_gunluk.csv (bayat mi) + skor_defteri.csv (parse olur mu)

Cikis kodu her zaman 0 (cron temiz cikar).
"""

import ast
import glob
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone, time as _time

# Konsol cp1252 ise emoji print()'i cokertmesin (Actions'ta zaten utf-8).
# Telegram/issue govdesi ayrica utf-8'e encode edildigi icin bundan etkilenmez.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# ── SABITLER ────────────────────────────────────────────────────────
REPO = os.environ.get("GITHUB_REPOSITORY", "ysfyprk3438-debug/bist-tarama")
ETIKET = "bekci"

# Sozdizimi kontrolu yapilacak dosyalar (+ pages/*.py glob ile eklenir)
SOZDIZIMI_DOSYALAR = ["app.py", "veri.py", "skor_motoru.py", "projektor.py"]

# Fiyat tazeligi icin ornek hisseler (BIST'in acik oldugu her gun guncellenmeli)
FIYAT_HISSELER = ["THYAO", "GARAN", "AKFGY"]

# BIST kapanis + veri yerlesim payi: 18:15 TR'den once bugunku bar henuz yok.
KAPANIS_ESIK = _time(18, 15)

# CSV bayatlik esigi (gun)
CSV_BAYAT_GUN = 5

# AKD manuel arsiv bayatlik esigi (gun) — son donem bitisi bu kadar eskiyse besleme gerekli
AKD_ARSIV = "akd_manuel_arsiv.csv"
AKD_BAYAT_GUN = 35

# Seviyeler
KIRMIZI = "KIRMIZI"
SARI = "SARI"


# ── ZAMAN / ISLEM GUNU ──────────────────────────────────────────────
def tr_simdi():
    """TR yerel saati (UTC+3, DST yok) — runner TZ'sinden bagimsiz."""
    return datetime.now(timezone.utc) + timedelta(hours=3)


def _onceki_isgunu(g):
    """g'yi (dahil) geriye dogru en yakin hafta ici gune ceker."""
    while g.weekday() >= 5:  # 5=Cumartesi, 6=Pazar
        g -= timedelta(days=1)
    return g


def beklenen_islem_gunu(simdi=None):
    """
    O an itibariyle verinin GUNCEL sayilmasi gereken son islem gunu.
    - Hafta sonu → onceki Cuma.
    - Hafta ici ama 18:15 TR oncesi → bugunku bar henuz yok, onceki islem gunu.
    - Hafta ici ve 18:15 sonrasi → bugun.
    """
    if simdi is None:
        simdi = tr_simdi()
    g = simdi.date()
    if simdi.weekday() < 5 and simdi.time() < KAPANIS_ESIK:
        g = g - timedelta(days=1)
    return _onceki_isgunu(g)


def isgunu_gecikmesi(son_bar, beklenen):
    """son_bar ile beklenen arasindaki HAFTA ICI gun sayisi (>=0)."""
    if son_bar >= beklenen:
        return 0
    fark = 0
    g = son_bar
    while g < beklenen:
        g += timedelta(days=1)
        if g.weekday() < 5:
            fark += 1
    return fark


# ── KONTROL a) SOZDIZIMI ────────────────────────────────────────────
def kontrol_sozdizimi(bulgular):
    dosyalar = list(SOZDIZIMI_DOSYALAR) + sorted(glob.glob(os.path.join("pages", "*.py")))
    for yol in dosyalar:
        if not os.path.exists(yol):
            bulgular.append({"seviye": KIRMIZI, "alan": "sozdizimi",
                             "mesaj": f"`{yol}` bulunamadi (silinmis/tasinmis?)."})
            continue
        try:
            with open(yol, "r", encoding="utf-8") as f:
                ast.parse(f.read(), filename=yol)
        except SyntaxError as e:
            bulgular.append({"seviye": KIRMIZI, "alan": "sozdizimi",
                             "mesaj": f"`{yol}` sozdizimi hatasi: satir {e.lineno} — {e.msg}"})
        except Exception as e:
            bulgular.append({"seviye": KIRMIZI, "alan": "sozdizimi",
                             "mesaj": f"`{yol}` okunamadi: {type(e).__name__}: {e}"})


# ── KONTROL b) FIYAT TAZELIGI ───────────────────────────────────────
def kontrol_fiyat(bulgular):
    try:
        from veri import veri_al, VADE_AYAR
    except Exception as e:
        bulgular.append({"seviye": KIRMIZI, "alan": "fiyat",
                         "mesaj": f"veri modulu import edilemedi: {type(e).__name__}: {e}"})
        return

    vade = VADE_AYAR["gunluk"]
    beklenen = beklenen_islem_gunu()
    for kod in FIYAT_HISSELER:
        try:
            df, durum = veri_al(kod, gun=vade["gun"], min_gun=vade["min_gun"],
                                aralik=vade["aralik"])
        except Exception as e:
            bulgular.append({"seviye": KIRMIZI, "alan": "fiyat",
                             "mesaj": f"{kod}: veri_al patladi ({type(e).__name__}: {e})."})
            continue
        if df is None or len(df) == 0:
            bulgular.append({"seviye": KIRMIZI, "alan": "fiyat",
                             "mesaj": f"{kod}: fiyat cekilemedi (kaynak: {durum})."})
            continue

        son_bar = df.index[-1].date()
        gecikme = isgunu_gecikmesi(son_bar, beklenen)
        if gecikme >= 2:
            bulgular.append({"seviye": KIRMIZI, "alan": "fiyat",
                             "mesaj": f"{kod}: son bar {son_bar}, beklenen {beklenen} "
                                      f"— {gecikme} islem gunu geride."})
        elif gecikme == 1:
            bulgular.append({"seviye": SARI, "alan": "fiyat",
                             "mesaj": f"{kod}: son bar {son_bar}, beklenen {beklenen} "
                                      f"— 1 islem gunu geride."})
        # gecikme == 0 → sorun yok


# ── KONTROL c) CSV BUTUNLUGU ────────────────────────────────────────
def kontrol_csv(bulgular):
    try:
        import pandas as pd
    except Exception as e:
        bulgular.append({"seviye": KIRMIZI, "alan": "csv",
                         "mesaj": f"pandas import edilemedi: {type(e).__name__}: {e}"})
        return

    # ileri_gunluk.csv — parse + bayatlik
    yol = "ileri_gunluk.csv"
    if not os.path.exists(yol):
        bulgular.append({"seviye": KIRMIZI, "alan": "csv",
                         "mesaj": f"`{yol}` bulunamadi."})
    else:
        try:
            df = pd.read_csv(yol)
            if df.empty or "tarih" not in df.columns:
                bulgular.append({"seviye": KIRMIZI, "alan": "csv",
                                 "mesaj": f"`{yol}` bos veya `tarih` sutunu yok."})
            else:
                son = pd.to_datetime(df["tarih"], errors="coerce").dropna().max()
                if son is None or pd.isna(son):
                    bulgular.append({"seviye": KIRMIZI, "alan": "csv",
                                     "mesaj": f"`{yol}` tarih sutunu okunamadi."})
                else:
                    yas = (tr_simdi().date() - son.date()).days
                    if yas > CSV_BAYAT_GUN:
                        bulgular.append({"seviye": SARI, "alan": "csv",
                                         "mesaj": f"`{yol}` son kayit {son.date()} "
                                                  f"({yas} gun once) — ileri-test log'u durmus olabilir."})
        except Exception as e:
            bulgular.append({"seviye": KIRMIZI, "alan": "csv",
                             "mesaj": f"`{yol}` parse edilemedi: {type(e).__name__}: {e}"})

    # skor_defteri.csv — sadece parse olur mu
    yol = "skor_defteri.csv"
    if not os.path.exists(yol):
        bulgular.append({"seviye": KIRMIZI, "alan": "csv",
                         "mesaj": f"`{yol}` bulunamadi."})
    else:
        try:
            df = pd.read_csv(yol)
            if "tarih" not in df.columns or "hisse" not in df.columns:
                bulgular.append({"seviye": KIRMIZI, "alan": "csv",
                                 "mesaj": f"`{yol}` beklenen sutunlar (tarih/hisse) eksik."})
        except Exception as e:
            bulgular.append({"seviye": KIRMIZI, "alan": "csv",
                             "mesaj": f"`{yol}` parse edilemedi: {type(e).__name__}: {e}"})


# ── KONTROL d) AKD ARSIV TAZELIGI ───────────────────────────────────
def kontrol_akd(bulgular):
    """
    akd_manuel_arsiv.csv son kaydinin tarih_bitis'i AKD_BAYAT_GUN'den eskiyse,
    dosya yoksa veya bossa → SARI 'AKD arsivi bayat — besleme gerekli'.
    Manuel besleme hatti oldugu icin KIRMIZI degil SARI (kritik degil ama hatirlatir).
    """
    try:
        import pandas as pd
    except Exception:
        return  # pandas yoksa kontrol_csv zaten KIRMIZI basar; burada sessiz gec

    yol = AKD_ARSIV
    if not os.path.exists(yol):
        bulgular.append({"seviye": SARI, "alan": "akd",
                         "mesaj": "AKD arsivi bayat — besleme gerekli "
                                  f"(`{yol}` yok)."})
        return
    try:
        df = pd.read_csv(yol)
    except Exception:
        # Bos dosya (sadece baslik / hic satir) pandas'ta EmptyDataError verebilir
        bulgular.append({"seviye": SARI, "alan": "akd",
                         "mesaj": f"AKD arsivi bayat — besleme gerekli (`{yol}` bos)."})
        return
    if df.empty or "tarih_bitis" not in df.columns:
        bulgular.append({"seviye": SARI, "alan": "akd",
                         "mesaj": f"AKD arsivi bayat — besleme gerekli (`{yol}` bos)."})
        return
    son = pd.to_datetime(df["tarih_bitis"], errors="coerce").dropna().max()
    if son is None or pd.isna(son):
        bulgular.append({"seviye": SARI, "alan": "akd",
                         "mesaj": f"AKD arsivi bayat — besleme gerekli "
                                  f"(`{yol}` tarih_bitis okunamadi)."})
        return
    yas = (tr_simdi().date() - son.date()).days
    if yas > AKD_BAYAT_GUN:
        bulgular.append({"seviye": SARI, "alan": "akd",
                         "mesaj": f"AKD arsivi bayat — besleme gerekli "
                                  f"(son donem bitisi {son.date()}, {yas} gun once)."})


# ── TELEGRAM ────────────────────────────────────────────────────────
def telegram_gonder(metin):
    """Telegram'a POST. Env yoksa SESSIZCE atla (stdout'a bas). Cokme yok."""
    token = os.environ.get("TELEGRAM_TOKEN", "")
    chat = os.environ.get("TELEGRAM_CHAT_ID", "")
    if not token or not chat:
        print("[telegram atlandi — env yok]\n" + metin)
        return False
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    veri = json.dumps({"chat_id": chat, "text": metin,
                       "disable_web_page_preview": True}).encode("utf-8")
    istek = urllib.request.Request(url, data=veri, method="POST",
                                   headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(istek, timeout=20) as y:
            return y.getcode() == 200
    except Exception as e:
        print(f"[telegram hatasi: {e}]")
        return False


# ── GITHUB ISSUE ────────────────────────────────────────────────────
def _github_token():
    # PAT varsa tercih et (workflow'da issue izni icin daha guvenilir).
    return os.environ.get("BEKCI_PAT", "") or os.environ.get("GITHUB_TOKEN", "")


def _github_api(method, yol, token, govde=None):
    url = f"https://api.github.com{yol}"
    veri = json.dumps(govde).encode("utf-8") if govde is not None else None
    istek = urllib.request.Request(url, data=veri, method=method, headers={
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "apex-bekci",
        "Content-Type": "application/json",
    })
    with urllib.request.urlopen(istek, timeout=25) as y:
        return json.loads(y.read().decode("utf-8"))


def acik_bekci_issue(token):
    """Acik 'bekci' etiketli ilk issue'yu dondurur (varsa), yoksa None."""
    try:
        sonuc = _github_api("GET", f"/repos/{REPO}/issues?state=open&labels={ETIKET}", token)
        for it in sonuc:
            if "pull_request" not in it:  # PR'lar da issue endpoint'inde gorunur
                return it
        return None
    except Exception as e:
        print(f"[issue listeleme hatasi: {e}]")
        return None


def issue_govdesi(bulgular, tarih):
    kirmizi = [b for b in bulgular if b["seviye"] == KIRMIZI]
    sari = [b for b in bulgular if b["seviye"] == SARI]
    s = []
    s.append(f"Bekci gece saglik kontrolu **{tarih}** tarihinde asagidaki bulgulari tespit etti.")
    s.append("")
    if kirmizi:
        s.append("### 🔴 KIRMIZI (acil)")
        for b in kirmizi:
            s.append(f"- **[{b['alan']}]** {b['mesaj']}")
        s.append("")
    if sari:
        s.append("### 🟡 SARI (dikkat)")
        for b in sari:
            s.append(f"- **[{b['alan']}]** {b['mesaj']}")
        s.append("")
    s.append("---")
    s.append("@claude gorev:")
    s.append("- Kok nedeni bul, **minimal** duzeltmeyi yaz, test et, PR ac.")
    s.append("- **Dosya silme.** Yon/fiyat tahmini ekleme.")
    s.append("- **Merge karari insanda** — sen sadece PR ac, otomatik merge etme.")
    s.append("")
    s.append("_Bekci tarafindan otomatik acildi. Ayni sorun icin tekrar issue acilmaz "
             "(spam korumasi); bu issue kapanana kadar yenisi olusmaz._")
    return "\n".join(s)


def issue_ac(bulgular, tarih):
    """
    Bulgu varsa issue acar. Acik bekci issue'su varsa YENISINI ACMAZ.
    Doner: (issue_url | None, yeni_mi: bool)
    """
    token = _github_token()
    if not token:
        print("[github issue atlandi — token yok]")
        return None, False

    mevcut = acik_bekci_issue(token)
    if mevcut is not None:
        print(f"[acik bekci issue mevcut #{mevcut.get('number')} — yeni acilmadi]")
        return mevcut.get("html_url"), False

    kirmizi_n = sum(1 for b in bulgular if b["seviye"] == KIRMIZI)
    isaret = "🔴" if kirmizi_n else "🟡"
    baslik = f"{isaret} Bekci: {len(bulgular)} bulgu ({tarih})"
    govde = {"title": baslik, "body": issue_govdesi(bulgular, tarih), "labels": [ETIKET]}
    try:
        it = _github_api("POST", f"/repos/{REPO}/issues", token, govde)
        print(f"[issue acildi #{it.get('number')}: {it.get('html_url')}]")
        return it.get("html_url"), True
    except Exception as e:
        print(f"[issue acilamadi: {e}]")
        return None, False


# ── ANA AKIS ────────────────────────────────────────────────────────
def calis():
    bulgular = []
    kontrol_sozdizimi(bulgular)
    kontrol_fiyat(bulgular)
    kontrol_csv(bulgular)
    kontrol_akd(bulgular)

    tarih = tr_simdi().strftime("%d.%m.%Y")

    if not bulgular:
        print(f"Bekci: bulgu yok. 🟢 [{tarih}]")
        telegram_gonder(f"🟢 Bekci ✓ {tarih}")
        return

    # Bulgu var → issue (spam korumali) + Telegram ozet
    kirmizi_n = sum(1 for b in bulgular if b["seviye"] == KIRMIZI)
    sari_n = len(bulgular) - kirmizi_n
    print(f"Bekci: {len(bulgular)} bulgu ({kirmizi_n} kirmizi, {sari_n} sari).")
    for b in bulgular:
        print(f"  - [{b['seviye']}/{b['alan']}] {b['mesaj']}")

    issue_url, _yeni = issue_ac(bulgular, tarih)

    isaret = "🔴" if kirmizi_n else "🟡"
    ozet = [f"{isaret} Bekci {tarih} — {kirmizi_n} kirmizi, {sari_n} sari bulgu."]
    # Ilk birkac bulguyu ekle
    for b in bulgular[:4]:
        ozet.append(f"• [{b['alan']}] {b['mesaj']}")
    if len(bulgular) > 4:
        ozet.append(f"… +{len(bulgular) - 4} bulgu daha")
    if issue_url:
        ozet.append(f"Issue: {issue_url}")
    telegram_gonder("\n".join(ozet))


if __name__ == "__main__":
    try:
        calis()
    except Exception as e:
        # Bekci'nin kendisi cron'u COKERTMEZ; hata basar, temiz cikar.
        print(f"[bekci beklenmeyen hata, cron temiz cikiyor: {type(e).__name__}: {e}]")
    sys.exit(0)
