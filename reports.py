# ============================================================
#  reports.py — Generación de PDF desde Streamlit
#  Produce el informe completo y lo retorna como bytes
#  para descarga directa desde el dashboard.
# ============================================================

import io
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer,
    Table, TableStyle, HRFlowable, PageBreak
)
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.pdfgen import canvas as rl_canvas

# ── Colores ───────────────────────────────────────────────
DARK   = colors.HexColor("#0a0e14")
ACCENT = colors.HexColor("#2b6cb0")
GREEN  = colors.HexColor("#276749")
RED    = colors.HexColor("#9b2c2c")
MUTED  = colors.HexColor("#718096")
LIGHT  = colors.HexColor("#ebf8ff")
WHITE  = colors.white
LGRAY  = colors.HexColor("#f7fafc")
BGRAY  = colors.HexColor("#e2e8f0")

def sty(name, **kw):
    return ParagraphStyle(name, **kw)

def make_styles():
    return {
        "titulo": sty("t", fontName="Helvetica-Bold", fontSize=20, leading=26,
                      textColor=DARK, spaceAfter=4),
        "sub":    sty("s", fontName="Helvetica", fontSize=11, leading=16,
                      textColor=MUTED, spaceAfter=12),
        "sec":    sty("se", fontName="Helvetica-Bold", fontSize=12, leading=16,
                      textColor=DARK, spaceBefore=14, spaceAfter=5),
        "sub2":   sty("sb", fontName="Helvetica-Bold", fontSize=10, leading=14,
                      textColor=ACCENT, spaceBefore=8, spaceAfter=3),
        "body":   sty("b", fontName="Helvetica", fontSize=9, leading=14,
                      textColor=colors.HexColor("#2d3748"),
                      alignment=TA_JUSTIFY, spaceAfter=5),
        "nota":   sty("n", fontName="Helvetica-Oblique", fontSize=8, leading=12,
                      textColor=MUTED, spaceAfter=4),
        "mono":   sty("m", fontName="Courier", fontSize=8, leading=13,
                      backColor=LGRAY, borderColor=BGRAY, borderWidth=1,
                      borderPad=6, spaceAfter=6,
                      textColor=colors.HexColor("#2d3748")),
    }

def tbl(headers, rows, col_widths=None):
    hs = ParagraphStyle("th", fontName="Helvetica-Bold", fontSize=8,
                        textColor=WHITE, alignment=TA_CENTER)
    cs = ParagraphStyle("td", fontName="Helvetica", fontSize=8,
                        textColor=colors.HexColor("#2d3748"), alignment=TA_CENTER)
    data = [[Paragraph(h, hs) for h in headers]]
    for row in rows:
        data.append([Paragraph(str(c), cs) for c in row])
    w = col_widths or ([(A4[0]-3*cm)/len(headers)]*len(headers))
    t = Table(data, colWidths=w, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND",     (0,0),(-1,0),  ACCENT),
        ("ROWBACKGROUNDS", (0,1),(-1,-1), [WHITE, LGRAY]),
        ("BOX",            (0,0),(-1,-1), 0.4, BGRAY),
        ("INNERGRID",      (0,0),(-1,-1), 0.3, BGRAY),
        ("TOPPADDING",     (0,0),(-1,-1), 5),
        ("BOTTOMPADDING",  (0,0),(-1,-1), 5),
        ("LEFTPADDING",    (0,0),(-1,-1), 6),
    ]))
    return t

class NC(rl_canvas.Canvas):
    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self._s = []
    def showPage(self):
        self._s.append(dict(self.__dict__))
        self._startPage()
    def save(self):
        n = len(self._s)
        for st in self._s:
            self.__dict__.update(st)
            W, H = A4
            self.setFillColor(DARK)
            self.rect(0, H-1.1*cm, W, 1.1*cm, fill=1, stroke=0)
            self.setFillColor(colors.HexColor("#63b3ed"))
            self.setFont("Helvetica-Bold", 7)
            self.drawString(1.3*cm, H-0.75*cm, "SISTEMA DE TRADING ALGORÍTMICO — INFORME")
            self.setFillColor(MUTED)
            self.setFont("Helvetica", 7)
            self.drawRightString(W-1.3*cm, H-0.75*cm,
                f"{datetime.now().strftime('%d/%m/%Y')}  |  pág. {self._pageNumber}/{n}")
            self.setFillColor(BGRAY)
            self.rect(0, 0, W, 0.8*cm, fill=1, stroke=0)
            self.setFillColor(MUTED)
            self.setFont("Helvetica", 7)
            self.drawString(1.3*cm, 0.28*cm,
                "Solo fines educativos. No constituye asesoramiento financiero.")
            super().showPage()
        super().save()


