"""
═══════════════════════════════════════════════════════════════
ARAYÜZ — BIST Tarama v4
═══════════════════════════════════════════════════════════════
HTML RENDER SORUNUNUN KÖKTEN ÇÖZÜMÜ:
Streamlit, 4+ boşlukla başlayan satırı "kod bloğu" sanıp çiğ basar.
temiz_html() her satırın baştaki boşluğunu silip tek satıra indirir.
unsafe_allow_html ile basılan HER blok bundan geçer.
"""


def temiz_html(html: str) -> str:
    """
    Girintili HTML'i Streamlit'in render edebileceği tek satıra indirir.
    Render sorununun çözümü budur — istisnasız her HTML bloğu buradan geçmeli.
    """
    return "".join(satir.strip() for satir in html.strip().splitlines())


# ══════════════════════════════════════════════════════════════
# RENK YARDIMCILARI
# ══════════════════════════════════════════════════════════════
def _puan_renk(p):
    return "#10B981" if p >= 70 else ("#F59E0B" if p >= 50 else "#EF4444")


def _rr_renk(rr):
    return "#10B981" if rr >= 2.5 else ("#F59E0B" if rr >= 1.5 else "#EF4444")


# ══════════════════════════════════════════════════════════════
# HİSSE KARTI — kurumsal, kompakt (ForInvest çizgisi)
# ══════════════════════════════════════════════════════════════
def _karar_seridi(r):
    """Kartın en üstündeki net karar şeridi (baş analist verdiği)."""
    karar = r.get("karar")
    if not karar:
        return ""
    # Çoklu zaman dilimi onay rozeti
    ztd = r.get("zaman_onay")
    ztd_rozet = ""
    if ztd and ztd.get("durum"):
        ztd_rozet = f'<div style="color:{ztd["renk"]};font-size:0.62rem;font-weight:600;margin-bottom:4px">{ztd["etiket"]}</div>'
    # Strateji türü rozeti (hangi oyun + sezon uyumu)
    strj = r.get("strateji")
    strj_rozet = ""
    if strj and strj.get("hisse_strateji_ad"):
        strj_rozet = f'<div style="color:{strj["hisse_renk"]};font-size:0.62rem;font-weight:600;margin-bottom:8px">{strj["hisse_ikon"]} {strj["hisse_strateji_ad"]} · {strj["uyum"]}</div>'
    return (
        f'<div style="background:{karar["renk"]}18;border-radius:8px;padding:8px 12px;margin-bottom:10px;'
        f'display:flex;justify-content:space-between;align-items:center">'
        f'<span style="color:{karar["renk"]};font-size:0.95rem;font-weight:800">{karar["ikon"]} {karar["karar"]}</span>'
        f'<span style="color:{karar["renk"]};font-size:0.8rem;font-weight:700">AV {karar["skor"]}</span>'
        f'</div>'
        f'<div style="color:#94A3B8;font-size:0.66rem;line-height:1.3;margin-bottom:6px">{karar["gerekce"]}</div>'
        f'{ztd_rozet}{strj_rozet}'
    )


