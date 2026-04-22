# Discovery / QnA Agent — Stage 2

## Files
| File | Purpose |
|------|---------|
| `agent.py` | `discovery_node(state)` — re-entrant node. Each invocation generates ONE next question (or returns when `open_questions` is empty). The `/discovery/answer` endpoint records an answer and re-invokes the node. |
| `prompts.py` | `SYSTEM`, `NEXT_QUESTION`, `PROCESS_ANSWER`. The `<DONE>` sentinel in `SYSTEM` signals "no more questions". |
| `tools.py` | `generate_next_question`, `process_answer`, `apply_patch`. `apply_patch` performs the back-channel update to `state.analyser_output` (BRD §6.4). |

## How to extend
- **Adaptive follow-ups** → feed `history` into `generate_next_question`.
- **Change answer-triggered update** → edit `process_answer` + `apply_patch`.
