"""
Graph persistence: load/save graph as JSON.
"""

import json
from pathlib import Path

import networkx as nx


def save_graph(G: nx.DiGraph, path: str | Path) -> None:
    """Write graph to JSON file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "nodes": [
            {"id": nid, **{k: v for k, v in attrs.items() if v is not None}}
            for nid, attrs in G.nodes(data=True)
        ],
        "edges": [
            {
                "source": u,
                "target": v,
                "edge_type": attrs.get("edge_type", "CALLS"),
                "weight": attrs.get("weight", 1.0),
            }
            for u, v, attrs in G.edges(data=True)
        ],
    }
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def load_graph(path: str | Path) -> nx.DiGraph:
    """Load graph from JSON file."""
    path = Path(path)
    if not path.exists():
        return nx.DiGraph()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return nx.DiGraph()
    if not isinstance(data, dict):
        return nx.DiGraph()
    G = nx.DiGraph()
    for n in data.get("nodes", []):
        n = dict(n)  # don't mutate original
        nid = n.pop("id", None)
        if nid is None:
            continue
        G.add_node(nid, **n)
    for e in data.get("edges", []):
        u, v = e.get("source"), e.get("target")
        if u is None or v is None:
            continue
        if G.has_node(u) and G.has_node(v):
            G.add_edge(
                u, v,
                edge_type=e.get("edge_type", "CALLS"),
                weight=e.get("weight", 1.0),
            )
    return G
