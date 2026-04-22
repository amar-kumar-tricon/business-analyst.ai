# `app/agents/` — LangGraph agent layer

This is the brain 🧠 of the product. A single LangGraph `StateGraph` wires
four agents together with human-approval interrupts between every stage.

## Files in this folder

| File | Purpose |
|------|---------|
| `state.py` | The `GraphState` TypedDict — **the public contract** between every node. Every field is read or written by at least one agent. Change with care. |
| `graph.py` | Builds and compiles the `StateGraph`. One function, one file — the entire pipeline is visible here. `interrupt_before=[...]` lists every human-approval gate. Use `get_graph()` to obtain the compiled singleton. |
| `llm_factory.py` | Single place where LangChain `ChatOpenAI` / `ChatAnthropic` clients are constructed. Every agent calls `build_llm(agent_id, state)` so we can hot-swap providers without touching agent logic. `@lru_cache` keeps instantiation cheap. |

## Sub-packages (one per agent)

Each agent is a **folder with the same three files**:

```
<agent>/
├── agent.py     ← async node function accepted by LangGraph
├── prompts.py   ← system / user prompt templates (no Python logic)
└── tools.py     ← discrete, unit-testable helper functions
```

| Sub-package | Stage | Main function | Key tools |
|-------------|:-----:|---------------|-----------|
| `analyser/` | 1 | `analyser_node(state)` | `score_document`, `enrich`, `classify_moscow`, `extract_risks`, `recommend_team` |
| `discovery/` | 2 | `discovery_node(state)` | `generate_next_question`, `process_answer`, `apply_patch` |
| `architecture/` | 3 | `architecture_node(state)` | `generate_mermaid_dfd`, `generate_mermaid_userflow`, `generate_plantuml_system`, `generate_plantuml_er`, `generate_plantuml_deployment` |
| `sprint/` | 4 | `sprint_node(state)` | `decompose`, `story_point`, `allocate`, `mvp_cutoff`, `size_team` |

## Rules of the graph

1. **Nodes return partial state dicts.** LangGraph merges them into `GraphState`.
2. **Nodes are pure functions of `GraphState`** — no mutation of globals.
3. **Human approvals are `interrupt_before` checkpoints** on `human_review_N`
   placeholder nodes. The `/approve/{stage}` endpoint calls `graph.update_state(...)`
   with any edits, then `graph.invoke(None, ...)` to resume.
4. **Tools live in `tools.py`** and should be importable + testable without
   spinning up an LLM (write them as `async def foo(..., llm)` so juniors can
   mock `llm`).

## Pipeline (at a glance)

```mermaid
flowchart LR
    DI[document_ingestion] --> A[analyser_agent]
    A --> HR1[[human_review_1]]
    HR1 --> D[discovery_agent]
    D --> HR2[[human_review_2]]
    HR2 --> AR[architecture_agent]
    AR --> HR3[[human_review_3]]
    HR3 --> SP[sprint_agent]
    SP --> HR4[[human_review_4]]
    HR4 --> F([END])
```
