from read4me.config import AppConfig, load_config


def test_load_config_defaults(monkeypatch) -> None:
    monkeypatch.delenv("READ4ME_OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("READ4ME_LOG_LEVEL", raising=False)

    config = load_config(env_file="/tmp/read4me-non-existent.env")

    assert config == AppConfig(openai_api_key="", log_level="INFO")


def test_load_config_from_env(monkeypatch) -> None:
    monkeypatch.setenv("READ4ME_OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("READ4ME_LOG_LEVEL", "DEBUG")

    config = load_config(env_file="/tmp/read4me-non-existent.env")

    assert config.openai_api_key == "test-key"
    assert config.log_level == "DEBUG"


def test_load_config_from_env_file(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("READ4ME_OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("READ4ME_LOG_LEVEL", raising=False)
    env_file = tmp_path / ".env"
    env_file.write_text(
        "READ4ME_OPENAI_API_KEY=env-file-key\nREAD4ME_LOG_LEVEL=WARNING\n",
        encoding="utf-8",
    )

    config = load_config(env_file=env_file)

    assert config.openai_api_key == "env-file-key"
    assert config.log_level == "WARNING"
