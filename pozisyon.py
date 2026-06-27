"""
APEX · POZİSYON / RİSK-ÖLÇEKLEME — vol-hedefleme (risk yönetimi, getiri tahmini DEĞİL).
Mantık: hisse ağırlığı = hedef_oynaklık / gerçekleşen_oynaklık (clamp 0..1).
DD bütçesi → hedef vol dönüşümü KABA kuraldır (yıllık ~max DD ≈ k×yıllık vol, k~2.5);
garanti değil, mertebe tahmini. Rejim "mevduat lehine" ise temkin tilt (ağırlığı kıs).
Amaç: "ya hep ya hiç" yerine bütçeye göre ölçekli maruziyet + tradeoff'u şeffaf göstermek.
"""
import numpy as np

K_DD = 2.5  # DD bütçesi → hedef vol kaba katsayısı


def yillik_vol(close, pencere=60):
    c = np.asarray(close, dtype=float)
    c = c[np.isfinite(c) & (c > 0)]
    if len(c) < 10:
        return None
    r = np.diff(np.log(c[-(pencere + 1):]))
    if len(r) < 5:
        return None
    return float(np.std(r, ddof=1) * np.sqrt(252))


def vol_hedef_agirlik(yvol, dd_butce_pct, k=K_DD, w_max=1.0):
    if not yvol or yvol <= 0:
        return 0.0
    hedef_vol = (dd_butce_pct / 100.0) / k
    return float(min(w_max, max(0.0, hedef_vol / yvol)))


def rejim_carpan(durus):
    # rejim kanıtlanmış edge değil → sadece temkin TİLT'i, tahmin değil
    return 1.0 if durus == "HİSSE LEHİNE" else 0.5


def oneri(close, durus, dd_butce=1.5):
    yvol = yillik_vol(close)
    w_saf = vol_hedef_agirlik(yvol, dd_butce)
    carp = rejim_carpan(durus)
    w = round(min(1.0, w_saf * carp), 3)
    return {"yvol": yvol, "w_saf": round(w_saf, 3), "carpan": carp, "w": w, "dd_butce": dd_butce}


def tradeoff_tablosu(close, butceler=(1.5, 5, 10, 20)):
    yvol = yillik_vol(close)
    return yvol, [(b, round(vol_hedef_agirlik(yvol, b) * 100, 1)) for b in butceler]


if __name__ == "__main__":
    rng = np.random.default_rng(0)
    px = 100 * np.cumprod(1 + rng.normal(0, 0.02, 300))  # ~%32 yıllık vol
    print("yvol:", yillik_vol(px))
    print("oneri (MEVDUAT LEHİNE):", oneri(px, "MEVDUAT LEHİNE"))
    print("oneri (HİSSE LEHİNE):", oneri(px, "HİSSE LEHİNE"))
    print("tradeoff:", tradeoff_tablosu(px))
