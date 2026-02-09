"""
Sample repo: entry point. Calls user_service and data_handler.
"""

from user_service import get_user, save_user
from data_handler import validate_input


def main() -> None:
    user_data = get_user("alice")
    validate_input(user_data)
    save_user(user_data)


if __name__ == "__main__":
    main()
