"""
Map natural-language query to intent (relationship type + target).
Keeps supported queries explicit and testable, with optional LLM routing.
"""

import json
import os
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
# Patterns now capture qualified names (e.g., "Session.cookies", "Response.status_code")
PATTERNS = [
    (
        r"where\s+is\s+([\w.]+)\s+modified",
        ("modification", [EdgeType.MODIFIED_BY], True),
    ),
    (
        r"who\s+calls\s+([\w.]+)",
        ("who_calls", [EdgeType.CALLS, EdgeType.RUNTIME_CALL], True),
    ),
    (
        r"what\s+(?:breaks\s+if\s+i\s+change|is\s+impacted\s+by\s+changing)\s+([\w.]+)",
        ("forward_impact", [EdgeType.CALLS, EdgeType.RUNTIME_CALL], False),
    ),
    (
        r"what\s+does\s+([\w.]+)\s+import",
        ("imports", [EdgeType.IMPORTS], False),
    ),
    (
        r"which\s+functions?\s+call\s+([\w.]+)",
        ("who_calls", [EdgeType.CALLS, EdgeType.RUNTIME_CALL], True),
    ),
    (
        r"what\s+does\s+([\w.]+)\s+(?:depend\s+on|call)\b",
        ("forward_impact", [EdgeType.CALLS, EdgeType.RUNTIME_CALL], False),
    ),
    (
        r"which\s+functions?\s+does\s+([\w.]+)\s+call",
        ("forward_impact", [EdgeType.CALLS, EdgeType.RUNTIME_CALL], False),
    ),
]


_INTENT_MAP = {
    "modification": ([EdgeType.MODIFIED_BY], True),
    "who_calls": ([EdgeType.CALLS, EdgeType.RUNTIME_CALL], True),
    "forward_impact": ([EdgeType.CALLS, EdgeType.RUNTIME_CALL], False),
    "imports": ([EdgeType.IMPORTS], False),
}


def parse_intent(query: str | None, config: dict | None = None) -> Optional[QueryIntent]:
    """
    Parse user query into QueryIntent.
    Returns None if no pattern matches or query is None/empty (unsupported query).

    Routing modes (config.intent.router):
    - "regex": deterministic regex only
    - "llm": LLM router, fallback to regex
    - "auto": LLM if available, else regex (default when config provided)
    If config is None, defaults to regex-only for deterministic tests.
    """
    if not query or not isinstance(query, str):
        return None

    if config is None:
        return _parse_intent_regex(query)

    intent_cfg = config.get("intent") or {}
    router = (intent_cfg.get("router") or "auto").lower()

    if router == "regex":
        return _parse_intent_regex(query)

    if router in ("llm", "auto"):
        intent = _parse_intent_llm(query, config)
        if intent:
            return intent
        return _parse_intent_regex(query)

    # Unknown router setting -> safe fallback
    return _parse_intent_regex(query)


def _parse_intent_regex(query: str) -> Optional[QueryIntent]:
    """Regex-only routing for deterministic intent parsing."""
    q = query.strip().lower()
    query_orig = query.strip()
    for pattern, (intent_type, edge_types, reverse) in PATTERNS:
        m = re.search(pattern, q, re.IGNORECASE)
        if m:
            # Preserve original case of target (e.g. "userData" not "userdata")
            target = query_orig[m.start(1) : m.end(1)]
            return QueryIntent(
                intent_type=intent_type,
                target_name=target,
                edge_types=edge_types,
                reverse=reverse,
            )
    return None


def _parse_intent_llm(query: str, config: dict) -> Optional[QueryIntent]:
    """LLM-based intent routing (JSON output), with strict validation."""
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        return None

    try:
        from google import genai
    except ImportError:
        return None

    model_name = (config.get("intent") or {}).get("model") or (config.get("llm") or {}).get("model") or "gemini-2.5-flash"

    prompt = f"""You route developer questions to a graph query intent.

Return ONLY valid JSON with keys: intent, target.
Valid intents: who_calls, modification, forward_impact, imports.
If you cannot determine, return: {{"intent": null, "target": null}}.

Examples:
Q: Who calls save_user?
A: {{"intent": "who_calls", "target": "save_user"}}

Q: Where is userData modified?
A: {{"intent": "modification", "target": "userData"}}

Q: What does main import?
A: {{"intent": "imports", "target": "main"}}

Q: What breaks if I change request?
A: {{"intent": "forward_impact", "target": "request"}}

Question: {query}
"""

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(model=model_name, contents=prompt)
        if hasattr(response, "text") and response.text:
            raw = response.text.strip()
        elif getattr(response, "candidates", None) and len(response.candidates) > 0:
            part = response.candidates[0].content.parts[0]
            raw = (getattr(part, "text", None) or "").strip()
        else:
            return None
    except Exception:
        return None

    # Extract JSON object from model output
    start = raw.find("{")
    end = raw.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    try:
        data = json.loads(raw[start : end + 1])
    except json.JSONDecodeError:
        return None

    intent_type = data.get("intent")
    target = data.get("target")
    if not intent_type or not target:
        return None
    if intent_type not in _INTENT_MAP:
        return None

    edge_types, reverse = _INTENT_MAP[intent_type]
    return QueryIntent(
        intent_type=intent_type,
        target_name=str(target),
        edge_types=edge_types,
        reverse=reverse,
    )
