"""
User service: get and save user data.
"""

from data_handler import update_user


def get_user(user_id: str) -> dict:
    """Fetch user by id (stub)."""
    return {"id": user_id, "name": "Alice"}


def save_user(user_data: dict) -> None:
    """Persist user; delegates to update_user."""
    update_user(user_data)


def delete_user(user_id: str) -> bool:
    """Remove user (stub)."""
    return True
