from app.api.auth import router as auth_router
from app.api.categories import router as categories_router
from app.api.posts import router as posts_router

__all__ = ["auth_router", "categories_router", "posts_router"]
