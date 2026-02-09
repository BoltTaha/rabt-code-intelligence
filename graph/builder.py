"""
Build a NetworkX DiGraph from parser output (and optional runtime events).
"""

import networkx as nx
from typing import List, Optional

from core.types import EdgeType, ParserOutput, RuntimeEvent


def build_graph(
    parser_output: ParserOutput,
    runtime_events: Optional[List[RuntimeEvent]] = None,
) -> nx.DiGraph:
    """
    Build a directed graph from static parser output and optional runtime events.
    Returns a NetworkX DiGraph with node attributes and edge attributes (type, weight).
    """
    G = nx.DiGraph()

    for node in parser_output.nodes:
        G.add_node(
            node.id,
            kind=node.kind.value,
            name=node.name,
            module=node.module,
            line=node.line,
            **node.metadata,
        )

    def _resolve_target(target_id: str) -> Optional[str]:
        """If target_id is missing, try package re-export: e.g. parser::function::parse_path -> parser.ast_parser::function::parse_path."""
        if G.has_node(target_id):
            return target_id
        # target_id format: "module::kind::name"
        parts = target_id.split("::", 2)
        if len(parts) != 3:
            return None
        mod, kind, name = parts
        for nid in G.nodes():
            if G.nodes[nid].get("name") == name and G.nodes[nid].get("kind") == kind:
                nmod = G.nodes[nid].get("module", "")
                if nmod.startswith(mod + "."):
                    return nid
        return None

    for edge in parser_output.edges:
        target_id = _resolve_target(edge.target_id)
        if G.has_node(edge.source_id) and target_id:
            G.add_edge(
                edge.source_id,
                target_id,
                edge_type=edge.edge_type.value,
                weight=edge.weight,
                **edge.metadata,
            )

    if runtime_events:
        for ev in runtime_events:
            if ev.event_type == "call" and ev.source_id and ev.target_id:
                if G.has_node(ev.source_id) and G.has_node(ev.target_id):
                    if G.has_edge(ev.source_id, ev.target_id):
                        G.edges[ev.source_id, ev.target_id]["weight"] = (
                            G.edges[ev.source_id, ev.target_id].get("weight", 1)
                            + ev.count
                        )
                    else:
                        G.add_edge(
                            ev.source_id,
                            ev.target_id,
                            edge_type=EdgeType.RUNTIME_CALL.value,
                            weight=float(ev.count),
                        )
            elif ev.event_type == "mutation" and ev.source_id and ev.variable_id:
                if G.has_node(ev.source_id) and G.has_node(ev.variable_id):
                    G.add_edge(
                        ev.source_id,
                        ev.variable_id,
                        edge_type=EdgeType.MODIFIED_BY.value,
                        weight=float(ev.count),
                    )

    return G
