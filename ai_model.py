# -*- coding: utf-8 -*-
"""
ai_model.py — APEX AI katmanı (makine öğrenmesi).

OHLCV'den özellik çıkarır; sonraki N (5) işlem günü için POZİTİF getiri olasılığını
WALK-FORWARD doğrulamayla tahmin eder. sklearn varsa LogReg + RandomForest +
GradientBoosting ENSEMBLE; yoksa numpy logistic-regression fallback ile çalışır.

DÜRÜSTLÜK İLKESİ — Etkin Piyasa Hipotezi gereği %100 tahmin İMKÂNSIZDIR. Bu katman
garanti vermez; olasılıkları KALİBRE eder (≈%5–95 bandı), zayıf/belirsiz sinyalleri
sert eler. Kazanç, isabetten değil; isabet + risk/ödül + stop disiplininden gelir.

DÜZELTME (F1, 27 Haziran 2026): walk-forward çağrısındaki "sahte sıfır" bug'ı giderildi.
Eskiden son 'ufuk' (5) güne yapay 0 etiketi ekleniyordu → wf_dogruluk/guven biraz yanlış
çıkıyordu. Artık walk-forward yalnızca gerçek etiketli (Xtr, ytr) ile çalışıyor.
NOT: Bu fix yalnızca raporlanan güven sayısını düzeltir; backtest işlem kararları
(olasilik/yon) etkilenmez.
"""
import numpy as np

try:
    from sklearn.linear_model import LogisticRegression
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
    from sklearn.preprocessing import StandardScaler
    SKLEARN = True
except Exception:
    SKLEARN = False

OZELLIK_ADI = [
    "Getiri-1g", "Getiri-3g", "Getiri-5g", "Getiri-10g", "RSI",
    "MA20 sapma", "MA50 sapma", "MA kesişim", "Oynaklık-10", "Hacim oranı",
    "Bollinger %b", "Momentum-10", "MACD", "ATR%", "Zirveye uzaklık", "Dibe uzaklık",
]


def _rsi(close, p=14):
    d = np.diff(close, prepend=close[0])
    up = np.where(d > 0, d, 0.0)
    dn = np.where(d < 0, -d, 0.0)
    ru = _ema(up, p)
    rd = _ema(dn, p)
    rs = ru / (rd + 1e-9)
    return 100 - 100 / (1 + rs)


def _ema(x, p):
    a = 2 / (p + 1)
    out = np.empty_like(x, dtype=float)
    out[0] = x[0]
    for i in range(1, len(x)):
        out[i] = a * x[i] + (1 - a) * out[i - 1]
    return out


def _sma(x, p):
    c = np.cumsum(np.insert(x, 0, 0.0))
    out = (c[p:] - c[:-p]) / p
    return np.concatenate([np.full(p - 1, out[0] if len(out) else x[0]), out])


def _ozellik_matris(df):
    """OHLCV DataFrame → (X, kapanis). Her satır o güne kadarki bilgiyle (nedensel)."""
    close = df["Close"].to_numpy(dtype=float)
    high = df["High"].to_numpy(dtype=float)
    low = df["Low"].to_numpy(dtype=float)
    vol = df["Volume"].to_numpy(dtype=float) if "Volume" in df else np.ones_like(close)
    n = len(close)
    if n < 60:
        return None, close

    ret = lambda k: np.concatenate([np.zeros(k), close[k:] / close[:-k] - 1])
    sma20, sma50 = _sma(close, 20), _sma(close, 50)
    std10 = np.array([close[max(0, i - 10):i + 1].std() / (close[i] + 1e-9) for i in range(n)])
    volma = _sma(vol, 20)
    bb_m, bb_s = sma20, np.array([close[max(0, i - 20):i + 1].std() for i in range(n)])
    bb_hi, bb_lo = bb_m + 2 * bb_s, bb_m - 2 * bb_s
    bbpos = (close - bb_lo) / (bb_hi - bb_lo + 1e-9)
    mom10 = ret(10)
    macd = _ema(close, 12) - _ema(close, 26)
    macd_h = (macd - _ema(macd, 9)) / (close + 1e-9)
    tr = np.maximum(high - low, np.abs(high - np.roll(close, 1)))
    atrp = _ema(tr, 14) / (close + 1e-9)
    hi20 = np.array([high[max(0, i - 20):i + 1].max() for i in range(n)])
    lo20 = np.array([low[max(0, i - 20):i + 1].min() for i in range(n)])

    X = np.column_stack([
        ret(1), ret(3), ret(5), ret(10), _rsi(close) / 100,
        close / (sma20 + 1e-9) - 1, close / (sma50 + 1e-9) - 1, sma20 / (sma50 + 1e-9) - 1,
        std10, vol / (volma + 1e-9) - 1, bbpos, mom10, macd_h, atrp,
        close / (hi20 + 1e-9) - 1, close / (lo20 + 1e-9) - 1,
    ])
    X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)
    return X, close


