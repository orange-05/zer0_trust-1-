"""
app/repositories/json_repository.py — JSON File Storage Implementation
=========================================================================
WHY JSON FILES?
- Simple to understand, inspect, and debug.
- No database setup required — great for learning and portfolios.
- Files persist between server restarts.
- Can be swapped for SQLite/PostgreSQL later without changing service layer.

HOW THIS WORKS:
- Each entity (pipelines, scans, deployments) has its own .json file.
- The file contains a JSON array of records: [{...}, {...}, ...]
- On every read: open file → parse JSON → return list.
- On every write: read existing list → modify → write entire list back.

THREAD SAFETY:
- We use our file_lock utility to ensure only one thread reads/writes
  at a time. Without this, concurrent requests could corrupt the file.

FILE INITIALIZATION:
- If the JSON file doesn't exist yet, we create it with an empty list [].
- This means the app works on first run without manual setup.
"""

import json
import os
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional

from app.repositories.base_repository import BaseRepository
from app.utils.file_lock import get_file_lock


class JsonRepository(BaseRepository):
    """
    A concrete repository that stores data in a JSON file.

    Each instance manages one JSON file (one entity type).
    """

    def __init__(self, file_path: str, id_prefix: str = "rec"):
        """
        Initialize the repository.

        Args:
            file_path: Absolute path to the JSON file
            id_prefix: Prefix for generated IDs (e.g., "pl" → "pl-abc123")
        """
        self.file_path = file_path
        self.id_prefix = id_prefix
        self._ensure_file_exists()

    def _ensure_file_exists(self) -> None:
        """
        Create the JSON file with an empty list if it doesn't exist.
        Also creates parent directories if needed.
        """
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        if not os.path.exists(self.file_path):
            with open(self.file_path, "w") as f:
                json.dump([], f)

    def _read_file(self) -> List[Dict]:
        """
        Read and parse the JSON file.

        Returns:
            List of records, or empty list if file is empty/corrupt

        WHY TRY/EXCEPT?
        - If the file is accidentally corrupted (empty, partial write),
          we return [] instead of crashing the entire request.
        """
        with open(self.file_path, "r") as f:
            try:
                return json.load(f)
            except (json.JSONDecodeError, ValueError):
                return []

    def _write_file(self, records: List[Dict]) -> None:
        """
        Write the list of records back to the JSON file.

        Args:
            records: Complete list of records to write

        WHY indent=2?
        - Makes the JSON file human-readable for debugging.
        - A one-liner JSON is harder to inspect manually.
        """
        with open(self.file_path, "w") as f:
            json.dump(records, f, indent=2, default=str)

    def _generate_id(self) -> str:
        """
        Generate a unique record ID with the configured prefix.

        Format: {prefix}-{first 8 chars of UUID}
        Example: "pl-a3f2b1c4", "sc-d9e7f8a1"

        WHY UUID?
        - UUIDs are universally unique — no collisions even across servers.
        - We take the first 8 chars to keep IDs short and readable.
        """
        short_id = str(uuid.uuid4()).replace("-", "")[:8]
        return f"{self.id_prefix}-{short_id}"

    def _get_timestamp(self) -> str:
        """
        Get current UTC timestamp in ISO 8601 format.

        WHY UTC?
        - Storing all timestamps in UTC avoids timezone confusion.
        - The API consumers can convert to their local timezone.

        Example: "2026-03-09T10:15:00Z"
        """
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # ----------------------------------------------------------------
    # CRUD OPERATIONS
    # Create, Read, Update, Delete — the four basic data operations
    # ----------------------------------------------------------------

    def get_all(self) -> List[Dict]:
        """Retrieve all records. Thread-safe read."""
        lock = get_file_lock(os.path.basename(self.file_path))
        with lock:
            return self._read_file()

    def get_by_id(self, record_id: str) -> Optional[Dict]:
        """
        Find a record by its ID.

        Returns None (not raises error) if not found — the service
        layer decides whether to return 404 or handle it differently.
        """
        lock = get_file_lock(os.path.basename(self.file_path))
        with lock:
            records = self._read_file()
            for record in records:
                if record.get("id") == record_id:
                    return record
            return None

    def save(self, record: Dict) -> Dict:
        """
        Save a new record to the JSON file.

        Automatically adds:
        - id: generated unique ID
        - created_at: current UTC timestamp

        Args:
            record: The record data (without id/created_at)

        Returns:
            The complete saved record including generated fields
        """
        lock = get_file_lock(os.path.basename(self.file_path))
        with lock:
            records = self._read_file()

            # Add auto-generated fields
            record["id"] = self._generate_id()
            record["created_at"] = self._get_timestamp()

            records.append(record)
            self._write_file(records)
            return record

    def update(self, record_id: str, updates: Dict) -> Optional[Dict]:
        """
        Update fields on an existing record.

        Args:
            record_id: ID of the record to update
            updates: Dict of {field: new_value} pairs

        Returns:
            Updated record, or None if not found
        """
        lock = get_file_lock(os.path.basename(self.file_path))
        with lock:
            records = self._read_file()

            for i, record in enumerate(records):
                if record.get("id") == record_id:
                    records[i].update(updates)
                    records[i]["updated_at"] = self._get_timestamp()
                    self._write_file(records)
                    return records[i]

            return None

    def delete(self, record_id: str) -> bool:
        """
        Delete a record by ID.

        Returns:
            True if deleted, False if not found
        """
        lock = get_file_lock(os.path.basename(self.file_path))
        with lock:
            records = self._read_file()
            original_count = len(records)
            records = [r for r in records if r.get("id") != record_id]

            if len(records) < original_count:
                self._write_file(records)
                return True
            return False