def generate_pdf(results: dict, params: dict) -> bytes:
    buf = io.BytesIO()
    s   = make_styles()
    doc = SimpleDocTemplate(buf, pagesize=A4,
          leftMargin=1.4*cm, rightMargin=1.4*cm,
          topMargin=1.7*cm,  bottomMargin=1.4*cm)

    story = []
    fecha = datetime.now().strftime("%d/%m/%Y %H:%M")
    fund  = results.get("fundamental", [])
    senales = results.get("senales",   {})
    bts   = results.get("backtests",   {})

    aprobadas = [r for r in fund if r["estado"] == "ok"]
    n_compra  = sum(1 for s in senales.values() if s.get("senal") == "COMPRA")

    # ── Portada ──────────────────────────────────────────
    story += [
        Spacer(1, 0.8*cm),
        Paragraph("Informe de Trading Algorítmico", s["titulo"]),
        Paragraph(f"NYSE/NASDAQ + CEDEARs · Generado: {fecha}", s["sub"]),
        HRFlowable(width="100%", thickness=2, color=ACCENT, spaceAfter=10),
    ]

    kpis = [
        ["Activos analizados", str(len(fund))],
        ["Pasan filtro fund.", str(len(aprobadas))],
        ["Señales de compra",  str(n_compra)],
        ["Backtests generados",str(len(bts))],
    ]
    kt = Table([[Paragraph(f"<b>{v}</b>", ParagraphStyle("kv",
                    fontName="Helvetica-Bold", fontSize=18,
                    textColor=ACCENT, alignment=TA_CENTER))
                for _, v in kpis],
               [Paragraph(l, ParagraphStyle("kl", fontName="Helvetica",
                    fontSize=8, textColor=MUTED, alignment=TA_CENTER))
                for l, _ in kpis]],
               colWidths=[(A4[0]-2.8*cm)/4]*4)
    kt.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), LGRAY),
        ("BOX",           (0,0),(-1,-1), 0.4, BGRAY),
        ("INNERGRID",     (0,0),(-1,-1), 0.4, BGRAY),
        ("TOPPADDING",    (0,0),(-1,-1), 10),
        ("BOTTOMPADDING", (0,0),(-1,-1), 10),
    ]))
    story += [kt, Spacer(1, 0.3*cm),
              Paragraph(f"Parámetros: P/E < {params['pe_max']} · ROE > {params['roe_min']*100:.0f}% · "
                        f"Stop {params['stop_loss']*100:.0f}% · TP {params['take_profit']*100:.0f}%", s["nota"]),
              PageBreak()]

    # ── Screener ─────────────────────────────────────────
    story += [Paragraph("1. Screener fundamental", s["sec"]),
              HRFlowable(width="100%", thickness=0.5, color=BGRAY, spaceAfter=6)]

    fund_rows = [[
        r["ticker"], r["nombre"][:22], r["mercado"],
        str(r["pe"]) if r["pe"] else "—",
        f"{r['roe']}%" if r["roe"] else "—",
        str(r["de"]) if r["de"] else "—",
        "✓ PASA" if r["estado"] == "ok" else r["motivo"][:28]
    ] for r in fund]

    story += [tbl(
        ["Ticker","Empresa","Mercado","P/E","ROE","D/E","Resultado"],
        fund_rows,
        col_widths=[1.8*cm, 4.8*cm, 2.8*cm, 1.6*cm, 1.8*cm, 1.6*cm, 4.4*cm]
    ), PageBreak()]

    # ── Señales técnicas ─────────────────────────────────
    story += [Paragraph("2. Señales técnicas", s["sec"]),
              HRFlowable(width="100%", thickness=0.5, color=BGRAY, spaceAfter=6)]

    if senales:
        sen_rows = [[
            t,
            f"${sv['precio']}",
            str(sv["rsi"]),
            f"${sv['ema_r']}",
            f"${sv['ema_l']}",
            sv["senal"],
            f"${sv['stop_loss']}",
            f"${sv['take_profit']}",
        ] for t, sv in senales.items()]
        story += [tbl(
            ["Ticker","Precio","RSI","EMA9","EMA21","Señal","Stop","Take Profit"],
            sen_rows,
            col_widths=[1.8*cm, 2.4*cm, 1.6*cm, 2.4*cm, 2.4*cm, 2.2*cm, 2.4*cm, 3.0*cm]
        )]
    else:
        story.append(Paragraph("Ninguna acción con señal activa en este período.", s["body"]))

    story.append(PageBreak())

    # ── Backtesting por activo ────────────────────────────
    story += [Paragraph("3. Backtesting profesional por activo", s["sec"]),
              HRFlowable(width="100%", thickness=0.5, color=BGRAY, spaceAfter=6)]

    for ticker, m in bts.items():
        story.append(Paragraph(f"3.{list(bts.keys()).index(ticker)+1} {ticker}", s["sub2"]))
        bt_rows = [
            ["Total trades",       str(m["total_trades"]),   "Win rate",       f"{m['win_rate']}%"],
            ["Retorno total",      f"{m['retorno']:+.2f}%",  "Retorno anual",  f"{m['retorno_anual']:+.2f}%"],
            ["Sharpe Ratio",       str(m["sharpe"]),         "Sortino Ratio",  str(m["sortino"])],
            ["Treynor Ratio",      str(m["treynor"]),        "Calmar Ratio",   str(m["calmar"])],
            ["Max Drawdown",       f"{m['max_dd']:.1f}%",    "DD Duración",    f"{m['max_dd_dur']}d"],
            ["Volatilidad",        f"{m['volatilidad']:.1f}%","VaR 95%",       f"{m['var_95']:.3f}%"],
            ["CVaR 95%",           f"{m['cvar_95']:.3f}%",   "AUC",            str(m["auc"])],
            ["Alpha total",        f"{m['alpha_total']:+.2f}%","Alpha anual",  f"{m['alpha_anual']:+.2f}%"],
            ["Beta vs SPY",        str(m["beta"]),           "Profit Factor",  str(m["profit_factor"])],
            ["vs SPY (benchmark)", f"{m['bm_retorno']:+.1f}%","Profit Factor", str(m["profit_factor"])],
        ]
        rows_flat = []
        for row in bt_rows:
            rows_flat.append([row[0], row[1], row[2], row[3]])
        story.append(tbl(
            ["Métrica", "Valor", "Métrica", "Valor"],
            rows_flat,
            col_widths=[4.5*cm, 3*cm, 4.5*cm, 3*cm]
        ))
        story.append(Spacer(1, 0.3*cm))

    # ── Resumen ejecutivo ─────────────────────────────────
    story += [PageBreak(),
              Paragraph("4. Resumen ejecutivo", s["sec"]),
              HRFlowable(width="100%", thickness=0.5, color=BGRAY, spaceAfter=6)]

    if bts:
        best = max(bts.values(), key=lambda x: x["sharpe"])
        story.append(Paragraph(
            f"El activo con mejor perfil riesgo/retorno es <b>{best['ticker']}</b> "
            f"con Sharpe de {best['sharpe']}, retorno anualizado de {best['retorno_anual']:+.1f}% "
            f"y win rate del {best['win_rate']}%. "
            f"{'La estrategia supera al benchmark SPY.' if best['alpha_total'] > 0 else 'La estrategia no supera al benchmark en este período.'}", s["body"]))

    story += [
        Spacer(1, 0.6*cm),
        HRFlowable(width="100%", thickness=0.5, color=BGRAY, spaceAfter=6),
        Paragraph("Aviso legal: informe generado automáticamente con fines educativos. "
                  "No constituye asesoramiento de inversión. Todo trading implica riesgo de pérdida.", s["nota"])
    ]

    doc.build(story, canvasmaker=NC)
    buf.seek(0)
    return buf.read()