def _numpy_lojistik(Xtr, ytr, Xpred, iters=300, lr=0.1):
    """sklearn yoksa: standardize + gradient-descent logistic regression."""
    mu, sd = Xtr.mean(0), Xtr.std(0) + 1e-9
    Z = (Xtr - mu) / sd
    Zp = (Xpred - mu) / sd
    w = np.zeros(Z.shape[1]); b = 0.0
    m = len(ytr)
    for _ in range(iters):
        p = 1 / (1 + np.exp(-(Z @ w + b)))
        g = p - ytr
        w -= lr * (Z.T @ g / m + 0.01 * w)
        b -= lr * g.mean()
    pr = 1 / (1 + np.exp(-(Zp @ w + b)))
    return float(pr[0]), np.abs(w)


def _ensemble_tahmin(Xtr, ytr, Xpred):
    """Dönen: (olasilik, uyusmazlik_std, onem[])."""
    if SKLEARN and len(np.unique(ytr)) > 1:
        sc = StandardScaler().fit(Xtr)
        Ztr, Zp = sc.transform(Xtr), sc.transform(Xpred)
        modeller = [
            LogisticRegression(max_iter=200, C=0.5),
            RandomForestClassifier(n_estimators=40, max_depth=4, min_samples_leaf=8, random_state=0, n_jobs=1),
            GradientBoostingClassifier(n_estimators=40, max_depth=3, learning_rate=0.08, subsample=0.8, random_state=0),
        ]
        probs, onemler = [], []
        for mdl in modeller:
            try:
                mdl.fit(Ztr, ytr)
                probs.append(float(mdl.predict_proba(Zp)[0, 1]))
                if hasattr(mdl, "feature_importances_"):
                    onemler.append(mdl.feature_importances_)
                elif hasattr(mdl, "coef_"):
                    onemler.append(np.abs(mdl.coef_[0]))
            except Exception:
                pass
        if probs:
            onem = np.mean(onemler, axis=0) if onemler else np.ones(Xtr.shape[1])
            return float(np.mean(probs)), float(np.std(probs)), onem
    # fallback: numpy logistic + bootstrap (uyuşmazlık için)
    p0, onem = _numpy_lojistik(Xtr, ytr, Xpred)
    boots = []
    rng = np.random.default_rng(0)
    for _ in range(3):
        idx = rng.integers(0, len(ytr), len(ytr))
        if len(np.unique(ytr[idx])) > 1:
            boots.append(_numpy_lojistik(Xtr[idx], ytr[idx], Xpred)[0])
    return p0, (float(np.std(boots)) if boots else 0.15), onem


