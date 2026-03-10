"""
app/utils/file_lock.py — Thread-Safe File Access
==================================================
WHY DO WE NEED A FILE LOCK?
- Flask can handle multiple requests at the same time (concurrently).
- If two requests both try to write to pipelines.json simultaneously,
  the file can get corrupted (partial writes, lost data).
- A threading.Lock() ensures only ONE thread can write at a time.

HOW IT WORKS:
- We create one Lock per file.
- Before reading or writing, we "acquire" the lock.
- Other threads must wait until the lock is "released".
- Python's `with lock:` syntax auto-releases even if an error occurs.

EXAMPLE:
    with get_file_lock("pipelines.json"):
        # Only one thread runs this block at a time
        data = read_json("pipelines.json")
        data.append(new_record)
        write_json("pipelines.json", data)

NOTE: This handles thread concurrency (multiple requests in one process).
For multi-process deployment (multiple Gunicorn workers), you'd need
file-level OS locks (fcntl) or a database. For this project, threading
locks are sufficient.
"""

import threading
from typing import Dict

# ----------------------------------------------------------------
# GLOBAL LOCK REGISTRY
# A dictionary mapping filename → Lock object.
# We reuse the same lock for the same file across all calls.
# ----------------------------------------------------------------
_file_locks: Dict[str, threading.Lock] = {}
_registry_lock = threading.Lock()  # Protects the _file_locks dict itself


def get_file_lock(filename: str) -> threading.Lock:
    """
    Get (or create) a threading.Lock for a specific filename.

    Args:
        filename: The name of the file to lock (e.g., "pipelines.json")

    Returns:
        A threading.Lock instance dedicated to that file

    WHY A REGISTRY LOCK?
    - Creating the per-file lock itself needs to be thread-safe.
    - Two threads might simultaneously try to create a lock for the
      same file — we'd end up with two different locks (not safe).
    - _registry_lock ensures only one thread adds to _file_locks at a time.
    """
    with _registry_lock:
        if filename not in _file_locks:
            _file_locks[filename] = threading.Lock()
        return _file_locks[filename]
