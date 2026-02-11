from pathlib import Path
import json

from read4me.audio_generation import generate_chapter_mp3_files
from read4me.manifest import Chapter, ChapterManifest


def test_generate_chapter_mp3_files_creates_one_file_per_chapter(tmp_path) -> None:
    class _FakeProvider:
        def __init__(self) -> None:
            self.calls = []

        def synthesize_to_mp3(self, text: str, output_file: Path, *, locale: str) -> None:
            self.calls.append((text, output_file.name, locale))
            output_file.write_bytes(b"mp3")

    manifest = ChapterManifest(
        source_path=Path("book.epub"),
        source_format="epub",
        chapters=[
            Chapter(index=1, title="Chapter One", text="First chapter text."),
            Chapter(index=2, title="Chapter Two!", text="Second chapter text."),
        ],
    )
    provider = _FakeProvider()

    output_files = generate_chapter_mp3_files(
        manifest,
        output_dir=tmp_path,
        provider=provider,
        locale="en-US",
    )

    assert [file.name for file in output_files] == [
        "001-chapter-one.mp3",
        "002-chapter-two.mp3",
    ]
    assert provider.calls == [
        ("First chapter text.", "001-chapter-one.mp3", "en-US"),
        ("Second chapter text.", "002-chapter-two.mp3", "en-US"),
    ]


def test_generate_chapter_mp3_files_skips_empty_cleaned_text(tmp_path) -> None:
    class _FakeProvider:
        def synthesize_to_mp3(self, text: str, output_file: Path, *, locale: str) -> None:
            output_file.write_bytes(b"mp3")

    manifest = ChapterManifest(
        source_path=Path("book.fb2"),
        source_format="fb2",
        chapters=[Chapter(index=1, title="Intro", text=" \n\t ")],
    )

    output_files = generate_chapter_mp3_files(
        manifest,
        output_dir=tmp_path,
        provider=_FakeProvider(),
        locale="en-US",
    )

    assert output_files == []


def test_generate_chapter_mp3_files_applies_id3_metadata(monkeypatch, tmp_path) -> None:
    class _FakeProvider:
        def synthesize_to_mp3(self, text: str, output_file: Path, *, locale: str) -> None:
            output_file.write_bytes(b"mp3")

    calls = []

    def _fake_apply_id3_metadata(
        mp3_file: Path,
        *,
        title: str,
        track_number: int,
        album: str,
        artist: str,
        cover_image_data: bytes | None = None,
        cover_mime_type: str | None = None,
    ):
        calls.append(
            (
                mp3_file.name,
                title,
                track_number,
                album,
                artist,
                cover_image_data,
                cover_mime_type,
            )
        )

    monkeypatch.setattr("read4me.audio_generation.apply_id3_metadata", _fake_apply_id3_metadata)

    manifest = ChapterManifest(
        source_path=Path("book.epub"),
        source_format="epub",
        chapters=[Chapter(index=1, title="Chapter One", text="Text")],
    )

    generate_chapter_mp3_files(
        manifest,
        output_dir=tmp_path,
        provider=_FakeProvider(),
        locale="en-US",
        book_title="My Book",
        author="Some Author",
        cover_image_data=b"img",
        cover_mime_type="image/png",
    )

    assert calls == [
        ("001-chapter-one.mp3", "My Book", 1, "My Book", "Some Author", b"img", "image/png")
    ]


def test_generate_chapter_mp3_files_resumes_from_cache(monkeypatch, tmp_path) -> None:
    class _FakeProvider:
        def __init__(self) -> None:
            self.calls = []

        def synthesize_to_mp3(self, text: str, output_file: Path, *, locale: str) -> None:
            self.calls.append(output_file.name)
            output_file.write_bytes(b"mp3")

    monkeypatch.setattr(
        "read4me.audio_generation.apply_id3_metadata",
        lambda *_args, **_kwargs: None,
    )

    (tmp_path / "001-chapter-one.mp3").write_bytes(b"mp3")
    cache_file = tmp_path / ".read4me-cache.json"
    cache_file.write_text(json.dumps({"completed_chapters": [1]}), encoding="utf-8")

    manifest = ChapterManifest(
        source_path=Path("book.epub"),
        source_format="epub",
        chapters=[
            Chapter(index=1, title="Chapter One", text="First text"),
            Chapter(index=2, title="Chapter Two", text="Second text"),
        ],
    )
    provider = _FakeProvider()

    output_files = generate_chapter_mp3_files(
        manifest,
        output_dir=tmp_path,
        provider=provider,
        locale="en-US",
    )

    assert [path.name for path in output_files] == ["002-chapter-two.mp3"]
    assert provider.calls == ["002-chapter-two.mp3"]
    cache_data = json.loads(cache_file.read_text(encoding="utf-8"))
    assert cache_data["completed_chapters"] == [1, 2]


def test_generate_chapter_mp3_files_waits_between_requests(monkeypatch, tmp_path) -> None:
    class _FakeProvider:
        def __init__(self) -> None:
            self.calls = []

        def synthesize_to_mp3(self, text: str, output_file: Path, *, locale: str) -> None:
            self.calls.append(output_file.name)
            output_file.write_bytes(b"mp3")

    sleeps = []
    monkeypatch.setattr("read4me.audio_generation.apply_id3_metadata", lambda *_args, **_kwargs: None)
    monkeypatch.setattr("read4me.audio_generation.time.sleep", lambda seconds: sleeps.append(seconds))

    manifest = ChapterManifest(
        source_path=Path("book.epub"),
        source_format="epub",
        chapters=[
            Chapter(index=1, title="One", text="one"),
            Chapter(index=2, title="Two", text="two"),
        ],
    )
    provider = _FakeProvider()

    generate_chapter_mp3_files(
        manifest,
        output_dir=tmp_path,
        provider=provider,
        locale="en-US",
        request_delay_seconds=1.5,
    )

    assert provider.calls == ["001-one.mp3", "002-two.mp3"]
    assert sleeps == [1.5]


def test_generate_chapter_mp3_files_retries_on_429(monkeypatch, tmp_path) -> None:
    class _RateLimitError(Exception):
        status_code = 429

    class _FakeProvider:
        def __init__(self) -> None:
            self.calls = 0

        def synthesize_to_mp3(self, text: str, output_file: Path, *, locale: str) -> None:
            self.calls += 1
            if self.calls == 1:
                raise _RateLimitError("too many requests")
            output_file.write_bytes(b"mp3")

    sleeps = []
    monkeypatch.setattr("read4me.audio_generation.apply_id3_metadata", lambda *_args, **_kwargs: None)
    monkeypatch.setattr("read4me.audio_generation.time.sleep", lambda seconds: sleeps.append(seconds))

    manifest = ChapterManifest(
        source_path=Path("book.epub"),
        source_format="epub",
        chapters=[Chapter(index=1, title="One", text="one")],
    )
    provider = _FakeProvider()

    output_files = generate_chapter_mp3_files(
        manifest,
        output_dir=tmp_path,
        provider=provider,
        locale="en-US",
        max_retries_on_429=2,
        retry_delay_seconds=2.0,
        request_delay_seconds=0.0,
    )

    assert [path.name for path in output_files] == ["001-one.mp3"]
    assert provider.calls == 2
    assert sleeps == [2.0]
