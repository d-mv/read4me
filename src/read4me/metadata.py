from pathlib import Path

from mutagen.id3 import APIC, ID3, TALB, TIT2, TPE1, TRCK


def apply_id3_metadata(
    mp3_file: Path,
    *,
    title: str,
    track_number: int,
    album: str,
    artist: str,
    cover_image_data: bytes | None = None,
    cover_mime_type: str | None = None,
) -> None:
    tags = ID3()
    tags.add(TIT2(encoding=3, text=title))
    tags.add(TRCK(encoding=3, text=str(track_number)))
    tags.add(TALB(encoding=3, text=album))
    tags.add(TPE1(encoding=3, text=artist))
    if cover_image_data and cover_mime_type:
        tags.add(
            APIC(
                encoding=3,
                mime=cover_mime_type,
                type=3,
                desc="Cover",
                data=cover_image_data,
            )
        )
    tags.save(mp3_file)
