# -*- coding: utf-8 -*-
"""
BIST Para Avcısı — Kart Tasarım Modülü
=======================================
Referans yerel uygulamanın kalite dilini Streamlit'e taşır:
  • Tek bir "hap (pill)" deseni — her sayısal rozet renkli zeminli
  • İki katlı kimlik bloğu (ticker büyük + sektör küçük)
  • Ayrılmış renk eksenleri (fiyat yönü ≠ skor kalitesi ≠ sinyal durumu)
  • Sıkı yazı ölçeği
  • İmza öğesi: Alım Puanı konik halkası

Kullanım:
    import streamlit as st
    from bist_kartlar import inject_styles, render_signal_row, render_signal_card

    inject_styles()                       # 1 kez, sayfa başında
    render_signal_row(hisse_dict)         # Güçlü Sinyaller / liste satırı (tıklamadan önce)
    render_signal_card(hisse_dict)        # Açılınca tam kart

Tüm fonksiyonlar HTML üretip st.markdown(..., unsafe_allow_html=True) ile basar.
Streamlit kolonları KULLANILMAZ — kartın içi tek HTML bloğudur (mobilde bozulmaz).
"""

import html
import streamlit as st


# ---------------------------------------------------------------------------
# TASARIM TOKEN'LARI  (tek kaynak — renk/ölçü buradan değişir)
# ---------------------------------------------------------------------------
TOKENS = {
    # Yüzeyler
    "bg":         "#0a0e17",
    "card":       "#121826",
    "card_2":     "#1a2233",   # metrik kutuları
    "hairline":   "rgba(255,255,255,0.07)",
    # Metin
    "text":       "#e9edf4",
    "muted":      "#8b94a6",
    "faint":      "#5b6475",
    # Marka
    "brand":      "#2bb8f0",   # BIST PARA AVCISI mavisi
    # Fiyat yönü ekseni
    "up":         "#2ee6a0",
    "up_bg":      "rgba(46,230,160,0.12)",
    "down":       "#ff5d6c",
    "down_bg":    "rgba(255,93,108,0.12)",
    # Nötr / uyarı ekseni
    "amber":      "#ffb020",
    "amber_bg":   "rgba(255,176,32,0.13)",
    "yellow":     "#f3d34a",
}


def _score_color(score: int) -> str:
    """Skor kalitesi rampası — fiyat renginden BAĞIMSIZ eksen."""
    if score >= 70:
        return TOKENS["up"]
    if score >= 50:
        return TOKENS["yellow"]
    if score >= 30:
        return TOKENS["amber"]
    return TOKENS["down"]


# Sinyal durumu -> (etiket rengi, trafik noktası rengi)
_SIGNAL_STATE = {
    "AL":            (TOKENS["up"],    TOKENS["up"]),
    "GÜÇLÜ AL":      (TOKENS["up"],    TOKENS["up"]),
    "DİP FIRSATI":   (TOKENS["up"],    TOKENS["up"]),
    "TAKİPTE TUT":   (TOKENS["amber"], TOKENS["amber"]),
    "TUT":           (TOKENS["amber"], TOKENS["amber"]),
    "UZAK DUR":      (TOKENS["down"],  TOKENS["down"]),
}


def _esc(v) -> str:
    return html.escape(str(v))


def _pct_pill(pct: float) -> str:
    """Renkli zeminli %değişim hapı — referansın imza deseni."""
    up = pct >= 0
    col = TOKENS["up"] if up else TOKENS["down"]
    bg = TOKENS["up_bg"] if up else TOKENS["down_bg"]
    arrow = "▲" if up else "▼"
    sign = "+" if up else ""
    return (
        f'<span class="bpa-pill" style="color:{col};background:{bg};">'
        f'{arrow} %{sign}{pct:.1f}</span>'
    )


def _score_pill(score: int) -> str:
    col = _score_color(score)
    return (
        f'<span class="bpa-pill" style="color:{col};'
        f'background:{col}1f;">{score}</span>'
    )


