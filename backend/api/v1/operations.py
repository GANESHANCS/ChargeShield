"""
FastAPI Router for Real-Time Fraud Operations & Alerts.
"""

from typing import List
from fastapi import APIRouter, HTTPException, status

from backend.services.operations_monitor import operations_monitor
from backend.services.alert_engine import alert_engine
from backend.analytics.service import analytics_service
from backend.schemas.operations import (
    OperationsOverviewResponse,
    OperationalAlert
)
from backend.analytics.schemas import SubsystemStatus

router = APIRouter(prefix="/api/v1/operations", tags=["Real-Time Operations & Monitoring"])


@router.get("/overview", response_model=OperationsOverviewResponse, summary="Get Live Operations Overview")
async def get_operations_overview():
    """Returns live operational metrics derived strictly from actual database records."""
    try:
        return operations_monitor.get_operations_overview()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve operations overview: {str(e)}"
        )


@router.get("/alerts", response_model=List[OperationalAlert], summary="Get Operational Active Alerts")
async def get_operational_alerts():
    """Returns real rules-based operational alerts evaluated against current system conditions."""
    try:
        return alert_engine.get_active_alerts()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve operational alerts: {str(e)}"
        )


@router.get("/health", response_model=SubsystemStatus, summary="Get Subsystem Operations Health")
async def get_operations_health():
    """Performs live health checks across FastAPI, SQLite DB, ML Engine, and Evidence Verifier."""
    try:
        return analytics_service.check_health()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve subsystem health: {str(e)}"
        )
