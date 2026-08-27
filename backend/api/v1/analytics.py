from fastapi import APIRouter, HTTPException, status
from backend.analytics.service import analytics_service
from backend.analytics.schemas import (
    AnalyticsOverviewResponse,
    DecisionAnalytics,
    RiskAnalytics,
    FinancialAnalytics,
    EvidenceAnalytics,
    SubsystemStatus,
    OperationalReportResponse
)

router = APIRouter(prefix="/api/v1/analytics", tags=["Analytics & Operational Intelligence"])

@router.get("/overview", response_model=AnalyticsOverviewResponse, summary="Get Complete Analytics Overview")
async def get_analytics_overview():
    """Returns aggregated operational, financial, decision, risk, evidence, and subsystem health metrics."""
    try:
        return analytics_service.get_overview()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate analytics overview: {str(e)}"
        )

@router.get("/decisions", response_model=DecisionAnalytics, summary="Get Decision Analytics")
async def get_decision_analytics():
    """Returns AI recommendations vs human decision distribution and agreement/disagreement rates."""
    try:
        return analytics_service.get_decision_analytics()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate decision analytics: {str(e)}"
        )

@router.get("/risk-distribution", response_model=RiskAnalytics, summary="Get Risk Analytics & Distributions")
async def get_risk_distribution():
    """Returns win probability buckets, dispute reason distributions, and amount brackets."""
    try:
        return analytics_service.get_risk_analytics()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate risk analytics: {str(e)}"
        )

@router.get("/financial", response_model=FinancialAnalytics, summary="Get Financial Analytics")
async def get_financial_analytics():
    """Returns total disputed value, decision breakdown value, and simulated recoverable value."""
    try:
        return analytics_service.get_financial_analytics()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate financial analytics: {str(e)}"
        )

@router.get("/evidence", response_model=EvidenceAnalytics, summary="Get Evidence Verification Analytics")
async def get_evidence_analytics():
    """Returns evidence claim verification counts, mismatches, and overall verification rate."""
    try:
        return analytics_service.get_evidence_analytics()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate evidence analytics: {str(e)}"
        )

@router.get("/health", response_model=SubsystemStatus, summary="Get Subsystem Status & Live Health Checks")
async def get_subsystem_health():
    """Performs real status checks across API, database, ML engine, evidence engine, review engine, and dataset."""
    try:
        return analytics_service.check_health()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check subsystem health: {str(e)}"
        )

@router.get("/report", response_model=OperationalReportResponse, summary="Export Operational Report")
async def get_operational_report():
    """Returns structured JSON operational report suitable for export/audit."""
    try:
        return analytics_service.get_report()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate operational report: {str(e)}"
        )

@router.get("/quality", summary="Get Programmatic Data Quality Metrics")
async def get_data_quality_metrics():
    """Returns composite Data Quality Score and itemized validation issues."""
    try:
        return analytics_service.get_data_quality()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve data quality metrics: {str(e)}"
        )

@router.get("/alerts", summary="Get Operational Attention & System Alerts")
async def get_system_alerts():
    """Returns active system & operational alerts evaluated against real live backend conditions."""
    try:
        return analytics_service.get_alerts()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve system alerts: {str(e)}"
        )

