from __future__ import annotations

import json
from typing import Any

from app.core.config import settings


def _safe_json_parse(text: str) -> dict[str, Any] | None:
    """Try to parse JSON text; return None if parsing fails."""
    try:
        return json.loads(text)
    except Exception:
        return None


def call_structured_json(prompt: str, fallback: dict[str, Any]) -> dict[str, Any]:
    """Call an LLM for JSON output, but always return a safe fallback when unavailable.

    This keeps local development stable even when API keys are missing.
    """
    # We keep imports inside the function so tests do not fail when provider libs are missing.
    if settings.default_model_provider == "openai" and settings.openai_api_key:
        try:
            from langchain_openai import ChatOpenAI

            model = ChatOpenAI(model=settings.default_model_name, api_key=settings.openai_api_key, temperature=0)
            message = model.invoke(prompt)
            parsed = _safe_json_parse(str(message.content))
            return parsed if isinstance(parsed, dict) else fallback
        except Exception:
            return fallback

    if settings.default_model_provider == "anthropic" and settings.anthropic_api_key:
        try:
            from langchain_anthropic import ChatAnthropic

            model = ChatAnthropic(model=settings.default_model_name, api_key=settings.anthropic_api_key, temperature=0)
            message = model.invoke(prompt)
            parsed = _safe_json_parse(str(message.content))
            return parsed if isinstance(parsed, dict) else fallback
        except Exception:
            return fallback

    return fallback
