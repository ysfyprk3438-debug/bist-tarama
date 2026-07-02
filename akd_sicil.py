# -*- coding: utf-8 -*-
"""
akd_sicil.py — APEX AKD desen→sicil etiketleyici (bağımsız modül)

FELSEFE (CLAUDE.md + durum.py ile uyumlu):
  • GÖZLEM, kehanet DEĞİL. "Geçmişte bu desenden sonra ne oldu" — betimleme + sicil.
  • YÖN TAHMİNİ YOK. AL/SAT dili YOK. Hedef/getiri vaadi YOK.
  • Her okuma kendi sicilini taşır. İsabet %40–60 ise → gri "≈ yazı-tura".
  • Look-ahead YOK: aracı-kurum deseni dönem SONUNDA bilinir; getiri dönem
    bitişinden İTİBAREN sonraki UFUK işlem günü üzerinden ölçülür.
  • Vadesi dolmamış kayda sonuç YAZILMAZ → "beklemede" (skor_motoru.py mühürleme
    mantığıyla birebir: i_end >= len(seri) ise atla).
  • Uydurma yok: veri yoksa "veri yok"; bilinmeyen alan boş.

Sadece standart kütüphane + veri.py (repodaki mevcut veri katmanı).
"""

import csv
import os
import sys
from datetime import date

# Windows konsolu cp1254 ise ▲/▼/İ print()'i çökertmesin (bekci.py'deki guard).
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

from veri import veri_al

# ── SABİTLER ────────────────────────────────────────────────────────
ARSIV = "akd_manuel_arsiv.csv"              # elle doğrulanmış (insan)
OTO_ARSIV = "akd_oto_arsiv.csv"             # otomatik çekici çıktısı (akd_oto_topla.py)
ARSIVLER = [ARSIV, OTO_ARSIV]               # sicil ikisini de okur (varsa)
UFUK = 10                                   # kurulum vadesi (işlem günü) — skor_motoru ile aynı
CUSTODIAN_ADLARI = {"BofA", "Citi", "Deutsche"}   # saklamacı (custodian) aracı kurumlar
KUCUK_ORNEKLEM = 5                           # bunun altında "yetersiz örneklem" uyarısı

BEKLEMEDE = "beklemede"
VERI_YOK = "veri yok"
YUKARI = "▲"
ASAGI = "▼"


# ── ARŞİV OKUMA ─────────────────────────────────────────────────────
def _float(x):
    """Boş/'—'/bozuk → None; aksi halde float."""
    if x is None:
        return None
    s = str(x).strip()
    if s == "" or s == "—":
        return None
    try:
        return float(s)
    except ValueError:
        return None


def _oku(yol=ARSIV):
    """Manuel AKD arşivini okur. Hisse bazında tarih_bitis'e göre artan sıralı satırlar."""
    try:
        with open(yol, encoding="utf-8") as f:
            satirlar = list(csv.DictReader(f))
    except FileNotFoundError:
        return []
    for r in satirlar:
        r["_ilk5"] = _float(r.get("ilk5_net_lot"))
        r["_alici_pct"] = _float(r.get("lider_alici_pct"))
        r["_cust_lot"] = _float(r.get("custodian_net_lot"))
    satirlar.sort(key=lambda r: (r.get("hisse", ""), r.get("tarih_bitis", "")))
    return satirlar


def _kaynaklari_oku(yollar=ARSIVLER):
    """Bir veya birden çok arşivi okuyup birleştirir. str de kabul eder. Yok olan atlanır."""
    if isinstance(yollar, str):
        yollar = [yollar]
    birlesik = []
    for y in yollar:
        birlesik.extend(_oku(y))
    return birlesik


def _grupla(satirlar):
    """
    {(hisse, donem_tipi): [satır, ...]} — cadence-aware gruplama.
    Günlük oto ile aylık manuel AYNI gruba düşmez; her grup kendi tarih_bitis'ine göre artan.
    (donem_tipi boşsa 'bilinmiyor' etiketiyle yine ayrı tutulur.)
    """
    d = {}
    for r in satirlar:
        anahtar = (r.get("hisse", ""), (r.get("donem_tipi") or "bilinmiyor").strip())
        d.setdefault(anahtar, []).append(r)
    for rows in d.values():
        rows.sort(key=lambda r: r.get("tarih_bitis", ""))
    return d


