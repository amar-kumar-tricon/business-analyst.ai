"""
app.agents.architecture.tools
=============================
Diagram generator helpers. Each function returns a DSL string; rendering to SVG
is handled by `services.diagram_service`.
"""
from __future__ import annotations

from typing import Any


async def generate_mermaid_dfd(analyser_output: Any, llm: Any) -> str:
    """Return Mermaid flowchart DSL for the data flow diagram."""
    # TODO: prompt llm with SYSTEM + analyser_output; return DSL.
    return "flowchart LR\n  A[Client] --> B[API]\n  B --> C[(DB)]"


async def generate_mermaid_userflow(analyser_output: Any, llm: Any) -> str:
    return "sequenceDiagram\n  User->>API: request\n  API-->>User: response"


async def generate_plantuml_system(analyser_output: Any, llm: Any) -> str:
    return "@startuml\nactor User\nUser -> Frontend\nFrontend -> Backend\n@enduml"


async def generate_plantuml_er(analyser_output: Any, llm: Any) -> str:
    return "@startuml\nentity Project\nentity Document\nProject ||--o{ Document\n@enduml"


async def generate_plantuml_deployment(analyser_output: Any, llm: Any) -> str:
    return "@startuml\ncloud Internet\nnode API\ndatabase Postgres\nInternet -> API\nAPI -> Postgres\n@enduml"
