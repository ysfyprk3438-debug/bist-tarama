# -*- coding: utf-8 -*-
"""
BIST PARA AVCISI — Yenilenmiş Kartlar
=====================================
arayuz.py içindeki `kompakt_satir(r)` ve `hisse_kart(r)` fonksiyonlarının
yerine geçer. Referans yerel uygulamanın kalite dili buraya taşındı:

  • Hap (pill) deseni — her sayısal rozet renkli zeminli
  • İki katlı kimlik (ticker büyük + sektör küçük)
  • Ayrılmış renk eksenleri:
        fiyat yönü (yeşil/kırmızı)  ≠  skor kalitesi (kendi rampası)  ≠  sinyal
  • Kart KİMLİKLE başlar, kararla değil (tam genişlik kırmızı bant kalktı)
  • İmza öğesi: Alım Puanı konik halkası
  • Tüm stiller INLINE — app.py'deki global CSS'e dokunmana gerek yok

KULLANIM (iki yoldan biri):
  A) Bu iki fonksiyonu arayuz.py'deki eski `kompakt_satir` / `hisse_kart`
     üzerine yapıştır.
  B) arayuz.py başına:  from arayuz_kartlar import kompakt_satir, hisse_kart

app.py'de çağrı zaten şöyle, dokunmana gerek yok:
     st.markdown(ui.kompakt_satir(r), unsafe_allow_html=True)
     st.markdown(ui.hisse_kart(r),   unsafe_allow_html=True)

NOT — alan adını göremediğim 3 yer (boş kalırsa bana söyle, tek seferde bağlarım):
  • r["rsi"]               → kimlik satırındaki "RSI xx"
  • r["pozisyon"]          → Pozisyon Yönetimi kutusu (lot/tutar/portfoy/max_kayip)
  • r["karar"]["mesaj"]    → karar gerekçe cümlesi
"""

import html

# ── Renk token'ları (tek kaynak) ───────────────────────────────────────────
C = {
    "card":   "#0D1117",
    "card2":  "#161D2B",
    "line":   "rgba(255,255,255,0.07)",
    "text":   "#E9EDF4",
    "muted":  "#8B94A6",
    "faint":  "#5B6475",
    "up":     "#10B981", "up_bg":   "rgba(16,185,129,0.13)",
    "down":   "#EF4444", "down_bg": "rgba(239,68,68,0.13)",
    "amber":  "#F59E0B", "amber_bg":"rgba(245,158,11,0.14)",
    "yellow": "#EAB308",
    "brand":  "#00D4FF",
}


def _e(v):
    return html.escape(str(v))


def _skor_renk(s):
    """Skor kalitesi rampası — fiyat renginden BAĞIMSIZ eksen."""
    s = s or 0
    if s >= 70: return C["up"]
    if s >= 50: return C["yellow"]
    if s >= 30: return C["amber"]
    return C["down"]


def _sektor_parcala(sektor):
    """'💊 Sağlık / Kimya' -> ('💊', 'Sağlık / Kimya')"""
    sektor = (sektor or "").strip()
    if not sektor:
        return "", ""
    parca = sektor.split(" ", 1)
    if len(parca) == 2 and not parca[0].isascii():   # ilk token emoji ise
        return parca[0], parca[1]
    return "", sektor


def _skor_al(r):
    """Alım Puanı: önce karar skoru, yoksa eski puan."""
    k = r.get("karar") or {}
    return int(k.get("skor", r.get("puan", 0)) or 0)


def _pct_hap(pct, kucuk=False):
    pct = float(pct or 0)
    up = pct >= 0
    col = C["up"] if up else C["down"]
    bg = C["up_bg"] if up else C["down_bg"]
    ok = "▲" if up else "▼"
    isaret = "+" if up else ""
    fs = "11.5px" if kucuk else "12.5px"
    return (f'<span style="display:inline-flex;align-items:center;gap:3px;'
            f'font-size:{fs};font-weight:700;line-height:1;padding:4px 8px;'
            f'border-radius:999px;color:{col};background:{bg};'
            f'font-variant-numeric:tabular-nums;white-space:nowrap">'
            f'{ok} %{isaret}{pct:.1f}</span>')


def _skor_hap(skor):
    col = _skor_renk(skor)
    return (f'<span style="display:inline-flex;align-items:center;'
            f'font-size:12.5px;font-weight:800;line-height:1;padding:4px 9px;'
            f'border-radius:999px;color:{col};background:{col}22;'
            f'font-variant-numeric:tabular-nums;min-width:30px;'
            f'justify-content:center">{int(skor or 0)}</span>')