# ---------------------------------------------------------------------------
# STİL  (sayfa başında 1 kez çağır)
# ---------------------------------------------------------------------------
def inject_styles() -> None:
    t = TOKENS
    st.markdown(
        f"""
        <style>
        /* Sistem fontu — referans yerel app gibi hissettirir (web fontu değil) */
        .bpa, .bpa * {{
            font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text",
                         "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            -webkit-font-smoothing: antialiased;
            box-sizing: border-box;
        }}

        /* ---- Hap (pill): tüm sayısal rozetlerin tek deseni ---- */
        .bpa-pill {{
            display:inline-flex; align-items:center; gap:4px;
            font-size:13px; font-weight:700; line-height:1;
            padding:5px 9px; border-radius:999px;
            font-variant-numeric: tabular-nums; white-space:nowrap;
        }}

        /* ---- Özet satırı (tıklamadan önce) ---- */
        .bpa-row {{
            display:flex; align-items:center; gap:12px;
            padding:13px 14px; border-radius:14px;
            background:{t['card']}; border:1px solid {t['hairline']};
            margin-bottom:8px;
        }}
        .bpa-row .dot {{
            width:8px; height:8px; border-radius:50%; flex:0 0 auto;
        }}
        .bpa-row .emoji {{ font-size:20px; flex:0 0 auto; }}
        .bpa-row .id {{ flex:1 1 auto; min-width:0; }}
        .bpa-row .tk {{
            font-size:17px; font-weight:700; color:{t['text']};
            letter-spacing:.2px; line-height:1.1;
        }}
        .bpa-row .sub {{
            font-size:12px; font-weight:600; color:{t['muted']};
            margin-top:2px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;
        }}
        .bpa-row .right {{
            display:flex; align-items:center; gap:8px; flex:0 0 auto;
        }}

        /* ---- Tam kart ---- */
        .bpa-card {{
            background:{t['card']}; border:1px solid {t['hairline']};
            border-radius:18px; padding:16px; margin-bottom:14px;
        }}
        /* Kimlik satırı — kart EN ÜSTTEN kimlikle başlar */
        .bpa-head {{ display:flex; align-items:flex-start; gap:12px; }}
        .bpa-head .emoji {{ font-size:26px; line-height:1; flex:0 0 auto; }}
        .bpa-head .id {{ flex:1 1 auto; min-width:0; }}
        .bpa-head .tk {{ font-size:22px; font-weight:800; color:{t['text']};
                         letter-spacing:.3px; line-height:1.05; }}
        .bpa-head .sec {{ font-size:12.5px; font-weight:600; color:{t['muted']}; margin-top:3px; }}
        .bpa-head .px  {{ font-size:21px; font-weight:800; color:{t['text']};
                          text-align:right; font-variant-numeric:tabular-nums; line-height:1.05; }}
        .bpa-head .rsi {{ font-size:11.5px; font-weight:600; color:{t['faint']};
                          text-align:right; margin-top:3px; }}

        /* Karar hapı (AL/TUT/UZAK DUR) — kimlik satırının altında, sola */
        .bpa-verdict {{
            display:inline-flex; align-items:center; gap:7px;
            margin-top:12px; padding:7px 12px; border-radius:999px;
            font-size:13.5px; font-weight:800; letter-spacing:.3px;
        }}
        .bpa-verdict .dot {{ width:8px; height:8px; border-radius:50%; }}

        .bpa-reason {{ font-size:13.5px; color:{t['muted']}; line-height:1.5; margin-top:11px; }}
        .bpa-tags   {{ display:flex; flex-wrap:wrap; gap:7px; margin-top:9px; }}
        .bpa-tag    {{ font-size:12px; font-weight:600; color:{t['amber']}; }}

        .bpa-hr {{ height:1px; background:{t['hairline']}; border:0; margin:15px 0; }}

        /* İmza öğesi: Alım Puanı konik halkası */
        .bpa-score {{ display:flex; align-items:center; gap:14px; }}
        .bpa-ring  {{
            --pct:0; --col:{t['muted']};
            width:64px; height:64px; border-radius:50%; flex:0 0 auto;
            background: conic-gradient(var(--col) calc(var(--pct)*3.6deg),
                                       rgba(255,255,255,0.07) 0);
            display:grid; place-items:center;
        }}
        .bpa-ring .inner {{
            width:50px; height:50px; border-radius:50%;
            background:{t['card']}; display:grid; place-items:center;
        }}
        .bpa-ring .val {{ font-size:18px; font-weight:800; }}
        .bpa-score .meta .lbl {{ font-size:11px; font-weight:700; letter-spacing:1px;
                                 text-transform:uppercase; color:{t['muted']}; }}
        .bpa-score .meta .cap {{ font-size:13.5px; font-weight:600; color:{t['text']}; margin-top:3px; }}

        /* Metrik kutuları (HEDEF/STOP/K-K/3 AYLIK) */
        .bpa-metrics {{ display:grid; grid-template-columns:repeat(4,1fr); gap:8px; margin-top:15px; }}
        .bpa-m {{ background:{t['card_2']}; border:1px solid {t['hairline']};
                  border-radius:12px; padding:10px 8px; text-align:center; }}
        .bpa-m .lbl {{ font-size:10px; font-weight:700; letter-spacing:.6px;
                       text-transform:uppercase; color:{t['muted']}; }}
        .bpa-m .v   {{ font-size:16px; font-weight:800; margin-top:5px;
                       font-variant-numeric:tabular-nums; }}
        .bpa-m .d   {{ font-size:11.5px; font-weight:600; margin-top:2px; }}

        @media (max-width:380px) {{
            .bpa-metrics {{ grid-template-columns:repeat(2,1fr); }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# 1) ÖZET SATIRI  (Güçlü Sinyaller / Tüm Fırsatlar listesi — tıklamadan önce)
# ---------------------------------------------------------------------------
def render_signal_row(s: dict) -> None:
    """
    s = {
        "ticker": "TRCAS", "sektor": "Sağlık / Kimya", "emoji": "💊",
        "sinyal": "DİP FIRSATI", "pct": 9.6, "skor": 23,
    }
    """
    state_col, dot_col = _SIGNAL_STATE.get(s.get("sinyal", ""), (TOKENS["muted"], TOKENS["muted"]))
    emoji = s.get("emoji", "")
    sub = s.get("sinyal", "")
    if s.get("sektor"):
        sub = f'{sub} · {s["sektor"]}' if sub else s["sektor"]

    st.markdown(
        f"""
        <div class="bpa">
          <div class="bpa-row">
            <span class="dot" style="background:{dot_col};"></span>
            {f'<span class="emoji">{_esc(emoji)}</span>' if emoji else ''}
            <div class="id">
              <div class="tk">{_esc(s["ticker"])}</div>
              <div class="sub" style="color:{state_col};">{_esc(sub)}</div>
            </div>
            <div class="right">
              {_pct_pill(float(s.get("pct", 0)))}
              {_score_pill(int(s.get("skor", 0)))}
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# 2) TAM KART  (satır açılınca)
# ---------------------------------------------------------------------------
def render_signal_card(s: dict) -> None:
    """
    s = {
        "ticker":"TRCAS", "sektor":"Sağlık / Kimya", "emoji":"💊",
        "fiyat":"42.20₺", "rsi":34, "pct":9.6,
        "sinyal":"DİP FIRSATI",
        "verdict":"UZAK DUR",                       # AL / TAKİPTE TUT / UZAK DUR
        "reason":"Zayıf skor + olumsuz sinyaller — şartlar uygun değil.",
        "tags":["⚠️ Aylık trend aşağı", "💥 Kırılım Takipçisi · FARKLI"],
        "skor":23, "skor_cap":"Zayıf — güven düşük",
        "metrics":[
            {"lbl":"HEDEF","v":"46.26₺","d":"+%9.6","dc":"up"},
            {"lbl":"STOP","v":"39.70₺","d":"-%5.9","dc":"down"},
            {"lbl":"K/K","v":"1:1.6","d":"","dc":"amber"},
            {"lbl":"3 AYLIK","v":"%+2.3","d":"","dc":"up"},
        ],
    }
    """
    t = TOKENS
    v_col, v_dot = _SIGNAL_STATE.get(s.get("verdict", ""), (t["muted"], t["muted"]))
    v_bg = {t["up"]: t["up_bg"], t["amber"]: t["amber_bg"], t["down"]: t["down_bg"]}.get(v_col, "rgba(255,255,255,.06)")

    # Etiketler
    tags_html = ""
    if s.get("tags"):
        chips = "".join(f'<span class="bpa-tag">{_esc(x)}</span>' for x in s["tags"])
        tags_html = f'<div class="bpa-tags">{chips}</div>'

    # Skor halkası
    skor = int(s.get("skor", 0))
    sc_col = _score_color(skor)
    ring = f"""
      <div class="bpa-score">
        <div class="bpa-ring" style="--pct:{skor};--col:{sc_col};">
          <div class="inner"><span class="val" style="color:{sc_col};">{skor}</span></div>
        </div>
        <div class="meta">
          <div class="lbl">Alım Puanı</div>
          <div class="cap">{_esc(s.get("skor_cap",""))}</div>
        </div>
      </div>
    """

    # Metrikler
    dc_map = {"up": t["up"], "down": t["down"], "amber": t["amber"], "": t["text"]}
    cells = ""
    for m in s.get("metrics", []):
        vc = dc_map.get(m.get("dc", ""), t["text"])
        d = f'<div class="d" style="color:{vc};">{_esc(m["d"])}</div>' if m.get("d") else ""
        cells += (
            f'<div class="bpa-m"><div class="lbl">{_esc(m["lbl"])}</div>'
            f'<div class="v" style="color:{vc};">{_esc(m["v"])}</div>{d}</div>'
        )
    metrics_html = f'<div class="bpa-metrics">{cells}</div>' if cells else ""

    rsi = f'<div class="rsi">RSI {_esc(s["rsi"])}</div>' if s.get("rsi") is not None else ""
    emoji = s.get("emoji", "")

    st.markdown(
        f"""
        <div class="bpa">
          <div class="bpa-card">

            <!-- KİMLİK önce gelir -->
            <div class="bpa-head">
              {f'<span class="emoji">{_esc(emoji)}</span>' if emoji else ''}
              <div class="id">
                <div class="tk">{_esc(s["ticker"])}</div>
                <div class="sec">{_esc(s.get("sektor",""))}</div>
              </div>
              <div>
                <div class="px">{_esc(s.get("fiyat",""))}</div>
                {rsi}
              </div>
            </div>

            <!-- KARAR: tam genişlik kırmızı bant yerine tek hap -->
            <div>
              <span class="bpa-verdict" style="color:{v_col};background:{v_bg};">
                <span class="dot" style="background:{v_dot};"></span>{_esc(s.get("verdict",""))}
              </span>
              <span class="bpa-pill" style="color:{v_col};background:{v_bg};margin-left:8px;">
                {_pct_pill(float(s.get("pct",0)))}
              </span>
            </div>

            <div class="bpa-reason">{_esc(s.get("reason",""))}</div>
            {tags_html}

            <hr class="bpa-hr"/>
            {ring}
            {metrics_html}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# DEMO  (kendi app'inde silebilirsin — sadece önizleme için)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    st.set_page_config(page_title="Kart Demo", layout="centered")
    st.markdown(
        f"<div style='background:{TOKENS['bg']};padding:8px;border-radius:8px'></div>",
        unsafe_allow_html=True,
    )
    inject_styles()

    st.markdown("#### 🔥 Güçlü Sinyaller (önce)")
    render_signal_row({"ticker": "TRCAS", "sektor": "Sağlık / Kimya", "emoji": "💊",
                       "sinyal": "DİP FIRSATI", "pct": 9.6, "skor": 72})
    render_signal_row({"ticker": "CIMSA", "sektor": "Sanayi", "emoji": "🏭",
                       "sinyal": "TAKİPTE TUT", "pct": 10.0, "skor": 29})

    st.markdown("#### Tam kart (açılınca)")
    render_signal_card({
        "ticker": "TRCAS", "sektor": "Sağlık / Kimya", "emoji": "💊",
        "fiyat": "42.20₺", "rsi": 34, "pct": 9.6,
        "sinyal": "DİP FIRSATI", "verdict": "UZAK DUR",
        "reason": "Zayıf skor + olumsuz sinyaller — şartlar uygun değil.",
        "tags": ["⚠️ Aylık trend aşağı", "💥 Kırılım Takipçisi · FARKLI"],
        "skor": 23, "skor_cap": "Zayıf — güven düşük",
        "metrics": [
            {"lbl": "HEDEF", "v": "46.26₺", "d": "+%9.6", "dc": "up"},
            {"lbl": "STOP", "v": "39.70₺", "d": "-%5.9", "dc": "down"},
            {"lbl": "K/K", "v": "1:1.6", "d": "", "dc": "amber"},
            {"lbl": "3 AYLIK", "v": "%+2.3", "d": "", "dc": "up"},
        ],
    })
