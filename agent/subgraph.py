"""
Format minimal subgraph as text for LLM consumption.
"""

import networkx as nx


def subgraph_to_text(G: nx.DiGraph) -> str:
    """
    Convert subgraph to a readable text representation.
    One line per edge: "source_name edge_type target_name" with optional impact (weight).
    When weight > 1, shows execution count so the LLM sees importance of the path.
    """
    if G is None or G.number_of_nodes() == 0:
        return "(empty subgraph)"

    lines: list[str] = []
    for u, v, attrs in G.edges(data=True):
        u_name = G.nodes[u].get("name", u)
        v_name = G.nodes[v].get("name", v)
        edge_type = attrs.get("edge_type", "CALLS")
        weight = attrs.get("weight", 1)
        try:
            w = float(weight)
        except (TypeError, ValueError):
            w = 1
        if w > 1:
            lines.append(f"{u_name} {edge_type} {v_name} (executed {int(w)} times)")
        else:
            lines.append(f"{u_name} {edge_type} {v_name}")

    if not lines:
        # Only isolated nodes (include module so same name in different modules stay distinct)
        for nid in G.nodes():
            name = G.nodes[nid].get("name", nid)
            kind = G.nodes[nid].get("kind", "node")
            mod = G.nodes[nid].get("module", "")
            lines.append(f"{kind} {name} ({mod})" if mod else f"{kind} {name}")

    return "\n".join(sorted(set(lines)))
