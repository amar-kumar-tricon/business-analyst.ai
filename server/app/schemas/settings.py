"""Schemas for per-agent LLM configuration (BRD §7.1)."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

AgentId = Literal["analyser", "discovery", "architecture", "sprint"]
Provider = Literal["openai", "anthropic", "azure-openai", "local"]


class LLMConfigIn(BaseModel):
    provider: Provider
    model_name: str
    temperature: float = Field(default=0.2, ge=0.0, le=2.0)
    max_tokens: int = Field(default=4096, gt=0)


class LLMConfigOut(LLMConfigIn):
    agent_id: AgentId
