import os
from typing import Any

try:
    from PIL import Image  # noqa: F401
except Exception:  # pragma: no cover - optional dependency guard
    Image = None

try:
    from pypdf import PdfReader
except Exception:  # pragma: no cover - optional dependency guard
    PdfReader = None

try:
    import easyocr
except Exception:  # pragma: no cover - optional dependency guard
    easyocr = None

# Initialize EasyOCR reader lazily (English language)
_ocr_reader = None


def get_ocr_reader():
    global _ocr_reader
    if _ocr_reader is None:
        if easyocr is None:
            raise ImportError("easyocr is not installed")
        # GPU=False ensures stability if CUDA isn't configured
        _ocr_reader = easyocr.Reader(["en"], gpu=False)
    return _ocr_reader

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extracts raw text directly from searchable PDF files."""
    extracted_text = ""
    if PdfReader is None:
        return extracted_text
    try:
        reader = PdfReader(pdf_path)
        for page in reader.pages:
            text = page.extract_text()
            if text:
                extracted_text += text + "\n"
    except Exception as e:
        from app.core.logging import get_logger
        get_logger(__name__).warning("Error reading PDF with PyPDF: %s", e)
    return extracted_text.strip()

def extract_text_from_image(image_path: str) -> str:
    """Extracts text from scanned medical images/lab reports using EasyOCR."""
    try:
        reader = get_ocr_reader()
        # EasyOCR extracts detailed text blocks
        results = reader.readtext(image_path, detail=0)
        return "\n".join(results)
    except Exception as e:
        from app.core.logging import get_logger
        get_logger(__name__).warning("Error executing EasyOCR: %s", e)
        return ""

def process_medical_report(file_path: str) -> str:
    """
    Main entry point for medical report ingestion.
    Supports both PDF and Image formats (PNG, JPG, JPEG).
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        text = extract_text_from_pdf(file_path)
        # Fallback to OCR if PDF contains scanned image rather than text
        if not text:
            from app.core.logging import get_logger
            get_logger(__name__).info("PDF has no embedded text. Running fallback OCR...")
            text = extract_text_from_image(file_path)
    elif ext in [".png", ".jpg", ".jpeg", ".tiff"]:
        text = extract_text_from_image(file_path)
    else:
        raise ValueError(f"Unsupported file format: {ext}")

    return text.strip()

def extract_text(file_path: str) -> str:
    """Compatibility entry point used by the agents."""
    return process_medical_report(file_path)


class OCRService:
    """
    Thin wrapper around OCR helper functions.
    """
    def __init__(self):
        self.logger = None

    def extract_text(self, file_path: str) -> str:
        """Extract text from a file (PDF or image)."""
        # prefer module-level helpers but expose a single method
        try:
            return process_medical_report(file_path)
        except Exception as exc:
            from app.core.logging import get_logger
            if self.logger is None:
                self.logger = get_logger(__name__)
            self.logger.exception("OCR extraction failed: %s", exc)
            return ""

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        return extract_text_from_pdf(pdf_path)

    def extract_text_from_image(self, image_path: str) -> str:
        return extract_text_from_image(image_path)