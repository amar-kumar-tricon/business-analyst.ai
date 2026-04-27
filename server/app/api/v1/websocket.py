from __future__ import annotations

from fastapi import APIRouter, WebSocket


ws_router = APIRouter(prefix="/ws", tags=["ws"])


@ws_router.websocket("/ping")
async def ws_ping(websocket: WebSocket) -> None:
    await websocket.accept()
    await websocket.send_json({"type": "ws_ping", "message": "pong"})
    await websocket.close()
