from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path, PurePosixPath
from xml.etree import ElementTree
from xml.etree.ElementTree import ParseError
from zipfile import ZipFile

CONTAINER_NS = {"c": "urn:oasis:names:tc:opendocument:xmlns:container"}
OPF_NS = {"opf": "http://www.idpf.org/2007/opf"}


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._parts: list[str] = []

    def handle_data(self, data: str) -> None:
        text = data.strip()
        if text:
            self._parts.append(text)

    def text(self) -> str:
        return " ".join(self._parts)


@dataclass(frozen=True)
class EpubChapter:
    title: str
    text: str


def _load_opf_path(archive: ZipFile) -> PurePosixPath:
    try:
        container_raw = archive.read("META-INF/container.xml")
    except KeyError as error:
        raise ValueError("EPUB OPF lookup failed: container.xml is missing") from error

    container_root = ElementTree.fromstring(container_raw)
    rootfile = container_root.find(".//c:rootfile", CONTAINER_NS)
    if rootfile is None:
        raise ValueError("EPUB container.xml missing rootfile entry")
    opf_full_path = rootfile.get("full-path")
    if not opf_full_path:
        raise ValueError("EPUB container.xml missing OPF path")
    return PurePosixPath(opf_full_path)


def parse_epub_chapters(epub_path: Path) -> list[EpubChapter]:
    with ZipFile(epub_path, "r") as archive:
        opf_path = _load_opf_path(archive)
        try:
            opf_raw = archive.read(str(opf_path))
        except KeyError as error:
            raise ValueError("EPUB OPF file is missing") from error

        opf_root = ElementTree.fromstring(opf_raw)
        manifest_items = {
            item.get("id"): item.get("href")
            for item in opf_root.findall(".//opf:manifest/opf:item", OPF_NS)
            if item.get("id") and item.get("href")
        }
        base_dir = opf_path.parent

        chapters: list[EpubChapter] = []
        for itemref in opf_root.findall(".//opf:spine/opf:itemref", OPF_NS):
            item_id = itemref.get("idref")
            href = manifest_items.get(item_id) if item_id else None
            if not href:
                continue

            chapter_path = str(base_dir / PurePosixPath(href))
            try:
                chapter_html = archive.read(chapter_path).decode("utf-8", errors="ignore")
            except KeyError:
                continue

            title = chapter_path.rsplit("/", 1)[-1].rsplit(".", 1)[0]
            text = ""
            try:
                chapter_root = ElementTree.fromstring(chapter_html)
                title_element = chapter_root.find(".//title")
                if title_element is not None and title_element.text and title_element.text.strip():
                    title = title_element.text.strip()
                body_element = chapter_root.find(".//body")
                if body_element is not None:
                    text = " ".join(
                        part.strip() for part in body_element.itertext() if part.strip()
                    )
            except ParseError:
                extractor = _TextExtractor()
                extractor.feed(chapter_html)
                text = extractor.text()

            if not text:
                continue

            chapters.append(EpubChapter(title=title, text=text))

        return chapters


def parse_epub_cover_artwork(epub_path: Path) -> tuple[bytes, str] | tuple[None, None]:
    with ZipFile(epub_path, "r") as archive:
        opf_path = _load_opf_path(archive)
        try:
            opf_raw = archive.read(str(opf_path))
        except KeyError as error:
            raise ValueError("EPUB OPF file is missing") from error

        opf_root = ElementTree.fromstring(opf_raw)
        manifest_items = {
            item.get("id"): (item.get("href"), item.get("media-type"))
            for item in opf_root.findall(".//opf:manifest/opf:item", OPF_NS)
            if item.get("id") and item.get("href")
        }
        base_dir = opf_path.parent

        cover_item_id = None
        for meta in opf_root.findall(".//opf:metadata/opf:meta", OPF_NS):
            if meta.get("name") == "cover":
                cover_item_id = meta.get("content")
                break

        if not cover_item_id:
            for item in opf_root.findall(".//opf:manifest/opf:item", OPF_NS):
                properties = item.get("properties", "")
                if "cover-image" in properties:
                    cover_item_id = item.get("id")
                    break

        if not cover_item_id:
            return None, None

        cover_entry = manifest_items.get(cover_item_id)
        if not cover_entry:
            return None, None
        href, mime_type = cover_entry
        if not href or not mime_type:
            return None, None

        cover_path = str(base_dir / PurePosixPath(href))
        try:
            cover_data = archive.read(cover_path)
        except KeyError:
            return None, None
        return cover_data, mime_type
