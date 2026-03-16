# ============================================================
#  chart_component.py v3
#  Gráfico limpio: solo señales COMPRA / VENTA consolidadas
#  Sin saturación — una señal por zona
# ============================================================

import json
import numpy as np
import pandas as pd
import ta as ta_lib


def to_ts(dt):
    try:
        return int(pd.Timestamp(dt).timestamp())
    except:
        return 0


def safe_val(s, i):
    try:
        v = float(s.iloc[i])
        return None if np.isnan(v) else round(v, 4)
    except:
        return None


def calcular_score_vela(close_v, rsi_v, ema9_v, ema21_v, macd_v, macd_s_v,
                         bb_lo_v, bb_up_v):
    """
    Mismo scoring que el dashboard — devuelve score -100 a +100.
    """
    pb, pv = 0, 0

    if rsi_v is not None:
        if rsi_v < 30:    pb += 25
        elif rsi_v < 40:  pb += 12
        elif rsi_v > 72:  pv += 25
        elif rsi_v > 65:  pv += 12

    if ema9_v is not None and ema21_v is not None:
        if ema9_v > ema21_v: pb += 15
        else:                 pv += 15

    if macd_v is not None and macd_s_v is not None:
        if macd_v > macd_s_v and macd_v > 0:   pb += 20
        elif macd_v > macd_s_v:                  pb += 10
        elif macd_v < macd_s_v and macd_v < 0:  pv += 20
        else:                                     pv += 10

    if bb_lo_v is not None and bb_up_v is not None and bb_up_v > bb_lo_v:
        if close_v <= bb_lo_v:   pb += 20
        elif close_v >= bb_up_v: pv += 20
        else:
            pos = (close_v - bb_lo_v) / (bb_up_v - bb_lo_v) * 100
            if pos < 25:  pb += 10
            elif pos > 75: pv += 10

    total = pb + pv
    return round((pb - pv) / total * 100) if total > 0 else 0


def detectar_senales_consolidadas(df):
    """
    Recorre toda la historia y marca SOLO señales fuertes:
    - COMPRA cuando score >= 55
    - VENTA cuando score <= -55
    Mínimo 10 velas entre señales para no saturar.
    """
    close  = df["Close"]
    n      = len(df)
    MIN_GAP = 10

    # Calcular todos los indicadores de una vez
    ema9_s  = ta_lib.trend.ema_indicator(close, window=9)
    ema21_s = ta_lib.trend.ema_indicator(close, window=21)
    rsi_s   = ta_lib.momentum.rsi(close, window=min(14, n-2))
    macd_i  = ta_lib.trend.MACD(close)
    macd_vs = macd_i.macd()
    macd_ss = macd_i.macd_signal()
    bb      = ta_lib.volatility.BollingerBands(close, window=min(20, n-2))
    bb_up_s = bb.bollinger_hband()
    bb_lo_s = bb.bollinger_lband()

    markers   = []
    last_buy  = -MIN_GAP
    last_sell = -MIN_GAP

    for i in range(26, n):  # Empezar en 26 para que MACD tenga datos
        try:
            cv    = float(close.iloc[i])
            score = calcular_score_vela(
                close_v  = cv,
                rsi_v    = safe_val(rsi_s,   i),
                ema9_v   = safe_val(ema9_s,  i),
                ema21_v  = safe_val(ema21_s, i),
                macd_v   = safe_val(macd_vs, i),
                macd_s_v = safe_val(macd_ss, i),
                bb_lo_v  = safe_val(bb_lo_s, i),
                bb_up_v  = safe_val(bb_up_s, i),
            )

            p = f"${round(cv, 2)}"

            if score >= 55 and (i - last_buy) >= MIN_GAP:
                last_buy = i
                markers.append({
                    "time":     to_ts(df.index[i]),
                    "position": "belowBar",
                    "color":    "#26a69a",
                    "shape":    "arrowUp",
                    "text":     f"COMPRA  {p}"
                })

            elif score <= -55 and (i - last_sell) >= MIN_GAP:
                last_sell = i
                markers.append({
                    "time":     to_ts(df.index[i]),
                    "position": "aboveBar",
                    "color":    "#ef5350",
                    "shape":    "arrowDown",
                    "text":     f"VENTA  {p}"
                })
        except:
            pass

    markers.sort(key=lambda x: x["time"])
    return markers


