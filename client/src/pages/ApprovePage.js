import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
/**
 * ApprovePage — Final review + export.
 *
 * Shows the rendered Stage-2 markdown for the user to read. The Approve
 * button POSTs /approve which builds the approved RAG index and writes
 * the .md / .pdf / .docx artifacts. Once approved, download links go live.
 */
import { useState } from "react";
import { Link } from "react-router-dom";
import { projectsApi } from "../api/projects";
import { useAppStore } from "../store/useAppStore";
export default function ApprovePage() {
    const { projectId, projectName, finalDocMarkdown } = useAppStore();
    const applyApprove = useAppStore((s) => s.applyApprove);
    const [busy, setBusy] = useState(false);
    const [approved, setApproved] = useState(false);
    const [error, setError] = useState(null);
    if (!projectId) {
        return (_jsxs("div", { className: "rounded-md border border-border bg-card p-6 text-sm", children: ["No active project \u2014 start from the ", _jsx(Link, { to: "/", className: "text-primary underline", children: "upload page" }), "."] }));
    }
    async function handleApprove() {
        if (!projectId)
            return;
        setError(null);
        setBusy(true);
        try {
            const r = await projectsApi.approve(projectId);
            applyApprove(r);
            setApproved(true);
        }
        catch (e) {
            setError(e?.response?.data?.detail ?? e.message ?? "Approve failed.");
        }
        finally {
            setBusy(false);
        }
    }
    return (_jsxs("section", { className: "space-y-5", children: [_jsxs("header", { className: "flex items-baseline justify-between", children: [_jsxs("div", { children: [_jsx("h2", { className: "text-xl font-semibold", children: "Final Review" }), _jsx("p", { className: "text-sm text-muted-foreground", children: projectName })] }), !approved && (_jsx("button", { disabled: busy, onClick: handleApprove, className: "inline-flex h-9 items-center rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground hover:opacity-90 disabled:opacity-50", children: busy ? "Approving…" : "Approve & Export" }))] }), error && (_jsx("div", { className: "rounded-md border border-destructive/50 bg-destructive/10 p-3 text-sm text-destructive", children: error })), approved && projectId && (_jsxs("div", { className: "rounded-lg border border-emerald-500/40 bg-emerald-500/10 p-5", children: [_jsx("p", { className: "font-medium text-emerald-600", children: "Approved & exported." }), _jsxs("div", { className: "mt-3 flex flex-wrap gap-3 text-sm", children: [_jsx("a", { href: projectsApi.artifactUrl(projectId, "md"), target: "_blank", rel: "noreferrer", className: "rounded-md border border-border bg-background px-3 py-1.5 hover:bg-accent", children: "Download .md" }), _jsx("a", { href: projectsApi.artifactUrl(projectId, "pdf"), target: "_blank", rel: "noreferrer", className: "rounded-md border border-border bg-background px-3 py-1.5 hover:bg-accent", children: "Download .pdf" }), _jsx("a", { href: projectsApi.artifactUrl(projectId, "docx"), target: "_blank", rel: "noreferrer", className: "rounded-md border border-border bg-background px-3 py-1.5 hover:bg-accent", children: "Download .docx" })] })] })), _jsxs("article", { className: "rounded-lg border border-border bg-card p-5", children: [_jsx("h3", { className: "mb-3 text-sm font-medium text-muted-foreground", children: "Final document preview" }), finalDocMarkdown ? (_jsx("pre", { className: "whitespace-pre-wrap break-words font-mono text-xs leading-relaxed", children: finalDocMarkdown })) : (_jsx("p", { className: "text-sm text-muted-foreground", children: "No final document available. Complete discovery first." }))] })] }));
}
