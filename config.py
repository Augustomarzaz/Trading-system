# ============================================================
#  config.py — Configuración central del sistema
#  Modificá este archivo para ajustar todos los parámetros
# ============================================================

# ── Universos de activos ──────────────────────────────────

UNIVERSE_NYSE = [
    # Tecnología
    "AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA",
    # Financiero
    "JPM", "BAC", "GS", "WFC", "C",
    # Salud
    "JNJ", "PFE", "MRK", "ABBV",
    # Energía
    "XOM", "CVX",
    # Consumo
    "KO", "PG", "WMT",
]

UNIVERSE_CEDEARS = [
    # CEDEARs disponibles en Argentina (tickers en Yahoo Finance)
    "GGAL",   # Grupo Financiero Galicia
    "YPF",    # YPF S.A.
    "BMA",    # Banco Macro
    "BBAR",   # BBVA Argentina
    "CEPU",   # Central Puerto
    "LOMA",   # Loma Negra
    "SUPV",   # Grupo Supervielle
    "TXAR",   # Ternium Argentina
    "MIRG",   # Mirgor
    "TECO2.BA", # Telecom Argentina (suffix .BA para Merval en yFinance)
]

# ── Parámetros fundamentales (defaults) ──────────────────
CONFIG = {
    "pe_max":  25,
    "roe_min": 0.12,
    "de_max":  1.5,
    "benchmark": "SPY",
    "rf_anual":  0.045,   # Tasa libre de riesgo (T-Bill 2025)
    "capital":   10_000,
}

# ── Parámetros técnicos (defaults) ───────────────────────
TECNICO = {
    "rsi_periodo":  14,
    "rsi_entrada":  40,
    "rsi_salida":   65,
    "ema_rapida":   9,
    "ema_lenta":    21,
}

# ── Gestión de riesgo (defaults) ─────────────────────────
RIESGO = {
    "stop_loss":       0.05,
    "take_profit":     0.12,
    "max_posiciones":  5,
}
