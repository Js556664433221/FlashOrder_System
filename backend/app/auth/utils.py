"""
Authentication Utilities.

Helper functions for:
- Password hashing and verification
- JWT token generation (for testing)
- Simulated token generation
- User lookup utilities
"""

import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Tuple


def hash_password(password: str) -> str:
    """
    Hash a password using SHA-256.

    Note: In production, use bcrypt or argon2 for secure hashing.

    Args:
        password: Plain text password

    Returns:
        Hexadecimal hash string
    """
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a hash.

    Args:
        plain_password: Plain text password to verify
        hashed_password: Stored hash to compare against

    Returns:
        True if password matches, False otherwise
    """
    return hash_password(plain_password) == hashed_password


def generate_simulated_token(user_id: int, role: str) -> str:
    """
    Generate a simulated authentication token for testing.

    Format: user_{id}_{role}_{random_hex}

    Args:
        user_id: User's database ID
        role: User's role (admin/salesman)

    Returns:
        Simulated token string

    Example:
        token = generate_simulated_token(1, "admin")
        # Returns: "user_1_admin_a1b2c3d4"
    """
    random_hex = secrets.token_hex(4)
    return f"user_{user_id}_{role}_{random_hex}"


def generate_test_bearer_token(user_id: int, role: str) -> str:
    """
    Generate a test bearer token.

    In production, use proper JWT with:
    - RS256 or HS256 algorithm
    - Appropriate expiration
    - Signed with secure secret key

    Args:
        user_id: User's database ID
        role: User's role

    Returns:
        Bearer token string
    """
    # This is a placeholder - in production, use PyJWT:
    # token = jwt.encode({
    #     "sub": user_id,
    #     "role": role,
    #     "exp": datetime.utcnow() + timedelta(hours=24)
    # }, SECRET_KEY, algorithm="HS256")
    return f"Bearer {generate_simulated_token(user_id, role)}"


def parse_simulated_token(token: str) -> Optional[Tuple[int, str]]:
    """
    Parse a simulated token to extract user_id and role.

    Args:
        token: Token string from generate_simulated_token

    Returns:
        Tuple of (user_id, role) or None if invalid

    Example:
        result = parse_simulated_token("user_1_admin_a1b2c3d4")
        if result:
            user_id, role = result
    """
    try:
        if token.startswith("user_"):
            # Remove any Bearer prefix
            token = token.replace("Bearer ", "")
            parts = token.split("_")

            if len(parts) >= 3:
                user_id = int(parts[1])
                role = parts[2]
                return (user_id, role)
    except (ValueError, IndexError):
        pass
    return None


def create_auth_headers(user_id: int, role: str, username: Optional[str] = None) -> dict:
    """
    Create simulated auth headers for API testing.

    Args:
        user_id: User's database ID
        role: User's role (admin/salesman)
        username: Optional username

    Returns:
        Dictionary of headers to include in requests

    Example:
        headers = create_auth_headers(1, "admin", "test_admin")
        response = client.get("/admin/users", headers=headers)
    """
    headers = {
        "X-Simulated-Role": role,
        "X-Simulated-User-Id": str(user_id),
    }
    if username:
        headers["X-Simulated-Username"] = username
    return headers


# Role constants for consistent usage
ROLE_ADMIN = "admin"
ROLE_SALESMAN = "salesman"

ALL_ROLES = [ROLE_ADMIN, ROLE_SALESMAN]

# Permission sets
ADMIN_PERMISSIONS = ["read", "write", "delete", "admin"]
SALESMAN_PERMISSIONS = ["read", "write"]

ROLE_PERMISSIONS = {
    ROLE_ADMIN: ADMIN_PERMISSIONS,
    ROLE_SALESMAN: SALESMAN_PERMISSIONS,
}


def has_permission(role: str, permission: str) -> bool:
    """
    Check if a role has a specific permission.

    Args:
        role: User's role
        permission: Permission to check

    Returns:
        True if role has permission
    """
    permissions = ROLE_PERMISSIONS.get(role, [])
    return permission in permissions or "admin" in permissions
