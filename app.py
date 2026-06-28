#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
APEX — Uygulamanın ilk çalışan hâli (v1.0)
═══════════════════════════════════════════════════════════════
Omurga HTML'i (apex_omurga_v1.html) DÜRÜST veriyle besler.

İlke: canlı piyasa verisi GEREKTİRMEYEN çekirdek (reel-faiz rejimi,
vol-hedef risk, sicille-ağırlıklı merkez puan) GERÇEK hesaplanır.
Canlı besleme bekleyen kısımlar (per-hisse fiyat, AKD, nabız) dürüstçe
"bağlanınca dolacak" kalır. Hiçbir yere uydurma %99 / +142% konmaz.

Kullanım:
  python apex_app.py                  -> apex.html üretir (tarayıcıda aç)
  streamlit run apex_app.py           -> Streamlit Cloud'da servis eder
"""
import json, datetime, math, pathlib

TEMPLATE = "apex_omurga_v1.html"   # omurga (görsel) — yan dosya
OUT      = "apex.html"

# ─────────────────────────────────────────────────────────────
# 1) MAKRO TABLO (statik, web-araştırmalı) → REEL FAİZ REJİMİ
#    reel = politika faizi − enflasyon.  Canlı veri GEREKMEZ.
# ─────────────────────────────────────────────────────────────
MAKRO = {  # (yıl, çeyrek): (politika %, enflasyon %)
    (2024, 4): (47.5, 44.4), (2025, 1): (45.0, 38.1), (2025, 2): (46.0, 35.0),
    (2025, 3): (43.0, 33.0), (2025, 4): (39.5, 31.5), (2026, 1): (37.0, 30.9),
    (2026, 2): (37.0, 32.5),
}

def _ceyrek(d): return (d.year, (d.month - 1)//3 + 1)

def rejim_hesapla(bugun=None):
    bugun = bugun or datetime.date.today()
    yc = _ceyrek(bugun)
    pol, enf = MAKRO.get(yc, MAKRO[max(MAKRO)])
    reel = round(pol - enf, 1)
    # histerezis: gir < -3 hisse, çık > +3 mevduat, arada → nötr
    if reel >= 3:   durus, lehte = "MEVDUAT LEHİNE", "mevduat"
    elif reel <= -3: durus, lehte = "HİSSE LEHİNE",   "hisse"
    else:           durus, lehte = "NÖTR",            "nötr"
    return {"politika": pol, "enflasyon": enf, "reel": reel,
            "durus": durus, "lehte": lehte}

# ─────────────────────────────────────────────────────────────
# 2) VOL-HEDEF RİSK (gerçek BIST'te doğrulanmış mantık)
#    agirlik = hedef_vol / gerçekleşen_vol ; hedef_vol = DD_bütçe × k
#    rejim mevduat lehine ise ×0.5 (savunma)
# ─────────────────────────────────────────────────────────────
def risk_pozisyon(dd_butce=0.015, k=2.5, gercek_vol=0.29, lehte="mevduat"):
    hedef_vol = dd_butce * k
    agirlik = hedef_vol / gercek_vol
    if lehte == "mevduat":
        agirlik *= 0.5
    agirlik = max(0.0, min(1.0, agirlik))
    return {"agirlik_pct": round(agirlik*100, 1),
            "mevduat_pct": round((1-agirlik)*100, 1),
            "dd_butce_pct": dd_butce*100, "hedef_vol_pct": round(hedef_vol*100,1),
            "gercek_vol_pct": round(gercek_vol*100,1), "k": k}

# ─────────────────────────────────────────────────────────────
# 3) AJANLAR + SİCİLLE-AĞIRLIKLI MERKEZ PUAN
#    sicil yoksa (N az) ağırlık tabanı düşük → aşırı-emin ajan merkezi şişiremez
# ─────────────────────────────────────────────────────────────
def merkez_ve_ajanlar(rej, risk, n_gun):
    getiri_sicil = 0.49   # yön tahmini ≈ yazı-tura (gece kanıtı)
    risk_sicil   = 0.92   # vol-hedef doğrulandı
    rejim_proxy  = 0.60   # rejim net AMA tahmin gücü ölçülmedi → ölçülü kredi

    # MERKEZ = "bir KARAR için sana ne kadar güvenmeliyim?"
    # Karar = yön (getiri) × boyut (risk). Yön yazı-turaysa, iyi boyutlama
    # zararı sınırlar ama EDGE yaratmaz → güven puanını GETİRİ ekseni taşır,
    # Risk yalnız zemin/fren olur. Böylece doğrulanmış-dar-beceri merkezi şişiremez.
    merkez = round(100 * (0.55*getiri_sicil + 0.30*risk_sicil + 0.15*rejim_proxy))

    ajanlar = [
        {"ad":"Rejim","ikon":"🧭","sc":72,"col":"up",
         "sub":f"reel faiz {'+' if rej['reel']>=0 else ''}%{rej['reel']} · {rej['durus'].lower()}"},
        {"ad":"Risk","ikon":"🛡️","sc":88,"col":"up","sub":"doğrulandı · sicil %92"},
        {"ad":"Getiri","ikon":"📈","sc":round(getiri_sicil*100),"col":"dn","sub":"≈ yazı-tura · sicil %49"},
        {"ad":"Denetçi","ikon":"🎯","sc":"↓","col":"pu",
         "sub":"Getiri çağrılarını sicille (%49) frenliyor","audit":True},
    ]
    q = "Bir karar için: risk disiplinine güven, getiri çağrısına güvenme."
    verdict = (f"Güven puanını <b>karar ekseni (getiri)</b> taşır ve o ≈ yazı-tura — "
               f"bu yüzden temkinli. Doğrulanmış olan <b>risk disiplini</b> (sicil %92): "
               f"zarar sınırlar ama edge yaratmaz. Rejim: <b>{rej['durus']}</b>. "
               f"İleri kayıt N={n_gun}; getiri sicili gerçekten yükselirse merkez de yükselir.")
    return merkez, ajanlar, q, verdict

# ─────────────────────────────────────────────────────────────
# 4) APP_DATA — omurganın beklediği dürüst veri
# ─────────────────────────────────────────────────────────────
def build_app_data(bugun=None):
    bugun = bugun or datetime.date.today()
    rej  = rejim_hesapla(bugun)
    risk = risk_pozisyon(lehte=rej["lehte"])
    # ileri kayıt gün sayısı (gerçek sistemde ileri_gunluk.csv satır sayısı)
    n_gun = 2
    merkez, ajanlar, q, verdict = merkez_ve_ajanlar(rej, risk, n_gun)

    # per-hisse: canlı fiyat beslemesi bağlanınca dolacak (şimdi dürüst örnek + sicil)
    stocks = [
        {"tk":"TATGD","nm":"Tat Gıda","dec":"İZLE","dcol":"blue","px":"—","ch":0,
         "rsi":56,"destek":18.27,"direnc":22,"hedef":22,"stop":19.35,"rr":2.1,"ay3":27,"sicil":49,
         "miniag":[["🧭 Rejim",rej['lehte'][:4],"m"],["🛡️ Risk",f"%{risk['agirlik_pct']}","m"],
                   ["📈 Getiri","%49","dn"],["📡 Nabız","—","m"],["🎯 Denetçi","düşür","pu"]],
         "akd":[["Oca","bos"],["Şub","bos"],["Mar","bos"],["Nis","bos"],["May","bos"],["Haz","bos"]],
         "recon":[["Kapanış fiyatı","—","ekle","bekle"],["Takas yoğunlaşması","—","ekle","bekle"],
                  ["AKD ilk 3 aracı","—","ekle","bekle"]]},
        {"tk":"GARAN","nm":"Garanti","dec":"İZLE","dcol":"blue","px":"—","ch":0,
         "rsi":61,"destek":132,"direnc":149,"hedef":149,"stop":132,"rr":1.7,"ay3":11.8,"sicil":53,
         "miniag":[["🧭 Rejim",rej['lehte'][:4],"m"],["🛡️ Risk",f"%{risk['agirlik_pct']}","m"],
                   ["📈 Getiri","%53","or"],["📡 Nabız","—","m"],["⚖️ Çelişki","—","pu"]],
         "akd":[["Oca","bos"],["Şub","bos"],["Mar","bos"],["Nis","bos"],["May","bos"],["Haz","bos"]],
         "recon":[["Kapanış fiyatı","—","ekle","bekle"],["Takas yoğunlaşması","—","ekle","bekle"]]},
    ]

    return {
        "uretildi": bugun.isoformat(),
        "delay_dk": 15,
        "rejim": rej, "risk": risk,
        "master": {"q": q, "skor": merkez, "verdict": verdict},
        "ajanlar": ajanlar,
        "stocks": stocks,
        "defter": {"deger":100000,"nakit":100000,"pozisyon":0,"maliyet":0,
                   "gz_acik":0,"gz_kapali":0,"komisyon":0},
        "nabiz": {"lab":"Bağlanınca","val":0.5,
                  "sub":"ekonomi RSS bağlanınca dolacak (Twitter/X ayrı faz)",
                  "haber":[["—","Haber beslemesi henüz bağlı değil","0.0","m"]]},
    }

# ─────────────────────────────────────────────────────────────
# 5) HTML üretimi — omurgaya enjekte et
# ─────────────────────────────────────────────────────────────
def build_html(template_path=TEMPLATE):
    data = build_app_data()
    tpl = pathlib.Path(template_path).read_text(encoding="utf-8")
    inject = "<script>window.__APP_DATA__ = " + json.dumps(data, ensure_ascii=False) + ";</script>\n"
    # ilk <script>'ten hemen önce veriyi tanımla → demo bypass edilir
    html = tpl.replace("<script>", inject + "<script>", 1)
    return html, data

def write_html(out=OUT):
    html, data = build_html()
    pathlib.Path(out).write_text(html, encoding="utf-8")
    return out, data

# ─────────────────────────────────────────────────────────────
# 6) Streamlit servis (Cloud) — opsiyonel
# ─────────────────────────────────────────────────────────────
def run_streamlit():
    import streamlit as st
    import streamlit.components.v1 as components
    st.set_page_config(page_title="APEX", page_icon="⚡", layout="centered")
    html, data = build_html()
    components.html(html, height=820, scrolling=True)
    with st.expander("Dürüstlük · bu ekrandaki sayılar nereden geliyor?"):
        st.write(f"Rejim: reel faiz %{data['rejim']['reel']} → **{data['rejim']['durus']}** "
                 f"(statik makro tablodan, canlı veri gerekmez).")
        st.write(f"Risk: vol-hedef → önerilen hisse **%{data['risk']['agirlik_pct']}** "
                 f"(DD bütçesi %{data['risk']['dd_butce_pct']}, k={data['risk']['k']}).")
        st.write(f"Merkez puan **{data['master']['skor']}/100** — sicille ağırlıklı; "
                 f"getiri yönü ≈ yazı-tura olduğu için düşük tutuluyor.")
        st.caption("Per-hisse fiyat, AKD ve nabız beslemesi bağlanınca dolacak. Uydurma sayı yok.")

# ─────────────────────────────────────────────────────────────
# 7) GİRİŞ — Streamlit Cloud mu, düz python mu otomatik anla
#    streamlit run app.py  → streamlit sys.modules'te olur → servis et
#    python app.py         → apex.html üret
# ─────────────────────────────────────────────────────────────
import sys as _sys
if "streamlit" in _sys.modules:
    run_streamlit()
elif __name__ == "__main__":
    out, data = write_html()
    print(f"✓ {out} üretildi.")
    print(f"  rejim={data['rejim']['durus']} (reel %{data['rejim']['reel']}) · "
          f"risk hisse %{data['risk']['agirlik_pct']} · merkez {data['master']['skor']}/100")
