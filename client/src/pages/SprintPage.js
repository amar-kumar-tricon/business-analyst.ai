import { jsx as _jsx, jsxs as _jsxs, Fragment as _Fragment } from "react/jsx-runtime";
import { useState } from "react";
import { Link } from "react-router-dom";
import { projectsApi } from "../api/projects";
import { useAppStore } from "../store/useAppStore";

const SEVERITY_COLOUR = {
    high: "text-destructive",
    medium: "text-amber-500",
    low: "text-emerald-500",
};

function Badge({ label, className }) {
    return _jsx("span", {
        className: `inline-block rounded px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${className}`,
        children: label.replace(/_/g, " ")
    });
}

function SummaryCards({ plan }) {
    const cards = [
        { label: "Total Sprints", value: plan.total_sprints },
        { label: "Sprint Duration", value: `${plan.sprint_duration_weeks}w each` },
        { label: "Total Story Points", value: plan.total_story_points },
        { label: "Total Man-Hours", value: plan.total_man_hours.toLocaleString() },
        { label: "MVP Cutoff Sprint", value: `Sprint ${plan.mvp_cutoff_sprint}` },
    ];
    return _jsx("div", {
        className: "grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5",
        children: cards.map((c) => _jsxs("div", {
            className: "rounded-lg border border-border bg-card p-4 text-center",
            children: [
                _jsx("p", { className: "text-xl font-bold text-primary", children: c.value }),
                _jsx("p", { className: "mt-0.5 text-xs text-muted-foreground", children: c.label })
            ]
        }, c.label))
    });
}

function TeamTable({ team }) {
    return _jsxs("div", {
        className: "rounded-lg border border-border bg-card p-5",
        children: [
            _jsx("h3", { className: "mb-3 text-sm font-semibold", children: "Team Composition" }),
            _jsxs("table", {
                className: "w-full text-sm",
                children: [
                    _jsx("thead", { children: _jsxs("tr", { className: "border-b border-border text-left text-xs text-muted-foreground", children: [_jsx("th", { className: "pb-2 font-medium", children: "Role" }), _jsx("th", { className: "pb-2 font-medium", children: "Headcount" }), _jsx("th", { className: "pb-2 font-medium", children: "Hrs / Sprint" })] }) }),
                    _jsx("tbody", { children: team.map((m) => _jsxs("tr", { className: "border-b border-border/50 last:border-0", children: [_jsx("td", { className: "py-1.5 font-medium", children: m.role }), _jsx("td", { className: "py-1.5", children: m.count }), _jsx("td", { className: "py-1.5", children: `${m.hours_per_sprint}h` })] }, m.role)) })
                ]
            })
        ]
    });
}

function TechStackTable({ stack }) {
    if (!stack.length) return null;
    return _jsxs("div", {
        className: "rounded-lg border border-border bg-card p-5",
        children: [
            _jsx("h3", { className: "mb-3 text-sm font-semibold", children: "Technology Stack" }),
            _jsxs("table", {
                className: "w-full text-sm",
                children: [
                    _jsx("thead", { children: _jsxs("tr", { className: "border-b border-border text-left text-xs text-muted-foreground", children: [_jsx("th", { className: "pb-2 font-medium", children: "Component" }), _jsx("th", { className: "pb-2 font-medium", children: "Technology" }), _jsx("th", { className: "pb-2 font-medium", children: "Rationale" })] }) }),
                    _jsx("tbody", { children: stack.map((t) => _jsxs("tr", { className: "border-b border-border/50 last:border-0", children: [_jsx("td", { className: "py-1.5 font-medium", children: t.component }), _jsx("td", { className: "py-1.5", children: t.technology }), _jsx("td", { className: "py-1.5 text-xs text-muted-foreground", children: t.rationale })] }, t.component)) })
                ]
            })
        ]
    });
}

