# ============================================================
#  patterns.py — Detección de patrones técnicos históricos
# ============================================================

import numpy as np
import pandas as pd
from scipy.signal import argrelextrema


def encontrar_pivotes(series, orden=5):
    arr = series.values
    max_idx = argrelextrema(arr, np.greater, order=orden)[0]
    min_idx = argrelextrema(arr, np.less,    order=orden)[0]
    return max_idx, min_idx

def pct_diff(a, b):
    return abs(a - b) / ((a + b) / 2) * 100

def pendiente_linea(precios):
    x = np.arange(len(precios))
    return np.polyfit(x, precios, 1)[0]


# ── 1. DOBLE TECHO / DOBLE PISO ──────────────────────────

def detectar_doble_techo_piso(df, tolerancia=2.0):
    resultados = []
    close = df["Close"]
    max_idx, min_idx = encontrar_pivotes(close, orden=5)

    for i in range(len(max_idx) - 1):
        idx1, idx2 = max_idx[i], max_idx[i + 1]
        p1, p2 = float(close.iloc[idx1]), float(close.iloc[idx2])
        mins_entre = [m for m in min_idx if idx1 < m < idx2]
        if not mins_entre or pct_diff(p1, p2) > tolerancia:
            continue
        cuello  = float(close.iloc[mins_entre[-1]])
        objetivo = round(cuello - (max(p1, p2) - cuello), 2)
        resultados.append({
            "patron": "Doble Techo", "tipo": "BAJISTA", "señal": "VENTA",
            "fecha": str(df.index[idx2])[:10],
            "precio_patron": round((p1 + p2) / 2, 2),
            "nivel_cuello": round(cuello, 2), "objetivo": objetivo,
            "descripcion": f"Dos máximos similares ${p1:.2f} / ${p2:.2f}. Cuello ${cuello:.2f}. Objetivo bajista ${objetivo}",
            "confianza": "Alta" if pct_diff(p1, p2) < 1 else "Media",
        })

    for i in range(len(min_idx) - 1):
        idx1, idx2 = min_idx[i], min_idx[i + 1]
        p1, p2 = float(close.iloc[idx1]), float(close.iloc[idx2])
        maxs_entre = [m for m in max_idx if idx1 < m < idx2]
        if not maxs_entre or pct_diff(p1, p2) > tolerancia:
            continue
        cuello  = float(close.iloc[maxs_entre[-1]])
        objetivo = round(cuello + (cuello - min(p1, p2)), 2)
        resultados.append({
            "patron": "Doble Piso", "tipo": "ALCISTA", "señal": "COMPRA",
            "fecha": str(df.index[idx2])[:10],
            "precio_patron": round((p1 + p2) / 2, 2),
            "nivel_cuello": round(cuello, 2), "objetivo": objetivo,
            "descripcion": f"Dos mínimos similares ${p1:.2f} / ${p2:.2f}. Cuello ${cuello:.2f}. Objetivo alcista ${objetivo}",
            "confianza": "Alta" if pct_diff(p1, p2) < 1 else "Media",
        })

    return resultados


# ── 2. HCH ────────────────────────────────────────────────

