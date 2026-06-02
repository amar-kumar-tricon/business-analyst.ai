import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
/**
 * App.tsx — top-level router.
 *
 * Stage 1 + 2 flow:
 *   /            UploadPage      — create project, upload BRD, run pipeline
 *   /analyser    AnalyserPage    — Stage 1 score & breakdown (read-only)
 *   /discovery   DiscoveryPage   — Stage 2 Q&A loop
 *   /approve     ApprovePage     — final document, approve & download
 *
 * Stages 3 & 4 (Architecture, Sprint) and Settings are out of scope for the
 * current backend; their pages remain stubs.
 */
import { NavLink, Route, Routes } from "react-router-dom";
import UploadPage from "./pages/UploadPage";
import AnalyserPage from "./pages/AnalyserPage";
import DiscoveryPage from "./pages/DiscoveryPage";
import ApprovePage from "./pages/ApprovePage";
import ArchitecturePage from "./pages/ArchitecturePage";
import SprintPage from "./pages/SprintPage";
import SettingsPage from "./pages/SettingsPage";
import { cn } from "@/lib/utils";
const links = [
    { to: "/", label: "Upload", end: true },
    { to: "/analyser", label: "1 · Analyser" },
    { to: "/discovery", label: "2 · Discovery" },
    { to: "/approve", label: "Approve" },
    { to: "/architecture", label: "3 · Architecture" },
    { to: "/sprint", label: "4 · Sprint" },
    { to: "/settings", label: "Settings" },
];
export default function App() {
    return (_jsxs("div", { className: "min-h-screen bg-background text-foreground", children: [_jsx("header", { className: "border-b border-border", children: _jsxs("div", { className: "container flex flex-col gap-3 py-4", children: [_jsx("h1", { className: "text-2xl font-bold tracking-tight text-primary", children: "BRA Tool" }), _jsx("nav", { className: "flex flex-wrap gap-1", children: links.map(({ to, label, end }) => (_jsx(NavLink, { to: to, end: end, className: ({ isActive }) => cn("rounded-md px-3 py-1.5 text-sm font-medium transition-colors", "text-muted-foreground hover:bg-accent hover:text-accent-foreground", isActive && "bg-accent text-accent-foreground"), children: label }, to))) })] }) }), _jsx("main", { className: "container py-8", children: _jsxs(Routes, { children: [_jsx(Route, { path: "/", element: _jsx(UploadPage, {}) }), _jsx(Route, { path: "/analyser", element: _jsx(AnalyserPage, {}) }), _jsx(Route, { path: "/discovery", element: _jsx(DiscoveryPage, {}) }), _jsx(Route, { path: "/approve", element: _jsx(ApprovePage, {}) }), _jsx(Route, { path: "/architecture", element: _jsx(ArchitecturePage, {}) }), _jsx(Route, { path: "/sprint", element: _jsx(SprintPage, {}) }), _jsx(Route, { path: "/settings", element: _jsx(SettingsPage, {}) })] }) })] }));
}
