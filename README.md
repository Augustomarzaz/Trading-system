# 📈 Sistema de Trading Algorítmico
**Swing Trading: NYSE/NASDAQ + CEDEARs · Streamlit Cloud · Alertas Telegram**

---

## 🗂️ Estructura del proyecto

```
trading_system/
├── app.py              ← Dashboard principal (Streamlit)
├── engine.py           ← Motor: screener + señales + backtesting
├── alerts.py           ← Bot de Telegram
├── reports.py          ← Generador de PDF
├── config.py           ← Configuración central
├── requirements.txt    ← Dependencias
└── README.md
```

---

## 🚀 Deploy en Streamlit Cloud (GRATIS, 24/7)

### Paso 1 — Crear cuenta en GitHub
1. Ir a [github.com](https://github.com) → Sign up (gratis)
2. Crear un repositorio nuevo → nombre: `trading-system`
3. Subir todos los archivos de esta carpeta

### Paso 2 — Crear cuenta en Streamlit Cloud
1. Ir a [share.streamlit.io](https://share.streamlit.io)
2. Iniciar sesión con tu cuenta de GitHub
3. Clic en **New app**
4. Seleccionar tu repositorio `trading-system`
5. Main file: `app.py`
6. Clic en **Deploy** ✅

Tu dashboard queda online en una URL como:
`https://tu-usuario-trading-system.streamlit.app`

---

## 📱 Configurar Bot de Telegram

### Crear el bot (5 minutos)
1. Abrir Telegram → buscar **@BotFather**
2. Escribir `/newbot`
3. Elegir un nombre: ej. `Mi Trading Bot`
4. Elegir un username: ej. `mi_trading_bot`
5. BotFather te da un **TOKEN** → copiarlo

### Obtener tu Chat ID
1. Abrir Telegram → buscar **@userinfobot**
2. Escribir `/start`
3. Te responde con tu **Chat ID** → copiarlo

### Configurar en Streamlit Cloud
1. Ir a tu app en Streamlit Cloud
2. Clic en **Settings** → **Secrets**
3. Agregar:
```toml
TELEGRAM_TOKEN   = "1234567890:ABCdefGhIjklmNoPqrSTuvwxYZ"
TELEGRAM_CHAT_ID = "987654321"
```
4. Guardar → la app se reinicia automáticamente ✅

---

## ⚙️ Personalización

### Agregar más acciones
En `config.py`, modificar `UNIVERSE_NYSE` o `UNIVERSE_CEDEARS`:
```python
UNIVERSE_NYSE = ["AAPL", "MSFT", "TU_ACCION_AQUI", ...]
```

### Cambiar frecuencia de actualización
En el sidebar del dashboard, el slider **"Actualización automática"**
permite elegir entre 5, 10, 15 o 30 minutos.

### Ajustar parámetros
Todos los filtros (P/E, RSI, Stop Loss, etc.) son ajustables
desde el sidebar sin tocar código.

---

## 📊 Métricas calculadas

| Categoría | Métricas |
|-----------|---------|
| Básicas | Total trades, Win rate, Profit Factor, Duración media |
| Retorno | Retorno total, CAGR, Ganancia/Pérdida media por trade |
| Ratios | Sharpe, Sortino, Treynor, Calmar, AUC |
| Riesgo | Max Drawdown, VaR 95%, CVaR 95%, Volatilidad, Beta |
| Benchmark | Alpha total, Alpha CAPM, Retorno SPY, Treynor relativo |

---

## ⚠️ Aviso legal
Este sistema es solo para fines educativos y de análisis personal.
No constituye asesoramiento financiero. Todo trading implica riesgo de pérdida de capital.
Siempre validá con paper trading antes de operar con dinero real.
