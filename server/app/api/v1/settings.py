"""
app.api.v1.settings
===================
Per-agent LLM configuration — readable + writable from the UI Settings panel.

BRD reference:
    §1.1 Configurable LLM per agent
    §7.1 GET/PUT /settings/llm-config
"""
from __future__ import annotations

from fastapi import APIRouter

from app.schemas.settings import LLMConfigIn, LLMConfigOut

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("/llm-config", response_model=list[LLMConfigOut])
async def get_llm_config() -> list[LLMConfigOut]:
    """Return current LLM configuration for every agent.

    TODO:
        * SELECT * FROM llm_configs
        * fall back to defaults from `settings.llm_*_model` if a row is missing
    """
    return []


@router.put("/llm-config/{agent_id}", response_model=LLMConfigOut)
async def update_llm_config(agent_id: str, payload: LLMConfigIn) -> LLMConfigOut:
    """Update provider/model/temperature/max_tokens for a single agent at runtime."""
    # TODO: upsert into llm_configs and invalidate any in-memory LLM cache
    return LLMConfigOut(agent_id=agent_id, **payload.model_dump())
