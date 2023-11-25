import logging

from litestar.logging import LoggingConfig
from litestar.types import Logger

log_config = LoggingConfig(
    root={"level": logging.getLevelName(logging.INFO), "handlers": ["console"]},
    formatters={"standard": {"format": "%(levelname)s:     %(message)s (%(filename)s:%(lineno)d)"}},
)


def get_logger() -> Logger:
    return log_config.configure()()
