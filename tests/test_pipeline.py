from pathlib import Path

from read4me.manifest import Chapter, ChapterManifest
from read4me.pipeline import ChapterChunk, build_chunk_plan, clean_chapter_text


def test_clean_chapter_text_collapses_whitespace() -> None:
    raw_text = "  First line.\n\nSecond\tline.   Third   line.  "

    cleaned = clean_chapter_text(raw_text)

    assert cleaned == "First line. Second line. Third line."


def test_build_chunk_plan_splits_text_by_max_chars() -> None:
    manifest = ChapterManifest(
        source_path=Path("book.epub"),
        source_format="epub",
        chapters=[Chapter(index=1, title="Ch 1", text="alpha beta gamma delta")],
    )

    chunks = build_chunk_plan(manifest, max_chars=11)

    assert chunks == [
        ChapterChunk(chapter_index=1, chapter_title="Ch 1", chunk_index=1, text="alpha beta"),
        ChapterChunk(chapter_index=1, chapter_title="Ch 1", chunk_index=2, text="gamma delta"),
    ]


def test_build_chunk_plan_drops_empty_chapters_after_cleanup() -> None:
    manifest = ChapterManifest(
        source_path=Path("book.fb2"),
        source_format="fb2",
        chapters=[Chapter(index=1, title="Ch 1", text=" \n\t ")],
    )

    chunks = build_chunk_plan(manifest, max_chars=100)

    assert chunks == []