def hisse_kart(r):
    p = r["puan"]
    p_renk = _puan_renk(p)
    rr_renk = _rr_renk(r["rr"])
    ay_renk = "#10B981" if r["donem_getiri"] > 0 else "#EF4444"
    sm = r["sm"]

    buyuk = (
        '<span style="background:#1C2940;color:#60A5FA;font-size:0.58rem;'
        'padding:1px 6px;border-radius:10px;margin-left:4px">🐋 BÜYÜK OYUNCU</span>'
        if sm["buyuk_oyuncu"] else ""
    )

    # Güven + niyet bandı (Güven Motoru)
    guven = r.get("guven")
    niyet = r.get("niyet")
    ruzgar = r.get("ruzgar")
    guven_html = ""
    if guven and niyet:
        niyet_rozet = ""
        if niyet["sinif"] not in ("NORMAL", "BELİRSİZ"):
            niyet_rozet = f'<span style="color:{niyet["renk"]};font-size:0.6rem;font-weight:700">{niyet["sinif"]}</span>'
        # Rüzgar rozeti
        ruzgar_rozet = ""
        if ruzgar and ruzgar["seviye"] not in ("—",):
            ruzgar_ikon = "🌬️" if ruzgar["skor"] > 0 else ("⚠️" if ruzgar["uyari"] else "•")
            ruzgar_rozet = f'<span style="color:{ruzgar["renk"]};font-size:0.6rem;font-weight:700;margin-left:8px">{ruzgar_ikon} {ruzgar["yon"]}</span>'
        guven_html = temiz_html(f"""
        <div style="background:#0A0F1A;border-radius:8px;padding:8px 10px;margin-top:10px;border-left:3px solid {guven['renk']}">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:3px">
            <span style="color:#94A3B8;font-size:0.6rem;font-weight:600;letter-spacing:0.3px">GÜVEN: <span style="color:{guven['renk']};font-weight:700">{guven['seviye']} %{guven['yuzde']}</span></span>
            <span>{niyet_rozet}{ruzgar_rozet}</span>
          </div>
          <div style="color:#64748B;font-size:0.62rem;line-height:1.3">{guven['gerekce']}</div>
        </div>
        """)

    # Pozisyon bloğu
    poz = r.get("pozisyon")
    poz_html = ""
    if poz and poz["lot"] > 0:
        vrej = r.get("volatilite", {})
        vrej_rozet = ""
        if vrej.get("rejim") and vrej["rejim"] != "BELİRSİZ":
            vrej_rozet = f'<span style="color:{vrej["renk"]};font-size:0.56rem;font-weight:700;float:right">🌡️ {vrej["rejim"]}</span>'
        poz_html = temiz_html(f"""
        <div style="margin-top:10px;background:#0A1628;border-radius:8px;padding:10px 12px;border:1px solid #1E3A5F">
          <div style="color:#38BDF8;font-size:0.62rem;font-weight:700;margin-bottom:6px;letter-spacing:0.5px">POZİSYON YÖNETİMİ {vrej_rozet}</div>
          <div style="display:flex;gap:8px">
            <div style="flex:1;text-align:center">
              <div style="color:#475569;font-size:0.58rem">LOT</div>
              <div style="color:#E2E8F0;font-weight:700;font-size:0.88rem">{poz['lot']:,}</div>
            </div>
            <div style="flex:1;text-align:center">
              <div style="color:#475569;font-size:0.58rem">TUTAR</div>
              <div style="color:#E2E8F0;font-weight:700;font-size:0.88rem">{poz['pozisyon_tl']:,.0f}₺</div>
            </div>
            <div style="flex:1;text-align:center">
              <div style="color:#475569;font-size:0.58rem">PORTFÖY</div>
              <div style="color:#F59E0B;font-weight:700;font-size:0.88rem">%{poz['pozisyon_yuzde']:.1f}</div>
            </div>
            <div style="flex:1;text-align:center">
              <div style="color:#475569;font-size:0.58rem">MAX KAYIP</div>
              <div style="color:#EF4444;font-weight:700;font-size:0.88rem">{poz['max_kayip_tl']:,.0f}₺</div>
            </div>
          </div>
        </div>
        """)

    # ── ALARM BANDI + TİTREŞİMLİ ÇERÇEVE ──
    alarm = r.get("alarm", {})
    alarm_band = ""
    kart_stil = "background:#0D1117;border:1px solid #1E293B;border-radius:12px;padding:14px 16px;margin-bottom:6px"
    if alarm.get("var"):
        arenk = alarm["renk"]
        # Titreşim animasyonu (kritik seviyede) — renge göre
        anim_map = {
            "#10B981": "pulse-yesil", "#EF4444": "pulse-kirmizi", "#38BDF8": "pulse-mavi",
            "#F59E0B": "pulse-turuncu", "#06B6D4": "pulse-turkuaz",
        }
        anim = anim_map.get(arenk, "pulse-yesil")
        if alarm.get("titresim"):
            kart_stil = f"background:#0D1117;border:2px solid {arenk};border-radius:12px;padding:14px 16px;margin-bottom:6px;animation:{anim} 1.4s infinite"
        else:
            kart_stil = f"background:#0D1117;border:2px solid {arenk}66;border-radius:12px;padding:14px 16px;margin-bottom:6px"
        # Alarm şeridi (kartın en üstünde)
        geri_sayim = f" · ~{alarm['gun']} gün" if alarm.get("gun") is not None else ""
        ikon = "⚡" if alarm["yon"] == "pozitif" else ("🔴" if alarm["yon"] == "negatif" else ("🟦" if alarm["yon"] == "firsat" else "🟠"))
        alarm_band = (
            f'<div style="background:{arenk}22;border-radius:8px;padding:6px 10px;margin-bottom:10px;'
            f'display:flex;justify-content:space-between;align-items:center">'
            f'<span style="color:{arenk};font-size:0.72rem;font-weight:700">{ikon} {alarm["etiket"]}{geri_sayim}</span>'
            f'<span style="color:{arenk};font-size:0.62rem">%{alarm["yakinlik"]} yakın</span></div>'
        )

    return temiz_html(f"""
    <div style="{kart_stil}">
      {alarm_band}
      {_karar_seridi(r)}
      <div style="display:flex;justify-content:space-between;align-items:flex-start">
        <div>
          <span style="font-size:1.1rem;font-weight:800;color:#E2E8F0">{r['kod']}</span>
          <span style="display:inline-block;padding:1px 8px;border-radius:20px;font-size:0.6rem;font-weight:600;margin-left:6px;background:#1E293B;color:#94A3B8">{r['sektor']}</span>
          {buyuk}
          <br><span style="display:inline-block;padding:2px 10px;border-radius:20px;font-size:0.68rem;font-weight:700;margin-top:6px;background:{'#064E3B' if r['renk']=='yesil' else '#451A03'};color:{'#10B981' if r['renk']=='yesil' else '#F59E0B'}">{r['sinyal']}</span>
        </div>
        <div style="text-align:right">
          <div style="color:#E2E8F0;font-weight:700;font-size:1.05rem">{r['son']:.2f}₺</div>
          <div style="color:#475569;font-size:0.66rem">RSI {r['rsi']:.0f}</div>
        </div>
      </div>
      <div style="background:#1E293B;border-radius:4px;height:5px;margin-top:10px">
        <div style="width:{p}%;height:5px;border-radius:4px;background:{p_renk}"></div>
      </div>
      <div style="display:flex;justify-content:space-between;margin-top:3px">
        <span style="color:#475569;font-size:0.63rem">Alım Puanı</span>
        <span style="color:{p_renk};font-size:0.7rem;font-weight:700">{p}/100</span>
      </div>
      <div style="display:flex;gap:7px;margin-top:10px">
        <div style="flex:1;background:#141B2D;border-radius:8px;padding:7px 8px;text-align:center">
          <div style="color:#475569;font-size:0.58rem;font-weight:600">HEDEF</div>
          <div style="color:#10B981;font-weight:700;font-size:0.85rem">{r['hedef']:.2f}₺</div>
          <div style="color:#10B981;font-size:0.62rem">+%{r['kazanc_pct']:.1f}</div>
        </div>
        <div style="flex:1;background:#141B2D;border-radius:8px;padding:7px 8px;text-align:center">
          <div style="color:#475569;font-size:0.58rem;font-weight:600">STOP</div>
          <div style="color:#EF4444;font-weight:700;font-size:0.85rem">{r['stop']:.2f}₺</div>
          <div style="color:#EF4444;font-size:0.62rem">-%{r['kayip_pct']:.1f}</div>
        </div>
        <div style="flex:1;background:#141B2D;border-radius:8px;padding:7px 8px;text-align:center">
          <div style="color:#475569;font-size:0.58rem;font-weight:600">K/K</div>
          <div style="color:{rr_renk};font-weight:700;font-size:0.85rem">1:{r['rr']:.1f}</div>
        </div>
        <div style="flex:1;background:#141B2D;border-radius:8px;padding:7px 8px;text-align:center">
          <div style="color:#475569;font-size:0.58rem;font-weight:600">3 AYLIK</div>
          <div style="color:{ay_renk};font-weight:700;font-size:0.85rem">%{r['donem_getiri']:+.1f}</div>
        </div>
      </div>
      <div style="margin-top:8px;background:#0A0F1A;border-radius:6px;padding:8px 10px">
        <div style="display:flex;justify-content:space-between;align-items:center">
          <span style="color:#64748B;font-size:0.6rem;font-weight:600;letter-spacing:0.3px">AKILLI PARA ANALİZİ</span>
          <span style="color:{sm['renk']};font-size:0.65rem;font-weight:700">{sm['skor']}/100</span>
        </div>
        <div style="background:#1E293B;border-radius:3px;height:4px;margin-top:4px">
          <div style="width:{sm['skor']}%;height:4px;border-radius:3px;background:{sm['renk']}"></div>
        </div>
        <div style="color:{sm['renk']};font-size:0.64rem;margin-top:4px">{sm['yorum']}</div>
      </div>
      {guven_html}
      {poz_html}
    </div>
    """)


