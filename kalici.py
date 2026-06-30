# surum 1
"""
═══════════════════════════════════════════════════════════════
KALICI — Cihazdan Bağımsız Bulut Kalıcılık (Google Sheets)
═══════════════════════════════════════════════════════════════
APEX'in tek hafıza omurgası. Cüzdan, normal taraf, ne varsa
buradan kalıcı olur — telefon, laptop, hangi cihazdan açarsan aç
AYNI veriyi görürsün. Streamlit konteyneri yeniden kurulsa,
uygulama aylarca uyusa bile veri Google Sheet'te durur.
Sen silmedikçe / sıfırlamadıkça gitmez.

Mantık:
- Tek Google Sheet. İçinde iki çalışma sayfası:
    * "apex_durum"  → makine: anahtar | veri_json | guncelleme   (gerçek kaynak)
    * "cuzdan_ozet" → insan : telefonda gözle okuyabileceğin tablo (ayna)
- Her şey bir ANAHTAR altında JSON olarak saklanır.
    yukle("sanal_borsa", varsayilan)  →  veriyi getirir
    kaydet("sanal_borsa", durum)      →  veriyi yazar
    sil("sanal_borsa")                →  sıfırlar
- Bağlantı yoksa (secrets girilmemişse) çökmez: yerel dosyaya
  yazar ve BULUT_AKTIF=False olur → arayüz uyarı gösterebilir.

Kurulum (bir kez, laptoptan): REHBER_KALICILIK.md
"""

import json
import datetime
import os

# Bağlantı durumu — arayüz "buluttayım / yereldeyim" diye bilsin
BULUT_AKTIF = False
SON_HATA = ""

# Çalışma sayfası adları
_MAKINE_SAYFA = "apex_durum"
_OZET_SAYFA = "cuzdan_ozet"
_BASLIK = ["anahtar", "veri_json", "guncelleme"]

# Yerel yedek klasörü (bulut yoksa veya çökerse)
_YEREL_KLASOR = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".kalici_yedek")


# ──────────────────────────────────────────────────────────────
# BAĞLANTI (cache'li — her tıklamada yeniden bağlanmaz)
# ──────────────────────────────────────────────────────────────
def _zaman():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _baglan():
    """gspread istemcisi + spreadsheet. Streamlit cache_resource ile tek sefer."""
    import streamlit as st

    @st.cache_resource(show_spinner=False)
    def _ic():
        import gspread
        from google.oauth2.service_account import Credentials
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]
        bilgi = dict(st.secrets["gcp_service_account"])
        creds = Credentials.from_service_account_info(bilgi, scopes=scopes)
        istemci = gspread.authorize(creds)
        sid = st.secrets["apex_sheet"]["sheet_id"]
        sh = istemci.open_by_key(sid)
        return sh

    return _ic()


def _sayfa(sh, ad, basliklar=None):
    """Çalışma sayfasını getir; yoksa oluştur (+ başlık satırı)."""
    import gspread
    try:
        ws = sh.worksheet(ad)
    except gspread.exceptions.WorksheetNotFound:
        ws = sh.add_worksheet(title=ad, rows=200, cols=max(3, len(basliklar or [])))
        if basliklar:
            ws.append_row(basliklar)  # yeni boş sayfa → 1. satıra başlık
    return ws


def _makine_sayfasi():
    sh = _baglan()
    return _sayfa(sh, _MAKINE_SAYFA, _BASLIK)


# ──────────────────────────────────────────────────────────────
# YEREL YEDEK (bulut yoksa)
# ──────────────────────────────────────────────────────────────
def _yerel_yol(anahtar):
    os.makedirs(_YEREL_KLASOR, exist_ok=True)
    guvenli = "".join(c if c.isalnum() or c in "-_" else "_" for c in anahtar)
    return os.path.join(_YEREL_KLASOR, f"{guvenli}.json")