def render_chart_html(df, ema9_s, ema21_s, ema50_s, rsi_s,
                      bb_up_s, bb_lo_s, sr, veredicto_cls, ticker):

    # ── Velas ──────────────────────────────────────────────
    candles = []
    for idx, row in df.iterrows():
        try:
            o = float(row.get("Open",  row["Close"]))
            h = float(row.get("High",  row["Close"]))
            l = float(row.get("Low",   row["Close"]))
            c = float(row["Close"])
            if any(np.isnan(x) for x in [o, h, l, c]):
                continue
            candles.append({"time": to_ts(idx),
                            "open": round(o,2), "high": round(h,2),
                            "low":  round(l,2), "close":round(c,2)})
        except:
            pass

    # ── Volumen ────────────────────────────────────────────
    volumes = []
    if "Volume" in df.columns:
        for idx, row in df.iterrows():
            try:
                v = float(row["Volume"])
                c = float(row["Close"])
                o = float(row.get("Open", c))
                if not np.isnan(v) and v > 0:
                    volumes.append({
                        "time":  to_ts(idx), "value": int(v),
                        "color": "rgba(38,166,154,0.15)" if c >= o else "rgba(239,83,80,0.15)"
                    })
            except:
                pass

    # ── Señales consolidadas COMPRA/VENTA ─────────────────
    markers = detectar_senales_consolidadas(df)
    n_buy   = sum(1 for m in markers if m["color"] == "#26a69a")
    n_sell  = sum(1 for m in markers if m["color"] == "#ef5350")

    # ── Soportes y resistencias ────────────────────────────
    price_lines = []
    if sr:
        for nivel, toques in (sr.get("resistencias") or [])[:3]:
            price_lines.append({
                "price": float(nivel), "color": "rgba(239,83,80,0.4)",
                "lineWidth": 1, "lineStyle": 2,
                "axisLabelVisible": True, "title": f"R ${nivel}"
            })
        for nivel, toques in (sr.get("soportes") or [])[:3]:
            price_lines.append({
                "price": float(nivel), "color": "rgba(38,166,154,0.4)",
                "lineWidth": 1, "lineStyle": 2,
                "axisLabelVisible": True, "title": f"S ${nivel}"
            })

    vc = {"cf":"#48bb78","c":"#68d391","n":"#a0aec0","v":"#fc8181","vf":"#f56565"}.get(veredicto_cls,"#a0aec0")

    jc  = json.dumps(candles)
    jv  = json.dumps(volumes)
    jm  = json.dumps(markers)
    jpl = json.dumps(price_lines)

    return f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<style>
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{background:#080b10;font-family:'DM Mono',monospace;overflow:hidden}}
  #chart{{width:100%;height:460px}}
  .legend{{
    position:absolute;top:10px;left:10px;z-index:100;
    background:rgba(8,11,16,.92);border:1px solid #1e2a3a;
    border-radius:8px;padding:10px 14px;font-size:10px;
    pointer-events:none;line-height:1.9;min-width:160px
  }}
  .lt{{font-size:13px;font-weight:500;color:#e2e8f0;margin-bottom:2px}}
  .lp{{font-size:18px;font-weight:300;margin-bottom:4px}}
  .lo{{font-size:10px;color:#4a5568;margin-bottom:6px}}
  .foot{{
    display:flex;align-items:center;gap:20px;
    padding:8px 14px;background:#0a0d13;
    border-top:1px solid #111827;font-size:10px;color:#4a5568
  }}
  .fi{{display:flex;align-items:center;gap:5px}}
  .fa{{font-size:13px;line-height:1}}
</style></head><body>
<div style="position:relative">
  <div id="chart"></div>
  <div class="legend">
    <div class="lt">{ticker}</div>
    <div class="lp" id="lp" style="color:{vc}">—</div>
    <div class="lo" id="lo">hover sobre el gráfico</div>
    <div style="height:4px;border-top:1px solid #111827;margin:4px 0"></div>
    <div style="font-size:10px;color:#2d4a6b;margin-bottom:2px">SEÑALES DETECTADAS</div>
    <div style="display:flex;gap:14px">
      <div style="color:#26a69a">▲ {n_buy} compras</div>
      <div style="color:#ef5350">▼ {n_sell} ventas</div>
    </div>
  </div>
</div>
<div class="foot">
  <div class="fi"><span class="fa" style="color:#26a69a">▲</span><b style="color:#26a69a">COMPRA</b> — score ≥ 55/100</div>
  <div class="fi"><span class="fa" style="color:#ef5350">▼</span><b style="color:#ef5350">VENTA</b> &nbsp;— score ≤ -55/100</div>
  <div style="margin-left:auto;color:#2d4a6b">{len(candles)} velas · S/R en líneas punteadas</div>
</div>

<script src="https://unpkg.com/lightweight-charts@4.1.3/dist/lightweight-charts.standalone.production.js"></script>
<script>
const C={jc},V={jv},MK={jm},PL={jpl};

const chart=LightweightCharts.createChart(document.getElementById('chart'),{{
  width:document.getElementById('chart').offsetWidth||900,
  height:460,
  layout:{{background:{{type:'solid',color:'#080b10'}},textColor:'#4a5568',fontSize:11}},
  grid:{{
    vertLines:{{color:'rgba(30,42,58,.3)'}},
    horzLines:{{color:'rgba(30,42,58,.3)'}}
  }},
  crosshair:{{
    mode:LightweightCharts.CrosshairMode.Normal,
    vertLine:{{color:'#1e2a3a',labelBackgroundColor:'#111720',style:2}},
    horzLine:{{color:'#1e2a3a',labelBackgroundColor:'#111720',style:2}}
  }},
  rightPriceScale:{{borderColor:'#1e2a3a',scaleMargins:{{top:0.06,bottom:0.18}}}},
  timeScale:{{borderColor:'#1e2a3a',timeVisible:true,secondsVisible:false,barSpacing:10}},
}});

// Velas
const cs=chart.addCandlestickSeries({{
  upColor:'#26a69a',downColor:'#ef5350',
  borderUpColor:'#26a69a',borderDownColor:'#ef5350',
  wickUpColor:'rgba(38,166,154,0.7)',wickDownColor:'rgba(239,83,80,0.7)',
}});
cs.setData(C);

// Volumen
if(V.length){{
  const vs=chart.addHistogramSeries({{
    priceFormat:{{type:'volume'}},priceScaleId:'vol',
    scaleMargins:{{top:0.86,bottom:0}}
  }});
  vs.setData(V);
}}

// Señales COMPRA / VENTA
if(MK.length) cs.setMarkers(MK);

// Soportes y resistencias
PL.forEach(pl=>cs.createPriceLine(pl));

// Leyenda dinámica
chart.subscribeCrosshairMove(p=>{{
  if(!p||!p.time) return;
  const d=p.seriesData.get(cs);
  if(!d) return;
  const lp=document.getElementById('lp');
  const lo=document.getElementById('lo');
  if(lp){{
    lp.textContent='$'+d.close.toFixed(2);
    lp.style.color=d.close>=d.open?'#26a69a':'#ef5350';
  }}
  if(lo) lo.textContent='O:$'+d.open+' H:$'+d.high+' L:$'+d.low;
}});

chart.timeScale().fitContent();
window.addEventListener('resize',()=>
  chart.applyOptions({{width:document.getElementById('chart').offsetWidth}}));
</script></body></html>"""