def _walk_forward(X, y, katman=3):
    """Genişleyen pencere ile örneklem-dışı (OOS) doğruluk. Look-ahead YOK."""
    n = len(y)
    if n < 80:
        return 0.5, 0
    dogru, top = 0, 0
    bas = int(n * 0.4)
    adim = max(10, (n - bas) // katman)
    i = bas
    while i + adim <= n:
        Xtr, ytr = X[:i], y[:i]
        Xte, yte = X[i:i + adim], y[i:i + adim]
        if len(np.unique(ytr)) < 2:
            i += adim; continue
        try:
            if SKLEARN:
                sc = StandardScaler().fit(Xtr)
                mdl = LogisticRegression(max_iter=200, C=0.5).fit(sc.transform(Xtr), ytr)
                tah = mdl.predict(sc.transform(Xte))
            else:
                mu, sd = Xtr.mean(0), Xtr.std(0) + 1e-9
                w = np.zeros(Xtr.shape[1]); b = 0.0
                Z = (Xtr - mu) / sd
                for _ in range(200):
                    p = 1 / (1 + np.exp(-(Z @ w + b))); g = p - ytr
                    w -= 0.1 * (Z.T @ g / len(ytr) + 0.01 * w); b -= 0.1 * g.mean()
                tah = (1 / (1 + np.exp(-(((Xte - mu) / sd) @ w + b))) > 0.5).astype(int)
            dogru += int((tah == yte).sum()); top += len(yte)
        except Exception:
            pass
        i += adim
    return (dogru / top if top else 0.5), top


def ai_analiz(df, ufuk=5):
    """
    Dönen dict:
      olasilik   : pozitif getiri olasılığı % (kalibre, 5–95)
      guven      : walk-forward doğruluk + örnek gücü %
      belirsizlik: model uyuşmazlığı + zayıf örnek %
      skor       : 0–100 birleşik AI skoru
      quantum    : en seçici "AI QUANTUM AL" sınıfı (bool)
      yon        : "AL" / "NÖTR" / "SAT"
      wf_dogruluk: OOS doğruluk %
      n_ornek    : eğitim örnek sayısı
      ozellikler : en etkili 4 özellik [(ad, agirlik%)]
      durum      : "model" / "yetersiz_veri"
    """
    try:
        X, close = _ozellik_matris(df)
        if X is None:
            return _bos("yetersiz_veri")
        n = len(close)
        y_full = (close[ufuk:] / close[:-ufuk] - 1 > 0).astype(int)
        Xtr = X[20:n - ufuk]
        ytr = y_full[20:]
        m = min(len(Xtr), len(ytr))
        Xtr, ytr = Xtr[:m], ytr[:m]
        if m < 60 or len(np.unique(ytr)) < 2:
            return _bos("yetersiz_veri")

        Xpred = X[-1:].copy()
        olasilik, uyusmazlik, onem = _ensemble_tahmin(Xtr, ytr, Xpred)
        # F1 DÜZELTME: sahte sıfır padding kaldırıldı; walk-forward yalnızca
        # gerçek etiketli (Xtr, ytr) ile çalışıyor (ikisi de uzunluk m, hizalı).
        wf_acc, wf_n = _walk_forward(Xtr, ytr)

        # kalibrasyon: aşırı uçları kırp, taban oranına çek (asla 0/100 değil)
        taban = float(ytr.mean())
        ol = 100 * (0.75 * olasilik + 0.25 * taban)
        ol = float(np.clip(ol, 5, 95))

        ornek_g = min(1.0, m / 180)
        guven = float(np.clip((wf_acc * 100) * (0.6 + 0.4 * ornek_g), 35, 90))
        belirsizlik = float(np.clip(uyusmazlik * 220 + (1 - ornek_g) * 25 + (1 - abs(olasilik - 0.5) * 2) * 20, 5, 80))

        skor = float(np.clip(ol * 0.5 + guven * 0.3 + (60 - belirsizlik) * 0.2, 0, 100))
        yon = "AL" if ol >= 56 else ("SAT" if ol <= 44 else "NÖTR")
        quantum = (ol >= 62 and guven >= 58 and belirsizlik <= 35 and yon == "AL")

        idx = np.argsort(onem)[::-1][:4]
        to = float(onem.sum()) + 1e-9
        ozellikler = [(OZELLIK_ADI[i], round(100 * onem[i] / to)) for i in idx]

        return {
            "olasilik": round(ol), "guven": round(guven), "belirsizlik": round(belirsizlik),
            "skor": round(skor), "quantum": bool(quantum), "yon": yon,
            "wf_dogruluk": round(wf_acc * 100), "n_ornek": int(m),
            "ozellikler": ozellikler, "motor": "ensemble" if SKLEARN else "numpy",
            "durum": "model",
        }
    except Exception:
        return _bos("hata")


def _bos(durum):
    return {"olasilik": 50, "guven": 0, "belirsizlik": 100, "skor": 0, "quantum": False,
            "yon": "NÖTR", "wf_dogruluk": 0, "n_ornek": 0, "ozellikler": [], "motor": "-", "durum": durum}