function StoryCard({ story }) {
    const [open, setOpen] = useState(false);
    return _jsxs("div", {
        className: "rounded-md border border-border bg-background p-3 text-xs",
        children: [
            _jsxs("div", {
                className: "flex items-start gap-2",
                children: [
                    _jsx("button", { onClick: () => setOpen((o) => !o), className: "mt-0.5 shrink-0 text-muted-foreground hover:text-foreground", children: open ? "▾" : "▸" }),
                    _jsxs("div", {
                        className: "flex-1 min-w-0",
                        children: [
                            _jsxs("div", { className: "flex flex-wrap items-center gap-1.5", children: [_jsx("span", { className: "font-mono text-[10px] text-muted-foreground", children: story.story_id }), _jsx("span", { className: "font-medium truncate", children: story.title })] }),
                            _jsxs("div", { className: "mt-1 flex flex-wrap gap-1", children: [_jsx(Badge, { label: `${story.story_points} pts`, className: "bg-muted text-muted-foreground" }), _jsx(Badge, { label: story.role, className: "bg-primary/10 text-primary" }), _jsx("span", { className: "text-[10px] text-muted-foreground", children: story.req_id })] })
                        ]
                    })
                ]
            }),
            open && _jsxs("div", {
                className: "mt-2 ml-5 space-y-2",
                children: [
                    _jsx("p", { className: "text-muted-foreground leading-relaxed", children: story.description }),
                    story.acceptance_criteria.length > 0 && _jsxs("div", { children: [_jsx("p", { className: "font-semibold mb-1", children: "Acceptance Criteria" }), _jsx("ul", { className: "list-disc list-inside space-y-0.5 text-muted-foreground", children: story.acceptance_criteria.map((ac, i) => _jsx("li", { children: ac }, i)) })] })
                ]
            })
        ]
    });
}

function SprintBoard({ sprint }) {
    const [open, setOpen] = useState(sprint.sprint_number === 1);
    return _jsxs("div", {
        className: `rounded-lg border ${sprint.is_mvp_cutoff ? "border-emerald-500/60" : "border-border"} bg-card`,
        children: [
            _jsxs("button", {
                onClick: () => setOpen((o) => !o),
                className: "flex w-full items-center gap-3 p-4 text-left",
                children: [
                    _jsx("span", { className: "text-base font-semibold", children: sprint.sprint_name }),
                    sprint.is_mvp_cutoff && _jsx(Badge, { label: "MVP Cutoff", className: "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400" }),
                    _jsxs("span", { className: "ml-auto text-xs text-muted-foreground", children: [`${sprint.total_points} pts · ${sprint.man_hours}h · ${sprint.stories.length} stories`] }),
                    _jsx("span", { className: "text-muted-foreground", children: open ? "▴" : "▾" })
                ]
            }),
            open && _jsxs("div", {
                className: "border-t border-border px-4 pb-4 pt-3 space-y-3",
                children: [
                    _jsxs("p", { className: "text-sm text-muted-foreground", children: [_jsx("span", { className: "font-medium text-foreground", children: "Goal: " }), sprint.goal] }),
                    sprint.features.length > 0 && _jsx("div", { className: "flex flex-wrap gap-1", children: sprint.features.map((f, i) => _jsx(Badge, { label: f, className: "bg-muted text-muted-foreground" }, i)) }),
                    _jsx("div", { className: "space-y-2", children: sprint.stories.map((s) => _jsx(StoryCard, { story: s }, s.story_id)) })
                ]
            })
        ]
    });
}

function RiskRegister({ risks }) {
    if (!risks.length) return null;
    return _jsxs("div", {
        className: "rounded-lg border border-border bg-card p-5",
        children: [
            _jsx("h3", { className: "mb-3 text-sm font-semibold", children: "Risk Register" }),
            _jsx("div", {
                className: "space-y-2",
                children: risks.map((r) => _jsxs("div", {
                    className: "rounded-md border border-border bg-background p-3 text-xs",
                    children: [
                        _jsxs("div", { className: "flex flex-wrap items-center gap-2 mb-1", children: [_jsx("span", { className: "font-mono text-muted-foreground", children: r.risk_id }), _jsx(Badge, { label: r.category, className: "bg-muted text-muted-foreground" }), _jsx("span", { className: `font-semibold ${SEVERITY_COLOUR[r.severity] ?? ""}`, children: r.severity.toUpperCase() }), r.sprint_impacted != null && _jsxs("span", { className: "text-muted-foreground", children: ["Sprint ", r.sprint_impacted] })] }),
                        _jsx("p", { className: "font-medium", children: r.description }),
                        r.mitigation && _jsxs("p", { className: "mt-1 text-muted-foreground", children: [_jsx("span", { className: "font-semibold text-foreground", children: "Mitigation: " }), r.mitigation] })
                    ]
                }, r.risk_id))
            })
        ]
    });
}

