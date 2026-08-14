from fastapi import APIRouter

from app.api import applications, assistant, browser_bridge, browser_session, dashboard, jobs, profiles, settings

api_router = APIRouter(prefix="/api")
api_router.include_router(settings.router, tags=["settings"])
api_router.include_router(profiles.router, tags=["profile"])
api_router.include_router(jobs.router, tags=["jobs"])
api_router.include_router(applications.router, tags=["applications"])
api_router.include_router(dashboard.router, tags=["dashboard"])
api_router.include_router(assistant.router, tags=["assistant"])
api_router.include_router(browser_bridge.router, tags=["browser bridge"])
api_router.include_router(browser_session.router, tags=["browser session"])
