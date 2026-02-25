"""
User service: get and save user data.
"""
import sys
from pathlib import Path

# Add project root so we can import runtime when running from sample_repo
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from data_handler import update_user
from runtime.tracer import track_runtime


def get_user(user_id: str) -> dict:
    """Fetch user by id (stub)."""
    return {"id": user_id, "name": "Alice"}


@track_runtime
def save_user(user_data: dict) -> None:
    """Persist user; delegates to update_user."""
    update_user(user_data)


def delete_user(user_id: str) -> bool:
    """Remove user (stub)."""
    return True
