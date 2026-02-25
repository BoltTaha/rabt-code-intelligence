"""
Data handling: validation and update. Modifies userData.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from runtime.tracer import track_mutation

# Global state (tracked variable for "Where is userData modified?")
userData: dict = {}


def validate_input(data: dict) -> bool:
    """Check input shape; may read userData."""
    return isinstance(data, dict) and "id" in data


def update_user(data: dict) -> None:
    """Update global userData (modification)."""
    global userData
    userData = data
    track_mutation(variable_name="userData", source="update_user")


def get_user_data() -> dict:
    """Return current userData."""
    return userData
