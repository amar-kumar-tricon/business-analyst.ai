from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone

from langgraph.graph import END, START, StateGraph

from app.agents.analyser import build_analyser_subgraph
from app.agents.discovery import build_discovery_subgraph
from app.agents.sprint import build_sprint_subgraph
from app.services.persistence import save_artifact, save_index
from app.services.rag import build_working_records
from app.shared.state_types import GraphState


def _now_iso() -> str:
    """Return current UTC time in ISO format."""
    return datetime.now(timezone.utc).isoformat()


def _chunk_id(project_id: str, heading: str, content: str) -> str:
    """Create a stable short ID for one chunk."""
    seed = f"{project_id}:{heading}:{content}".encode("utf-8")
    return hashlib.sha1(seed).hexdigest()[:16]


def ingest_node(state: GraphState) -> dict:
    """Prepare minimal parsed document structure before analysis starts."""
    updates: dict = {}

    if not state.get("parsed_documents"):
        parsed_documents = []
        for file_name in state.get("raw_files", []):
            parsed_documents.append(
                {
                    "file_name": file_name,
                    "file_type": "text/plain",
                    "s3_key": f"uploads/{state['project_id']}/{file_name}",
                    "sections": [
                        {
                            "file_name": file_name,
                            "section_heading": "Imported Context",
                            "page": 1,
                            "content_type": "text",
                            "content": state.get("additional_context", ""),
                            "raw_image_ref": None,
                        }
                    ],
                }
            )
        updates["parsed_documents"] = parsed_documents

    if state.get("review_1_status") is None:
        updates["review_1_status"] = "pending"
    if state.get("review_2_status") is None:
        updates["review_2_status"] = "pending"

    return updates


def raw_rag_index_node(state: GraphState) -> dict:
    """Build a working RAG index from parsed sections."""
    chunk_ids, records = build_working_records(state["project_id"], state.get("parsed_documents", []))

    index_path = save_index(
        project_id=state["project_id"],
        version=state["version"],
        kind="working",
        records=records,
    )

    return {
        "working_chunk_ids": chunk_ids,
        "streaming_events": [
            {
                "event_id": str(uuid.uuid4()),
                "type": "working_index_created",
                "node": "raw_rag_index_node",
                "payload": {
                    "index_path": index_path,
                    "chunk_count": len(chunk_ids),
                },
                "timestamp": _now_iso(),
            }
        ],
    }


def apply_review_1_edits_node(state: GraphState) -> dict:
    """Apply review-1 human edits from payload into analyser output."""
    payload = state.get("user_edits_payload") or {}
    analyser = state.get("analyser_output")
    if not analyser:
        return {"review_1_status": "approved"}

    deltas = []
    summary = payload.get("executive_summary")
    if isinstance(summary, str) and summary.strip() and summary != analyser.get("executive_summary"):
        deltas.append(
            {
                "change_id": str(uuid.uuid4()),
                "source": "user_edit",
                "source_ref": "review_1",
                "field_path": "analyser_output.executive_summary",
                "old_value": analyser.get("executive_summary"),
                "new_value": summary.strip(),
                "timestamp": _now_iso(),
            }
        )
        analyser = {**analyser, "executive_summary": summary.strip()}

    return {
        "analyser_output": analyser,
        "review_1_status": "approved",
        "delta_changes": deltas,
    }


def route_review_2_node(state: GraphState) -> dict:
    """No-op node used as a clean interrupt checkpoint before final routing."""
    _ = state
    return {}


def apply_review_2_edits_node(state: GraphState) -> dict:
    """Apply final human markdown edits before artifact export."""
    payload = state.get("user_edits_payload") or {}
    appendix = payload.get("final_doc_appendix")
    markdown = state.get("final_doc_markdown") or ""
    if not isinstance(appendix, str) or not appendix.strip():
        return {"review_2_status": "approved"}

    updated_markdown = f"{markdown}\n\n## Review Notes\n\n{appendix.strip()}\n"
    return {
        "final_doc_markdown": updated_markdown,
        "review_2_status": "approved",
        "delta_changes": [
            {
                "change_id": str(uuid.uuid4()),
                "source": "user_edit",
                "source_ref": "review_2",
                "field_path": "final_doc_markdown",
                "old_value": markdown,
                "new_value": updated_markdown,
                "timestamp": _now_iso(),
            }
        ],
    }


