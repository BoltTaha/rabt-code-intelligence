"""
Runtime instrumentation: decorators and event logging.
Phase 2: read .runtime_events.jsonl and convert to RuntimeEvent list for the graph.
"""

import json
from pathlib import Path
from typing import List

from core.types import RuntimeEvent

LOG_FILE = Path(".runtime_events.jsonl")


def _node_id(module: str, kind: str, name: str) -> str:
    """Match parser's node id format: module::kind::name."""
    return f"{module}::{kind}::{name}"


def _resolve_module(repo_path: str, module: str, main_module: str) -> str:
    """Resolve short module names (e.g. user_service) to full path (e.g. examples.sample_repo.user_service)."""
    if module == "__main__":
        return main_module
    if not module or "." in module:
        return module  # empty or already fully qualified
    prefix = repo_path.replace("/", ".").rstrip(".")
    if not prefix:
        return module
    return f"{prefix}.{module}"


def collect_runtime_events(repo_path: str, config: dict) -> List[RuntimeEvent]:
    """
    Read .runtime_events.jsonl and convert to RuntimeEvent objects.
    Builds source_id and target_id as module::function::name so they match graph nodes.
    """
    events: List[RuntimeEvent] = []
    if not LOG_FILE.exists():
        return events

    runtime_config = config.get("runtime") or {}
    main_module = runtime_config.get("main_module", "__main__")

    try:
        lines = LOG_FILE.read_text(encoding="utf-8").strip().splitlines()
        for line in lines:
            if not line.strip():
                continue
            data = json.loads(line)

            if data.get("event_type") == "call":
                source_module = _resolve_module(
                    repo_path, data.get("source_module", "runtime_driver"), main_module
                )
                source_name = data.get("source_name", "unknown")
                target_module = _resolve_module(
                    repo_path, data.get("target_module", ""), main_module
                )
                target_name = data.get("target_name", "")
                source_id = _node_id(source_module, "function", source_name)
                target_id = _node_id(target_module, "function", target_name)
                events.append(
                    RuntimeEvent(
                        event_type="call",
                        source_id=source_id,
                        target_id=target_id,
                        count=1,
                    )
                )
            elif data.get("event_type") == "mutation":
                source_module = _resolve_module(
                    repo_path, data.get("source_module", "unknown"), main_module
                )
                source_name = data.get("source_name", "unknown")
                variable_name = data.get("variable", "")
                if not variable_name:
                    continue
                source_id = _node_id(source_module, "function", source_name)
                variable_id = _node_id(source_module, "variable", variable_name)
                events.append(
                    RuntimeEvent(
                        event_type="mutation",
                        source_id=source_id,
                        variable_id=variable_id,
                        count=1,
                    )
                )
    except (OSError, json.JSONDecodeError):
        pass

    return events


__all__ = ["collect_runtime_events", "RuntimeEvent"]
