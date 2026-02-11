from dataclasses import dataclass
from pathlib import Path

from read4me.parsers.epub import parse_epub_chapters
from read4me.parsers.fb2 import parse_fb2_chapters
from read4me.parsers.pdf import parse_pdf_chapters

SUPPORTED_MANIFEST_SUFFIXES = {".pdf", ".epub", ".fb2"}


@dataclass(frozen=True)
class Chapter:
    index: int
    title: str
    text: str


@dataclass(frozen=True)
class ChapterManifest:
    source_path: Path
    source_format: str
    chapters: list[Chapter]


def _normalize_chapters(raw_chapters: list[object]) -> list[Chapter]:
    chapters: list[Chapter] = []
    for index, chapter in enumerate(raw_chapters, start=1):
        title = getattr(chapter, "title")
        text = getattr(chapter, "text")
        chapters.append(Chapter(index=index, title=title, text=text))
    return chapters


def build_chapter_manifest(
    input_file: Path, *, ocr_fallback: bool = False
) -> ChapterManifest:
    suffix = input_file.suffix.lower()
    if suffix not in SUPPORTED_MANIFEST_SUFFIXES:
        raise ValueError("Unsupported input format. Use .pdf, .epub, or .fb2.")

    if suffix == ".epub":
        raw_chapters = parse_epub_chapters(input_file)
        return ChapterManifest(
            source_path=input_file,
            source_format="epub",
            chapters=_normalize_chapters(raw_chapters),
        )
    if suffix == ".fb2":
        raw_chapters = parse_fb2_chapters(input_file)
        return ChapterManifest(
            source_path=input_file,
            source_format="fb2",
            chapters=_normalize_chapters(raw_chapters),
        )

    raw_chapters = parse_pdf_chapters(input_file, ocr_fallback=ocr_fallback)
    return ChapterManifest(
        source_path=input_file,
        source_format="pdf",
        chapters=_normalize_chapters(raw_chapters),
    )
