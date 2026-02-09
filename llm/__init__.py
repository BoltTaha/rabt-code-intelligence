"""
LLM integration: prompt building and API client.
Phase 5 of the plan; stub for MVP — no API calls until Week 8.
"""

def answer_with_llm(subgraph_text: str, query: str, _config: dict) -> tuple[str, str]:
    """
    Placeholder: return (answer, confidence).
    confidence in ("HIGH", "MEDIUM", "LOW").
    """
    return (
        f"(LLM not configured; subgraph had {len(subgraph_text)} chars.)",
        "MEDIUM",
    )

__all__ = ["answer_with_llm"]
