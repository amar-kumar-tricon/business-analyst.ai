"""Schemas for Stage 2 — Discovery / QnA agent."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

QAStatus = Literal["pending", "answered", "deferred", "na"]


class QAExchange(BaseModel):
    id: str
    question: str
    answer: str | None = None
    status: QAStatus = "pending"


class DiscoveryState(BaseModel):
    project_id: str
    current_question: str | None = None
    history: list[QAExchange] = []


class DiscoveryAnswerIn(BaseModel):
    answer: str = ""
    status: QAStatus = "answered"
