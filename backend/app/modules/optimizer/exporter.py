import io
from typing import Any

import docx
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer


class ResumeExporter:
    """Generates ATS-compliant, single-column PDF and DOCX documents from tailored resume snapshots."""

    def generate_pdf(self, tailored_content: dict[str, Any]) -> bytes:
        """Render a clean, single-column ATS-friendly PDF using ReportLab."""
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

        # Custom ATS Typography Styles
        name_style = ParagraphStyle(
            "ATS_Name",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=18,
            leading=22,
            textColor=HexColor("#1F2937"),
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
            spaceAfter=12,
        )

        section_heading_style = ParagraphStyle(
            "ATS_Heading",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            textColor=HexColor("#2563EB"),
            spaceBefore=10,
            spaceAfter=3,
        )

        item_title_style = ParagraphStyle(
            "ATS_ItemTitle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=13,
            textColor=HexColor("#1F2937"),
        )

        item_sub_style = ParagraphStyle(
            "ATS_ItemSub",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            textColor=HexColor("#4B5563"),
            spaceAfter=3,
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
            or "Professional Resume"
        )
        contact_info = (
            tailored_content.get("contact_info") or "Email: user@example.com | Location: Active"
        )

        story.append(Paragraph(candidate_name, name_style))
        story.append(Paragraph(contact_info, contact_style))
        story.append(HRFlowable(width="100%", thickness=1, color=HexColor("#D1D9E6"), spaceAfter=8))

        # 2. Sections
        sections = tailored_content.get("sections", [])
        for section in sections:
            heading = section.get("heading") or section.get("section_type", "Section")
            story.append(Paragraph(heading.upper(), section_heading_style))
            story.append(
                HRFlowable(width="100%", thickness=0.5, color=HexColor("#E5E7EB"), spaceAfter=5)
            )

            # Items in section
            for item in section.get("items", []):
                title = item.get("title", "")
                org = item.get("organization", "")
                dates = (
                    f"{item.get('start_date', '')} - {item.get('end_date', 'Present')}"
                    if item.get("start_date")
                    else ""
                )
                loc = item.get("location", "")

                sub_line_parts = [p for p in [org, loc, dates] if p]
                sub_line = " | ".join(sub_line_parts)

                if title:
                    story.append(Paragraph(title, item_title_style))
                if sub_line:
                    story.append(Paragraph(sub_line, item_sub_style))

                # Bullets
                for bullet in item.get("bullets", []):
                    bullet_text = bullet if isinstance(bullet, str) else str(bullet)
                    if bullet_text.strip():
                        story.append(Paragraph(f"• {bullet_text.strip()}", bullet_style))

                story.append(Spacer(1, 4))

            # Non-itemized raw content (e.g. Skills block)
            if not section.get("items") and section.get("raw_content"):
                story.append(Paragraph(section["raw_content"], bullet_style))
                story.append(Spacer(1, 4))

        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()

    def generate_docx(self, tailored_content: dict[str, Any]) -> bytes:
        """Render a clean, single-column ATS-friendly DOCX document."""
        doc = docx.Document()

        # Set standard margins (0.75 inch)
        for section in doc.sections:
            section.top_margin = docx.shared.Inches(0.75)
            section.bottom_margin = docx.shared.Inches(0.75)
            section.left_margin = docx.shared.Inches(0.75)
            section.right_margin = docx.shared.Inches(0.75)

        # 1. Header
        candidate_name = (
            tailored_content.get("full_name")
            or tailored_content.get("candidate_name")
            or "Professional Resume"
        )
        contact_info = (
            tailored_content.get("contact_info") or "Email: user@example.com | Location: Active"
        )

        p_name = doc.add_paragraph()
        p_name.alignment = docx.enum.text.WD_ALIGN_PARAGRAPH.CENTER
        run_name = p_name.add_run(candidate_name)
        run_name.font.name = "Arial"
        run_name.font.size = docx.shared.Pt(18)
        run_name.font.bold = True

        p_contact = doc.add_paragraph()
        p_contact.alignment = docx.enum.text.WD_ALIGN_PARAGRAPH.CENTER
        run_contact = p_contact.add_run(contact_info)
        run_contact.font.name = "Arial"
        run_contact.font.size = docx.shared.Pt(9)
        run_contact.font.color.rgb = docx.shared.RGBColor(75, 85, 99)

        # 2. Sections
        for section in tailored_content.get("sections", []):
            heading = section.get("heading") or section.get("section_type", "Section")
            p_head = doc.add_paragraph()
            p_head.paragraph_format.space_before = docx.shared.Pt(10)
            p_head.paragraph_format.space_after = docx.shared.Pt(3)
            run_head = p_head.add_run(heading.upper())
            run_head.font.name = "Arial"
            run_head.font.size = docx.shared.Pt(11)
            run_head.font.bold = True
            run_head.font.color.rgb = docx.shared.RGBColor(37, 99, 235)

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
                p_item.paragraph_format.space_before = docx.shared.Pt(3)
                p_item.paragraph_format.space_after = docx.shared.Pt(1)

                if title:
                    r_title = p_item.add_run(title)
                    r_title.font.name = "Arial"
                    r_title.font.size = docx.shared.Pt(10)
                    r_title.font.bold = True

                sub_line_parts = [p for p in [org, loc, dates] if p]
                if sub_line_parts:
                    p_sub = doc.add_paragraph()
                    p_sub.paragraph_format.space_after = docx.shared.Pt(2)
                    r_sub = p_sub.add_run(" | ".join(sub_line_parts))
                    r_sub.font.name = "Arial"
                    r_sub.font.size = docx.shared.Pt(9)
                    r_sub.font.italic = True
                    r_sub.font.color.rgb = docx.shared.RGBColor(75, 85, 99)

                # Bullets
                for bullet in item.get("bullets", []):
                    bullet_text = bullet if isinstance(bullet, str) else str(bullet)
                    if bullet_text.strip():
                        p_b = doc.add_paragraph(style="List Bullet")
                        p_b.paragraph_format.space_after = docx.shared.Pt(2)
                        r_b = p_b.add_run(bullet_text.strip())
                        r_b.font.name = "Arial"
                        r_b.font.size = docx.shared.Pt(9)

            if not section.get("items") and section.get("raw_content"):
                p_raw = doc.add_paragraph()
                p_raw.paragraph_format.space_after = docx.shared.Pt(3)
                r_raw = p_raw.add_run(section["raw_content"])
                r_raw.font.name = "Arial"
                r_raw.font.size = docx.shared.Pt(9)

        buffer = io.BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        return buffer.getvalue()


# Global exporter instance
resume_exporter = ResumeExporter()
