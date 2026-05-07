from .products import router as products_router
from .orders import router as orders_router
from .payments import router as payments_router
from .admin import router as admin_router
from .auth import router as auth_router, get_current_user_from_token

__all__ = ["products_router", "orders_router", "payments_router", "admin_router", "auth_router", "get_current_user_from_token"]
