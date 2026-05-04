"""
app.agents.architecture.tools
=============================
LLM-powered diagram generators.

Each function:
    - Builds a strict prompt
    - Calls the LLM (via llm_gateway)
    - Returns ONLY valid DSL (or a deterministic fallback)
"""
from __future__ import annotations

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
    prompt = f"""
Return a JSON object with a single key "dsl" containing a Mermaid Data Flow Diagram.

STRICT RULES:
- The value of "dsl" must start with: flowchart LR
- No explanations, only the JSON object
- Include: Client, API, DB, External services if relevant

CONTEXT:
{analyser_output}
"""
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
    prompt = f"""
Return a JSON object with a single key "dsl" containing a Mermaid Sequence Diagram for the user flow.

STRICT RULES:
- The value of "dsl" must start with: sequenceDiagram
- No explanations, only the JSON object
- Show the key user journey

CONTEXT:
{analyser_output}
"""
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
    prompt = f"""
Return a JSON object with a single key "dsl" containing a PlantUML System Architecture Diagram.

STRICT RULES:
- Must start with @startuml and end with @enduml
- No explanations, only the JSON object
- Include: frontend, backend, database, external APIs

CONTEXT:
{analyser_output}
"""
    result = call_structured_json(prompt, {"dsl": _SYSTEM_FALLBACK})
    return _extract_dsl(result, "dsl", _SYSTEM_FALLBACK)


# ---- PlantUML: ER Diagram ----

_ER_FALLBACK = """\
@startuml
!theme plain
entity "User" as user {
  * id : uuid <<PK>>
  --
  name : varchar
  email : varchar
}

entity "Project" as project {
  * id : uuid <<PK>>
  --
  name : varchar
  status : varchar
  created_at : timestamp
}

user ||--o{ project : owns
@enduml
"""


def generate_plantuml_er(analyser_output: dict) -> str:
    prompt = f"""
Return a JSON object with a single key "dsl" containing a PlantUML ER Diagram.

STRICT RULES:
- Use entity definitions with relationships
- Must start with @startuml and end with @enduml
- No explanations, only the JSON object

CONTEXT:
{analyser_output}
"""
    result = call_structured_json(prompt, {"dsl": _ER_FALLBACK})
    return _extract_dsl(result, "dsl", _ER_FALLBACK)


# ---- PlantUML: Deployment Diagram ----

_DEPLOYMENT_FALLBACK = """\
@startuml
!theme plain
node "Web Server" as web {
  [Frontend SPA]
}
node "App Server" as app_server {
  [API Service]
}
database "Database" as db
cloud "Cloud Services" as cloud

web --> app_server : HTTPS
app_server --> db : SQL
app_server --> cloud : REST
@enduml
"""


def generate_plantuml_deployment(analyser_output: dict) -> str:
    prompt = f"""
Return a JSON object with a single key "dsl" containing a PlantUML Deployment Diagram.

STRICT RULES:
- Must start with @startuml and end with @enduml
- Show cloud, services, database
- No explanations, only the JSON object

CONTEXT:
{analyser_output}
"""
    result = call_structured_json(prompt, {"dsl": _DEPLOYMENT_FALLBACK})
    return _extract_dsl(result, "dsl", _DEPLOYMENT_FALLBACK)
