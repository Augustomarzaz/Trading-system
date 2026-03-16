# ============================================================
#  app.py — Dashboard principal actualizado
#  + Buscador manual de tickers
#  + Tab de patrones técnicos históricos
# ============================================================

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import json
from datetime import datetime
import time

from engine   import run_analysis, backtest
from alerts   import send_telegram
from reports  import generate_pdf
from patterns import analizar_patrones
from config   import UNIVERSE_NYSE, UNIVERSE_CEDEARS, TECNICO, RIESGO, CONFIG

st.set_page_config(
    page_title="Trading System",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@300;400;500&display=swap');
  html, body, [class*="css"] { font-family: 'IBM Plex Sans', sans-serif; }
  .stApp { background-color: #0a0e14; color: #e2e8f0; }
  div[data-testid="stSidebar"] { background: #111720 !important; }
  div[data-testid="stSidebar"] * { color: #e2e8f0 !important; }
  .metric-card {
    background: #111720; border: 1px solid rgba(99,179,237,0.15);
    border-radius: 10px; padding: 16px 20px; margin-bottom: 12px;
  }
  .metric-label { font-size: 11px; color: #718096; letter-spacing:.1em; text-transform:uppercase; margin-bottom:4px; }
  .metric-value { font-family:'IBM Plex Mono',monospace; font-size:24px; font-weight:300; color:#e2e8f0; }
  .metric-value.green { color:#68d391; }
  .metric-value.red   { color:#fc8181; }
  .metric-value.amber { color:#f6ad55; }
  .section-header {
    font-size:11px; font-weight:500; color:#63b3ed;
    letter-spacing:.12em; text-transform:uppercase;
    border-bottom:1px solid rgba(99,179,237,0.2);
    padding-bottom:6px; margin-bottom:14px;
  }
  .patron-card {
    background:#111720; border:1px solid rgba(99,179,237,0.12);
    border-radius:10px; padding:16px; margin-bottom:10px;
  }
  .patron-card.alcista { border-color: rgba(104,211,145,0.4); }
  .patron-card.bajista { border-color: rgba(252,129,129,0.35); }
  .badge { display:inline-block; font-size:11px; padding:2px 10px; border-radius:3px; font-weight:500; }
  .badge-buy  { background:rgba(104,211,145,.15); color:#68d391; border:1px solid rgba(104,211,145,.3); }
  .badge-sell { background:rgba(252,129,129,.15); color:#fc8181; border:1px solid rgba(252,129,129,.3); }
  .badge-wait { background:rgba(113,128,150,.15); color:#a0aec0; border:1px solid rgba(113,128,150,.3); }
  .badge-alta  { background:rgba(104,211,145,.12); color:#68d391; font-size:10px; padding:1px 7px; border-radius:3px; }
  .badge-media { background:rgba(246,173,85,.12);  color:#f6ad55; font-size:10px; padding:1px 7px; border-radius:3px; }
  .badge-baja  { background:rgba(252,129,129,.12); color:#fc8181; font-size:10px; padding:1px 7px; border-radius:3px; }
</style>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Configuración")
    st.divider()
    st.markdown("**🔍 Análisis de activo específico**")
    ticker_manual   = st.text_input("Ingresar ticker", placeholder="Ej: AAPL, GGAL, YPF, BMA...",
        help="NYSE/NASDAQ: AAPL, MSFT\nCEDEARs: GGAL, YPF, BMA\nMerval: GGAL.BA, YPFD.BA")
    analizar_manual = st.button("🔎 Analizar ticker", use_container_width=True, type="primary")
    st.divider()
    st.markdown("**📊 Screener automático**")
    mercado  = st.multiselect("Mercados", ["NYSE / NASDAQ", "CEDEARs (Merval)"],
                               default=["NYSE / NASDAQ", "CEDEARs (Merval)"])
    periodo  = st.selectbox("Período", ["6mo", "1y", "2y"], index=1)
    st.markdown("**Filtros fundamentales**")
    pe_max   = st.slider("P/E máximo",        10, 50,  CONFIG["pe_max"])
    roe_min  = st.slider("ROE mínimo (%)",      5, 30,  int(CONFIG["roe_min"]*100))
    de_max   = st.slider("Deuda/Equity máx.", 0.5, 3.0, CONFIG["de_max"], step=0.1)
    st.markdown("**Parámetros técnicos**")
    rsi_e    = st.slider("RSI entrada", 20, 50, TECNICO["rsi_entrada"])
    rsi_s    = st.slider("RSI salida",  55, 80, TECNICO["rsi_salida"])
    st.markdown("**Gestión de riesgo**")
    sl       = st.slider("Stop Loss (%)",    1, 15, int(RIESGO["stop_loss"]*100))
    tp       = st.slider("Take Profit (%)", 5, 30, int(RIESGO["take_profit"]*100))
    st.divider()
    refresh_min  = st.selectbox("Auto-refresh (min)", [5, 10, 15, 30], index=2)
    auto_refresh = st.toggle("Activar auto-refresh", value=True)
    st.divider()
    if st.button("📄 Generar PDF", use_container_width=True):
        st.session_state["gen_pdf"] = True
    if st.button("🔄 Analizar ahora", use_container_width=True):
        st.session_state["force_run"] = True

params = {
    "pe_max": pe_max, "roe_min": roe_min/100, "de_max": de_max,
    "rsi_entrada": rsi_e, "rsi_salida": rsi_s,
    "stop_loss": sl/100, "take_profit": tp/100, "periodo": periodo,
}
universe = []
if "NYSE / NASDAQ"    in mercado: universe += UNIVERSE_NYSE
if "CEDEARs (Merval)" in mercado: universe += UNIVERSE_CEDEARS

# ── Auto-refresh ──────────────────────────────────────────
if auto_refresh:
    if "last_run" not in st.session_state:
        st.session_state["last_run"] = 0
    elapsed = time.time() - st.session_state["last_run"]
    if elapsed > refresh_min * 60 or st.session_state.get("force_run"):
        st.session_state["force_run"] = False
        st.session_state["last_run"]  = time.time()
        st.session_state["results"]   = run_analysis(universe, params)
        st.session_state["run_time"]  = datetime.now().strftime("%H:%M:%S")

if "results" not in st.session_state:
    with st.spinner("Analizando mercado..."):
        st.session_state["results"]  = run_analysis(universe, params)
        st.session_state["run_time"] = datetime.now().strftime("%H:%M:%S")

results  = st.session_state["results"]
run_time = st.session_state.get("run_time", "—")


def kpi(col, label, val, color=""):
    col.markdown(f'<div class="metric-card"><div class="metric-label">{label}</div><div class="metric-value {color}">{val}</div></div>', unsafe_allow_html=True)


# ── ANÁLISIS MANUAL ───────────────────────────────────────
if analizar_manual and ticker_manual.strip():
    ticker_clean = ticker_manual.strip().upper()
    st.markdown(f"## 🔍 Análisis: {ticker_clean}")
    st.divider()

    with st.spinner(f"Descargando datos de {ticker_clean}..."):
        try:
            df_m = yf.download(ticker_clean, period=periodo, interval="1d", progress=False)
            if isinstance(df_m.columns, pd.MultiIndex):
                df_m.columns = df_m.columns.get_level_values(0)

            if df_m.empty or len(df_m) < 30:
                st.error(f"No se encontraron datos para '{ticker_clean}'. Verificá el ticker.")
            else:
                precio_actual = round(float(df_m["Close"].iloc[-1]), 2)
                precio_inicio = round(float(df_m["Close"].iloc[0]),  2)
                retorno_per   = round((precio_actual - precio_inicio) / precio_inicio * 100, 2)

                k1, k2, k3, k4 = st.columns(4)
                kpi(k1, "Precio actual",      f"${precio_actual}")
                kpi(k2, f"Retorno ({periodo})", f"{retorno_per:+.1f}%", "green" if retorno_per>0 else "red")
                kpi(k3, "Período",             periodo)
                kpi(k4, "Velas disponibles",   len(df_m))

                tab_p, tab_sr, tab_bt = st.tabs(["📐 Patrones", "📏 Soportes/Resistencias", "🔬 Backtest"])

                with tab_p:
                    res_pat  = analizar_patrones(df_m)
                    patrones = res_pat["patrones"]
                    consenso = res_pat["consenso"]
                    c_color  = "green" if consenso=="COMPRA" else ("red" if consenso=="VENTA" else "amber")

                    c1,c2,c3,c4 = st.columns(4)
                    kpi(c1, "Patrones detectados", res_pat["total_patrones"])
                    kpi(c2, "Consenso",            consenso, c_color)
                    kpi(c3, "Señales compra",       res_pat["n_compras"], "green" if res_pat["n_compras"]>0 else "")
                    kpi(c4, "Señales venta",        res_pat["n_ventas"],  "red"   if res_pat["n_ventas"]>0  else "")
                    st.divider()

                    if not patrones:
                        st.info("No se detectaron patrones claros. Probá con período más largo (2y).")
                    else:
                        for p in patrones:
                            tipo_l    = p["tipo"].lower()
                            badge_cls = "badge-buy"  if p["señal"]=="COMPRA" else ("badge-sell" if p["señal"]=="VENTA" else "badge-wait")
                            badge_txt = "▲ COMPRA"   if p["señal"]=="COMPRA" else ("▼ VENTA"    if p["señal"]=="VENTA" else "◌ "+p["señal"])
                            conf_cls  = f"badge-{p.get('confianza','Media').lower()}"
                            st.markdown(f"""
                            <div class="patron-card {tipo_l}">
                              <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
                                <span style="font-size:14px;font-weight:500;color:#e2e8f0">{p['patron']}</span>
                                <div>
                                  <span class="badge {badge_cls}" style="margin-right:6px">{badge_txt}</span>
                                  <span class="{conf_cls}">Confianza: {p.get('confianza','—')}</span>
                                </div>
                              </div>
                              <div style="font-size:12px;color:#a0aec0;line-height:1.8">
                                {p['descripcion']}<br>
                                <span style="color:#718096">Detectado: {p['fecha']} | Precio patrón: ${p['precio_patron']} | Objetivo: ${p['objetivo']}</span>
                              </div>
                            </div>""", unsafe_allow_html=True)

                with tab_sr:
                    sr = res_pat.get("soportes_resistencias", {})
                    if sr:
                        s_color = "green" if sr.get("señal")=="COMPRA" else ("red" if sr.get("señal")=="VENTA" else "amber")
                        cs1, cs2 = st.columns(2)
                        kpi(cs1, "Precio actual", f"${sr.get('precio_actual', precio_actual)}")
                        kpi(cs2, "Señal S/R",      sr.get("señal","NEUTRAL"), s_color)
                        st.caption(sr.get("descripcion",""))
                        st.divider()
                        col_r, col_s = st.columns(2)
                        with col_r:
                            st.markdown('<div class="section-header">Resistencias</div>', unsafe_allow_html=True)
                            for nivel, toques in sr.get("resistencias", []):
                                dist = round((nivel - precio_actual) / precio_actual * 100, 1)
                                st.markdown(f'<div style="display:flex;justify-content:space-between;padding:7px 0;border-bottom:1px solid rgba(99,179,237,0.08);font-size:13px"><span style="color:#fc8181;font-family:monospace">${nivel}</span><span style="color:#718096">{toques} toques | +{dist}%</span></div>', unsafe_allow_html=True)
                        with col_s:
                            st.markdown('<div class="section-header">Soportes</div>', unsafe_allow_html=True)
                            for nivel, toques in sr.get("soportes", []):
                                dist = round((precio_actual - nivel) / precio_actual * 100, 1)
                                st.markdown(f'<div style="display:flex;justify-content:space-between;padding:7px 0;border-bottom:1px solid rgba(99,179,237,0.08);font-size:13px"><span style="color:#68d391;font-family:monospace">${nivel}</span><span style="color:#718096">{toques} toques | -{dist}%</span></div>', unsafe_allow_html=True)

                with tab_bt:
                    with st.spinner("Calculando backtest..."):
                        bt_r = backtest(ticker_clean, params)
                    if bt_r:
                        b1,b2,b3,b4,b5,b6 = st.columns(6)
                        kpi(b1,"Retorno",   f"{bt_r['retorno']:+.1f}%",   "green" if bt_r['retorno']>0 else "red")
                        kpi(b2,"Win rate",  f"{bt_r['win_rate']:.1f}%",  "green" if bt_r['win_rate']>50 else "amber")
                        kpi(b3,"Trades",    bt_r['total_trades'])
                        kpi(b4,"Sharpe",    f"{bt_r['sharpe']:.2f}",     "green" if bt_r['sharpe']>1 else "amber")
                        kpi(b5,"Max DD",    f"{bt_r['max_dd']:.1f}%",    "red")
                        kpi(b6,"vs SPY",    f"{bt_r['alpha_total']:+.1f}%","green" if bt_r['alpha_total']>0 else "red")
                        eq = bt_r.get("equity_curve", [])
                        if eq:
                            st.line_chart(pd.DataFrame({"Equity ($)": eq}), height=200)
                    else:
                        st.warning("No se pudo calcular el backtest para este ticker.")

        except Exception as e:
            st.error(f"Error: {str(e)}")
    st.divider()


# ── Header ────────────────────────────────────────────────
ct, cd = st.columns([3,1])
with ct:
    st.markdown("## 📈 Trading System — Screener automático")
    st.caption(f"Última actualización: {run_time} · {len(universe)} activos · Auto-refresh: {refresh_min} min")
with cd:
    ahora   = datetime.now()
    abierto = 9 <= ahora.hour < 16 and ahora.weekday() < 5
    st.markdown(f"<div style='text-align:right;padding-top:14px;color:#718096;font-size:13px'>{'🟢 Mercado abierto' if abierto else '🔴 Mercado cerrado'}<br>{ahora.strftime('%d/%m/%Y %H:%M')}</div>", unsafe_allow_html=True)

st.divider()

fund      = results.get("fundamental", [])
senales   = results.get("senales",     {})
bts       = results.get("backtests",   {})
aprobadas = [r for r in fund if r["estado"]=="ok"]
n_compra  = sum(1 for s in senales.values() if s.get("senal")=="COMPRA")
best_ret  = max((b.get("retorno",0) for b in bts.values()), default=0)

k1,k2,k3,k4,k5 = st.columns(5)
kpi(k1,"Activos analizados", len(universe))
kpi(k2,"Pasan filtro",       len(aprobadas), "amber" if aprobadas else "")
kpi(k3,"Señal COMPRA",       n_compra,       "green" if n_compra>0 else "")
kpi(k4,"Mejor retorno (BT)", f"+{best_ret:.1f}%" if best_ret>0 else f"{best_ret:.1f}%", "green" if best_ret>0 else "red")
kpi(k5,"Stop / TP",          f"-{sl}% / +{tp}%")

tab1,tab2,tab3,tab4,tab5 = st.tabs(["🔍 Screener","📊 Señales","🔬 Backtesting","📉 Riesgo","🌎 Benchmark"])

with tab1:
    st.markdown('<div class="section-header">Screener fundamental</div>', unsafe_allow_html=True)
    filtro = st.radio("Mostrar",["Todos","Solo aprobadas","Solo rechazadas"], horizontal=True)
    rows   = fund
    if filtro=="Solo aprobadas":  rows=[r for r in fund if r["estado"]=="ok"]
    if filtro=="Solo rechazadas": rows=[r for r in fund if r["estado"]!="ok"]
    if rows:
        df_f = pd.DataFrame(rows)
        df_f["Estado"] = df_f["estado"].apply(lambda x:"✅ PASA" if x=="ok" else ("⚠️ Sin datos" if x=="sin_datos" else "❌ Falla"))
        df_d = df_f[["ticker","nombre","mercado","pe","roe","de","motivo","Estado"]].copy()
        df_d.columns=["Ticker","Empresa","Mercado","P/E","ROE %","D/E","Detalle","Estado"]
        st.dataframe(df_d, use_container_width=True, hide_index=True)

with tab2:
    st.markdown('<div class="section-header">Señales técnicas</div>', unsafe_allow_html=True)
    if not senales:
        st.warning("Ninguna acción pasó el filtro fundamental.")
    else:
        cols = st.columns(3)
        for i,(ticker,s) in enumerate(senales.items()):
            senal     = s.get("senal","ESPERAR")
            badge_cls = "badge-buy" if senal=="COMPRA" else ("badge-sell" if senal=="VENDER" else "badge-wait")
            badge_txt = "▲ COMPRA"  if senal=="COMPRA" else ("▼ VENDER" if senal=="VENDER" else "◌ ESPERAR")
            rsi_color = "#68d391" if s["rsi"]<40 else ("#fc8181" if s["rsi"]>65 else "#f6ad55")
            cols[i%3].markdown(f"""
            <div class="metric-card" style="{'border-color:rgba(104,211,145,.5)' if senal=='COMPRA' else ''}">
              <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px">
                <span style="font-family:monospace;font-size:15px;font-weight:500">{ticker}</span>
                <span class="badge {badge_cls}">{badge_txt}</span>
              </div>
              <div style="font-family:monospace;font-size:20px;color:#63b3ed;margin-bottom:8px">${s['precio']}</div>
              <div style="font-size:12px;color:#718096;line-height:2">
                RSI: <span style="color:{rsi_color}">{s['rsi']}</span><br>
                EMA9: ${s['ema_r']} | EMA21: ${s['ema_l']}<br>
                Stop: <span style="color:#fc8181">${s['stop_loss']}</span> | TP: <span style="color:#68d391">${s['take_profit']}</span>
              </div>
            </div>""", unsafe_allow_html=True)
            if senal=="COMPRA" and not s.get("alerta_enviada"):
                try:
                    send_telegram(f"🟢 *COMPRA* {ticker} ${s['precio']} | RSI {s['rsi']} | SL ${s['stop_loss']} | TP ${s['take_profit']}")
                    s["alerta_enviada"]=True
                except: pass

with tab3:
    st.markdown('<div class="section-header">Backtesting profesional</div>', unsafe_allow_html=True)
    if not bts:
        st.info("Sin datos de backtest.")
    else:
        ticker_sel = st.selectbox("Activo", list(bts.keys()))
        m = bts[ticker_sel]
        b1,b2,b3,b4,b5,b6 = st.columns(6)
        kpi(b1,"Retorno",  f"{m['retorno']:+.1f}%",   "green" if m['retorno']>0  else "red")
        kpi(b2,"Win rate", f"{m['win_rate']:.1f}%",   "green" if m['win_rate']>50 else "amber")
        kpi(b3,"Trades",   m['total_trades'])
        kpi(b4,"Sharpe",   f"{m['sharpe']:.2f}",      "green" if m['sharpe']>1   else "amber")
        kpi(b5,"Sortino",  f"{m['sortino']:.2f}",     "green" if m['sortino']>1.5 else "amber")
        kpi(b6,"Max DD",   f"{m['max_dd']:.1f}%",     "red")
        c1,c2 = st.columns(2)
        with c1:
            st.dataframe(pd.DataFrame([
                ["Sharpe",f"{m['sharpe']:.4f}","> 1.0"],["Sortino",f"{m['sortino']:.4f}","> 1.5"],
                ["Treynor",f"{m['treynor']:.4f}","> 0"],["Calmar",f"{m['calmar']:.4f}","> 1.0"],
                ["AUC",f"{m['auc']:.4f}","> 0.55"],["Beta",f"{m['beta']:.4f}","< 1"],
                ["Alpha",f"{m['alpha_anual']:+.2f}%","> 0%"],
            ], columns=["Ratio","Valor","Ref"]), use_container_width=True, hide_index=True)
        with c2:
            st.dataframe(pd.DataFrame([
                ["Wins/Losses",f"{m['wins']}/{m['losses']}"],["Win rate",f"{m['win_rate']:.1f}%"],
                ["G. media",f"+{m['ganancia_media']:.2f}%"],["P. media",f"-{m['perdida_media']:.2f}%"],
                ["Duración",f"{m['duracion_media']:.1f}d"],["VaR 95%",f"{m['var_95']:.3f}%"],
                ["CVaR 95%",f"{m['cvar_95']:.3f}%"],["Volatilidad",f"{m['volatilidad']:.2f}%"],
            ], columns=["Métrica","Valor"]), use_container_width=True, hide_index=True)
        eq = m.get("equity_curve",[])
        if eq: st.line_chart(pd.DataFrame({"Equity ($)":eq}), height=200)
        if m.get("trades"):
            st.dataframe(pd.DataFrame(m["trades"]), use_container_width=True, hide_index=True)

with tab4:
    st.markdown('<div class="section-header">Métricas de riesgo</div>', unsafe_allow_html=True)
    if bts:
        st.dataframe(pd.DataFrame([{"Ticker":t,"Max DD":f"{m['max_dd']:.1f}%","Volatilidad":f"{m['volatilidad']:.1f}%",
            "VaR 95%":f"{m['var_95']:.3f}%","CVaR 95%":f"{m['cvar_95']:.3f}%","Beta":f"{m['beta']:.2f}","Calmar":f"{m['calmar']:.2f}"}
            for t,m in bts.items()]), use_container_width=True, hide_index=True)

with tab5:
    st.markdown('<div class="section-header">Comparación con SPY</div>', unsafe_allow_html=True)
    if bts:
        st.dataframe(pd.DataFrame([{"Ticker":t,"Estrategia":f"{m['retorno']:+.1f}%","SPY":f"{m['bm_retorno']:+.1f}%",
            "Alpha":f"{m['alpha_total']:+.1f}%","Alpha anual":f"{m['alpha_anual']:+.2f}%",
            "Sharpe":f"{m['sharpe']:.2f}","Sortino":f"{m['sortino']:.2f}","Beta":f"{m['beta']:.2f}"}
            for t,m in bts.items()]), use_container_width=True, hide_index=True)

if st.session_state.get("gen_pdf"):
    st.session_state["gen_pdf"] = False
    with st.spinner("Generando PDF..."):
        pdf_bytes = generate_pdf(results, params)
    st.download_button("⬇️ Descargar PDF", data=pdf_bytes,
        file_name=f"informe_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf", mime="application/pdf")

if auto_refresh:
    time.sleep(1)
    st.rerun()