export default function SprintPage() {
    const { projectId, projectName, sprintPlan } = useAppStore();
    const applySprintPlan = useAppStore((s) => s.applySprintPlan);
    const [busy, setBusy] = useState(false);
    const [error, setError] = useState(null);

    if (!projectId) {
        return _jsxs("div", {
            className: "rounded-md border border-border bg-card p-6 text-sm",
            children: ["No active project — start from the ", _jsx(Link, { to: "/", className: "text-primary underline", children: "upload page" }), "."]
        });
    }

    async function handleGenerate() {
        if (!projectId) return;
        setError(null);
        setBusy(true);
        try {
            const r = await projectsApi.sprint(projectId);
            applySprintPlan(r);
        } catch (e) {
            setError(e?.response?.data?.detail ?? e.message ?? "Sprint generation failed.");
        } finally {
            setBusy(false);
        }
    }

    return _jsxs("section", {
        className: "space-y-6",
        children: [
            _jsxs("header", {
                className: "flex items-baseline justify-between gap-4",
                children: [
                    _jsxs("div", { children: [_jsx("h2", { className: "text-xl font-semibold", children: "Stage 4 — Sprint Planner" }), _jsx("p", { className: "text-sm text-muted-foreground", children: projectName })] }),
                    _jsx("button", {
                        disabled: busy,
                        onClick: handleGenerate,
                        className: "inline-flex h-9 items-center rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground hover:opacity-90 disabled:opacity-50",
                        children: busy
                            ? _jsxs(_Fragment, { children: [_jsx("span", { className: "mr-2 inline-block h-3.5 w-3.5 animate-spin rounded-full border-2 border-primary-foreground border-t-transparent" }), "Generating…"] })
                            : sprintPlan ? "Regenerate Sprint Plan" : "Generate Sprint Plan"
                    })
                ]
            }),

            error && _jsx("div", { className: "rounded-md border border-destructive/50 bg-destructive/10 p-3 text-sm text-destructive", children: error }),

            busy && !sprintPlan && _jsx("div", { className: "rounded-lg border border-border bg-card p-6 text-center text-sm text-muted-foreground animate-pulse", children: "Running sprint planning LLM… this usually takes 15–30 seconds." }),

            !busy && !sprintPlan && !error && _jsxs("div", {
                className: "rounded-lg border border-dashed border-border bg-card p-8 text-center text-sm text-muted-foreground",
                children: [
                    _jsx("p", { className: "text-base font-medium mb-1", children: "No sprint plan yet" }),
                    _jsxs("p", { children: ["Click ", _jsx("span", { className: "font-semibold", children: "Generate Sprint Plan" }), " above to run the LLM sprint planner."] }),
                    _jsx("p", { className: "mt-1 text-xs", children: "Requires Stage 1 (analysis) to have completed first." })
                ]
            }),

            sprintPlan && _jsxs(_Fragment, {
                children: [
                    _jsx(SummaryCards, { plan: sprintPlan }),
                    _jsxs("div", {
                        className: "grid gap-4 md:grid-cols-2",
                        children: [_jsx(TeamTable, { team: sprintPlan.team_composition }), _jsx(TechStackTable, { stack: sprintPlan.technology_stack })]
                    }),
                    _jsxs("div", {
                        className: "space-y-3",
                        children: [
                            _jsx("h3", { className: "text-sm font-semibold", children: "Sprint Boards" }),
                            sprintPlan.sprints.map((s) => _jsx(SprintBoard, { sprint: s }, s.sprint_number))
                        ]
                    }),
                    _jsx(RiskRegister, { risks: sprintPlan.risk_register }),
                    _jsxs("p", { className: "text-xs text-muted-foreground", children: ["Generated at ", new Date(sprintPlan.generated_at).toLocaleString()] })
                ]
            })
        ]
    });
}
