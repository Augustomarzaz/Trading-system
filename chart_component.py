# ============================================================
#  chart_component.py v2 — Gráfico limpio con señales clave
# ============================================================

import json
import numpy as np
import pandas as pd


def to_ts(dt):
    try:
        return int(pd.Timestamp(dt).timestamp())
    except:
        return 0


def prep_line(series):
    data = []
    for idx, val in series.items():
        try:
            v = float(val)
            if not np.isnan(v):
                data.append({"time": to_ts(idx), "value": round(v, 4)})
        except:
            pass
    return data


def detectar_senales_limpias(df, ema9_s, ema21_s, rsi_s, bb_up_s, bb_lo_s):
    """
    Solo marca señales REALMENTE relevantes, sin saturar.
    - Cruces EMA: mínimo 8 velas entre señales
    - RSI: solo valores extremos (<30 o >72), sin repetir en la misma zona
    - Bollinger: solo cuando el CIERRE está fuera de la banda
    """
    markers  = []
    close    = df["Close"]
    n        = len(df)
    MIN_DIST = 8

    # EMA Cruces
    last_ema = -MIN_DIST
    if ema9_s is not None and ema21_s is not None:
        for i in range(1, n):
            try:
                e9, e21   = float(ema9_s.iloc[i]),   float(ema21_s.iloc[i])
                e9p, e21p = float(ema9_s.iloc[i-1]), float(ema21_s.iloc[i-1])
                if any(np.isnan(x) for x in [e9, e21, e9p, e21p]):
                    continue
                if (i - last_ema) < MIN_DIST:
                    continue
                p = round(float(close.iloc[i]), 2)
                if e9 > e21 and e9p <= e21p:
                    markers.append({"time": to_ts(df.index[i]), "position": "belowBar",
                                    "color": "#26a69a", "shape": "arrowUp",   "text": f"EMA ↑ ${p}"})
                    last_ema = i
                elif e9 < e21 and e9p >= e21p:
                    markers.append({"time": to_ts(df.index[i]), "position": "aboveBar",
                                    "color": "#ef5350", "shape": "arrowDown", "text": f"EMA ↓ ${p}"})
                    last_ema = i
            except:
                pass

    # RSI extremos
    in_os, in_ob = False, False
    if rsi_s is not None:
        for i in range(1, n):
            try:
                rv = float(rsi_s.iloc[i])
                if np.isnan(rv):
                    continue
                p = round(float(close.iloc[i]), 2)
                if rv < 30 and not in_os:
                    in_os = True
                    markers.append({"time": to_ts(df.index[i]), "position": "belowBar",
                                    "color": "#00bcd4", "shape": "circle", "text": f"RSI {round(rv)} ${p}"})
                elif rv >= 35:
                    in_os = False
                if rv > 72 and not in_ob:
                    in_ob = True
                    markers.append({"time": to_ts(df.index[i]), "position": "aboveBar",
                                    "color": "#ff9800", "shape": "circle", "text": f"RSI {round(rv)} ${p}"})
                elif rv <= 68:
                    in_ob = False
            except:
                pass

    # Bollinger: solo cierre fuera de banda
    last_bb_lo = -MIN_DIST
    last_bb_up = -MIN_DIST
    if bb_up_s is not None and bb_lo_s is not None:
        for i in range(n):
            try:
                blo = float(bb_lo_s.iloc[i])
                bup = float(bb_up_s.iloc[i])
                if np.isnan(blo) or np.isnan(bup):
                    continue
                cv = float(close.iloc[i])
                p  = round(cv, 2)
                if cv < blo and (i - last_bb_lo) >= MIN_DIST:
                    last_bb_lo = i
                    markers.append({"time": to_ts(df.index[i]), "position": "belowBar",
                                    "color": "#7c4dff", "shape": "arrowUp",   "text": f"BB↓ ${p}"})
                elif cv > bup and (i - last_bb_up) >= MIN_DIST:
                    last_bb_up = i
                    markers.append({"time": to_ts(df.index[i]), "position": "aboveBar",
                                    "color": "#ff6d00", "shape": "arrowDown", "text": f"BB↑ ${p}"})
            except:
                pass

    markers.sort(key=lambda x: x["time"])
    return markers


