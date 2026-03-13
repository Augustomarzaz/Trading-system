# ============================================================
#  engine.py — Motor de análisis central
#  Screener fundamental + Señales técnicas + Backtesting
#  con métricas profesionales completas
# ============================================================

import yfinance as yf
import pandas as pd
import ta as ta_lib
import numpy as np
from scipy import stats
from datetime import datetime
import warnings
warnings.filterwarnings("ignore")

from config import CONFIG, TECNICO, RIESGO


# ── Detección de mercado por ticker ──────────────────────
def get_mercado(ticker):
    cedear_sufijos = [".BA"]
    cedears_conocidos = ["GGAL","YPF","BMA","BBAR","CEPU","LOMA","SUPV","TXAR","MIRG"]
    if any(ticker.endswith(s) for s in cedear_sufijos):
        return "CEDEAR"
    if ticker in cedears_conocidos:
        return "CEDEAR"
    return "NYSE/NASDAQ"


# ── SCREENER FUNDAMENTAL ──────────────────────────────────
def screener_fundamental(tickers, params):
    resultados = []
    for ticker in tickers:
        try:
            info   = yf.Ticker(ticker).info
            pe     = info.get("trailingPE",      None)
            roe    = info.get("returnOnEquity",  None)
            de     = info.get("debtToEquity",    None)
            nombre = info.get("shortName",       ticker)
            sector = info.get("sector",          "—")

            if None in [pe, roe, de]:
                resultados.append({
                    "ticker": ticker, "nombre": nombre, "sector": sector,
                    "mercado": get_mercado(ticker),
                    "estado": "sin_datos", "motivo": "Datos incompletos",
                    "pe": None, "roe": None, "de": None
                })
                continue

            de_norm = de / 100 if de > 5 else de
            fallos  = []
            if pe     >= params["pe_max"]:              fallos.append(f"P/E {pe:.1f}")
            if roe    <= params["roe_min"]:              fallos.append(f"ROE {roe*100:.1f}%")
            if de_norm >= params["de_max"]:             fallos.append(f"D/E {de_norm:.2f}")

            resultados.append({
                "ticker":  ticker,
                "nombre":  nombre,
                "sector":  sector,
                "mercado": get_mercado(ticker),
                "estado":  "ok" if not fallos else "fail",
                "motivo":  ", ".join(fallos) if fallos else "Pasa todos los filtros",
                "pe":      round(pe, 1),
                "roe":     round(roe * 100, 1),
                "de":      round(de_norm, 2),
            })
        except Exception as e:
            resultados.append({
                "ticker": ticker, "nombre": ticker, "sector": "—",
                "mercado": get_mercado(ticker),
                "estado": "error", "motivo": str(e)[:60],
                "pe": None, "roe": None, "de": None
            })
    return resultados


# ── SEÑALES TÉCNICAS ──────────────────────────────────────
def calcular_senales(ticker, params):
    try:
        df = yf.download(ticker, period="6mo", interval="1d", progress=False)
        if df.empty or len(df) < 30:
            return None
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        df["EMA_r"] = ta_lib.trend.ema_indicator(df["Close"], window=TECNICO["ema_rapida"])
        df["EMA_l"] = ta_lib.trend.ema_indicator(df["Close"], window=TECNICO["ema_lenta"])
        df["RSI"]   = ta_lib.momentum.rsi(df["Close"], window=TECNICO["rsi_periodo"])

        hoy, ayer = df.iloc[-1], df.iloc[-2]
        precio    = round(float(hoy["Close"]),    2)
        rsi       = round(float(hoy["RSI"]),      1)
        ema_r     = float(hoy["EMA_r"])
        ema_l     = float(hoy["EMA_l"])

        cruce_alcista  = (ema_r > ema_l)  and (float(ayer["EMA_r"]) <= float(ayer["EMA_l"]))
        cruce_bajista  = (ema_r < ema_l)  and (float(ayer["EMA_r"]) >= float(ayer["EMA_l"]))

        senal = "COMPRA"  if (rsi < params["rsi_entrada"] or cruce_alcista) else \
                "VENDER"  if (rsi > params["rsi_salida"]  or cruce_bajista) else \
                "ESPERAR"

        precios_hist = [round(float(x), 2) for x in df["Close"].tail(60).tolist()]

        return {
            "ticker":      ticker,
            "precio":      precio,
            "rsi":         rsi,
            "ema_r":       round(ema_r, 2),
            "ema_l":       round(ema_l, 2),
            "cruce_alc":   cruce_alcista,
            "cruce_baj":   cruce_bajista,
            "senal":       senal,
            "stop_loss":   round(precio * (1 - params["stop_loss"]),   2),
            "take_profit": round(precio * (1 + params["take_profit"]), 2),
            "precios_hist":precios_hist,
        }
    except:
        return None


