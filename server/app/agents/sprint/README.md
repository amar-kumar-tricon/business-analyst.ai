# Sprint Planning Agent — Stage 4

## Files
| File | Purpose |
|------|---------|
| `agent.py` | `sprint_node(state)` — reads finalised `analyser_output` + `architecture_output` and writes a `SprintPlanOut` to `state.sprint_plan`. |
| `prompts.py` | `SYSTEM` prompt with default assumptions: 2-week sprints, velocity 40 pts/sprint/2 devs, 1 point ≈ 4 man-hours. |
| `tools.py` | `decompose` · `story_point` · `allocate(velocity=40)` · `mvp_cutoff` · `size_team`. The `allocate` function is a pure greedy packer and is unit-testable. |

## How to extend
- **Change velocity / hours-per-point** → edit `SYSTEM` prompt + default arg of `allocate`.
- **Different MVP rule** → rewrite `tools.mvp_cutoff` (e.g., use a priority score).
- **Extra team roles** → extend `size_team` to inspect which services appear in `architecture_output`.
