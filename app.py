# ============================================================
#  SISTEMA DE TRADING ALGORÍTMICO — STREAMLIT APP
#  Archivo principal: app.py
#
#  INSTRUCCIONES DE DEPLOY:
#  1. Subir esta carpeta a GitHub
#  2. Ir a share.streamlit.io → conectar repo
#  3. Configurar secrets (ver README.md)
# ============================================================

import streamlit as st
import pandas as pd
import numpy as np
import json
from datetime import datetime
import time

from engine   import run_analysis
from alerts   import send_telegram
from reports  import generate_pdf
from config   import UNIVERSE_NYSE, UNIVERSE_CEDEARS, TECNICO, RIESGO, CONFIG

# ── Configuración de página ───────────────────────────────
st.set_page_config(
    page_title="Trading System",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── CSS personalizado ─────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@300;400;500&display=swap');

  html, body, [class*="css"] { font-family: 'IBM Plex Sans', sans-serif; }
  .main { background-color: #0a0e14; }
  .stApp { background-color: #0a0e14; color: #e2e8f0; }

  .metric-card {
    background: #111720;
    border: 1px solid rgba(99,179,237,0.15);
    border-radius: 10px;
    padding: 16px 20px;
    margin-bottom: 12px;
  }
  .metric-label {
    font-size: 11px; color: #718096;
    letter-spacing: .1em; text-transform: uppercase;
    margin-bottom: 4px;
  }
  .metric-value {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 24px; font-weight: 300; color: #e2e8f0;
  }
  .metric-value.green { color: #68d391; }
  .metric-value.red   { color: #fc8181; }
  .metric-value.amber { color: #f6ad55; }

  .signal-buy  { color: #68d391; font-weight: 500; }
  .signal-wait { color: #718096; }
  .signal-sell { color: #fc8181; font-weight: 500; }

  .section-header {
    font-size: 11px; font-weight: 500; color: #63b3ed;
    letter-spacing: .12em; text-transform: uppercase;
    border-bottom: 1px solid rgba(99,179,237,0.2);
    padding-bottom: 6px; margin-bottom: 14px;
  }
  .badge {
    display: inline-block; font-size: 11px; padding: 2px 10px;
    border-radius: 3px; font-weight: 500;
  }
  .badge-buy  { background: rgba(104,211,145,.15); color: #68d391; border: 1px solid rgba(104,211,145,.3); }
  .badge-wait { background: rgba(113,128,150,.15); color: #a0aec0; border: 1px solid rgba(113,128,150,.3); }
  .badge-sell { background: rgba(252,129,129,.15); color: #fc8181; border: 1px solid rgba(252,129,129,.3); }

  div[data-testid="stSidebar"] { background: #111720 !important; }
  div[data-testid="stSidebar"] * { color: #e2e8f0 !important; }
</style>
""", unsafe_allow_html=True)


# ── Sidebar ───────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Configuración")
    st.divider()

    mercado = st.multiselect(
        "Mercados",
        ["NYSE / NASDAQ", "CEDEARs (Merval)"],
        default=["NYSE / NASDAQ", "CEDEARs (Merval)"]
    )

    periodo = st.selectbox("Período backtest", ["6mo", "1y", "2y"], index=1)

    st.markdown("**Filtros fundamentales**")
    pe_max  = st.slider("P/E máximo",      10, 50, CONFIG["pe_max"])
    roe_min = st.slider("ROE mínimo (%)",   5, 30, int(CONFIG["roe_min"]*100))
    de_max  = st.slider("Deuda/Equity máx", 0.5, 3.0, CONFIG["de_max"], step=0.1)

    st.markdown("**Parámetros técnicos**")
    rsi_e = st.slider("RSI entrada", 20, 50, TECNICO["rsi_entrada"])
    rsi_s = st.slider("RSI salida",  55, 80, TECNICO["rsi_salida"])

    st.markdown("**Gestión de riesgo**")
    sl = st.slider("Stop Loss (%)",   1, 15, int(RIESGO["stop_loss"]*100))
    tp = st.slider("Take Profit (%)", 5, 30, int(RIESGO["take_profit"]*100))

    st.divider()
    refresh_min = st.selectbox("Actualización automática", [5, 10, 15, 30], index=2)
    auto_refresh = st.toggle("Activar auto-refresh", value=True)

    st.divider()
    if st.button("📄 Generar PDF", use_container_width=True):
        st.session_state["gen_pdf"] = True

    if st.button("🔄 Analizar ahora", use_container_width=True, type="primary"):
        st.session_state["force_run"] = True


# ── Parámetros dinámicos ──────────────────────────────────
params = {
    "pe_max":      pe_max,
    "roe_min":     roe_min / 100,
    "de_max":      de_max,
    "rsi_entrada": rsi_e,
    "rsi_salida":  rsi_s,
    "stop_loss":   sl / 100,
    "take_profit": tp / 100,
    "periodo":     periodo,
}

universe = []
if "NYSE / NASDAQ" in mercado:
    universe += UNIVERSE_NYSE
if "CEDEARs (Merval)" in mercado:
    universe += UNIVERSE_CEDEARS


# ── Auto-refresh ──────────────────────────────────────────
if auto_refresh:
    # Streamlit re-runs cada N minutos solo si usás st.rerun con time
    if "last_run" not in st.session_state:
        st.session_state["last_run"] = 0
    elapsed = time.time() - st.session_state["last_run"]
    if elapsed > refresh_min * 60 or st.session_state.get("force_run"):
        st.session_state["force_run"] = False
        st.session_state["last_run"]  = time.time()
        st.session_state["results"]   = run_analysis(universe, params)
        st.session_state["run_time"]  = datetime.now().strftime("%H:%M:%S")


# ── Ejecutar análisis si no hay resultados ────────────────
if "results" not in st.session_state:
    with st.spinner("Analizando mercado..."):
        st.session_state["results"]  = run_analysis(universe, params)
        st.session_state["run_time"] = datetime.now().strftime("%H:%M:%S")

results  = st.session_state["results"]
run_time = st.session_state.get("run_time", "—")


# ── Header ────────────────────────────────────────────────
col_t, col_d = st.columns([3, 1])
with col_t:
    st.markdown("## 📈 Trading System")
    st.caption(f"Última actualización: {run_time}  ·  Próxima en {refresh_min} min  ·  {len(universe)} activos analizados")
with col_d:
    ahora = datetime.now()
    mercado_abierto = 9 <= ahora.hour < 16 and ahora.weekday() < 5
    estado = "🟢 Mercado abierto" if mercado_abierto else "🔴 Mercado cerrado"
    st.markdown(f"<div style='text-align:right;padding-top:14px;color:#718096;font-size:13px'>{estado}<br>{ahora.strftime('%d/%m/%Y %H:%M')}</div>", unsafe_allow_html=True)

st.divider()


# ── KPIs globales ─────────────────────────────────────────
fund   = results.get("fundamental", [])
senales = results.get("senales", {})
bts    = results.get("backtests", {})

total       = len(universe)
aprobadas   = [r for r in fund if r["estado"] == "ok"]
n_compra    = sum(1 for s in senales.values() if s.get("senal") == "COMPRA")
best_ret    = max((b.get("retorno", 0) for b in bts.values()), default=0)

k1, k2, k3, k4, k5 = st.columns(5)
def kpi(col, label, val, color=""):
    col.markdown(f"""
    <div class="metric-card">
      <div class="metric-label">{label}</div>
      <div class="metric-value {color}">{val}</div>
    </div>""", unsafe_allow_html=True)

kpi(k1, "Activos analizados", total)
kpi(k2, "Pasan filtro fund.", len(aprobadas), "amber" if aprobadas else "")
kpi(k3, "Señal COMPRA hoy",   n_compra, "green" if n_compra > 0 else "")
kpi(k4, "Mejor retorno (BT)", f"+{best_ret:.1f}%" if best_ret > 0 else f"{best_ret:.1f}%", "green" if best_ret > 0 else "red")
kpi(k5, "Stop / Take Profit", f"-{sl}% / +{tp}%")


# ── Tabs principales ──────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🔍 Screener", "📊 Señales", "🔬 Backtesting", "📉 Riesgo", "🌎 Benchmark"
])


# ════════════════════════════════════════════════════
# TAB 1: SCREENER FUNDAMENTAL
# ════════════════════════════════════════════════════
with tab1:
    st.markdown('<div class="section-header">Screener fundamental</div>', unsafe_allow_html=True)

    col_f, col_s = st.columns([2, 1])
    with col_f:
        filtro_estado = st.radio("Mostrar", ["Todos", "Solo aprobadas", "Solo rechazadas"], horizontal=True)

    rows_display = fund
    if filtro_estado == "Solo aprobadas":
        rows_display = [r for r in fund if r["estado"] == "ok"]
    elif filtro_estado == "Solo rechazadas":
        rows_display = [r for r in fund if r["estado"] != "ok"]

    if rows_display:
        df_fund = pd.DataFrame(rows_display)
        df_fund["Estado"] = df_fund["estado"].apply(
            lambda x: "✅ PASA" if x == "ok" else ("⚠️ Sin datos" if x == "sin_datos" else "❌ Falla")
        )
        df_fund["Mercado"] = df_fund["mercado"]
        df_display = df_fund[["ticker", "nombre", "Mercado", "pe", "roe", "de", "motivo", "Estado"]].copy()
        df_display.columns = ["Ticker", "Empresa", "Mercado", "P/E", "ROE %", "D/E", "Detalle", "Estado"]
        st.dataframe(df_display, use_container_width=True, hide_index=True,
            column_config={
                "Ticker":  st.column_config.TextColumn(width="small"),
                "Estado":  st.column_config.TextColumn(width="small"),
                "Mercado": st.column_config.TextColumn(width="small"),
            })
    else:
        st.info("Sin datos disponibles.")


# ════════════════════════════════════════════════════
# TAB 2: SEÑALES TÉCNICAS
# ════════════════════════════════════════════════════
with tab2:
    st.markdown('<div class="section-header">Señales técnicas en tiempo real</div>', unsafe_allow_html=True)

    if not senales:
        st.warning("Ninguna acción pasó el filtro fundamental. Considerá ajustar los parámetros.")
    else:
        cols = st.columns(3)
        for i, (ticker, s) in enumerate(senales.items()):
            col = cols[i % 3]
            senal     = s.get("senal", "ESPERAR")
            badge_cls = "badge-buy" if senal == "COMPRA" else ("badge-sell" if senal == "VENDER" else "badge-wait")
            badge_txt = "▲ COMPRA" if senal == "COMPRA" else ("▼ VENDER" if senal == "VENDER" else "◌ ESPERAR")
            rsi_color = "#68d391" if s['rsi'] < 40 else ("#fc8181" if s['rsi'] > 65 else "#f6ad55")

            col.markdown(f"""
            <div class="metric-card" style="{'border-color:rgba(104,211,145,.5)' if senal=='COMPRA' else ''}">
              <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px">
                <span style="font-family:'IBM Plex Mono',monospace;font-size:15px;font-weight:500;color:#e2e8f0">{ticker}</span>
                <span class="badge {badge_cls}">{badge_txt}</span>
              </div>
              <div style="font-family:'IBM Plex Mono',monospace;font-size:20px;color:#63b3ed;margin-bottom:10px">${s['precio']}</div>
              <div style="font-size:12px;color:#718096;line-height:2">
                RSI: <span style="color:{rsi_color}">{s['rsi']}</span><br>
                EMA9: ${s['ema_r']} &nbsp;|&nbsp; EMA21: ${s['ema_l']}<br>
                Stop: <span style="color:#fc8181">${s['stop_loss']}</span> &nbsp;|&nbsp;
                TP: <span style="color:#68d391">${s['take_profit']}</span>
              </div>
            </div>""", unsafe_allow_html=True)

            # Enviar alerta Telegram si hay señal de compra
            if senal == "COMPRA" and s.get("alerta_enviada") is not True:
                try:
                    msg = (f"🟢 *SEÑAL DE COMPRA*\n"
                           f"Ticker: *{ticker}*\n"
                           f"Precio: ${s['precio']}\n"
                           f"RSI: {s['rsi']}\n"
                           f"Stop Loss: ${s['stop_loss']}\n"
                           f"Take Profit: ${s['take_profit']}\n"
                           f"Hora: {datetime.now().strftime('%H:%M')}")
                    send_telegram(msg)
                    s["alerta_enviada"] = True
                except:
                    pass


# ════════════════════════════════════════════════════
# TAB 3: BACKTESTING COMPLETO
# ════════════════════════════════════════════════════
with tab3:
    st.markdown('<div class="section-header">Backtesting profesional</div>', unsafe_allow_html=True)

    if not bts:
        st.info("No hay datos de backtest. Las acciones deben pasar el filtro fundamental primero.")
    else:
        ticker_sel = st.selectbox("Seleccionar activo", list(bts.keys()))
        m = bts[ticker_sel]

        # KPIs del backtest
        b1, b2, b3, b4, b5, b6 = st.columns(6)
        kpi(b1, "Retorno total",     f"{m['retorno']:+.1f}%",    "green" if m['retorno']>0 else "red")
        kpi(b2, "Win rate",          f"{m['win_rate']:.1f}%",    "green" if m['win_rate']>50 else "amber")
        kpi(b3, "Total trades",      m['total_trades'])
        kpi(b4, "Sharpe ratio",      f"{m['sharpe']:.2f}",       "green" if m['sharpe']>1 else "amber")
        kpi(b5, "Sortino ratio",     f"{m['sortino']:.2f}",      "green" if m['sortino']>1.5 else "amber")
        kpi(b6, "Max Drawdown",      f"{m['max_dd']:.1f}%",      "red")

        c1, c2 = st.columns(2)
        with c1:
            st.markdown('<div class="section-header" style="margin-top:8px">Ratios ajustados por riesgo</div>', unsafe_allow_html=True)
            ratios_df = pd.DataFrame([
                ["Sharpe Ratio",    f"{m['sharpe']:.4f}",   "Retorno/volatilidad total",          "> 1.0 = Bueno"],
                ["Sortino Ratio",   f"{m['sortino']:.4f}",  "Retorno/volatilidad negativa",        "> 1.5 = Excelente"],
                ["Treynor Ratio",   f"{m['treynor']:.4f}",  "Retorno/riesgo sistémico (Beta)",     "> 0 = Positivo"],
                ["Calmar Ratio",    f"{m['calmar']:.4f}",   "Retorno anual/Max Drawdown",          "> 1.0 = Bueno"],
                ["Profit Factor",   f"{m['profit_factor']:.2f}", "Ganancias brutas/pérdidas brutas","≥ 1.25 = Aceptable"],
                ["AUC Equity",      f"{m['auc']:.4f}",      "Área bajo curva normalizada",         "> 0.55 = Bueno"],
                ["Beta vs SPY",     f"{m['beta']:.4f}",     "Sensibilidad al mercado",             "< 1 = Menos riesgo"],
                ["Alpha anual",     f"{m['alpha_anual']:+.2f}%", "Exceso sobre benchmark",         "> 0% = Agrega valor"],
            ], columns=["Ratio", "Valor", "Descripción", "Referencia"])
            st.dataframe(ratios_df, use_container_width=True, hide_index=True)

        with c2:
            st.markdown('<div class="section-header" style="margin-top:8px">Estadísticas de trades</div>', unsafe_allow_html=True)
            stats_df = pd.DataFrame([
                ["Total trades",           m['total_trades']],
                ["Wins",                   m['wins']],
                ["Losses",                 m['losses']],
                ["Win rate",               f"{m['win_rate']:.1f}%"],
                ["Ganancia media",         f"+{m['ganancia_media']:.2f}%"],
                ["Pérdida media",          f"-{m['perdida_media']:.2f}%"],
                ["Duración media",         f"{m['duracion_media']:.1f} días"],
                ["Retorno anualizado",     f"{m['retorno_anual']:+.2f}%"],
                ["VaR 95% diario",         f"{m['var_95']:.3f}%"],
                ["CVaR 95% diario",        f"{m['cvar_95']:.3f}%"],
                ["Volatilidad anualizada", f"{m['volatilidad']:.2f}%"],
                ["Max DD duración",        f"{m['max_dd_dur']} días"],
            ], columns=["Métrica", "Valor"])
            st.dataframe(stats_df, use_container_width=True, hide_index=True)

        # Curva de equity
        st.markdown('<div class="section-header" style="margin-top:16px">Curva de equity</div>', unsafe_allow_html=True)
        eq = m.get("equity_curve", [])
        if eq:
            eq_df = pd.DataFrame({"Equity ($)": eq})
            st.line_chart(eq_df, use_container_width=True, height=220)

        # Detalle de trades
        st.markdown('<div class="section-header">Detalle de operaciones</div>', unsafe_allow_html=True)
        if m.get("trades"):
            trades_df = pd.DataFrame(m["trades"])
            trades_df["entrada"] = trades_df["entrada"].astype(str).str[:10]
            trades_df["salida"]  = trades_df["salida"].astype(str).str[:10]
            st.dataframe(trades_df, use_container_width=True, hide_index=True)


# ════════════════════════════════════════════════════
# TAB 4: RIESGO
# ════════════════════════════════════════════════════
with tab4:
    st.markdown('<div class="section-header">Métricas de riesgo del portafolio</div>', unsafe_allow_html=True)

    if bts:
        riesgo_rows = []
        for t, m in bts.items():
            riesgo_rows.append({
                "Ticker":      t,
                "Max DD":      f"{m['max_dd']:.1f}%",
                "Volatilidad": f"{m['volatilidad']:.1f}%",
                "VaR 95%":     f"{m['var_95']:.3f}%",
                "CVaR 95%":    f"{m['cvar_95']:.3f}%",
                "Beta":        f"{m['beta']:.2f}",
                "Calmar":      f"{m['calmar']:.2f}",
                "DD Duración": f"{m['max_dd_dur']}d",
            })
        st.dataframe(pd.DataFrame(riesgo_rows), use_container_width=True, hide_index=True)

        st.divider()
        st.markdown("#### Interpretación de métricas de riesgo")
        st.markdown("""
        | Métrica | Qué mide | Umbral aceptable |
        |---------|----------|-----------------|
        | **Max Drawdown** | Caída máxima pico a valle | < 20% para swing trading |
        | **Volatilidad anualizada** | Dispersión de retornos diarios × √252 | < 25% moderado |
        | **VaR 95%** | Pérdida máxima en 95% de los días | Depende del capital |
        | **CVaR / Expected Shortfall** | Pérdida promedio en el peor 5% de días | Siempre > VaR |
        | **Beta** | Correlación con el mercado | < 1 = menos riesgo sistémico |
        | **Calmar** | Retorno anual / Max DD | > 1 = excelente |
        """)
    else:
        st.info("Correr el análisis primero para ver métricas de riesgo.")


# ════════════════════════════════════════════════════
# TAB 5: BENCHMARK
# ════════════════════════════════════════════════════
with tab5:
    st.markdown('<div class="section-header">Comparación con benchmark (SPY)</div>', unsafe_allow_html=True)

    if bts:
        bm_rows = []
        for t, m in bts.items():
            bm_rows.append({
                "Ticker":          t,
                "Retorno estrategia": f"{m['retorno']:+.1f}%",
                "Retorno SPY":     f"{m['bm_retorno']:+.1f}%",
                "Alpha total":     f"{m['alpha_total']:+.1f}%",
                "Alpha anual":     f"{m['alpha_anual']:+.2f}%",
                "Sharpe":          f"{m['sharpe']:.2f}",
                "Sortino":         f"{m['sortino']:.2f}",
                "Beta":            f"{m['beta']:.2f}",
                "Treynor":         f"{m['treynor']:.4f}",
            })
        st.dataframe(pd.DataFrame(bm_rows), use_container_width=True, hide_index=True)
    else:
        st.info("Sin datos de benchmark disponibles.")


# ── Generación de PDF bajo demanda ────────────────────────
if st.session_state.get("gen_pdf"):
    st.session_state["gen_pdf"] = False
    with st.spinner("Generando informe PDF..."):
        pdf_bytes = generate_pdf(results, params)
    st.download_button(
        "⬇️ Descargar informe PDF",
        data=pdf_bytes,
        file_name=f"informe_trading_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
        mime="application/pdf"
    )

# ── Auto-rerun ────────────────────────────────────────────
if auto_refresh:
    time.sleep(1)
    st.rerun()
