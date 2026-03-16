# ============================================================
#  app.py — Dashboard rediseñado
#  Búsqueda libre de activo → Técnico arriba, Fundamental abajo
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
from reports  import generate_pdf
from config   import CONFIG, TECNICO, RIESGO
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

html, body, [class*="css"] {
  font-family: 'Syne', sans-serif;
  background: #080b10 !important;
  color: #dde3ee;
}
.stApp { background: #080b10 !important; }
.stApp > header { background: transparent !important; }
div[data-testid="stSidebar"] { display: none; }

/* Barra de búsqueda superior */
.search-wrap {
  max-width: 680px;
  margin: 0 auto 2rem;
}
.search-label {
  font-size: 11px; letter-spacing: .18em; text-transform: uppercase;
  color: #4a5568; margin-bottom: 8px;
}

/* Señal principal */
.signal-hero {
  border-radius: 16px;
  padding: 28px 32px;
  margin-bottom: 16px;
  position: relative;
  overflow: hidden;
}
.signal-hero.compra  { background: linear-gradient(135deg,#0d1f14 0%,#0b1a12 100%); border: 1px solid #1a4731; }
.signal-hero.venta   { background: linear-gradient(135deg,#1f0d0d 0%,#1a0b0b 100%); border: 1px solid #4a1515; }
.signal-hero.esperar { background: #0d1117; border: 1px solid #1e2a3a; }

.signal-tag {
  display: inline-flex; align-items: center; gap: 6px;
  font-family: 'DM Mono', monospace;
  font-size: 11px; letter-spacing: .14em; text-transform: uppercase;
  padding: 4px 12px; border-radius: 4px; margin-bottom: 14px;
}
.signal-tag.compra  { background: rgba(72,187,120,.12); color: #68d391; border: 1px solid rgba(72,187,120,.25); }
.signal-tag.venta   { background: rgba(245,101,101,.12); color: #fc8181; border: 1px solid rgba(245,101,101,.25); }
.signal-tag.esperar { background: rgba(160,174,192,.1);  color: #a0aec0; border: 1px solid rgba(160,174,192,.2); }

.signal-price {
  font-family: 'DM Mono', monospace;
  font-size: 48px; font-weight: 300; letter-spacing: -.02em;
  line-height: 1; margin-bottom: 6px;
}
.signal-price.compra  { color: #68d391; }
.signal-price.venta   { color: #fc8181; }
.signal-price.esperar { color: #e2e8f0; }

.signal-ticker {
  font-size: 13px; color: #718096; letter-spacing: .06em;
  margin-bottom: 20px;
}

.levels-row {
  display: flex; gap: 24px; flex-wrap: wrap;
}
.level-item { }
.level-label {
  font-size: 10px; letter-spacing: .12em; text-transform: uppercase;
  color: #4a5568; margin-bottom: 3px;
}
.level-val {
  font-family: 'DM Mono', monospace;
  font-size: 16px; font-weight: 400;
}
.level-val.sl  { color: #fc8181; }
.level-val.tp  { color: #68d391; }
.level-val.neu { color: #a0aec0; }

/* Cards de indicadores */
.ind-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10px;
  margin-bottom: 16px;
}
.ind-card {
  background: #0d1117;
  border: 1px solid #1e2a3a;
  border-radius: 10px;
  padding: 14px 16px;
}
.ind-label {
  font-size: 10px; letter-spacing: .12em; text-transform: uppercase;
  color: #4a5568; margin-bottom: 6px;
}
.ind-val {
  font-family: 'DM Mono', monospace;
  font-size: 20px; font-weight: 400; color: #e2e8f0;
}
.ind-val.green  { color: #68d391; }
.ind-val.red    { color: #fc8181; }
.ind-val.amber  { color: #f6ad55; }
.ind-sub {
  font-size: 10px; color: #4a5568; margin-top: 3px;
}

/* Patrones */
.patron-row {
  display: flex; align-items: flex-start; gap: 14px;
  padding: 14px 0;
  border-bottom: 1px solid #0d1117;
}
.patron-row:last-child { border-bottom: none; }
.patron-dot {
  width: 8px; height: 8px; border-radius: 50%;
  flex-shrink: 0; margin-top: 5px;
}
.patron-dot.alcista { background: #68d391; }
.patron-dot.bajista { background: #fc8181; }
.patron-dot.neutral { background: #718096; }
.patron-name {
  font-size: 13px; font-weight: 500; color: #e2e8f0;
  margin-bottom: 3px;
}
.patron-desc {
  font-size: 12px; color: #718096; line-height: 1.6;
}
.patron-meta {
  font-family: 'DM Mono', monospace;
  font-size: 10px; color: #4a5568; margin-top: 4px;
}

/* Sección fundamental */
.fund-section {
  background: #0a0d13;
  border: 1px solid #1a2030;
  border-radius: 14px;
  padding: 24px 28px;
  margin-top: 8px;
}
.fund-title {
  font-size: 11px; letter-spacing: .18em; text-transform: uppercase;
  color: #2d4a6b; margin-bottom: 20px;
  padding-bottom: 12px;
  border-bottom: 1px solid #111827;
}
.fund-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}
.fund-item { }
.fund-item-label {
  font-size: 10px; letter-spacing: .1em; text-transform: uppercase;
  color: #2d4a6b; margin-bottom: 4px;
}
.fund-item-val {
  font-family: 'DM Mono', monospace;
  font-size: 15px; color: #8aa4c8;
}
.fund-note {
  font-size: 11px; color: #2d4a6b; line-height: 1.7;
  border-top: 1px solid #111827;
  padding-top: 14px; margin-top: 4px;
}

/* Backtest strip */
.bt-strip {
  display: grid;
  grid-template-columns: repeat(5,1fr);
  gap: 10px;
  margin-bottom: 16px;
}
.bt-cell {
  background: #0d1117;
  border: 1px solid #1e2a3a;
  border-radius: 8px;
  padding: 12px 14px;
  text-align: center;
}
.bt-cell-label { font-size: 10px; color: #4a5568; letter-spacing:.1em; text-transform:uppercase; margin-bottom:5px; }
.bt-cell-val   { font-family:'DM Mono',monospace; font-size:17px; color:#e2e8f0; }
.bt-cell-val.g { color:#68d391; }
.bt-cell-val.r { color:#fc8181; }
.bt-cell-val.a { color:#f6ad55; }

/* Divider con label */
.divider-label {
  display: flex; align-items: center; gap: 12px;
  margin: 28px 0 20px;
}
.divider-label span {
  font-size: 10px; letter-spacing: .16em; text-transform: uppercase;
  color: #2d4a6b; white-space: nowrap;
}
.divider-label::before, .divider-label::after {
  content: ''; flex: 1; height: 1px; background: #111827;
}

/* Consenso badge grande */
.consenso-block {
  display: flex; align-items: center; gap: 16px;
  background: #0d1117; border: 1px solid #1e2a3a;
  border-radius: 10px; padding: 16px 20px;
  margin-bottom: 16px;
}
.consenso-num {
  font-family: 'DM Mono', monospace;
  font-size: 32px; font-weight: 300;
}
.consenso-num.g { color: #68d391; }
.consenso-num.r { color: #fc8181; }
.consenso-num.a { color: #f6ad55; }
.consenso-text { font-size: 12px; color: #718096; line-height: 1.6; }
</style>
""", unsafe_allow_html=True)


# ── Header ────────────────────────────────────────────────
st.markdown("""
<div style="display:flex;justify-content:space-between;align-items:center;
  padding:20px 0 32px;border-bottom:1px solid #111827;margin-bottom:32px">
  <div>
    <div style="font-size:11px;letter-spacing:.18em;text-transform:uppercase;
      color:#2d4a6b;margin-bottom:4px">Sistema de trading algorítmico</div>
    <div style="font-size:22px;font-weight:700;color:#e2e8f0;letter-spacing:-.01em">
      Market Scanner</div>
  </div>
  <div style="font-family:'DM Mono',monospace;font-size:11px;color:#2d4a6b;text-align:right">
""" + datetime.now().strftime("%d/%m/%Y %H:%M") + """
  </div>
</div>
""", unsafe_allow_html=True)


# ── Buscador ──────────────────────────────────────────────
col_input, col_btn, col_per = st.columns([4, 1, 1])
with col_input:
    ticker_input = st.text_input("", placeholder="Buscá un activo: MELI, AAPL, GGAL, YPF, BMA...",
        label_visibility="collapsed",
        help="Ingresá cualquier ticker de NYSE, NASDAQ o CEDEARs")
with col_btn:
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    buscar = st.button("Analizar →", use_container_width=True, type="primary")
with col_per:
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    periodo = st.selectbox("", ["6mo","1y","2y"], index=1, label_visibility="collapsed")


# ── Parámetros ────────────────────────────────────────────
params = {
    "pe_max": 30, "roe_min": 0.10, "de_max": 2.0,
    "rsi_entrada": TECNICO["rsi_entrada"],
    "rsi_salida":  TECNICO["rsi_salida"],
    "stop_loss":   RIESGO["stop_loss"],
    "take_profit": RIESGO["take_profit"],
    "periodo":     periodo,
}


# ── Análisis ──────────────────────────────────────────────
if buscar and ticker_input.strip():
    ticker = ticker_input.strip().upper()

    with st.spinner(f"Analizando {ticker}..."):
        try:
            df = yf.download(ticker, period=periodo, interval="1d", progress=False)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            if df.empty or len(df) < 30:
                st.error(f"No se encontraron datos para '{ticker}'. Verificá el ticker e intentá de nuevo.")
                st.stop()

            # ── Calcular indicadores ──────────────────────
            close  = df["Close"]
            n      = len(close)

            ema9   = ta_lib.trend.ema_indicator(close, window=9)
            ema21  = ta_lib.trend.ema_indicator(close, window=21)
            ema50  = ta_lib.trend.ema_indicator(close, window=50)
            rsi    = ta_lib.momentum.rsi(close, window=14)
            macd_i = ta_lib.trend.MACD(close)
            macd_v = macd_i.macd()
            macd_s = macd_i.macd_signal()
            bb     = ta_lib.volatility.BollingerBands(close, window=20)

            precio     = round(float(close.iloc[-1]), 2)
            rsi_val    = round(float(rsi.iloc[-1]), 1)
            ema9_val   = round(float(ema9.iloc[-1]), 2)
            ema21_val  = round(float(ema21.iloc[-1]), 2)
            ema50_val  = round(float(ema50.iloc[-1]), 2) if n >= 52 else None
            macd_val   = round(float(macd_v.iloc[-1]), 3)
            macd_sig   = round(float(macd_s.iloc[-1]), 3)
            bb_up      = round(float(bb.bollinger_hband().iloc[-1]), 2)
            bb_lo      = round(float(bb.bollinger_lband().iloc[-1]), 2)
            bb_mid     = round(float(bb.bollinger_mavg().iloc[-1]),  2)

            retorno_per = round((precio - float(close.iloc[0])) / float(close.iloc[0]) * 100, 2)

            # ── Lógica de señal ───────────────────────────
            puntos_compra, puntos_venta = 0, 0

            # RSI
            if rsi_val < 35:       puntos_compra += 2
            elif rsi_val < 45:     puntos_compra += 1
            elif rsi_val > 70:     puntos_venta  += 2
            elif rsi_val > 60:     puntos_venta  += 1

            # EMA cruce
            if ema9_val > ema21_val:   puntos_compra += 1
            else:                       puntos_venta  += 1

            # MACD
            if macd_val > macd_sig:    puntos_compra += 1
            else:                       puntos_venta  += 1

            # Bollinger
            if precio <= bb_lo:        puntos_compra += 2
            elif precio >= bb_up:      puntos_venta  += 2

            # EMA50
            if ema50_val:
                if precio > ema50_val: puntos_compra += 1
                else:                  puntos_venta  += 1

            total_pts = puntos_compra + puntos_venta
            fuerza    = round(max(puntos_compra, puntos_venta) / max(total_pts, 1) * 100)

            if puntos_compra > puntos_venta + 1:
                senal_txt  = "COMPRA"
                senal_cls  = "compra"
            elif puntos_venta > puntos_compra + 1:
                senal_txt  = "VENTA"
                senal_cls  = "venta"
            else:
                senal_txt  = "ESPERAR"
                senal_cls  = "esperar"

            sl_val = round(precio * (1 - RIESGO["stop_loss"]),   2)
            tp_val = round(precio * (1 + RIESGO["take_profit"]), 2)

            # ── INFO FUNDAMENTAL ─────────────────────────
            info = {}
            try:
                raw = yf.Ticker(ticker).info
                info = {
                    "nombre":    raw.get("longName", ticker),
                    "sector":    raw.get("sector", "—"),
                    "industria": raw.get("industry", "—"),
                    "pais":      raw.get("country", "—"),
                    "cap":       raw.get("marketCap", None),
                    "pe":        raw.get("trailingPE", None),
                    "pb":        raw.get("priceToBook", None),
                    "ps":        raw.get("priceToSalesTrailing12Months", None),
                    "roe":       raw.get("returnOnEquity", None),
                    "roa":       raw.get("returnOnAssets", None),
                    "margen":    raw.get("profitMargins", None),
                    "de":        raw.get("debtToEquity", None),
                    "rev":       raw.get("totalRevenue", None),
                    "ebitda":    raw.get("ebitda", None),
                    "div":       raw.get("dividendYield", None),
                    "beta":      raw.get("beta", None),
                    "resumen":   raw.get("longBusinessSummary", ""),
                    "52w_high":  raw.get("fiftyTwoWeekHigh", None),
                    "52w_low":   raw.get("fiftyTwoWeekLow",  None),
                    "target":    raw.get("targetMeanPrice",  None),
                    "rec":       raw.get("recommendationKey","—"),
                }
            except:
                info = {"nombre": ticker}

            # ── Patrones ─────────────────────────────────
            res_pat = analizar_patrones(df)

            # ── Backtest ──────────────────────────────────
            bt = backtest(ticker, params)

        except Exception as e:
            st.error(f"Error al analizar {ticker}: {str(e)}")
            st.stop()

    # ════════════════════════════════════════════════════
    # RENDER — SECCIÓN TÉCNICA
    # ════════════════════════════════════════════════════

    nombre_disp = info.get("nombre", ticker)

    # Señal principal hero
    senal_emoji = "▲" if senal_cls=="compra" else ("▼" if senal_cls=="venta" else "◌")
    precio_color = senal_cls
    st.markdown(f"""
    <div class="signal-hero {senal_cls}">
      <div class="signal-tag {senal_cls}">{senal_emoji} señal {senal_txt} · fuerza {fuerza}%</div>
      <div class="signal-price {precio_color}">${precio}</div>
      <div class="signal-ticker">{ticker} · {nombre_disp[:50]} · período {periodo}</div>
      <div class="levels-row">
        <div class="level-item">
          <div class="level-label">Stop Loss</div>
          <div class="level-val sl">${sl_val}</div>
        </div>
        <div class="level-item">
          <div class="level-label">Take Profit</div>
          <div class="level-val tp">${tp_val}</div>
        </div>
        <div class="level-item">
          <div class="level-label">Ratio R/R</div>
          <div class="level-val neu">1 : {round(RIESGO['take_profit']/RIESGO['stop_loss'],1)}</div>
        </div>
        <div class="level-item">
          <div class="level-label">Retorno {periodo}</div>
          <div class="level-val {'tp' if retorno_per>0 else 'sl'}">{retorno_per:+.1f}%</div>
        </div>
        <div class="level-item">
          <div class="level-label">Señales compra/venta</div>
          <div class="level-val neu">{puntos_compra}C · {puntos_venta}V</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Cards de indicadores
    rsi_cls   = "green" if rsi_val<40 else ("red" if rsi_val>65 else "amber")
    macd_cls  = "green" if macd_val>macd_sig else "red"
    ema_cls   = "green" if ema9_val>ema21_val else "red"
    bb_pos    = round((precio - bb_lo) / (bb_up - bb_lo) * 100) if (bb_up - bb_lo) > 0 else 50

    st.markdown(f"""
    <div class="ind-grid">
      <div class="ind-card">
        <div class="ind-label">RSI (14)</div>
        <div class="ind-val {rsi_cls}">{rsi_val}</div>
        <div class="ind-sub">{'Sobrevendido' if rsi_val<40 else ('Sobrecomprado' if rsi_val>65 else 'Neutral')}</div>
      </div>
      <div class="ind-card">
        <div class="ind-label">MACD</div>
        <div class="ind-val {macd_cls}">{macd_val}</div>
        <div class="ind-sub">Señal: {macd_sig} · {'Alcista' if macd_val>macd_sig else 'Bajista'}</div>
      </div>
      <div class="ind-card">
        <div class="ind-label">EMA 9 / 21</div>
        <div class="ind-val {ema_cls}">${ema9_val}</div>
        <div class="ind-sub">EMA21: ${ema21_val} · {'Alcista' if ema9_val>ema21_val else 'Bajista'}</div>
      </div>
      <div class="ind-card">
        <div class="ind-label">Bollinger Bands</div>
        <div class="ind-val {'green' if bb_pos<20 else ('red' if bb_pos>80 else 'amber')}">{bb_pos}%</div>
        <div class="ind-sub">Inf: ${bb_lo} · Sup: ${bb_up}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Patrones técnicos ──────────────────────────────
    st.markdown('<div class="divider-label"><span>patrones detectados</span></div>', unsafe_allow_html=True)

    patrones = res_pat.get("patrones", [])
    consenso = res_pat.get("consenso", "NEUTRAL")
    cons_c   = "g" if consenso=="COMPRA" else ("r" if consenso=="VENTA" else "a")

    col_cons, col_pat = st.columns([1, 2])
    with col_cons:
        st.markdown(f"""
        <div class="consenso-block">
          <div class="consenso-num {cons_c}">{res_pat['fuerza']}%</div>
          <div class="consenso-text">
            Consenso: <b style="color:#e2e8f0">{consenso}</b><br>
            {res_pat['n_compras']} alcistas · {res_pat['n_ventas']} bajistas<br>
            {res_pat['total_patrones']} patrones analizados
          </div>
        </div>
        """, unsafe_allow_html=True)

        # Soportes y resistencias
        sr = res_pat.get("soportes_resistencias", {})
        if sr and sr.get("soportes") and sr.get("resistencias"):
            st.markdown(f"""
            <div style="background:#0d1117;border:1px solid #1e2a3a;border-radius:10px;padding:16px;margin-top:10px">
              <div class="ind-label" style="margin-bottom:12px">Soportes y resistencias</div>
              {''.join([f'<div style="display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid #0a0d13;font-size:12px"><span style="color:#fc8181;font-family:DM Mono,monospace">${n}</span><span style="color:#4a5568">{t} toques</span></div>' for n,t in sr.get("resistencias",[])[:3]])}
              <div style="height:6px"></div>
              {''.join([f'<div style="display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid #0a0d13;font-size:12px"><span style="color:#68d391;font-family:DM Mono,monospace">${n}</span><span style="color:#4a5568">{t} toques</span></div>' for n,t in sr.get("soportes",[])[:3]])}
            </div>
            """, unsafe_allow_html=True)

    with col_pat:
        if not patrones:
            st.markdown('<div style="color:#4a5568;font-size:13px;padding:16px 0">No se detectaron patrones claros. Probá con período 2y.</div>', unsafe_allow_html=True)
        else:
            html_pat = ""
            for p in patrones[:8]:
                tipo_l = p["tipo"].lower()
                s_cls  = "badge-buy"  if p["señal"]=="COMPRA" else ("badge-sell" if p["señal"]=="VENTA" else "badge-wait")
                html_pat += f"""
                <div class="patron-row">
                  <div class="patron-dot {tipo_l if tipo_l in ['alcista','bajista'] else 'neutral'}"></div>
                  <div style="flex:1">
                    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:3px">
                      <span class="patron-name">{p['patron']}</span>
                      <span style="font-size:10px;padding:1px 8px;border-radius:3px;
                        background:{'rgba(104,211,145,.12)' if p['señal']=='COMPRA' else ('rgba(252,129,129,.12)' if p['señal']=='VENTA' else 'rgba(160,174,192,.1)')};
                        color:{'#68d391' if p['señal']=='COMPRA' else ('#fc8181' if p['señal']=='VENTA' else '#a0aec0')}">
                        {p['señal']}
                      </span>
                    </div>
                    <div class="patron-desc">{p['descripcion']}</div>
                    <div class="patron-meta">Objetivo: ${p['objetivo']} · Confianza: {p.get('confianza','—')}</div>
                  </div>
                </div>"""
            st.markdown(html_pat, unsafe_allow_html=True)

    # ── Backtest ──────────────────────────────────────
    if bt:
        st.markdown('<div class="divider-label"><span>backtest histórico</span></div>', unsafe_allow_html=True)
        ret_c = "g" if bt['retorno']>0 else "r"
        alp_c = "g" if bt['alpha_total']>0 else "r"
        shr_c = "g" if bt['sharpe']>1 else ("a" if bt['sharpe']>0.5 else "r")
        wr_c  = "g" if bt['win_rate']>50 else "a"
        dd_c  = "r"
        st.markdown(f"""
        <div class="bt-strip">
          <div class="bt-cell"><div class="bt-cell-label">Retorno total</div><div class="bt-cell-val {ret_c}">{bt['retorno']:+.1f}%</div></div>
          <div class="bt-cell"><div class="bt-cell-label">vs SPY</div><div class="bt-cell-val {alp_c}">{bt['alpha_total']:+.1f}%</div></div>
          <div class="bt-cell"><div class="bt-cell-label">Win rate</div><div class="bt-cell-val {wr_c}">{bt['win_rate']:.0f}%</div></div>
          <div class="bt-cell"><div class="bt-cell-label">Sharpe</div><div class="bt-cell-val {shr_c}">{bt['sharpe']:.2f}</div></div>
          <div class="bt-cell"><div class="bt-cell-label">Max DD</div><div class="bt-cell-val {dd_c}">{bt['max_dd']:.1f}%</div></div>
        </div>
        """, unsafe_allow_html=True)

        eq = bt.get("equity_curve", [])
        if eq:
            st.line_chart(pd.DataFrame({"Equity ($)": eq}),
                          height=160, use_container_width=True)

    # ════════════════════════════════════════════════════
    # SECCIÓN FUNDAMENTAL — contexto, no filtro
    # ════════════════════════════════════════════════════
    st.markdown('<div class="divider-label"><span>análisis fundamental — contexto</span></div>', unsafe_allow_html=True)

    def fmt_num(v, prefijo="", sufijo="", mult=1, decimales=1):
        if v is None: return "—"
        v2 = v * mult
        if abs(v2) >= 1e9:  return f"{prefijo}{v2/1e9:.{decimales}f}B{sufijo}"
        if abs(v2) >= 1e6:  return f"{prefijo}{v2/1e6:.{decimales}f}M{sufijo}"
        return f"{prefijo}{v2:.{decimales}f}{sufijo}"

    pe_txt    = f"{info['pe']:.1f}x"    if info.get("pe")    else "—"
    pb_txt    = f"{info['pb']:.2f}x"    if info.get("pb")    else "—"
    roe_txt   = fmt_num(info.get("roe"), sufijo="%", mult=100)
    roa_txt   = fmt_num(info.get("roa"), sufijo="%", mult=100)
    margen_tx = fmt_num(info.get("margen"), sufijo="%", mult=100)
    de_txt    = f"{info['de']/100:.2f}" if info.get("de") and info["de"]>5 else (f"{info['de']:.2f}" if info.get("de") else "—")
    cap_txt   = fmt_num(info.get("cap"), prefijo="$")
    rev_txt   = fmt_num(info.get("rev"), prefijo="$")
    ebitda_tx = fmt_num(info.get("ebitda"), prefijo="$")
    div_txt   = fmt_num(info.get("div"), sufijo="%", mult=100) if info.get("div") else "Sin dividendo"
    beta_txt  = f"{info['beta']:.2f}" if info.get("beta") else "—"
    target_tx = f"${info['target']:.2f}" if info.get("target") else "—"
    w52_txt   = f"${info.get('52w_low','—')} – ${info.get('52w_high','—')}"
    rec_txt   = str(info.get("rec","—")).upper()

    st.markdown(f"""
    <div class="fund-section">
      <div class="fund-title">{info.get('nombre', ticker)} · {info.get('sector','—')} · {info.get('industria','—')} · {info.get('pais','—')}</div>

      <div class="fund-grid">
        <div class="fund-item"><div class="fund-item-label">P/E Ratio</div><div class="fund-item-val">{pe_txt}</div></div>
        <div class="fund-item"><div class="fund-item-label">P/B Ratio</div><div class="fund-item-val">{pb_txt}</div></div>
        <div class="fund-item"><div class="fund-item-label">Market Cap</div><div class="fund-item-val">{cap_txt}</div></div>
        <div class="fund-item"><div class="fund-item-label">ROE</div><div class="fund-item-val">{roe_txt}</div></div>
        <div class="fund-item"><div class="fund-item-label">ROA</div><div class="fund-item-val">{roa_txt}</div></div>
        <div class="fund-item"><div class="fund-item-label">Margen neto</div><div class="fund-item-val">{margen_tx}</div></div>
        <div class="fund-item"><div class="fund-item-label">Deuda/Equity</div><div class="fund-item-val">{de_txt}</div></div>
        <div class="fund-item"><div class="fund-item-label">Revenue</div><div class="fund-item-val">{rev_txt}</div></div>
        <div class="fund-item"><div class="fund-item-label">EBITDA</div><div class="fund-item-val">{ebitda_tx}</div></div>
        <div class="fund-item"><div class="fund-item-label">Dividendo</div><div class="fund-item-val">{div_txt}</div></div>
        <div class="fund-item"><div class="fund-item-label">Beta</div><div class="fund-item-val">{beta_txt}</div></div>
        <div class="fund-item"><div class="fund-item-label">Target analistas</div><div class="fund-item-val">{target_tx}</div></div>
        <div class="fund-item"><div class="fund-item-label">Rango 52 semanas</div><div class="fund-item-val" style="font-size:12px">{w52_txt}</div></div>
        <div class="fund-item"><div class="fund-item-label">Recomendación</div><div class="fund-item-val">{rec_txt}</div></div>
      </div>

      {'<div class="fund-note">' + info["resumen"][:500] + ('...' if len(info.get("resumen",""))>500 else '') + '</div>' if info.get("resumen") else ''}
    </div>
    """, unsafe_allow_html=True)

    # Alerta Telegram si hay compra fuerte
    if senal_cls == "compra" and fuerza >= 70:
        try:
            send_telegram(
                f"🟢 *SEÑAL FUERTE DE COMPRA*\n"
                f"Ticker: *{ticker}*\n"
                f"Precio: ${precio} | Fuerza: {fuerza}%\n"
                f"Stop Loss: ${sl_val} | Take Profit: ${tp_val}\n"
                f"RSI: {rsi_val} | MACD: {'▲' if macd_val>macd_sig else '▼'}"
            )
        except: pass

else:
    # Estado inicial — pantalla vacía con instrucción
    st.markdown("""
    <div style="text-align:center;padding:80px 0;color:#2d4a6b">
      <div style="font-size:48px;margin-bottom:16px">↑</div>
      <div style="font-size:14px;letter-spacing:.1em;text-transform:uppercase">
        Ingresá un ticker para comenzar el análisis
      </div>
      <div style="font-size:12px;margin-top:8px;color:#1e3050">
        NYSE · NASDAQ · CEDEARs · Merval
      </div>
    </div>
    """, unsafe_allow_html=True)
