# surum 4 — APEX Sanal Borsa: native Streamlit, BULUT kalici cuzdan (Google Sheets, cihazdan bagimsiz)
import os
import json
import math
import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))
import kalici as kl  # bulut kalicilik omurgasi (Google Sheets)
STATE_FILE = ROOT / "cuzdan_durum.json"  # yedek/gecis icin durabilir, artik kullanilmiyor
APEX_ANAHTAR = "sanal_borsa"  # bulutta cuzdanin anahtari

TK_DEF = ["THYAO", "AKBNK", "SASA", "EREGL", "ASELS", "BIMAS", "TUPRS", "FROTO"]
AY = ["Oca", "Sub", "Mar", "Nis", "May", "Haz", "Tem", "Agu", "Eyl", "Eki", "Kas", "Ara"]
SON = 10
REB = 21
DEP_D = 0.45 / 252.0
COM = 0.002

D = {}  # PR, MA, MA50, RSI, idxLvl, N, TK, DLAB

# ---------------- veri ----------------
def _synthetic(n, base, amp, ph, drift):
    a = []
    nw = 0.0
    for i in range(n):
        t = i / (n - 1)
        wave = 1 + amp * math.sin(t * (7 + ph)) + 0.05 * math.sin(t * 23)
        a.append(round(base * wave * (1 + 0.0006 * drift * i) * (1 + 0.01 * math.sin(i / 5.0)), 4))
    return a

def fetch_real(kodlar):
    import pandas as pd
    from veri import veri_al
    seri = {}
    for k in kodlar:
        try:
            df, _ = veri_al(k, gun=430, min_gun=120, aralik="1d")
            if df is not None and len(df) >= 120:
                seri[k] = df["Close"]
        except Exception:
            pass
    if len(seri) < 2:
        return None
    mat = pd.DataFrame(seri).dropna()
    if len(mat) < 120:
        return None
    mat = mat.tail(260)
    kodlar2 = [k for k in kodlar if k in mat.columns]
    PR = [[round(float(v), 4) for v in mat[k].tolist()] for k in kodlar2]
    DLAB = [f"{d.day} {AY[d.month - 1]}" for d in mat.index]
    return {"TK": kodlar2, "PR": PR, "DLAB": DLAB}

def sma(a, w):
    out = []
    for i in range(len(a)):
        s = max(0, i - w + 1)
        seg = a[s:i + 1]
        out.append(sum(seg) / len(seg))
    return out

def rsi_calc(p, per):
    r = [None] * len(p)
    g = l = 0.0
    for i in range(1, per + 1):
        d = p[i] - p[i - 1]
        if d > 0: g += d
        else: l -= d
    ag = g / per; al = l / per
    r[per] = 100 - 100 / (1 + (ag / al if al else 100))
    for i in range(per + 1, len(p)):
        d = p[i] - p[i - 1]
        ag = (ag * (per - 1) + (d if d > 0 else 0)) / per
        al = (al * (per - 1) + (-d if d < 0 else 0)) / per
        r[i] = 100 - 100 / (1 + (ag / al if al else 100))
    return r

def build(data):
    D["TK"] = data["TK"]; D["PR"] = data["PR"]; D["DLAB"] = data["DLAB"]
    D["N"] = len(data["PR"][0]); D["NST"] = len(data["TK"])
    D["MA"] = [sma(px, 20) for px in D["PR"]]
    D["MA50"] = [sma(px, 50) for px in D["PR"]]
    D["RSI"] = [rsi_calc(px, 14) for px in D["PR"]]
    idx = []
    for d in range(D["N"]):
        s = sum(D["PR"][k][d] / D["PR"][k][0] for k in range(D["NST"]))
        idx.append(s / D["NST"])
    D["idxLvl"] = idx
    D["D0"] = max(130, D["N"] - 90)

# ---------------- analiz matematigi ----------------
def vol_at(PX, t):
    rr = [PX[i] / PX[i - 1] - 1 for i in range(max(1, t - 60), t)]
    if not rr: return 0.3
    m = sum(rr) / len(rr)
    return math.sqrt(sum((x - m) ** 2 for x in rr) / len(rr)) * math.sqrt(252)

def crP(k):
    PX, M, o = D["PR"][k], D["MA"][k], []
    for i in range(21, D["N"]):
        d0 = PX[i - 1] - M[i - 1]; d1 = PX[i] - M[i]
        if (d0 <= 0 and d1 > 0) or (d0 >= 0 and d1 < 0): o.append((i, d1 > 0))
    return o

def crM(k):
    a, b, o = D["MA"][k], D["MA50"][k], []
    for i in range(51, D["N"]):
        d0 = a[i - 1] - b[i - 1]; d1 = a[i] - b[i]
        if (d0 <= 0 and d1 > 0) or (d0 >= 0 and d1 < 0): o.append((i, d1 > 0))
    return o

def brK(k, kind):
    PX, o = D["PR"][k], []
    for i in range(21, D["N"]):
        w = PX[i - 20:i]
        if kind == "hi" and PX[i] > max(w): o.append(i)
        if kind == "lo" and PX[i] < min(w): o.append(i)
    return [c for j, c in enumerate(o) if j == 0 or c - o[j - 1] > 3]

def rsi_ev(k):
    R = D["RSI"][k]; up = []; dn = []
    for i in range(15, D["N"]):
        if R[i - 1] is not None and R[i] is not None:
            if R[i - 1] < 70 <= R[i]: up.append(i)
            if R[i - 1] > 30 >= R[i]: dn.append(i)
    return up, dn

def track(k, evs):
    PX = D["PR"][k]; rows = []; conf = 0; tot = 0; cm = []; xm = []
    for (i, d) in evs:
        if i + SON < D["N"]:
            r = (PX[i + SON] / PX[i] - 1) * 100
            ok = (r == 0) or ((r > 0) == (d > 0))
            tot += 1
            if ok: conf += 1; cm.append(abs(r))
            else: xm.append(abs(r))
    hit = round(conf / tot * 100) if tot else 0
    ac = sum(cm) / len(cm) if cm else 0
    ax = sum(xm) / len(xm) if xm else 0
    return {"tot": tot, "hit": hit, "ac": ac, "ax": ax}

def verdict(T):
    if T["tot"] < 6: return ("OLGUNLASMADI", "neu", f"{T['tot']} kez · yeterli veri yok")
    m = round(50 / math.sqrt(T["tot"]))
    if T["hit"] >= 50 + m: return ("OLUMLU", "up", f"%{50 + m} esigini gecti")
    if T["hit"] <= 50 - m: return ("OLUMSUZ", "dn", f"%{50 - m} altina dustu")
    return ("YAZI-TURA", "neu", f"%{50 - m}-%{50 + m} arasi")

def events_dir(k):
    ev = []
    for (i, up) in crP(k): ev.append((i, 1 if up else -1))
    for (i, up) in crM(k): ev.append((i, 1 if up else -1))
    for i in brK(k, "hi"): ev.append((i, 1))
    for i in brK(k, "lo"): ev.append((i, -1))
    up, dn = rsi_ev(k)
    for i in up: ev.append((i, -1))
    for i in dn: ev.append((i, 1))
    return ev

def score_full(k):
    PX = D["PR"][k]; ev = events_dir(k)
    C = Tt = 0; sP = sN = 0.0
    for (i, y) in ev:
        if i + SON < D["N"]:
            r = PX[i + SON] / PX[i] - 1
            Tt += 1
            if y * r >= 0: C += 1; sP += abs(r)
            else: sN += abs(r)
    rawMag = (sP / (sP + sN) * 100) if (sP + sN) else 50
    uyum = 50 + (rawMag - 50) * Tt / (Tt + 10) if Tt else 50
    yon = round(C / Tt * 100) if Tt else 50
    m = max(5, round(50 / math.sqrt(max(Tt, 1))))
    if Tt < 12: band = ("yetersiz", "neu")
    elif uyum >= 50 + m: band = ("okumalar tuttu", "up")
    elif uyum <= 50 - m: band = ("ters", "dn")
    else: band = ("yazi-tura", "neu")
    return {"uyum": uyum, "yon": yon, "Tt": Tt, "m": m, "band": band, "ev": ev}

