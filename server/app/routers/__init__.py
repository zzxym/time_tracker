from app.routers.auth import router as auth_router
from app.routers.activities import router as activities_router
from app.routers.tags import router as tags_router
from app.routers.stats import router as stats_router
from app.routers.admin import router as admin_router
from app.routers.teams import router as teams_router

__all__ = ["auth_router", "activities_router", "tags_router", "stats_router", "admin_router", "teams_router"]
