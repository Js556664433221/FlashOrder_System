from fastapi import Depends, HTTPException, Header
from typing import Optional

# Mock user class for simulated authentication
class MockUser:
    def __init__(self, id: int, username: str, role: str, is_active: bool = True):
        self.id = id
        self.username = username
        self.role = role
        self.is_active = is_active


async def get_current_user(
    x_simulated_role: Optional[str] = Header(None, alias="X-Simulated-Role")
) -> MockUser:
    """Mock authentication using X-Simulated-Role header.

    - Set header to 'admin' for admin privileges
    - Set header to 'staff' or omit for staff privileges
    - No header returns 401
    """
    if x_simulated_role is None:
        raise HTTPException(status_code=401, detail="Not authenticated. Set X-Simulated-Role header.")

    if x_simulated_role == "admin":
        return MockUser(id=1, username="mock_admin", role="admin", is_active=True)
    elif x_simulated_role == "staff":
        return MockUser(id=2, username="mock_staff", role="staff", is_active=True)
    else:
        raise HTTPException(status_code=401, detail="Invalid X-Simulated-Role. Use 'admin' or 'staff'.")


async def get_current_active_user(
    current_user: MockUser = Depends(get_current_user)
) -> MockUser:
    """Verify that the current user is active."""
    if not current_user.is_active:
        raise HTTPException(status_code=403, detail="Inactive user")
    return current_user


async def get_current_active_staff(
    current_user: MockUser = Depends(get_current_user)
) -> MockUser:
    """Verify that the current user is an active staff or admin."""
    if not current_user.is_active:
        raise HTTPException(status_code=403, detail="Inactive user")
    if current_user.role not in ["staff", "admin"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions. Staff or admin role required.")
    return current_user


async def get_current_active_admin(
    current_user: MockUser = Depends(get_current_user)
) -> MockUser:
    """Verify that the current user has the admin role."""
    if not current_user.is_active:
        raise HTTPException(status_code=403, detail="Inactive user")
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return current_user
