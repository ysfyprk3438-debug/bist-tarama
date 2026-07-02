# -*- coding: utf-8 -*-
"""
tarama_core.py — Streamlit'ten BAĞIMSIZ tarama çekirdeği.
Hem app.py (canlı arayüz) hem telegram_alarm.py (zamanlanmış görev) bunu kullanır.
"""
from concurrent.futures import ThreadPoolExecutor, as_completed

BIST_SEKTORLER = {
    "🏦 Bankacılık": ['AKBNK','GARAN','HALKB','ISCTR','VAKBN','YKBNK','TSKB','ALBRK','SKBNK','KLNMA'],
    "⚡ Enerji": ['EUPWR','ODAS','ENJSA','AKSEN','ZOREN','AYEN','AYDEM','KCAER','CWENE','NATEN'],
    "🏭 Sanayi": ['EREGL','KRDMD','ISDMR','CEMTS','CIMSA','AFYON','ARCLK','VESTL','BFREN','DOAS','OTKAR','FROTO','TOASO','TTRAK'],
    "💊 Sağlık / Kimya": ['ECILC','SELEC','MPARK','DEVA','ECZYT','GUBRF','HEKTS','PETKM','SASA','TRCAS','PRKAB'],
    "🛒 Perakende / Gıda": ['BIMAS','MGROS','SOKM','ULKER','CCOLA','AEFES','TATGD','PNSUT','BANVT','DARDL'],
    "📡 Teknoloji / Telekom": ['TTKOM','TCELL','ASELS','NETAS','LOGO','INDES','ARENA','DGATE','KAREL','SMART','PAPIL'],
    "✈️ Ulaşım / Turizm": ['THYAO','PGSUS','TAVHL','CLEBI','MAALT','RYSAS'],
    "🏗️ İnşaat / GYO": ['EKGYO','ISGYO','TRGYO','KLGYO','VKGYO','SNGYO','HLGYO','ENKAI','TKFEN','GSDHO'],
    "💼 Holding": ['SAHOL','KCHOL','DOHOL','ALARK','BERA','GOLTS','ADEL','GESAN','MAVI','BRISA','KARSN','GLYHO'],
}
BIST_TUM, KOD_SEKTOR = [], {}
for _sek, _kodlar in BIST_SEKTORLER.items():
    for _k in _kodlar:
        if _k not in KOD_SEKTOR:
            BIST_TUM.append(_k)
            KOD_SEKTOR[_k] = _sek


def tara(vade_key="haftalik", gecmis=None):
    """
    Tam tarama + bağlam zenginleştirme. Streamlit gerektirmez.
    Dönen: (sonuclar:list, xu100:float). Hata/veri yoksa ([], 0.0).
    """
    gecmis = gecmis or []
    try:
        from veri import veri_al, VADE_AYAR
        from analiz import analiz_et
        import piyasa as pi
        import ruzgar as rz
        import strateji as strj
        import psikoloji as psi
        import genislik as gen
        try:
            import ai_model
        except Exception:
            ai_model = None
        try:
            import kalibrasyon as klb
        except Exception:
            klb = None

        ayar = VADE_AYAR.get(vade_key, VADE_AYAR["haftalik"])

        endeks_close, xu100 = None, 0.0
        edf, _ = veri_al("XU100", gun=ayar["gun"], min_gun=ayar["min_gun"], aralik=ayar["aralik"])
        if edf is None:
            edf, _ = veri_al("GARAN", gun=ayar["gun"], min_gun=ayar["min_gun"], aralik=ayar["aralik"])
        if edf is not None and len(edf) >= 2:
            endeks_close = edf["Close"].values
            xu100 = float(edf["Close"].iloc[-1] / edf["Close"].iloc[-2] - 1) * 100
        rejim = "YÜKSELİŞ TRENDİ" if xu100 >= 0 else "DÜŞÜŞ / TEMKİNLİ"
        carpan = 1.0

        def _tek(kod):
            df, _d = veri_al(kod, gun=ayar["gun"], min_gun=ayar["min_gun"], aralik=ayar["aralik"])
            if df is None:
                return None, None
            try:
                gk = gen.genislik_katki(df)
            except Exception:
                gk = None
            r = analiz_et(kod, df, ayar, 100000, carpan, KOD_SEKTOR.get(kod, "Diğer"), endeks_close=endeks_close)
            if r and ai_model is not None:
                try:
                    r["ai"] = ai_model.ai_analiz(df)
                except Exception:
                    pass
            return r, gk

        sonuclar, katkilar = [], []
        with ThreadPoolExecutor(max_workers=8) as ex:
            futs = {ex.submit(_tek, h): h for h in BIST_TUM}
            for f in as_completed(futs):
                try:
                    r, gk = f.result()
                    if gk is not None:
                        katkilar.append(gk)
                    if r:
                        sonuclar.append(r)
                except Exception:
                    pass
        if not sonuclar:
            return [], xu100

        try:
            genislik = gen.genislik_ozeti(katkilar, endeks_pct=xu100)
        except Exception:
            genislik = {"ma200_oran": 50, "yeni_zirve": 0, "yeni_dip": 0}
        try:
            rot = pi.sektor_rotasyon(sonuclar)
        except Exception:
            rot = None
        try:
            pstrat = strj.piyasa_stratejisi(genislik, rejim)
        except Exception:
            pstrat = None
        try:
            psk = psi.korku_acgozluluk(genislik, None, xu100)
        except Exception:
            psk = None

        for r in sonuclar:
            try:
                r["ruzgar"] = rz.ruzgar_hesapla(r, rejim, rot)
            except Exception:
                pass
            try:
                if pstrat is not None:
                    r["strateji"] = strj.strateji_analizi(r, pstrat)
            except Exception:
                pass
            if r.get("karar") and r.get("strateji"):
                try:
                    e_sk = r["karar"]["skor"]
                    h = r["strateji"]["hisse_strateji"]
                    pe = psi.psikoloji_karar_etkisi(psk, h) if psk else {"etki": 0}
                    kal = klb.kalibrasyon_ayari(gecmis, r.get("sinyal")) if klb else {"ayar": 0}
                    r["karar"]["skor"] = max(0, min(100, e_sk + r["strateji"].get("karar_etkisi", 0) + pe.get("etki", 0) + kal.get("ayar", 0)))
                except Exception:
                    pass

        sonuclar.sort(key=lambda x: (x.get("karar") or {}).get("skor", x.get("puan", 0)), reverse=True)
        return sonuclar, xu100
    except Exception:
        return [], 0.0