def reading_defs(k):
    PX = D["PR"][k]; mm = crM(k); pm = crP(k); up, dn = rsi_ev(k)
    hi = brK(k, "hi"); lo = brK(k, "lo")
    pb = []
    for i in range(25, D["N"]):
        ma = D["MA"][k][i]
        if not ma: continue
        near = abs(PX[i] - ma) / ma < 0.006
        ab = any(PX[j] > ma * 1.025 for j in range(i - 5, i))
        if near and ab: pb.append(i)
    pb = [c for j, c in enumerate(pb) if j == 0 or c - pb[j - 1] > 5]
    Dd = []
    def dl(i): return D["DLAB"][min(max(i, 0), D["N"] - 1)]
    if mm:
        son = mm[-1]
        Dd.append(dict(ic="◇", nm=("Altin Kesisim" if son[1] else "Olum Kesisimi"),
                       en=("Golden Cross" if son[1] else "Death Cross"), last=son[0], dt="son: " + dl(son[0]),
                       T=track(k, [(i, 1 if u else -1) for (i, u) in mm]),
                       nedir=("20 gunluk ortalama 50 gunlugun ustune cikti — yakin donem hizlandi." if son[1] else "20 gunluk ortalama 50 gunlugun altina indi — yakin donem zayifladi."),
                       perc=("\"Yukselis basliyor\" diye okunur." if son[1] else "\"Dusus basliyor\" diye okunur.")))
    Dd.append(dict(ic="◯", nm="Fiyatin Ortalamayi Kesmesi", en="Fiyat x 20G",
                   last=(pm[-1][0] if pm else 0), dt=f"{len(pm)} kez",
                   T=track(k, [(i, 1 if u else -1) for (i, u) in pm]),
                   nedir="20G = son 20 gunun ortalama fiyat cizgisi. Fiyat onu yukari/asagi kesti.",
                   perc="\"Yukari kesti = al, asagi = sat\" diye okunur."))
    if up:
        Dd.append(dict(ic="⊕", nm="Asiri Hizli Yukselis", en="RSI > 70", last=up[-1], dt="son: " + dl(up[-1]),
                       T=track(k, [(i, -1) for i in up]),
                       nedir="RSI hiz gostergesi 70 ustu = kisa surede cok hizli yukselmis.",
                       perc="\"Fazla isindi, soluklanabilir\" diye okunur."))
    if dn:
        Dd.append(dict(ic="⊖", nm="Asiri Hizli Dusus", en="RSI < 30", last=dn[-1], dt="son: " + dl(dn[-1]),
                       T=track(k, [(i, 1) for i in dn]),
                       nedir="RSI 30 alti = kisa surede cok hizli dusmus.",
                       perc="\"Fazla soguldu, toparlayabilir\" diye okunur."))
    if pb:
        Dd.append(dict(ic="↩", nm="Ortalamaya Geri Donus", en="Pullback", last=pb[-1], dt="son: " + dl(pb[-1]),
                       T=track(k, [(i, 1) for i in pb]),
                       nedir="Yukselen fiyat geri gelip 20G ortalamaya degdi — soluklandi.",
                       perc="\"Yukselis ortalamayi test ediyor\" diye okunur."))
    if hi:
        Dd.append(dict(ic="△", nm="Yeni 20-Gun Zirvesi", en="20-Day High", last=hi[-1], dt="son: " + dl(hi[-1]),
                       T=track(k, [(i, 1) for i in hi]),
                       nedir="Fiyat son 20 gunun en yuksegini asti.",
                       perc="\"Guc / yukari kirilim\" diye okunur."))
    if lo:
        Dd.append(dict(ic="▽", nm="Yeni 20-Gun Dibi", en="20-Day Low", last=lo[-1], dt="son: " + dl(lo[-1]),
                       T=track(k, [(i, -1) for i in lo]),
                       nedir="Fiyat son 20 gunun en dusugunu kirdi.",
                       perc="\"Zayiflik / asagi kirilim\" diye okunur."))
    Dd.sort(key=lambda r: r["last"], reverse=True)
    return Dd

# ---------------- cuzdan ----------------
def init_state():
    d0 = D.get("D0", 120)
    return dict(day=d0, startDay=d0, cash=0.0, mevduat=0.0, posM={}, posA={}, ledger=[],
                deposited=0.0, withdrawn=0.0, realizedM=0.0, realizedA=0.0, auto=False, started=False,
                depGhost=0.0, naifGhost=0.0, idxUnits=0.0, tab="havuz", acctTab="birlesik", sel=0, msg="")

def price(s, k): return D["PR"][int(k)][min(s["day"], D["N"] - 1)]
def today_pct(s, k):
    d = s["day"]
    return (D["PR"][k][d] / D["PR"][k][d - 1] - 1) * 100 if d > 0 else 0
def pv(s, pos): return sum(p["qty"] * price(s, k) for k, p in pos.items())
def tot_val(s): return s["cash"] + s["mevduat"] + pv(s, s["posM"]) + pv(s, s["posA"])
def idx_ghost(s): return s["idxUnits"] * D["idxLvl"][min(s["day"], D["N"] - 1)]

def logtx(s, **o):
    o["day"] = s["day"]; s["ledger"].insert(0, o)

def deposit(s, a):
    a = float(a or 0)
    if a <= 0: s["msg"] = "Gecerli tutar gir"; return
    s["cash"] += a; s["deposited"] += a; s["depGhost"] += a; s["naifGhost"] += a
    s["idxUnits"] += a / D["idxLvl"][s["day"]]
    if not s["started"]: s["started"] = True; s["startDay"] = s["day"]
    logtx(s, type="Para Yukleme", amt=a, src="-"); s["msg"] = f"{int(a)} yuklendi"

def withdraw(s, a):
    a = float(a or 0)
    if a <= 0 or a > s["cash"]: s["msg"] = "Yetersiz nakit"; return
    s["cash"] -= a; s["withdrawn"] += a
    s["depGhost"] = max(0, s["depGhost"] - a); s["naifGhost"] = max(0, s["naifGhost"] - a)
    s["idxUnits"] = max(0, s["idxUnits"] - a / D["idxLvl"][s["day"]])
    logtx(s, type="Para Cekme", amt=-a, src="-")

def to_deposit(s, a):
    a = float(a or 0)
    if a <= 0 or a > s["cash"]: s["msg"] = "Yetersiz nakit"; return
    s["cash"] -= a; s["mevduat"] += a; logtx(s, type="Mevduata koy", amt=a, src="M"); s["msg"] = f"{int(a)} mevduata kondu"

def from_deposit(s, a):
    a = float(a or 0)
    if a <= 0 or a > s["mevduat"]: s["msg"] = "Mevduat yetersiz"; return
    s["mevduat"] -= a; s["cash"] += a; logtx(s, type="Mevduattan cek", amt=a, src="M")

def _buy(s, pos, k, tl):
    tl = float(tl or 0)
    if tl <= 0: return False
    c = tl * (1 + COM)
    if c > s["cash"] + 1e-6: s["msg"] = "Yetersiz nakit"; return False
    s["cash"] -= c; k = str(k)
    if k not in pos: pos[k] = {"qty": 0.0, "cost": 0.0}
    pos[k]["qty"] += tl / price(s, k); pos[k]["cost"] += tl
    return True

def _sell(s, pos, k, frac, src):
    k = str(k)
    if k not in pos or pos[k]["qty"] <= 0: return None
    q = pos[k]["qty"] * frac; net = q * price(s, k) * (1 - COM); cp = pos[k]["cost"] * frac; pnl = net - cp
    if src == "M": s["realizedM"] += pnl
    else: s["realizedA"] += pnl
    s["cash"] += net; pos[k]["qty"] -= q; pos[k]["cost"] -= cp
    if pos[k]["qty"] < 1e-6: del pos[k]
    return net

def buy_m(s, k, tl):
    if _buy(s, s["posM"], k, tl):
        logtx(s, type="AL", k=int(k), price=price(s, k), amt=-float(tl) * (1 + COM), src="M"); s["msg"] = f"{D['TK'][int(k)]} alindi"

