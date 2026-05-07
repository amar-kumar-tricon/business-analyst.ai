from __future__ import annotations

import json
from typing import Any

from app.core.config import settings


def _safe_json_parse(text: str) -> dict[str, Any] | None:
    """Try to parse JSON text; strips markdown fences and trailing garbage."""
    try:
        stripped = text.strip()
        # Strip markdown code fences
        if stripped.startswith("```"):
            stripped = stripped.split("\n", 1)[-1]
            stripped = stripped.rsplit("```", 1)[0]
        stripped = stripped.strip()
        # Extract just the outermost JSON object {...}
        start = stripped.find("{")
        end = stripped.rfind("}")
        if start != -1 and end != -1 and end > start:
            stripped = stripped[start : end + 1]
        return json.loads(stripped)
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

    if settings.default_model_provider == "groq" and settings.groq_api_key:
        try:
            from langchain_groq import ChatGroq

            model = ChatGroq(model=settings.default_model_name, api_key=settings.groq_api_key, temperature=0)
            message = model.invoke(prompt)
            parsed = _safe_json_parse(str(message.content))
            return parsed if isinstance(parsed, dict) else fallback
        except Exception:
            return fallback

    return fallback
