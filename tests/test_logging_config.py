import logging

from read4me.logging_config import configure_logging


def test_configure_logging_sets_named_logger_level() -> None:
    logger = configure_logging("DEBUG")

    assert logger.name == "read4me"
    assert logger.level == logging.DEBUG
