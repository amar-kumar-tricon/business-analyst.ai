"""
app.agents.architecture.tools
=============================
LLM-powered diagram generators.

Each function:
    - Builds a strict prompt from analyser_output
    - Calls the LLM (via llm_gateway)
    - Returns a dict with "dsl" and "explanation" keys
"""
from __future__ import annotations

import json
from app.services.llm_gateway import call_structured_json


def _extract_dsl(result: dict, key: str, fallback: str) -> str:
    """Pull the DSL string out of a JSON response, stripping markdown fences."""
    raw = result.get(key, fallback)
    if not isinstance(raw, str):
        return fallback
    content = raw.strip()
    if content.startswith("```"):
        lines = content.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        content = "\n".join(lines).strip()
    return content or fallback


def _extract_explanation(result: dict) -> str:
    """Pull the explanation string from a JSON response."""
    return str(result.get("explanation", "")).strip()


def _summarize_context(analyser_output: dict) -> str:
    """Build a concise context string from the analyser output for prompts."""
    summary = analyser_output.get("executive_summary", "")
    frs = analyser_output.get("functional_requirements", [])
    fr_lines = "\n".join(
        f"  - [{fr.get('moscow', 'N/A')}] {fr.get('description', '')}"
        for fr in frs[:20]
    )
    risks = analyser_output.get("risks", [])
    risk_lines = "\n".join(
        f"  - [{r.get('severity', 'N/A')}] {r.get('description', '')}"
        for r in risks[:10]
    )
    team = analyser_output.get("recommended_team", {})
    return (
        f"PROJECT SUMMARY: {summary}\n\n"
        f"FUNCTIONAL REQUIREMENTS:\n{fr_lines}\n\n"
        f"RISKS:\n{risk_lines}\n\n"
        f"TEAM: {json.dumps(team, default=str)}"
    )


# ---- Mermaid: Data Flow Diagram ----

_DFD_FALLBACK = """\
flowchart LR
    Client([Client]) --> API[API Gateway]
    API --> Auth[Auth Service]
    API --> Core[Core Service]
    Core --> DB[(Database)]
    Core --> Ext[External API]
"""


def generate_mermaid_dfd(analyser_output: dict) -> dict:
    context = _summarize_context(analyser_output)
    prompt = (
        "You are a senior software architect. Based on the project context below, "
        "generate a Mermaid **flowchart** Data Flow Diagram.\n\n"
        "STRICT RULES:\n"
        '1. Return ONLY a JSON object: {"dsl": "<mermaid code>", "explanation": "<1-2 sentence description>"}\n'
        '2. The "dsl" value MUST start with "flowchart LR" on its own line\n'
        "3. Use ONLY valid Mermaid flowchart syntax. NEVER use 'participant' or 'sequenceDiagram' keywords.\n"
        "4. Node syntax:\n"
        "   - Round-edge: A([External Entity])\n"
        "   - Rectangle:  B[Process Name]\n"
        "   - Cylinder:   C[(Database)]\n"
        "5. Arrow syntax: A --> B or A -->|label| B\n"
        "6. Each node ID must be a simple alphanumeric string (no spaces, no special chars)\n"
        "7. Put each node definition and arrow on its OWN line. Do NOT use semicolons to join statements.\n"
        "8. Use actual component names from the project requirements\n"
        "9. Keep it to 8-15 nodes maximum\n\n"
        "EXAMPLE of valid flowchart DSL (note: each statement on its own line):\n"
        "flowchart LR\n"
        "    User([User]) -->|uploads file| WebUI[Web Interface]\n"
        "    WebUI -->|POST /api| API[API Gateway]\n"
        "    API --> Auth[Auth Service]\n"
        "    API --> Core[Core Service]\n"
        "    Core --> DB[(Database)]\n"
        "    Core -->|calls| ExtAPI([External API])\n\n"
        f"{context}\n\n"
        "Return ONLY the JSON object. No markdown fences."
    )
    fallback = {"dsl": _DFD_FALLBACK, "explanation": "Default data flow diagram."}
    result = call_structured_json(prompt, fallback)
    return {"dsl": _extract_dsl(result, "dsl", _DFD_FALLBACK), "explanation": _extract_explanation(result)}


# ---- Mermaid: User Flow ----

_USERFLOW_FALLBACK = """\
sequenceDiagram
    actor User
    User->>App: Opens application
    App->>API: Request data
    API->>DB: Query
    DB-->>API: Result
    API-->>App: Response
    App-->>User: Display
"""


def generate_mermaid_userflow(analyser_output: dict) -> dict:
    context = _summarize_context(analyser_output)
    prompt = (
        "You are a senior software architect. Based on the project context below, "
        "generate a Mermaid **sequenceDiagram** showing the primary user journey.\n\n"
        "STRICT RULES:\n"
        '1. Return ONLY a JSON object: {"dsl": "<mermaid code>", "explanation": "<1-2 sentence description>"}\n'
        '2. The "dsl" value MUST start with "sequenceDiagram" on its own line\n'
        "3. Use ONLY valid Mermaid sequence syntax. NEVER use flowchart syntax.\n"
        '4. Participant syntax: "participant Name" or "actor Name" — each on its own line\n'
        "5. Arrow syntax: A->>B: label  or  B-->>A: response\n"
        "6. Each statement on its own line. Do NOT use semicolons to join statements.\n"
        "7. Derive the user journey from the actual functional requirements\n"
        "8. Show 6-12 interactions maximum\n\n"
        "EXAMPLE of valid sequenceDiagram DSL:\n"
        "sequenceDiagram\n"
        "    actor User\n"
        "    participant Frontend\n"
        "    participant API\n"
        "    participant DB\n"
        "    User->>Frontend: Open app\n"
        "    Frontend->>API: GET /data\n"
        "    API->>DB: Query\n"
        "    DB-->>API: Result\n"
        "    API-->>Frontend: JSON response\n"
        "    Frontend-->>User: Display data\n\n"
        f"{context}\n\n"
        "Return ONLY the JSON object. No markdown fences."
    )
    fallback = {"dsl": _USERFLOW_FALLBACK, "explanation": "Default user flow diagram."}
    result = call_structured_json(prompt, fallback)
    return {"dsl": _extract_dsl(result, "dsl", _USERFLOW_FALLBACK), "explanation": _extract_explanation(result)}


