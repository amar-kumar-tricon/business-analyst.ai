import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
/**
 * SettingsPage — placeholder.
 *
 * Per-agent LLM configuration is not yet exposed by the backend.
 */
export default function SettingsPage() {
    return (_jsxs("section", { className: "rounded-lg border border-border bg-card p-6", children: [_jsx("h2", { className: "text-xl font-semibold", children: "Settings" }), _jsxs("p", { className: "mt-2 text-sm text-muted-foreground", children: ["LLM provider and model are configured via the server ", _jsx("code", { children: ".env" }), " file (", _jsx("code", { children: "OPENAI_API_KEY" }), ", ", _jsx("code", { children: "DEFAULT_MODEL_NAME" }), "). A UI for per-agent overrides will land in a later phase."] })] }));
}
