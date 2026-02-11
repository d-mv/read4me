from pathlib import Path

from read4me.manifest import Chapter, ChapterManifest, build_chapter_manifest


def test_build_manifest_for_epub(monkeypatch, tmp_path) -> None:
    epub_file = tmp_path / "book.epub"
    epub_file.write_bytes(b"epub")

    def _fake_parse_epub_chapters(_path: Path):
        return [type("ChapterLike", (), {"title": "Ch 1", "text": "Hello"})()]

    monkeypatch.setattr("read4me.manifest.parse_epub_chapters", _fake_parse_epub_chapters)

    manifest = build_chapter_manifest(epub_file)

    assert manifest == ChapterManifest(
        source_path=epub_file,
        source_format="epub",
        chapters=[Chapter(index=1, title="Ch 1", text="Hello")],
    )


def test_build_manifest_for_pdf_passes_ocr_flag(monkeypatch, tmp_path) -> None:
    pdf_file = tmp_path / "book.pdf"
    pdf_file.write_bytes(b"%PDF-1.0")

    def _fake_parse_pdf_chapters(_path: Path, *, ocr_fallback: bool):
        assert ocr_fallback is True
        return [type("ChapterLike", (), {"title": "Page 1", "text": "Text"})()]

    monkeypatch.setattr("read4me.manifest.parse_pdf_chapters", _fake_parse_pdf_chapters)

    manifest = build_chapter_manifest(pdf_file, ocr_fallback=True)

    assert manifest.chapters[0].title == "Page 1"
    assert manifest.source_format == "pdf"


def test_build_manifest_rejects_unsupported_suffix(tmp_path) -> None:
    unknown_file = tmp_path / "book.txt"
    unknown_file.write_text("x", encoding="utf-8")

    try:
        build_chapter_manifest(unknown_file)
        assert False, "expected ValueError for unsupported format"
    except ValueError as error:
        assert "Unsupported input format" in str(error)
