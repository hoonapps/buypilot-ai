from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFError, TTFont
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs" / "specpilot_ai_product_plan.md"
OUTPUT = Path("/Users/kimyanghoon/output/pdf/shopping_purchase_decision_agent_plan.pdf")


def register_fonts() -> tuple[str, str]:
    candidates = [
        "/System/Library/Fonts/AppleSDGothicNeo.ttc",
        "/System/Library/Fonts/Supplemental/AppleGothic.ttf",
        "/System/Library/Fonts/Supplemental/NotoSansGothic-Regular.ttf",
    ]
    for font_path in candidates:
        if Path(font_path).exists():
            try:
                pdfmetrics.registerFont(TTFont("Korean", font_path))
                pdfmetrics.registerFont(TTFont("KoreanBold", font_path))
                return "Korean", "KoreanBold"
            except TTFError:
                continue
    return "Helvetica", "Helvetica-Bold"


FONT, BOLD = register_fonts()


def make_styles():
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "title",
            parent=base["Title"],
            fontName=BOLD,
            fontSize=24,
            leading=32,
            textColor=colors.HexColor("#111827"),
            alignment=TA_CENTER,
            spaceAfter=18,
        ),
        "subtitle": ParagraphStyle(
            "subtitle",
            parent=base["Normal"],
            fontName=FONT,
            fontSize=11,
            leading=18,
            textColor=colors.HexColor("#475569"),
            alignment=TA_CENTER,
            spaceAfter=24,
        ),
        "h2": ParagraphStyle(
            "h2",
            parent=base["Heading2"],
            fontName=BOLD,
            fontSize=15,
            leading=21,
            textColor=colors.HexColor("#0f766e"),
            spaceBefore=14,
            spaceAfter=8,
            keepWithNext=True,
        ),
        "h3": ParagraphStyle(
            "h3",
            parent=base["Heading3"],
            fontName=BOLD,
            fontSize=12,
            leading=18,
            textColor=colors.HexColor("#1f2937"),
            spaceBefore=10,
            spaceAfter=6,
            keepWithNext=True,
        ),
        "body": ParagraphStyle(
            "body",
            parent=base["BodyText"],
            fontName=FONT,
            fontSize=9.4,
            leading=15,
            textColor=colors.HexColor("#334155"),
            spaceAfter=6,
            alignment=TA_LEFT,
        ),
        "bullet": ParagraphStyle(
            "bullet",
            parent=base["BodyText"],
            fontName=FONT,
            fontSize=9.2,
            leading=14,
            leftIndent=12,
            firstLineIndent=-8,
            textColor=colors.HexColor("#334155"),
            spaceAfter=4,
        ),
        "quote": ParagraphStyle(
            "quote",
            parent=base["BodyText"],
            fontName=FONT,
            fontSize=10,
            leading=16,
            leftIndent=10,
            rightIndent=10,
            borderColor=colors.HexColor("#99f6e4"),
            borderWidth=1,
            borderPadding=8,
            backColor=colors.HexColor("#f0fdfa"),
            textColor=colors.HexColor("#0f766e"),
            spaceBefore=8,
            spaceAfter=10,
        ),
        "code": ParagraphStyle(
            "code",
            parent=base["Code"],
            fontName=FONT,
            fontSize=8,
            leading=11,
            leftIndent=4,
            rightIndent=4,
            textColor=colors.HexColor("#1f2937"),
            backColor=colors.HexColor("#f1f5f9"),
            borderPadding=8,
            spaceBefore=6,
            spaceAfter=8,
        ),
        "footer": ParagraphStyle(
            "footer",
            parent=base["Normal"],
            fontName=FONT,
            fontSize=7.5,
            textColor=colors.HexColor("#64748b"),
        ),
    }


STYLES = make_styles()


def clean_inline(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("**", "")
        .strip()
    )


def table_from_lines(lines: list[str]) -> Table:
    rows = []
    for line in lines:
        cells = [clean_inline(cell) for cell in line.strip("|").split("|")]
        rows.append([Paragraph(cell, STYLES["body"]) for cell in cells])

    width = A4[0] - 42 * mm
    column_count = max(1, len(rows[0]))
    col_widths = [width / column_count] * column_count
    table = Table(rows, colWidths=col_widths, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#ecfdf5")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#0f766e")),
                ("FONTNAME", (0, 0), (-1, -1), FONT),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return table


def parse_markdown(text: str):
    story = []
    lines = text.splitlines()
    i = 0
    in_code = False
    code_lines: list[str] = []

    while i < len(lines):
        raw = lines[i]
        line = raw.rstrip()

        if line.startswith("```"):
            if in_code:
                story.append(Preformatted("\n".join(code_lines), STYLES["code"]))
                code_lines = []
                in_code = False
            else:
                in_code = True
            i += 1
            continue

        if in_code:
            code_lines.append(line)
            i += 1
            continue

        if not line.strip():
            story.append(Spacer(1, 3))
            i += 1
            continue

        if line.startswith("# "):
            story.append(Paragraph(clean_inline(line[2:]), STYLES["title"]))
            story.append(
                Paragraph(
                    "컴퓨터 견적과 노트북 구매를 위한 LangGraph 기반 구매 의사결정 에이전트",
                    STYLES["subtitle"],
                )
            )
        elif line.startswith("## "):
            if "최종 산출물" in line:
                story.append(PageBreak())
            story.append(Paragraph(clean_inline(line[3:]), STYLES["h2"]))
        elif line.startswith("### "):
            story.append(Paragraph(clean_inline(line[4:]), STYLES["h3"]))
        elif line.startswith("> "):
            story.append(Paragraph(clean_inline(line[2:]), STYLES["quote"]))
        elif line.startswith("- "):
            story.append(Paragraph(f"- {clean_inline(line[2:])}", STYLES["bullet"]))
        elif line[0].isdigit() and ". " in line[:4]:
            story.append(Paragraph(clean_inline(line), STYLES["bullet"]))
        elif line.startswith("|") and i + 1 < len(lines) and lines[i + 1].startswith("|"):
            table_lines = [line]
            i += 1
            if set(lines[i].replace("|", "").strip()) <= {"-", ":"}:
                i += 1
            while i < len(lines) and lines[i].startswith("|"):
                table_lines.append(lines[i])
                i += 1
            story.append(table_from_lines(table_lines))
            story.append(Spacer(1, 8))
            continue
        else:
            story.append(Paragraph(clean_inline(line), STYLES["body"]))
        i += 1

    return story


def draw_page(canvas, doc):
    canvas.saveState()
    width, height = A4
    canvas.setStrokeColor(colors.HexColor("#e2e8f0"))
    canvas.line(20 * mm, height - 17 * mm, width - 20 * mm, height - 17 * mm)
    canvas.setFont(FONT, 7.5)
    canvas.setFillColor(colors.HexColor("#64748b"))
    canvas.drawString(20 * mm, height - 12 * mm, "SpecPilot AI 제품 기획서")
    canvas.drawRightString(width - 20 * mm, 12 * mm, str(doc.page))
    canvas.restoreState()


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(OUTPUT),
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=24 * mm,
        bottomMargin=20 * mm,
        title="SpecPilot AI 제품 기획서",
        author="Codex",
    )
    story = parse_markdown(SOURCE.read_text(encoding="utf-8"))
    doc.build(story, onFirstPage=draw_page, onLaterPages=draw_page)
    print(OUTPUT)


if __name__ == "__main__":
    main()
