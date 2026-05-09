"""
Authentication and Authorization Module.

Exports:
    - CurrentUser: User context dataclass
    - get_current_user: Main authentication dependency
    - get_current_active_user: Verify active user
    - get_current_salesman: Salesman-only access
    - get_current_admin: Admin-only access
    - get_current_salesman_or_admin: Shared access
    - require_order_ownership: Order access verification
    - require_roles: Role factory decorator

Usage:
    from app.auth import get_current_user, CurrentUser

    @router.get("/me")
    async def get_me(user: CurrentUser = Depends(get_current_user)):
        return user.to_dict()
"""

from .dependencies import (
    # Main classes
    CurrentUser,

    # Core dependencies
    get_current_user,
    get_current_active_user,

    # Role-specific dependencies
    get_current_salesman,
    get_current_admin,
    get_current_salesman_or_admin,

    # Utility functions
    require_order_ownership,
    require_roles,
)

from .utils import (
    # Password utilities
    hash_password,
    verify_password,

    # Token utilities
    generate_simulated_token,
    generate_test_bearer_token,
    parse_simulated_token,
    create_auth_headers,

    # Role utilities
    has_permission,

    # Constants
    ROLE_ADMIN,
    ROLE_SALESMAN,
    ALL_ROLES,
    ROLE_PERMISSIONS,
    ADMIN_PERMISSIONS,
    SALESMAN_PERMISSIONS,
)

__all__ = [
    # Classes
    "CurrentUser",

    # Dependencies
    "get_current_user",
    "get_current_active_user",
    "get_current_salesman",
    "get_current_admin",
    "get_current_salesman_or_admin",

    # Utilities
    "require_order_ownership",
    "require_roles",

    # Password
    "hash_password",
    "verify_password",

    # Tokens
    "generate_simulated_token",
    "generate_test_bearer_token",
    "parse_simulated_token",
    "create_auth_headers",

    # Roles
    "has_permission",
    "ROLE_ADMIN",
    "ROLE_SALESMAN",
    "ALL_ROLES",
    "ROLE_PERMISSIONS",
    "ADMIN_PERMISSIONS",
    "SALESMAN_PERMISSIONS",
]
