"""
FastAPI Router for Phase 12 Model Intelligence, Performance, Calibration, Thresholds, and Outcome Ingestion.
Exposes RBAC-protected outcome ingestion and governance endpoints.
"""

import json
import uuid
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, status, Depends, Query
from pydantic import BaseModel, Field

from backend.api.dependencies import get_current_user, require_role
from backend.db.database import get_db_session
from backend.db.models import UserModel, ModelOutcomeModel
from backend.services.case_service import case_service
from backend.services.model_performance_service import model_performance_service
from backend.services.calibration_service import calibration_service
from backend.services.threshold_optimization_service import threshold_optimization_service
from backend.services.model_registry_service import model_registry_service
from backend.services.learning_service import learning_service
from backend.services.feedback_pipeline_service import feedback_pipeline_service

router = APIRouter(prefix="/api/v1/model", tags=["Model Intelligence & Learning"])

REPORT_PATH = Path("ml/reports/evaluation_report.json")
METADATA_PATH = Path("ml/artifacts/metadata.json")


# Pydantic Schemas for Outcome Ingestion & Threshold Approval
class OutcomeIngestionRequest(BaseModel):
    dispute_id: str = Field(..., json_schema_extra={"example": "DSP_000001"})
    actual_outcome: str = Field(..., json_schema_extra={"example": "WON"}, description="WON, LOST, or EXPIRED")
    resolution_timestamp: Optional[str] = Field(None, json_schema_extra={"example": "2026-08-24T12:00:00Z"})
    financial_recovery_amount: Optional[float] = Field(None, json_schema_extra={"example": 1500.0})
    justification: str = Field(..., min_length=5, json_schema_extra={"example": "Merchant dispute accepted and chargeback funds recovered from acquirer."})


class ThresholdApproveRequest(BaseModel):
    proposed_threshold: float = Field(..., json_schema_extra={"example": 0.35})
    reason: str = Field(..., min_length=10, json_schema_extra={"example": "Analytical evaluation shows superior net financial recovery at 0.35 threshold."})
    evidence_metrics: Optional[Dict[str, Any]] = Field(default_factory=dict)


# Existing & Updated Endpoints
@router.get("/performance", summary="Get Model Performance and Evaluation Metrics")
async def get_model_performance(
    timeframe: str = Query("30D", description="Timeframe horizon: 7D, 30D, 90D, ALL_TIME, daily, weekly, monthly"),
    data_state: str = Query("PRODUCTION", description="Data state filter: PRODUCTION or SIMULATION"),
    current_user: UserModel = Depends(get_current_user)
) -> Dict[str, Any]:
    """Returns model performance metrics calculated across the specified timeframe and data state."""
    try:
        metrics = model_performance_service.get_performance_by_timeframe(timeframe, data_state)

        metrics["model_metadata"] = {
            "model_id": "chargeshield_ml_v1",
            "model_type": "LightGBM + Logistic Regression Baseline",
            "optimal_threshold": 0.29,
            "status": "PRODUCTION"
        }

        # Attach artifact metadata for compatibility
        if REPORT_PATH.exists():
            try:
                with open(REPORT_PATH, "r", encoding="utf-8") as f:
                    eval_report = json.load(f)
                    metrics["evaluation_report_artifact"] = eval_report
                    metrics["evaluation_report"] = eval_report
            except Exception:
                pass

        return metrics
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load model performance metrics: {str(e)}"
        )


@router.get("/monitoring", summary="Get Model Monitoring & Drift Foundation Metrics")
async def get_model_monitoring(current_user: UserModel = Depends(get_current_user)):
    """Returns production model monitoring status, prediction distribution, and drift foundation."""
    try:
        from backend.services.model_monitor import model_monitor
        return model_monitor.get_monitoring_status()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve model monitoring metrics: {str(e)}"
        )


@router.get("/feedback", summary="Get Model-Human Agreement & Feedback Metrics")
async def get_model_feedback(current_user: UserModel = Depends(get_current_user)):
    """Returns AI vs Human agreement, disagreement rates, and disagreement case IDs."""
    try:
        from backend.services.feedback_service import feedback_service
        return feedback_service.get_feedback_metrics()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve model feedback metrics: {str(e)}"
        )


