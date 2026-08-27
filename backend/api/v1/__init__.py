"""
API v1 Package Init for ChargeShield Backend.
"""

from fastapi import APIRouter
from backend.api.v1.cases import router as cases_router
from backend.api.v1.review import router as review_router
from backend.api.v1.model import router as model_router
from backend.api.v1.analytics import router as analytics_router
from backend.api.v1.operations import router as operations_router
from backend.api.v1.simulation import router as simulation_router
from backend.api.v1.case_workflow import router as case_workflow_router
from backend.api.v1.auth import router as auth_router, users_router
from backend.api.v1.export import router as export_router
from backend.api.v1.jobs import router as jobs_router

api_v1_router = APIRouter()
api_v1_router.include_router(auth_router)
api_v1_router.include_router(users_router)
api_v1_router.include_router(export_router)
api_v1_router.include_router(jobs_router)
api_v1_router.include_router(cases_router)
api_v1_router.include_router(review_router)
api_v1_router.include_router(model_router)
api_v1_router.include_router(analytics_router)
api_v1_router.include_router(operations_router)
api_v1_router.include_router(simulation_router)
api_v1_router.include_router(case_workflow_router)
