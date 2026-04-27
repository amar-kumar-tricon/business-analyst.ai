# Stage 1 + 2 Contracts (Locked)

This file is the source of truth for our incremental implementation.

## 1) State Contracts

- Shared state types live in [app/shared/state_types.py](../app/shared/state_types.py)
- Parent state: GraphState
- Stage 1 subgraph state: AnalyserState
- Stage 2 subgraph state: DiscoveryState
- Reducer fields (append semantics): qa_history, delta_changes, streaming_events

## 2) Stage 1 Score Criteria (weights)

- functional_requirements: 0.20
- business_logic: 0.15
- existing_system: 0.15
- target_audience: 0.10
- architecture_context: 0.15
- nfrs: 0.10
- timeline_budget: 0.10
- visual_assets: 0.05

## 3) Discovery Limits

- Max discovery questions per run: 10
- Loop terminates when any applies:
  - discovery_terminated is true
  - questions_asked_count >= 10
  - current_question is null
  - no unresolved open questions remain

## 4) Approval Status Values

- review_1_status: pending | edits_made | approved
- review_2_status: pending | edits_made | more_questions | approved

## 5) Delta Audit Format

- Every change to analyser output after initial generation must append a DeltaChange
- Delta source values: enrichment | qa | user_edit

## 6) No-Auth Rule (current phase)

- No auth dependencies in routes
- No user_id in GraphState
- No created_by fields in DB models for now
