from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from read4me.parsers.epub import parse_epub_cover_artwork
from read4me.parsers.fb2 import parse_fb2_cover_artwork
from read4me.parsers.pdf import parse_pdf_first_page_artwork


def extract_embedded_cover_artwork(
    input_file: Path, source_format: str
) -> tuple[bytes, str] | tuple[None, None]:
    if source_format == "epub":
        return parse_epub_cover_artwork(input_file)
    if source_format == "fb2":
        return parse_fb2_cover_artwork(input_file)
    if source_format == "pdf":
        return parse_pdf_first_page_artwork(input_file)
    return None, None


def generate_fallback_cover_artwork(
    *, title: str, author: str, size: int = 1024
) -> tuple[bytes, str]:
    image = Image.new("RGB", (size, size), color=(26, 26, 28))
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    text = f"{title}\n\n{author}"
    draw.multiline_text(
        (64, 64),
        text,
        fill=(245, 245, 245),
        font=font,
        spacing=12,
    )

    output = BytesIO()
    image.save(output, format="PNG")
    return output.getvalue(), "image/png"