def approved_rag_index_node(state: GraphState) -> dict:
    """Save approved requirements/risks index for retrieval after sign-off."""
    analyser = state.get("analyser_output") or {}
    records = []

    for req in analyser.get("functional_requirements", []):
        records.append(
            {
                "kind": "requirement",
                "id": req.get("req_id"),
                "text": req.get("description", ""),
                "metadata": json.dumps({"moscow": req.get("moscow")}),
            }
        )
    for risk in analyser.get("risks", []):
        records.append(
            {
                "kind": "risk",
                "id": risk.get("risk_id"),
                "text": risk.get("description", ""),
                "metadata": json.dumps({"severity": risk.get("severity")}),
            }
        )

    index_path = save_index(
        project_id=state["project_id"],
        version=state["version"],
        kind="approved",
        records=records,
    )

    return {
        "streaming_events": [
            {
                "event_id": str(uuid.uuid4()),
                "type": "approved_index_created",
                "node": "approved_rag_index_node",
                "payload": {"index_path": index_path, "record_count": len(records)},
                "timestamp": _now_iso(),
            }
        ]
    }


def artifact_export_node(state: GraphState) -> dict:
    """Export markdown into md/pdf/docx artifacts.

    We try real generation first, then fallback to text placeholders.
    """
    markdown = state.get("final_doc_markdown") or "# Business Requirements Analysis\n\n_No content available._\n"
    md_key = save_artifact(state["project_id"], state["version"], "md", markdown)

    pdf_content: bytes | str
    try:
        from weasyprint import HTML

        pdf_content = HTML(string=f"<pre>{markdown}</pre>").write_pdf()
    except Exception:
        pdf_content = f"PDF_PLACEHOLDER\n\nGenerated from:\n{markdown}"

    try:
        from docx import Document
        from io import BytesIO

        document = Document()
        for line in markdown.splitlines():
            document.add_paragraph(line)
        buf = BytesIO()
        document.save(buf)
        docx_content: bytes | str = buf.getvalue()
    except Exception:
        docx_content = f"DOCX_PLACEHOLDER\n\nGenerated from:\n{markdown}"

    pdf_key = save_artifact(state["project_id"], state["version"], "pdf", pdf_content)
    docx_key = save_artifact(state["project_id"], state["version"], "docx", docx_content)

    return {
        "final_doc_markdown": markdown,
        "final_doc_pdf_s3_key": pdf_key,
        "final_doc_docx_s3_key": docx_key,
        "streaming_events": [
            {
                "event_id": str(uuid.uuid4()),
                "type": "artifacts_exported",
                "node": "artifact_export_node",
                "payload": {
                    "markdown": md_key,
                    "pdf": pdf_key,
                    "docx": docx_key,
                },
                "timestamp": _now_iso(),
            }
        ],
    }


# ──────────────────────────────────────────────
# Stage 3 — Mock Architecture Node
# (replaced by real Architecture Agent when ready)
# ──────────────────────────────────────────────