# ══════════════════════════════════════════════════════════════
# REJİM (BORSA DURUMU) KARTI
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
# ÖZET İSTATİSTİK KUTUSU
# ══════════════════════════════════════════════════════════════
def istat_kutu(etiket, deger, renk):
    return temiz_html(f"""
    <div style="background:#0D1117;border:1px solid #1E293B;border-radius:10px;padding:14px;text-align:center">
      <div style="color:#94A3B8;font-size:0.68rem">{etiket}</div>
      <div style="color:{renk};font-size:1.8rem;font-weight:800">{deger}</div>
    </div>
    """)


# ══════════════════════════════════════════════════════════════
# KOMPAKT SATIR (expander içi — tek tek kaydırmaya son)
# ══════════════════════════════════════════════════════════════
def kompakt_satir(r):
    p_renk = _puan_renk(r["puan"])
    return temiz_html(f"""
    <div style="display:flex;justify-content:space-between;align-items:center;padding:8px 10px;border-bottom:1px solid #1E293B">
      <div>
        <span style="color:#E2E8F0;font-weight:700;font-size:0.9rem">{r['kod']}</span>
        <span style="color:#64748B;font-size:0.66rem;margin-left:6px">{r['sinyal']}</span>
      </div>
      <div style="display:flex;gap:12px;align-items:center">
        <span style="color:#10B981;font-size:0.72rem">+%{r['kazanc_pct']:.1f}</span>
        <span style="color:{p_renk};font-size:0.78rem;font-weight:700">{r['puan']}</span>
      </div>
    </div>
    """)
