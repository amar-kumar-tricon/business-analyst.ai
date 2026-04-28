from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.projects import projects_router


api_router = APIRouter()
api_router.include_router(projects_router)


@api_router.get("/ping", tags=["meta"])
async def ping() -> dict[str, str]:
    """Quick API ping for connectivity checks."""
    return {"message": "pong"}
