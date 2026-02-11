from read4me.cover_artwork import generate_fallback_cover_artwork
from read4me.cover_artwork import extract_embedded_cover_artwork
from pathlib import Path


def test_generate_fallback_cover_artwork_returns_png_bytes() -> None:
    cover_data, mime_type = generate_fallback_cover_artwork(
        title="The Book",
        author="The Author",
    )

    assert mime_type == "image/png"
    assert cover_data.startswith(b"\x89PNG\r\n\x1a\n")


def test_extract_embedded_cover_artwork_uses_pdf_first_page(monkeypatch) -> None:
    monkeypatch.setattr(
        "read4me.cover_artwork.parse_pdf_first_page_artwork",
        lambda _path: (b"pdf-cover", "image/png"),
    )

    cover_data, mime_type = extract_embedded_cover_artwork(Path("book.pdf"), "pdf")

    assert cover_data == b"pdf-cover"
    assert mime_type == "image/png"
