"""
Data handling: validation and update. Modifies userData.
"""

# Global state (tracked variable for "Where is userData modified?")
userData: dict = {}


def validate_input(data: dict) -> bool:
    """Check input shape; may read userData."""
    return isinstance(data, dict) and "id" in data


def update_user(data: dict) -> None:
    """Update global userData (modification)."""
    global userData
    userData = data


def get_user_data() -> dict:
    """Return current userData."""
    return userData
