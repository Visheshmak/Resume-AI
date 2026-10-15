from fastapi import APIRouter

from app.api.routes.analysis import router as analysis_router
from app.api.routes.auth import router as auth_router
from app.api.routes.dashboard import router as dashboard_router
from app.api.routes.health import router as health_router
from app.api.routes.jobs import router as jobs_router
from app.api.routes.resumes import router as resumes_router

api_router = APIRouter()
api_router.include_router(health_router, prefix="/health", tags=["system"])
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(resumes_router, prefix="/resumes", tags=["resumes"])
api_router.include_router(jobs_router, prefix="/jobs", tags=["jobs"])
api_router.include_router(analysis_router, prefix="/analysis", tags=["analysis"])
api_router.include_router(dashboard_router, prefix="/dashboard", tags=["dashboard"])
