from __future__ import annotations

import asyncio
from collections import defaultdict
from copy import deepcopy
from typing import DefaultDict

from app.core.config import settings
from app.shared.state_types import StreamEvent


class EventBus:
    """Project event bus.

    Simple idea:
    - Always keep an in-memory backlog for quick local reads.
    - If Redis is available, also publish there so multiple workers can listen.
    """

    def __init__(self) -> None:
        self._subscribers: DefaultDict[str, list[asyncio.Queue[StreamEvent]]] = defaultdict(list)
        self._backlog: DefaultDict[str, list[StreamEvent]] = defaultdict(list)
        self._redis_client = None
        self._redis_enabled = False

    async def ensure_redis(self) -> None:
        """Connect to Redis lazily so app boot does not fail when Redis is down."""
        if self._redis_enabled:
            return
        try:
            from redis.asyncio import Redis

            self._redis_client = Redis.from_url(settings.redis_url, decode_responses=True)
            await self._redis_client.ping()
            self._redis_enabled = True
        except Exception:
            self._redis_client = None
            self._redis_enabled = False

    def publish(self, project_id: str, event: StreamEvent) -> None:
        """Publish one event to local subscribers and backlog."""
        self._backlog[project_id].append(deepcopy(event))
        for queue in list(self._subscribers[project_id]):
            queue.put_nowait(deepcopy(event))

    async def publish_async(self, project_id: str, event: StreamEvent) -> None:
        """Publish event locally, and to Redis if connected."""
        self.publish(project_id, event)
        await self.ensure_redis()
        if self._redis_enabled and self._redis_client is not None:
            await self._redis_client.publish(f"bra:events:{project_id}", str(event))

    def subscribe(self, project_id: str) -> asyncio.Queue[StreamEvent]:
        """Create a queue for one websocket/listener."""
        queue: asyncio.Queue[StreamEvent] = asyncio.Queue()
        self._subscribers[project_id].append(queue)
        return queue

    def unsubscribe(self, project_id: str, queue: asyncio.Queue[StreamEvent]) -> None:
        """Remove a listener queue when websocket disconnects."""
        subscribers = self._subscribers.get(project_id)
        if not subscribers:
            return
        if queue in subscribers:
            subscribers.remove(queue)

    def backlog(self, project_id: str) -> list[StreamEvent]:
        """Return historical events so new clients can catch up quickly."""
        return deepcopy(self._backlog.get(project_id, []))


event_bus = EventBus()
