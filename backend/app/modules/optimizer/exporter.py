import io
from typing import Any

import docx
from docx.shared import Inches, Pt, RGBColor
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer


def sanitize_text_for_reportlab(text: str) -> str:
    """Normalize unicode and XML entities for standard Helvetica PDF rendering."""
    if not text:
        return ""
    # XML entity escaping
    s = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    # Replace typography dashes and quotes with standard ASCII equivalents
    s = s.replace("\u2013", "-").replace("\u2014", "-")
    s = s.replace("\u2018", "'").replace("\u2019", "'")
    s = s.replace("\u201c", '"').replace("\u201d", '"')
    s = s.replace("\u2022", "•")
    s = s.replace("\u00a0", " ")
    return s.strip()


def add_page_number(canvas, doc):
    """Draw professional page numbering on all pages."""
    page_num = canvas.getPageNumber()
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(HexColor("#9CA3AF"))
    canvas.drawRightString(doc.pagesize[0] - 40, 20, f"Page {page_num}")
    canvas.restoreState()


class ResumeExporter:
    """Generates ATS-compliant, single-column PDF and DOCX documents with robust formatting,
    multiline wrapping, orphan header prevention, and pre-export validation.
    """

    def validate_content(self, content: dict[str, Any]) -> None:
        """Validate content dictionary before exporting."""
        if not content:
            raise ValueError("Cannot export empty resume content.")

        name = (
            content.get("full_name")
            or content.get("candidate_name")
            or ""
        ).strip()
        if not name:
            raise ValueError("Cannot export resume: missing candidate name.")

        sections = content.get("sections", [])
        if not sections and not content.get("raw_sections"):
            raise ValueError("Cannot export resume: at least one resume section is required.")

    def generate_pdf(self, tailored_content: dict[str, Any]) -> bytes:
        """Render a clean, single-column ATS-friendly PDF using ReportLab."""
        self.validate_content(tailored_content)

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=40,
            leftMargin=40,
            topMargin=40,
            bottomMargin=40,
        )

        styles = getSampleStyleSheet()

        # ATS Typography Styles
        name_style = ParagraphStyle(
            "ATS_Name",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=18,
            leading=22,
            textColor=HexColor("#111827"),
            alignment=1,  # Center
            spaceAfter=4,
        )

        contact_style = ParagraphStyle(
            "ATS_Contact",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            textColor=HexColor("#4B5563"),
            alignment=1,  # Center
            spaceAfter=10,
        )

        section_heading_style = ParagraphStyle(
            "ATS_Heading",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            textColor=HexColor("#1D4ED8"),
            spaceBefore=10,
            spaceAfter=3,
            keepWithNext=True,  # Prevent orphan headings at the bottom of pages
        )

        item_title_style = ParagraphStyle(
            "ATS_ItemTitle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=13,
            textColor=HexColor("#1F2937"),
            keepWithNext=True,
        )

        item_sub_style = ParagraphStyle(
            "ATS_ItemSub",
            parent=styles["Normal"],
            fontName="Helvetica-Oblique",
            fontSize=9,
            leading=12,
            textColor=HexColor("#4B5563"),
            spaceAfter=3,
            keepWithNext=True,
        )

        bullet_style = ParagraphStyle(
            "ATS_Bullet",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=13,
            textColor=HexColor("#1F2937"),
            leftIndent=15,
            firstLineIndent=-10,
            spaceAfter=2,
        )

        story = []

        # 1. Header (Candidate Name & Contact)
        candidate_name = (
            tailored_content.get("full_name")
            or tailored_content.get("candidate_name")
            or "Candidate Profile"
        )
        contact_info = (
            tailored_content.get("contact_info") or "Verified Candidate Profile • CareerPilot"
        )

        story.append(Paragraph(sanitize_text_for_reportlab(candidate_name), name_style))
        story.append(Paragraph(sanitize_text_for_reportlab(contact_info), contact_style))
        story.append(HRFlowable(width="100%", thickness=1, color=HexColor("#CBD5E1"), spaceAfter=6))

        # 2. Sections
        sections = tailored_content.get("sections", [])
        for section in sections:
            heading = section.get("heading") or section.get("section_type", "Section")
            story.append(Paragraph(sanitize_text_for_reportlab(heading.upper()), section_heading_style))
            story.append(
                HRFlowable(width="100%", thickness=0.5, color=HexColor("#E2E8F0"), spaceAfter=5)
            )

            # Items in section
            for item in section.get("items", []):
                title = sanitize_text_for_reportlab(item.get("title", ""))
                org = sanitize_text_for_reportlab(item.get("organization", ""))
                dates = (
                    f"{item.get('start_date', '')} - {item.get('end_date', 'Present')}"
                    if item.get("start_date")
                    else ""
                )
                dates = sanitize_text_for_reportlab(dates)
                loc = sanitize_text_for_reportlab(item.get("location", ""))

                sub_line_parts = [p for p in [org, loc, dates] if p]
                sub_line = " | ".join(sub_line_parts)

                if title:
                    story.append(Paragraph(title, item_title_style))
                if sub_line:
                    story.append(Paragraph(sub_line, item_sub_style))

                # Bullets & Descriptive Content
                has_bullets = False
                for bullet in item.get("bullets", []):
                    bullet_text = bullet if isinstance(bullet, str) else str(bullet)
                    sanitized_b = sanitize_text_for_reportlab(bullet_text)
                    if sanitized_b:
                        story.append(Paragraph(f"• {sanitized_b}", bullet_style))
                        has_bullets = True

                # If no bullets, render description / text lines
                if not has_bullets:
                    desc = item.get("description") or item.get("text") or ""
                    if desc:
                        sanitized_desc = sanitize_text_for_reportlab(desc)
                        for line in sanitized_desc.splitlines():
                            if line.strip():
                                story.append(Paragraph(line.strip(), bullet_style))

                story.append(Spacer(1, 4))

            # Non-itemized raw content (e.g. Skills block, Summary block)
            if not section.get("items") and section.get("raw_content"):
                sanitized_raw = sanitize_text_for_reportlab(section["raw_content"])
                for line in sanitized_raw.splitlines():
                    if line.strip():
                        story.append(Paragraph(line.strip(), bullet_style))
                story.append(Spacer(1, 4))

        doc.build(story, onFirstPage=add_page_number, onLaterPages=add_page_number)
        buffer.seek(0)
        return buffer.getvalue()

    def generate_docx(self, tailored_content: dict[str, Any]) -> bytes:
        """Render a clean, single-column ATS-friendly DOCX document."""
        self.validate_content(tailored_content)

        doc = docx.Document()

        # Set standard margins (0.75 inch)
        for section in doc.sections:
            section.top_margin = Inches(0.75)
            section.bottom_margin = Inches(0.75)
            section.left_margin = Inches(0.75)
            section.right_margin = Inches(0.75)

        # 1. Header
        candidate_name = (
            tailored_content.get("full_name")
            or tailored_content.get("candidate_name")
            or "Candidate Profile"
        )
        contact_info = (
            tailored_content.get("contact_info") or "Verified Candidate Profile • CareerPilot"
        )

        p_name = doc.add_paragraph()
        p_name.alignment = docx.enum.text.WD_ALIGN_PARAGRAPH.CENTER
        run_name = p_name.add_run(candidate_name)
        run_name.font.name = "Arial"
        run_name.font.size = Pt(18)
        run_name.font.bold = True

        p_contact = doc.add_paragraph()
        p_contact.alignment = docx.enum.text.WD_ALIGN_PARAGRAPH.CENTER
        run_contact = p_contact.add_run(contact_info)
        run_contact.font.name = "Arial"
        run_contact.font.size = Pt(9)
        run_contact.font.color.rgb = RGBColor(75, 85, 99)

        # 2. Sections
        for section in tailored_content.get("sections", []):
            heading = section.get("heading") or section.get("section_type", "Section")
            p_head = doc.add_paragraph()
            p_head.paragraph_format.space_before = Pt(10)
            p_head.paragraph_format.space_after = Pt(3)
            p_head.paragraph_format.keep_with_next = True
            run_head = p_head.add_run(heading.upper())
            run_head.font.name = "Arial"
            run_head.font.size = Pt(11)
            run_head.font.bold = True
            run_head.font.color.rgb = RGBColor(29, 78, 216)

            for item in section.get("items", []):
                title = item.get("title", "")
                org = item.get("organization", "")
                dates = (
                    f"{item.get('start_date', '')} - {item.get('end_date', 'Present')}"
                    if item.get("start_date")
                    else ""
                )
                loc = item.get("location", "")

                p_item = doc.add_paragraph()
                p_item.paragraph_format.space_before = Pt(3)
                p_item.paragraph_format.space_after = Pt(1)
                p_item.paragraph_format.keep_with_next = True

                if title:
                    r_title = p_item.add_run(title)
                    r_title.font.name = "Arial"
                    r_title.font.size = Pt(10)
                    r_title.font.bold = True

                sub_line_parts = [p for p in [org, loc, dates] if p]
                if sub_line_parts:
                    p_sub = doc.add_paragraph()
                    p_sub.paragraph_format.space_after = Pt(2)
                    p_sub.paragraph_format.keep_with_next = True
                    r_sub = p_sub.add_run(" | ".join(sub_line_parts))
                    r_sub.font.name = "Arial"
                    r_sub.font.size = Pt(9)
                    r_sub.font.italic = True
                    r_sub.font.color.rgb = RGBColor(75, 85, 99)

                # Bullets & Description
                has_bullets = False
                for bullet in item.get("bullets", []):
                    bullet_text = bullet if isinstance(bullet, str) else str(bullet)
                    if bullet_text.strip():
                        p_b = doc.add_paragraph(style="List Bullet")
                        p_b.paragraph_format.space_after = Pt(2)
                        r_b = p_b.add_run(bullet_text.strip())
                        r_b.font.name = "Arial"
                        r_b.font.size = Pt(9)
                        has_bullets = True

                if not has_bullets:
                    desc = item.get("description") or item.get("text") or ""
                    if desc:
                        for line in desc.splitlines():
                            if line.strip():
                                p_d = doc.add_paragraph()
                                p_d.paragraph_format.space_after = Pt(2)
                                r_d = p_d.add_run(line.strip())
                                r_d.font.name = "Arial"
                                r_d.font.size = Pt(9)

            if not section.get("items") and section.get("raw_content"):
                p_raw = doc.add_paragraph()
                p_raw.paragraph_format.space_after = Pt(3)
                r_raw = p_raw.add_run(section["raw_content"])
                r_raw.font.name = "Arial"
                r_raw.font.size = Pt(9)

        buffer = io.BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        return buffer.getvalue()


# Global exporter instance
resume_exporter = ResumeExporter()
