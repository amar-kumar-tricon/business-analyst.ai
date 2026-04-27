from __future__ import annotations


class GraphPlaceholder:
    """Temporary graph placeholder until Stage 1/2 graph is implemented."""

    def __init__(self) -> None:
        self.nodes = {"bootstrap_node": object()}


def get_graph() -> GraphPlaceholder:
    return GraphPlaceholder()
