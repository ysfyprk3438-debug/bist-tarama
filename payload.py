# -*- coding: utf-8 -*-
"""
payload.py — Gerçek analiz çıktısını (analiz_et 'r' sözlüğü) yeni arayüzün
JS veri modeline çevirir. Arayüz (ui_app_template.html) bu modeli okur.

Hiçbir alan eksik kalsa bile arayüz çökmez: makul varsayılanlar üretilir.
"""
import math

try:
    import seffaflik as sf
except Exception:
    sf = None

# BIST kodu → şirket adı (arayüzde gri alt başlık). Bilinmeyen kod = kodun kendisi.
NAME_MAP = {
    "AKBNK":"Akbank","GARAN":"Garanti BBVA","HALKB":"Halkbank","ISCTR":"İş Bankası C","VAKBN":"VakıfBank",
    "YKBNK":"Yapı Kredi","TSKB":"TSKB","ALBRK":"Albaraka Türk","SKBNK":"Şekerbank","KLNMA":"Kalkınma B.",
    "EUPWR":"Europower","ODAS":"Odaş Elektrik","ENJSA":"Enerjisa","AKSEN":"Aksa Enerji","ZOREN":"Zorlu Enerji",
    "AYEN":"Ayen Enerji","AYDEM":"Aydem Enerji","KCAER":"Kocaer Çelik","CWENE":"CW Enerji","NATEN":"Naturel Enerji",
    "EREGL":"Ereğli Demir Çelik","KRDMD":"Kardemir D","ISDMR":"İskenderun Demir","CEMTS":"Çemtaş","CIMSA":"Çimsa",
    "AFYON":"Afyon Çimento","ARCLK":"Arçelik","VESTL":"Vestel","BFREN":"Bosch Fren","DOAS":"Doğuş Otomotiv",
    "OTKAR":"Otokar","FROTO":"Ford Otosan","TOASO":"Tofaş","TTRAK":"Türk Traktör",
    "ECILC":"EİS Eczacıbaşı","SELEC":"Selçuk Ecza","MPARK":"MLP Sağlık","DEVA":"Deva Holding","ECZYT":"Eczacıbaşı Yatırım",
    "GUBRF":"Gübre Fabrikaları","HEKTS":"Hektaş","PETKM":"Petkim","SASA":"Sasa Polyester","TRCAS":"Turcas Petrol","PRKAB":"Türk Prysmian",
    "BIMAS":"BİM Mağazalar","MGROS":"Migros","SOKM":"Şok Marketler","ULKER":"Ülker","CCOLA":"Coca-Cola İçecek",
    "AEFES":"Anadolu Efes","TATGD":"Tat Gıda","PNSUT":"Pınar Süt","BANVT":"Banvit","DARDL":"Dardanel",
    "TTKOM":"Türk Telekom","TCELL":"Turkcell","ASELS":"Aselsan","NETAS":"Netaş","LOGO":"Logo Yazılım",
    "INDES":"İndeks Bilgisayar","ARENA":"Arena Bilgisayar","DGATE":"Datagate","KAREL":"Karel","SMART":"Smartiks","PAPIL":"Papilon",
    "THYAO":"Türk Hava Yolları","PGSUS":"Pegasus","TAVHL":"TAV Havalimanları","CLEBI":"Çelebi","MAALT":"Marmaris Altınyunus","RYSAS":"Reysaş",
    "EKGYO":"Emlak Konut GYO","ISGYO":"İş GYO","TRGYO":"Torunlar GYO","KLGYO":"Kiler GYO","VKGYO":"Vakıf GYO",
    "SNGYO":"Sinpaş GYO","HLGYO":"Halk GYO","ENKAI":"Enka İnşaat","TKFEN":"Tekfen Holding","GSDHO":"GSD Holding",
    "SAHOL":"Sabancı Holding","KCHOL":"Koç Holding","DOHOL":"Doğan Holding","ALARK":"Alarko Holding","BERA":"Bera Holding",
    "GOLTS":"Göltaş Çimento","ADEL":"Adel Kalemcilik","GESAN":"Girişim Elektrik","MAVI":"Mavi Giyim","BRISA":"Brisa","KARSN":"Karsan","GLYHO":"Global Yatırım",
}


def _f(x, d=0.0):
    try:
        v = float(x)
        if math.isnan(v) or math.isinf(v):
            return d
        return v
    except Exception:
        return d


def _fmt_tl(tl):
    """199600 -> '199.6K', 9000 -> '9.0K', 850 -> '850'."""
    if tl is None:
        return "—"
    a = abs(_f(tl))
    if a >= 1000:
        return f"{_f(tl)/1000:.1f}K"
    return f"{_f(tl):.0f}"


