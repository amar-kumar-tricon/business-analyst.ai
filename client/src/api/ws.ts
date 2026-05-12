/**
 * Wrapper around the `/ws/projects/{id}/events` WebSocket endpoint.
 * Backend at server/app/api/v1/websocket.py replays the backlog on connect
 * then streams new events as they happen.
 */
import type { BackendEvent } from "../types";

export function openProjectStream(
  projectId: string,
  onEvent: (e: BackendEvent) => void
): WebSocket {
  const base = (import.meta.env.VITE_WS_BASE_URL ?? "/ws").replace(/\/$/, "");
  const proto = location.protocol === "https:" ? "wss" : "ws";
  const url = `${proto}://${location.host}${base}/projects/${projectId}/events`;
  const ws = new WebSocket(url);
  ws.onmessage = (ev) => {
    try {
      onEvent(JSON.parse(ev.data));
    } catch {
      console.warn("Malformed WS payload:", ev.data);
    }
  };
  ws.onerror = (e) => console.error("WS error", e);
  return ws;
}
