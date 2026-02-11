from typer.testing import CliRunner

from read4me.manifest import Chapter, ChapterManifest
from read4me.cli import app


def test_help_lists_convert_command() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Commands" in result.stdout
    assert "convert" in result.stdout
    assert "inspect" in result.stdout
    assert "voices" in result.stdout


def test_convert_fails_for_missing_input_file(tmp_path) -> None:
    runner = CliRunner()
    output_dir = tmp_path / "out"
    missing_file = tmp_path / "missing.epub"

    result = runner.invoke(app, ["convert", str(missing_file), "--out", str(output_dir)])

    assert result.exit_code != 0
    assert "Input file does not exist" in result.output


def test_convert_fails_for_unsupported_format(tmp_path) -> None:
    runner = CliRunner()
    input_file = tmp_path / "book.txt"
    input_file.write_text("hello", encoding="utf-8")
    output_dir = tmp_path / "out"

    result = runner.invoke(app, ["convert", str(input_file), "--out", str(output_dir)])

    assert result.exit_code != 0
    assert "Unsupported input format" in result.output


def test_convert_creates_output_dir_for_supported_input(monkeypatch, tmp_path) -> None:
    runner = CliRunner()
    input_file = tmp_path / "book.epub"
    input_file.write_bytes(b"epub-data")
    output_dir = tmp_path / "out"

    def _fake_build_manifest(*_args, **_kwargs):
        return type("ManifestLike", (), {"chapters": []})()

    monkeypatch.setattr("read4me.cli.build_chapter_manifest", _fake_build_manifest)

    result = runner.invoke(app, ["convert", str(input_file), "--out", str(output_dir)])

    assert result.exit_code == 0
    assert output_dir.exists()
    assert "Queued conversion" in result.stdout


def test_convert_accepts_ocr_fallback_flag_for_pdf(monkeypatch, tmp_path) -> None:
    runner = CliRunner()
    input_file = tmp_path / "book.pdf"
    input_file.write_bytes(b"%PDF-1.0")
    output_dir = tmp_path / "out"

    def _fake_build_chapter_manifest(_path, *, ocr_fallback: bool):
        assert ocr_fallback is True
        return type("ManifestLike", (), {"chapters": []})()

    monkeypatch.setattr("read4me.cli.build_chapter_manifest", _fake_build_chapter_manifest)

    result = runner.invoke(
        app,
        ["convert", str(input_file), "--out", str(output_dir), "--ocr-fallback"],
    )

    assert result.exit_code == 0


def test_convert_generates_mp3_files_when_chapters_exist(monkeypatch, tmp_path) -> None:
    runner = CliRunner()
    input_file = tmp_path / "book.fb2"
    input_file.write_text("<FictionBook/>", encoding="utf-8")
    output_dir = tmp_path / "out"
    monkeypatch.setenv("READ4ME_OPENAI_API_KEY", "test-key")

    manifest = ChapterManifest(
        source_path=input_file,
        source_format="fb2",
        chapters=[Chapter(index=1, title="Chapter One", text="Hello world")],
    )

    monkeypatch.setattr("read4me.cli.build_chapter_manifest", lambda *_args, **_kwargs: manifest)
    monkeypatch.setattr(
        "read4me.cli.OpenAITTSProvider",
        lambda **kwargs: type("Provider", (), {"kwargs": kwargs})(),
    )

    def _fake_generate(
        *,
        manifest,
        output_dir,
        provider,
        locale,
        request_delay_seconds,
        max_retries_on_429,
        retry_delay_seconds,
        book_title,
        author,
        cover_image_data,
        cover_mime_type,
    ):
        assert len(manifest.chapters) == 1
        assert locale == "en-US"
        assert getattr(provider, "kwargs")["api_key"] == "test-key"
        assert request_delay_seconds == 1.0
        assert max_retries_on_429 == 5
        assert retry_delay_seconds == 2.0
        assert book_title == "Untitled"
        assert author == "Unknown"
        assert cover_image_data is not None
        assert cover_mime_type == "image/png"
        return [output_dir / "001-chapter-one.mp3"]

    monkeypatch.setattr("read4me.cli.generate_chapter_mp3_files", _fake_generate)

    result = runner.invoke(app, ["convert", str(input_file), "--out", str(output_dir)])

    assert result.exit_code == 0
    assert "Generated 1 MP3 files" in result.stdout


