from dataclasses import dataclass
import base64
from pathlib import Path
from xml.etree import ElementTree

FB2_NS = {"fb2": "http://www.gribuser.ru/xml/fictionbook/2.0"}
XLINK_NS = "{http://www.w3.org/1999/xlink}href"


@dataclass(frozen=True)
class Fb2Chapter:
    title: str
    text: str


def _join_text(parts: list[str]) -> str:
    return " ".join(part.strip() for part in parts if part and part.strip())


def parse_fb2_chapters(fb2_path: Path) -> list[Fb2Chapter]:
    root = ElementTree.parse(fb2_path).getroot()
    body = root.find("fb2:body", FB2_NS)
    if body is None:
        raise ValueError("FB2 body is missing")

    chapters: list[Fb2Chapter] = []
    for index, section in enumerate(body.findall("fb2:section", FB2_NS), start=1):
        title_node = section.find("fb2:title", FB2_NS)
        title_parts: list[str] = []
        if title_node is not None:
            title_parts = [text for text in title_node.itertext()]
        title = _join_text(title_parts) or f"Chapter {index}"

        paragraph_texts = []
        for paragraph in section.findall("fb2:p", FB2_NS):
            paragraph_texts.append("".join(paragraph.itertext()))

        text = _join_text(paragraph_texts)
        if not text:
            continue

        chapters.append(Fb2Chapter(title=title, text=text))

    return chapters


def parse_fb2_cover_artwork(fb2_path: Path) -> tuple[bytes, str] | tuple[None, None]:
    root = ElementTree.parse(fb2_path).getroot()
    image = root.find(".//fb2:description/fb2:title-info/fb2:coverpage/fb2:image", FB2_NS)
    if image is None:
        return None, None

    href = image.get(XLINK_NS, "")
    if not href.startswith("#"):
        return None, None
    binary_id = href[1:]
    binary = root.find(f".//fb2:binary[@id='{binary_id}']", FB2_NS)
    if binary is None or not binary.text:
        return None, None

    mime_type = binary.get("content-type", "image/jpeg")
    cover_data = base64.b64decode(binary.text.encode("utf-8"))
    return cover_data, mime_type