# ═══════════════════════════════════════════════════════════════════════════
# 1) ÖZET SATIR  (Güçlü Sinyaller / Büyük Oyuncu / İzleme — tıklamadan önce)
# ═══════════════════════════════════════════════════════════════════════════
def kompakt_satir(r):
    skor = _skor_al(r)
    dot = _skor_renk(skor)
    emoji, sektor_ad = _sektor_parcala(r.get("sektor"))
    sinyal = r.get("sinyal", "")
    balina = (r.get("sm") or {}).get("buyuk_oyuncu")

    alt = sinyal
    if sektor_ad:
        alt = f"{sinyal} · {sektor_ad}" if sinyal else sektor_ad

    return f"""
<div style="display:flex;align-items:center;gap:11px;padding:12px 13px;
     border-radius:13px;background:{C['card']};border:1px solid {C['line']};
     margin-bottom:7px;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif">
  <span style="width:7px;height:7px;border-radius:50%;background:{dot};flex:0 0 auto"></span>
  {f'<span style="font-size:19px;flex:0 0 auto">{_e(emoji)}</span>' if emoji else ''}
  <div style="flex:1 1 auto;min-width:0">
    <div style="font-size:16px;font-weight:700;color:{C['text']};letter-spacing:.2px;line-height:1.1">
      {_e(r.get('kod',''))}{' <span style="font-size:13px">🐋</span>' if balina else ''}
    </div>
    <div style="font-size:11.5px;font-weight:600;color:{C['muted']};margin-top:2px;
         overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{_e(alt)}</div>
  </div>
  <div style="display:flex;align-items:center;gap:7px;flex:0 0 auto">
    <span style="font-size:13.5px;font-weight:700;color:{C['text']};
          font-variant-numeric:tabular-nums">{float(r.get('son',0)):.2f}₺</span>
    {_pct_hap(r.get('kazanc_pct'), kucuk=True)}
    {_skor_hap(skor)}
  </div>
</div>"""


