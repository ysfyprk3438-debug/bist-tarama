# -*- coding: utf-8 -*-
"""
robot_motor.py — APEX / NOVA paper (sanal) otomatik al-sat motoru.

Her turda: durumu yükle → tarama sonuçlarına göre AL/SAT kararı ver → uygula →
durumu kaydet. Durum tek bir JSON dosyasında tutulur (robot_durum.json), böylece
zamanlanmış görev (cron) her çalıştığında kaldığı yerden devam eder.

Gerçek emir YOKTUR — tamamen sanal. Bildirim Telegram ile yapılır (robot_calistir.py).
"""
import json
import os
import datetime

import payload as pl

DURUM_DOSYA = os.environ.get("ROBOT_DURUM", "robot_durum.json")
KOMISYON = 0.002  # %0.2 alım-satım maliyeti

# Karakter → kaç pozisyon + pozisyon başına bütçe oranı
KARAKTER = {
    "sakin":   {"max_pozisyon": 5,  "poz_yuzde": 0.10, "min_av": 70},
    "dengeli": {"max_pozisyon": 8,  "poz_yuzde": 0.12, "min_av": 62},
    "hircin":  {"max_pozisyon": 12, "poz_yuzde": 0.14, "min_av": 55},
}

VARSAYILAN = {
    "baslangic": 100000.0,
    "nakit": 100000.0,
    "pozisyonlar": {},   # kod -> {lot, maliyet, hedef, stop, tarih}
    "islemler": [],      # kapanan işlemler (geçmiş)
    "karakter": "dengeli",
    "guncelleme": None,
}


def yukle(dosya=None):
    dosya = dosya or DURUM_DOSYA
    if os.path.exists(dosya):
        try:
            with open(dosya, encoding="utf-8") as f:
                return {**VARSAYILAN, **json.load(f)}
        except Exception:
            pass
    return json.loads(json.dumps(VARSAYILAN))


def kaydet(durum, dosya=None):
    dosya = dosya or DURUM_DOSYA
    durum["guncelleme"] = datetime.datetime.now().isoformat(timespec="minutes")
    with open(dosya, "w", encoding="utf-8") as f:
        json.dump(durum, f, ensure_ascii=False, indent=2)
    return dosya


def _puan(u):
    return u.get("av", 0) * 0.6 + pl.win_pct(u) * 0.4


def tur(durum, sonuclar):
    """Bir karar turu. Dönen: (durum, mesajlar[])."""
    msgs = []
    uis = {}
    for r in (sonuclar or []):
        try:
            u = pl.to_ui(r)
            uis[u["tk"]] = u
        except Exception:
            continue

    ayar = KARAKTER.get(durum.get("karakter", "dengeli"), KARAKTER["dengeli"])
    poz = durum["pozisyonlar"]
    bugun = datetime.date.today().isoformat()
    satilan = set()

    # ── 1) SATIŞLAR: hedef / stop / sinyal dönüşü ──
    for kod in list(poz.keys()):
        p = poz[kod]
        u = uis.get(kod)
        fiyat = float(u["px"]) if u else p["maliyet"]
        sat, sebep = False, ""
        if fiyat >= p["hedef"]:
            sat, sebep = True, "hedef 🎯"
        elif fiyat <= p["stop"]:
            sat, sebep = True, "stop 🛡️"
        elif u and u["side"] == "SAT":
            sat, sebep = True, "sinyal ↩️"
        if sat:
            tutar = p["lot"] * fiyat * (1 - KOMISYON)
            kz_pct = (fiyat - p["maliyet"]) / p["maliyet"] * 100 if p["maliyet"] else 0
            kz_tl = p["lot"] * (fiyat - p["maliyet"])
            durum["nakit"] += tutar
            durum["islemler"].append({
                "kod": kod, "al": p["maliyet"], "sat": round(fiyat, 2), "lot": p["lot"],
                "kz_pct": round(kz_pct, 2), "kz_tl": round(kz_tl), "sebep": sebep, "tarih": bugun,
            })
            msgs.append(f"🔴 SAT {kod} @ {fiyat:.2f} · {sebep} · {'+' if kz_pct >= 0 else ''}{kz_pct:.1f}% ({'+' if kz_tl >= 0 else ''}{kz_tl:.0f}₺)")
            satilan.add(kod)
            del poz[kod]

    # ── 2) ALIMLAR: en yüksek puanlı sinyaller, boş slot + nakit varsa ──
    adaylar = [u for u in uis.values()
               if u["side"] == "AL" and u["v"] in ("simdi", "al")
               and u["av"] >= ayar["min_av"] and u["tk"] not in poz and u["tk"] not in satilan]
    adaylar.sort(key=_puan, reverse=True)
    bos = max(0, ayar["max_pozisyon"] - len(poz))
    for u in adaylar[:bos]:
        butce = durum["nakit"] * ayar["poz_yuzde"]
        px = float(u["px"])
        lot = int(butce / (px * (1 + KOMISYON))) if px > 0 else 0
        if lot < 1:
            continue
        tutar = lot * px * (1 + KOMISYON)
        if tutar > durum["nakit"]:
            continue
        durum["nakit"] -= tutar
        poz[u["tk"]] = {"lot": lot, "maliyet": round(px, 2),
                        "hedef": float(u["hedef"]), "stop": float(u["stop"]), "tarih": bugun}
        msgs.append(f"🟢 AL {u['tk']} @ {px:.2f} · {lot} lot · hedef {float(u['hedef']):.2f} / stop {float(u['stop']):.2f}")

    dg = durum.setdefault("deger_gecmis", [])
    dg.append(round(deger(durum, uis)))
    durum["deger_gecmis"] = dg[-250:]
    return durum, msgs