# ══════════════════════════════════════════════════════════════════
# DESEN TANIMLARI
# Her desen fonksiyonu, arşivden {desen, hisse, capa_tarih} instance listesi üretir.
# capa_tarih = tetikleyen kaydın tarih_bitis'i (sinyalin bilindiği an).
# ══════════════════════════════════════════════════════════════════
def desen_uc_ay_net_alici(kayitlar):
    """A · 'ilk5 3 dönem üst üste net alıcı': ardışık 3 kayıt da ilk5_net_lot > 0
    (aynı kadans içinde — aylık manuel için 3 ay, günlük oto için 3 gün)."""
    out = []
    for (hisse, donem), rows in kayitlar.items():
        for i in range(2, len(rows)):
            uclu = rows[i - 2:i + 1]
            if all((r["_ilk5"] is not None and r["_ilk5"] > 0) for r in uclu):
                out.append({"desen": "ilk5 3 dönem üst üste net alıcı", "hisse": hisse,
                            "donem": donem, "capa_tarih": rows[i]["tarih_bitis"]})
    return out


def desen_custodian_baskin(kayitlar):
    """B · 'custodian tek başına %40+ alıcı': lider_alici bir saklamacı ve payı ≥ %40."""
    out = []
    for (hisse, donem), rows in kayitlar.items():
        for r in rows:
            lider = (r.get("lider_alici") or "").strip()
            pct = r["_alici_pct"]
            if lider in CUSTODIAN_ADLARI and pct is not None and pct >= 40:
                out.append({"desen": "custodian tek başına %40+ alıcı", "hisse": hisse,
                            "donem": donem, "capa_tarih": r["tarih_bitis"]})
    return out


def desen_yon_degisti(kayitlar):
    """C · 'ilk5 net yön değiştirdi (kırmızı→yeşil)': önceki < 0, sonraki > 0."""
    out = []
    for (hisse, donem), rows in kayitlar.items():
        for i in range(1, len(rows)):
            onceki, simdi = rows[i - 1]["_ilk5"], rows[i]["_ilk5"]
            if onceki is not None and simdi is not None and onceki < 0 and simdi > 0:
                out.append({"desen": "ilk5 net yön değiştirdi (kırmızı→yeşil)", "hisse": hisse,
                            "donem": donem, "capa_tarih": rows[i]["tarih_bitis"]})
    return out


# (görünen ad, tespit fonksiyonu) — ad her zaman buradan gelir (boş desende de temiz).
DESENLER = [
    ("ilk5 3 dönem üst üste net alıcı", desen_uc_ay_net_alici),
    ("custodian tek başına %40+ alıcı", desen_custodian_baskin),
    ("ilk5 net yön değiştirdi (kırmızı→yeşil)", desen_yon_degisti),
]


# ══════════════════════════════════════════════════════════════════
# FORWARD-RETURN (skor_motoru.py idiom: tam seri + pozisyon indeksi)
# ══════════════════════════════════════════════════════════════════
_FIYAT_CACHE = {}


def _seri(kod):
    """(close_list, iso_tarih_list) artan; veri yoksa (None, None). Bir kez cache'lenir."""
    if kod in _FIYAT_CACHE:
        return _FIYAT_CACHE[kod]
    try:
        df, _ = veri_al(kod, gun=430, min_gun=120, aralik="1d")
    except Exception:
        df = None
    if df is None or len(df) == 0:
        _FIYAT_CACHE[kod] = (None, None)
        return None, None
    c = [float(x) for x in df["Close"].tolist()]
    t = [str(d)[:10] for d in df.index]
    _FIYAT_CACHE[kod] = (c, t)
    return c, t


def sonraki_getiri(kod, capa_tarih):
    """
    capa_tarih'ten sonraki UFUK işlem günü getirisi.
    Döner: (sonuc, getiri) — sonuc ∈ {▲, ▼, beklemede, veri yok}, getiri float|None.
    Mühürleme: i_end >= len(seri) ise 'beklemede' (skor_motoru.skor_sonuclandir ile birebir).
    """
    c, t = _seri(kod)
    if c is None:
        return VERI_YOK, None
    # capa_tarih'e eşit veya ondan SONRAKİ ilk bar (giriş)
    i0 = None
    for i, gun in enumerate(t):
        if gun >= capa_tarih:
            i0 = i
            break
    if i0 is None:
        return VERI_YOK, None
    i_end = i0 + UFUK
    if i_end >= len(c):
        return BEKLEMEDE, None                 # vade dolmadı → sonuç yazma
    if c[i0] <= 0:
        return VERI_YOK, None
    getiri = c[i_end] / c[i0] - 1.0
    return (YUKARI if getiri > 0 else ASAGI), getiri


def instance_sonucla(inst):
    """Bir instance'a sonuç + getiri iliştirir (kopya döner)."""
    sonuc, getiri = sonraki_getiri(inst["hisse"], inst["capa_tarih"])
    d = dict(inst)
    d["sonuc"] = sonuc
    d["getiri"] = getiri
    return d


