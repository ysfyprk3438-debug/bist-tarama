"""
═══════════════════════════════════════════════════════════════
ARAYÜZ — BIST Para Avcısı v4 (kart dili yenilendi)
═══════════════════════════════════════════════════════════════
Streamlit, 4+ boşlukla başlayan satırı "kod bloğu" sanıp çiğ basar.
temiz_html() her satırın baştaki boşluğunu silip tek satıra indirir.
unsafe_allow_html ile basılan HER blok bundan geçer.

Bu sürümde kartlar referans yerel uygulamanın diline çekildi:
  • Hap (pill) deseni — sayısal rozetler renkli zeminli
  • İki katlı kimlik (ticker büyük + sektör küçük), kart kimlikle başlar
  • Ayrılmış renk eksenleri: skor kalitesi ≠ fiyat yönü
  • İmza: Alım Puanı konik halkası
  • Mevcut tüm veriler korunur (alarm, karar, güven, niyet, rüzgar, pozisyon)
"""


def temiz_html(html: str) -> str:
    """Girintili HTML'i tek satıra indirir — render sorununun çözümü."""
    return "".join(satir.strip() for satir in html.strip().splitlines())


# ══════════════════════════════════════════════════════════════
# RENK YARDIMCILARI
# ══════════════════════════════════════════════════════════════
def _puan_renk(p):
    return "#10B981" if p >= 70 else ("#F59E0B" if p >= 50 else "#EF4444")


def _rr_renk(rr):
    return "#10B981" if rr >= 2.5 else ("#F59E0B" if rr >= 1.5 else "#EF4444")


# ── Yeni kart yardımcıları (referans hap dili) ──
_FONT = "-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif"


def _skor_renk(s):
    """Skor kalitesi rampası — fiyat renginden BAĞIMSIZ eksen."""
    s = s or 0
    if s >= 70:
        return "#10B981"
    if s >= 50:
        return "#EAB308"
    if s >= 30:
        return "#F59E0B"
    return "#EF4444"


def _sektor_parcala(sektor):
    """'💊 Sağlık / Kimya' -> ('💊', 'Sağlık / Kimya')"""
    sektor = (sektor or "").strip()
    if not sektor:
        return "", ""
    parca = sektor.split(" ", 1)
    if len(parca) == 2 and not parca[0].isascii():
        return parca[0], parca[1]
    return "", sektor


def _pct_hap(pct, kucuk=False):
    pct = float(pct or 0)
    up = pct >= 0
    col = "#10B981" if up else "#EF4444"
    bg = "rgba(16,185,129,0.13)" if up else "rgba(239,68,68,0.13)"
    ok = "▲" if up else "▼"
    isaret = "+" if up else ""
    fs = "11px" if kucuk else "12.5px"
    return (f'<span style="display:inline-flex;align-items:center;gap:3px;font-size:{fs};'
            f'font-weight:700;line-height:1;padding:4px 8px;border-radius:999px;color:{col};'
            f'background:{bg};font-variant-numeric:tabular-nums;white-space:nowrap">'
            f'{ok} %{isaret}{pct:.1f}</span>')


def _skor_hap(skor):
    col = _skor_renk(skor)
    return (f'<span style="display:inline-flex;align-items:center;justify-content:center;'
            f'min-width:30px;font-size:12.5px;font-weight:800;line-height:1;padding:4px 9px;'
            f'border-radius:999px;color:{col};background:{col}22;'
            f'font-variant-numeric:tabular-nums">{int(skor or 0)}</span>')


