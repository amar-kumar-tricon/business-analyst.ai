"""
app.agents.architecture.tools
=============================
LLM-powered diagram generators.

Each function:
    - Builds a strict prompt from analyser_output
    - Calls the LLM (via llm_gateway)
    - Returns ONLY valid DSL (or a deterministic fallback)
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
    return f"""PROJECT SUMMARY: {summary}

FUNCTIONAL REQUIREMENTS:
{fr_lines}

RISKS:
{risk_lines}

TEAM: {json.dumps(team, default=str)}"""


# ---- Mermaid: Data Flow Diagram ----

_DFD_FALLBACK = """\
flowchart LR
    Client([Client]) --> API[API Gateway]
    API --> Auth[Auth Service]
    API --> Core[Core Service]
    Core --> DB[(Database)]
    Core --> Ext[External API]
"""


def generate_mermaid_dfd(analyser_output: dict) -> str:
    context = _summarize_context(analyser_output)
    prompt = f"""You are a senior software architect. Based on the project context below, generate a Mermaid Data Flow Diagram.

STRICT RULES:
1. Return ONLY a JSON object: {{"dsl": "<mermaid code>"}}
2. The "dsl" value MUST start with "flowchart LR"
3. Use actual component names derived from the project requirements (not generic placeholders)
4. Show data flows between: users/clients, API layer, business services, databases, and external integrations
5. Use proper Mermaid syntax: ([...]) for external entities, [...] for processes, [(...)] for data stores
6. Do NOT add any explanation, markdown fences, or extra keys
7. Keep it to 8-15 nodes maximum for readability

{context}

Return ONLY the JSON object with the "dsl" key. No markdown fences."""
    result = call_structured_json(prompt, {"dsl": _DFD_FALLBACK})
    return _extract_dsl(result, "dsl", _DFD_FALLBACK)


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


def generate_mermaid_userflow(analyser_output: dict) -> str:
    context = _summarize_context(analyser_output)
    prompt = f"""You are a senior software architect. Based on the project context below, generate a Mermaid Sequence Diagram showing the primary user journey.

STRICT RULES:
1. Return ONLY a JSON object: {{"dsl": "<mermaid code>"}}
2. The "dsl" value MUST start with "sequenceDiagram"
3. Derive the user journey from the actual functional requirements — show the critical path a user takes
4. Include participants like: actor User, Frontend, API, relevant services, Database
5. Use proper Mermaid sequence syntax: ->>, -->>
6. Show 6-12 interactions maximum for readability
7. Do NOT add any explanation, markdown fences, or extra keys

{context}

Return ONLY the JSON object with the "dsl" key. No markdown fences."""
    result = call_structured_json(prompt, {"dsl": _USERFLOW_FALLBACK})
    return _extract_dsl(result, "dsl", _USERFLOW_FALLBACK)


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


def generate_plantuml_system(analyser_output: dict) -> str:
    context = _summarize_context(analyser_output)
    prompt = f"""You are a senior software architect. Based on the project context below, generate a PlantUML System Architecture Diagram.

STRICT RULES:
1. Return ONLY a JSON object: {{"dsl": "<plantuml code>"}}
2. The "dsl" value MUST start with "@startuml" and end with "@enduml"
3. Derive components from the actual project requirements — name services, databases, and integrations based on the real system
4. Use: actor, rectangle, database, cloud, queue, component as appropriate
5. Show connections with labeled arrows (e.g. --> with : label)
6. Keep it readable — max 10-12 components
7. Do NOT add any explanation, markdown fences, or extra keys

{context}

Return ONLY the JSON object with the "dsl" key. No markdown fences."""
    result = call_structured_json(prompt, {"dsl": _SYSTEM_FALLBACK})
    return _extract_dsl(result, "dsl", _SYSTEM_FALLBACK)


# ---- PlantUML: ER Diagram ----

_ER_FALLBACK = """\
@startuml
!theme plain
entity "User" as user {{
  * id : uuid <<PK>>
  --
  name : varchar
  email : varchar
}}

entity "Project" as project {{
  * id : uuid <<PK>>
  --
  name : varchar
  status : varchar
  created_at : timestamp
}}

user ||--o{{ project : owns
@enduml
"""


def generate_plantuml_er(analyser_output: dict) -> str:
    context = _summarize_context(analyser_output)
    prompt = f"""You are a senior software architect. Based on the project context below, generate a PlantUML Entity Relationship Diagram.

STRICT RULES:
1. Return ONLY a JSON object: {{"dsl": "<plantuml code>"}}
2. The "dsl" value MUST start with "@startuml" and end with "@enduml"
3. Derive entities and relationships from the actual functional requirements
4. Each entity must have: primary key field(s), 2-5 relevant attribute fields
5. Show cardinality: ||--o{{ (one-to-many), ||--|| (one-to-one), }}--{{ (many-to-many)
6. Include 4-8 entities maximum
7. Do NOT add any explanation, markdown fences, or extra keys

{context}

Return ONLY the JSON object with the "dsl" key. No markdown fences."""
    result = call_structured_json(prompt, {"dsl": _ER_FALLBACK})
    return _extract_dsl(result, "dsl", _ER_FALLBACK)


# ---- PlantUML: Deployment Diagram ----

_DEPLOYMENT_FALLBACK = """\
@startuml
!theme plain
node "Web Server" as web {{
  [Frontend SPA]
}}
node "App Server" as app_server {{
  [API Service]
}}
database "Database" as db
cloud "Cloud Services" as cloud

web --> app_server : HTTPS
app_server --> db : SQL
app_server --> cloud : REST
@enduml
"""


def generate_plantuml_deployment(analyser_output: dict) -> str:
    context = _summarize_context(analyser_output)
    prompt = f"""You are a senior software architect. Based on the project context below, generate a PlantUML Deployment Diagram.

STRICT RULES:
1. Return ONLY a JSON object: {{"dsl": "<plantuml code>"}}
2. The "dsl" value MUST start with "@startuml" and end with "@enduml"
3. Show the infrastructure: web servers, app servers, databases, caches, CDN, cloud services
4. Derive the deployment architecture from the actual project requirements
5. Use: node, database, cloud, queue, rectangle for different component types
6. Label connections with protocols (HTTPS, SQL, gRPC, REST, etc.)
7. Do NOT add any explanation, markdown fences, or extra keys

{context}

Return ONLY the JSON object with the "dsl" key. No markdown fences."""
    result = call_structured_json(prompt, {"dsl": _DEPLOYMENT_FALLBACK})
    return _extract_dsl(result, "dsl", _DEPLOYMENT_FALLBACK)
