from fastapi import APIRouter

from app.api import applications, dashboard, jobs, profiles, settings

api_router = APIRouter(prefix="/api")
api_router.include_router(settings.router, tags=["settings"])
api_router.include_router(profiles.router, tags=["profile"])
api_router.include_router(jobs.router, tags=["jobs"])
api_router.include_router(applications.router, tags=["applications"])
api_router.include_router(dashboard.router, tags=["dashboard"])