# ══════════════════════════════════════════════════════════════
# HİSSE KARTI — kimlik önce, hap dili, skor halkası
# ══════════════════════════════════════════════════════════════
def hisse_kart(r):
    p = int(r.get("puan", 0) or 0)
    p_renk = _skor_renk(p)
    sm = r.get("sm", {}) or {}
    emoji, sektor_ad = _sektor_parcala(r.get("sektor"))
    renk_sinyal = "#10B981" if r.get("renk") == "yesil" else "#F59E0B"

    # ── ALARM BANDI + TİTREŞİMLİ ÇERÇEVE (mevcut özellik korunur) ──
    alarm = r.get("alarm", {}) or {}
    kart_stil = ("background:#0D1117;border:1px solid rgba(255,255,255,0.07);"
                 "border-radius:18px;padding:16px;margin-bottom:14px")
    alarm_band = ""
    if alarm.get("var"):
        arenk = alarm["renk"]
        anim_map = {"#10B981": "pulse-yesil", "#EF4444": "pulse-kirmizi",
                    "#38BDF8": "pulse-mavi", "#F59E0B": "pulse-turuncu", "#06B6D4": "pulse-turkuaz"}
        anim = anim_map.get(arenk, "pulse-yesil")
        if alarm.get("titresim"):
            kart_stil = (f"background:#0D1117;border:2px solid {arenk};border-radius:18px;"
                         f"padding:16px;margin-bottom:14px;animation:{anim} 1.4s infinite")
        else:
            kart_stil = (f"background:#0D1117;border:1px solid {arenk}66;border-radius:18px;"
                         f"padding:16px;margin-bottom:14px")
        geri = f" · ~{alarm['gun']} gün" if alarm.get("gun") is not None else ""
        a_ikon = "⚡" if alarm["yon"] == "pozitif" else ("🔴" if alarm["yon"] == "negatif"
                  else ("🟦" if alarm["yon"] == "firsat" else "🟠"))
        alarm_band = (f'<div style="display:flex;justify-content:space-between;align-items:center;'
                      f'padding:7px 11px;border-radius:999px;background:{arenk}22;margin-bottom:12px">'
                      f'<span style="color:{arenk};font-size:12px;font-weight:700">{a_ikon} {alarm["etiket"]}{geri}</span>'
                      f'<span style="color:{arenk};font-size:11px;font-weight:600">%{alarm["yakinlik"]} yakın</span></div>')

    # ── KİMLİK satırı (önce gelir) ──
    balina = ' 🐋' if sm.get("buyuk_oyuncu") else ''
    rsi_html = ""
    if r.get("rsi") is not None:
        rsi_html = f'<div style="font-size:11.5px;font-weight:600;color:#5B6475;text-align:right;margin-top:3px">RSI {r["rsi"]:.0f}</div>'
    emoji_html = f'<span style="font-size:25px;line-height:1;flex:0 0 auto">{emoji}</span>' if emoji else ''
    kimlik = (f'<div style="display:flex;align-items:flex-start;gap:12px">'
              f'{emoji_html}'
              f'<div style="flex:1 1 auto;min-width:0">'
              f'<div style="font-size:21px;font-weight:800;color:#E9EDF4;letter-spacing:.3px;line-height:1.05">{r.get("kod","")}{balina}</div>'
              f'<div style="font-size:12px;font-weight:600;color:#8B94A6;margin-top:3px">{sektor_ad}</div></div>'
              f'<div style="flex:0 0 auto">'
              f'<div style="font-size:20px;font-weight:800;color:#E9EDF4;text-align:right;font-variant-numeric:tabular-nums;line-height:1.05">{float(r.get("son",0)):.2f}₺</div>'
              f'{rsi_html}</div></div>')

    # ── KARAR (verdict) — tam genişlik bant yerine hap + AV ──
    karar = r.get("karar")
    verdict_html = ""
    gerekce_html = ""
    if karar:
        vcol = karar.get("renk", "#94A3B8")
        verdict_html = (f'<span style="display:inline-flex;align-items:center;gap:7px;padding:6px 12px;'
                        f'border-radius:999px;font-size:13px;font-weight:800;letter-spacing:.3px;color:{vcol};background:{vcol}1f">'
                        f'<span style="width:8px;height:8px;border-radius:50%;background:{vcol}"></span>{karar.get("ikon","")} {karar.get("karar","")}'
                        f'<span style="opacity:.8;font-size:11.5px;margin-left:4px">AV {karar.get("skor","")}</span></span>')
        if karar.get("gerekce"):
            gerekce_html = f'<div style="font-size:13px;color:#8B94A6;line-height:1.5;margin-top:11px">{karar["gerekce"]}</div>'

    sinyal_html = (f'<span style="display:inline-flex;align-items:center;font-size:12.5px;font-weight:700;'
                   f'padding:5px 11px;border-radius:999px;color:{renk_sinyal};background:{renk_sinyal}1c">{r.get("sinyal","")}</span>')
    karar_satiri = (f'<div style="display:flex;align-items:center;gap:9px;flex-wrap:wrap;margin-top:12px">'
                    f'{verdict_html}{sinyal_html}</div>')

    # ztd + strateji rozetleri (mevcut özellikler korunur)
    rozet_list = []
    ztd = r.get("zaman_onay")
    if ztd and ztd.get("durum"):
        rozet_list.append(f'<span style="color:{ztd["renk"]};font-size:12px;font-weight:600">{ztd["etiket"]}</span>')
    strj = r.get("strateji")
    if strj and strj.get("hisse_strateji_ad"):
        rozet_list.append(f'<span style="color:{strj["hisse_renk"]};font-size:12px;font-weight:600">{strj["hisse_ikon"]} {strj["hisse_strateji_ad"]} · {strj["uyum"]}</span>')
    rozet_html = (f'<div style="display:flex;flex-wrap:wrap;gap:9px;margin-top:9px">{"".join(rozet_list)}</div>'
                  if rozet_list else "")

    # ── İMZA: Alım Puanı konik halkası ──
    cap = {70: "Güçlü zemin", 50: "Orta zemin", 30: "Zayıf zemin", 0: "Çok zayıf"}[
        70 if p >= 70 else 50 if p >= 50 else 30 if p >= 30 else 0]
    ring = (f'<div style="display:flex;align-items:center;gap:14px">'
            f'<div style="width:62px;height:62px;border-radius:50%;flex:0 0 auto;display:grid;place-items:center;'
            f'background:conic-gradient({p_renk} {p*3.6:.0f}deg,rgba(255,255,255,0.07) 0)">'
            f'<div style="width:48px;height:48px;border-radius:50%;background:#0D1117;display:grid;place-items:center">'
            f'<span style="font-size:18px;font-weight:800;color:{p_renk}">{p}</span></div></div>'
            f'<div><div style="font-size:10.5px;font-weight:700;letter-spacing:1px;text-transform:uppercase;color:#8B94A6">Alım Puanı</div>'
            f'<div style="font-size:13.5px;font-weight:600;color:#E9EDF4;margin-top:3px">{cap}</div></div></div>')

    # ── METRİK kutuları ──
    hedef_s = f"{r.get('hedef', 0):.2f}₺"
    stop_s = f"{r.get('stop', 0):.2f}₺"
    kk_s = f"1:{r.get('rr', 0):.1f}"
    ay_v = r.get("donem_getiri", 0)
    ay_s = f"%{ay_v:+.1f}"
    ay_renk = "#10B981" if ay_v > 0 else "#EF4444"
    kz_s = f"+%{r.get('kazanc_pct', 0):.1f}"
    ky_s = f"-%{r.get('kayip_pct', 0):.1f}"

    def _kutu(lbl, val, vcol, alt="", acol=""):
        alt_h = (f'<div style="font-size:11px;font-weight:600;color:{acol};margin-top:2px">{alt}</div>'
                 if alt else "")
        return (f'<div style="background:#161D2B;border:1px solid rgba(255,255,255,0.07);border-radius:11px;'
                f'padding:10px 6px;text-align:center">'
                f'<div style="font-size:9.5px;font-weight:700;letter-spacing:.5px;text-transform:uppercase;color:#8B94A6">{lbl}</div>'
                f'<div style="font-size:15px;font-weight:800;margin-top:4px;color:{vcol};font-variant-numeric:tabular-nums">{val}</div>{alt_h}</div>')

    metrik = (f'<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:7px;margin-top:14px">'
              f'{_kutu("HEDEF", hedef_s, "#10B981", kz_s, "#10B981")}'
              f'{_kutu("STOP", stop_s, "#EF4444", ky_s, "#EF4444")}'
              f'{_kutu("K/K", kk_s, "#F59E0B")}'
              f'{_kutu("3 AYLIK", ay_s, ay_renk)}</div>')

    # ── AKILLI PARA barı ──
    ap = int(sm.get("skor", 0) or 0)
    ap_renk = sm.get("renk", "#94A3B8")
    ap_html = (f'<div style="margin-top:15px">'
               f'<div style="display:flex;justify-content:space-between;font-size:10.5px;font-weight:700;'
               f'letter-spacing:.5px;text-transform:uppercase;color:#8B94A6;margin-bottom:6px">'
               f'<span>Akıllı Para Analizi</span><span style="color:{ap_renk}">{ap}/100</span></div>'
               f'<div style="background:#161D2B;border-radius:4px;height:6px">'
               f'<div style="width:{max(2, ap)}%;height:6px;border-radius:4px;background:{ap_renk}"></div></div>'
               f'<div style="font-size:12px;color:{ap_renk};margin-top:5px">{sm.get("yorum", "")}</div></div>')

    # ── GÜVEN bandı (+ niyet + rüzgar rozetleri, mevcut) ──
    guven = r.get("guven")
    niyet = r.get("niyet")
    ruzgar = r.get("ruzgar")
    guven_html = ""
    if guven:
        grenk = guven.get("renk", "#94A3B8")
        rozetler = ""
        if niyet and niyet.get("sinif") not in ("NORMAL", "BELİRSİZ"):
            rozetler += f'<span style="color:{niyet["renk"]};font-size:11px;font-weight:700">{niyet["sinif"]}</span>'
        if ruzgar and ruzgar.get("seviye") not in ("—", None):
            rikon = "🌬️" if ruzgar["skor"] > 0 else ("⚠️" if ruzgar.get("uyari") else "•")
            rozetler += f'<span style="color:{ruzgar["renk"]};font-size:11px;font-weight:700;margin-left:8px">{rikon} {ruzgar["yon"]}</span>'
        gg = guven.get("gerekce", "")
        gg_html = f'<div style="font-size:12px;color:#5B6475;line-height:1.35;margin-top:3px">{gg}</div>' if gg else ""
        guven_html = (f'<div style="border-left:3px solid {grenk};padding:8px 0 8px 12px;margin-top:15px">'
                      f'<div style="display:flex;justify-content:space-between;align-items:center">'
                      f'<span style="font-size:13px;color:#8B94A6">GÜVEN: <b style="color:{grenk}">{guven.get("seviye","")} %{guven.get("yuzde",0)}</b></span>'
                      f'<span>{rozetler}</span></div>{gg_html}</div>')

    # ── POZİSYON YÖNETİMİ (gerçek alan adları + tavan rozeti) ──
    poz = r.get("pozisyon")
    poz_html = ""
    if poz and poz.get("lot", 0) > 0:
        vrej = r.get("volatilite", {}) or {}
        rejim_rozet = ""
        if vrej.get("rejim") and vrej["rejim"] != "BELİRSİZ":
            rejim_rozet = f'<span style="font-size:11.5px;font-weight:700;color:{vrej.get("renk","#F59E0B")}">🌡️ {vrej["rejim"]}</span>'
        tavan_not = ' <span style="color:#64748B;font-size:10px;font-weight:600">· tavan</span>' if poz.get("tavan_uygulandi") else ''

        def _pz(lbl, val, col):
            return (f'<div style="text-align:center"><div style="font-size:9.5px;font-weight:700;letter-spacing:.4px;color:#8B94A6">{lbl}</div>'
                    f'<div style="font-size:14px;font-weight:800;color:{col};margin-top:3px;font-variant-numeric:tabular-nums">{val}</div></div>')

        lot_s = f"{poz['lot']:,}"
        tutar_s = f"{poz['pozisyon_tl']:,.0f}₺"
        pf_s = f"%{poz['pozisyon_yuzde']:.1f}"
        mk_s = f"{poz['max_kayip_tl']:,.0f}₺"
        poz_html = (f'<div style="background:#0D1117;border:1px solid rgba(255,255,255,0.07);border-radius:12px;padding:12px;margin-top:15px">'
                    f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px">'
                    f'<span style="font-size:11px;font-weight:700;letter-spacing:.5px;text-transform:uppercase;color:#38BDF8">Pozisyon Yönetimi{tavan_not}</span>{rejim_rozet}</div>'
                    f'<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:8px">'
                    f'{_pz("LOT", lot_s, "#E9EDF4")}{_pz("TUTAR", tutar_s, "#E9EDF4")}'
                    f'{_pz("PORTFÖY", pf_s, "#F59E0B")}{_pz("MAX KAYIP", mk_s, "#EF4444")}</div></div>')

    return temiz_html(f"""
    <div style="{kart_stil};font-family:{_FONT}">
      {alarm_band}
      {kimlik}
      {karar_satiri}
      {gerekce_html}
      {rozet_html}
      <div style="height:1px;background:rgba(255,255,255,0.07);margin:15px 0"></div>
      {ring}
      {metrik}
      {ap_html}
      {guven_html}
      {poz_html}
    </div>
    """)


