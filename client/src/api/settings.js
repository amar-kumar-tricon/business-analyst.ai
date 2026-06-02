import { http } from "./http";
export const settingsApi = {
    getLlmConfig: () => http.get("/settings/llm-config").then((r) => r.data),
    updateLlmConfig: (agentId, payload) => http.put(`/settings/llm-config/${agentId}`, payload),
};
