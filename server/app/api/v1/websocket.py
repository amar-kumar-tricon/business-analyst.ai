"""
app.api.v1.websocket
====================
Real-time streaming channel for a specific project's agent run.

BRD reference:
    §7.2  WS /ws/projects/{project_id}/stream

Event contract (JSON lines sent to the client):
    { "type": "token",          "payload": "<streamed-token>" }
    { "type": "question",       "payload": { "question": "..." } }
    { "type": "stage_complete", "payload": { "stage": "analyse" } }
    { "type": "error",          "payload": { "message": "..." } }

TODO:
    * maintain a registry of connected clients per `project_id` (pub/sub)
    * have agent nodes publish events via a shared asyncio Queue
"""
from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

ws_router = APIRouter(prefix="/ws", tags=["websocket"])


@ws_router.websocket("/projects/{project_id}/stream")
async def project_stream(websocket: WebSocket, project_id: str) -> None:
    await websocket.accept()
    try:
        await websocket.send_json({"type": "token", "payload": f"(connected to {project_id})"})
        while True:
            # In the final impl, read from an asyncio.Queue populated by agent callbacks.
            msg = await websocket.receive_text()
            await websocket.send_json({"type": "token", "payload": f"echo:{msg}"})
    except WebSocketDisconnect:
        return