# ══════════════════════════════════════════════════════════════
# REJİM (BORSA DURUMU) KARTI — değişmedi
# ══════════════════════════════════════════════════════════════
def rejim_kart(rejim, xu100_pct):
    yesil = "YÜKSELİŞ" in rejim
    sari = "DÜZELTME" in rejim or "YATAY" in rejim
    bg = "#0B1F14" if yesil else ("#1C1505" if sari else "#1C0808")
    kenar = "#10B981" if yesil else ("#F59E0B" if sari else "#EF4444")
    ikon = "🟢" if yesil else ("🟡" if sari else "🔴")
    pct_renk = "#10B981" if xu100_pct > 0 else "#EF4444"
    return temiz_html(f"""
    <div style="background:{bg};border-left:4px solid {kenar};border-radius:10px;padding:14px 16px;margin-bottom:16px">
      <div style="display:flex;justify-content:space-between;align-items:center">
        <div>
          <span style="color:#94A3B8;font-size:0.72rem;font-weight:600">BORSA DURUMU</span><br>
          <span style="color:#E2E8F0;font-size:1rem;font-weight:700">{ikon} {rejim}</span>
        </div>
        <div style="text-align:right">
          <span style="color:#94A3B8;font-size:0.7rem">XU100 Aylık</span><br>
          <span style="color:{pct_renk};font-size:1.1rem;font-weight:700">%{xu100_pct:+.1f}</span>
        </div>
      </div>
    </div>
    """)


