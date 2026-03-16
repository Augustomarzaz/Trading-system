# ============================================================
#  app.py — Dashboard v4
#  Un solo veredicto claro + detalle expandible
# ============================================================

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime

import ta as ta_lib
from patterns import analizar_patrones
from alerts   import send_telegram
from config   import TECNICO, RIESGO
from engine   import backtest

st.set_page_config(
    page_title="Trading System", page_icon="📈",
    layout="wide", initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;500;700&family=DM+Mono:wght@300;400;500&display=swap');
*, *::before, *::after { box-sizing:border-box; margin:0; padding:0; }
html,body,[class*="css"] { font-family:'Syne',sans-serif; background:#080b10!important; color:#dde3ee; }
.stApp { background:#080b10!important; }
.stApp > header { background:transparent!important; }
div[data-testid="stSidebar"] { display:none; }

/* ── VEREDICTO ── */
.verdict-wrap {
  border-radius:20px; padding:40px 44px; margin-bottom:20px;
  display:flex; flex-direction:column; align-items:flex-start;
}
.verdict-wrap.cf  { background:#071a0f; border:2px solid #1a6b3a; }
.verdict-wrap.c   { background:#0d1f14; border:1px solid #1a4731; }
.verdict-wrap.n   { background:#0d1117; border:1px solid #1e2a3a; }
.verdict-wrap.v   { background:#1f0d0d; border:1px solid #4a1515; }
.verdict-wrap.vf  { background:#1a0707; border:2px solid #8b1a1a; }

.verdict-tag {
  font-family:'DM Mono',monospace; font-size:11px; letter-spacing:.2em;
  text-transform:uppercase; padding:5px 14px; border-radius:4px; margin-bottom:18px;
}
.verdict-tag.cf  { background:rgba(72,187,120,.15); color:#48bb78; border:1px solid rgba(72,187,120,.3); }
.verdict-tag.c   { background:rgba(104,211,145,.1);  color:#68d391; border:1px solid rgba(104,211,145,.25); }
.verdict-tag.n   { background:rgba(160,174,192,.08); color:#a0aec0; border:1px solid rgba(160,174,192,.2); }
.verdict-tag.v   { background:rgba(245,101,101,.1);  color:#fc8181; border:1px solid rgba(245,101,101,.25); }
.verdict-tag.vf  { background:rgba(229,62,62,.15);   color:#f56565; border:1px solid rgba(229,62,62,.3); }

.verdict-main {
  font-size:52px; font-weight:700; letter-spacing:-.02em; line-height:1; margin-bottom:8px;
}
.verdict-main.cf { color:#48bb78; }
.verdict-main.c  { color:#68d391; }
.verdict-main.n  { color:#a0aec0; }
.verdict-main.v  { color:#fc8181; }
.verdict-main.vf { color:#f56565; }

.verdict-ticker { font-size:15px; color:#718096; margin-bottom:24px; letter-spacing:.03em; }

.verdict-levels {
  display:flex; gap:28px; flex-wrap:wrap;
  padding-top:20px; border-top:1px solid rgba(255,255,255,.06); width:100%;
}
.vl-item { }
.vl-label { font-size:10px; letter-spacing:.14em; text-transform:uppercase; color:#4a5568; margin-bottom:4px; }
.vl-val   { font-family:'DM Mono',monospace; font-size:18px; }
.vl-val.sl  { color:#fc8181; }
.vl-val.tp  { color:#68d391; }
.vl-val.neu { color:#a0aec0; }

.verdict-razon {
  font-size:13px; color:#718096; line-height:1.8; margin-bottom:20px;
  max-width:640px;
}
.verdict-razon b { color:#e2e8f0; }

/* Score bar */
.score-bar-wrap { width:100%; margin-bottom:20px; }
.score-bar-track {
  width:100%; height:8px; background:#0d1117; border-radius:4px;
  overflow:hidden; position:relative;
}
.score-bar-fill {
  height:100%; border-radius:4px;
  transition: width .6s ease;
}
.score-labels {
  display:flex; justify-content:space-between;
  font-family:'DM Mono',monospace; font-size:10px; color:#4a5568; margin-top:5px;
}

/* Detalle cards */
.det-grid { display:grid; grid-template-columns:repeat(4,1fr); gap:10px; margin-bottom:16px; }
.det-card { background:#0d1117; border:1px solid #1e2a3a; border-radius:10px; padding:14px 16px; }
.det-label { font-size:10px; letter-spacing:.1em; text-transform:uppercase; color:#4a5568; margin-bottom:6px; }
.det-val   { font-family:'DM Mono',monospace; font-size:19px; color:#e2e8f0; }
.det-val.g { color:#68d391; } .det-val.r { color:#fc8181; } .det-val.a { color:#f6ad55; }
.det-sub   { font-size:10px; color:#4a5568; margin-top:3px; }

/* Señales internas */
.signals-list { display:flex; flex-direction:column; gap:8px; }
.signal-row {
  display:flex; align-items:center; justify-content:space-between;
  background:#0d1117; border:1px solid #1e2a3a; border-radius:8px;
  padding:10px 14px;
}
.sr-left  { display:flex; align-items:center; gap:10px; }
.sr-dot   { width:8px; height:8px; border-radius:50%; flex-shrink:0; }
.sr-dot.g { background:#68d391; } .sr-dot.r { background:#fc8181; } .sr-dot.a { background:#f6ad55; }
.sr-name  { font-size:13px; color:#e2e8f0; }
.sr-desc  { font-size:11px; color:#718096; margin-top:1px; }
.sr-badge { font-family:'DM Mono',monospace; font-size:10px; padding:2px 8px; border-radius:3px; }
.srb-g { background:rgba(104,211,145,.1); color:#68d391; }
.srb-r { background:rgba(252,129,129,.1); color:#fc8181; }
.srb-a { background:rgba(246,173,85,.1);  color:#f6ad55; }

/* Fund */
.fund-wrap { background:#0a0d13; border:1px solid #1a2030; border-radius:14px; padding:22px 26px; }
.fund-hdr  { font-size:11px; letter-spacing:.16em; text-transform:uppercase; color:#2d4a6b;
  margin-bottom:16px; padding-bottom:10px; border-bottom:1px solid #111827; }
.fund-g4   { display:grid; grid-template-columns:repeat(4,1fr); gap:14px; margin-bottom:14px; }
.fi-label  { font-size:10px; letter-spacing:.1em; text-transform:uppercase; color:#2d4a6b; margin-bottom:3px; }
.fi-val    { font-family:'DM Mono',monospace; font-size:14px; color:#8aa4c8; }
.fi-val.g  { color:#68d391; } .fi-val.r { color:#fc8181; }
.fund-desc { font-size:11px; color:#4a5568; line-height:1.8; border-top:1px solid #111827; padding-top:12px; }

.divider-lbl { display:flex; align-items:center; gap:10px; margin:24px 0 16px; }
.divider-lbl span { font-size:10px; letter-spacing:.16em; text-transform:uppercase; color:#2d4a6b; white-space:nowrap; }
.divider-lbl::before,.divider-lbl::after { content:''; flex:1; height:1px; background:#111827; }
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────
st.markdown(f"""
<div style="display:flex;justify-content:space-between;align-items:center;
  padding:18px 0 24px;border-bottom:1px solid #111827;margin-bottom:24px">
  <div>
    <div style="font-size:11px;letter-spacing:.18em;text-transform:uppercase;color:#2d4a6b;margin-bottom:3px">
      Sistema de trading algorítmico</div>
    <div style="font-size:22px;font-weight:700;color:#e2e8f0;letter-spacing:-.01em">Market Scanner</div>
  </div>
  <div style="font-family:'DM Mono',monospace;font-size:11px;color:#2d4a6b">
    {datetime.now().strftime("%d/%m/%Y %H:%M")}
  </div>
</div>
""", unsafe_allow_html=True)

# ── Buscador ──────────────────────────────────────────────
c1, c2, c3, c4 = st.columns([4, 1, 1, 1])
with c1:
    ticker_input = st.text_input("", placeholder="MELI, AAPL, GGAL, YPF, NVDA...",
        label_visibility="collapsed")
with c2:
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    buscar = st.button("Analizar →", use_container_width=True, type="primary")
with c3:
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    periodo = st.selectbox("", ["6mo","1y","2y"], index=1, label_visibility="collapsed")
with c4:
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    timeframe = st.selectbox("", ["1d","1wk","1mo"], index=0, label_visibility="collapsed",
        format_func=lambda x: {"1d":"Diario","1wk":"Semanal","1mo":"Mensual"}[x])

tf_label = {"1d":"Diario","1wk":"Semanal","1mo":"Mensual"}[timeframe]
params   = {
    "rsi_entrada": TECNICO["rsi_entrada"], "rsi_salida": TECNICO["rsi_salida"],
    "stop_loss": RIESGO["stop_loss"], "take_profit": RIESGO["take_profit"],
    "pe_max":30, "roe_min":0.10, "de_max":2.0, "periodo": periodo,
}

# ═══════════════════════════════════════════════════════════
# MOTOR DE SCORING — produce UN solo veredicto
# ═══════════════════════════════════════════════════════════
def calcular_veredicto(df, rsi_v, ema9, ema21, ema50, macd_v, macd_s, bb_lo, bb_up, precio, patrones):
    """
    Pondera todas las señales y retorna:
    score (-100 a +100), veredicto (5 niveles), razón, señales_detalle
    """
    señales = []

    # ── RSI ───────────────────────────────────────────────
    if rsi_v is not None:
        if rsi_v < 30:
            señales.append({"nombre":"RSI","desc":f"RSI {rsi_v} — zona de sobreventa extrema","pts":25,"dir":"BUY","peso":"alto"})
        elif rsi_v < 40:
            señales.append({"nombre":"RSI","desc":f"RSI {rsi_v} — zona de valor, posible rebote","pts":12,"dir":"BUY","peso":"medio"})
        elif rsi_v > 75:
            señales.append({"nombre":"RSI","desc":f"RSI {rsi_v} — sobrecompra extrema","pts":25,"dir":"SELL","peso":"alto"})
        elif rsi_v > 65:
            señales.append({"nombre":"RSI","desc":f"RSI {rsi_v} — sobrecompra, cuidado","pts":12,"dir":"SELL","peso":"medio"})
        else:
            señales.append({"nombre":"RSI","desc":f"RSI {rsi_v} — zona neutral","pts":0,"dir":"NEUTRAL","peso":"bajo"})

    # ── EMA cruce ─────────────────────────────────────────
    if ema9 and ema21:
        if ema9 > ema21:
            señales.append({"nombre":"EMA 9/21","desc":f"EMA9 (${ema9}) por encima de EMA21 (${ema21}) — tendencia alcista","pts":15,"dir":"BUY","peso":"alto"})
        else:
            señales.append({"nombre":"EMA 9/21","desc":f"EMA9 (${ema9}) por debajo de EMA21 (${ema21}) — tendencia bajista","pts":15,"dir":"SELL","peso":"alto"})

    # ── EMA50 ─────────────────────────────────────────────
    if ema50:
        if precio > ema50:
            señales.append({"nombre":"EMA 50","desc":f"Precio (${precio}) por encima de EMA50 (${ema50}) — mercado alcista","pts":10,"dir":"BUY","peso":"medio"})
        else:
            señales.append({"nombre":"EMA 50","desc":f"Precio (${precio}) por debajo de EMA50 (${ema50}) — mercado bajista","pts":10,"dir":"SELL","peso":"medio"})

    # ── MACD ─────────────────────────────────────────────
    if macd_v is not None and macd_s is not None:
        if macd_v > macd_s and macd_v > 0:
            señales.append({"nombre":"MACD","desc":f"MACD ({macd_v}) por encima de señal y positivo — momentum fuerte","pts":20,"dir":"BUY","peso":"alto"})
        elif macd_v > macd_s:
            señales.append({"nombre":"MACD","desc":f"MACD ({macd_v}) cruzando señal ({macd_s}) — momentum mejorando","pts":10,"dir":"BUY","peso":"medio"})
        elif macd_v < macd_s and macd_v < 0:
            señales.append({"nombre":"MACD","desc":f"MACD ({macd_v}) por debajo de señal y negativo — momentum bajista fuerte","pts":20,"dir":"SELL","peso":"alto"})
        else:
            señales.append({"nombre":"MACD","desc":f"MACD ({macd_v}) por debajo de señal — momentum débil","pts":10,"dir":"SELL","peso":"medio"})

    # ── Bollinger ─────────────────────────────────────────
    if bb_up > bb_lo:
        bb_pos = (precio - bb_lo) / (bb_up - bb_lo) * 100
        if bb_pos < 10:
            señales.append({"nombre":"Bollinger","desc":f"Precio tocando banda inferior (${bb_lo}) — posible rebote","pts":20,"dir":"BUY","peso":"alto"})
        elif bb_pos < 25:
            señales.append({"nombre":"Bollinger","desc":f"Precio en zona baja de Bollinger — zona de valor","pts":10,"dir":"BUY","peso":"medio"})
        elif bb_pos > 90:
            señales.append({"nombre":"Bollinger","desc":f"Precio tocando banda superior (${bb_up}) — posible corrección","pts":20,"dir":"SELL","peso":"alto"})
        elif bb_pos > 75:
            señales.append({"nombre":"Bollinger","desc":f"Precio en zona alta de Bollinger — precaución","pts":10,"dir":"SELL","peso":"medio"})
        else:
            señales.append({"nombre":"Bollinger","desc":f"Precio en zona media de Bollinger — sin señal clara","pts":0,"dir":"NEUTRAL","peso":"bajo"})

    # ── Patrones (máximo 15 pts, no saturar) ─────────────
    pts_pat_buy  = sum(5 for p in patrones if p.get("señal")=="COMPRA" and p.get("confianza") in ["Alta","Media"])
    pts_pat_sell = sum(5 for p in patrones if p.get("señal")=="VENTA"  and p.get("confianza") in ["Alta","Media"])
    pts_pat_buy  = min(pts_pat_buy,  15)
    pts_pat_sell = min(pts_pat_sell, 15)

    n_buy_pat  = sum(1 for p in patrones if p.get("señal")=="COMPRA")
    n_sell_pat = sum(1 for p in patrones if p.get("señal")=="VENTA")

    if pts_pat_buy > pts_pat_sell and n_buy_pat > 0:
        señales.append({"nombre":"Patrones técnicos","desc":f"{n_buy_pat} patrón(es) alcistas detectados ({', '.join(set(p['patron'] for p in patrones if p.get('señal')=='COMPRA')[:2])})","pts":pts_pat_buy,"dir":"BUY","peso":"medio"})
    elif pts_pat_sell > pts_pat_buy and n_sell_pat > 0:
        señales.append({"nombre":"Patrones técnicos","desc":f"{n_sell_pat} patrón(es) bajistas detectados ({', '.join(set(p['patron'] for p in patrones if p.get('señal')=='VENTA')[:2])})","pts":pts_pat_sell,"dir":"SELL","peso":"medio"})
    else:
        señales.append({"nombre":"Patrones técnicos","desc":"Sin patrones dominantes claros en este período","pts":0,"dir":"NEUTRAL","peso":"bajo"})

    # ── Score final ───────────────────────────────────────
    score_buy  = sum(s["pts"] for s in señales if s["dir"]=="BUY")
    score_sell = sum(s["pts"] for s in señales if s["dir"]=="SELL")
    score_max  = sum(s["pts"] for s in señales if s["dir"] in ["BUY","SELL"]) or 1
    score      = round((score_buy - score_sell) / score_max * 100)

    # ── Veredicto ─────────────────────────────────────────
    if score >= 55:
        veredicto, cls, emoji = "COMPRA FUERTE", "cf", "▲▲"
        razon = (f"El activo presenta <b>múltiples señales alcistas alineadas</b> en temporalidad {tf_label}. "
                 f"RSI, MACD, tendencia de medias y posición en Bollinger apuntan en la misma dirección. "
                 f"Alta probabilidad de movimiento alcista.")
    elif score >= 20:
        veredicto, cls, emoji = "COMPRA", "c", "▲"
        razon = (f"La mayoría de los indicadores favorecen el lado comprador en temporalidad {tf_label}. "
                 f"Hay señales positivas pero no todas están alineadas. "
                 f"Podés entrar con gestión de riesgo estricta.")
    elif score <= -55:
        veredicto, cls, emoji = "VENTA FUERTE", "vf", "▼▼"
        razon = (f"El activo presenta <b>múltiples señales bajistas alineadas</b> en temporalidad {tf_label}. "
                 f"Momentum, tendencia e indicadores de volatilidad apuntan a la baja. "
                 f"No es momento de entrar en compra.")
    elif score <= -20:
        veredicto, cls, emoji = "VENTA", "v", "▼"
        razon = (f"La mayoría de los indicadores favorecen el lado vendedor en temporalidad {tf_label}. "
                 f"Hay presión bajista pero no extrema. "
                 f"Evitá entrar en compra hasta que mejore el contexto técnico.")
    else:
        veredicto, cls, emoji = "NEUTRAL", "n", "◌"
        razon = (f"Las señales están divididas en temporalidad {tf_label}. "
                 f"No hay una dirección clara dominante. "
                 f"Lo mejor es esperar a que el precio rompa un nivel clave antes de tomar decisión.")

    return score, veredicto, cls, emoji, razon, señales


# ══════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════
if buscar and ticker_input.strip():
    ticker = ticker_input.strip().upper()

    with st.spinner(f"Analizando {ticker}..."):
        try:
            df = yf.download(ticker, period=periodo, interval=timeframe, progress=False, auto_adjust=True)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            if df.empty or len(df) < 20:
                st.error(f"No se encontraron datos para '{ticker}'.")
                st.stop()

            close  = df["Close"]
            n      = len(close)
            precio = round(float(close.iloc[-1]), 2)

            # Indicadores
            ema9_s  = ta_lib.trend.ema_indicator(close, window=9)
            ema21_s = ta_lib.trend.ema_indicator(close, window=21)
            ema50_s = ta_lib.trend.ema_indicator(close, window=min(50,n-1))
            rsi_s   = ta_lib.momentum.rsi(close, window=min(14,n-2))
            macd_i  = ta_lib.trend.MACD(close)
            macd_vs = macd_i.macd()
            macd_ss = macd_i.macd_signal()
            bb      = ta_lib.volatility.BollingerBands(close, window=min(20,n-2))

            def safe(s): 
                v = float(s.iloc[-1])
                return None if np.isnan(v) else round(v, 2)

            rsi_v  = safe(rsi_s)
            ema9   = safe(ema9_s)
            ema21  = safe(ema21_s)
            ema50  = safe(ema50_s)
            macd_v = safe(macd_vs)
            macd_sg= safe(macd_ss)
            bb_up  = safe(bb.bollinger_hband())
            bb_lo  = safe(bb.bollinger_lband())

            retorno = round((precio - float(close.iloc[0])) / float(close.iloc[0]) * 100, 2)

            # Última vela
            fecha_str = df.index[-1].strftime("%d/%m/%Y") if hasattr(df.index[-1],"strftime") else str(df.index[-1])[:10]
            high_v = round(float(df["High"].iloc[-1]),2) if "High" in df.columns else precio
            low_v  = round(float(df["Low"].iloc[-1]),2)  if "Low"  in df.columns else precio

            # Patrones
            res_pat  = analizar_patrones(df)
            patrones = res_pat.get("patrones", [])
            sr       = res_pat.get("soportes_resistencias", {})

            # Fundamental
            info = {}
            try:
                raw = yf.Ticker(ticker).info
                info = {
                    "nombre":  raw.get("longName") or raw.get("shortName") or ticker,
                    "sector":  raw.get("sector","—"),
                    "pais":    raw.get("country","—"),
                    "cap":     raw.get("marketCap"),
                    "pe":      raw.get("trailingPE") or raw.get("forwardPE"),
                    "pb":      raw.get("priceToBook"),
                    "roe":     raw.get("returnOnEquity"),
                    "roa":     raw.get("returnOnAssets"),
                    "margen":  raw.get("profitMargins"),
                    "de":      raw.get("debtToEquity"),
                    "rev":     raw.get("totalRevenue"),
                    "ebitda":  raw.get("ebitda"),
                    "beta":    raw.get("beta"),
                    "div":     raw.get("dividendYield"),
                    "target":  raw.get("targetMeanPrice"),
                    "rec":     raw.get("recommendationKey","—"),
                    "52h":     raw.get("fiftyTwoWeekHigh"),
                    "52l":     raw.get("fiftyTwoWeekLow"),
                    "eps":     raw.get("trailingEps"),
                    "ev_eb":   raw.get("enterpriseToEbitda"),
                    "resumen": raw.get("longBusinessSummary",""),
                }
            except:
                info = {"nombre": ticker}

            # Backtest
            bt = backtest(ticker, params) if timeframe == "1d" else None

            # VEREDICTO
            score, veredicto, cls, emoji, razon, señales_det = calcular_veredicto(
                df, rsi_v, ema9, ema21, ema50, macd_v, macd_sg,
                bb_lo, bb_up, precio, patrones
            )

            # Niveles según dirección del veredicto
            es_compra = cls in ["cf", "c"]
            es_venta  = cls in ["vf", "v"]
            if es_compra:
                sl_val      = round(precio * (1 - RIESGO["stop_loss"]),   2)
                tp_val      = round(precio * (1 + RIESGO["take_profit"]), 2)
                sl_label    = "Stop Loss"
                tp_label    = "Take Profit"
            elif es_venta:
                sl_val      = round(precio * (1 + RIESGO["stop_loss"]),   2)
                tp_val      = round(precio * (1 - RIESGO["take_profit"]), 2)
                sl_label    = "Stop (corto)"
                tp_label    = "Objetivo bajista"
            else:
                sl_val      = None
                tp_val      = None
                sl_label    = "Stop Loss"
                tp_label    = "Take Profit"

        except Exception as e:
            st.error(f"Error: {str(e)}")
            st.stop()

    # ══════════════════════════════════════════════════════
    # RENDER — VEREDICTO PRINCIPAL
    # ══════════════════════════════════════════════════════
    nombre_c = info.get("nombre", ticker)

    # Barra de score
    score_pct  = min(max(score + 100, 0), 200) / 2  # 0-100%
    bar_color  = "#48bb78" if score>=55 else ("#68d391" if score>=20 else ("#fc8181" if score<=-20 else ("#f56565" if score<=-55 else "#a0aec0")))

    st.markdown(f"""
    <div class="verdict-wrap {cls}">
      <div class="verdict-tag {cls}">{emoji} {veredicto} · Score {score:+d}/100 · {tf_label}</div>
      <div class="verdict-main {cls}">{veredicto}</div>
      <div class="verdict-ticker">{ticker} · {nombre_c[:50]} · {fecha_str}</div>
      <div class="verdict-razon">{razon}</div>

      <div class="score-bar-wrap">
        <div class="score-bar-track">
          <div class="score-bar-fill" style="width:{score_pct}%;background:{bar_color}"></div>
        </div>
        <div class="score-labels">
          <span>Venta fuerte</span><span>Venta</span><span>Neutral</span><span>Compra</span><span>Compra fuerte</span>
        </div>
      </div>

      <div class="verdict-levels">
        <div class="vl-item"><div class="vl-label">Precio actual</div><div class="vl-val neu">${precio}</div></div>
        {f'<div class="vl-item"><div class="vl-label">{sl_label}</div><div class="vl-val {"tp" if es_venta else "sl"}">${sl_val}</div></div>' if sl_val else ''}
        {f'<div class="vl-item"><div class="vl-label">{tp_label}</div><div class="vl-val {"sl" if es_venta else "tp"}">${tp_val}</div></div>' if tp_val else ''}
        {f'<div class="vl-item"><div class="vl-label">Ratio R/R</div><div class="vl-val neu">1:{round(RIESGO["take_profit"]/RIESGO["stop_loss"],1)}</div></div>' if sl_val else ''}
        <div class="vl-item"><div class="vl-label">Retorno {periodo}</div><div class="vl-val {'tp' if retorno>0 else 'sl'}">{retorno:+.1f}%</div></div>
        <div class="vl-item"><div class="vl-label">High / Low hoy</div><div class="vl-val neu">${high_v} / ${low_v}</div></div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Alerta Telegram
    if cls in ["cf","c"]:
        try:
            send_telegram(f"{'🟢🟢' if cls=='cf' else '🟢'} *{veredicto}* — {ticker} ${precio}\nScore: {score:+d}/100 | SL ${sl_val} | TP ${tp_val}")
        except: pass

    # ══════════════════════════════════════════════════════
    # DETALLE EXPANDIBLE
    # ══════════════════════════════════════════════════════
    with st.expander("Ver análisis detallado", expanded=False):

        # Señales individuales
        st.markdown('<div class="divider-lbl"><span>señales que componen el veredicto</span></div>', unsafe_allow_html=True)
        html_s = '<div class="signals-list">'
        for s in señales_det:
            dot = "g" if s["dir"]=="BUY" else ("r" if s["dir"]=="SELL" else "a")
            badge_cls = "srb-g" if s["dir"]=="BUY" else ("srb-r" if s["dir"]=="SELL" else "srb-a")
            badge_txt = f"+{s['pts']}pts" if s["dir"]=="BUY" else (f"-{s['pts']}pts" if s["dir"]=="SELL" else "neutro")
            html_s += f"""
            <div class="signal-row">
              <div class="sr-left">
                <div class="sr-dot {dot}"></div>
                <div>
                  <div class="sr-name">{s['nombre']}</div>
                  <div class="sr-desc">{s['desc']}</div>
                </div>
              </div>
              <span class="sr-badge {badge_cls}">{badge_txt}</span>
            </div>"""
        html_s += '</div>'
        st.markdown(html_s, unsafe_allow_html=True)

        # Indicadores numéricos
        st.markdown('<div class="divider-lbl"><span>indicadores técnicos</span></div>', unsafe_allow_html=True)
        rsi_cls  = "g" if (rsi_v and rsi_v<40) else ("r" if (rsi_v and rsi_v>65) else "a")
        macd_cls = "g" if (macd_v and macd_sg and macd_v>macd_sg) else "r"
        ema_cls  = "g" if (ema9 and ema21 and ema9>ema21) else "r"
        bb_pos   = round((precio-bb_lo)/(bb_up-bb_lo)*100) if bb_up and bb_lo and (bb_up-bb_lo)>0 else 50

        st.markdown(f"""
        <div class="det-grid">
          <div class="det-card"><div class="det-label">RSI (14)</div>
            <div class="det-val {rsi_cls}">{rsi_v or '—'}</div>
            <div class="det-sub">{'Sobreventa' if rsi_v and rsi_v<40 else ('Sobrecompra' if rsi_v and rsi_v>65 else 'Neutral')}</div></div>
          <div class="det-card"><div class="det-label">MACD</div>
            <div class="det-val {macd_cls}">{macd_v or '—'}</div>
            <div class="det-sub">Señal: {macd_sg or '—'}</div></div>
          <div class="det-card"><div class="det-label">EMA 9 / 21</div>
            <div class="det-val {ema_cls}">${ema9 or '—'}</div>
            <div class="det-sub">EMA21: ${ema21 or '—'}</div></div>
          <div class="det-card"><div class="det-label">Bollinger %B</div>
            <div class="det-val {'g' if bb_pos<25 else ('r' if bb_pos>75 else 'a')}">{bb_pos}%</div>
            <div class="det-sub">Inf ${bb_lo} · Sup ${bb_up}</div></div>
        </div>
        """, unsafe_allow_html=True)

        # Soportes y resistencias
        if sr and (sr.get("resistencias") or sr.get("soportes")):
            st.markdown('<div class="divider-lbl"><span>soportes y resistencias clave</span></div>', unsafe_allow_html=True)
            col_r, col_s = st.columns(2)
            with col_r:
                st.markdown('<div style="font-size:10px;letter-spacing:.12em;text-transform:uppercase;color:#2d4a6b;margin-bottom:8px">Resistencias</div>', unsafe_allow_html=True)
                for nivel, toques in sr.get("resistencias",[])[:5]:
                    dist    = round((nivel-precio)/precio*100,1)
                    cercano = abs(dist) < 3
                    st.markdown(f'<div style="display:flex;justify-content:space-between;padding:7px 0;border-bottom:1px solid #0d1117;font-size:13px"><span style="color:{"#fc8181" if cercano else "#8aa4c8"};font-family:monospace">${nivel}{"  ← cercano" if cercano else ""}</span><span style="color:#4a5568">{toques} toques · +{dist}%</span></div>', unsafe_allow_html=True)
            with col_s:
                st.markdown('<div style="font-size:10px;letter-spacing:.12em;text-transform:uppercase;color:#2d4a6b;margin-bottom:8px">Soportes</div>', unsafe_allow_html=True)
                for nivel, toques in sr.get("soportes",[])[:5]:
                    dist    = round((precio-nivel)/precio*100,1)
                    cercano = abs(dist) < 3
                    st.markdown(f'<div style="display:flex;justify-content:space-between;padding:7px 0;border-bottom:1px solid #0d1117;font-size:13px"><span style="color:{"#68d391" if cercano else "#8aa4c8"};font-family:monospace">${nivel}{"  ← cercano" if cercano else ""}</span><span style="color:#4a5568">{toques} toques · -{dist}%</span></div>', unsafe_allow_html=True)

        # Backtest
        if bt:
            st.markdown('<div class="divider-lbl"><span>backtest histórico</span></div>', unsafe_allow_html=True)
            ret_c = "g" if bt['retorno']>0 else "r"
            st.markdown(f"""
            <div style="display:grid;grid-template-columns:repeat(5,1fr);gap:10px;margin-bottom:12px">
              <div class="det-card"><div class="det-label">Retorno</div><div class="det-val {ret_c}">{bt['retorno']:+.1f}%</div></div>
              <div class="det-card"><div class="det-label">vs SPY</div><div class="det-val {'g' if bt['alpha_total']>0 else 'r'}">{bt['alpha_total']:+.1f}%</div></div>
              <div class="det-card"><div class="det-label">Win rate</div><div class="det-val {'g' if bt['win_rate']>50 else 'a'}">{bt['win_rate']:.0f}%</div></div>
              <div class="det-card"><div class="det-label">Sharpe</div><div class="det-val {'g' if bt['sharpe']>1 else 'a'}">{bt['sharpe']:.2f}</div></div>
              <div class="det-card"><div class="det-label">Max DD</div><div class="det-val r">{bt['max_dd']:.1f}%</div></div>
            </div>
            """, unsafe_allow_html=True)
            eq = bt.get("equity_curve",[])
            if eq:
                st.line_chart(pd.DataFrame({"Equity ($)":eq}), height=140, use_container_width=True)

    # ══════════════════════════════════════════════════════
    # FUNDAMENTAL — siempre visible, al fondo
    # ══════════════════════════════════════════════════════
    st.markdown('<div class="divider-lbl"><span>análisis fundamental</span></div>', unsafe_allow_html=True)

    def fmt(v, pre="", suf="", dec=1):
        if v is None: return "—"
        try:
            v2 = float(v)
            if abs(v2)>=1e12: return f"{pre}{v2/1e12:.{dec}f}T{suf}"
            if abs(v2)>=1e9:  return f"{pre}{v2/1e9:.{dec}f}B{suf}"
            if abs(v2)>=1e6:  return f"{pre}{v2/1e6:.{dec}f}M{suf}"
            return f"{pre}{v2:.{dec}f}{suf}"
        except: return "—"

    def pct(v):
        try: return f"{float(v)*100:.1f}%" if v else "—"
        except: return "—"

    rec_map = {"buy":"Compra","strong_buy":"Compra fuerte","hold":"Mantener",
               "sell":"Venta","strong_sell":"Venta fuerte"}
    rec_str = rec_map.get(str(info.get("rec","")).lower(),
              str(info.get("rec","—")).replace("_"," ").capitalize())

    target_txt = f"${round(float(info['target']),2)}" if info.get("target") else "—"
    target_cls = "g" if info.get("target") and float(info["target"])>precio else "r"

    st.markdown(f"""
    <div class="fund-wrap">
      <div class="fund-hdr">
        {info.get('nombre',ticker)} &nbsp;·&nbsp; {info.get('sector','—')} &nbsp;·&nbsp; {info.get('pais','—')}
      </div>
      <div class="fund-g4">
        <div><div class="fi-label">Market Cap</div><div class="fi-val">{fmt(info.get('cap'),pre='$')}</div></div>
        <div><div class="fi-label">Revenue</div><div class="fi-val">{fmt(info.get('rev'),pre='$')}</div></div>
        <div><div class="fi-label">EBITDA</div><div class="fi-val">{fmt(info.get('ebitda'),pre='$')}</div></div>
        <div><div class="fi-label">EPS</div><div class="fi-val">{fmt(info.get('eps'),pre='$',dec=2)}</div></div>
        <div><div class="fi-label">P/E Ratio</div>
          <div class="fi-val {'g' if info.get('pe') and float(info['pe'])<20 else ('r' if info.get('pe') and float(info['pe'])>30 else '')}">{fmt(info.get('pe'),suf='x') if info.get('pe') else '—'}</div></div>
        <div><div class="fi-label">P/B Ratio</div><div class="fi-val">{fmt(info.get('pb'),suf='x',dec=2) if info.get('pb') else '—'}</div></div>
        <div><div class="fi-label">EV/EBITDA</div><div class="fi-val">{fmt(info.get('ev_eb'),suf='x') if info.get('ev_eb') else '—'}</div></div>
        <div><div class="fi-label">ROE</div>
          <div class="fi-val {'g' if info.get('roe') and float(info['roe'])>0.15 else ''}">{pct(info.get('roe'))}</div></div>
        <div><div class="fi-label">ROA</div><div class="fi-val">{pct(info.get('roa'))}</div></div>
        <div><div class="fi-label">Margen neto</div>
          <div class="fi-val {'g' if info.get('margen') and float(info['margen'])>0.15 else ''}">{pct(info.get('margen'))}</div></div>
        <div><div class="fi-label">Deuda/Equity</div><div class="fi-val">{fmt(info.get('de'),dec=0)+'x' if info.get('de') else '—'}</div></div>
        <div><div class="fi-label">Beta</div><div class="fi-val">{fmt(info.get('beta'),dec=2) if info.get('beta') else '—'}</div></div>
        <div><div class="fi-label">Dividendo</div><div class="fi-val">{pct(info.get('div'))}</div></div>
        <div><div class="fi-label">Target analistas</div><div class="fi-val {target_cls}">{target_txt}</div></div>
        <div><div class="fi-label">Recomendación</div>
          <div class="fi-val {'g' if 'compra' in rec_str.lower() else ('r' if 'venta' in rec_str.lower() else '')}">{rec_str}</div></div>
        <div><div class="fi-label">Rango 52 sem.</div><div class="fi-val" style="font-size:12px">${info.get('52l','—')} – ${info.get('52h','—')}</div></div>
      </div>
      {'<div class="fund-desc">' + str(info.get("resumen",""))[:550] + ('...' if len(str(info.get("resumen","")))>550 else '') + '</div>' if info.get("resumen") else '<div class="fund-desc">Sin descripción disponible.</div>'}
    </div>
    """, unsafe_allow_html=True)

else:
    st.markdown("""
    <div style="text-align:center;padding:100px 0;color:#2d4a6b">
      <div style="font-size:11px;letter-spacing:.2em;text-transform:uppercase;margin-bottom:12px">
        Ingresá un ticker para comenzar
      </div>
      <div style="font-size:12px;color:#1e3050">
        MELI · AAPL · GGAL · YPF · NVDA · BMA · MSFT · TSLA
      </div>
    </div>
    """, unsafe_allow_html=True)