def _yerel_yukle(anahtar, varsayilan):
    yol = _yerel_yol(anahtar)
    if os.path.exists(yol):
        try:
            with open(yol, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return varsayilan
    return varsayilan


def _yerel_kaydet(anahtar, veri):
    try:
        with open(_yerel_yol(anahtar), "w", encoding="utf-8") as f:
            json.dump(veri, f, ensure_ascii=False)
        return True
    except Exception:
        return False


def _yerel_sil(anahtar):
    yol = _yerel_yol(anahtar)
    if os.path.exists(yol):
        try:
            os.remove(yol)
        except Exception:
            pass


# ──────────────────────────────────────────────────────────────
# GENEL API — uygulamanın kullandığı 3 fonksiyon
# ──────────────────────────────────────────────────────────────
def yukle(anahtar, varsayilan=None):
    """anahtar altındaki veriyi getir. Yoksa varsayilan döner."""
    global BULUT_AKTIF, SON_HATA
    try:
        ws = _makine_sayfasi()
        kayitlar = ws.get_all_records()  # başlık satırını atlar, dict listesi
        BULUT_AKTIF = True
        for r in kayitlar:
            if str(r.get("anahtar", "")) == anahtar:
                ham = r.get("veri_json", "")
                if not ham:
                    return varsayilan
                try:
                    return json.loads(ham)
                except Exception:
                    return varsayilan
        return varsayilan
    except Exception as e:
        BULUT_AKTIF = False
        SON_HATA = str(e)
        return _yerel_yukle(anahtar, varsayilan)


def kaydet(anahtar, veri):
    """anahtar altına veriyi (JSON olarak) yaz. Varsa günceller, yoksa ekler."""
    global BULUT_AKTIF, SON_HATA
    blob = json.dumps(veri, ensure_ascii=False)
    # Tek hücre sınırı 50.000 karakter — pratik cüzdan için fazlasıyla yeter
    if len(blob) > 49000:
        SON_HATA = "Veri tek hücreye sığmayacak kadar büyüdü (>49k karakter)."
    try:
        ws = _makine_sayfasi()
        anahtarlar = ws.col_values(1)  # A sütunu
        satir = None
        for i, a in enumerate(anahtarlar):
            if a == anahtar:
                satir = i + 1  # 1-indeksli
                break
        if satir:
            ws.update_cell(satir, 2, blob)        # B sütunu: veri
            ws.update_cell(satir, 3, _zaman())    # C sütunu: zaman
        else:
            ws.append_row([anahtar, blob, _zaman()], value_input_option="RAW")
        BULUT_AKTIF = True
        # Yerel yedeği de tazele (çift güvence)
        _yerel_kaydet(anahtar, veri)
        return True
    except Exception as e:
        BULUT_AKTIF = False
        SON_HATA = str(e)
        return _yerel_kaydet(anahtar, veri)


def sil(anahtar):
    """anahtarı tamamen kaldır (sıfırlama)."""
    global BULUT_AKTIF, SON_HATA
    try:
        ws = _makine_sayfasi()
        anahtarlar = ws.col_values(1)
        for i, a in enumerate(anahtarlar):
            if a == anahtar:
                ws.delete_rows(i + 1)
                break
        BULUT_AKTIF = True
    except Exception as e:
        BULUT_AKTIF = False
        SON_HATA = str(e)
    _yerel_sil(anahtar)


# ──────────────────────────────────────────────────────────────
# İNSAN-OKUR AYNA — Google Sheet'i telefonda açınca güzel görün
# ──────────────────────────────────────────────────────────────
def tablo_yaz(basliklar, satirlar, sayfa_adi=_OZET_SAYFA):
    """
    'cuzdan_ozet' sayfasını baştan yazar (temizleyip yeniden doldurur).
    basliklar: ["Hisse", "Lot", "Maliyet", ...]
    satirlar : [["AKBNK", 100, 52.3, ...], ...]
    Bulut yoksa sessizce geçer (kritik değil, sadece görsel ayna).
    """
    try:
        sh = _baglan()
        ws = _sayfa(sh, sayfa_adi, basliklar)
        ws.clear()
        govde = [basliklar] + [[("" if h is None else h) for h in s] for s in satirlar]
        ws.append_rows(govde, value_input_option="RAW")
        return True
    except Exception:
        return False
