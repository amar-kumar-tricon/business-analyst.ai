/**
 * Lightweight wrapper around the `/ws/projects/{id}/stream` WebSocket endpoint.
 * Dispatches typed events to subscribers. See server/app/api/v1/websocket.py.
 */
export type StreamEvent =
  | { type: "token"; payload: string }
  | { type: "stage_complete"; payload: { stage: string } }
  | { type: "question"; payload: { question: string } }
  | { type: "error"; payload: { message: string } };

export function openProjectStream(projectId: string, onEvent: (e: StreamEvent) => void) {
  const base = import.meta.env.VITE_WS_BASE_URL ?? "/ws";
  const url = `${location.protocol === "https:" ? "wss" : "ws"}://${location.host}${base}/projects/${projectId}/stream`;
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
