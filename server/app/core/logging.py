"""
app.core.logging
================
Central logging configuration. Use `logging.getLogger(__name__)` everywhere else.

TODO:
    * swap to `structlog` if you need JSON logs for ELK/Loki
    * inject a per-request trace id via middleware (contextvars)
"""
from __future__ import annotations

import logging
import sys

from app.core.config import settings


def configure_logging() -> None:
    level = logging.DEBUG if settings.app_debug else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s  %(levelname)-7s  %(name)s  ·  %(message)s",
        datefmt="%H:%M:%S",
        stream=sys.stdout,
        force=True,
    )
    # Tame noisy libs
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