# Phase 12 Outcomes Ingestion & Query Endpoints
@router.post("/outcomes", summary="Record Ground-Truth Production Dispute Outcome")
async def record_dispute_outcome(
    payload: OutcomeIngestionRequest,
    current_user: UserModel = Depends(require_role(["ADMIN", "REVIEWER"]))
) -> Dict[str, Any]:
    """
    RBAC-protected endpoint (ADMIN, REVIEWER) to record actual dispute ground-truth outcomes.
    Rejects simulation cases, enforces outcome immutability, and logs audit events.
    """
    dispute_id = payload.dispute_id.strip()
    outcome_val = payload.actual_outcome.strip().upper()

    if outcome_val not in ["WON", "LOST", "EXPIRED"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid outcome '{outcome_val}'. Must be one of ['WON', 'LOST', 'EXPIRED']."
        )

    # Rule B: Rejection of simulation cases
    if dispute_id.startswith("DSP_SIM_"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="SIMULATION cases cannot receive production outcome labels. Outcome recording is strictly limited to PRODUCTION cases."
        )

    # Rule A: Case must exist in production corpus
    case_detail = case_service.get_case_detail(dispute_id)
    if not case_detail or "error" in case_detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dispute case '{dispute_id}' not found."
        )

    dispute_data = case_detail.get("dispute", {})
    if dispute_data.get("data_state") == "SIMULATION":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="SIMULATION cases cannot receive production outcome labels. Outcome recording is strictly limited to PRODUCTION cases."
        )


    with get_db_session() as db:
        # Rule C, D, E: Check existing outcome immutability
        existing = db.query(ModelOutcomeModel).filter(ModelOutcomeModel.dispute_id == dispute_id).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Outcome label for dispute '{dispute_id}' is immutable. Recorded outcome: '{existing.actual_outcome}' on {existing.created_at}. Duplicate or conflicting labels are rejected."
            )

        outcome_id = f"OUT_{dispute_id}_{uuid.uuid4().hex[:6].upper()}"
        res_time = payload.resolution_timestamp or datetime.now(timezone.utc).isoformat()
        now_iso = datetime.now(timezone.utc).isoformat()

        outcome_record = ModelOutcomeModel(
            outcome_id=outcome_id,
            dispute_id=dispute_id,
            actual_outcome=outcome_val,
            resolution_timestamp=res_time,
            financial_recovery_amount=payload.financial_recovery_amount,
            reviewer_id=current_user.username,
            justification=payload.justification,
            data_state="PRODUCTION",
            created_at=now_iso
        )
        db.add(outcome_record)
        db.commit()

        fin_status = "EXPLICIT_RECOVERY" if payload.financial_recovery_amount is not None else "INSUFFICIENT_DATA"

        return {
            "status": "RECORDED",
            "outcome_id": outcome_id,
            "dispute_id": dispute_id,
            "actual_outcome": outcome_val,
            "resolution_timestamp": res_time,
            "financial_recovery_amount": payload.financial_recovery_amount,
            "financial_status": fin_status,
            "data_state": "PRODUCTION",
            "reviewer_id": current_user.username,
            "justification": payload.justification,
            "created_at": now_iso
        }


@router.get("/outcomes", summary="Get Ground-Truth Production Dispute Outcomes")
async def get_dispute_outcomes(
    dispute_id: Optional[str] = None,
    current_user: UserModel = Depends(get_current_user)
) -> Dict[str, Any]:
    """Returns recorded ground-truth outcomes. Accessible by all authenticated roles."""
    with get_db_session() as db:
        query = db.query(ModelOutcomeModel).filter(ModelOutcomeModel.data_state == "PRODUCTION")
        if dispute_id:
            query = query.filter(ModelOutcomeModel.dispute_id == dispute_id)

        outcomes = query.order_by(ModelOutcomeModel.created_at.desc()).all()

        records = [
            {
                "outcome_id": o.outcome_id,
                "dispute_id": o.dispute_id,
                "actual_outcome": o.actual_outcome,
                "resolution_timestamp": o.resolution_timestamp,
                "financial_recovery_amount": o.financial_recovery_amount,
                "financial_status": "EXPLICIT_RECOVERY" if o.financial_recovery_amount is not None else "INSUFFICIENT_DATA",
                "reviewer_id": o.reviewer_id,
                "justification": o.justification,
                "data_state": o.data_state,
                "created_at": o.created_at
            }
            for o in outcomes
        ]

        return {
            "status": "SUCCESS",
            "total_outcomes": len(records),
            "outcomes": records,
            "data_provenance": "PRODUCTION"
        }


# Phase 12 Calibration, Thresholds, Registry, Learning & Approval Endpoints
@router.get("/calibration", summary="Get Model Probability Calibration Evaluation")
async def get_model_calibration(current_user: UserModel = Depends(get_current_user)) -> Dict[str, Any]:
    """Returns probability calibration analysis across 10 probability buckets."""
    return calibration_service.evaluate_calibration()


@router.get("/thresholds", summary="Get Multi-Threshold Optimization Analysis")
async def get_model_thresholds(current_user: UserModel = Depends(get_current_user)) -> Dict[str, Any]:
    """Returns comparative threshold optimization evaluations (0.10 - 0.90) and recommendation status."""
    return threshold_optimization_service.evaluate_thresholds()


@router.post("/thresholds/approve", summary="Approve Production Decision Threshold Modification")
async def approve_threshold_change(
    payload: ThresholdApproveRequest,
    current_user: UserModel = Depends(require_role(["ADMIN"]))
) -> Dict[str, Any]:
    """
    ADMIN-only endpoint to explicitly approve a production decision threshold modification.
    Creates an immutable audit entry and updates active production model configuration.
    """
    try:
        return threshold_optimization_service.approve_threshold_change(
            proposed_threshold=payload.proposed_threshold,
            admin_id=current_user.username,
            reason=payload.reason,
            evidence_metrics=payload.evidence_metrics or {}
        )
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )


@router.get("/registry", summary="Get Model Version Registry & Lifecycle Status")
async def get_model_registry(current_user: UserModel = Depends(get_current_user)) -> Dict[str, Any]:
    """Returns registered ML model versions and active lifecycle states."""
    return model_registry_service.get_registry_status()


@router.get("/learning", summary="Get Continuous Learning Readiness & Decision Feedback Metrics")
async def get_model_learning(current_user: UserModel = Depends(get_current_user)) -> Dict[str, Any]:
    """Returns learning readiness, eligible production cases, AI vs Human vs Outcome correctness metrics."""
    learning_metrics = learning_service.get_learning_metrics()
    readiness_info = feedback_pipeline_service.get_learning_readiness_and_eligibility()
    return {
        **learning_metrics,
        "pipeline_readiness": readiness_info
    }