def test_convert_forwards_custom_locale_to_generation(monkeypatch, tmp_path) -> None:
    runner = CliRunner()
    input_file = tmp_path / "book.fb2"
    input_file.write_text("<FictionBook/>", encoding="utf-8")
    output_dir = tmp_path / "out"
    monkeypatch.setenv("READ4ME_OPENAI_API_KEY", "test-key")

    manifest = ChapterManifest(
        source_path=input_file,
        source_format="fb2",
        chapters=[Chapter(index=1, title="Chapter One", text="Privet mir")],
    )

    monkeypatch.setattr("read4me.cli.build_chapter_manifest", lambda *_args, **_kwargs: manifest)
    monkeypatch.setattr(
        "read4me.cli.OpenAITTSProvider",
        lambda **kwargs: type("Provider", (), {"kwargs": kwargs})(),
    )

    def _fake_generate(
        *,
        manifest,
        output_dir,
        provider,
        locale,
        request_delay_seconds,
        max_retries_on_429,
        retry_delay_seconds,
        book_title,
        author,
        cover_image_data,
        cover_mime_type,
    ):
        assert locale == "ru-RU"
        assert request_delay_seconds == 1.0
        assert max_retries_on_429 == 5
        assert retry_delay_seconds == 2.0
        assert book_title == "Untitled"
        assert author == "Unknown"
        assert cover_image_data is not None
        assert cover_mime_type == "image/png"
        return [output_dir / "001-chapter-one.mp3"]

    monkeypatch.setattr("read4me.cli.generate_chapter_mp3_files", _fake_generate)

    result = runner.invoke(
        app,
        ["convert", str(input_file), "--out", str(output_dir), "--locale", "ru-RU"],
    )

    assert result.exit_code == 0


def test_convert_forwards_rate_limit_options(monkeypatch, tmp_path) -> None:
    runner = CliRunner()
    input_file = tmp_path / "book.fb2"
    input_file.write_text("<FictionBook/>", encoding="utf-8")
    output_dir = tmp_path / "out"
    monkeypatch.setenv("READ4ME_OPENAI_API_KEY", "test-key")

    manifest = ChapterManifest(
        source_path=input_file,
        source_format="fb2",
        chapters=[Chapter(index=1, title="Chapter One", text="Hello world")],
    )

    monkeypatch.setattr("read4me.cli.build_chapter_manifest", lambda *_args, **_kwargs: manifest)
    monkeypatch.setattr(
        "read4me.cli.OpenAITTSProvider",
        lambda **kwargs: type("Provider", (), {"kwargs": kwargs})(),
    )

    captured = {}

    def _fake_generate(
        *,
        manifest,
        output_dir,
        provider,
        locale,
        request_delay_seconds,
        max_retries_on_429,
        retry_delay_seconds,
        book_title,
        author,
        cover_image_data,
        cover_mime_type,
    ):
        captured["request_delay_seconds"] = request_delay_seconds
        captured["max_retries_on_429"] = max_retries_on_429
        captured["retry_delay_seconds"] = retry_delay_seconds
        captured["book_title"] = book_title
        captured["author"] = author
        captured["cover_mime_type"] = cover_mime_type
        return [output_dir / "001-chapter-one.mp3"]

    monkeypatch.setattr("read4me.cli.generate_chapter_mp3_files", _fake_generate)

    result = runner.invoke(
        app,
        [
            "convert",
            str(input_file),
            "--out",
            str(output_dir),
            "--request-delay-seconds",
            "2.5",
            "--max-retries-on-429",
            "9",
            "--retry-delay-seconds",
            "4.0",
        ],
    )

    assert result.exit_code == 0
    assert captured == {
        "request_delay_seconds": 2.5,
        "max_retries_on_429": 9,
        "retry_delay_seconds": 4.0,
        "book_title": "Untitled",
        "author": "Unknown",
        "cover_mime_type": "image/png",
    }


def test_convert_forwards_author_and_title(monkeypatch, tmp_path) -> None:
    runner = CliRunner()
    input_file = tmp_path / "book.fb2"
    input_file.write_text("<FictionBook/>", encoding="utf-8")
    output_dir = tmp_path / "out"
    monkeypatch.setenv("READ4ME_OPENAI_API_KEY", "test-key")

    manifest = ChapterManifest(
        source_path=input_file,
        source_format="fb2",
        chapters=[Chapter(index=1, title="Chapter One", text="Hello world")],
    )

    monkeypatch.setattr("read4me.cli.build_chapter_manifest", lambda *_args, **_kwargs: manifest)
    monkeypatch.setattr(
        "read4me.cli.OpenAITTSProvider",
        lambda **kwargs: type("Provider", (), {"kwargs": kwargs})(),
    )

    captured = {}

    def _fake_generate(
        *,
        manifest,
        output_dir,
        provider,
        locale,
        request_delay_seconds,
        max_retries_on_429,
        retry_delay_seconds,
        book_title,
        author,
        cover_image_data,
        cover_mime_type,
    ):
        captured["book_title"] = book_title
        captured["author"] = author
        captured["cover_mime_type"] = cover_mime_type
        return [output_dir / "001-chapter-one.mp3"]

    monkeypatch.setattr("read4me.cli.generate_chapter_mp3_files", _fake_generate)

    result = runner.invoke(
        app,
        [
            "convert",
            str(input_file),
            "--out",
            str(output_dir),
            "--title",
            "Book Name",
            "--author",
            "Author Name",
        ],
    )

    assert result.exit_code == 0
    assert captured == {
        "book_title": "Book Name",
        "author": "Author Name",
        "cover_mime_type": "image/png",
    }


