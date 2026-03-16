# ============================================================
#  app.py — Dashboard v3
#  + Timeframe selector
#  + Patrones: semáforo + detalle con fecha/vela/entrada
#  + Fundamental corregido
# ============================================================

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime
import time

import ta as ta_lib
from patterns import analizar_patrones
from alerts   import send_telegram
from config   import TECNICO, RIESGO
from engine   import backtest

st.set_page_config(
    page_title="Trading System",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;500;700&family=DM+Mono:wght@300;400;500&display=swap');
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html, body, [class*="css"] { font-family: 'Syne', sans-serif; background: #080b10 !important; color: #dde3ee; }
.stApp { background: #080b10 !important; }
.stApp > header { background: transparent !important; }
div[data-testid="stSidebar"] { display: none; }

/* Signal hero */
.signal-hero { border-radius: 16px; padding: 28px 32px; margin-bottom: 16px; }
.signal-hero.compra  { background: #0d1f14; border: 1px solid #1a4731; }
.signal-hero.venta   { background: #1f0d0d; border: 1px solid #4a1515; }
.signal-hero.esperar { background: #0d1117; border: 1px solid #1e2a3a; }
.signal-tag { display:inline-flex;align-items:center;gap:6px;font-family:'DM Mono',monospace;
  font-size:11px;letter-spacing:.14em;text-transform:uppercase;padding:4px 12px;border-radius:4px;margin-bottom:14px; }
.signal-tag.compra  { background:rgba(72,187,120,.12);color:#68d391;border:1px solid rgba(72,187,120,.25); }
.signal-tag.venta   { background:rgba(245,101,101,.12);color:#fc8181;border:1px solid rgba(245,101,101,.25); }
.signal-tag.esperar { background:rgba(160,174,192,.1);color:#a0aec0;border:1px solid rgba(160,174,192,.2); }
.signal-price { font-family:'DM Mono',monospace;font-size:48px;font-weight:300;line-height:1;margin-bottom:6px; }
.signal-price.compra  { color:#68d391; }
.signal-price.venta   { color:#fc8181; }
.signal-price.esperar { color:#e2e8f0; }
.signal-ticker { font-size:13px;color:#718096;letter-spacing:.06em;margin-bottom:20px; }
.levels-row { display:flex;gap:24px;flex-wrap:wrap; }
.level-label { font-size:10px;letter-spacing:.12em;text-transform:uppercase;color:#4a5568;margin-bottom:3px; }
.level-val { font-family:'DM Mono',monospace;font-size:16px; }
.level-val.sl { color:#fc8181; } .level-val.tp { color:#68d391; } .level-val.neu { color:#a0aec0; }

/* Indicadores */
.ind-grid { display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:16px; }
.ind-card { background:#0d1117;border:1px solid #1e2a3a;border-radius:10px;padding:14px 16px; }
.ind-label { font-size:10px;letter-spacing:.12em;text-transform:uppercase;color:#4a5568;margin-bottom:6px; }
.ind-val { font-family:'DM Mono',monospace;font-size:20px;color:#e2e8f0; }
.ind-val.green{color:#68d391;} .ind-val.red{color:#fc8181;} .ind-val.amber{color:#f6ad55;}
.ind-sub { font-size:10px;color:#4a5568;margin-top:3px; }

/* Semáforo */
.semaforo-wrap { display:flex;gap:10px;margin-bottom:20px; }
.sem-item { flex:1;border-radius:10px;padding:16px;text-align:center; }
.sem-item.activo-buy  { background:#0d1f14;border:2px solid #1a4731; }
.sem-item.activo-sell { background:#1f0d0d;border:2px solid #4a1515; }
.sem-item.activo-wait { background:#131a24;border:2px solid #1e3a5f; }
.sem-item.inactivo    { background:#0a0d13;border:1px solid #111827;opacity:.4; }
.sem-icon { font-size:26px;margin-bottom:6px; }
.sem-label { font-size:10px;letter-spacing:.12em;text-transform:uppercase;color:#4a5568;margin-bottom:4px; }
.sem-val { font-family:'DM Mono',monospace;font-size:14px;font-weight:500; }
.sem-val.g{color:#68d391;} .sem-val.r{color:#fc8181;} .sem-val.a{color:#f6ad55;} .sem-val.n{color:#a0aec0;}

/* Patron card */
.patron-card { background:#0d1117;border:1px solid #1e2a3a;border-radius:12px;padding:18px 20px;margin-bottom:10px; }
.patron-card.alcista { border-left:3px solid #68d391; }
.patron-card.bajista { border-left:3px solid #fc8181; }
.patron-card.neutral { border-left:3px solid #718096; }
.patron-header { display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:10px; }
.patron-name { font-size:14px;font-weight:600;color:#e2e8f0;margin-bottom:2px; }
.patron-timeframe { font-size:10px;color:#4a5568;font-family:'DM Mono',monospace; }
.patron-badge { font-size:10px;padding:3px 10px;border-radius:3px;font-weight:500; }
.pb-buy  { background:rgba(104,211,145,.12);color:#68d391;border:1px solid rgba(104,211,145,.25); }
.pb-sell { background:rgba(252,129,129,.12);color:#fc8181;border:1px solid rgba(252,129,129,.25); }
.pb-wait { background:rgba(160,174,192,.1);color:#a0aec0;border:1px solid rgba(160,174,192,.2); }
.patron-data { display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-bottom:10px; }
.pd-item { background:#080b10;border-radius:6px;padding:8px 10px; }
.pd-label { font-size:9px;letter-spacing:.1em;text-transform:uppercase;color:#2d4a6b;margin-bottom:3px; }
.pd-val { font-family:'DM Mono',monospace;font-size:13px;color:#a0aec0; }
.pd-val.g{color:#68d391;} .pd-val.r{color:#fc8181;} .pd-val.w{color:#e2e8f0;}
.patron-accion { background:#080b10;border-radius:6px;padding:10px 12px;font-size:12px;color:#718096;line-height:1.6; }
.patron-accion b { color:#e2e8f0; }

/* Fundamental */
.fund-section { background:#0a0d13;border:1px solid #1a2030;border-radius:14px;padding:24px 28px;margin-top:8px; }
.fund-title { font-size:11px;letter-spacing:.18em;text-transform:uppercase;color:#2d4a6b;
  margin-bottom:20px;padding-bottom:12px;border-bottom:1px solid #111827; }
.fund-grid { display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:16px; }
.fund-item-label { font-size:10px;letter-spacing:.1em;text-transform:uppercase;color:#2d4a6b;margin-bottom:4px; }
.fund-item-val { font-family:'DM Mono',monospace;font-size:15px;color:#8aa4c8; }
.fund-item-val.good { color:#68d391; } .fund-item-val.bad { color:#fc8181; } .fund-item-val.mid { color:#f6ad55; }
.fund-note { font-size:11px;color:#4a5568;line-height:1.8;border-top:1px solid #111827;padding-top:14px;margin-top:4px; }

/* Divider */
.divider-label { display:flex;align-items:center;gap:12px;margin:28px 0 20px; }
.divider-label span { font-size:10px;letter-spacing:.16em;text-transform:uppercase;color:#2d4a6b;white-space:nowrap; }
.divider-label::before, .divider-label::after { content:'';flex:1;height:1px;background:#111827; }

/* BT */
.bt-strip { display:grid;grid-template-columns:repeat(5,1fr);gap:10px;margin-bottom:12px; }
.bt-cell { background:#0d1117;border:1px solid #1e2a3a;border-radius:8px;padding:12px;text-align:center; }
.bt-cell-label { font-size:10px;color:#4a5568;letter-spacing:.1em;text-transform:uppercase;margin-bottom:5px; }
.bt-cell-val { font-family:'DM Mono',monospace;font-size:17px;color:#e2e8f0; }
.bt-cell-val.g{color:#68d391;} .bt-cell-val.r{color:#fc8181;} .bt-cell-val.a{color:#f6ad55;}
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────
st.markdown(f"""
<div style="display:flex;justify-content:space-between;align-items:center;
  padding:20px 0 28px;border-bottom:1px solid #111827;margin-bottom:28px">
  <div>
    <div style="font-size:11px;letter-spacing:.18em;text-transform:uppercase;color:#2d4a6b;margin-bottom:4px">
      Sistema de trading algorítmico</div>
    <div style="font-size:22px;font-weight:700;color:#e2e8f0;letter-spacing:-.01em">Market Scanner</div>
  </div>
  <div style="font-family:'DM Mono',monospace;font-size:11px;color:#2d4a6b">
    {datetime.now().strftime("%d/%m/%Y %H:%M")}
  </div>
</div>
""", unsafe_allow_html=True)

# ── Buscador + controles ──────────────────────────────────
c1, c2, c3, c4 = st.columns([4, 1, 1, 1])
with c1:
    ticker_input = st.text_input("", placeholder="Buscá un activo: MELI, AAPL, GGAL, YPF...",
        label_visibility="collapsed")
with c2:
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    buscar = st.button("Analizar →", use_container_width=True, type="primary")
with c3:
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    periodo = st.selectbox("", ["6mo","1y","2y"], index=1, label_visibility="collapsed",
        help="Período de historia para el análisis")
with c4:
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    timeframe = st.selectbox("", ["1d","1wk","1mo"], index=0, label_visibility="collapsed",
        format_func=lambda x: {"1d":"Diario","1wk":"Semanal","1mo":"Mensual"}[x],
        help="Temporalidad de las velas")

tf_label = {"1d":"Diario (1D)","1wk":"Semanal (1W)","1mo":"Mensual (1M)"}[timeframe]
tf_short = {"1d":"1D","1wk":"1W","1mo":"1M"}[timeframe]

params = {
    "pe_max":30,"roe_min":0.10,"de_max":2.0,
    "rsi_entrada": TECNICO["rsi_entrada"],
    "rsi_salida":  TECNICO["rsi_salida"],
    "stop_loss":   RIESGO["stop_loss"],
    "take_profit": RIESGO["take_profit"],
    "periodo":     periodo,
}

# ── Análisis ──────────────────────────────────────────────
if buscar and ticker_input.strip():
    ticker = ticker_input.strip().upper()

    with st.spinner(f"Analizando {ticker} en {tf_label}..."):
        try:
            df = yf.download(ticker, period=periodo, interval=timeframe, progress=False, auto_adjust=True)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            if df.empty or len(df) < 20:
                st.error(f"No se encontraron datos para '{ticker}'. Verificá el ticker.")
                st.stop()

            close = df["Close"]
            n     = len(close)

            # Indicadores
            ema9  = ta_lib.trend.ema_indicator(close, window=9)
            ema21 = ta_lib.trend.ema_indicator(close, window=21)
            ema50 = ta_lib.trend.ema_indicator(close, window=min(50, n-1))
            rsi   = ta_lib.momentum.rsi(close, window=min(14, n-2))
            macd_i= ta_lib.trend.MACD(close)
            macd_v= macd_i.macd()
            macd_s= macd_i.macd_signal()
            bb    = ta_lib.volatility.BollingerBands(close, window=min(20,n-2))

            precio    = round(float(close.iloc[-1]),  2)
            rsi_val   = round(float(rsi.iloc[-1]),    1)  if not np.isnan(float(rsi.iloc[-1]))  else None
            ema9_val  = round(float(ema9.iloc[-1]),   2)  if not np.isnan(float(ema9.iloc[-1])) else None
            ema21_val = round(float(ema21.iloc[-1]),  2)  if not np.isnan(float(ema21.iloc[-1]))else None
            ema50_val = round(float(ema50.iloc[-1]),  2)  if not np.isnan(float(ema50.iloc[-1]))else None
            macd_val  = round(float(macd_v.iloc[-1]), 3)  if not np.isnan(float(macd_v.iloc[-1]))else None
            macd_sig  = round(float(macd_s.iloc[-1]), 3)  if not np.isnan(float(macd_s.iloc[-1]))else None
            bb_up     = round(float(bb.bollinger_hband().iloc[-1]), 2)
            bb_lo     = round(float(bb.bollinger_lband().iloc[-1]), 2)

            retorno   = round((precio - float(close.iloc[0])) / float(close.iloc[0]) * 100, 2)
            sl_val    = round(precio * (1 - RIESGO["stop_loss"]),   2)
            tp_val    = round(precio * (1 + RIESGO["take_profit"]), 2)

            # Fecha y descripción de la última vela
            ultima_fecha = df.index[-1]
            fecha_str    = ultima_fecha.strftime("%d/%m/%Y") if hasattr(ultima_fecha,"strftime") else str(ultima_fecha)[:10]
            open_v  = round(float(df["Open"].iloc[-1]),  2) if "Open"  in df.columns else precio
            high_v  = round(float(df["High"].iloc[-1]),  2) if "High"  in df.columns else precio
            low_v   = round(float(df["Low"].iloc[-1]),   2) if "Low"   in df.columns else precio
            vol_v   = int(df["Volume"].iloc[-1])             if "Volume" in df.columns else 0

            # Tipo de vela
            cuerpo = precio - open_v
            rango  = high_v - low_v if high_v > low_v else 0.01
            if abs(cuerpo) / rango < 0.1:
                tipo_vela = "Doji"
            elif cuerpo > 0 and abs(cuerpo)/rango > 0.6:
                tipo_vela = "Vela alcista fuerte"
            elif cuerpo < 0 and abs(cuerpo)/rango > 0.6:
                tipo_vela = "Vela bajista fuerte"
            elif cuerpo > 0:
                tipo_vela = "Vela alcista"
            else:
                tipo_vela = "Vela bajista"

            # Score de señal
            pc, pv = 0, 0
            if rsi_val:
                if rsi_val < 35:   pc += 2
                elif rsi_val < 45: pc += 1
                elif rsi_val > 70: pv += 2
                elif rsi_val > 60: pv += 1
            if ema9_val and ema21_val:
                if ema9_val > ema21_val: pc += 1
                else:                    pv += 1
            if macd_val is not None and macd_sig is not None:
                if macd_val > macd_sig: pc += 1
                else:                   pv += 1
            if precio <= bb_lo:  pc += 2
            elif precio >= bb_up: pv += 2
            if ema50_val:
                if precio > ema50_val: pc += 1
                else:                  pv += 1

            total_pts = pc + pv
            fuerza    = round(max(pc, pv) / max(total_pts,1) * 100)
            if pc > pv + 1:   senal_txt, senal_cls = "COMPRA",  "compra"
            elif pv > pc + 1: senal_txt, senal_cls = "VENTA",   "venta"
            else:             senal_txt, senal_cls = "ESPERAR", "esperar"

            # Patrones
            res_pat  = analizar_patrones(df)
            patrones = res_pat.get("patrones", [])

            # Fundamental
            info = {}
            try:
                raw  = yf.Ticker(ticker).fast_info
                raw2 = yf.Ticker(ticker).info
                info = {
                    "nombre":    raw2.get("longName") or raw2.get("shortName") or ticker,
                    "sector":    raw2.get("sector","—"),
                    "industria": raw2.get("industry","—"),
                    "pais":      raw2.get("country","—"),
                    "cap":       raw2.get("marketCap"),
                    "pe":        raw2.get("trailingPE") or raw2.get("forwardPE"),
                    "pb":        raw2.get("priceToBook"),
                    "ps":        raw2.get("priceToSalesTrailing12Months"),
                    "roe":       raw2.get("returnOnEquity"),
                    "roa":       raw2.get("returnOnAssets"),
                    "margen":    raw2.get("profitMargins"),
                    "de":        raw2.get("debtToEquity"),
                    "rev":       raw2.get("totalRevenue"),
                    "ebitda":    raw2.get("ebitda"),
                    "div":       raw2.get("dividendYield"),
                    "beta":      raw2.get("beta"),
                    "resumen":   raw2.get("longBusinessSummary",""),
                    "52h":       raw2.get("fiftyTwoWeekHigh"),
                    "52l":       raw2.get("fiftyTwoWeekLow"),
                    "target":    raw2.get("targetMeanPrice"),
                    "rec":       raw2.get("recommendationKey","—"),
                    "empleados": raw2.get("fullTimeEmployees"),
                    "eps":       raw2.get("trailingEps"),
                    "ev_ebitda": raw2.get("enterpriseToEbitda"),
                }
            except Exception as e:
                info = {"nombre": ticker, "sector":"—","industria":"—","pais":"—"}

            # Backtest (solo en diario)
            bt = None
            if timeframe == "1d":
                bt = backtest(ticker, params)

        except Exception as e:
            st.error(f"Error: {str(e)}")
            st.stop()

    # ══════════════════════════════════════════════════
    # RENDER
    # ══════════════════════════════════════════════════

    # ── Señal hero ────────────────────────────────────
    senal_emoji = "▲" if senal_cls=="compra" else ("▼" if senal_cls=="venta" else "◌")
    st.markdown(f"""
    <div class="signal-hero {senal_cls}">
      <div class="signal-tag {senal_cls}">{senal_emoji} señal {senal_txt} · fuerza {fuerza}% · {tf_label}</div>
      <div class="signal-price {senal_cls}">${precio}</div>
      <div class="signal-ticker">{ticker} · {info.get('nombre',ticker)[:45]} · última vela: {fecha_str} · {tipo_vela}</div>
      <div class="levels-row">
        <div><div class="level-label">Stop Loss</div><div class="level-val sl">${sl_val}</div></div>
        <div><div class="level-label">Take Profit</div><div class="level-val tp">${tp_val}</div></div>
        <div><div class="level-label">Ratio R/R</div><div class="level-val neu">1:{round(RIESGO['take_profit']/RIESGO['stop_loss'],1)}</div></div>
        <div><div class="level-label">Retorno {periodo}</div><div class="level-val {'tp' if retorno>0 else 'sl'}">{retorno:+.1f}%</div></div>
        <div><div class="level-label">Open / High / Low</div><div class="level-val neu">${open_v} / ${high_v} / ${low_v}</div></div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Indicadores ───────────────────────────────────
    rsi_cls  = "green" if (rsi_val and rsi_val<40) else ("red" if (rsi_val and rsi_val>65) else "amber")
    macd_cls = "green" if (macd_val and macd_sig and macd_val>macd_sig) else "red"
    ema_cls  = "green" if (ema9_val and ema21_val and ema9_val>ema21_val) else "red"
    bb_pos   = round((precio-bb_lo)/(bb_up-bb_lo)*100) if (bb_up-bb_lo)>0 else 50

    st.markdown(f"""
    <div class="ind-grid">
      <div class="ind-card">
        <div class="ind-label">RSI (14) · {tf_short}</div>
        <div class="ind-val {rsi_cls}">{rsi_val if rsi_val else '—'}</div>
        <div class="ind-sub">{'Sobrevendido — zona de compra' if rsi_val and rsi_val<40 else ('Sobrecomprado — zona de venta' if rsi_val and rsi_val>65 else 'Neutral')}</div>
      </div>
      <div class="ind-card">
        <div class="ind-label">MACD · {tf_short}</div>
        <div class="ind-val {macd_cls}">{macd_val if macd_val else '—'}</div>
        <div class="ind-sub">Señal: {macd_sig if macd_sig else '—'} · {'Momentum alcista' if macd_val and macd_sig and macd_val>macd_sig else 'Momentum bajista'}</div>
      </div>
      <div class="ind-card">
        <div class="ind-label">EMA 9 / 21 · {tf_short}</div>
        <div class="ind-val {ema_cls}">${ema9_val if ema9_val else '—'}</div>
        <div class="ind-sub">EMA21: ${ema21_val if ema21_val else '—'} · {'Tendencia alcista' if ema9_val and ema21_val and ema9_val>ema21_val else 'Tendencia bajista'}</div>
      </div>
      <div class="ind-card">
        <div class="ind-label">Bollinger · {tf_short}</div>
        <div class="ind-val {'green' if bb_pos<25 else ('red' if bb_pos>75 else 'amber')}">{bb_pos}%</div>
        <div class="ind-sub">Inf: ${bb_lo} · Sup: ${bb_up} · {'Cerca del piso' if bb_pos<25 else ('Cerca del techo' if bb_pos>75 else 'Zona media')}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ══════════════════════════════════════════════════
    # PATRONES — semáforo + detalle
    # ══════════════════════════════════════════════════
    st.markdown('<div class="divider-label"><span>patrones técnicos detectados</span></div>', unsafe_allow_html=True)

    consenso = res_pat.get("consenso","NEUTRAL")
    n_c      = res_pat.get("n_compras",0)
    n_v      = res_pat.get("n_ventas",0)
    fuerza_p = res_pat.get("fuerza",0)
    sr       = res_pat.get("soportes_resistencias",{})
    res_c    = sr.get("res_cercana",(None,0))
    sop_c    = sr.get("sop_cercana",(None,0))

    # Decisión de acción concreta
    if consenso == "COMPRA":
        accion_txt  = "ENTRAR EN COMPRA"
        accion_desc = f"La mayoría de los patrones detectados son alcistas ({n_c} de {n_c+n_v}). Considerá entrar con Stop Loss en ${sl_val} y Take Profit en ${tp_val}."
        accion_color= "#68d391"
    elif consenso == "VENTA":
        accion_txt  = "NO ENTRAR / SALIR"
        accion_desc = f"La mayoría de los patrones detectados son bajistas ({n_v} de {n_c+n_v}). Si tenés posición abierta, considerá cerrarla cerca de ${sop_c[0] if sop_c[0] else sl_val}."
        accion_color= "#fc8181"
    else:
        accion_txt  = "ESPERAR CONFIRMACIÓN"
        accion_desc = f"Las señales están divididas ({n_c} alcistas vs {n_v} bajistas). No hay una dirección clara. Esperá que el precio rompa soporte o resistencia antes de entrar."
        accion_color= "#f6ad55"

    # Semáforo visual
    compra_activo  = "activo-buy"  if consenso=="COMPRA"  else "inactivo"
    esperar_activo = "activo-wait" if consenso=="NEUTRAL" else "inactivo"
    venta_activo   = "activo-sell" if consenso=="VENTA"   else "inactivo"

    st.markdown(f"""
    <div class="semaforo-wrap">
      <div class="sem-item {compra_activo}">
        <div class="sem-icon">▲</div>
        <div class="sem-label">Compra</div>
        <div class="sem-val g">{n_c} señales</div>
      </div>
      <div class="sem-item {esperar_activo}">
        <div class="sem-icon">◌</div>
        <div class="sem-label">Esperar</div>
        <div class="sem-val a">{res_pat['total_patrones']} analizados</div>
      </div>
      <div class="sem-item {venta_activo}">
        <div class="sem-icon">▼</div>
        <div class="sem-label">Venta</div>
        <div class="sem-val r">{n_v} señales</div>
      </div>
      <div class="sem-item" style="flex:2;background:#0d1117;border:1px solid #1e2a3a;border-radius:10px;padding:16px 20px;opacity:1">
        <div style="font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:#4a5568;margin-bottom:6px">Acción recomendada</div>
        <div style="font-size:15px;font-weight:600;color:{accion_color};margin-bottom:6px">{accion_txt}</div>
        <div style="font-size:12px;color:#718096;line-height:1.6">{accion_desc}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Detalle de patrones ───────────────────────────
    if not patrones:
        st.markdown('<div style="color:#4a5568;font-size:13px;padding:12px 0">No se detectaron patrones claros. Probá con período 2y o timeframe semanal.</div>', unsafe_allow_html=True)
    else:
        for p in patrones[:8]:
            tipo_l    = p["tipo"].lower()
            if tipo_l not in ["alcista","bajista"]: tipo_l = "neutral"
            pb_cls    = "pb-buy"  if p["señal"]=="COMPRA" else ("pb-sell" if p["señal"]=="VENTA" else "pb-wait")
            señal_txt2= "▲ COMPRA" if p["señal"]=="COMPRA" else ("▼ VENTA" if p["señal"]=="VENTA" else "◌ "+p["señal"])

            # Acción concreta por patrón
            if p["señal"] == "COMPRA":
                accion_pat = f"<b>Cuándo entrar:</b> cuando el precio supere ${p['nivel_cuello']} con volumen. <b>Objetivo:</b> ${p['objetivo']}. <b>Stop:</b> ${sl_val}."
            elif p["señal"] == "VENTA":
                accion_pat = f"<b>Cuándo salir:</b> si el precio rompe por debajo de ${p['nivel_cuello']}. <b>Objetivo bajista:</b> ${p['objetivo']}."
            else:
                accion_pat = f"<b>Qué hacer:</b> sin acción por ahora. Esperá confirmación de ruptura del rango ${p['nivel_cuello']} – ${p['objetivo']}."

            st.markdown(f"""
            <div class="patron-card {tipo_l}">
              <div class="patron-header">
                <div>
                  <div class="patron-name">{p['patron']}</div>
                  <div class="patron-timeframe">Detectado en vela {tf_short} · {p['fecha']}</div>
                </div>
                <span class="patron-badge {pb_cls}">{señal_txt2}</span>
              </div>
              <div class="patron-data">
                <div class="pd-item">
                  <div class="pd-label">Fecha detección</div>
                  <div class="pd-val w">{p['fecha']}</div>
                </div>
                <div class="pd-item">
                  <div class="pd-label">Temporalidad</div>
                  <div class="pd-val w">{tf_label}</div>
                </div>
                <div class="pd-item">
                  <div class="pd-label">Nivel clave</div>
                  <div class="pd-val w">${p['nivel_cuello']}</div>
                </div>
                <div class="pd-item">
                  <div class="pd-label">Objetivo precio</div>
                  <div class="pd-val {'g' if p['señal']=='COMPRA' else ('r' if p['señal']=='VENTA' else 'w')}">${p['objetivo']}</div>
                </div>
              </div>
              <div class="patron-accion">
                <b>Qué es:</b> {p['descripcion']}<br><br>
                {accion_pat}
              </div>
            </div>
            """, unsafe_allow_html=True)

    # ── Soportes y resistencias ───────────────────────
    if sr and (sr.get("resistencias") or sr.get("soportes")):
        st.markdown('<div class="divider-label"><span>soportes y resistencias clave</span></div>', unsafe_allow_html=True)
        col_r, col_s = st.columns(2)
        with col_r:
            st.markdown(f'<div style="font-size:10px;letter-spacing:.12em;text-transform:uppercase;color:#2d4a6b;margin-bottom:10px">Resistencias — zona de venta</div>', unsafe_allow_html=True)
            for nivel, toques in sr.get("resistencias",[])[:5]:
                dist = round((nivel-precio)/precio*100,1)
                cercano = abs(dist) < 3
                st.markdown(f'<div style="display:flex;justify-content:space-between;align-items:center;padding:8px 0;border-bottom:1px solid #0d1117;font-size:13px"><span style="color:{"#fc8181" if cercano else "#8aa4c8"};font-family:DM Mono,monospace;font-weight:{"600" if cercano else "400"}">${nivel} {"← cercano" if cercano else ""}</span><span style="color:#4a5568">{toques} toques · +{dist}%</span></div>', unsafe_allow_html=True)
        with col_s:
            st.markdown(f'<div style="font-size:10px;letter-spacing:.12em;text-transform:uppercase;color:#2d4a6b;margin-bottom:10px">Soportes — zona de compra</div>', unsafe_allow_html=True)
            for nivel, toques in sr.get("soportes",[])[:5]:
                dist = round((precio-nivel)/precio*100,1)
                cercano = abs(dist) < 3
                st.markdown(f'<div style="display:flex;justify-content:space-between;align-items:center;padding:8px 0;border-bottom:1px solid #0d1117;font-size:13px"><span style="color:{"#68d391" if cercano else "#8aa4c8"};font-family:DM Mono,monospace;font-weight:{"600" if cercano else "400"}">${nivel} {"← cercano" if cercano else ""}</span><span style="color:#4a5568">{toques} toques · -{dist}%</span></div>', unsafe_allow_html=True)

    # ── Backtest ──────────────────────────────────────
    if bt:
        st.markdown('<div class="divider-label"><span>backtest histórico</span></div>', unsafe_allow_html=True)
        ret_c = "g" if bt['retorno']>0 else "r"
        st.markdown(f"""
        <div class="bt-strip">
          <div class="bt-cell"><div class="bt-cell-label">Retorno</div><div class="bt-cell-val {ret_c}">{bt['retorno']:+.1f}%</div></div>
          <div class="bt-cell"><div class="bt-cell-label">vs SPY</div><div class="bt-cell-val {'g' if bt['alpha_total']>0 else 'r'}">{bt['alpha_total']:+.1f}%</div></div>
          <div class="bt-cell"><div class="bt-cell-label">Win rate</div><div class="bt-cell-val {'g' if bt['win_rate']>50 else 'a'}">{bt['win_rate']:.0f}%</div></div>
          <div class="bt-cell"><div class="bt-cell-label">Sharpe</div><div class="bt-cell-val {'g' if bt['sharpe']>1 else 'a'}">{bt['sharpe']:.2f}</div></div>
          <div class="bt-cell"><div class="bt-cell-label">Max DD</div><div class="bt-cell-val r">{bt['max_dd']:.1f}%</div></div>
        </div>
        """, unsafe_allow_html=True)
        eq = bt.get("equity_curve",[])
        if eq:
            st.line_chart(pd.DataFrame({"Equity ($)":eq}), height=150, use_container_width=True)

    # ══════════════════════════════════════════════════
    # FUNDAMENTAL
    # ══════════════════════════════════════════════════
    st.markdown('<div class="divider-label"><span>análisis fundamental — contexto</span></div>', unsafe_allow_html=True)

    def fmt(v, pre="", suf="", mult=1, dec=1):
        if v is None: return "—"
        v2 = float(v) * mult
        if abs(v2)>=1e12: return f"{pre}{v2/1e12:.{dec}f}T{suf}"
        if abs(v2)>=1e9:  return f"{pre}{v2/1e9:.{dec}f}B{suf}"
        if abs(v2)>=1e6:  return f"{pre}{v2/1e6:.{dec}f}M{suf}"
        if abs(v2)>=1e3:  return f"{pre}{v2/1e3:.{dec}f}K{suf}"
        return f"{pre}{v2:.{dec}f}{suf}"

    def pct(v):
        if v is None: return "—"
        return f"{float(v)*100:.1f}%"

    def cls_pe(v):
        if v is None: return ""
        return "good" if float(v)<20 else ("mid" if float(v)<30 else "bad")

    def cls_roe(v):
        if v is None: return ""
        return "good" if float(v)>0.15 else ("mid" if float(v)>0.08 else "bad")

    rec_map = {"buy":"Compra","strong_buy":"Compra fuerte","hold":"Mantener","sell":"Venta","strong_sell":"Venta fuerte"}
    rec_str  = rec_map.get(str(info.get("rec","")).lower(), str(info.get("rec","—")).capitalize())

    st.markdown(f"""
    <div class="fund-section">
      <div class="fund-title">
        {info.get('nombre',ticker)} &nbsp;·&nbsp; {info.get('sector','—')} &nbsp;·&nbsp;
        {info.get('industria','—')} &nbsp;·&nbsp; {info.get('pais','—')}
      </div>

      <div class="fund-grid">
        <div>
          <div class="fund-item-label">Market Cap</div>
          <div class="fund-item-val">{fmt(info.get('cap'), pre='$')}</div>
        </div>
        <div>
          <div class="fund-item-label">Revenue</div>
          <div class="fund-item-val">{fmt(info.get('rev'), pre='$')}</div>
        </div>
        <div>
          <div class="fund-item-label">EBITDA</div>
          <div class="fund-item-val">{fmt(info.get('ebitda'), pre='$')}</div>
        </div>
        <div>
          <div class="fund-item-label">EPS</div>
          <div class="fund-item-val">{fmt(info.get('eps'), pre='$', dec=2)}</div>
        </div>
        <div>
          <div class="fund-item-label">P/E Ratio</div>
          <div class="fund-item-val {cls_pe(info.get('pe'))}">{fmt(info.get('pe'), suf='x', dec=1) if info.get('pe') else '—'}</div>
        </div>
        <div>
          <div class="fund-item-label">P/B Ratio</div>
          <div class="fund-item-val">{fmt(info.get('pb'), suf='x', dec=2) if info.get('pb') else '—'}</div>
        </div>
        <div>
          <div class="fund-item-label">EV/EBITDA</div>
          <div class="fund-item-val">{fmt(info.get('ev_ebitda'), suf='x', dec=1) if info.get('ev_ebitda') else '—'}</div>
        </div>
        <div>
          <div class="fund-item-label">P/S Ratio</div>
          <div class="fund-item-val">{fmt(info.get('ps'), suf='x', dec=2) if info.get('ps') else '—'}</div>
        </div>
        <div>
          <div class="fund-item-label">ROE</div>
          <div class="fund-item-val {cls_roe(info.get('roe'))}">{pct(info.get('roe'))}</div>
        </div>
        <div>
          <div class="fund-item-label">ROA</div>
          <div class="fund-item-val">{pct(info.get('roa'))}</div>
        </div>
        <div>
          <div class="fund-item-label">Margen neto</div>
          <div class="fund-item-val {'good' if info.get('margen') and float(info['margen'])>0.15 else ''}">{pct(info.get('margen'))}</div>
        </div>
        <div>
          <div class="fund-item-label">Deuda/Equity</div>
          <div class="fund-item-val {'bad' if info.get('de') and float(info['de'])>150 else ''}">{fmt(info.get('de'), dec=0) + 'x' if info.get('de') else '—'}</div>
        </div>
        <div>
          <div class="fund-item-label">Beta</div>
          <div class="fund-item-val">{fmt(info.get('beta'), dec=2) if info.get('beta') else '—'}</div>
        </div>
        <div>
          <div class="fund-item-label">Dividendo</div>
          <div class="fund-item-val">{pct(info.get('div'))}</div>
        </div>
        <div>
          <div class="fund-item-label">Target analistas</div>
          <div class="fund-item-val {'good' if info.get('target') and float(info['target'])>precio else 'bad'}">{('$'+str(round(float(info['target']),2))) if info.get('target') else '—'}</div>
        </div>
        <div>
          <div class="fund-item-label">Recomendación</div>
          <div class="fund-item-val {'good' if 'compra' in rec_str.lower() else ('bad' if 'venta' in rec_str.lower() else '')}">{rec_str}</div>
        </div>
      </div>

      <div style="display:flex;gap:16px;margin-bottom:14px;font-size:12px;color:#4a5568">
        <span>Rango 52 sem: <span style="color:#8aa4c8;font-family:DM Mono,monospace">${info.get('52l','—')} – ${info.get('52h','—')}</span></span>
        {'<span>Empleados: <span style="color:#8aa4c8;font-family:DM Mono,monospace">' + f"{int(info['empleados']):,}" + '</span></span>' if info.get('empleados') else ''}
      </div>

      {'<div class="fund-note">' + str(info.get("resumen",""))[:600] + ('...' if len(str(info.get("resumen","")))>600 else '') + '</div>' if info.get("resumen") else '<div class="fund-note">Sin descripción disponible para este activo.</div>'}
    </div>
    """, unsafe_allow_html=True)

    # Alerta Telegram
    if senal_cls == "compra" and fuerza >= 70:
        try:
            send_telegram(f"🟢 *COMPRA FUERTE* {ticker} ${precio} | Fuerza {fuerza}% | SL ${sl_val} | TP ${tp_val} | RSI {rsi_val}")
        except: pass

else:
    st.markdown("""
    <div style="text-align:center;padding:80px 0;color:#2d4a6b">
      <div style="font-size:48px;margin-bottom:16px">↑</div>
      <div style="font-size:14px;letter-spacing:.1em;text-transform:uppercase">
        Ingresá un ticker para comenzar el análisis
      </div>
      <div style="font-size:12px;margin-top:8px;color:#1e3050">
        NYSE · NASDAQ · CEDEARs · Merval — Ej: MELI, AAPL, GGAL, YPF, BMA
      </div>
    </div>
    """, unsafe_allow_html=True)