def mock_architecture_node(state: GraphState) -> dict:
    """
    Return a mocked ArchitectureResult.

    This node acts as a stand-in for the real Architecture Agent which is still
    under development.  Sprint Agent reads `architecture_output` from state;
    it will work with real data once the Architecture Agent is wired in.
    """
    analyser = state.get("analyser_output") or {}
    reqs = analyser.get("functional_requirements", [])
    team = analyser.get("recommended_team", {})
    roles = team.get("roles", ["Backend Developer", "Frontend Developer"])

    mermaid_data_flow = (
        "flowchart TD\n"
        "    User([User / Product Manager]) -->|Upload Docs| UploadUI[Upload UI]\n"
        "    UploadUI -->|multipart/form-data| FastAPI[FastAPI Backend]\n"
        "    FastAPI -->|parse + chunk| DocParser[Document Parser]\n"
        "    DocParser -->|sections| RAGIndex[(RAG Index)]\n"
        "    FastAPI -->|invoke graph| LangGraph[LangGraph Pipeline]\n"
        "    LangGraph -->|read chunks| RAGIndex\n"
        "    LangGraph -->|write outputs| SQLite[(SQLite DB)]\n"
        "    LangGraph -->|stream events| WebSocket[WebSocket /ws]\n"
        "    WebSocket -->|live tokens| FrontendUI[React Frontend]\n"
        "    SQLite -->|query| FastAPI\n"
        "    FastAPI -->|JSON response| FrontendUI\n"
    )

    mermaid_user_flow = (
        "sequenceDiagram\n"
        "    participant PM as Product Manager\n"
        "    participant UI as React UI\n"
        "    participant API as FastAPI\n"
        "    participant Graph as LangGraph\n"
        "    PM->>UI: Upload requirement docs\n"
        "    UI->>API: POST /projects/{id}/files\n"
        "    PM->>UI: Trigger analysis\n"
        "    UI->>API: POST /projects/{id}/run\n"
        "    API->>Graph: Run Analyser + Discovery stages\n"
        "    Graph-->>API: Stream events via WebSocket\n"
        "    API-->>UI: Live status updates\n"
        "    PM->>UI: Review & approve Stage 1\n"
        "    UI->>API: POST /projects/{id}/discovery/answer\n"
        "    PM->>UI: Approve architecture (Stage 3)\n"
        "    UI->>API: POST /projects/{id}/architecture/approve\n"
        "    API->>Graph: Run Sprint Agent (Stage 4)\n"
        "    Graph-->>API: SprintPlan generated\n"
        "    PM->>UI: Review & approve Sprint Plan\n"
        "    UI->>API: POST /projects/{id}/sprint/approve\n"
    )

    plantuml_system = (
        "@startuml\n"
        "!theme plain\n"
        "package \"Frontend\" {\n"
        "  [React SPA] as UI\n"
        "}\n"
        "package \"API Layer\" {\n"
        "  [FastAPI] as API\n"
        "  [WebSocket Handler] as WS\n"
        "}\n"
        "package \"Agent Layer\" {\n"
        "  [Analyser Agent] as Analyser\n"
        "  [Discovery Agent] as Discovery\n"
        "  [Architecture Agent] as Architecture\n"
        "  [Sprint Agent] as Sprint\n"
        "}\n"
        "package \"Data Layer\" {\n"
        "  database \"SQLite\" as DB\n"
        "  folder \"File Storage\" as FS\n"
        "}\n"
        "UI --> API : REST calls\n"
        "UI --> WS : WebSocket stream\n"
        "API --> Analyser : invoke\n"
        "Analyser --> Discovery : state handoff\n"
        "Discovery --> Architecture : state handoff\n"
        "Architecture --> Sprint : state handoff\n"
        "API --> DB : read/write\n"
        "API --> FS : upload/download\n"
        "@enduml\n"
    )

    diagrams = [
        {
            "diagram_id": str(uuid.uuid4()),
            "title": "System Architecture",
            "diagram_type": "system_architecture",
            "tool": "plantuml",
            "dsl": plantuml_system,
            "description": "Component-level view of the full BRA Tool system.",
        },
        {
            "diagram_id": str(uuid.uuid4()),
            "title": "Data Flow",
            "diagram_type": "data_flow",
            "tool": "mermaid",
            "dsl": mermaid_data_flow,
            "description": "How data moves from document upload to sprint plan generation.",
        },
        {
            "diagram_id": str(uuid.uuid4()),
            "title": "User Flow",
            "diagram_type": "user_flow",
            "tool": "mermaid",
            "dsl": mermaid_user_flow,
            "description": "End-to-end journey for Product Manager through all 4 stages.",
        },
    ]

    tech_stack_notes = (
        f"Backend: FastAPI + Python 3.12. "
        f"Agent framework: LangGraph. "
        f"Database: SQLite (dev) → PostgreSQL (prod). "
        f"Team roles derived from analysis: {', '.join(roles)}."
    )

    architecture_output = {
        "diagrams": diagrams,
        "tech_stack_notes": tech_stack_notes,
        "generated_at": _now_iso(),
        "is_mocked": True,
    }

    return {
        "architecture_output": architecture_output,
        "review_3_status": "pending",
        "streaming_events": [
            {
                "event_id": str(uuid.uuid4()),
                "type": "architecture_generated",
                "node": "mock_architecture_node",
                "payload": {
                    "diagram_count": len(diagrams),
                    "is_mocked": True,
                },
                "timestamp": _now_iso(),
            }
        ],
    }


def apply_review_3_edits_node(state: GraphState) -> dict:
    """Approve Stage-3 architecture output (with optional edits)."""
    return {"review_3_status": "approved"}


def apply_review_4_edits_node(state: GraphState) -> dict:
    """Approve Stage-4 sprint plan (with optional edits)."""
    payload = state.get("user_edits_payload") or {}
    sprint_plan = state.get("sprint_plan") or {}

    # Allow free-text notes to be appended to the sprint plan
    notes = payload.get("sprint_notes")
    if isinstance(notes, str) and notes.strip():
        sprint_plan = {**sprint_plan, "reviewer_notes": notes.strip()}

    return {
        "sprint_plan": sprint_plan,
        "review_4_status": "approved",
    }


