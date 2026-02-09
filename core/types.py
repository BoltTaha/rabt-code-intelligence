"""
Shared data contracts for the pipeline.
Used by parser, graph, runtime, and agent layers.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class EdgeType(str, Enum):
    """Static and dynamic edge types in the dependency graph."""

    # Static (from AST)
    CALLS = "CALLS"
    IMPORTS = "IMPORTS"
    INHERITS = "INHERITS"
    REFERENCES = "REFERENCES"

    # Dynamic (from runtime instrumentation)
    RUNTIME_CALL = "RuntimeCall"
    MODIFIED_BY = "MODIFIED_BY"


class NodeKind(str, Enum):
    """Kind of node in the graph."""

    FUNCTION = "function"
    CLASS = "class"
    VARIABLE = "variable"
    MODULE = "module"


@dataclass(frozen=True)
class Node:
    """A single node in the dependency graph."""

    id: str  # unique identifier, e.g. "module::function_name"
    kind: NodeKind
    name: str
    module: str  # source module/path
    line: Optional[int] = None
    metadata: dict = field(default_factory=dict)

    def __hash__(self) -> int:
        return hash(self.id)


@dataclass
class Edge:
    """A directed edge between two nodes."""

    source_id: str
    target_id: str
    edge_type: EdgeType
    weight: float = 1.0
    metadata: dict = field(default_factory=dict)


@dataclass
class ParserOutput:
    """Output of the static parser. Contract for parser layer."""

    nodes: List[Node]
    edges: List[Edge]

    def __post_init__(self) -> None:
        self.nodes = list(self.nodes)
        self.edges = list(self.edges)


@dataclass
class RuntimeEvent:
    """A single runtime event (call or mutation). Contract for runtime layer."""

    event_type: str  # "call" | "mutation"
    source_id: Optional[str] = None
    target_id: Optional[str] = None
    variable_id: Optional[str] = None
    count: int = 1
    metadata: dict = field(default_factory=dict)
