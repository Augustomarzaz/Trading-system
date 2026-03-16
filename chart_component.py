# ============================================================
#  chart_component.py
#  Gráfico de velas estilo TradingView con señales marcadas
#  Usa lightweight-charts (open source de TradingView)
# ============================================================

import json
import numpy as np
import pandas as pd


def to_ts(dt):
    """Convierte fecha a Unix timestamp (segundos)."""
    try:
        return int(pd.Timestamp(dt).timestamp())
    except:
        return 0


def prep_line(series):
    """Convierte una Serie de pandas a lista de {time, value}."""
    data = []
    for idx, val in series.items():
        try:
            v = float(val)
            if not np.isnan(v):
                data.append({"time": to_ts(idx), "value": round(v, 4)})
        except:
            pass
    return data


def detectar_senales_historicas(df, ema9_s, ema21_s, rsi_s, bb_up_s, bb_lo_s):
    """
    Escanea la historia completa y devuelve markers con:
    - Fecha exacta (timestamp)
    - Tipo de señal
    - Precio en esa vela
    """
    markers = []
    close   = df["Close"]
    n       = len(df)

    # ── 1. Cruces de EMA 9 / EMA 21 ──────────────────────
    if ema9_s is not None and ema21_s is not None:
        for i in range(1, n):
            try:
                e9,  e21  = float(ema9_s.iloc[i]),   float(ema21_s.iloc[i])
                e9p, e21p = float(ema9_s.iloc[i-1]), float(ema21_s.iloc[i-1])
                if any(np.isnan(x) for x in [e9, e21, e9p, e21p]):
                    continue
                p = round(float(close.iloc[i]), 2)
                if e9 > e21 and e9p <= e21p:
                    markers.append({
                        "time":     to_ts(df.index[i]),
                        "position": "belowBar",
                        "color":    "#26a69a",
                        "shape":    "arrowUp",
                        "text":     f"Cruce EMA ↑  ${p}"
                    })
                elif e9 < e21 and e9p >= e21p:
                    markers.append({
                        "time":     to_ts(df.index[i]),
                        "position": "aboveBar",
                        "color":    "#ef5350",
                        "shape":    "arrowDown",
                        "text":     f"Cruce EMA ↓  ${p}"
                    })
            except:
                pass

    # ── 2. RSI extremos ───────────────────────────────────
    if rsi_s is not None:
        in_os, in_ob = False, False
        for i in range(1, n):
            try:
                rv, rvp = float(rsi_s.iloc[i]), float(rsi_s.iloc[i-1])
                if np.isnan(rv) or np.isnan(rvp):
                    continue
                p = round(float(close.iloc[i]), 2)

                if rv < 40 and rvp >= 40 and not in_os:
                    in_os = True
                    markers.append({
                        "time":     to_ts(df.index[i]),
                        "position": "belowBar",
                        "color":    "#00bcd4",
                        "shape":    "circle",
                        "text":     f"RSI {round(rv,1)}  ${p}"
                    })
                elif rv >= 40:
                    in_os = False

                if rv > 65 and rvp <= 65 and not in_ob:
                    in_ob = True
                    markers.append({
                        "time":     to_ts(df.index[i]),
                        "position": "aboveBar",
                        "color":    "#ff9800",
                        "shape":    "circle",
                        "text":     f"RSI {round(rv,1)}  ${p}"
                    })
                elif rv <= 65:
                    in_ob = False
            except:
                pass

    # ── 3. Bollinger Band toques ──────────────────────────
    if bb_up_s is not None and bb_lo_s is not None:
        for i in range(n):
            try:
                bb_lo_v = float(bb_lo_s.iloc[i])
                bb_up_v = float(bb_up_s.iloc[i])
                if np.isnan(bb_lo_v) or np.isnan(bb_up_v):
                    continue
                low_v  = float(df["Low"].iloc[i])  if "Low"  in df.columns else float(close.iloc[i])
                high_v = float(df["High"].iloc[i]) if "High" in df.columns else float(close.iloc[i])
                p      = round(float(close.iloc[i]), 2)

                if low_v <= bb_lo_v * 1.003:
                    markers.append({
                        "time":     to_ts(df.index[i]),
                        "position": "belowBar",
                        "color":    "#7c4dff",
                        "shape":    "arrowUp",
                        "text":     f"BB Inf  ${p}"
                    })
                elif high_v >= bb_up_v * 0.997:
                    markers.append({
                        "time":     to_ts(df.index[i]),
                        "position": "aboveBar",
                        "color":    "#ff6d00",
                        "shape":    "arrowDown",
                        "text":     f"BB Sup  ${p}"
                    })
            except:
                pass

    markers.sort(key=lambda x: x["time"])
    return markers


