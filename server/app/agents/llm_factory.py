"""
app.agents.llm_factory
======================
Single place where LLM clients are constructed. Every agent calls
`build_llm(agent_id, state)` so we can hot-swap providers without touching
agent code.

Pattern:
    cfg = state["llm_config"][agent_id]          # {'provider': 'openai', ...}
    llm = build_llm(agent_id, state)
    result = await llm.ainvoke(prompt)
"""
from __future__ import annotations

from functools import lru_cache
from typing import Any

from app.core.config import settings


@lru_cache(maxsize=32)
def _openai(model: str, temperature: float, max_tokens: int):
    from langchain_openai import ChatOpenAI

    return ChatOpenAI(
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        api_key=settings.openai_api_key,
    )


@lru_cache(maxsize=32)
def _anthropic(model: str, temperature: float, max_tokens: int):
    from langchain_anthropic import ChatAnthropic

    return ChatAnthropic(
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        api_key=settings.anthropic_api_key,
    )


_PROVIDER_DEFAULTS: dict[str, str] = {
    "analyser": settings.llm_analyser_model,
    "discovery": settings.llm_discovery_model,
    "architecture": settings.llm_architecture_model,
    "sprint": settings.llm_sprint_model,
}


def build_llm(agent_id: str, state: dict[str, Any]):
    """Return an instantiated LangChain chat model for the given agent."""
    cfg = (state.get("llm_config") or {}).get(agent_id, {})
    provider = cfg.get("provider", "openai")
    model = cfg.get("model_name") or _PROVIDER_DEFAULTS.get(agent_id, "gpt-4o")
    temperature = cfg.get("temperature", 0.2)
    max_tokens = cfg.get("max_tokens", 4096)

    if provider == "openai":
        return _openai(model, temperature, max_tokens)
    if provider == "anthropic":
        return _anthropic(model, temperature, max_tokens)
    raise ValueError(f"Unknown LLM provider: {provider}")
