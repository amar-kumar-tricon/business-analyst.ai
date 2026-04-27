from __future__ import annotations

from fastapi import APIRouter


api_router = APIRouter()


@api_router.get("/ping", tags=["meta"])
async def ping() -> dict[str, str]:
    return {"message": "pong"}
