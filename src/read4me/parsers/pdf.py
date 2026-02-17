from dataclasses import dataclass
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

from pypdf import PdfReader


@dataclass(frozen=True)
class PdfChapter:
    title: str
    text: str


def _looks_meaningful_text(text: str) -> bool:
    stripped = text.strip()
    if len(stripped) < 8:
        return False
    letters = sum(1 for ch in stripped if ch.isalpha())
    return letters >= 3


def _extract_pdf_chapters(pdf_path: Path) -> list[PdfChapter]:
    reader = PdfReader(pdf_path)
    chapters: list[PdfChapter] = []
    for index, page in enumerate(reader.pages, start=1):
        text = (page.extract_text() or "").strip()
        if not text or not _looks_meaningful_text(text):
            continue
        chapters.append(PdfChapter(title=f"Page {index}", text=text))
    return chapters


def parse_pdf_first_page_artwork(pdf_path: Path) -> tuple[bytes, str] | tuple[None, None]:
    try:
        import fitz
    except ImportError:
        return None, None

    document = fitz.open(str(pdf_path))
    try:
        if document.page_count < 1:
            return None, None
        page = document.load_page(0)
        pixmap = page.get_pixmap(alpha=False)
        return pixmap.tobytes("png"), "image/png"
    finally:
        document.close()


def _run_ocrmypdf(pdf_path: Path, *, language: str = "rus+eng") -> Path:
    if shutil.which("ocrmypdf") is None:
        raise RuntimeError(
            "ocrmypdf is not installed. Install ocrmypdf + tesseract to use --ocr-fallback."
        )

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
        output_path = Path(temp_file.name)

    try:
        subprocess.run(
            [
                "ocrmypdf",
                "--force-ocr",
                "-l",
                language,
                str(pdf_path),
                str(output_path),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as error:
        if output_path.exists():
            output_path.unlink(missing_ok=True)
        raise RuntimeError(f"OCR fallback failed: {error.stderr.strip()}") from error
    return output_path


def _extract_pdf_chapters_with_tesseract(pdf_path: Path, *, language: str = "rus+eng") -> list[PdfChapter]:
    if shutil.which("tesseract") is None:
        return []
    try:
        import fitz
    except ImportError:
        return []

    chapters: list[PdfChapter] = []
    document = fitz.open(str(pdf_path))
    try:
        for index in range(document.page_count):
            page = document.load_page(index)
            pixmap = page.get_pixmap(alpha=False, dpi=300)
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
                image_path = Path(temp_file.name)
            try:
                pixmap.save(str(image_path))
                result = subprocess.run(
                    ["tesseract", str(image_path), "stdout", "-l", language, "--psm", "11"],
                    check=True,
                    capture_output=True,
                    text=True,
                )
                text = result.stdout.strip()
            except subprocess.CalledProcessError:
                continue
            finally:
                image_path.unlink(missing_ok=True)
            if text and _looks_meaningful_text(text):
                chapters.append(PdfChapter(title=f"Page {index + 1}", text=text))
    finally:
        document.close()
    return chapters


def parse_pdf_chapters(pdf_path: Path, *, ocr_fallback: bool = False) -> list[PdfChapter]:
    chapters = _extract_pdf_chapters(pdf_path)

    if chapters:
        return chapters
    if ocr_fallback:
        ocr_pdf_path = _run_ocrmypdf(pdf_path)
        try:
            ocr_chapters = _extract_pdf_chapters(ocr_pdf_path)
            if not ocr_chapters:
                ocr_chapters = _extract_pdf_chapters_with_tesseract(ocr_pdf_path)
        finally:
            if ocr_pdf_path.exists():
                os.unlink(ocr_pdf_path)
        if ocr_chapters:
            return ocr_chapters
        raise ValueError("OCR fallback completed but no extractable PDF text found")
    raise ValueError("No extractable PDF text found")
