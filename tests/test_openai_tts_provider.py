from pathlib import Path

from read4me.tts.openai_provider import OpenAITTSProvider


def test_openai_tts_provider_writes_mp3_file(tmp_path) -> None:
    class _FakeSpeechAPI:
        def __init__(self) -> None:
            self.calls = []

        def create(self, **kwargs):
            self.calls.append(kwargs)
            return type("Response", (), {"content": b"mp3-bytes"})()

    class _FakeClient:
        def __init__(self) -> None:
            self.audio = type("Audio", (), {"speech": _FakeSpeechAPI()})()

    client = _FakeClient()
    provider = OpenAITTSProvider(api_key="test-key", client=client)
    output_file = tmp_path / "chapter-01.mp3"

    provider.synthesize_to_mp3("Hello chapter", output_file, locale="en-US")

    assert output_file.read_bytes() == b"mp3-bytes"
    assert client.audio.speech.calls == [
        {
            "model": "gpt-4o-mini-tts",
            "voice": "alloy",
            "input": "Hello chapter",
            "response_format": "mp3",
            "instructions": (
                "If the text is in English, speak with a British accent. "
                "For non-English text, use natural native pronunciation."
            ),
        }
    ]


def test_openai_tts_provider_rejects_empty_text(tmp_path) -> None:
    class _FakeClient:
        def __init__(self) -> None:
            self.audio = type("Audio", (), {"speech": object()})()

    provider = OpenAITTSProvider(api_key="test-key", client=_FakeClient())
    output_file = tmp_path / "chapter-01.mp3"

    try:
        provider.synthesize_to_mp3("   ", output_file)
        assert False, "expected ValueError for empty input text"
    except ValueError as error:
        assert "Text for TTS cannot be empty" in str(error)


def test_openai_tts_provider_keeps_non_english_locale_neutral(tmp_path) -> None:
    class _FakeSpeechAPI:
        def __init__(self) -> None:
            self.calls = []

        def create(self, **kwargs):
            self.calls.append(kwargs)
            return type("Response", (), {"content": b"mp3-bytes"})()

    class _FakeClient:
        def __init__(self) -> None:
            self.audio = type("Audio", (), {"speech": _FakeSpeechAPI()})()

    client = _FakeClient()
    provider = OpenAITTSProvider(api_key="test-key", client=client)
    output_file = tmp_path / "chapter-01.mp3"

    provider.synthesize_to_mp3("Bonjour chapitre", output_file, locale="fr-FR")

    assert "instructions" not in client.audio.speech.calls[0]
