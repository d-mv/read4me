import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class AppConfig:
    openai_api_key: str
    log_level: str


def load_config(env_file: Path | str = ".env") -> AppConfig:
    load_dotenv(dotenv_path=env_file, override=False)
    return AppConfig(
        openai_api_key=os.getenv("READ4ME_OPENAI_API_KEY", ""),
        log_level=os.getenv("READ4ME_LOG_LEVEL", "INFO"),
    )
