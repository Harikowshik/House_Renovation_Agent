"""PDF Report Generator for AI Home Renovation Dossiers.

Generates structured, print-ready PDF reports with styling,
metadata cards, and sanitized text formatting.
"""

import re
from fpdf import FPDF
from typing import Dict, Any, Optional


def clean_markdown_for_pdf(text: str) -> str:
    """Strip complex markdown tags and normalize emojis/tables to plain ASCII-compatible text."""
    if not text:
        return ""
    # Remove markdown headers
    text = re.sub(r"#+\s*", "", text)
    # Remove bold/italic markers
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"\*([^*]+)\*", r"\1", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)

    # Clean markdown table separator lines like |---|---|---|
    text = re.sub(r"\|[\s\-:|]+\|", "", text)
    # Format table rows (| Col1 | Col2 |) into clean structured text
    def format_table_row(match):
        raw = match.group(0)
        cells = [c.strip() for c in raw.split("|") if c.strip()]
        return "  * " + " | ".join(cells) if cells else ""
    text = re.sub(r"\|[^\n]+\|", format_table_row, text)

    # Replace non-ascii chars/emojis with readable approximations
    replacements = {
        "📸": "[PHOTO]",
        "🎨": "[DESIGN]",
        "🏗️": "[BUILD]",
        "🏗": "[BUILD]",
        "💰": "[BUDGET]",
        "⏱️": "[TIME]",
        "⏱": "[TIME]",
        "📐": "[DIM]",
        "🛠️": "[TOOLS]",
        "🛠": "[TOOLS]",
        "🟢": "[DIY]",
        "🔴": "[PRO]",
        "💡": "[TIP]",
        "✅": "[DONE]",
        "🔒": "[LOCKED]",
        "📉": "[BUDGET-FIRST]",
        "🎯": "[PRIORITY]",
        "🚫": "[NO-PAINT]",
        "🪑": "[FURNITURE]",
        "—": "-",
        "–": "-",
        "―": "-",
        "“": '"',
        "”": '"',
        "‘": "'",
        "’": "'",
        "•": "*",
        "✓": "[OK]",
        "✔": "[OK]",
        "✗": "[X]",
        "✖": "[X]",
        "→": "->",
        "←": "<-",
        "\u00a0": " ",
        "\u200b": "",
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
        
    # Ensure text is encodable in latin-1 for standard PDF fonts
    text = text.encode("latin-1", "replace").decode("latin-1")
    return text


class RenovationPDF(FPDF):
    def header(self):
        self.set_font("helvetica", "B", 11)
        self.set_text_color(70, 80, 95)
        self.cell(100, 8, "AI HOME RENOVATION DOSSIER", border=0, align="L")
        self.set_font("helvetica", "I", 8)
        self.cell(90, 8, "Google Gemini Multimodal Vision", border=0, align="R", new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(200, 210, 225)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font("helvetica", "I", 8)
        self.set_text_color(140, 150, 165)
        self.cell(0, 10, f"Page {self.page_no()}", border=0, align="C", new_x="LMARGIN", new_y="NEXT")


from fpdf.enums import WrapMode, XPos, YPos


def safe_write_paragraph(pdf: FPDF, text: str, line_height: float = 5.0) -> None:
    """Safely renders text with WrapMode.CHAR to guarantee no horizontal overflow exceptions."""
    if not text:
        return
    pdf.set_x(pdf.l_margin)
    try:
        pdf.multi_cell(
            w=pdf.epw,
            h=line_height,
            text=text,
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
            wrapmode=WrapMode.CHAR,
        )
    except Exception:
        # Ultimate fallback: chunk by 75 characters using simple cells
        for i in range(0, len(text), 75):
            chunk = text[i:i+75]
            try:
                pdf.set_x(pdf.l_margin)
                pdf.cell(pdf.epw, line_height, chunk, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            except Exception:
                pass


def build_renovation_pdf(
    room_type: str,
    budget: str,
    target_style: str,
    roi_info: Dict[str, Any],
    quantities: Dict[str, Any],
    assessment: str,
    design_plan: str,
    roadmap: str,
    diy_breakdown: Optional[str],
    slc_prompt: str,
) -> bytes:
    """Generates complete renovation dossier as PDF bytes with guaranteed error-free rendering."""
    try:
        return _build_styled_renovation_pdf(
            room_type=room_type,
            budget=budget,
            target_style=target_style,
            roi_info=roi_info,
            quantities=quantities,
            assessment=assessment,
            design_plan=design_plan,
            roadmap=roadmap,
            diy_breakdown=diy_breakdown,
            slc_prompt=slc_prompt,
        )
    except Exception:
        # Bulletproof fallback: Plain clean PDF layout if styled PDF hits any rendering quirks
        return _build_fallback_renovation_pdf(
            room_type=room_type,
            budget=budget,
            target_style=target_style,
            roi_info=roi_info,
            assessment=assessment,
            design_plan=design_plan,
            roadmap=roadmap,
            diy_breakdown=diy_breakdown,
            slc_prompt=slc_prompt,
        )


def _build_styled_renovation_pdf(
    room_type: str,
    budget: str,
    target_style: str,
    roi_info: Dict[str, Any],
    quantities: Dict[str, Any],
    assessment: str,
    design_plan: str,
    roadmap: str,
    diy_breakdown: Optional[str],
    slc_prompt: str,
) -> bytes:
    pdf = RenovationPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Document Title
    pdf.set_font("helvetica", "B", 18)
    pdf.set_text_color(25, 35, 55)
    pdf.set_x(pdf.l_margin)
    pdf.cell(pdf.epw, 9, f"{room_type.upper()} RENOVATION PLAN", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="L")
    pdf.ln(2)

    # Executive Summary Card
    card_y = pdf.get_y()
    pdf.set_fill_color(240, 245, 255)
    pdf.set_draw_color(180, 205, 245)
    pdf.rect(10, card_y, 190, 24, style="DF")
    
    pdf.set_xy(14, card_y + 3)
    pdf.set_font("helvetica", "B", 8)
    pdf.set_text_color(50, 60, 80)
    pdf.cell(45, 5, "STATED BUDGET:")
    pdf.cell(45, 5, "TARGET AESTHETIC:")
    pdf.cell(45, 5, "ESTIMATED EQUITY GAIN:")
    pdf.cell(45, 5, "EXPECTED RESALE ROI:", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.set_x(14)
    pdf.set_font("helvetica", "B", 11)
    pdf.set_text_color(30, 110, 220)
    pdf.cell(45, 8, str(budget)[:22])
    pdf.cell(45, 8, str(target_style)[:22])
    pdf.cell(45, 8, str(roi_info.get("estimated_value_added", "N/A"))[:22])
    pdf.cell(45, 8, f"{roi_info.get('roi_percentage', 65)}%", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_xy(pdf.l_margin, card_y + 28)

    # Dimensions & Material Quantities Summary
    pdf.set_font("helvetica", "B", 11)
    pdf.set_text_color(30, 45, 70)
    pdf.set_x(pdf.l_margin)
    pdf.cell(pdf.epw, 7, "MATERIAL QUANTITY ESTIMATES", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("helvetica", "", 9)
    pdf.set_text_color(60, 70, 85)
    
    q_line = (
        f"Floor Area: {quantities.get('floor_sqft', 0)} sq ft  |  "
        f"Paint: {quantities.get('paint_gallons', 0)} Gallons (2 coats)  |  "
        f"Flooring: {quantities.get('flooring_needed_sqft', 0)} sq ft (~{quantities.get('flooring_boxes', 0)} boxes)"
    )
    if quantities.get("backsplash_sqft", 0) > 0:
        q_line += f"  |  Tile Needed: {quantities.get('backsplash_sqft')} sq ft"
    safe_write_paragraph(pdf, q_line, line_height=5.0)
    pdf.ln(3)

    # Sections to render
    sections = [
        ("1. VISUAL SPACE ASSESSMENT & LAYOUT PRESERVATION", assessment),
        ("2. SPECIFIED DESIGN FINISHES & MATERIALS", design_plan),
        ("3. EXECUTION ROADMAP, BUDGET & TIMELINE", roadmap),
        ("4. DIY FEASIBILITY & LABOR SAVINGS", diy_breakdown or "Standard contractor execution recommended."),
        ("5. PHOTOREALISTIC RENDERING BRIEF (SLC FORMULA)", slc_prompt),
    ]

    for title, content in sections:
        if not content:
            continue
            
        # Section Header Banner
        pdf.ln(2)
        pdf.set_fill_color(230, 238, 250)
        pdf.set_font("helvetica", "B", 10)
        pdf.set_text_color(20, 35, 60)
        pdf.set_x(pdf.l_margin)
        pdf.cell(pdf.epw, 7, f"  {title}", fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(2)

        # Section Body Text
        pdf.set_font("helvetica", "", 9)
        pdf.set_text_color(50, 60, 75)
        clean_text = clean_markdown_for_pdf(content)
        
        paragraphs = clean_text.split("\n")
        for para in paragraphs:
            para = para.strip()
            if not para:
                pdf.ln(2)
                continue
            safe_write_paragraph(pdf, para, line_height=5.0)

    return bytes(pdf.output())


def _build_fallback_renovation_pdf(
    room_type: str,
    budget: str,
    target_style: str,
    roi_info: Dict[str, Any],
    assessment: str,
    design_plan: str,
    roadmap: str,
    diy_breakdown: Optional[str],
    slc_prompt: str,
) -> bytes:
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("helvetica", "B", 16)
    pdf.cell(pdf.epw, 10, f"{room_type.upper()} RENOVATION DOSSIER", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("helvetica", "", 10)
    pdf.cell(pdf.epw, 7, f"Budget: {budget} | Style: {target_style} | ROI: {roi_info.get('roi_percentage', 65)}%", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(4)

    all_sections = [
        ("ASSESSMENT", assessment),
        ("DESIGN SPECIFICATIONS", design_plan),
        ("ROADMAP & BUDGET", roadmap),
        ("DIY BREAKDOWN", diy_breakdown or ""),
        ("RENDERING PROMPT", slc_prompt),
    ]

    for title, text in all_sections:
        if not text:
            continue
        pdf.set_font("helvetica", "B", 11)
        pdf.cell(pdf.epw, 8, title, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_font("helvetica", "", 9)
        cleaned = clean_markdown_for_pdf(text)
        for line in cleaned.split("\n"):
            line = line.strip()
            if line:
                safe_write_paragraph(pdf, line, line_height=4.5)
            else:
                pdf.ln(2)
        pdf.ln(3)

    return bytes(pdf.output())


