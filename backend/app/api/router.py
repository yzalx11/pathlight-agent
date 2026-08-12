from fastapi import APIRouter

from app.api import applications, dashboard, profiles, settings

api_router = APIRouter(prefix="/api")
api_router.include_router(settings.router, tags=["settings"])
api_router.include_router(profiles.router, tags=["profile"])
api_router.include_router(applications.router, tags=["applications"])
api_router.include_router(dashboard.router, tags=["dashboard"])