def _name(kod):
    return NAME_MAP.get(kod, kod)


def _teknik_kesisim(r):
    """teknik_olay listesinden altın/ölüm kesişimini bul."""
    for o in (r.get("teknik_olay") or []):
        et = (o.get("etiket") or "")
        tip = (o.get("tip") or "")
        if "altın" in et.lower() or "altin" in tip.lower() or tip == "golden_cross":
            return ("golden", et or "Altın kesişim gerçekleşti")
        if "ölüm" in et.lower() or "olum" in tip.lower() or tip == "death_cross":
            return ("death", et or "Ölüm kesişimi gerçekleşti")
    return (None, None)


def _side_v(r, golden, death, av):
    karar = (r.get("karar") or {}).get("karar", "") or ""
    niyet = (r.get("niyet") or {}).get("sinif", "") or ""
    tehlike = any(x in niyet for x in ("DAĞITIM", "OLAĞANDIŞI", "SÜRÜ"))
    if "UZAK" in karar or tehlike or death:
        return "SAT", "kesinSat"
    # AL tarafı: etiket nihai AV skoruyla TUTARLI olsun (kadran=skor=etiket)
    if av >= 75:
        return "AL", "simdi"
    if av >= 60:
        return "AL", "al"
    return "AL", "izle"


def _zaman(r, side, golden, death, v):
    al = r.get("alarm") or {}
    et = (al.get("etiket") or "")
    gun = al.get("gun")
    bull = any(w in et for w in ("Altın", "Dip", "Destek", "Kırılım", "Boğa"))
    bear = any(w in et for w in ("Ölüm", "Direnç", "Tepe", "Dağıtım", "Ayı"))
    if al.get("var") and et:
        if side == "AL" and not bear:
            return f"{et} · ~{gun}g" if gun else et
        if side == "SAT" and not bull:
            return f"{et} · ~{gun}g" if gun else et
    if side == "SAT":
        return "Şimdi sat — kesişim" if death else "Şimdi sat"
    if golden:
        return "Altın kesişim — şimdi"
    if v == "simdi":
        return "Şimdi al"
    if v == "al":
        return "Yakın takip"
    return "Tetik bekliyor"


def _defter(r):
    """seffaflik.karar_defteri → lehte/aleyhte/belirsiz açıklama listeleri."""
    if sf is None:
        return [], [], []
    try:
        kd = sf.karar_defteri(r)
    except Exception:
        return [], [], []
    def ac(lst):
        out = []
        for it in (lst or []):
            if isinstance(it, (list, tuple)) and len(it) >= 2:
                out.append(str(it[1]))
            else:
                out.append(str(it))
        return out[:4]
    return ac(kd.get("lehte")), ac(kd.get("aleyhte")), ac(kd.get("belirsiz"))


