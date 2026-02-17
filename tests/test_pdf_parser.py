from pathlib import Path

from read4me.parsers.pdf import PdfChapter, parse_pdf_chapters


class _FakePage:
    def __init__(self, text: str | None) -> None:
        self._text = text

    def extract_text(self) -> str | None:
        return self._text


class _FakeReader:
    def __init__(self, _path: Path) -> None:
        self.pages = [_FakePage("Page one text"), _FakePage("Page two text")]


def test_parse_pdf_chapters_extracts_text_by_page(monkeypatch, tmp_path) -> None:
    pdf_file = tmp_path / "book.pdf"
    pdf_file.write_bytes(b"%PDF-1.0")
    monkeypatch.setattr("read4me.parsers.pdf.PdfReader", _FakeReader)

    chapters = parse_pdf_chapters(pdf_file)

    assert chapters == [
        PdfChapter(title="Page 1", text="Page one text"),
        PdfChapter(title="Page 2", text="Page two text"),
    ]


def test_parse_pdf_chapters_requires_ocr_when_no_text(monkeypatch, tmp_path) -> None:
    class _ReaderWithEmptyPages:
        def __init__(self, _path: Path) -> None:
            self.pages = [_FakePage(""), _FakePage(None)]

    pdf_file = tmp_path / "scan.pdf"
    pdf_file.write_bytes(b"%PDF-1.0")
    monkeypatch.setattr("read4me.parsers.pdf.PdfReader", _ReaderWithEmptyPages)
    monkeypatch.setattr("read4me.parsers.pdf.shutil.which", lambda _name: None)

    try:
        parse_pdf_chapters(pdf_file, ocr_fallback=True)
        assert False, "expected RuntimeError for missing OCR tool"
    except RuntimeError as error:
        assert "ocrmypdf" in str(error)


def test_parse_pdf_chapters_rejects_symbol_garbage_text(monkeypatch, tmp_path) -> None:
    class _ReaderWithGarbageText:
        def __init__(self, _path: Path) -> None:
            self.pages = [_FakePage("-\n./")]

    pdf_file = tmp_path / "garbage.pdf"
    pdf_file.write_bytes(b"%PDF-1.0")
    monkeypatch.setattr("read4me.parsers.pdf.PdfReader", _ReaderWithGarbageText)

    try:
        parse_pdf_chapters(pdf_file)
        assert False, "expected ValueError for non-linguistic extracted PDF text"
    except ValueError as error:
        assert "No extractable PDF text found" in str(error)


def test_parse_pdf_chapters_uses_ocr_fallback_output(monkeypatch, tmp_path) -> None:
    input_pdf = tmp_path / "scan.pdf"
    ocr_pdf = tmp_path / "scan-ocr.pdf"
    input_pdf.write_bytes(b"%PDF-1.0")
    ocr_pdf.write_bytes(b"%PDF-1.0")

    class _ReaderByPath:
        def __init__(self, path: Path) -> None:
            if Path(path).name == "scan.pdf":
                self.pages = [_FakePage("-\n./")]
            else:
                self.pages = [_FakePage("OCR recovered Russian text")]

    monkeypatch.setattr("read4me.parsers.pdf.PdfReader", _ReaderByPath)
    monkeypatch.setattr("read4me.parsers.pdf._run_ocrmypdf", lambda _src: ocr_pdf)

    chapters = parse_pdf_chapters(input_pdf, ocr_fallback=True)

    assert chapters == [PdfChapter(title="Page 1", text="OCR recovered Russian text")]


def test_parse_pdf_chapters_uses_tesseract_when_ocr_pdf_has_no_extractable_text(
    monkeypatch, tmp_path
) -> None:
    input_pdf = tmp_path / "scan.pdf"
    ocr_pdf = tmp_path / "scan-ocr.pdf"
    input_pdf.write_bytes(b"%PDF-1.0")
    ocr_pdf.write_bytes(b"%PDF-1.0")

    class _ReaderByPath:
        def __init__(self, path: Path) -> None:
            if Path(path).name == "scan.pdf":
                self.pages = [_FakePage("-\n./")]
            else:
                self.pages = [_FakePage("")]

    monkeypatch.setattr("read4me.parsers.pdf.PdfReader", _ReaderByPath)
    monkeypatch.setattr("read4me.parsers.pdf._run_ocrmypdf", lambda _src: ocr_pdf)
    monkeypatch.setattr(
        "read4me.parsers.pdf._extract_pdf_chapters_with_tesseract",
        lambda _path: [PdfChapter(title="Page 1", text="Tesseract recovered text")],
    )

    chapters = parse_pdf_chapters(input_pdf, ocr_fallback=True)

    assert chapters == [PdfChapter(title="Page 1", text="Tesseract recovered text")]
