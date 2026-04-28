from __future__ import annotations

from fastapi import APIRouter, WebSocket

from app.shared.event_bus import event_bus


ws_router = APIRouter(prefix="/ws", tags=["ws"])


@ws_router.websocket("/ping")
async def ws_ping(websocket: WebSocket) -> None:
    """Simple connectivity test websocket."""
    await websocket.accept()
    await websocket.send_json({"type": "ws_ping", "message": "pong"})
    await websocket.close()


@ws_router.websocket("/projects/{project_id}/events")
async def ws_project_events(websocket: WebSocket, project_id: str) -> None:
    """Stream project events to UI in real time."""
    await websocket.accept()

    # Send old events first so the client can catch up.
    for event in event_bus.backlog(project_id):
        await websocket.send_json(event)

    # Then keep sending new events as they come.
    queue = event_bus.subscribe(project_id)
    try:
        while True:
            event = await queue.get()
            await websocket.send_json(event)
    finally:
        event_bus.unsubscribe(project_id, queue)
