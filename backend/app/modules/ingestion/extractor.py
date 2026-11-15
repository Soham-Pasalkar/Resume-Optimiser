import io
import logging

from docx import Document
from pdfplumber import open as open_pdf
from pypdf import PdfReader

logger = logging.getLogger(__name__)


class DocumentExtractor:
    """Extracts raw text and structure from PDF and DOCX documents with OCR fallback."""

    MIN_CHARS_PER_PAGE_FOR_DIGITAL = 50

    @classmethod
    def extract_from_pdf(cls, file_bytes: bytes) -> tuple[str, bool]:
        """Extract text from PDF. If character density is low, attempt OCR fallback.
        Returns: (extracted_text, ocr_applied)
        """
        extracted_pages = []
        is_scanned = False
        ocr_applied = False

        try:
            # First pass: High-speed extraction via pdfplumber
            with open_pdf(io.BytesIO(file_bytes)) as pdf:
                total_pages = len(pdf.pages)
                for _page_idx, page in enumerate(pdf.pages):
                    text = page.extract_text() or ""
                    extracted_pages.append(text)

            combined_text = "\n\n".join(extracted_pages).strip()
            avg_chars_per_page = len(combined_text) / total_pages if total_pages > 0 else 0

            if avg_chars_per_page < cls.MIN_CHARS_PER_PAGE_FOR_DIGITAL:
                is_scanned = True
        except Exception as exc:
            logger.warning(
                f"pdfplumber extraction encountered error: {exc}. Trying pypdf fallback."
            )
            try:
                reader = PdfReader(io.BytesIO(file_bytes))
                pages = [page.extract_text() or "" for page in reader.pages]
                combined_text = "\n\n".join(pages).strip()
                if len(combined_text) < 50:
                    is_scanned = True
            except Exception as e:
                logger.error(f"pypdf fallback failed: {e}")
                is_scanned = True
                combined_text = ""

        # OCR Fallback for scanned resumes
        if is_scanned:
            try:
                import pytesseract

                ocr_pages = []
                with open_pdf(io.BytesIO(file_bytes)) as pdf:
                    for page in pdf.pages:
                        # Convert page to image
                        page_image = page.to_image(resolution=200).original
                        ocr_text = pytesseract.image_to_string(page_image)
                        ocr_pages.append(ocr_text)

                ocr_result = "\n\n".join(ocr_pages).strip()
                if len(ocr_result) > len(combined_text):
                    combined_text = ocr_result
                    ocr_applied = True
            except Exception as ocr_err:
                logger.info(
                    f"OCR fallback skipped or tesseract binary unavailable: {ocr_err}. Retaining digital text."
                )

        return combined_text, ocr_applied

    @classmethod
    def extract_from_docx(cls, file_bytes: bytes) -> str:
        """Extract text and bullet lists from DOCX document."""
        doc = Document(io.BytesIO(file_bytes))
        paragraphs = []

        # Extract paragraphs with bullet notation preservation
        for p in doc.paragraphs:
            text = p.text.strip()
            if not text:
                continue
            # Preserve bullet indicators if styled as List Bullet
            if p.style and "Bullet" in p.style.name:
                paragraphs.append(f"• {text}")
            else:
                paragraphs.append(text)

        # Extract text from tables if present
        for table in doc.tables:
            for row in table.rows:
                row_texts = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                if row_texts:
                    paragraphs.append(" | ".join(row_texts))

        return "\n\n".join(paragraphs).strip()
