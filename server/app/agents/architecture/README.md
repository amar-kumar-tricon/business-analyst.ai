# Architecture Agent — Stage 3

## Files
| File | Purpose |
|------|---------|
| `agent.py` | `architecture_node(state)` — reads finalised `analyser_output` and produces all five diagrams. Writes the result to `state.architecture_output`. |
| `prompts.py` | `SYSTEM` prompt describing every diagram type and its target DSL. |
| `tools.py` | One function per diagram: `generate_mermaid_dfd`, `generate_mermaid_userflow`, `generate_plantuml_system`, `generate_plantuml_er`, `generate_plantuml_deployment`. Each returns a DSL string. |

## Rendering model
- **Mermaid** DSL → rendered in the browser by `client/src/pages/ArchitecturePage.tsx` using the `mermaid` npm package.
- **PlantUML** DSL → returned as-is; the frontend can render via the public PlantUML service or we can add a local Kroki renderer later. **No Java required in this repo.**
- DSL validation lives in `services/diagram_service.py::validate_mermaid` and `validate_plantuml`.
