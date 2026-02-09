"""Unit tests for parser (uses only stdlib + core)."""

import tempfile
from pathlib import Path

import pytest
from core.types import EdgeType, NodeKind, ParserOutput
from parser import parse_path


def test_parse_empty_dir(tmp_path):
    out = parse_path(str(tmp_path))
    assert isinstance(out, ParserOutput)
    assert out.nodes == [] and out.edges == []


def test_parse_single_file():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("def foo(): pass\n")
        path = f.name
    try:
        out = parse_path(path)
        assert len(out.nodes) >= 1
        func_nodes = [n for n in out.nodes if n.kind == NodeKind.FUNCTION]
        assert any(n.name == "foo" for n in func_nodes)
    finally:
        Path(path).unlink(missing_ok=True)


def test_parse_sample_repo():
    # Run from repo root; sample_repo is examples/sample_repo
    base = Path(__file__).resolve().parent.parent.parent
    repo = base / "examples" / "sample_repo"
    if not repo.exists():
        pytest.skip("examples/sample_repo not found")
    out = parse_path(str(repo))
    assert len(out.nodes) > 0 and len(out.edges) > 0
    assert any(n.kind == NodeKind.FUNCTION for n in out.nodes)
    assert any(e.edge_type == EdgeType.CALLS for e in out.edges)