def sell_m(s, k):
    n = _sell(s, s["posM"], k, 1.0, "M")
    if n is not None: logtx(s, type="SAT", k=int(k), price=price(s, k), amt=n, src="M"); s["msg"] = f"{D['TK'][int(k)]} satildi"

def bull(s): return [k for k in range(D["NST"]) if D["PR"][k][s["day"]] > D["MA"][k][s["day"]]]

def apex_reb(s):
    base = s["cash"] + pv(s, s["posA"]); bl = bull(s); tgt = {}
    if bl:
        tw = {}; ss = 0.0
        for k in bl:
            iv = 1 / max(vol_at(D["PR"][k], s["day"]), 0.05); tw[k] = iv; ss += iv
        for k in bl: tgt[str(k)] = base * 0.5 * tw[k] / ss
    for k in list(s["posA"].keys()):
        if k not in tgt: _sell(s, s["posA"], k, 1.0, "A")
    for k, tv in tgt.items():
        cur = s["posA"][k]["qty"] * price(s, k) if k in s["posA"] else 0
        diff = tv - cur
        if diff > 50: _buy(s, s["posA"], k, min(diff, s["cash"] / (1 + COM) - 1))
    logtx(s, type="APEX otomatik dengeledi", amt=0, src="A")

def advance(s, days):
    for _ in range(days):
        if s["day"] >= D["N"] - 1: s["msg"] = "Veri sonu"; break
        if s["mevduat"] > 0: s["mevduat"] *= (1 + DEP_D)
        if s["started"]:
            s["depGhost"] *= (1 + DEP_D)
            b = bull(s)
            if b:
                nr = sum(D["PR"][k][s["day"] + 1] / D["PR"][k][s["day"]] - 1 for k in b) / len(b)
            else:
                nr = DEP_D
            s["naifGhost"] *= (1 + nr)
        s["day"] += 1
        if s["auto"] and s["started"] and (s["day"] - s["startDay"]) % REB == 0: apex_reb(s)

def deltas(s):
    if not s["started"]: return None
    m = tot_val(s)
    return dict(dep=(m / (s["depGhost"] or 1) - 1) * 100,
                naif=(m / (s["naifGhost"] or 1) - 1) * 100,
                idx=(m / (idx_ghost(s) or 1) - 1) * 100)

# ---------------- kalicilik (BULUT — cihazdan bagimsiz) ----------------
def load_state():
    if "apex" in st.session_state:
        return st.session_state["apex"]
    s = kl.yukle(APEX_ANAHTAR, None)   # Google Sheets'ten getir
    if not s or "day" not in s:
        s = init_state()
    if s["day"] > D["N"] - 1: s["day"] = D["N"] - 1
    if s["day"] < 0: s["day"] = D["D0"]
    st.session_state["apex"] = s
    return s

def save_state(s):
    st.session_state["apex"] = s
    kl.kaydet(APEX_ANAHTAR, s)         # Google Sheets'e yaz (kalici)

def _ozet_yaz(s):
    """Google Sheet'te insan-okur ayna (telefonda gozle bak). Best-effort."""
    try:
        basliklar = ["Bolum", "Kod", "Lot", "Guncel", "Deger_TL"]
        satirlar = []
        for etiket, pos in (("Manuel", s.get("posM", {})), ("Otomatik", s.get("posA", {}))):
            for k, p in pos.items():
                kod = D["TK"][int(k)] if D.get("TK") else str(k)
                f = price(s, k)
                satirlar.append([etiket, kod, p.get("qty", 0), round(f, 2), round(p.get("qty", 0) * f)])
        getiri = (tot_val(s) / s["deposited"] - 1) * 100 if s["deposited"] else 0
        satirlar += [
            ["—", "NAKIT", "", "", round(s["cash"])],
            ["—", "MEVDUAT", "", "", round(s["mevduat"])],
            ["—", "YATIRILAN", "", "", round(s["deposited"])],
            ["—", "CEKILEN", "", "", round(s["withdrawn"])],
            ["—", "TOPLAM", "", "", round(tot_val(s))],
            ["—", "GETIRI_%", "", "", round(getiri, 1)],
        ]
        kl.tablo_yaz(basliklar, satirlar)
    except Exception:
        pass

# ---------------- bicim ----------------
def ftl(n): return "₺" + f"{round(n):,}".replace(",", ".")
def fsig(n):
    return ("" if n >= 0 else "−") + "₺" + f"{round(abs(n)):,}".replace(",", ".")
def dl(i): return D["DLAB"][min(max(i, 0), D["N"] - 1)]

# ---------------- HTML ----------------
def sparkline(k, day, color):
    PX = D["PR"][k][max(0, day - 80):day + 1]
    lo = min(PX); hi = max(PX); rng = (hi - lo) or 1
    n = len(PX); pts = []
    for i, v in enumerate(PX):
        x = i / (n - 1) * 150 if n > 1 else 0
        y = 40 - (v - lo) / rng * 40
        pts.append(("M" if i == 0 else "L") + f"{x:.1f} {y:.1f}")
    return f'<svg viewBox="0 0 150 40" preserveAspectRatio="none" style="width:100%;height:40px;opacity:.5"><path d="{" ".join(pts)}" fill="none" stroke="{color}" stroke-width="1"/></svg>'

