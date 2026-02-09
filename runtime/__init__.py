"""
Runtime instrumentation: decorators and event logging.
Phase 2 of the plan; stub for MVP — no runtime edges until Week 3–4.
"""

from core.types import RuntimeEvent

# Placeholder: collect_runtime_events(repo_path, config) -> List[RuntimeEvent]
def collect_runtime_events(_repo_path: str, _config: dict) -> list:
    """Return empty list until runtime instrumentation is implemented."""
    return []

__all__ = ["collect_runtime_events", "RuntimeEvent"]