def detectar_hch(df, tolerancia=3.0):
    resultados = []
    close = df["Close"]
    max_idx, min_idx = encontrar_pivotes(close, orden=5)

    for i in range(len(max_idx) - 2):
        h1_i, cab_i, h2_i = max_idx[i], max_idx[i+1], max_idx[i+2]
        h1, cab, h2 = float(close.iloc[h1_i]), float(close.iloc[cab_i]), float(close.iloc[h2_i])
        if cab <= h1 or cab <= h2 or pct_diff(h1, h2) > tolerancia:
            continue
        mins_izq = [m for m in min_idx if h1_i < m < cab_i]
        mins_der = [m for m in min_idx if cab_i < m < h2_i]
        if not mins_izq or not mins_der:
            continue
        cuello  = (float(close.iloc[mins_izq[-1]]) + float(close.iloc[mins_der[0]])) / 2
        objetivo = round(cuello - (cab - cuello), 2)
        resultados.append({
            "patron": "HCH (Hombro-Cabeza-Hombro)", "tipo": "BAJISTA", "señal": "VENTA",
            "fecha": str(df.index[h2_i])[:10],
            "precio_patron": round(cab, 2), "nivel_cuello": round(cuello, 2), "objetivo": objetivo,
            "descripcion": f"H1=${h1:.2f} | Cab=${cab:.2f} | H2=${h2:.2f}. Cuello ${cuello:.2f}. Objetivo ${objetivo}",
            "confianza": "Alta" if pct_diff(h1, h2) < 1.5 else "Media",
        })

    for i in range(len(min_idx) - 2):
        h1_i, cab_i, h2_i = min_idx[i], min_idx[i+1], min_idx[i+2]
        h1, cab, h2 = float(close.iloc[h1_i]), float(close.iloc[cab_i]), float(close.iloc[h2_i])
        if cab >= h1 or cab >= h2 or pct_diff(h1, h2) > tolerancia:
            continue
        maxs_izq = [m for m in max_idx if h1_i < m < cab_i]
        maxs_der = [m for m in max_idx if cab_i < m < h2_i]
        if not maxs_izq or not maxs_der:
            continue
        cuello  = (float(close.iloc[maxs_izq[-1]]) + float(close.iloc[maxs_der[0]])) / 2
        objetivo = round(cuello + (cuello - cab), 2)
        resultados.append({
            "patron": "HCH Invertido", "tipo": "ALCISTA", "señal": "COMPRA",
            "fecha": str(df.index[h2_i])[:10],
            "precio_patron": round(cab, 2), "nivel_cuello": round(cuello, 2), "objetivo": objetivo,
            "descripcion": f"H1=${h1:.2f} | Cab=${cab:.2f} | H2=${h2:.2f}. Cuello ${cuello:.2f}. Objetivo ${objetivo}",
            "confianza": "Alta" if pct_diff(h1, h2) < 1.5 else "Media",
        })

    return resultados


# ── 3. TRIÁNGULOS ─────────────────────────────────────────

def detectar_triangulos(df):
    resultados = []
    close = df["Close"]
    max_idx, min_idx = encontrar_pivotes(close, orden=4)
    if len(max_idx) < 3 or len(min_idx) < 3:
        return resultados

    max_p = [float(close.iloc[i]) for i in max_idx[-4:]]
    min_p = [float(close.iloc[i]) for i in min_idx[-4:]]
    pend_max = pendiente_linea(max_p)
    pend_min = pendiente_linea(min_p)
    precio   = float(close.iloc[-1])
    res      = round(np.mean(max_p), 2)
    sop      = round(np.mean(min_p), 2)
    amp      = round(res - sop, 2)
    tol      = np.mean(max_p) * 0.001

    if pend_min > tol and abs(pend_max) < tol:
        tipo, señal, bias = "Triángulo Ascendente",  "COMPRA",  "ALCISTA"
        objetivo = round(res + amp, 2)
        desc = f"Mínimos crecientes, resistencia plana en ${res}. Ruptura alcista esperada. Objetivo ${objetivo}"
    elif pend_max < -tol and abs(pend_min) < tol:
        tipo, señal, bias = "Triángulo Descendente", "VENTA",   "BAJISTA"
        objetivo = round(sop - amp, 2)
        desc = f"Máximos decrecientes, soporte plano en ${sop}. Ruptura bajista esperada. Objetivo ${objetivo}"
    elif pend_max < -tol and pend_min > tol:
        tipo, señal, bias = "Triángulo Simétrico",   "ESPERAR", "NEUTRAL"
        objetivo = round(res, 2)
        desc = f"Convergencia entre ${sop} y ${res}. Esperar ruptura para confirmar dirección."
    else:
        return resultados

    resultados.append({
        "patron": tipo, "tipo": bias, "señal": señal,
        "fecha": str(df.index[-1])[:10],
        "precio_patron": precio, "nivel_cuello": sop, "objetivo": objetivo,
        "descripcion": desc, "confianza": "Media",
    })
    return resultados


