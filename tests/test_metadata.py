from pathlib import Path

from read4me.metadata import apply_id3_metadata


def test_apply_id3_metadata_sets_track_title_and_album(monkeypatch, tmp_path) -> None:
    calls = {"frames": [], "saved": False}

    class _FakeID3:
        def __init__(self, *_args, **_kwargs) -> None:
            pass

        def add(self, frame) -> None:
            calls["frames"].append(frame)

        def save(self, _path: Path) -> None:
            calls["saved"] = True

    monkeypatch.setattr("read4me.metadata.ID3", _FakeID3)
    monkeypatch.setattr("read4me.metadata.TIT2", lambda **kwargs: ("TIT2", kwargs))
    monkeypatch.setattr("read4me.metadata.TRCK", lambda **kwargs: ("TRCK", kwargs))
    monkeypatch.setattr("read4me.metadata.TALB", lambda **kwargs: ("TALB", kwargs))
    monkeypatch.setattr("read4me.metadata.TPE1", lambda **kwargs: ("TPE1", kwargs))
    monkeypatch.setattr("read4me.metadata.APIC", lambda **kwargs: ("APIC", kwargs))

    mp3_file = tmp_path / "001-chapter-one.mp3"
    mp3_file.write_bytes(b"mp3")

    apply_id3_metadata(
        mp3_file,
        title="My Book",
        track_number=1,
        album="My Book",
        artist="Some Author",
        cover_image_data=b"img",
        cover_mime_type="image/png",
    )

    assert ("TIT2", {"encoding": 3, "text": "My Book"}) in calls["frames"]
    assert ("TRCK", {"encoding": 3, "text": "1"}) in calls["frames"]
    assert ("TALB", {"encoding": 3, "text": "My Book"}) in calls["frames"]
    assert ("TPE1", {"encoding": 3, "text": "Some Author"}) in calls["frames"]
    assert (
        "APIC",
        {"encoding": 3, "mime": "image/png", "type": 3, "desc": "Cover", "data": b"img"},
    ) in calls["frames"]
    assert calls["saved"] is True
