import fitz

from dataclasses import dataclass
from typing import Optional


MAX_PAGES = 25
OCR_PAGE_LIMIT = 10
MIN_TEXT_LENGTH = 60


@dataclass
class ExtractionResult:

    text: str
    method: str
    pages: int
    warning: Optional[str] = None


def run_ocr(document):

    try:
        import pytesseract
        from PIL import Image

    except ImportError:
        return "", "OCR dependencies are not installed"

    extracted_pages = []

    try:

        for page_number in range(
            min(len(document), OCR_PAGE_LIMIT)
        ):

            page = document[page_number]

            pix = page.get_pixmap(
                matrix=fitz.Matrix(2, 2),
                alpha=False
            )

            image = Image.frombytes(
                "RGB",
                [pix.width, pix.height],
                pix.samples
            )

            page_text = pytesseract.image_to_string(
                image,
                lang="eng"
            )

            extracted_pages.append(page_text)

        return "\n".join(extracted_pages), None

    except Exception as exc:
        return "", f"OCR failed: {str(exc)[:200]}"


def extract_pdf_text(pdf_bytes: bytes) -> ExtractionResult:

    try:

        document = fitz.open(
            stream=pdf_bytes,
            filetype="pdf"
        )

    except Exception as exc:
        raise ValueError(
            f"Invalid or unreadable PDF: {exc}"
        )

    try:

        if document.needs_pass:
            raise ValueError(
                "Password-protected PDFs are not supported"
            )

        page_count = len(document)

        if page_count == 0:
            raise ValueError("PDF contains no pages")

        if page_count > MAX_PAGES:
            raise ValueError(
                f"Maximum {MAX_PAGES} pages allowed"
            )

        text_pages = []

        for page in document:
            text_pages.append(
                page.get_text("text")
            )

        original_text = "\n".join(text_pages).strip()

        if len(original_text) >= MIN_TEXT_LENGTH:

            return ExtractionResult(
                text=original_text,
                method="TEXT",
                pages=page_count
            )

        # Fallback for scanned PDFs
        ocr_text, warning = run_ocr(document)

        if len(ocr_text.strip()) > len(original_text):

            return ExtractionResult(
                text=ocr_text.strip(),
                method="OCR",
                pages=page_count,
                warning=warning
            )

        return ExtractionResult(
            text=original_text,
            method="NO_TEXT",
            pages=page_count,
            warning=warning or "Unable to extract meaningful text"
        )

    finally:
        document.close()