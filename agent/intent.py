"""
Map natural-language query to intent (relationship type + target).
Keeps supported queries explicit and testable.
"""

import re
from dataclasses import dataclass
from typing import List, Optional

from core.types import EdgeType


@dataclass
class QueryIntent:
    """Resolved intent from a user query."""

    intent_type: str  # "modification" | "who_calls" | "forward_impact" | "imports"
    target_name: str  # e.g. "userData", "save_user"
    edge_types: List[EdgeType]
    reverse: bool = False  # True = predecessors, False = successors


# Query pattern → (intent_type, edge_types, reverse)
PATTERNS = [
    (
        r"where\s+is\s+(\w+)\s+modified",
        ("modification", [EdgeType.MODIFIED_BY], True),
    ),
    (
        r"who\s+calls\s+(\w+)",
        ("who_calls", [EdgeType.CALLS, EdgeType.RUNTIME_CALL], True),
    ),
    (
        r"what\s+(?:breaks\s+if\s+i\s+change|is\s+impacted\s+by\s+changing)\s+(\w+)",
        ("forward_impact", [EdgeType.CALLS, EdgeType.RUNTIME_CALL], False),
    ),
    (
        r"what\s+does\s+(\w+)\s+import",
        ("imports", [EdgeType.IMPORTS], False),
    ),
    (
        r"which\s+functions?\s+call\s+(\w+)",
        ("who_calls", [EdgeType.CALLS, EdgeType.RUNTIME_CALL], True),
    ),
    (
        r"what\s+does\s+(\w+)\s+(?:depend\s+on|call)\b",
        ("forward_impact", [EdgeType.CALLS, EdgeType.RUNTIME_CALL], False),
    ),
]


def parse_intent(query: str | None) -> Optional[QueryIntent]:
    """
    Parse user query into QueryIntent.
    Returns None if no pattern matches or query is None/empty (unsupported query).
    """
    if not query or not isinstance(query, str):
        return None
    q = query.strip().lower()
    for pattern, (intent_type, edge_types, reverse) in PATTERNS:
        m = re.search(pattern, q, re.IGNORECASE)
        if m:
            target = m.group(1)
            return QueryIntent(
                intent_type=intent_type,
                target_name=target,
                edge_types=edge_types,
                reverse=reverse,
            )
    return None