# ── BACKTESTING PROFESIONAL ───────────────────────────────
def backtest(ticker, params):
    try:
        periodo = params.get("periodo", "2y")
        df  = yf.download(ticker,           period=periodo, interval="1d", progress=False)
        bm  = yf.download(CONFIG["benchmark"], period=periodo, interval="1d", progress=False)

        for d in [df, bm]:
            if isinstance(d.columns, pd.MultiIndex):
                d.columns = d.columns.get_level_values(0)

        df["EMA_r"] = ta_lib.trend.ema_indicator(df["Close"], window=TECNICO["ema_rapida"])
        df["EMA_l"] = ta_lib.trend.ema_indicator(df["Close"], window=TECNICO["ema_lenta"])
        df["RSI"]   = ta_lib.momentum.rsi(df["Close"], window=TECNICO["rsi_periodo"])
        df = df.dropna()

        bm_close = bm["Close"].reindex(df.index, method="ffill").fillna(method="bfill")

        capital, posicion, precio_compra, fecha_compra = CONFIG["capital"], 0, 0, None
        trades, equity = [], []

        for i in range(1, len(df)):
            f, fa   = df.iloc[i], df.iloc[i - 1]
            precio  = float(f["Close"])
            rsi     = float(f["RSI"])
            er, el  = float(f["EMA_r"]), float(f["EMA_l"])
            era     = float(fa["EMA_r"])
            ela     = float(fa["EMA_l"])
            fecha   = df.index[i]

            equity.append(capital if posicion == 0 else posicion * precio)

            if posicion == 0:
                cruce = er > el and era <= ela
                if rsi < params["rsi_entrada"] or cruce:
                    posicion, precio_compra, fecha_compra = capital / precio, precio, fecha
            else:
                cambio = (precio - precio_compra) / precio_compra
                motivo = None
                if cambio >= params["take_profit"]:        motivo = "Take Profit"
                elif cambio <= -params["stop_loss"]:       motivo = "Stop Loss"
                elif rsi > params["rsi_salida"]:           motivo = "RSI Salida"
                elif er < el and era >= ela:               motivo = "Cruce bajista"

                if motivo:
                    capital = posicion * precio
                    trades.append({
                        "entrada":       str(fecha_compra)[:10],
                        "salida":        str(fecha)[:10],
                        "precio_compra": round(precio_compra, 2),
                        "precio_venta":  round(precio, 2),
                        "retorno_pct":   round(cambio * 100, 4),
                        "ganancia_usd":  round(cambio * posicion * precio_compra, 2),
                        "duracion_dias": (fecha - fecha_compra).days,
                        "motivo":        motivo,
                        "resultado":     "WIN" if cambio > 0 else "LOSS",
                    })
                    posicion = 0

        if posicion > 0:
            capital = posicion * float(df["Close"].iloc[-1])

        if not trades or len(equity) < 10:
            return None

        # ── Métricas ────────────────────────────────────
        rf_d     = (1 + CONFIG["rf_anual"]) ** (1/252) - 1
        eq_s     = pd.Series(equity)
        eq_ret   = eq_s.pct_change().dropna().values

        bm_vals  = bm_close.values[-len(equity):]
        bm_ret   = pd.Series(bm_vals).pct_change().dropna().values
        n        = min(len(eq_ret), len(bm_ret))
        eq_ret, bm_ret = eq_ret[-n:], bm_ret[-n:]

        wins     = [t for t in trades if t["resultado"] == "WIN"]
        losses   = [t for t in trades if t["resultado"] == "LOSS"]

        total_t   = len(trades)
        win_rate  = len(wins) / total_t * 100 if total_t else 0
        ret_total = (capital - CONFIG["capital"]) / CONFIG["capital"] * 100
        dias      = max((df.index[-1] - df.index[0]).days, 1)
        años      = dias / 365.25
        ret_anual = ((capital / CONFIG["capital"]) ** (1/años) - 1) * 100 if años > 0 else 0

        g_media   = np.mean([t["retorno_pct"] for t in wins])   if wins   else 0
        p_media   = abs(np.mean([t["retorno_pct"] for t in losses])) if losses else 0
        pf        = (g_media * len(wins)) / (p_media * len(losses)) if losses and p_media > 0 else 99

        # Benchmark
        bm_i      = float(bm_close.iloc[0])
        bm_f      = float(bm_close.iloc[-1])
        bm_ret_t  = (bm_f - bm_i) / bm_i * 100
        bm_anual  = ((bm_f / bm_i) ** (1/años) - 1) * 100 if años > 0 else 0
        alpha_t   = ret_total - bm_ret_t

        # Sharpe
        exc       = eq_ret - rf_d
        sharpe    = (np.mean(exc) / np.std(exc)) * np.sqrt(252) if np.std(exc) > 0 else 0

        # Sortino
        neg       = exc[exc < 0]
        dd_std    = np.std(neg) * np.sqrt(252) if len(neg) > 0 else 1e-6
        sortino   = (np.mean(exc) * 252) / dd_std

        # Treynor + Alpha CAPM
        beta_v, alpha_v, *_ = stats.linregress(bm_ret, eq_ret)
        treynor   = ((np.mean(eq_ret) - rf_d) * 252) / beta_v if beta_v != 0 else 0
        alpha_an  = alpha_v * 252 * 100

        # Max Drawdown
        rolling   = eq_s.cummax()
        dd_s      = (eq_s - rolling) / rolling * 100
        max_dd    = float(dd_s.min())
        dd_dur    = int((dd_s < 0).sum())

        # Calmar
        calmar    = ret_anual / abs(max_dd) if max_dd != 0 else 0

        # Volatilidad
        vol       = np.std(eq_ret) * np.sqrt(252) * 100

        # VaR / CVaR
        var95     = float(np.percentile(eq_ret, 5)) * 100
        cvar95    = float(np.mean(eq_ret[eq_ret <= np.percentile(eq_ret, 5)])) * 100

        # AUC
        eq_norm   = (eq_s - eq_s.min()) / (eq_s.max() - eq_s.min() + 1e-9)
        auc       = float(np.trapz(eq_norm.values) / len(eq_norm))

        # Motivos
        motivos   = {}
        for t in trades:
            motivos[t["motivo"]] = motivos.get(t["motivo"], 0) + 1

        return {
            "ticker":         ticker,
            "total_trades":   total_t,
            "wins":           len(wins),
            "losses":         len(losses),
            "win_rate":       round(win_rate,   2),
            "profit_factor":  round(pf,         2),
            "duracion_media": round(np.mean([t["duracion_dias"] for t in trades]), 1),
            "ganancia_media": round(g_media,    2),
            "perdida_media":  round(p_media,    2),
            "retorno":        round(ret_total,  2),
            "retorno_anual":  round(ret_anual,  2),
            "capital_final":  round(capital,    2),
            "bm_retorno":     round(bm_ret_t,   2),
            "bm_anual":       round(bm_anual,   2),
            "alpha_total":    round(alpha_t,    2),
            "alpha_anual":    round(alpha_an,   2),
            "beta":           round(beta_v,     4),
            "sharpe":         round(sharpe,     4),
            "sortino":        round(sortino,    4),
            "treynor":        round(treynor,    4),
            "calmar":         round(calmar,     4),
            "max_dd":         round(max_dd,     2),
            "max_dd_dur":     dd_dur,
            "volatilidad":    round(vol,        2),
            "var_95":         round(var95,      4),
            "cvar_95":        round(cvar95,     4),
            "auc":            round(auc,        4),
            "motivos":        motivos,
            "trades":         trades,
            "equity_curve":   [round(v, 2) for v in equity],
        }
    except Exception as e:
        return None


# ── FUNCIÓN PRINCIPAL ─────────────────────────────────────
def run_analysis(universe, params):
    fund    = screener_fundamental(universe, params)
    aprobadas = [r["ticker"] for r in fund if r["estado"] == "ok"]

    senales, backtests = {}, {}
    for ticker in aprobadas:
        s = calcular_senales(ticker, params)
        if s:
            senales[ticker] = s
        b = backtest(ticker, params)
        if b:
            backtests[ticker] = b

    return {
        "fundamental": fund,
        "senales":     senales,
        "backtests":   backtests,
        "timestamp":   datetime.now().isoformat(),
    }