def test_convert_uses_embedded_cover_when_available(monkeypatch, tmp_path) -> None:
    runner = CliRunner()
    input_file = tmp_path / "book.epub"
    input_file.write_bytes(b"epub")
    output_dir = tmp_path / "out"
    monkeypatch.setenv("READ4ME_OPENAI_API_KEY", "test-key")

    manifest = ChapterManifest(
        source_path=input_file,
        source_format="epub",
        chapters=[Chapter(index=1, title="Chapter One", text="Hello world")],
    )

    monkeypatch.setattr("read4me.cli.build_chapter_manifest", lambda *_args, **_kwargs: manifest)
    monkeypatch.setattr(
        "read4me.cli.OpenAITTSProvider",
        lambda **kwargs: type("Provider", (), {"kwargs": kwargs})(),
    )
    monkeypatch.setattr(
        "read4me.cli.extract_embedded_cover_artwork",
        lambda *_args, **_kwargs: (b"cover-bytes", "image/jpeg"),
    )

    captured = {}

    def _fake_generate(
        *,
        manifest,
        output_dir,
        provider,
        locale,
        request_delay_seconds,
        max_retries_on_429,
        retry_delay_seconds,
        book_title,
        author,
        cover_image_data,
        cover_mime_type,
    ):
        captured["cover_image_data"] = cover_image_data
        captured["cover_mime_type"] = cover_mime_type
        return [output_dir / "001-chapter-one.mp3"]

    monkeypatch.setattr("read4me.cli.generate_chapter_mp3_files", _fake_generate)

    result = runner.invoke(app, ["convert", str(input_file), "--out", str(output_dir)])

    assert result.exit_code == 0
    assert captured == {"cover_image_data": b"cover-bytes", "cover_mime_type": "image/jpeg"}


def test_convert_uses_pdf_first_page_cover(monkeypatch, tmp_path) -> None:
    runner = CliRunner()
    input_file = tmp_path / "book.pdf"
    input_file.write_bytes(b"%PDF-1.0")
    output_dir = tmp_path / "out"
    monkeypatch.setenv("READ4ME_OPENAI_API_KEY", "test-key")

    manifest = ChapterManifest(
        source_path=input_file,
        source_format="pdf",
        chapters=[Chapter(index=1, title="Page 1", text="Hello world")],
    )

    monkeypatch.setattr("read4me.cli.build_chapter_manifest", lambda *_args, **_kwargs: manifest)
    monkeypatch.setattr(
        "read4me.cli.OpenAITTSProvider",
        lambda **kwargs: type("Provider", (), {"kwargs": kwargs})(),
    )
    monkeypatch.setattr(
        "read4me.cli.extract_embedded_cover_artwork",
        lambda *_args, **_kwargs: (b"pdf-page-cover", "image/png"),
    )
    monkeypatch.setattr(
        "read4me.cli.generate_fallback_cover_artwork",
        lambda **_kwargs: (_ for _ in ()).throw(AssertionError("fallback should not be used")),
    )

    captured = {}

    def _fake_generate(
        *,
        manifest,
        output_dir,
        provider,
        locale,
        request_delay_seconds,
        max_retries_on_429,
        retry_delay_seconds,
        book_title,
        author,
        cover_image_data,
        cover_mime_type,
    ):
        captured["cover_image_data"] = cover_image_data
        captured["cover_mime_type"] = cover_mime_type
        return [output_dir / "001-page-1.mp3"]

    monkeypatch.setattr("read4me.cli.generate_chapter_mp3_files", _fake_generate)

    result = runner.invoke(
        app, ["convert", str(input_file), "--out", str(output_dir), "--ocr-fallback"]
    )

    assert result.exit_code == 0
    assert captured == {"cover_image_data": b"pdf-page-cover", "cover_mime_type": "image/png"}


def test_inspect_reports_format_and_chapter_count(monkeypatch, tmp_path) -> None:
    runner = CliRunner()
    input_file = tmp_path / "book.epub"
    input_file.write_bytes(b"epub")
    manifest = ChapterManifest(
        source_path=input_file,
        source_format="epub",
        chapters=[Chapter(index=1, title="One", text="a"), Chapter(index=2, title="Two", text="b")],
    )
    monkeypatch.setattr("read4me.cli.build_chapter_manifest", lambda *_args, **_kwargs: manifest)

    result = runner.invoke(app, ["inspect", str(input_file)])

    assert result.exit_code == 0
    assert "Format: epub" in result.stdout
    assert "Chapters: 2" in result.stdout


def test_voices_lists_available_voices() -> None:
    runner = CliRunner()

    result = runner.invoke(app, ["voices"])

    assert result.exit_code == 0
    assert "alloy" in result.stdout
