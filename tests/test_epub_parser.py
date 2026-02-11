from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from read4me.parsers.epub import parse_epub_chapters, parse_epub_cover_artwork


def _create_test_epub(epub_path: Path) -> None:
    with ZipFile(epub_path, "w", compression=ZIP_DEFLATED) as archive:
        archive.writestr("mimetype", "application/epub+zip")
        archive.writestr(
            "META-INF/container.xml",
            """<?xml version="1.0"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>
""",
        )
        archive.writestr(
            "OEBPS/content.opf",
            """<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0">
  <manifest>
    <item id="ch1" href="chapter1.xhtml" media-type="application/xhtml+xml"/>
    <item id="ch2" href="chapter2.xhtml" media-type="application/xhtml+xml"/>
  </manifest>
  <spine>
    <itemref idref="ch1"/>
    <itemref idref="ch2"/>
  </spine>
</package>
""",
        )
        archive.writestr(
            "OEBPS/chapter1.xhtml",
            """<html><head><title>Chapter One</title></head>
<body><h1>Chapter One</h1><p>First chapter text.</p></body></html>""",
        )
        archive.writestr(
            "OEBPS/chapter2.xhtml",
            """<html><head><title>Chapter Two</title></head>
<body><h1>Chapter Two</h1><p>Second chapter text.</p></body></html>""",
        )


def _create_test_epub_with_cover(epub_path: Path) -> bytes:
    cover_bytes = b"\x89PNG\r\n\x1a\ncover"
    with ZipFile(epub_path, "w", compression=ZIP_DEFLATED) as archive:
        archive.writestr("mimetype", "application/epub+zip")
        archive.writestr(
            "META-INF/container.xml",
            """<?xml version="1.0"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>
""",
        )
        archive.writestr(
            "OEBPS/content.opf",
            """<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0">
  <metadata>
    <meta name="cover" content="cover-image"/>
  </metadata>
  <manifest>
    <item id="cover-image" href="cover.png" media-type="image/png"/>
  </manifest>
  <spine/>
</package>
""",
        )
        archive.writestr("OEBPS/cover.png", cover_bytes)
    return cover_bytes


def test_parse_epub_chapters_reads_spine_in_order(tmp_path) -> None:
    epub_path = tmp_path / "book.epub"
    _create_test_epub(epub_path)

    chapters = parse_epub_chapters(epub_path)

    assert [chapter.title for chapter in chapters] == ["Chapter One", "Chapter Two"]
    assert chapters[0].text == "Chapter One First chapter text."
    assert chapters[1].text == "Chapter Two Second chapter text."


def test_parse_epub_chapters_raises_on_missing_opf(tmp_path) -> None:
    epub_path = tmp_path / "invalid.epub"
    with ZipFile(epub_path, "w", compression=ZIP_DEFLATED) as archive:
        archive.writestr("mimetype", "application/epub+zip")

    try:
        parse_epub_chapters(epub_path)
        assert False, "expected ValueError for missing OPF"
    except ValueError as error:
        assert "OPF" in str(error)


def test_parse_epub_cover_artwork_extracts_embedded_cover(tmp_path) -> None:
    epub_path = tmp_path / "cover.epub"
    expected_cover = _create_test_epub_with_cover(epub_path)

    cover_data, mime_type = parse_epub_cover_artwork(epub_path)

    assert cover_data == expected_cover
    assert mime_type == "image/png"