def render_chart_html(df, ema9_s, ema21_s, ema50_s, rsi_s,
                      bb_up_s, bb_lo_s, sr, veredicto_cls, ticker):

    # Velas
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

    # Volumen
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
                        "color": "rgba(38,166,154,0.18)" if c >= o else "rgba(239,83,80,0.18)"
                    })
            except:
                pass

    ema9_data  = prep_line(ema9_s)  if ema9_s  is not None else []
    ema21_data = prep_line(ema21_s) if ema21_s is not None else []
    ema50_data = prep_line(ema50_s) if ema50_s is not None else []
    bb_up_data = prep_line(bb_up_s) if bb_up_s is not None else []
    bb_lo_data = prep_line(bb_lo_s) if bb_lo_s is not None else []

    markers = detectar_senales_limpias(df, ema9_s, ema21_s, rsi_s, bb_up_s, bb_lo_s)

    price_lines = []
    if sr:
        for nivel, toques in (sr.get("resistencias") or [])[:3]:
            price_lines.append({"price": float(nivel), "color": "rgba(239,83,80,0.45)",
                                "lineWidth": 1, "lineStyle": 1,
                                "axisLabelVisible": True, "title": f"R ${nivel}"})
        for nivel, toques in (sr.get("soportes") or [])[:3]:
            price_lines.append({"price": float(nivel), "color": "rgba(38,166,154,0.45)",
                                "lineWidth": 1, "lineStyle": 1,
                                "axisLabelVisible": True, "title": f"S ${nivel}"})

    vc = {"cf":"#48bb78","c":"#68d391","n":"#a0aec0","v":"#fc8181","vf":"#f56565"}.get(veredicto_cls,"#a0aec0")
    n_m = len(markers)

    jc  = json.dumps(candles);  jv  = json.dumps(volumes)
    je9 = json.dumps(ema9_data); je21= json.dumps(ema21_data)
    je50= json.dumps(ema50_data);jbu = json.dumps(bb_up_data)
    jbl = json.dumps(bb_lo_data);jm  = json.dumps(markers)
    jpl = json.dumps(price_lines)

    return f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<style>
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{background:#080b10;font-family:'DM Mono',monospace;overflow:hidden}}
  #chart{{width:100%;height:460px}}
  .legend{{position:absolute;top:10px;left:10px;z-index:100;
    background:rgba(8,11,16,.9);border:1px solid #1e2a3a;border-radius:8px;
    padding:10px 14px;font-size:10px;pointer-events:none;line-height:1.9;min-width:170px}}
  .lt{{font-size:13px;font-weight:500;color:#e2e8f0;margin-bottom:2px}}
  .lp{{font-size:17px;font-weight:300;margin-bottom:4px}}
  .lo{{font-size:10px;color:#4a5568;margin-bottom:6px}}
  .lr{{display:flex;align-items:center;gap:7px;color:#718096}}
  .ll{{height:2px;width:14px;border-radius:1px;flex-shrink:0}}
  .ld{{width:14px;border-top:1px dashed;flex-shrink:0}}
  .foot{{display:flex;align-items:center;gap:16px;flex-wrap:wrap;
    padding:7px 12px;background:#0a0d13;border-top:1px solid #111827;font-size:10px;color:#4a5568}}
  .fi{{display:flex;align-items:center;gap:4px}}
</style></head><body>
<div style="position:relative">
  <div id="chart"></div>
  <div class="legend">
    <div class="lt">{ticker}</div>
    <div class="lp" id="lp" style="color:{vc}">—</div>
    <div class="lo" id="lo">hover sobre el gráfico</div>
    <div style="height:4px;border-top:1px solid #111827;margin:4px 0"></div>
    <div class="lr"><div class="ll" style="background:#2196F3"></div><span style="color:#5b9bd5">EMA 9</span></div>
    <div class="lr"><div class="ll" style="background:#FF9800"></div><span style="color:#c87d3a">EMA 21</span></div>
    <div class="lr"><div class="ll" style="background:#9C27B0"></div><span style="color:#9b6ab5">EMA 50</span></div>
    <div class="lr"><div class="ld" style="border-color:rgba(140,140,220,.5)"></div><span style="color:#555">Bollinger</span></div>
  </div>
</div>
<div class="foot">
  <div class="fi"><span style="color:#26a69a;font-size:12px">▲</span>EMA alcista</div>
  <div class="fi"><span style="color:#ef5350;font-size:12px">▼</span>EMA bajista</div>
  <div class="fi"><span style="color:#00bcd4;font-size:9px">●</span>RSI&lt;30</div>
  <div class="fi"><span style="color:#ff9800;font-size:9px">●</span>RSI&gt;72</div>
  <div class="fi"><span style="color:#7c4dff;font-size:12px">▲</span>BB inferior</div>
  <div class="fi"><span style="color:#ff6d00;font-size:12px">▼</span>BB superior</div>
  <div style="margin-left:auto;color:#2d4a6b">{n_m} señales · {len(candles)} velas</div>
</div>
<script src="https://unpkg.com/lightweight-charts@4.1.3/dist/lightweight-charts.standalone.production.js"></script>
<script>
const C={jc},V={jv},E9={je9},E21={je21},E50={je50},BU={jbu},BL={jbl},MK={jm},PL={jpl};
const chart=LightweightCharts.createChart(document.getElementById('chart'),{{
  width:document.getElementById('chart').offsetWidth||900,height:460,
  layout:{{background:{{type:'solid',color:'#080b10'}},textColor:'#4a5568',fontSize:11}},
  grid:{{vertLines:{{color:'rgba(30,42,58,.35)'}},horzLines:{{color:'rgba(30,42,58,.35)'}}}},
  crosshair:{{mode:LightweightCharts.CrosshairMode.Normal,
    vertLine:{{color:'#1e2a3a',labelBackgroundColor:'#111720',style:2}},
    horzLine:{{color:'#1e2a3a',labelBackgroundColor:'#111720',style:2}}}},
  rightPriceScale:{{borderColor:'#1e2a3a',scaleMargins:{{top:0.06,bottom:0.18}}}},
  timeScale:{{borderColor:'#1e2a3a',timeVisible:true,secondsVisible:false,barSpacing:8}},
}});
const cs=chart.addCandlestickSeries({{
  upColor:'#26a69a',downColor:'#ef5350',
  borderUpColor:'#26a69a',borderDownColor:'#ef5350',
  wickUpColor:'#26a69a',wickDownColor:'#ef5350',
}});
cs.setData(C);
if(V.length){{
  const vs=chart.addHistogramSeries({{priceFormat:{{type:'volume'}},priceScaleId:'vol',scaleMargins:{{top:0.86,bottom:0}}}});
  vs.setData(V);
}}
if(E9.length)  chart.addLineSeries({{color:'#2196F3',lineWidth:1,priceLineVisible:false,lastValueVisible:false}}).setData(E9);
if(E21.length) chart.addLineSeries({{color:'#FF9800',lineWidth:1,priceLineVisible:false,lastValueVisible:false}}).setData(E21);
if(E50.length) chart.addLineSeries({{color:'#9C27B0',lineWidth:1,priceLineVisible:false,lastValueVisible:false}}).setData(E50);
if(BU.length)  chart.addLineSeries({{color:'rgba(140,140,220,.28)',lineWidth:1,lineStyle:2,priceLineVisible:false,lastValueVisible:false}}).setData(BU);
if(BL.length)  chart.addLineSeries({{color:'rgba(140,140,220,.28)',lineWidth:1,lineStyle:2,priceLineVisible:false,lastValueVisible:false}}).setData(BL);
if(MK.length)  cs.setMarkers(MK);
PL.forEach(pl=>cs.createPriceLine(pl));
chart.subscribeCrosshairMove(p=>{{
  if(!p||!p.time) return;
  const d=p.seriesData.get(cs);
  if(!d) return;
  const lp=document.getElementById('lp'),lo=document.getElementById('lo');
  if(lp){{lp.textContent='$'+d.close;lp.style.color=d.close>=d.open?'#26a69a':'#ef5350';}}
  if(lo) lo.textContent='O:$'+d.open+' H:$'+d.high+' L:$'+d.low+' C:$'+d.close;
}});
chart.timeScale().fitContent();
window.addEventListener('resize',()=>chart.applyOptions({{width:document.getElementById('chart').offsetWidth}}));
</script></body></html>"""
