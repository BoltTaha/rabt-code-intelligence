"""
Shared utilities. Imported by others.
"""

def normalize_id(raw: str) -> str:
    """Normalize string id."""
    return raw.strip().lower()