def _risk(dg, baslangic):
    """Sortino, Max Düşüş %, Ulcer Endeksi (equity eğrisinden)."""
    if not dg or len(dg) < 5:
        return None, None, None
    s = [baslangic] + list(dg)
    rets = [(s[i] / s[i - 1] - 1) for i in range(1, len(s)) if s[i - 1]]
    neg = [r for r in rets if r < 0]
    dd = (sum(r * r for r in neg) / len(neg)) ** 0.5 if neg else 1e-9
    mean = sum(rets) / len(rets) if rets else 0.0
    sortino = round(mean / dd * (252 ** 0.5), 2) if dd else 0.0
    peak, mdd, sq = s[0], 0.0, []
    for v in s:
        peak = max(peak, v)
        d = (v - peak) / peak * 100 if peak else 0.0
        mdd = min(mdd, d)
        sq.append(d * d)
    ulcer = round((sum(sq) / len(sq)) ** 0.5, 2) if sq else 0.0
    return sortino, round(abs(mdd), 1), ulcer


def deger(durum, uis=None):
    """Toplam portföy değeri = nakit + açık pozisyonlar."""
    v = durum["nakit"]
    for kod, p in durum["pozisyonlar"].items():
        fiyat = (uis.get(kod, {}).get("px") if uis else None) or p["maliyet"]
        v += p["lot"] * float(fiyat)
    return v


def karne(durum):
    """Özet karne: işlem sayısı, başarı %, toplam K/Z, kendini puanlama (0-10)."""
    isl = durum["islemler"]
    kazanan = [i for i in isl if i.get("kz_pct", 0) >= 0]
    basari = round(100 * len(kazanan) / len(isl)) if isl else 0
    toplam_kz = sum(i.get("kz_tl", 0) for i in isl)
    getiri = sum(i["kz_tl"] for i in isl if i.get("kz_tl", 0) >= 0)
    zarar = sum(i["kz_tl"] for i in isl if i.get("kz_tl", 0) < 0)
    deg = deger(durum)
    toplam_getiri_pct = (deg / durum["baslangic"] - 1) * 100 if durum["baslangic"] else 0
    # kendini puanlama: başarı + getiri katkısı
    skor = max(0.0, min(10.0, basari / 12.0 + max(0, toplam_getiri_pct) / 5.0 + 2.0))
    sortino, mdd, ulcer = _risk(durum.get("deger_gecmis", []), durum["baslangic"])
    return {
        "islem": len(isl), "basari": basari, "toplam_kz": round(toplam_kz),
        "getiri": round(getiri), "zarar": round(zarar),
        "deger": round(deg), "getiri_pct": round(toplam_getiri_pct, 1),
        "skor": round(skor, 1), "nakit": round(durum["nakit"]),
        "acik": len(durum["pozisyonlar"]),
        "sortino": sortino, "mdd": mdd, "ulcer": ulcer,
    }
