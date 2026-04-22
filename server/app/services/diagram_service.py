"""
app.services.diagram_service
============================
Lightweight diagram helpers.

For the local-only MVP, PlantUML rendering is NOT done server-side (that would
require a Java runtime). Instead, we return PlantUML DSL to the client; the
frontend can render it using https://www.plantuml.com/plantuml/svg/<encoded>
or a local Kroki/PlantUML service can be wired in later.

Mermaid is rendered entirely in the browser — we only validate the DSL here
to catch obvious syntax errors before storing it.
"""
from __future__ import annotations

_MERMAID_KEYWORDS = (
    "graph",
    "flowchart",
    "sequenceDiagram",
    "stateDiagram",
    "stateDiagram-v2",
    "erDiagram",
    "classDiagram",
)


def validate_mermaid(dsl: str) -> tuple[bool, str | None]:
    """Check that the DSL starts with a known Mermaid diagram keyword."""
    head = dsl.strip().split("\n", 1)[0].strip()
    if any(head.startswith(k) for k in _MERMAID_KEYWORDS):
        return True, None
    return False, f"Mermaid DSL does not start with a known diagram keyword: {head!r}"


def validate_plantuml(dsl: str) -> tuple[bool, str | None]:
    """PlantUML DSL must be wrapped in `@startuml ... @enduml`."""
    text = dsl.strip()
    if text.startswith("@startuml") and text.endswith("@enduml"):
        return True, None
    return False, "PlantUML DSL must be wrapped in @startuml ... @enduml"
