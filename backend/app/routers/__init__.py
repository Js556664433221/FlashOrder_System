from .products import router as products_router
from .orders import router as orders_router
from .payments import router as payments_router
from .admin import router as admin_router
from .auth import router as auth_router, get_current_user_from_token
from .activity import router as activity_router
from .promo import router as promo_router
from .promo_validate import router as promo_validate_router
from .users import router as users_router
from .customers import router as customers_router

__all__ = [
    "products_router", "orders_router", "payments_router",
    "admin_router", "auth_router", "activity_router",
    "promo_router", "promo_validate_router", "users_router",
    "customers_router",
    "get_current_user_from_token"
]