def to_ui(r):
    """Tek bir analiz sonucunu (r) arayüz hisse modeline çevirir."""
    kod = r.get("kod", "—")
    son = _f(r.get("son"))
    karar = r.get("karar") or {}
    guven = r.get("guven") or {}
    sm = r.get("sm") or {}
    niyet = r.get("niyet") or {}
    vol = r.get("volatilite") or {}
    ruz = r.get("ruzgar") or {}
    poz = r.get("pozisyon") or {}

    gk, gtxt = _teknik_kesisim(r)
    golden, death = (gk == "golden"), (gk == "death")
    av = int(karar.get("skor", r.get("puan", 0)) or 0)
    side, v = _side_v(r, golden, death, av)
    zaman = _zaman(r, side, golden, death, v)

    # fiyat geçmişi (grafik) + günlük değişim
    hist = []
    ch = 0.0
    df = r.get("df_grafik")
    try:
        if df is not None and "Close" in df:
            c = df["Close"].dropna()
            hist = [round(float(x), 4) for x in c.tolist()[-60:]]
            if len(hist) >= 2 and hist[-2]:
                ch = (hist[-1] / hist[-2] - 1) * 100
    except Exception:
        hist, ch = [], 0.0

    lehte, aleyhte, belirsiz = _defter(r)

    # listeler
    lists = ["bist"]
    if side == "AL":
        if v in ("simdi", "al"):
            lists.append("kesinAl")
        if v == "simdi":
            lists.append("hemenAl")
        if golden:
            lists.append("altinKesisim")
        if (karar.get("aciliyet", 0) or 0) >= 1 or v == "simdi":
            lists.append("trade")
    else:
        lists.append("kesinSat")
        if "Şimdi sat" in zaman:
            lists.append("hemenSat")
        if any(x in (niyet.get("sinif", "") or "") for x in ("DAĞITIM", "OLAĞANDIŞI", "SÜRÜ")):
            lists.append("manip")

    kesisim = gtxt or (golden and "Altın kesişim gerçekleşti") or (death and "Ölüm kesişimi gerçekleşti") or "MA'lar yakınsıyor"

    return {
        "tk": kod,
        "nm": _name(kod),
        "px": round(son, 2),
        "giris": round(son, 2),
        "ch": round(ch, 2),
        "wh": bool(sm.get("buyuk_oyuncu")),
        "av": av,
        "guven": int(guven.get("yuzde", 0) or 0),
        "rsi": int(_f(r.get("rsi"))),
        "destek": round(_f(r.get("destek")), 2),
        "direnc": round(_f(r.get("direnc")), 2),
        "hedef": round(_f(r.get("hedef")), 2),
        "kz": round(_f(r.get("kazanc_pct")), 1),
        "stop": round(_f(r.get("stop")), 2),
        "ky": round(_f(r.get("kayip_pct")), 1),
        "rr": round(_f(r.get("rr")), 1),
        "ay": round(_f(r.get("donem_getiri")), 1),
        "zaman": zaman,
        "kesisim": kesisim,
        "gerekce": karar.get("gerekce", "") or "",
        "sm": int(sm.get("skor", 0) or 0),
        "smt": sm.get("yorum", "") or "",
        "niyet": niyet.get("sinif", "NORMAL") or "NORMAL",
        "ruzgar": ruz.get("seviye") or ruz.get("yon") or "Nötr",
        "rejim": vol.get("rejim", "NORMAL") or "NORMAL",
        "sektor": r.get("sektor", "") or "",
        "ai": r.get("ai"),
        "lot": int(poz.get("lot", 0) or 0),
        "tutar": _fmt_tl(poz.get("pozisyon_tl")),
        "pf": round(_f(poz.get("pozisyon_yuzde")), 1),
        "mk": _fmt_tl(poz.get("max_kayip_tl")),
        "lehte": lehte,
        "aleyhte": aleyhte,
        "belirsiz": belirsiz,
        "side": side,
        "v": v,
        "lists": lists,
        "hist": hist,
    }


def win_pct(u):
    """Kazanma/isabet % — arayüzdeki JS ile birebir."""
    av, gv = u.get("av", 0), u.get("guven", 0)
    if u.get("side") == "SAT":
        return min(92, max(55, 100 - av + 8))
    return min(93, max(40, round(gv * 0.55 + av * 0.4 + 6)))


def sure_gun(u):
    kz = u.get("kz", 0) or 0
    scalp = "trade" in (u.get("lists") or [])
    return max(1, round(kz / (2.4 if scalp else 1.5)))


def build_sectors(sonuclar):
    """Sektör bazlı ısı: ortalama AV skoru, hisse sayısı, ortalama akıllı para."""
    grup = {}
    for r in (sonuclar or []):
        sek = r.get("sektor") or "Diğer"
        av = (r.get("karar") or {}).get("skor", r.get("puan", 0)) or 0
        sm = (r.get("sm") or {}).get("skor", 0) or 0
        g = grup.setdefault(sek, {"av": 0, "sm": 0, "n": 0})
        g["av"] += av
        g["sm"] += sm
        g["n"] += 1
    out = []
    for sek, g in grup.items():
        n = max(1, g["n"])
        out.append({"sektor": sek, "ort": round(g["av"] / n), "sm": round(g["sm"] / n), "n": g["n"]})
    out.sort(key=lambda x: x["ort"], reverse=True)
    return out


def build_market(sonuclar, xu100=None):
    """Mini piyasa listesi: endeks + en çok hareket edenler. [kod, ad, fiyatStr, değişimNum]"""
    out = []
    if xu100 is not None:
        out.append(["XU100", "BIST 100", "Endeks", round(_f(xu100), 2)])
    # en yüksek av skorlu birkaçı
    sl = sorted(sonuclar, key=lambda x: (x.get("karar") or {}).get("skor", 0), reverse=True)[:5]
    for r in sl:
        u = to_ui(r)
        out.append([u["tk"], u["nm"], f"{u['px']:.2f}", u["ch"]])
    return out


def build_payload(sonuclar, xu100=None):
    """Tam arayüz verisi. Boşsa arayüz kendi demo verisini kullanır."""
    stocks = []
    for r in (sonuclar or []):
        try:
            stocks.append(to_ui(r))
        except Exception:
            continue
    pl = {"stocks": stocks}
    if stocks:
        pl["market"] = build_market(sonuclar, xu100)
        pl["sectors"] = build_sectors(sonuclar)
    return pl
