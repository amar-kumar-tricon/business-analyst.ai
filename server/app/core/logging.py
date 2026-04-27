from __future__ import annotations

import logging


def configure_logging() -> None:
    """Set a simple, consistent logging format for local development."""

    root_logger = logging.getLogger()
    if root_logger.handlers:
        return

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
