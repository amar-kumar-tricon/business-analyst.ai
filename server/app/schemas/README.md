# `app/schemas/` — Pydantic request / response models

Pure data contracts. No SQLAlchemy, no HTTP, no LLM code. These types flow
between the route handlers, the agent nodes, and the TypeScript types in
`client/src/types/`.

## Files

| File | Contains | Used by |
|------|----------|---------|
| `project.py` | `ProjectCreate`, `ProjectOut`, `ApprovalRequest`, `ExportRequest`, `StageName` literal | `api/v1/projects.py`, `export.py` |
| `analyser.py` | `AnalyserResult` + `ProjectOverview`, `FunctionalRequirements`, `Risk`, `TeamRole`, `CompletenessScore` | Stage 1 agent output |
| `discovery.py` | `QAExchange`, `DiscoveryState`, `DiscoveryAnswerIn` | Stage 2 agent + route |
| `architecture.py` | `MermaidDiagram`, `PlantUMLDiagram`, `ArchitectureOut` | Stage 3 agent output |
| `sprint.py` | `Story`, `Sprint`, `TeamRole`, `SprintPlanOut` | Stage 4 agent output |
| `settings.py` | `LLMConfigIn`, `LLMConfigOut`, `AgentId`, `Provider` literals | `api/v1/settings.py` |

## Convention

When you change a schema here, mirror the change in
[client/src/types/index.ts](../../../client/src/types/index.ts) so the frontend
types stay in sync. There is no code-gen step — we keep the surface small
enough that hand-syncing is reliable.
