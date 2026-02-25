"""
Runtime tracer: decorator to log function calls to .runtime_events.jsonl.
Used by Phase 2 runtime instrumentation so the graph can merge dynamic edges.
"""

import functools
import inspect
import json
import time
from pathlib import Path
from typing import Any, Callable

# Global log file path (project root when run from repo)
LOG_FILE = Path(".runtime_events.jsonl")


def track_runtime(func: Callable) -> Callable:
    """
    Decorator: Log a 'call' event to .runtime_events.jsonl whenever this function runs.
    Logs source (caller) and target (decorated function) module/name so events
    can be mapped to graph node IDs (module::function::name).
    """
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        # Caller from stack (frame that called this wrapper)
        source_module = "__main__"
        source_name = "unknown"
        try:
            # stack[0]=wrapper, stack[1]=caller
            frame = inspect.stack()[1].frame
            source_module = frame.f_globals.get("__name__", "__main__")
            source_name = frame.f_code.co_name
        except (IndexError, AttributeError):
            pass

        event = {
            "event_type": "call",
            "source_module": source_module,
            "source_name": source_name,
            "target_module": func.__module__,
            "target_name": func.__name__,
            "timestamp": time.time(),
        }

        try:
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(event) + "\n")
        except OSError:
            pass  # Don't crash the app if logging fails

        return func(*args, **kwargs)

    return wrapper


def track_mutation(variable_name: str, source: str = "unknown") -> None:
    """
    Log a 'mutation' event to .runtime_events.jsonl.
    Call this when a critical variable is changed so the graph can add MODIFIED_BY edges.
    """
    source_module = "unknown"
    try:
        frame = inspect.stack()[1].frame
        source_module = frame.f_globals.get("__name__", "unknown")
    except (IndexError, AttributeError):
        pass

    event = {
        "event_type": "mutation",
        "source_module": source_module,
        "source_name": source,
        "variable": variable_name,
        "timestamp": time.time(),
    }

    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(event) + "\n")
    except OSError:
        pass


def clear_logs() -> None:
    """Wipe the log file clean before a new run."""
    if LOG_FILE.exists():
        LOG_FILE.unlink()
