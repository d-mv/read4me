from pathlib import Path

import typer

from read4me.config import load_config
from read4me.logging_config import configure_logging
from read4me.manifest import build_chapter_manifest
from read4me.pipeline import build_chunk_plan
from read4me.audio_generation import generate_chapter_mp3_files
from read4me.cover_artwork import extract_embedded_cover_artwork, generate_fallback_cover_artwork
from read4me.tts.openai_provider import OpenAITTSProvider

app = typer.Typer(
    help="Convert books into chapter-based MP3 audiobooks.",
    no_args_is_help=True,
)
SUPPORTED_INPUT_SUFFIXES = {".pdf", ".epub", ".fb2"}
AVAILABLE_VOICES = ["alloy", "ash", "ballad", "coral", "echo", "sage", "shimmer"]


@app.callback()
def callback() -> None:
    """Root CLI callback."""


@app.command()
def convert(
    input_file: Path,
    out: Path = typer.Option(..., "--out"),
    author: str = typer.Option("Unknown", "--author"),
    title: str = typer.Option("Untitled", "--title"),
    ocr_fallback: bool = typer.Option(False, "--ocr-fallback"),
    locale: str = typer.Option("en-US", "--locale"),
    request_delay_seconds: float = typer.Option(1.0, "--request-delay-seconds"),
    max_retries_on_429: int = typer.Option(5, "--max-retries-on-429"),
    retry_delay_seconds: float = typer.Option(2.0, "--retry-delay-seconds"),
) -> None:
    """Convert one input book into chapter MP3 files."""
    if not input_file.exists() or not input_file.is_file():
        raise typer.BadParameter("Input file does not exist", param_hint="input_file")
    if input_file.suffix.lower() not in SUPPORTED_INPUT_SUFFIXES:
        raise typer.BadParameter(
            "Unsupported input format. Use .pdf, .epub, or .fb2.",
            param_hint="input_file",
        )
    out.mkdir(parents=True, exist_ok=True)

    config = load_config()
    logger = configure_logging(config.log_level)

    manifest = build_chapter_manifest(input_file, ocr_fallback=ocr_fallback)
    chunks = build_chunk_plan(manifest)

    logger.info("convert requested for %s -> %s", input_file, out)
    typer.echo(
        f"Queued conversion: {input_file} -> {out} "
        f"({len(manifest.chapters)} chapters, {len(chunks)} chunks)"
    )
    if manifest.chapters:
        if not config.openai_api_key:
            raise typer.BadParameter(
                "READ4ME_OPENAI_API_KEY is required to generate MP3 files."
            )
        provider = OpenAITTSProvider(api_key=config.openai_api_key)
        cover_image_data, cover_mime_type = extract_embedded_cover_artwork(
            input_file, manifest.source_format
        )
        if not cover_image_data or not cover_mime_type:
            cover_image_data, cover_mime_type = generate_fallback_cover_artwork(
                title=title,
                author=author,
            )
        output_files = generate_chapter_mp3_files(
            manifest=manifest,
            output_dir=out,
            provider=provider,
            locale=locale,
            book_title=title,
            author=author,
            cover_image_data=cover_image_data,
            cover_mime_type=cover_mime_type,
            request_delay_seconds=request_delay_seconds,
            max_retries_on_429=max_retries_on_429,
            retry_delay_seconds=retry_delay_seconds,
        )
        typer.echo(f"Generated {len(output_files)} MP3 files")


def main() -> None:
    app()


@app.command()
def inspect(input_file: Path) -> None:
    """Inspect book structure and chapter stats."""
    if not input_file.exists() or not input_file.is_file():
        raise typer.BadParameter("Input file does not exist", param_hint="input_file")
    manifest = build_chapter_manifest(input_file)
    typer.echo(f"Format: {manifest.source_format}")
    typer.echo(f"Chapters: {len(manifest.chapters)}")


@app.command()
def voices() -> None:
    """List available TTS voices."""
    for voice in AVAILABLE_VOICES:
        typer.echo(voice)
