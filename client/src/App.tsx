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
  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="border-b border-border">
        <div className="container flex flex-col gap-3 py-4">
          <h1 className="text-2xl font-bold tracking-tight text-primary">BRA Tool</h1>
          <nav className="flex flex-wrap gap-1">
            {links.map(({ to, label, end }) => (
              <NavLink
                key={to}
                to={to}
                end={end}
                className={({ isActive }) =>
                  cn(
                    "rounded-md px-3 py-1.5 text-sm font-medium transition-colors",
                    "text-muted-foreground hover:bg-accent hover:text-accent-foreground",
                    isActive && "bg-accent text-accent-foreground"
                  )
                }
              >
                {label}
              </NavLink>
            ))}
          </nav>
        </div>
      </header>

      <main className="container py-8">
        <Routes>
          <Route path="/" element={<UploadPage />} />
          <Route path="/analyser" element={<AnalyserPage />} />
          <Route path="/discovery" element={<DiscoveryPage />} />
          <Route path="/approve" element={<ApprovePage />} />
          <Route path="/architecture" element={<ArchitecturePage />} />
          <Route path="/sprint" element={<SprintPage />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Routes>
      </main>
    </div>
  );
}
