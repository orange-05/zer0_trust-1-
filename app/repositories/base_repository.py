"""
app/repositories/base_repository.py — Abstract Base Repository
================================================================
WHY A BASE REPOSITORY?
- All repositories (pipelines, scans, deployments) share the same
  CRUD operations: get_all, get_by_id, save, delete.
- Instead of writing the same code 4 times, we define it once here.
- Specific repositories inherit from BaseRepository and get all
  these methods for free.

DESIGN PATTERN: Repository Pattern
- The Repository Pattern separates data access logic from business logic.
- Service layer asks: "give me pipeline pl-001"
- Repository handles: "open pipelines.json, find id pl-001, return it"
- Service doesn't know HOW data is stored — it just asks the repository.
- This means you could swap JSON files for a real database later
  without changing any service code.

ABSTRACT CLASS:
- We use ABC (Abstract Base Class) to define an interface.
- Any class inheriting BaseRepository MUST implement the abstract methods.
- This enforces consistent behavior across all repositories.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class BaseRepository(ABC):
    """
    Abstract base class defining the interface all repositories must follow.

    Abstract methods must be implemented by child classes.
    Concrete methods (like find_by_field) are shared by all children.
    """

    @abstractmethod
    def get_all(self) -> List[Dict]:
        """
        Retrieve all records from the data store.

        Returns:
            List of all records as dictionaries
        """
        pass

    @abstractmethod
    def get_by_id(self, record_id: str) -> Optional[Dict]:
        """
        Retrieve a single record by its ID.

        Args:
            record_id: The unique identifier (e.g., "pl-001")

        Returns:
            The record as a dict, or None if not found
        """
        pass

    @abstractmethod
    def save(self, record: Dict) -> Dict:
        """
        Save a new record to the data store.

        Args:
            record: The record dict to save

        Returns:
            The saved record (may include generated fields like id, created_at)
        """
        pass

    @abstractmethod
    def update(self, record_id: str, updates: Dict) -> Optional[Dict]:
        """
        Update an existing record.

        Args:
            record_id: ID of the record to update
            updates: Dict of fields to update

        Returns:
            Updated record, or None if not found
        """
        pass

    @abstractmethod
    def delete(self, record_id: str) -> bool:
        """
        Delete a record by ID.

        Args:
            record_id: ID of the record to delete

        Returns:
            True if deleted, False if not found
        """
        pass

    def find_by_field(self, field: str, value: Any) -> List[Dict]:
        """
        Find all records where a field matches a value.
        This is a CONCRETE method — all child classes inherit it.

        Args:
            field: Field name to search on (e.g., "status")
            value: Value to match (e.g., "failed")

        Returns:
            List of matching records

        Example:
            pipeline_repo.find_by_field("status", "failed")
            → Returns all pipelines with status == "failed"
        """
        return [
            record for record in self.get_all()
            if record.get(field) == value
        ]

    def count(self) -> int:
        """Return the total number of records."""
        return len(self.get_all())