# ── 4. SOPORTES Y RESISTENCIAS ────────────────────────────

def detectar_soportes_resistencias(df, n_niveles=5, tolerancia=1.5):
    close  = df["Close"]
    high   = df["High"] if "High" in df.columns else close
    low    = df["Low"]  if "Low"  in df.columns else close
    max_idx, min_idx = encontrar_pivotes(close, orden=3)

    niveles_r = [float(high.iloc[i])  for i in max_idx]
    niveles_s = [float(low.iloc[i])   for i in min_idx]
    precio    = float(close.iloc[-1])

    def agrupar(niveles, tol):
        if not niveles:
            return []
        s = sorted(niveles)
        grupos = [[s[0]]]
        for n in s[1:]:
            if pct_diff(n, grupos[-1][-1]) <= tol:
                grupos[-1].append(n)
            else:
                grupos.append([n])
        return sorted([(round(np.mean(g), 2), len(g)) for g in grupos], key=lambda x: -x[1])[:n_niveles]

    resistencias = agrupar(niveles_r, tolerancia)
    soportes     = agrupar(niveles_s, tolerancia)

    res_c = min(resistencias, key=lambda x: abs(x[0] - precio), default=(None, 0))
    sop_c = min(soportes,     key=lambda x: abs(x[0] - precio), default=(None, 0))

    señal = "NEUTRAL"
    desc  = f"Precio actual: ${precio:.2f}"
    if res_c[0] and sop_c[0]:
        dist_s = (precio - sop_c[0]) / precio * 100
        dist_r = (res_c[0] - precio) / precio * 100
        if dist_s < 1.5:
            señal = "COMPRA"
            desc += f" — Apoyado en soporte ${sop_c[0]} ({sop_c[1]} toques)"
        elif dist_r < 1.5:
            señal = "VENTA"
            desc += f" — Cerca de resistencia ${res_c[0]} ({res_c[1]} toques)"
        else:
            desc += f" | Soporte: ${sop_c[0]} | Resistencia: ${res_c[0]}"

    return {
        "resistencias": resistencias, "soportes": soportes,
        "señal": señal, "descripcion": desc,
        "res_cercana": res_c, "sop_cercana": sop_c,
        "precio_actual": round(precio, 2),
    }


# ── 5. BANDERAS ───────────────────────────────────────────

def detectar_banderas(df, min_impulso=5.0):
    resultados = []
    close = df["Close"]
    if len(close) < 30:
        return resultados

    seg     = close.iloc[-40:]
    impulso = (float(seg.iloc[9]) - float(seg.iloc[0])) / float(seg.iloc[0]) * 100
    if abs(impulso) < min_impulso:
        return resultados

    consol      = seg.iloc[-15:]
    rango_c     = (float(consol.max()) - float(consol.min())) / float(consol.mean()) * 100
    precio      = float(close.iloc[-1])
    es_alcista  = impulso > 0

    if rango_c < 5.0:
        tipo    = "Bandera Alcista" if es_alcista else "Bandera Bajista"
        señal   = "COMPRA"         if es_alcista else "VENTA"
        bias    = "ALCISTA"        if es_alcista else "BAJISTA"
        objetivo = round(precio * (1 + abs(impulso) / 100), 2) if es_alcista \
                   else round(precio * (1 - abs(impulso) / 100), 2)
        resultados.append({
            "patron": tipo, "tipo": bias, "señal": señal,
            "fecha": str(df.index[-1])[:10],
            "precio_patron": round(precio, 2),
            "nivel_cuello": round(float(consol.min()), 2),
            "objetivo": objetivo,
            "descripcion": f"Impulso {impulso:+.1f}% seguido de consolidación ({rango_c:.1f}% rango). Objetivo ${objetivo}",
            "confianza": "Media" if abs(impulso) > 8 else "Baja",
        })
    return resultados


# ── 6. CRUCES DE MEDIAS ───────────────────────────────────

