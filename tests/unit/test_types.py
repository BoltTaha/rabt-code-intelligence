"""Unit tests for core types (no external deps)."""

import pytest
from core.types import Edge, EdgeType, Node, NodeKind, ParserOutput


def test_node_id_unique():
    n = Node(id="m::function::f", kind=NodeKind.FUNCTION, name="f", module="m")
    assert n.id == "m::function::f"
    assert hash(n) == hash("m::function::f")


def test_parser_output():
    out = ParserOutput(nodes=[], edges=[])
    assert out.nodes == []
    out = ParserOutput(
        nodes=[Node("a", NodeKind.MODULE, "a", "a")],
        edges=[Edge("a", "b", EdgeType.CALLS)],
    )
    assert len(out.nodes) == 1 and len(out.edges) == 1
