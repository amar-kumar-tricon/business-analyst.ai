from __future__ import annotations

import json
import logging
from typing import Any

from app.core.config import settings


log = logging.getLogger(__name__)


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
    provider = settings.default_model_provider
    model_name = settings.default_model_name

    if provider == "openai" and settings.openai_api_key:
        try:
            from langchain_openai import ChatOpenAI

            log.info("[llm] call_structured_json provider=openai model=%s prompt_chars=%d", model_name, len(prompt))
            model = ChatOpenAI(model=model_name, api_key=settings.openai_api_key, temperature=0)
            message = model.invoke(prompt)
            parsed = _safe_json_parse(str(message.content))
            ok = isinstance(parsed, dict)
            log.info("[llm] response provider=openai parsed_ok=%s response_chars=%d", ok, len(str(message.content)))
            return parsed if ok else fallback
        except Exception as e:
            log.warning("[llm] openai call failed: %s — using fallback", e)
            return fallback

    if provider == "anthropic" and settings.anthropic_api_key:
        try:
            from langchain_anthropic import ChatAnthropic

            log.info("[llm] call_structured_json provider=anthropic model=%s prompt_chars=%d", model_name, len(prompt))
            model = ChatAnthropic(model=model_name, api_key=settings.anthropic_api_key, temperature=0)
            message = model.invoke(prompt)
            parsed = _safe_json_parse(str(message.content))
            ok = isinstance(parsed, dict)
            log.info("[llm] response provider=anthropic parsed_ok=%s response_chars=%d", ok, len(str(message.content)))
            return parsed if ok else fallback
        except Exception as e:
            log.warning("[llm] anthropic call failed: %s — using fallback", e)
            return fallback

    log.info("[llm] no usable provider configured (provider=%s) — using fallback", provider)
    return fallback
