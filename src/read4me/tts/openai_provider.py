from pathlib import Path
from typing import Any

from openai import OpenAI


class OpenAITTSProvider:
    def __init__(
        self,
        api_key: str,
        *,
        model: str = "gpt-4o-mini-tts",
        voice: str = "alloy",
        client: Any | None = None,
    ) -> None:
        self.model = model
        self.voice = voice
        self.client = client if client is not None else OpenAI(api_key=api_key)

    def _accent_instructions_for_locale(self, locale: str) -> str | None:
        normalized = locale.lower()
        if normalized == "en" or normalized.startswith("en-"):
            return (
                "If the text is in English, speak with a British accent. "
                "For non-English text, use natural native pronunciation."
            )
        return None

    def synthesize_to_mp3(
        self, text: str, output_file: Path, *, locale: str = "en-US"
    ) -> None:
        if not text.strip():
            raise ValueError("Text for TTS cannot be empty")

        request_payload = {
            "model": self.model,
            "voice": self.voice,
            "input": text,
            "response_format": "mp3",
        }
        accent_instructions = self._accent_instructions_for_locale(locale)
        if accent_instructions:
            request_payload["instructions"] = accent_instructions

        response = self.client.audio.speech.create(
            **request_payload,
        )
        output_file.parent.mkdir(parents=True, exist_ok=True)
        if hasattr(response, "stream_to_file"):
            response.stream_to_file(str(output_file))
            return
        if hasattr(response, "write_to_file"):
            response.write_to_file(str(output_file))
            return
        if hasattr(response, "content"):
            output_file.write_bytes(response.content)
            return
        raise RuntimeError("Unexpected OpenAI TTS response format")
