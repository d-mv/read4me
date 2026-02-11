import re
import time
from pathlib import Path
from typing import Any

from read4me.manifest import ChapterManifest
from read4me.metadata import apply_id3_metadata
from read4me.pipeline import clean_chapter_text
from read4me.resume_cache import load_completed_chapters, save_completed_chapters


def _slugify(value: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return normalized or "chapter"


def generate_chapter_mp3_files(
    manifest: ChapterManifest,
    *,
    output_dir: Path,
    provider: Any,
    locale: str,
    book_title: str = "Untitled",
    author: str = "Unknown",
    cover_image_data: bytes | None = None,
    cover_mime_type: str | None = None,
    request_delay_seconds: float = 1.0,
    max_retries_on_429: int = 5,
    retry_delay_seconds: float = 2.0,
) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    output_files: list[Path] = []
    album = book_title
    cache_file = output_dir / ".read4me-cache.json"
    completed_chapters = load_completed_chapters(cache_file)
    sent_requests = 0

    for chapter in manifest.chapters:
        cleaned_text = clean_chapter_text(chapter.text)
        if not cleaned_text:
            continue
        output_file = output_dir / f"{chapter.index:03d}-{_slugify(chapter.title)}.mp3"
        if chapter.index in completed_chapters and output_file.exists():
            continue
        if sent_requests > 0 and request_delay_seconds > 0:
            time.sleep(request_delay_seconds)
        attempt = 0
        while True:
            try:
                provider.synthesize_to_mp3(cleaned_text, output_file, locale=locale)
                break
            except Exception as error:
                is_rate_limit = getattr(error, "status_code", None) == 429
                if not is_rate_limit or attempt >= max_retries_on_429:
                    raise
                attempt += 1
                time.sleep(retry_delay_seconds)
        apply_id3_metadata(
            output_file,
            title=book_title,
            track_number=chapter.index,
            album=album,
            artist=author,
            cover_image_data=cover_image_data,
            cover_mime_type=cover_mime_type,
        )
        completed_chapters.add(chapter.index)
        save_completed_chapters(cache_file, completed_chapters)
        output_files.append(output_file)
        sent_requests += 1

    return output_files
