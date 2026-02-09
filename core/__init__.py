"""
Shared types and contracts for the Semantic Graph Memory pipeline.
All layers depend on these; no layer-specific types here.
"""

from core.types import (
    Node,
    Edge,
    EdgeType,
    NodeKind,
    ParserOutput,
    RuntimeEvent,
)

__all__ = [
    "Node",
    "Edge",
    "EdgeType",
    "NodeKind",
    "ParserOutput",
    "RuntimeEvent",
]