# ══════════════════════════════════════════════════════════════
# ÖZET İSTATİSTİK KUTUSU — değişmedi
# ══════════════════════════════════════════════════════════════
def istat_kutu(etiket, deger, renk):
    return temiz_html(f"""
    <div style="background:#0D1117;border:1px solid #1E293B;border-radius:10px;padding:14px;text-align:center">
      <div style="color:#94A3B8;font-size:0.68rem">{etiket}</div>
      <div style="color:{renk};font-size:1.8rem;font-weight:800">{deger}</div>
    </div>
    """)


# ══════════════════════════════════════════════════════════════
# KOMPAKT SATIR — referans hap dili
# ══════════════════════════════════════════════════════════════
def kompakt_satir(r):
    skor = int(r.get("puan", 0) or 0)
    dot = _skor_renk(skor)
    emoji, sektor_ad = _sektor_parcala(r.get("sektor"))
    sinyal = r.get("sinyal", "")
    balina = (r.get("sm") or {}).get("buyuk_oyuncu")
    alt = f"{sinyal} · {sektor_ad}" if (sinyal and sektor_ad) else (sinyal or sektor_ad)
    emoji_html = f'<span style="font-size:19px;flex:0 0 auto">{emoji}</span>' if emoji else ''
    return temiz_html(f"""
    <div style="display:flex;align-items:center;gap:11px;padding:12px 13px;border-radius:13px;background:#0D1117;border:1px solid rgba(255,255,255,0.07);margin-bottom:7px;font-family:{_FONT}">
      <span style="width:7px;height:7px;border-radius:50%;background:{dot};flex:0 0 auto"></span>
      {emoji_html}
      <div style="flex:1 1 auto;min-width:0">
        <div style="font-size:16px;font-weight:700;color:#E9EDF4;letter-spacing:.2px;line-height:1.1">{r.get('kod','')}{' 🐋' if balina else ''}</div>
        <div style="font-size:11.5px;font-weight:600;color:#8B94A6;margin-top:2px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{alt}</div>
      </div>
      <div style="display:flex;align-items:center;gap:7px;flex:0 0 auto">
        <span style="font-size:13.5px;font-weight:700;color:#E9EDF4;font-variant-numeric:tabular-nums">{float(r.get('son',0)):.2f}₺</span>
        {_pct_hap(r.get('kazanc_pct'), kucuk=True)}
        {_skor_hap(skor)}
      </div>
    </div>
    """)
