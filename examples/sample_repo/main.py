"""
Sample repo: entry point. Calls user_service and data_handler.
"""
import sys
from pathlib import Path

# Add project root so runtime.tracer resolves when running this file directly
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from user_service import get_user, save_user
from data_handler import validate_input


def main() -> None:
    user_data = get_user("alice")
    validate_input(user_data)
    save_user(user_data)


def secret_feature():
    """I am a new feature (living graph test)."""
    print("Shhh")


if __name__ == "__main__":
    main()
