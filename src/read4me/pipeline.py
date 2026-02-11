from dataclasses import dataclass

from read4me.manifest import ChapterManifest


@dataclass(frozen=True)
class ChapterChunk:
    chapter_index: int
    chapter_title: str
    chunk_index: int
    text: str


def clean_chapter_text(text: str) -> str:
    return " ".join(text.split())


def _chunk_text(text: str, max_chars: int) -> list[str]:
    words = text.split(" ")
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    for word in words:
        word_len = len(word)
        added_len = word_len if not current else word_len + 1
        if current and current_len + added_len > max_chars:
            chunks.append(" ".join(current))
            current = [word]
            current_len = word_len
            continue
        current.append(word)
        current_len += added_len

    if current:
        chunks.append(" ".join(current))
    return chunks


def build_chunk_plan(manifest: ChapterManifest, max_chars: int = 3000) -> list[ChapterChunk]:
    chunks: list[ChapterChunk] = []
    for chapter in manifest.chapters:
        cleaned_text = clean_chapter_text(chapter.text)
        if not cleaned_text:
            continue
        text_chunks = _chunk_text(cleaned_text, max_chars=max_chars)
        for chunk_index, text_chunk in enumerate(text_chunks, start=1):
            chunks.append(
                ChapterChunk(
                    chapter_index=chapter.index,
                    chapter_title=chapter.title,
                    chunk_index=chunk_index,
                    text=text_chunk,
                )
            )
    return chunks
