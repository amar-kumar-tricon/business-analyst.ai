export function openProjectStream(projectId, onEvent) {
    const base = (import.meta.env.VITE_WS_BASE_URL ?? "/ws").replace(/\/$/, "");
    const proto = location.protocol === "https:" ? "wss" : "ws";
    const url = `${proto}://${location.host}${base}/projects/${projectId}/events`;
    const ws = new WebSocket(url);
    ws.onmessage = (ev) => {
        try {
            onEvent(JSON.parse(ev.data));
        }
        catch {
            console.warn("Malformed WS payload:", ev.data);
        }
    };
    ws.onerror = (e) => console.error("WS error", e);
    return ws;
}