# ──────────────────────────────────────────────
# Routing helpers
# ──────────────────────────────────────────────

def _route_after_analyser(state: GraphState) -> str:
    """Choose next node after Stage-1 human review decision."""
    return "discovery_stage_node" if state["review_1_status"] == "approved" else "apply_review_1_edits_node"


def _route_after_review_2(state: GraphState) -> str:
    """Choose next node after Stage-2 human review decision."""
    if state["review_2_status"] == "more_questions":
        return "discovery_stage_node"
    if state["review_2_status"] == "approved":
        return "approved_rag_index_node"
    return "apply_review_2_edits_node"


def _route_after_review_3(state: GraphState) -> str:
    """Choose next node after Stage-3 architecture review decision."""
    if state.get("review_3_status") == "regenerate":
        return "mock_architecture_node"
    return "apply_review_3_edits_node"


def build_parent_graph():
    """Build the full parent graph: Analyser → Discovery → Architecture → Sprint → Export."""
    analyser_subgraph = build_analyser_subgraph()
    discovery_subgraph = build_discovery_subgraph()
    sprint_subgraph = build_sprint_subgraph()

    graph = StateGraph(GraphState)

    # ── Nodes ──────────────────────────────────────────────────────────────────
    graph.add_node("ingest_node", ingest_node)
    graph.add_node("raw_rag_index_node", raw_rag_index_node)

    # Stage 1 — Analyser
    graph.add_node("analyser_stage_node", analyser_subgraph)
    graph.add_node("apply_review_1_edits_node", apply_review_1_edits_node)

    # Stage 2 — Discovery
    graph.add_node("discovery_stage_node", discovery_subgraph)
    graph.add_node("route_review_2_node", route_review_2_node)
    graph.add_node("apply_review_2_edits_node", apply_review_2_edits_node)
    graph.add_node("approved_rag_index_node", approved_rag_index_node)

    # Stage 3 — Architecture (mocked until real agent is ready)
    graph.add_node("mock_architecture_node", mock_architecture_node)
    graph.add_node("apply_review_3_edits_node", apply_review_3_edits_node)

    # Stage 4 — Sprint Planning
    graph.add_node("sprint_stage_node", sprint_subgraph)
    graph.add_node("apply_review_4_edits_node", apply_review_4_edits_node)

    # Export
    graph.add_node("artifact_export_node", artifact_export_node)

    # ── Edges ──────────────────────────────────────────────────────────────────

    # Ingest → Analyser
    graph.add_edge(START, "ingest_node")
    graph.add_edge("ingest_node", "raw_rag_index_node")
    graph.add_edge("raw_rag_index_node", "analyser_stage_node")

    # Analyser review gate (Stage 1)
    graph.add_conditional_edges(
        "analyser_stage_node",
        _route_after_analyser,
        {
            "apply_review_1_edits_node": "apply_review_1_edits_node",
            "discovery_stage_node": "discovery_stage_node",
        },
    )
    graph.add_edge("apply_review_1_edits_node", "discovery_stage_node")

    # Discovery → review gate (Stage 2)
    graph.add_edge("discovery_stage_node", "route_review_2_node")
    graph.add_conditional_edges(
        "route_review_2_node",
        _route_after_review_2,
        {
            "apply_review_2_edits_node": "apply_review_2_edits_node",
            "discovery_stage_node": "discovery_stage_node",
            "approved_rag_index_node": "approved_rag_index_node",
        },
    )
    graph.add_edge("apply_review_2_edits_node", "approved_rag_index_node")

    # After discovery approval → Architecture (Stage 3)
    graph.add_edge("approved_rag_index_node", "mock_architecture_node")

    # Architecture review gate (Stage 3)
    graph.add_conditional_edges(
        "mock_architecture_node",
        _route_after_review_3,
        {
            "mock_architecture_node": "mock_architecture_node",
            "apply_review_3_edits_node": "apply_review_3_edits_node",
        },
    )
    graph.add_edge("apply_review_3_edits_node", "sprint_stage_node")

    # Sprint review gate (Stage 4) → Export
    graph.add_edge("sprint_stage_node", "apply_review_4_edits_node")
    graph.add_edge("apply_review_4_edits_node", "artifact_export_node")
    graph.add_edge("artifact_export_node", END)

    return graph.compile(
        interrupt_before=[
            "apply_review_1_edits_node",
            "route_review_2_node",
            "apply_review_3_edits_node",
            "apply_review_4_edits_node",
        ]
    )

def get_graph():
    """Return compiled parent graph instance."""
    return build_parent_graph()