# ═══════════════════════════════════════════════════════════════════════════
# 2) TAM KART  (Tüm Fırsatlar — satır)
# ═══════════════════════════════════════════════════════════════════════════
def hisse_kart(r):
    son = float(r.get("son", 0) or 0)
    hedef = r.get("hedef")
    stop = r.get("stop")
    skor = _skor_al(r)
    sc = _skor_renk(skor)
    emoji, sektor_ad = _sektor_parcala(r.get("sektor"))

    # ── Karar (verdict): varsa kendi metnini kullan, yoksa skordan türet ──
    karar = r.get("karar") or {}
    v_text = karar.get("etiket") or karar.get("karar") or karar.get("ad")
    if not v_text:
        if skor >= 70:   v_text = "AL"
        elif skor >= 50: v_text = "TAKİPTE TUT"
        elif skor >= 35: v_text = "İZLE"
        else:            v_text = "UZAK DUR"
    v_col = {"AL": C["up"], "GÜÇLÜ AL": C["up"], "TAKİPTE TUT": C["amber"],
             "TUT": C["amber"], "İZLE": C["muted"], "UZAK DUR": C["down"]}.get(v_text, sc)
    v_bg = {C["up"]: C["up_bg"], C["amber"]: C["amber_bg"],
            C["down"]: C["down_bg"]}.get(v_col, "rgba(255,255,255,.06)")

    rsi = r.get("rsi")
    rsi_html = (f'<div style="font-size:11.5px;font-weight:600;color:{C["faint"]};'
                f'text-align:right;margin-top:3px">RSI {_e(rsi)}</div>') if rsi is not None else ""

    # ── Sinyal hapı (DİP FIRSATI / Takipte Tut … ) ──
    sinyal = r.get("sinyal", "")
    sinyal_html = (f'<span style="display:inline-flex;align-items:center;font-size:12.5px;'
                   f'font-weight:700;padding:5px 11px;border-radius:999px;color:{sc};'
                   f'background:{sc}1c">{_e(sinyal)}</span>') if sinyal else ""

    # ── Karar gerekçe cümlesi (varsa) ──
    mesaj = karar.get("mesaj") or karar.get("aciklama") or karar.get("sebep") or ""
    mesaj_html = (f'<div style="font-size:13px;color:{C["muted"]};line-height:1.5;'
                  f'margin-top:11px">{_e(mesaj)}</div>') if mesaj else ""

    # ── Uyarı / olay etiketleri ──
    etiketler = r.get("uyarilar") or []
    if not etiketler:
        for o in (r.get("teknik_olay") or []):
            if o.get("yon") == "negatif":
                etiketler.append(o.get("etiket", ""))
    tag_html = ""
    if etiketler:
        chips = "".join(f'<span style="font-size:12px;font-weight:600;color:{C["amber"]}">{_e(x)}</span>'
                        for x in etiketler[:3])
        tag_html = f'<div style="display:flex;flex-wrap:wrap;gap:9px;margin-top:9px">{chips}</div>'

    # ── İmza: Alım Puanı konik halkası ──
    skor_cap = ({70: "Güçlü — şartlar lehte", 50: "Orta — temkinli izle",
                 30: "Zayıf — güven düşük", 0: "Çok zayıf — uzak dur"})[
        70 if skor >= 70 else 50 if skor >= 50 else 30 if skor >= 30 else 0]
    ring = f"""
  <div style="display:flex;align-items:center;gap:14px">
    <div style="width:62px;height:62px;border-radius:50%;flex:0 0 auto;display:grid;
         place-items:center;background:conic-gradient({sc} {skor*3.6:.0f}deg,
         rgba(255,255,255,0.07) 0)">
      <div style="width:48px;height:48px;border-radius:50%;background:{C['card']};
           display:grid;place-items:center">
        <span style="font-size:18px;font-weight:800;color:{sc}">{skor}</span>
      </div>
    </div>
    <div>
      <div style="font-size:10.5px;font-weight:700;letter-spacing:1px;text-transform:uppercase;
           color:{C['muted']}">Alım Puanı</div>
      <div style="font-size:13.5px;font-weight:600;color:{C['text']};margin-top:3px">{_e(skor_cap)}</div>
    </div>
  </div>"""

    # ── Metrik kutuları (HEDEF / STOP / K/K / 3 AYLIK) ──
    def _kutu(lbl, val, alt, alt_col):
        alt_html = (f'<div style="font-size:11px;font-weight:600;color:{alt_col};'
                    f'margin-top:2px">{_e(alt)}</div>') if alt else ""
        return (f'<div style="background:{C["card2"]};border:1px solid {C["line"]};'
                f'border-radius:11px;padding:10px 6px;text-align:center">'
                f'<div style="font-size:9.5px;font-weight:700;letter-spacing:.5px;'
                f'text-transform:uppercase;color:{C["muted"]}">{_e(lbl)}</div>'
                f'<div style="font-size:15px;font-weight:800;margin-top:4px;color:{C["text"]};'
                f'font-variant-numeric:tabular-nums">{val}</div>{alt_html}</div>')

    kutular = []
    if hedef:
        hp = (hedef - son) / son * 100 if son else 0
        kutular.append(_kutu("HEDEF", f'<span style="color:{C["up"]}">{hedef:.2f}₺</span>',
                             f"+%{hp:.1f}", C["up"]))
    if stop:
        sp = (stop - son) / son * 100 if son else 0
        kutular.append(_kutu("STOP", f'<span style="color:{C["down"]}">{stop:.2f}₺</span>',
                             f"-%{abs(sp):.1f}", C["down"]))
    if hedef and stop and son and (son - stop) > 0:
        kk = (hedef - son) / (son - stop)
        kutular.append(_kutu("K/K", f'<span style="color:{C["amber"]}">1:{kk:.1f}</span>', "", ""))
    uc_ay = r.get("uc_ay_pct", r.get("ay3_pct"))
    if uc_ay is not None:
        col = C["up"] if uc_ay >= 0 else C["down"]
        kutular.append(_kutu("3 AYLIK", f'<span style="color:{col}">%{uc_ay:+.1f}</span>', "", ""))
    metrik_html = ""
    if kutular:
        metrik_html = (f'<div style="display:grid;grid-template-columns:repeat({len(kutular)},1fr);'
                       f'gap:7px;margin-top:14px">{"".join(kutular)}</div>')

    # ── Akıllı Para barı (skordan etiket türet) ──
    sm = r.get("sm") or {}
    ap = int(sm.get("skor", 0) or 0)
    ap_lbl = "Akıllı para güçlü" if ap >= 60 else ("Nötr" if ap >= 40 else "Satış baskısı")
    ap_col = C["up"] if ap >= 60 else (C["muted"] if ap >= 40 else C["down"])
    ap_html = f"""
  <div style="margin-top:15px">
    <div style="display:flex;justify-content:space-between;font-size:10.5px;font-weight:700;
         letter-spacing:.5px;text-transform:uppercase;color:{C['muted']};margin-bottom:6px">
      <span>Akıllı Para Analizi</span><span style="color:{ap_col}">{ap}/100</span></div>
    <div style="background:{C['card2']};border-radius:4px;height:6px">
      <div style="width:{max(2,ap)}%;height:6px;border-radius:4px;background:{ap_col}"></div></div>
    <div style="font-size:12px;color:{ap_col};margin-top:5px">{ap_lbl}</div>
  </div>"""

    # ── Güven callout ──
    guven = r.get("guven") or {}
    guven_html = ""
    if guven:
        gr = guven.get("renk", C["muted"])
        gnot = guven.get("mesaj") or guven.get("not") or ""
        gnot_html = (f'<div style="font-size:12px;color:{C["muted"]};margin-top:3px">{_e(gnot)}</div>'
                     if gnot else "")
        guven_html = (f'<div style="border-left:3px solid {gr};padding:8px 0 8px 12px;margin-top:15px">'
                      f'<div style="font-size:13px;color:{C["muted"]}">GÜVEN: '
                      f'<b style="color:{gr}">{_e(guven.get("seviye",""))} %{int(guven.get("yuzde",0))}</b></div>'
                      f'{gnot_html}</div>')

    # ── Pozisyon Yönetimi (opsiyonel — alan varsa) + SIKIŞMA rozeti ──
    poz = r.get("pozisyon") or {}
    vol = r.get("volatilite") or {}
    rejim = vol.get("rejim")
    rejim_html = (f'<span style="font-size:11.5px;font-weight:700;color:{vol.get("renk",C["amber"])}">'
                  f'🌡️ {_e(rejim)}</span>') if rejim and rejim != "BELİRSİZ" else ""
    poz_html = ""
    if poz:
        def _pz(lbl, val, col=C["text"]):
            return (f'<div style="text-align:center"><div style="font-size:9.5px;font-weight:700;'
                    f'letter-spacing:.4px;color:{C["muted"]}">{lbl}</div>'
                    f'<div style="font-size:14px;font-weight:800;color:{col};margin-top:3px;'
                    f'font-variant-numeric:tabular-nums">{val}</div></div>')
        lot = poz.get("lot"); tutar = poz.get("tutar")
        pf = poz.get("portfoy_pct", poz.get("portfoy"))
        mk = poz.get("max_kayip")
        hucreler = ""
        if lot is not None:   hucreler += _pz("LOT", f"{int(lot):,}")
        if tutar is not None: hucreler += _pz("TUTAR", f"{float(tutar):,.0f}₺")
        if pf is not None:    hucreler += _pz("PORTFÖY", f"%{float(pf):.1f}", C["amber"])
        if mk is not None:    hucreler += _pz("MAX KAYIP", f"{float(mk):,.0f}₺", C["down"])
        if hucreler:
            n = hucreler.count("text-align:center")
            poz_html = (f'<div style="background:{C["card"]};border:1px solid {C["line"]};'
                        f'border-radius:12px;padding:12px;margin-top:15px">'
                        f'<div style="display:flex;justify-content:space-between;align-items:center;'
                        f'margin-bottom:10px"><span style="font-size:11px;font-weight:700;'
                        f'letter-spacing:.5px;text-transform:uppercase;color:{C["brand"]}">'
                        f'Pozisyon Yönetimi</span>{rejim_html}</div>'
                        f'<div style="display:grid;grid-template-columns:repeat({n},1fr);'
                        f'gap:8px">{hucreler}</div></div>')

    # ── KART (kimlik önce gelir) ──
    return f"""
<div style="background:{C['card']};border:1px solid {C['line']};border-radius:18px;
     padding:16px;margin-bottom:14px;
     font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif">

  <div style="display:flex;align-items:flex-start;gap:12px">
    {f'<span style="font-size:25px;line-height:1;flex:0 0 auto">{_e(emoji)}</span>' if emoji else ''}
    <div style="flex:1 1 auto;min-width:0">
      <div style="font-size:21px;font-weight:800;color:{C['text']};letter-spacing:.3px;line-height:1.05">
        {_e(r.get('kod',''))}</div>
      <div style="font-size:12px;font-weight:600;color:{C['muted']};margin-top:3px">{_e(sektor_ad)}</div>
    </div>
    <div style="flex:0 0 auto">
      <div style="font-size:20px;font-weight:800;color:{C['text']};text-align:right;
           font-variant-numeric:tabular-nums;line-height:1.05">{son:.2f}₺</div>
      {rsi_html}
    </div>
  </div>

  <div style="display:flex;align-items:center;gap:9px;flex-wrap:wrap;margin-top:12px">
    <span style="display:inline-flex;align-items:center;gap:7px;padding:6px 12px;
          border-radius:999px;font-size:13px;font-weight:800;letter-spacing:.3px;
          color:{v_col};background:{v_bg}">
      <span style="width:8px;height:8px;border-radius:50%;background:{v_col}"></span>{_e(v_text)}</span>
    {sinyal_html}
  </div>

  {mesaj_html}
  {tag_html}

  <div style="height:1px;background:{C['line']};margin:15px 0"></div>
  {ring}
  {metrik_html}
  {ap_html}
  {guven_html}
  {poz_html}
</div>"""
