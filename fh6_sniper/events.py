"""User-facing event logging for the overlay log tab."""
from __future__ import annotations

import logging


LOGGER_NAME = "fh6.events"
SUCCESS = 25

logging.addLevelName(SUCCESS, "SUCCESS")


def get_logger() -> logging.Logger:
    return logging.getLogger(LOGGER_NAME)


def info(message: str, *args, **kwargs) -> None:
    get_logger().info(message, *args, **kwargs)


def success(message: str, *args, **kwargs) -> None:
    get_logger().log(SUCCESS, message, *args, **kwargs)


def warning(message: str, *args, **kwargs) -> None:
    get_logger().warning(message, *args, **kwargs)


def error(message: str, *args, **kwargs) -> None:
    get_logger().error(message, *args, **kwargs)