def detectar_cruces_medias(df):
    resultados = []
    close = df["Close"]
    n     = len(close)

    for ma_r, ma_l, plazo in [(9, 21, "Corto"), (20, 50, "Mediano"), (50, 200, "Largo")]:
        if n < ma_l + 2:
            continue
        sma_r = close.rolling(ma_r).mean()
        sma_l = close.rolling(ma_l).mean()
        if sma_r.isna().iloc[-1] or sma_l.isna().iloc[-1]:
            continue

        r_hoy,  l_hoy  = float(sma_r.iloc[-1]), float(sma_l.iloc[-1])
        r_ayer, l_ayer = float(sma_r.iloc[-2]), float(sma_l.iloc[-2])
        precio = float(close.iloc[-1])

        cruce_alc = r_hoy > l_hoy and r_ayer <= l_ayer
        cruce_baj = r_hoy < l_hoy and r_ayer >= l_ayer
        tend_alc  = r_hoy > l_hoy

        if cruce_alc:
            nombre = "Golden Cross" if ma_l >= 200 else f"Cruce Alcista MA{ma_r}/MA{ma_l}"
            señal, bias = "COMPRA", "ALCISTA"
            desc = f"MA{ma_r} (${r_hoy:.2f}) cruzó por encima de MA{ma_l} (${l_hoy:.2f}). Señal alcista {plazo} plazo."
            conf = "Alta" if ma_l >= 200 else "Media"
        elif cruce_baj:
            nombre = "Death Cross" if ma_l >= 200 else f"Cruce Bajista MA{ma_r}/MA{ma_l}"
            señal, bias = "VENTA", "BAJISTA"
            desc = f"MA{ma_r} (${r_hoy:.2f}) cruzó por debajo de MA{ma_l} (${l_hoy:.2f}). Señal bajista {plazo} plazo."
            conf = "Alta" if ma_l >= 200 else "Media"
        else:
            nombre = f"Tendencia MA{ma_r}/MA{ma_l}"
            señal  = "MANTENER" if tend_alc else "PRECAUCIÓN"
            bias   = "ALCISTA"  if tend_alc else "BAJISTA"
            desc   = f"MA{ma_r}=${r_hoy:.2f} {'>' if tend_alc else '<'} MA{ma_l}=${l_hoy:.2f}. Tendencia {bias.lower()} {plazo} plazo."
            conf   = "Media"

        resultados.append({
            "patron": nombre, "tipo": bias, "señal": señal,
            "fecha": str(df.index[-1])[:10],
            "precio_patron": round(precio, 2),
            "nivel_cuello": round(l_hoy, 2),
            "objetivo": round(precio * 1.05 if tend_alc else precio * 0.95, 2),
            "descripcion": desc, "confianza": conf,
        })
    return resultados


# ── FUNCIÓN PRINCIPAL ─────────────────────────────────────

def analizar_patrones(df):
    patrones = []
    try: patrones += detectar_doble_techo_piso(df)
    except: pass
    try: patrones += detectar_hch(df)
    except: pass
    try: patrones += detectar_triangulos(df)
    except: pass
    try: patrones += detectar_banderas(df)
    except: pass
    try: patrones += detectar_cruces_medias(df)
    except: pass

    sr = {}
    try: sr = detectar_soportes_resistencias(df)
    except: pass

    compras = sum(1 for p in patrones if p.get("señal") == "COMPRA")
    ventas  = sum(1 for p in patrones if p.get("señal") == "VENTA")
    total   = compras + ventas

    if total == 0:
        consenso, fuerza = "NEUTRAL", 0
    elif compras > ventas:
        consenso, fuerza = "COMPRA", round(compras / total * 100)
    else:
        consenso, fuerza = "VENTA",  round(ventas  / total * 100)

    return {
        "patrones": patrones, "soportes_resistencias": sr,
        "consenso": consenso, "fuerza": fuerza,
        "n_compras": compras, "n_ventas": ventas,
        "total_patrones": len(patrones),
    }