def chart_svg(k, day):
    PX = D["PR"][k]; MA = D["MA"][k]; MA50 = D["MA50"][k]
    VIS = 84; vs = max(20, day - VIS); ve = day
    W = 372; H = 232; LX = 38; RX = 58; TY = 16; PB = 188
    vis = PX[vs:ve + 1]; lo = min(vis); hi = max(vis); pad = (hi - lo) * 0.08 or 1
    def xs(i): return LX + (i - vs) / (ve - vs) * (W - LX - RX)
    def ys(v): return TY + (hi + pad - v) / ((hi - lo) + 2 * pad) * (PB - TY)
    def P(a):
        d = ""
        for i in range(vs, ve + 1):
            if a[i] is None: continue
            d += ("M" if d == "" else "L") + f"{xs(i):.1f} {ys(a[i]):.1f} "
        return d
    s = [f'<svg viewBox="0 0 {W} {H}" style="width:100%">']
    for q in range(5):
        v = lo + (hi - lo) * q / 4; y = ys(v)
        s.append(f'<line x1="{LX}" y1="{y:.1f}" x2="{W-RX}" y2="{y:.1f}" stroke="rgba(232,228,216,.05)"/><text x="{LX-4}" y="{y+3:.1f}" text-anchor="end" font-family="monospace" font-size="8" fill="#5A616B">{v:.0f}</text>')
    s.append(f'<path d="{P(MA50)}" fill="none" stroke="#6F7A84" stroke-width="1.1" stroke-dasharray="2 3" opacity=".55"/>')
    s.append(f'<path d="{P(MA)}" fill="none" stroke="#E8B84B" stroke-width="1.1" stroke-dasharray="3 3" opacity=".6"/>')
    s.append(f'<path d="{P(PX)}" fill="none" stroke="#E8E4D8" stroke-width="2" stroke-linejoin="round"/>')
    for (i, up) in crP(k):
        if vs <= i <= ve:
            x = xs(i); y = ys(PX[i])
            s.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4.5" fill="rgba(174,180,189,.18)" stroke="#C9CDD3" stroke-width="1.7"/>')
    for (i, up) in crM(k):
        if vs <= i <= ve:
            x = xs(i); y = ys(MA[i])
            s.append(f'<path d="M{x:.1f} {y-5:.1f} L{x+5:.1f} {y:.1f} L{x:.1f} {y+5:.1f} L{x-5:.1f} {y:.1f} Z" fill="rgba(232,184,75,.18)" stroke="#E8B84B" stroke-width="1.7"/>')
    gx = xs(ve)
    items = [dict(ty=ys(PX[ve]), t=ftl(PX[ve]).replace("₺", ""), c="#E8E4D8", b=1),
             dict(ty=ys(MA[ve]), t="20G", c="#E8B84B", b=0),
             dict(ty=ys(MA50[ve]), t="50G", c="#6F7A84", b=0)]
    items.sort(key=lambda o: o["ty"]); cy = TY + 4
    for o in items:
        o["y"] = max(o["ty"], cy); cy = o["y"] + 12
    ov = cy - 4 - PB
    if ov > 0:
        for o in items: o["y"] -= ov
    for o in items:
        s.append(f'<circle cx="{gx:.1f}" cy="{o["ty"]:.1f}" r="{3 if o["b"] else 2.2}" fill="{o["c"]}"/><text x="{gx+6:.1f}" y="{o["y"]+3:.1f}" font-family="monospace" font-size="8" fill="{o["c"]}">{o["t"]}</text>')
    for i in [vs, (vs + ve) // 2, ve]:
        anc = "start" if i == vs else ("end" if i == ve else "middle")
        s.append(f'<text x="{xs(i):.1f}" y="{PB+14:.1f}" text-anchor="{anc}" font-family="monospace" font-size="8" fill="#5A616B">{dl(i)}</text>')
    s.append("</svg>")
    return "".join(s)

def trace_svg(k, day, S, gUp, gLo):
    PX = D["PR"][k]; traj = []
    t = 70
    while t <= day:
        c = tt = 0; sp = sn = 0.0
        for (i, y) in S["ev"]:
            if i + SON <= t:
                r = PX[i + SON] / PX[i] - 1; tt += 1
                if y * r >= 0: c += 1; sp += abs(r)
                else: sn += abs(r)
        if tt >= 4:
            rm = (sp / (sp + sn) * 100) if (sp + sn) else 50
            traj.append((t, 50 + (rm - 50) * tt / (tt + 10)))
        t += 6
    if len(traj) <= 3: return "", None
    us = [p[1] for p in traj]; tmin = min(us); tmax = max(us); tavg = sum(us) / len(us); cur = us[-1]
    W = 336; H = 72; LX = 8; RX = 44; TY = 8; BY = 58
    yMin = min(38, tmin - 3); yMax = max(62, tmax + 3)
    def xT(t): return LX + (t - traj[0][0]) / ((day - traj[0][0]) or 1) * (W - LX - RX)
    def yV(v): return TY + (yMax - v) / (yMax - yMin) * (BY - TY)
    s = [f'<svg viewBox="0 0 {W} {H}" style="width:100%;margin-top:6px">']
    s.append(f'<rect x="{LX}" y="{yV(gUp):.1f}" width="{W-LX-RX}" height="{yV(gLo)-yV(gUp):.1f}" fill="rgba(232,228,216,.045)"/>')
    s.append(f'<line x1="{LX}" y1="{yV(50):.1f}" x2="{W-RX}" y2="{yV(50):.1f}" stroke="rgba(232,228,216,.22)" stroke-dasharray="3 3"/><text x="{W-RX+3}" y="{yV(50)+3:.1f}" font-family="monospace" font-size="8" fill="#5A616B">50</text>')
    s.append(f'<line x1="{LX}" y1="{yV(tavg):.1f}" x2="{W-RX}" y2="{yV(tavg):.1f}" stroke="rgba(232,184,75,.3)" stroke-dasharray="1 3"/><text x="{W-RX+3}" y="{yV(tavg)+3:.1f}" font-family="monospace" font-size="8" fill="rgba(232,184,75,.7)">ruh</text>')
    d = ""
    for j, (tt, u) in enumerate(traj): d += ("M" if j == 0 else "L") + f"{xT(tt):.1f} {yV(u):.1f} "
    fc = "#2DD4BF" if cur >= gUp else ("#EF5B4C" if cur <= gLo else "#C9CDD3")
    s.append(f'<path d="{d}" fill="none" stroke="{fc}" stroke-width="1.6"/><circle cx="{xT(traj[-1][0]):.1f}" cy="{yV(cur):.1f}" r="3" fill="{fc}"/><text x="{xT(traj[-1][0])+5:.1f}" y="{yV(cur)+3:.1f}" font-family="monospace" font-size="8" fill="{fc}" font-weight="600">%{cur:.0f}</text></svg>')
    return "".join(s), dict(tmin=tmin, tmax=tmax, tavg=tavg, cur=cur, m=S["m"])

# kalan HTML uretimi UI icinde (st.markdown). Burada test edilebilir saf parcalar bitti.

# ---------------- ek HTML uretimi ----------------
def durum_html(s, k):
    yvol = vol_at(D["PR"][k], s["day"])
    ortG = (price(s, k) / D["MA"][k][s["day"]] - 1) * 100
    stop = 2 * (yvol / math.sqrt(252)) * 100
    ag = min(0.02 / yvol, 1) * 100
    vlab = "sakin" if yvol < 0.3 else ("orta" if yvol < 0.5 else "sert")
    cu = "up" if ortG >= 0 else "dn"
    return (f'<div class="card"><div class="sec">DURUM · CANLI</div>'
            f'<div class="du"><div class="k">ortalamaya gore</div><div class="v {cu}">{"+%" if ortG>=0 else "−%"}{abs(ortG):.1f}</div></div>'
            f'<div class="du"><div class="k">oynaklik</div><div class="v">{vlab} ~%{yvol*100:.0f}</div></div>'
            f'<div class="du"><div class="k">oynakliga gore agirlik</div><div class="v">%{ag:.1f}</div></div>'
            f'<div class="du"><div class="k">oynaklik stopu</div><div class="v dn">−%{stop:.1f}</div></div></div>')

def uygunluk_html(k, day, S):
    PX = D["PR"][k]; C = Tt = 0; sP = sN = 0.0
    for (i, y) in S["ev"]:
        if i + SON < D["N"]:
            r = PX[i + SON] / PX[i] - 1; Tt += 1
            if y * r >= 0: C += 1; sP += abs(r)
            else: sN += abs(r)
    yon = round(C / Tt * 100) if Tt else 50
    uyum = S["uyum"]; m = S["m"]; gUp = 50 + m; gLo = 50 - m
    if Tt < 12: band = ("yeterli veri yok · guvenme", "neu")
    elif uyum >= gUp: band = ("okumalar gecmiste TUTMUS", "up")
    elif uyum <= gLo: band = ("okumalar TERS tutmus", "dn")
    else: band = ("yazi-tura · okumalara guvenme", "neu")
    h = [f'<div class="card"><div class="sec">PIYASA OKUMASINA UYGUNLUK</div>']
    h.append(f'<div class="usplitrow"><div class="usplit"><span class="big up">%{yon}</span><span class="ul">gerceklesen<br>tuttu</span></div><div class="usep"></div><div class="usplit"><span class="big dn">%{100-yon}</span><span class="ul">gerceklesmeyen<br>tutmadi</span></div></div>')
    h.append(f'<div class="ubar"><div class="st" style="width:{yon}%"></div><div class="sr" style="width:{100-yon}%"></div><div class="thr" style="left:{gLo}%"></div><div class="thr" style="left:{gUp}%"></div></div>')
    h.append('<div class="barlbl"><span>gerceklesen</span><span>gerceklesmeyen</span></div>')
    h.append(f'<div class="karisik">Karisik skor <span class="ksm">(yon + buyukluk, torpulu)</span>: <b class="{band[1]}">~%{uyum:.0f}</b> · <span class="{band[1]}">{band[0]}</span></div>')
    h.append(f'<div class="guven">Guven esigi <span class="ksm">("al" degil)</span>: <b class="up">%{gUp} ustu</b> guvenilir · <b class="dn">%{gLo} alti</b> ters · arasi ≈ yazi-tura.</div>')
    cOlg = cP = cN = cY = cT = 0
    for rd in reading_defs(k):
        cT += 1; v = verdict(rd["T"])
        if v[0] != "OLGUNLASMADI": cOlg += 1
        if v[0] == "OLUMLU": cP += 1
        elif v[0] == "OLUMSUZ": cN += 1
        elif v[0] == "YAZI-TURA": cY += 1
    son = ("Olgun okuma yok — derinlikte de guvenilir yon cikmiyor." if cOlg == 0 else
           ("Olgunlarin agirligi olumlu, yine de garanti degil." if cP > cN else
            ("Olgunlarin agirligi ters tarafta." if cN > cP else "Olgunlar dengeli.")))
    h.append(f'<div class="genel"><span class="glab">GENEL DEGERLENDIRME</span>{cT} okumadan <b>{cOlg} olgun</b>: <b class="up">{cP} olumlu</b> · <b class="dn">{cN} olumsuz</b> · <b class="neu">{cY} yazi-tura</b>. Genel skor <b class="{band[1]}">~%{uyum:.0f}</b>. {son}</div>')
    tsvg, ti = trace_svg(k, day, S, gUp, gLo)
    if tsvg:
        civ = abs(ti["tavg"] - 50) <= ti["m"]
        note = ("Iz 50 (yazi-tura) bandinda — okumalar genelde yon vermez." if civ else "Iz 50 disina oturmus — okumalarin gecmiste karsiligi olmus; ileri-test sinamali.")
        h.append('<div class="genel"><span class="glab">SKOR IZI · HISSENIN RUHU</span></div>' + tsvg)
        h.append(f'<div class="tracetxt">Skor yil boyunca %{ti["tmin"]:.0f}–%{ti["tmax"]:.0f} gezindi, ruhu ~%{ti["tavg"]:.0f} (sari). Su an %{ti["cur"]:.0f}. {note} Basta savrulur, veri biriktikce olgunlasir.</div>')
    h.append("</div>")
    return "".join(h)

def readings_html(k):
    h = ['<div class="card"><div class="sec">GRAFIK OKUMALARI · BU HISSE</div>']
    for r in reading_defs(k):
        T = r["T"]; v = verdict(T)
        h.append(f'<div class="rd"><div class="rdh"><span class="ic">{r["ic"]}</span><span class="nm">{r["nm"]}</span><span class="en">{r["en"]}</span><span class="dt">{r["dt"]}</span></div>')
        h.append(f'<div class="nedir"><span class="lab">Nedir</span> {r["nedir"]}</div>')
        if T["tot"] == 0:
            h.append('<div class="data"><span class="neu">sonuc penceresi dolmadi</span></div>')
        else:
            h.append(f'<div class="data"><span class="yr">SON 1 YIL · SONRAKI {SON} GUN</span><span class="up">gerceklesen %{T["hit"]}</span><span class="dn">gerceklesmeyen %{100-T["hit"]}</span><span class="neu">{T["tot"]} kez</span><span class="sz">tuttugunda ort %{T["ac"]:.1f} · tutmadiginda ort %{T["ax"]:.1f}</span></div>')
            h.append(f'<div class="vbadge"><span class="vlab {v[1]}">{v[0]}</span><span class="vwhy">{v[2]}</span></div>')
        h.append(f'<div class="perc"><span class="lab">Piyasa</span> {r["perc"]}</div></div>')
    h.append("</div>")
    return "".join(h)

def coaching(s):
    dd = deltas(s)
    if not dd:
        return [("◆", "neu", "<b>Basla:</b> Cuzdana sanal para yukle. Sonra hisse al ya da otomatigi ac.")]
    n = []; ret = (tot_val(s) / s["deposited"] - 1) * 100 if s["deposited"] else 0
    if dd["naif"] > 0: n.append(("✓", "up", f'<b>Iyi yondesin.</b> Naif halinden +%{dd["naif"]:.1f} ondesin — risk yonetimi isini yapiyor.'))
    else: n.append(("!", "dn", "<b>Naif halin su an onde.</b> Tek donem; disiplinin degeri kotu gunlerde belli olur."))
    if dd["dep"] < 0: n.append(("⚠", "am", f'<b>Dikkat.</b> Param tumuyle mevduatta dursaydi %{abs(dd["dep"]):.1f} fazlasi olurdu. Daha cok mevduat dusun.'))
    else: n.append(("★", "up", f'<b>Mevduati geciyorsun (+%{dd["dep"]:.1f}).</b> Guzel ama tek donem, riskini koru.'))
    n.append(("◎", "neu", f'Karin varsa sor: piyasa genel yukseldi mi? Oyleyse bu <b>beta</b>. Endekse gore: {"+" if dd["idx"]>=0 else "−"}%{abs(dd["idx"]):.1f}.'))
    n.append(("◆", "neu", "<b>Amac:</b> zengin olmak degil; <b>kaybetmemeyi, disiplini, aldanmamayi</b> ogrenmek."))
    return n

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Archivo:wght@700;800&family=IBM+Plex+Mono:wght@400;500;600&family=Hanken+Grotesk:wght@400;500;600&display=swap');
#MainMenu,header,footer{visibility:hidden;}
.stApp{background:#06080B;}
.block-container{padding:10px 12px 60px!important;max-width:480px!important;}
section.main>div{padding-top:0!important;}
html,body,[class*="css"]{font-family:'Hanken Grotesk',sans-serif;color:#E8E4D8;}
.stButton>button{font-family:'IBM Plex Mono',monospace;font-size:12px;font-weight:600;background:#11181F;color:#E8E4D8;border:1px solid rgba(232,228,216,.14);border-radius:9px;padding:7px 4px;width:100%;}
.stButton>button:hover{border-color:rgba(45,212,191,.4);color:#2DD4BF;}
.stButton>button[kind="primary"]{background:rgba(45,212,191,.1);border-color:rgba(45,212,191,.4);color:#2DD4BF;}
div[data-testid="stNumberInput"] input{font-family:'IBM Plex Mono',monospace;background:#06080B;color:#E8E4D8;border:1px solid rgba(232,228,216,.14);}
.ax{font-family:'IBM Plex Mono',monospace;}
.top{display:flex;align-items:center;gap:8px;margin-bottom:6px;}
.top .h1{font-family:'Archivo';font-weight:800;font-size:19px;}
.top .badge{font-family:'IBM Plex Mono';font-size:8px;color:#5A616B;border:1px solid rgba(232,228,216,.14);padding:2px 6px;border-radius:5px;margin-left:auto;}
.journey{display:flex;gap:4px;margin:6px 0 8px;}
.jst{flex:1;text-align:center;padding:5px 2px;border-radius:6px;background:#0C1117;border:1px solid rgba(232,228,216,.08);color:#5A616B;font-family:'IBM Plex Mono';font-size:7px;line-height:1.25;}
.jst.on{background:rgba(45,212,191,.1);border-color:rgba(45,212,191,.35);color:#2DD4BF;}
.msg{font-family:'IBM Plex Mono';font-size:10px;color:#E8B84B;min-height:13px;margin:2px;}
.card{background:#0C1117;border:1px solid rgba(232,228,216,.08);border-radius:14px;padding:13px;margin:0 0 11px;}
.sec{font-family:'Archivo';font-weight:700;font-size:9px;letter-spacing:.13em;color:#7E848E;border-bottom:1px solid rgba(232,228,216,.08);padding-bottom:7px;margin-bottom:10px;}
.warnb{font-family:'Hanken Grotesk';font-size:10px;color:#7E848E;line-height:1.5;background:rgba(232,184,75,.05);border:1px solid rgba(232,184,75,.18);border-radius:10px;padding:9px 11px;margin-bottom:10px;}
.warnb b{color:#E8B84B;font-family:'IBM Plex Mono';}
.bigval{font-family:'IBM Plex Mono';font-weight:600;font-size:27px;line-height:1;}
.lbl{font-family:'IBM Plex Mono';font-size:9px;color:#5A616B;}
.deltas{display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;margin-top:11px;}
.dl{background:#11181F;border:1px solid rgba(232,228,216,.08);border-radius:10px;padding:9px 4px;text-align:center;}
.dl .k{font-family:'IBM Plex Mono';font-size:7.5px;color:#5A616B;}.dl .v{font-family:'IBM Plex Mono';font-size:15px;font-weight:600;margin-top:2px;}
.tile{position:relative;background:#0C1117;border:1px solid rgba(232,228,216,.08);border-radius:14px;padding:11px;overflow:hidden;min-height:118px;display:flex;flex-direction:column;margin-bottom:6px;}
.tile .spark{position:absolute;left:0;right:0;bottom:0;}
.tile .tk{font-family:'IBM Plex Mono';font-weight:600;font-size:14px;position:relative;z-index:1;}
.tile .pxr{font-family:'IBM Plex Mono';font-size:10px;color:#7E848E;position:relative;z-index:1;}
.tile .scw{margin-top:auto;position:relative;z-index:1;}
.tile .scl{font-family:'IBM Plex Mono';font-size:7px;color:#5A616B;letter-spacing:.06em;}
.tile .sc{font-family:'IBM Plex Mono';font-weight:600;font-size:21px;line-height:1.1;}
.chip{font-family:'IBM Plex Mono';font-size:8px;padding:2px 6px;border-radius:5px;border:1px solid rgba(232,228,216,.14);}
.du{display:inline-block;width:50%;padding:6px 0;vertical-align:top;}
.du .k{font-family:'IBM Plex Mono';font-size:9px;color:#5A616B;}.du .v{font-family:'IBM Plex Mono';font-size:14px;font-weight:600;margin-top:2px;}
.usplitrow{display:flex;align-items:center;gap:14px;}
.usplit{display:flex;align-items:baseline;gap:8px;}.usplit .big{font-family:'IBM Plex Mono';font-size:25px;font-weight:600;}
.usplit .ul{font-family:'IBM Plex Mono';font-size:8px;color:#5A616B;line-height:1.3;}
.usep{width:1px;align-self:stretch;background:rgba(232,228,216,.14);margin:3px 0;}
.ubar{position:relative;height:8px;border-radius:5px;overflow:hidden;display:flex;margin:12px 0 4px;background:rgba(232,228,216,.06);}
.ubar .st{background:rgba(45,212,191,.55);}.ubar .sr{background:rgba(239,91,76,.5);}.ubar .thr{position:absolute;top:-3px;bottom:-3px;width:1.5px;background:rgba(232,228,216,.5);}
.barlbl{display:flex;justify-content:space-between;font-family:'IBM Plex Mono';font-size:8px;color:#5A616B;margin-bottom:9px;}
.karisik,.guven{font-family:'Hanken Grotesk';font-size:11px;color:#7E848E;margin-top:7px;line-height:1.5;}.karisik b,.guven b{font-family:'IBM Plex Mono';}
.ksm{font-size:9px;color:#5A616B;}
.genel{font-family:'Hanken Grotesk';font-size:11px;color:#7E848E;margin-top:10px;line-height:1.55;border-top:1px solid rgba(232,228,216,.08);padding-top:10px;}
.genel .glab{font-family:'Archivo';font-weight:700;font-size:8px;letter-spacing:.1em;color:#E8B84B;display:block;margin-bottom:4px;}.genel b{font-family:'IBM Plex Mono';}
.tracetxt{font-family:'Hanken Grotesk';font-size:10.5px;color:#7E848E;line-height:1.55;margin-top:4px;}
.rd{padding:13px 0;border-bottom:1px solid rgba(232,228,216,.08);}.rd:last-child{border-bottom:0;}
.rdh{display:flex;align-items:center;gap:8px;margin-bottom:2px;flex-wrap:wrap;}
.rdh .ic{font-family:'IBM Plex Mono';font-size:13px;color:#C9CDD3;width:18px;text-align:center;}
.rdh .nm{font-family:'Archivo';font-weight:700;font-size:13px;}
.rdh .en{font-family:'IBM Plex Mono';font-size:8px;color:#5A616B;border:1px solid rgba(232,228,216,.14);padding:1px 6px;border-radius:5px;}
.rdh .dt{font-family:'IBM Plex Mono';font-size:9px;color:#7E848E;margin-left:auto;}
.nedir{font-family:'Hanken Grotesk';font-size:11.5px;color:#C9CDD3;margin:6px 0 9px;padding-left:26px;line-height:1.5;}
.nedir .lab,.perc .lab{font-family:'IBM Plex Mono';font-size:7.5px;letter-spacing:.1em;text-transform:uppercase;color:#5A616B;border:1px solid rgba(232,228,216,.08);padding:1px 5px;border-radius:4px;margin-right:5px;}
.data{font-family:'IBM Plex Mono';font-size:11px;display:flex;flex-wrap:wrap;gap:3px 12px;padding-left:26px;}
.data .yr{color:#5A616B;font-size:9px;width:100%;}.data .sz{width:100%;color:#5A616B;font-size:9px;margin-top:2px;}
.vbadge{display:flex;align-items:baseline;gap:9px;padding-left:26px;margin-top:8px;}
.vlab{font-family:'Archivo';font-weight:700;font-size:10px;letter-spacing:.06em;padding:2px 8px;border-radius:5px;}
.vlab.up{color:#2DD4BF;background:rgba(45,212,191,.1);border:1px solid rgba(45,212,191,.28);}
.vlab.dn{color:#EF5B4C;background:rgba(239,91,76,.1);border:1px solid rgba(239,91,76,.28);}
.vlab.neu{color:#C9CDD3;background:rgba(232,228,216,.05);border:1px solid rgba(232,228,216,.14);}
.vwhy{font-family:'IBM Plex Mono';font-size:9px;color:#5A616B;}
.perc{font-family:'Hanken Grotesk';font-size:11px;color:#7E848E;margin-top:8px;padding-left:26px;line-height:1.5;}
.acrow{display:flex;justify-content:space-between;font-family:'IBM Plex Mono';font-size:12px;padding:8px 0;border-bottom:1px solid rgba(232,228,216,.08);}
.acrow .k{color:#7E848E;}
.pos{display:flex;align-items:center;gap:9px;padding:10px 0;border-bottom:1px solid rgba(232,228,216,.08);font-family:'IBM Plex Mono';}
.pos .tk{font-size:13px;font-weight:600;}.pos .mid{font-size:10px;color:#7E848E;line-height:1.4;}.pos .pl{margin-left:auto;text-align:right;font-size:12px;font-weight:600;}
.srctag{font-family:'IBM Plex Mono';font-size:8px;padding:1px 5px;border-radius:4px;border:1px solid rgba(232,228,216,.14);color:#5A616B;margin-left:5px;}
.tagM{color:#2DD4BF;border-color:rgba(45,212,191,.3);}.tagA{color:#E8B84B;border-color:rgba(232,184,75,.3);}
.led{font-family:'IBM Plex Mono';font-size:10px;display:flex;gap:7px;padding:6px 0;border-bottom:1px solid rgba(232,228,216,.05);color:#7E848E;}
.led .d{width:42px;color:#5A616B;}.led .t{flex:1;color:#E8E4D8;}.led .a{font-weight:600;}
.note{display:flex;gap:9px;padding:9px 0;border-bottom:1px solid rgba(232,228,216,.08);font-family:'Hanken Grotesk';font-size:11.5px;line-height:1.5;}
.note:last-child{border-bottom:0;}.note .ic{font-family:'IBM Plex Mono';font-size:12px;flex:none;width:16px;text-align:center;}.note b{font-family:'IBM Plex Mono';}
.trrow{display:flex;align-items:center;gap:8px;font-family:'IBM Plex Mono';margin-bottom:2px;}
.trrow .tk{font-size:13px;font-weight:600;width:56px;}.trrow .px{font-size:11px;}.trrow .cg{font-size:10px;font-weight:600;}
.up{color:#2DD4BF;}.dn{color:#EF5B4C;}.am{color:#E8B84B;}.neu{color:#C9CDD3;}
.bk{font-family:'IBM Plex Mono';font-size:11px;color:#7E848E;}
h3.hh{font-family:'Archivo';font-weight:800;font-size:22px;margin:2px 0;}
</style>
"""

def H(html): st.markdown(html, unsafe_allow_html=True)

@st.cache_data(ttl=3600, show_spinner="Gercek BIST verisi cekiliyor...")
def cached_data(kodlar):
    return fetch_real(kodlar)

def main():
    st.set_page_config(page_title="APEX Sanal Borsa", layout="centered")
    H(CSS)
    data = None
    try:
        data = cached_data(tuple(TK_DEF))
    except Exception:
        data = None
    real = bool(data)
    if not data:
        n = 250
        data = {"TK": TK_DEF,
                "PR": [_synthetic(n, 30 + i * 25, 0.12 + i * 0.01, i * 3, (i % 3) - 1) for i in range(len(TK_DEF))],
                "DLAB": [f"{(i % 28) + 1} {AY[(i // 21) % 12]}" for i in range(n)]}
    build(data)
    s = load_state()

    H('<div class="top"><span class="h1">APEX</span><span class="badge">' + ("SANAL · GERCEK VERI" if real else "SANAL · SENTETIK") + '</span></div>')
    _renk, _yazi = (("#34d399", "☁️ Bulut kalici · her cihazda ayni cuzdan") if kl.BULUT_AKTIF
                    else ("#fbbf24", "⚠️ Yerel mod · bulut bagli degil (REHBER_KALICILIK)"))
    H(f'<div style="text-align:center;font-size:0.72rem;color:{_renk};margin:-2px 0 8px">{_yazi}</div>')
    H("<a href='/' target='_self' style='display:block;text-align:center;font-size:0.78rem;"
      "color:#9fb4ad;text-decoration:none;margin:0 0 8px'>\u2190 APEX ana sayfa</a>")
    stg = ["Ogren", "Sanal Test", "Ilk Gercek Adim", "Tecrube", "Lisansli APEX"]
    H('<div class="journey">' + "".join(f'<div class="jst {"on" if i==1 else ""}">{x}{"<br>•buradasin•" if i==1 else ""}</div>' for i, x in enumerate(stg)) + '</div>')

    c = st.columns([1.1, 1, 1, 1.2])
    if c[0].button(f"Gun: {dl(s['day'])}", key="dshow"): pass
    if c[1].button("Gun +1", key="adv1"): advance(s, 1); save_state(s); st.rerun()
    if c[2].button("Hafta +1", key="adv5"): advance(s, 5); save_state(s); st.rerun()
    if c[3].button(("Oto: ACIK" if s["auto"] else "Oto: kapali"), key="auto", type=("primary" if s["auto"] else "secondary")):
        s["auto"] = not s["auto"]; s["msg"] = "Otomatik " + ("ACIK — sen yokken APEX devam eder" if s["auto"] else "kapali")
        if s["auto"] and s["started"]: apex_reb(s)
        save_state(s); st.rerun()

    if s.get("msg"): H(f'<div class="msg">{s["msg"]}</div>')

    tabs = [("havuz", "Havuz"), ("islem", "Islem"), ("pozisyon", "Pozisyon"), ("muhasebe", "Muhasebe"), ("cuzdan", "Cuzdan")]
    nc = st.columns(5)
    cur = "hisse" if s["tab"] == "hisse" else s["tab"]
    for i, (tk, lbl) in enumerate(tabs):
        on = (cur == tk) or (tk == "havuz" and s["tab"] == "hisse")
        if nc[i].button(lbl, key="nav" + tk, type=("primary" if on else "secondary")):
            s["tab"] = tk; s["msg"] = ""; save_state(s); st.rerun()

    view = s["tab"]
    if view == "havuz": v_havuz(s)
    elif view == "hisse": v_hisse(s)
    elif view == "islem": v_islem(s)
    elif view == "pozisyon": v_pozisyon(s)
    elif view == "muhasebe": v_muhasebe(s)
    elif view == "cuzdan": v_cuzdan(s)

def v_havuz(s):
    H('<div class="warnb"><b>Havuz — okuma-uygunlugu skoruna gore sirali.</b> AL listesi DEGIL: skor "okumalar gecmiste ne kadar tuttu" demek. Cogu hisse ~%50 (yazi-tura).</div>')
    arr = sorted([(k, score_full(k)) for k in range(D["NST"])], key=lambda o: o[1]["uyum"], reverse=True)
    cols = st.columns(2)
    for idx, (k, S) in enumerate(arr):
        col = cols[idx % 2]
        cg = today_pct(s, k); sc = S["band"][1]
        color = "#2DD4BF" if sc == "up" else ("#EF5B4C" if sc == "dn" else "#7E848E")
        cgc = "up" if cg >= 0 else "dn"
        with col:
            H(f'<div class="tile"><div class="spark">{sparkline(k, s["day"], color)}</div>'
              f'<div class="tk">{D["TK"][k]}</div><div class="pxr">{ftl(price(s,k))} <span class="{cgc}">{"▲%" if cg>=0 else "▼%"}{abs(cg):.1f}</span></div>'
              f'<div class="scw"><div class="scl">OKUMA-UYGUNLUGU</div><div class="ax"><span class="sc {sc}">~%{S["uyum"]:.0f}</span> <span class="chip {sc}">{S["band"][0]}</span></div></div></div>')
            if st.button("Incele →", key=f"open{k}"):
                s["sel"] = k; s["tab"] = "hisse"; save_state(s); st.rerun()

def v_hisse(s):
    k = s["sel"]; day = s["day"]; S = score_full(k)
    if st.button("← Havuz", key="back"): s["tab"] = "havuz"; save_state(s); st.rerun()
    cg = today_pct(s, k); cgc = "up" if cg >= 0 else "dn"
    H(f'<div class="ax" style="display:flex;align-items:baseline;gap:8px"><span class="hh">{D["TK"][k]}</span><span style="font-weight:600;font-size:18px;margin-left:auto">{ftl(price(s,k))}</span><span class="{cgc}" style="font-size:12px;font-weight:600">{"▲%" if cg>=0 else "▼%"}{abs(cg):.1f}</span></div>')
    H('<div class="lbl" style="margin-bottom:9px">komuta merkezi · grafik son ~4 ay · sicil son 1 yil</div>')
    H(f'<div class="card" style="padding:8px 6px 4px">{chart_svg(k, day)}</div>')
    H(durum_html(s, k))
    H(uygunluk_html(k, day, S))
    H(readings_html(k))
    H('<div class="lbl" style="text-align:center">sinyal/hedef/al-sat yok · her okuma kendi sicilini tasir</div>')

def v_islem(s):
    H('<div class="card"><div class="sec">ISLEM · MANUEL AL-SAT</div>')
    for k in range(D["NST"]):
        cg = today_pct(s, k); cgc = "up" if cg >= 0 else "dn"
        held = str(k) in s["posM"] and s["posM"][str(k)]["qty"] > 0
        H(f'<div class="trrow"><span class="tk">{D["TK"][k]}</span><span class="px">{ftl(price(s,k))}</span><span class="cg {cgc}">{"▲%" if cg>=0 else "▼%"}{abs(cg):.1f}</span></div>')
        cc = st.columns([1.4, 1, 1])
        amt = cc[0].number_input("tutar", min_value=0, step=1000, key=f"amt{k}", label_visibility="collapsed", placeholder="₺")
        if cc[1].button("AL", key=f"buy{k}", type="primary"): buy_m(s, k, amt); save_state(s); st.rerun()
        if held:
            if cc[2].button("SAT", key=f"sell{k}"): sell_m(s, k); save_state(s); st.rerun()
    H('</div>')
    H(f'<div class="card"><div class="sec">MANUEL MEVDUAT</div><div class="lbl" style="line-height:1.5;margin-bottom:8px">Nakdini elle mevduata koy, faiz islesin (%45/yil). Mevduat: <b class="am">{ftl(s["mevduat"])}</b></div>')
    mc = st.columns([1.4, 1, 1])
    mev = mc[0].number_input("mev", min_value=0, step=1000, key="mevamt", label_visibility="collapsed", placeholder="₺")
    if mc[1].button("Koy", key="mevkoy"): to_deposit(s, mev); save_state(s); st.rerun()
    if mc[2].button("Cek", key="mevcek"): from_deposit(s, mev); save_state(s); st.rerun()
    H('</div>')

def v_pozisyon(s):
    H('<div class="card"><div class="sec">POZISYONLAR</div>')
    allp = []
    for k, p in s["posM"].items():
        if p["qty"] > 0: allp.append((int(k), p, "M"))
    for k, p in s["posA"].items():
        if p["qty"] > 0: allp.append((int(k), p, "A"))
    if not allp: H('<div class="lbl">Pozisyon yok. Islemden al ya da otomatigi ac.</div>')
    for (k, p, src) in allp:
        avg = p["cost"] / p["qty"]; curp = price(s, k); val = p["qty"] * curp; pnl = val - p["cost"]; pp = (curp / avg - 1) * 100
        tag = "tagM" if src == "M" else "tagA"
        H(f'<div class="pos"><span class="tk">{D["TK"][k]}<span class="srctag {tag}">{"manuel" if src=="M" else "oto"}</span></span><div class="mid">{p["qty"]:.1f} ad · ort {ftl(avg)}<br>{ftl(val)}</div><span class="pl {"up" if pnl>=0 else "dn"}">{fsig(pnl)}<br><span class="lbl">{"+" if pp>=0 else "−"}%{abs(pp):.1f}</span></span></div>')
    H('</div>')
    H(f'<div class="card"><div class="acrow"><span class="k">Nakit</span><span>{ftl(s["cash"])}</span></div><div class="acrow"><span class="k">Mevduat</span><span class="am">{ftl(s["mevduat"])}</span></div><div class="acrow" style="border-bottom:0"><span class="k">Toplam portfoy</span><span class="{"up" if tot_val(s)>=s["deposited"] else "dn"}">{ftl(tot_val(s))}</span></div></div>')

def v_muhasebe(s):
    sub = [("manuel", "Manuel"), ("oto", "Otomatik"), ("birlesik", "Birlesik")]
    sc = st.columns(3)
    for i, (tk, lbl) in enumerate(sub):
        if sc[i].button(lbl, key="sub" + tk, type=("primary" if s["acctTab"] == tk else "secondary")):
            s["acctTab"] = tk; save_state(s); st.rerun()
    costM = sum(p["cost"] for p in s["posM"].values()); costA = sum(p["cost"] for p in s["posA"].values())
    unrealM = pv(s, s["posM"]) - costM; unrealA = pv(s, s["posA"]) - costA
    def block(rows):
        h = '<div class="card">'
        for i, r in enumerate(rows):
            border = ' style="border-bottom:0"' if i == len(rows) - 1 else ""
            h += f'<div class="acrow"{border}><span class="k">{r[0]}</span><span class="{r[2] if len(r)>2 else ""}">{r[1]}</span></div>'
        return h + "</div>"
    if s["acctTab"] == "manuel":
        H('<div class="sec" style="border:0;margin:4px 2px">MANUEL DEFTER · SENIN KARARLARIN</div>')
        H(block([("Manuel pozisyon", ftl(pv(s, s["posM"]))), ("Mevduat (faizli)", ftl(s["mevduat"]), "am"),
                 ("Gerceklesen K/Z", fsig(s["realizedM"]), "up" if s["realizedM"] >= 0 else "dn"),
                 ("Gerceklesmemis K/Z", fsig(unrealM), "up" if unrealM >= 0 else "dn"),
                 ("Manuel toplam", ftl(pv(s, s["posM"]) + s["mevduat"]))]))
    elif s["acctTab"] == "oto":
        H('<div class="sec" style="border:0;margin:4px 2px">OTOMATIK DEFTER · APEX</div>')
        H(block([("APEX pozisyon", ftl(pv(s, s["posA"]))),
                 ("Gerceklesen K/Z", fsig(s["realizedA"]), "up" if s["realizedA"] >= 0 else "dn"),
                 ("Gerceklesmemis K/Z", fsig(unrealA), "up" if unrealA >= 0 else "dn"),
                 ("Durum", "ACIK" if s["auto"] else "kapali", "up" if s["auto"] else "neu")]))
    else:
        net = tot_val(s) - s["deposited"] + s["withdrawn"]
        H('<div class="sec" style="border:0;margin:4px 2px">BIRLESIK · MANUEL + OTOMATIK + NAKIT</div>')
        H(block([("Yatirilan / Cekilen", ftl(s["deposited"]) + " / " + ftl(s["withdrawn"])),
                 ("Nakit", ftl(s["cash"])), ("Mevduat", ftl(s["mevduat"]), "am"),
                 ("Manuel pozisyon", ftl(pv(s, s["posM"]))), ("Otomatik pozisyon", ftl(pv(s, s["posA"]))),
                 ("Gerceklesen K/Z (M+A)", fsig(s["realizedM"] + s["realizedA"]), "up" if (s["realizedM"] + s["realizedA"]) >= 0 else "dn"),
                 ("Toplam portfoy", ftl(tot_val(s)), "up" if tot_val(s) >= s["deposited"] else "dn"),
                 ("Net kar/zarar", fsig(net), "up" if net >= 0 else "dn")]))
    h = '<div class="card"><div class="sec">ISLEM DEFTERI</div>'
    if not s["ledger"]: h += '<div class="lbl">Henuz islem yok.</div>'
    for e in s["ledger"][:16]:
        a = fsig(e["amt"]) if e.get("amt") else ""
        srctag = f'<span class="srctag {"tagM" if e.get("src")=="M" else "tagA"}">{e["src"]}</span> ' if e.get("src") and e["src"] != "-" else ""
        kn = (" " + D["TK"][e["k"]]) if "k" in e else ""
        ac = "up" if e.get("amt", 0) > 0 else ("dn" if e.get("amt", 0) < 0 else "neu")
        h += f'<div class="led"><span class="d">{dl(e["day"])}</span><span class="t">{srctag}{e["type"]}{kn}</span><span class="a {ac}">{a}</span></div>'
    h += "</div>"; H(h)

def v_cuzdan(s):
    _ozet_yaz(s)  # Google Sheet'teki gozle-okunur ozeti tazele
    dd = deltas(s); mine = tot_val(s)
    H('<div class="warnb"><b>Sanal egitim hesabi.</b> Gercek para yok. Amac: riski, disiplini, kaybetmemeyi gercek veriyle ogrenmek.</div>')
    h = f'<div class="card"><div class="lbl">SANAL PORTFOY DEGERI</div><div class="bigval {"up" if mine>=s["deposited"] else "dn"}">{ftl(mine)}</div><div class="lbl" style="margin-top:5px">nakit {ftl(s["cash"])} · mevduat {ftl(s["mevduat"])} · hisse {ftl(pv(s,s["posM"])+pv(s,s["posA"]))}</div>'
    if dd:
        h += f'<div class="deltas"><div class="dl"><div class="k">mevduata gore</div><div class="v {"up" if dd["dep"]>=0 else "dn"}">{"+" if dd["dep"]>=0 else "−"}%{abs(dd["dep"]):.1f}</div></div><div class="dl"><div class="k">naif sana gore</div><div class="v {"up" if dd["naif"]>=0 else "dn"}">{"+" if dd["naif"]>=0 else "−"}%{abs(dd["naif"]):.1f}</div></div><div class="dl"><div class="k">endekse gore</div><div class="v {"up" if dd["idx"]>=0 else "dn"}">{"+" if dd["idx"]>=0 else "−"}%{abs(dd["idx"]):.1f}</div></div></div>'
    h += "</div>"; H(h)
    H('<div class="card"><div class="sec">PARA YUKLE / CEK · SANAL</div>')
    dc = st.columns([1.4, 1, 1])
    val = dc[0].number_input("yukle", min_value=0, step=10000, key="depamt", label_visibility="collapsed", placeholder="₺ örn 100000")
    if dc[1].button("Yukle", key="depbtn", type="primary"): deposit(s, val); save_state(s); st.rerun()
    if dc[2].button("Cek", key="witbtn"): withdraw(s, val); save_state(s); st.rerun()
    if not s["started"]:
        if st.button("Hizli ₺100.000 yukle", key="quick"): deposit(s, 100000); save_state(s); st.rerun()
    H('</div>')
    H('<div class="card"><div class="sec">YONETICI NOTU · SANA DURUST BAKIS</div>' + "".join(f'<div class="note"><span class="ic {x[1]}">{x[0]}</span><div>{x[2]}</div></div>' for x in coaching(s)) + '</div>')
    with st.expander("Cuzdani sifirla"):
        st.caption("Tum islemler, pozisyonlar ve mevduat silinir. Geri alinamaz.")
        if st.button("Evet, sifirla", key="reset"):
            kl.sil(APEX_ANAHTAR)  # buluttan da sil
            try: STATE_FILE.unlink()
            except Exception: pass
            st.session_state["apex"] = init_state(); st.rerun()

if not os.environ.get("APEX_TEST"):
    main()
