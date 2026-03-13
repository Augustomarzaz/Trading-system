# ============================================================
#  alerts.py — Alertas automáticas por Telegram
#
#  CONFIGURACIÓN (una sola vez):
#  1. Abrí Telegram y buscá @BotFather
#  2. Escribí /newbot y seguí los pasos
#  3. Copiá el TOKEN que te da BotFather
#  4. Buscá @userinfobot en Telegram → te da tu CHAT_ID
#  5. En Streamlit Cloud → Settings → Secrets, agregá:
#       TELEGRAM_TOKEN = "tu_token_aqui"
#       TELEGRAM_CHAT_ID = "tu_chat_id_aqui"
# ============================================================

import requests
import streamlit as st
from datetime import datetime


def send_telegram(mensaje: str) -> bool:
    """
    Envía un mensaje de texto a Telegram vía Bot API.
    Retorna True si fue exitoso, False en caso contrario.
    """
    try:
        # Lee los secrets de Streamlit Cloud
        token   = st.secrets.get("TELEGRAM_TOKEN",   "")
        chat_id = st.secrets.get("TELEGRAM_CHAT_ID", "")

        if not token or not chat_id:
            # Si no hay secrets configurados, no falla — solo no envía
            return False

        url  = f"https://api.telegram.org/bot{token}/sendMessage"
        data = {
            "chat_id":    chat_id,
            "text":       mensaje,
            "parse_mode": "Markdown",
        }
        resp = requests.post(url, data=data, timeout=10)
        return resp.status_code == 200

    except Exception:
        return False


def alerta_compra(ticker, precio, rsi, stop_loss, take_profit):
    msg = (
        f"🟢 *SEÑAL DE COMPRA*\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"Ticker: *{ticker}*\n"
        f"Precio actual: `${precio}`\n"
        f"RSI: `{rsi}`\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🔴 Stop Loss:   `${stop_loss}`\n"
        f"🎯 Take Profit: `${take_profit}`\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🕐 {datetime.now().strftime('%d/%m/%Y %H:%M')}"
    )
    return send_telegram(msg)


def alerta_venta(ticker, precio, motivo, ganancia_pct):
    emoji = "✅" if ganancia_pct > 0 else "❌"
    msg = (
        f"{emoji} *SEÑAL DE VENTA — {motivo.upper()}*\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"Ticker: *{ticker}*\n"
        f"Precio de salida: `${precio}`\n"
        f"Resultado: `{ganancia_pct:+.2f}%`\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🕐 {datetime.now().strftime('%d/%m/%Y %H:%M')}"
    )
    return send_telegram(msg)


def alerta_resumen_diario(n_analizadas, n_compra, n_esperar):
    msg = (
        f"📊 *RESUMEN DIARIO — Trading System*\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"Activos analizados: `{n_analizadas}`\n"
        f"Señales de compra:  `{n_compra}`\n"
        f"En espera:          `{n_esperar}`\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🕐 {datetime.now().strftime('%d/%m/%Y %H:%M')}"
    )
    return send_telegram(msg)