# ══════════════════════════════════════════════════════════════════
# SİCİL ÖZETİ
# ══════════════════════════════════════════════════════════════════
def sicil_ozeti(sonuclu_instances):
    """
    Olgunlaşmış (▲/▼) instance'lardan sicil çıkarır.
    Döner: {n, yukari, asagi, ort_yukari_pct, ort_asagi_pct, isabet, etiket}
      • n            : olgunlaşan örneklem (beklemede / veri yok hariç)
      • isabet       : yukari / n  (None eğer n == 0)
      • etiket       : '≈ yazı-tura' (%40–60), 'yetersiz örneklem' (n<5), veya betimleyici
    """
    olgun = [x for x in sonuclu_instances if x["sonuc"] in (YUKARI, ASAGI)]
    n = len(olgun)
    yukari = [x for x in olgun if x["sonuc"] == YUKARI]
    asagi = [x for x in olgun if x["sonuc"] == ASAGI]

    def _ort_pct(xs):
        if not xs:
            return None
        return round(sum(x["getiri"] for x in xs) / len(xs) * 100, 2)

    isabet = (len(yukari) / n) if n else None

    if n == 0:
        etiket = "kayıt yok / hepsi beklemede"
    elif n < KUCUK_ORNEKLEM:
        etiket = f"yetersiz örneklem (n={n}) — sicil anlamsız"
    elif 0.40 <= isabet <= 0.60:
        etiket = "≈ yazı-tura"
    else:
        # 40–60 dışında da yön VAADİ değil — sadece geçmiş dağılımın betimi
        etiket = f"geçmişte {'daha çok ▲' if isabet > 0.60 else 'daha çok ▼'} (gözlem, garanti değil)"

    return {"n": n, "yukari": len(yukari), "asagi": len(asagi),
            "ort_yukari_pct": _ort_pct(yukari), "ort_asagi_pct": _ort_pct(asagi),
            "isabet": (round(isabet, 3) if isabet is not None else None),
            "etiket": etiket}


def tara(yollar=ARSIVLER):
    """Tüm desenleri tarar (manuel + oto arşiv). Döner: [(desen_adi, [sonuclu_instance...], ozet), ...]."""
    kayitlar = _grupla(_kaynaklari_oku(yollar))
    sonuc = []
    for ad, fn in DESENLER:
        instances = [instance_sonucla(i) for i in fn(kayitlar)]
        sonuc.append((ad, instances, sicil_ozeti(instances)))
    return sonuc


# ══════════════════════════════════════════════════════════════════
# KONSOL RAPORU
# ══════════════════════════════════════════════════════════════════
def _getiri_str(g):
    return "—" if g is None else f"%{g * 100:+.1f}"


def rapor(yollar=ARSIVLER):
    if isinstance(yollar, str):
        yollar = [yollar]
    mevcut = [y for y in yollar if os.path.exists(y)]
    s = []
    s.append("═" * 62)
    s.append("AKD SİCİL — gözlem, yön tahmini DEĞİL")
    s.append(f"Kaynak: {', '.join(mevcut) or '(dosya yok)'}  ·  ufuk: {UFUK} işlem günü  ·  "
             f"tarih: {date.today().isoformat()}")
    s.append("Bir desenden SONRA fiyatın ne yaptığının sicili. AL/SAT/hedef YOK.")
    s.append("═" * 62)

    for ad, instances, ozet in tara(yollar):
        s.append("")
        s.append(f"▸ Desen: {ad}")
        if not instances:
            s.append("   (arşivde bu desen hiç tetiklenmedi)")
        for x in instances:
            s.append(f"   {x['hisse']} [{x.get('donem', '—')}] · çapa {x['capa_tarih']} · "
                     f"{x['sonuc']} {_getiri_str(x['getiri'])}")
        s.append(f"   SİCİL → n={ozet['n']} · ▲{ozet['yukari']} / ▼{ozet['asagi']} · "
                 f"isabet={'—' if ozet['isabet'] is None else f'%{ozet['isabet']*100:.0f}'} · "
                 f"[{ozet['etiket']}]")
        if ozet["ort_yukari_pct"] is not None or ozet["ort_asagi_pct"] is not None:
            s.append(f"   ortalama: ▲ {'—' if ozet['ort_yukari_pct'] is None else f'%{ozet['ort_yukari_pct']:+.1f}'}"
                     f" · ▼ {'—' if ozet['ort_asagi_pct'] is None else f'%{ozet['ort_asagi_pct']:+.1f}'}")

    s.append("")
    s.append("─" * 62)
    s.append("Not: 'beklemede' = vade (10 işlem günü) henüz dolmadı, sonuç mühürlenmedi.")
    s.append("İsabet %40–60 → «≈ yazı-tura»: desen yön VERMİYOR. Yatırım tavsiyesi değildir.")
    return "\n".join(s)


if __name__ == "__main__":
    print(rapor())
