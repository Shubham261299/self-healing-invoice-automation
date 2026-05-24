"""Tesseract-based screenshot validation."""
import pytesseract
from PIL import Image
from pathlib import Path
from src.config import TESSERACT_CMD
from src.logger import get_logger

log = get_logger()

if TESSERACT_CMD:
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD


def extract_text(image_path: Path) -> str:
    """Run OCR on a screenshot and return extracted text."""
    try:
        img = Image.open(image_path)
        text = pytesseract.image_to_string(img)
        return text.strip()
    except Exception as e:
        log.error(f"OCR failed on {image_path}: {e}")
        return ""


def validate_text_present(image_path: Path, expected: str) -> bool:
    """Return True if expected text appears in screenshot."""
    text = extract_text(image_path)
    found = expected.lower() in text.lower()
    log.info(f"OCR validation for '{expected}': {'✓ found' if found else '✗ missing'}")
    return found