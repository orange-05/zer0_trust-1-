"""
app/utils/security.py — Password Hashing & Security Utilities
===============================================================
WHY HASH PASSWORDS?
- NEVER store plain-text passwords. If your database is breached,
  plain passwords expose all users immediately.
- A hash is a one-way transformation: "password123" → "$2b$12$..."
- To verify login: hash the input and compare to the stored hash.
- We use bcrypt via Werkzeug — it's slow by design (resists brute force).

WHY NOT MD5 OR SHA256?
- MD5/SHA256 are fast — attackers can try billions per second.
- bcrypt is intentionally slow (configurable "work factor").
- This makes brute force attacks impractical.

HOW JWT WORKS IN THIS PROJECT:
- User logs in → server creates a signed token containing user ID.
- Token is returned to client.
- Client sends token in Authorization header for protected routes.
- Server verifies signature — if valid, grants access.
- No session state is stored server-side (stateless auth).
"""

from werkzeug.security import generate_password_hash, check_password_hash


def hash_password(plain_password: str) -> str:
    """
    Hash a plain-text password using bcrypt (via Werkzeug).

    Args:
        plain_password: The raw password from registration form

    Returns:
        A bcrypt hash string safe to store in the database

    Example:
        hash_password("MyPass123!") → "$pbkdf2-sha256$260000$..."
    """
    return generate_password_hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain-text password against a stored hash.

    Args:
        plain_password: Password entered during login
        hashed_password: Hash retrieved from the database

    Returns:
        True if password matches, False otherwise

    WHY NOT == comparison?
    - Hashes include random salt, so the same password produces
      different hashes each time. Direct comparison would fail.
    - check_password_hash extracts the salt and rehashes correctly.
    """
    return check_password_hash(hashed_password, plain_password)