def render_chart_html(df, ema9_s, ema21_s, ema50_s, rsi_s,
                      bb_up_s, bb_lo_s, sr, veredicto_cls, ticker):
    """
    Genera el HTML completo del gráfico de velas con señales.
    Se embebe en Streamlit con st.components.v1.html()
    """

    # ── Velas ─────────────────────────────────────────────
    candles = []
    for idx, row in df.iterrows():
        try:
            candles.append({
                "time":  to_ts(idx),
                "open":  round(float(row["Open"]),  2),
                "high":  round(float(row["High"]),  2),
                "low":   round(float(row["Low"]),   2),
                "close": round(float(row["Close"]), 2),
            })
        except:
            pass

    # ── Volumen ───────────────────────────────────────────
    volumes = []
    if "Volume" in df.columns:
        for idx, row in df.iterrows():
            try:
                c = float(row["Close"])
                o = float(row["Open"])
                volumes.append({
                    "time":  to_ts(idx),
                    "value": int(float(row["Volume"])),
                    "color": "rgba(38,166,154,0.25)" if c >= o else "rgba(239,83,80,0.25)"
                })
            except:
                pass

    # ── Series de indicadores ─────────────────────────────
    ema9_data  = prep_line(ema9_s)  if ema9_s  is not None else []
    ema21_data = prep_line(ema21_s) if ema21_s is not None else []
    ema50_data = prep_line(ema50_s) if ema50_s is not None else []
    bb_up_data = prep_line(bb_up_s) if bb_up_s is not None else []
    bb_lo_data = prep_line(bb_lo_s) if bb_lo_s is not None else []

    # ── Señales históricas ────────────────────────────────
    markers = detectar_senales_historicas(
        df, ema9_s, ema21_s, rsi_s, bb_up_s, bb_lo_s
    )

    # ── Líneas de soporte/resistencia ─────────────────────
    price_lines = []
    if sr:
        for nivel, toques in sr.get("resistencias", [])[:4]:
            price_lines.append({
                "price":             float(nivel),
                "color":             "rgba(239,83,80,0.55)",
                "lineWidth":         1,
                "lineStyle":         2,
                "axisLabelVisible":  True,
                "title":             f"R {toques}t"
            })
        for nivel, toques in sr.get("soportes", [])[:4]:
            price_lines.append({
                "price":            float(nivel),
                "color":            "rgba(38,166,154,0.55)",
                "lineWidth":        1,
                "lineStyle":        2,
                "axisLabelVisible": True,
                "title":            f"S {toques}t"
            })

    # ── Color del veredicto ───────────────────────────────
    verdict_color = {
        "cf": "#48bb78", "c": "#68d391",
        "n":  "#a0aec0",
        "v":  "#fc8181", "vf": "#f56565"
    }.get(veredicto_cls, "#a0aec0")

    # ── Serializar ────────────────────────────────────────
    jc   = json.dumps(candles)
    jv   = json.dumps(volumes)
    je9  = json.dumps(ema9_data)
    je21 = json.dumps(ema21_data)
    je50 = json.dumps(ema50_data)
    jbu  = json.dumps(bb_up_data)
    jbl  = json.dumps(bb_lo_data)
    jm   = json.dumps(markers)
    jpl  = json.dumps(price_lines)

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ background: #080b10; font-family: 'DM Mono', monospace; overflow: hidden; }}
  #chart-container {{ width: 100%; position: relative; }}
  #chart {{ width: 100%; height: 480px; }}

  .legend {{
    position: absolute; top: 10px; left: 10px; z-index: 100;
    background: rgba(8,11,16,0.92);
    border: 1px solid #1e2a3a;
    border-radius: 6px; padding: 8px 12px;
    font-size: 11px; color: #718096;
    pointer-events: none; line-height: 1.8;
    min-width: 200px;
  }}
  .legend b {{ color: #e2e8f0; font-weight: 500; }}
  .l-row {{ display: flex; align-items: center; gap: 8px; }}
  .l-dot {{ height: 2px; border-radius: 1px; flex-shrink: 0; }}

  .signal-bar {{
    display: flex; gap: 20px; flex-wrap: wrap;
    padding: 8px 12px;
    background: #0a0d13;
    border-top: 1px solid #111827;
    font-size: 10px; color: #4a5568;
    letter-spacing: .05em;
  }}
  .si {{ display: flex; align-items: center; gap: 5px; }}
</style>
</head>
<body>

<div id="chart-container">
  <div id="chart"></div>
  <div class="legend" id="legend">
    <div class="l-row" style="margin-bottom:4px">
      <b id="ticker-lbl">{ticker}</b>
      <span id="price-lbl" style="color:{verdict_color}; font-size:13px"></span>
    </div>
    <div id="ohlc-lbl" style="color:#718096;font-size:10px"></div>
    <div style="height:6px"></div>
    <div class="l-row"><div class="l-dot" style="background:#2196F3;width:18px"></div><span style="color:#2196F3">EMA 9</span></div>
    <div class="l-row"><div class="l-dot" style="background:#FF9800;width:18px"></div><span style="color:#FF9800">EMA 21</span></div>
    <div class="l-row"><div class="l-dot" style="background:#9C27B0;width:18px"></div><span style="color:#9C27B0">EMA 50</span></div>
    <div class="l-row"><div class="l-dot" style="background:rgba(100,100,200,0.6);width:18px;border-top:1px dashed rgba(100,100,200,0.6)"></div><span style="color:#aaa">Bollinger</span></div>
  </div>
</div>

<div class="signal-bar">
  <div class="si"><span style="color:#26a69a;font-size:13px">▲</span> Cruce EMA alcista</div>
  <div class="si"><span style="color:#ef5350;font-size:13px">▼</span> Cruce EMA bajista</div>
  <div class="si"><span style="color:#00bcd4">●</span> RSI sobreventa (&lt;40)</div>
  <div class="si"><span style="color:#ff9800">●</span> RSI sobrecompra (&gt;65)</div>
  <div class="si"><span style="color:#7c4dff;font-size:13px">▲</span> Toca BB inferior</div>
  <div class="si"><span style="color:#ff6d00;font-size:13px">▼</span> Toca BB superior</div>
  <div class="si" style="margin-left:auto;color:#2d4a6b">{len(markers)} señales detectadas</div>
</div>

<script src="https://unpkg.com/lightweight-charts@4.1.3/dist/lightweight-charts.standalone.production.js"></script>
<script>
const candles   = {jc};
const volumes   = {jv};
const ema9d     = {je9};
const ema21d    = {je21};
const ema50d    = {je50};
const bbUpd     = {jbu};
const bbLod     = {jbl};
const markers   = {jm};
const pLines    = {jpl};

const chart = LightweightCharts.createChart(document.getElementById('chart'), {{
  width:  document.getElementById('chart').offsetWidth || 900,
  height: 480,
  layout: {{
    background: {{ type: 'solid', color: '#080b10' }},
    textColor:  '#718096',
    fontSize:   11,
  }},
  grid: {{
    vertLines: {{ color: 'rgba(30,42,58,0.6)' }},
    horzLines: {{ color: 'rgba(30,42,58,0.6)' }},
  }},
  crosshair: {{
    mode:     LightweightCharts.CrosshairMode.Normal,
    vertLine: {{ color: '#1e2a3a', labelBackgroundColor: '#111720', style: 2 }},
    horzLine: {{ color: '#1e2a3a', labelBackgroundColor: '#111720', style: 2 }},
  }},
  rightPriceScale: {{ borderColor: '#1e2a3a' }},
  timeScale: {{
    borderColor:    '#1e2a3a',
    timeVisible:    true,
    secondsVisible: false,
    barSpacing:     8,
  }},
}});

// ── Velas ──────────────────────────────────────────────
const candleSeries = chart.addCandlestickSeries({{
  upColor:         '#26a69a',
  downColor:       '#ef5350',
  borderUpColor:   '#26a69a',
  borderDownColor: '#ef5350',
  wickUpColor:     '#26a69a',
  wickDownColor:   '#ef5350',
}});
candleSeries.setData(candles);

// ── Volumen ────────────────────────────────────────────
if (volumes.length > 0) {{
  const volS = chart.addHistogramSeries({{
    priceFormat:   {{ type: 'volume' }},
    priceScaleId:  'vol',
    scaleMargins:  {{ top: 0.82, bottom: 0 }},
  }});
  volS.setData(volumes);
  chart.priceScale('vol').applyOptions({{ scaleMargins: {{ top: 0.82, bottom: 0 }} }});
}}

// ── EMAs ───────────────────────────────────────────────
if (ema9d.length)  {{ chart.addLineSeries({{ color:'#2196F3', lineWidth:1, priceLineVisible:false }}).setData(ema9d);  }}
if (ema21d.length) {{ chart.addLineSeries({{ color:'#FF9800', lineWidth:1, priceLineVisible:false }}).setData(ema21d); }}
if (ema50d.length) {{ chart.addLineSeries({{ color:'#9C27B0', lineWidth:1, priceLineVisible:false }}).setData(ema50d); }}

// ── Bollinger ──────────────────────────────────────────
if (bbUpd.length) {{
  chart.addLineSeries({{ color:'rgba(120,120,220,0.35)', lineWidth:1, lineStyle:2, priceLineVisible:false }}).setData(bbUpd);
}}
if (bbLod.length) {{
  chart.addLineSeries({{ color:'rgba(120,120,220,0.35)', lineWidth:1, lineStyle:2, priceLineVisible:false }}).setData(bbLod);
}}

// ── Marcadores de señales ──────────────────────────────
if (markers.length > 0) {{
  candleSeries.setMarkers(markers);
}}

// ── Soportes y resistencias ────────────────────────────
pLines.forEach(pl => candleSeries.createPriceLine(pl));

// ── Leyenda dinámica al pasar el mouse ─────────────────
chart.subscribeCrosshairMove(param => {{
  if (!param.time) return;
  const d = param.seriesData.get(candleSeries);
  if (!d) return;
  const isUp = d.close >= d.open;
  document.getElementById('price-lbl').textContent = '$' + d.close;
  document.getElementById('ohlc-lbl').textContent =
    `O: ${{d.open}}  H: ${{d.high}}  L: ${{d.low}}  C: ${{d.close}}`;
  document.getElementById('price-lbl').style.color = isUp ? '#26a69a' : '#ef5350';
}});

// ── Fit al contenido ───────────────────────────────────
chart.timeScale().fitContent();

// ── Responsive ────────────────────────────────────────
window.addEventListener('resize', () => {{
  chart.applyOptions({{ width: document.getElementById('chart').offsetWidth }});
}});
</script>
</body>
</html>"""

    return html
