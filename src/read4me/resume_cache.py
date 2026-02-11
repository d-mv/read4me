import json
from pathlib import Path


def load_completed_chapters(cache_file: Path) -> set[int]:
    if not cache_file.exists():
        return set()
    try:
        payload = json.loads(cache_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return set()
    completed = payload.get("completed_chapters", [])
    return {int(index) for index in completed}


def save_completed_chapters(cache_file: Path, completed_chapters: set[int]) -> None:
    payload = {"completed_chapters": sorted(completed_chapters)}
    cache_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")
