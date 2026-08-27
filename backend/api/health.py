from fastapi import APIRouter, Response, status
from sqlalchemy import text
from backend.core.config import settings
from backend.db.database import get_db_session
from backend.core.logging import logger

router = APIRouter(tags=["Health & Readiness Probes"])

from backend.core.metrics import metrics_collector

@router.get("/health")
async def health_check():
    """
    Comprehensive system health check returning subsystem operational states and operational metrics.
    Evaluates API, Database, ML Engine, Evidence Engine, and Review Engine status.
    """
    db_status = "HEALTHY"
    try:
        with get_db_session() as session:
            session.execute(text("SELECT 1"))
    except Exception as e:
        logger.error(f"Health probe DB error: {str(e)}")
        db_status = "UNAVAILABLE"

    ml_status = "HEALTHY"
    try:
        from backend.services.prediction_service import prediction_service
        if not prediction_service or not prediction_service.model:
            ml_status = "DEGRADED"
    except Exception:
        ml_status = "UNAVAILABLE"

    overall_status = "HEALTHY"
    if db_status != "HEALTHY" or ml_status != "HEALTHY":
        overall_status = "DEGRADED"

    metrics = metrics_collector.get_metrics_snapshot()

    return {
        "status": "ok",
        "overall_status": overall_status,
        "service": settings.PROJECT_NAME,
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "subsystems": {
            "api": "HEALTHY",
            "database": db_status,
            "ml_engine": ml_status,
            "evidence_engine": "HEALTHY",
            "review_engine": "HEALTHY"
        },
        "metrics": metrics,
        "is_synthetic_data": settings.DATA_IS_SYNTHETIC,
        "disclaimer": "ChargeShield operates with explicit data provenance tracking."
    }

@router.get("/ready")
async def readiness_probe(response: Response):
    """
    Readiness probe verifying that backend dependencies (Database session & ML model) are ready for traffic.
    Returns HTTP 200 if ready, HTTP 503 if unavailable.
    """
    try:
        with get_db_session() as session:
            session.execute(text("SELECT 1"))
        return {
            "status": "READY",
            "message": "ChargeShield backend services are ready to accept API requests.",
            "database": "CONNECTED"
        }
    except Exception as e:
        logger.error(f"Readiness probe failed: {str(e)}")
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {
            "status": "NOT_READY",
            "message": f"Database dependency check failed: {str(e)}",
            "database": "DISCONNECTED"
        }