# ---- PlantUML: System Architecture ----

_SYSTEM_FALLBACK = """\
@startuml
!theme plain
actor User
rectangle "Frontend" as FE
rectangle "Backend API" as BE
database "Database" as DB
cloud "External APIs" as EXT

User --> FE
FE --> BE
BE --> DB
BE --> EXT
@enduml
"""


def generate_plantuml_system(analyser_output: dict) -> dict:
    context = _summarize_context(analyser_output)
    prompt = (
        "You are a senior software architect. Based on the project context below, "
        "generate a PlantUML System Architecture Diagram.\n\n"
        "STRICT RULES:\n"
        '1. Return ONLY a JSON object: {"dsl": "<plantuml code>", "explanation": "<1-2 sentence description>"}\n'
        '2. The "dsl" value MUST start with "@startuml" and end with "@enduml"\n'
        "3. Derive components from the actual project requirements\n"
        "4. Use: actor, rectangle, database, cloud, queue, component as appropriate\n"
        "5. Show connections with labeled arrows (e.g. --> : label)\n"
        "6. Keep it readable — max 10-12 components\n\n"
        f"{context}\n\n"
        "Return ONLY the JSON object. No markdown fences."
    )
    fallback = {"dsl": _SYSTEM_FALLBACK, "explanation": "Default system architecture diagram."}
    result = call_structured_json(prompt, fallback)
    return {"dsl": _extract_dsl(result, "dsl", _SYSTEM_FALLBACK), "explanation": _extract_explanation(result)}


# ---- PlantUML: ER Diagram ----

_ER_FALLBACK = """\
@startuml
!theme plain
entity "User" {
  * id : uuid <<PK>>
  --
  name : varchar
  email : varchar
}

entity "Project" {
  * id : uuid <<PK>>
  --
  name : varchar
  status : varchar
  created_at : timestamp
}

User ||--o{ Project : owns
@enduml
"""


def generate_plantuml_er(analyser_output: dict) -> dict:
    context = _summarize_context(analyser_output)
    prompt = (
        "You are a senior software architect. Based on the project context below, "
        "generate a PlantUML Entity Relationship Diagram.\n\n"
        "STRICT RULES:\n"
        '1. Return ONLY a JSON object: {"dsl": "<plantuml code>", "explanation": "<1-2 sentence description>"}\n'
        '2. The "dsl" value MUST start with "@startuml" and end with "@enduml"\n'
        "3. Derive entities and relationships from the actual functional requirements\n"
        "4. Each entity must have: primary key field(s), 2-5 relevant attribute fields\n"
        "5. Show cardinality: ||--o{ (one-to-many), ||--|| (one-to-one)\n"
        "6. Include 4-8 entities maximum\n\n"
        f"{context}\n\n"
        "Return ONLY the JSON object. No markdown fences."
    )
    fallback = {"dsl": _ER_FALLBACK, "explanation": "Default entity relationship diagram."}
    result = call_structured_json(prompt, fallback)
    return {"dsl": _extract_dsl(result, "dsl", _ER_FALLBACK), "explanation": _extract_explanation(result)}


# ---- PlantUML: Deployment Diagram ----

_DEPLOYMENT_FALLBACK = """\
@startuml
!theme plain
node "Web Server" {
  [Frontend SPA]
}
node "App Server" {
  [API Service]
}
database "Database" as db
cloud "Cloud Services" as cloud

[Frontend SPA] --> [API Service] : HTTPS
[API Service] --> db : SQL
[API Service] --> cloud : REST
@enduml
"""


def generate_plantuml_deployment(analyser_output: dict) -> dict:
    context = _summarize_context(analyser_output)
    prompt = (
        "You are a senior software architect. Based on the project context below, "
        "generate a PlantUML Deployment Diagram.\n\n"
        "STRICT RULES:\n"
        '1. Return ONLY a JSON object: {"dsl": "<plantuml code>", "explanation": "<1-2 sentence description>"}\n'
        '2. The "dsl" value MUST start with "@startuml" and end with "@enduml"\n'
        "3. Show the infrastructure: web servers, app servers, databases, caches, CDN, cloud services\n"
        "4. Derive the deployment architecture from the actual project requirements\n"
        "5. Use: node, database, cloud, queue, rectangle for different component types\n"
        "6. Label connections with protocols (HTTPS, SQL, gRPC, REST, etc.)\n\n"
        f"{context}\n\n"
        "Return ONLY the JSON object. No markdown fences."
    )
    fallback = {"dsl": _DEPLOYMENT_FALLBACK, "explanation": "Default deployment diagram."}
    result = call_structured_json(prompt, fallback)
    return {"dsl": _extract_dsl(result, "dsl", _DEPLOYMENT_FALLBACK), "explanation": _extract_explanation(result)}
