import asyncio
import io
import logging
import time
from typing import Any

logger = logging.getLogger(__name__)

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.lib.colors import HexColor
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    from reportlab.lib.enums import TA_LEFT, TA_CENTER
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False
    logger.warning("reportlab not installed — PDF export will not be available")


BLUE = HexColor("#3b82f6")
PURPLE = HexColor("#8b5cf6")
RED = HexColor("#ef4444")
GREEN = HexColor("#22c55e")
DARK = HexColor("#1e293b")
LIGHT = HexColor("#f8fafc")


def _build_pdf(session_data: dict) -> bytes:
    if not HAS_REPORTLAB:
        raise RuntimeError("reportlab is not installed. Run: pip install reportlab")

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=20*mm, bottomMargin=20*mm,
                            leftMargin=15*mm, rightMargin=15*mm)
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle("Title2", parent=styles["Title"], fontSize=18, textColor=BLUE, spaceAfter=6)
    heading_style = ParagraphStyle("Heading3", parent=styles["Heading2"], fontSize=13, textColor=PURPLE, spaceAfter=4)
    body_style = ParagraphStyle("Body2", parent=styles["Normal"], fontSize=10, leading=14, textColor=DARK)
    meta_style = ParagraphStyle("Meta", parent=styles["Normal"], fontSize=9, textColor=HexColor("#64748b"))

    elements = []

    # Header
    elements.append(Paragraph("SupplyChainGPT — Council Session Report", title_style))
    elements.append(Spacer(1, 4*mm))
    elements.append(Paragraph(f"Session ID: {session_data.get('session_id', 'N/A')}", meta_style))
    elements.append(Paragraph(f"Query: {session_data.get('query', 'N/A')}", meta_style))
    ts = session_data.get("timestamp") or time.strftime("%Y-%m-%d %H:%M:%S")
    elements.append(Paragraph(f"Generated: {ts}", meta_style))
    elements.append(HRFlowable(width="100%", thickness=1, color=BLUE))
    elements.append(Spacer(1, 6*mm))

    # Agent Contributions
    elements.append(Paragraph("Agent Contributions", heading_style))
    elements.append(Spacer(1, 3*mm))

    agent_outputs = session_data.get("agent_outputs", [])
    if agent_outputs:
        for ao in agent_outputs:
            agent_name = ao.get("agent", ao.get("name", "Unknown"))
            confidence = ao.get("confidence", 0)
            content = ao.get("output", ao.get("content", ""))

            # Confidence bar as table
            conf_pct = f"{confidence:.0%}" if isinstance(confidence, (int, float)) else "N/A"
            bar_data = [[f"{agent_name}", f"Confidence: {conf_pct}"]]
            bar_table = Table(bar_data, colWidths=[60*mm, 80*mm])
            bar_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (0, 0), PURPLE),
                ("TEXTCOLOR", (0, 0), (0, 0), LIGHT),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]))
            elements.append(bar_table)
            elements.append(Spacer(1, 2*mm))

            # Truncate long content
            if len(content) > 500:
                content = content[:500] + "..."
            elements.append(Paragraph(content.replace("\n", "<br/>"), body_style))
            elements.append(Spacer(1, 4*mm))
    else:
        elements.append(Paragraph("No agent outputs recorded.", body_style))

    elements.append(HRFlowable(width="100%", thickness=0.5, color=HexColor("#cbd5e1")))
    elements.append(Spacer(1, 4*mm))

    # Debate History
    debate_history = session_data.get("debate_history", [])
    if debate_history:
        elements.append(Paragraph("Debate History", heading_style))
        elements.append(Spacer(1, 3*mm))
        for i, round_data in enumerate(debate_history):
            round_text = f"Round {i+1}: {str(round_data)[:300]}"
            elements.append(Paragraph(round_text.replace("\n", "<br/>"), body_style))
            elements.append(Spacer(1, 2*mm))
        elements.append(HRFlowable(width="100%", thickness=0.5, color=HexColor("#cbd5e1")))
        elements.append(Spacer(1, 4*mm))

    # Final Recommendation
    elements.append(Paragraph("Final Recommendation", heading_style))
    elements.append(Spacer(1, 3*mm))
    recommendation = session_data.get("recommendation", "No recommendation generated.")
    elements.append(Paragraph(recommendation.replace("\n", "<br/>"), body_style))
    elements.append(Spacer(1, 6*mm))

    # Risk Scores Table
    risk_scores = session_data.get("risk_scores", [])
    if risk_scores:
        elements.append(Paragraph("Risk Scores", heading_style))
        elements.append(Spacer(1, 3*mm))
        table_data = [["Category", "Score", "Level"]]
        for rs in risk_scores:
            category = rs.get("category", rs.get("name", "N/A"))
            score = rs.get("score", 0)
            level = "High" if score > 70 else "Medium" if score > 40 else "Low"
            table_data.append([category, str(score), level])

        risk_table = Table(table_data, colWidths=[60*mm, 30*mm, 30*mm])
        risk_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), DARK),
            ("TEXTCOLOR", (0, 0), (-1, 0), LIGHT),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#cbd5e1")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [LIGHT, HexColor("#e2e8f0")]),
        ]))
        elements.append(risk_table)

    doc.build(elements)
    return buf.getvalue()


async def generate_pdf(session_data: dict) -> bytes:
    return await asyncio.to_thread(_build_pdf, session_data)
