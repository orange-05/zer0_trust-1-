"""
app/repositories/user_repository.py — User Data Access
========================================================
WHY A SPECIFIC REPOSITORY?
- UserRepository inherits all CRUD from JsonRepository.
- It adds user-specific methods like find_by_username.
- This keeps the interface clean — callers don't write filter loops.
"""

import os
from flask import current_app
from app.repositories.json_repository import JsonRepository
from typing import Dict, Optional


class UserRepository(JsonRepository):
    """Manages user records in users.json."""

    def __init__(self):
        # We get the data directory from Flask app config.
        # This allows TestingConfig to point to a different directory.
        data_dir = current_app.config["DATA_DIR"]
        file_path = os.path.join(data_dir, "users.json")
        super().__init__(file_path=file_path, id_prefix="usr")

    def find_by_username(self, username: str) -> Optional[Dict]:
        """
        Find a user by their username (case-sensitive).

        Used during login to look up the user before password verification.

        Returns:
            User record dict, or None if not found
        """
        users = self.get_all()
        for user in users:
            if user.get("username") == username:
                return user
        return None

    def username_exists(self, username: str) -> bool:
        """
        Check if a username is already taken.

        Used during registration to prevent duplicates.
        """
        return self.find_by_username(username) is not None
