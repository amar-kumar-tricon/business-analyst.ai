/**
 * App.tsx — top-level router.
 *
 * Styled with Tailwind CSS. shadcn/ui design tokens come from styles.css
 * (bg-background, text-foreground, border-border, etc.).
 *
 * Add a new stage by:
 *   1) creating a component under src/pages/
 *   2) adding a <Route> and <NavLink> entry here.
 */
import { NavLink, Route, Routes } from "react-router-dom";
import UploadPage from "./pages/UploadPage";
import AnalyserPage from "./pages/AnalyserPage";
import DiscoveryPage from "./pages/DiscoveryPage";
import ArchitecturePage from "./pages/ArchitecturePage";
import SprintPage from "./pages/SprintPage";
import SettingsPage from "./pages/SettingsPage";
import { cn } from "@/lib/utils";

const links = [
  { to: "/", label: "Upload", end: true },
  { to: "/analyser", label: "1 · Analyser" },
  { to: "/discovery", label: "2 · Discovery" },
  { to: "/architecture", label: "3 · Architecture" },
  { to: "/sprint", label: "4 · Sprint" },
  { to: "/settings", label: "Settings" },
];

export default function App() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="border-b border-border">
        <div className="container flex flex-col gap-3 py-4">
          <h1 className="text-2xl font-bold tracking-tight text-primary">
            BRA Tool
          </h1>
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
                    isActive && "bg-accent text-accent-foreground",
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
          <Route path="/architecture" element={<ArchitecturePage />} />
          <Route path="/sprint" element={<SprintPage />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Routes>
      </main>
    </div>
  );
}
