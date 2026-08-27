"""
FastAPI Router for Risk Case operations and ML predictions.
Exposes endpoints for listing cases, viewing case detail, predicting win probability, and SHAP explanations.
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query, status

from backend.schemas.cases import CaseListResponse, CaseDetailResponse
from backend.schemas.predictions import PredictionResponse, ExplanationResponse
from backend.agent.schemas import InvestigationReport
from backend.agent.investigator import investigation_agent
from backend.evidence.schemas import VerifiedInvestigationResponse
from backend.evidence.verifier import evidence_verifier
from backend.services.case_service import case_service
from backend.services.prediction_service import prediction_service

router = APIRouter(prefix="/api/v1/cases", tags=["Risk Cases"])

@router.get("", response_model=CaseListResponse, summary="List Chargeback Risk Cases")
async def list_cases(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status_filter: Optional[str] = Query(None, alias="status", description="Dispute status (e.g. CLOSED, NEW, UNDER_REVIEW)"),
    reason: Optional[str] = Query(None, description="Dispute reason code (e.g. 13.1_MERCH_NOT_RECEIVED)"),
    min_prob: Optional[float] = Query(None, ge=0.0, le=1.0, description="Minimum win probability"),
    max_prob: Optional[float] = Query(None, ge=0.0, le=1.0, description="Maximum win probability"),
    sort_by: Optional[str] = Query("newest", description="Sort order: newest, oldest, amount_desc, amount_asc, prob_desc, prob_asc"),
    search: Optional[str] = Query(None, description="Global search query across dispute ID, transaction ID, customer ID, or reason code")
):
    """
    Retrieves a paginated list of risk cases with configurable filtering, global search, and sorting.
    """
    res = case_service.list_cases(
        page=page,
        page_size=page_size,
        status=status_filter,
        reason=reason,
        min_prob=min_prob,
        max_prob=max_prob,
        sort_by=sort_by,
        search=search
    )
    return res

@router.get("/{dispute_id}", response_model=CaseDetailResponse, summary="Get Risk Case Detail")
async def get_case_detail(dispute_id: str):
    """
    Retrieves full relational entity details for a single chargeback case.
    Includes dispute, customer, transaction, order, delivery, communications, and ML prediction.
    """
    detail = case_service.get_case_detail(dispute_id)
    if not detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chargeback dispute case '{dispute_id}' not found."
        )
    return detail

@router.get("/{dispute_id}/prediction", response_model=PredictionResponse, summary="Get Case ML Prediction")
async def get_case_prediction(dispute_id: str):
    """
    Invokes the trained Phase 2 LightGBM ML Engine artifact to calculate the calibrated win probability.
    """
    try:
        pred = prediction_service.predict_dispute(dispute_id)
        return pred
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction computation failed: {str(e)}"
        )

@router.get("/{dispute_id}/explanation", response_model=ExplanationResponse, summary="Get Case SHAP Explanation")
async def get_case_explanation(dispute_id: str):
    """
    Extracts SHAP TreeExplainer feature attributions for a given dispute prediction.
    """
    try:
        explanation = prediction_service.explain_dispute(dispute_id)
        return explanation
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"SHAP explanation computation failed: {str(e)}"
        )

@router.post("/{dispute_id}/investigate", response_model=InvestigationReport, summary="Run Read-Only AI Risk Investigation")
async def investigate_case(dispute_id: str):
    """
    Executes a read-only evidence-grounded risk investigation for a single dispute case.
    Returns structured InvestigationReport containing executive summary, timeline, supporting/risk factors, ML assessment, and evidence references.
    """
    try:
        report = investigation_agent.investigate_case(dispute_id)
        return report
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Investigation execution failed: {str(e)}"
        )

@router.post("/{dispute_id}/verify", response_model=VerifiedInvestigationResponse, summary="Run Evidence Verification & Citations")
async def verify_case_investigation(dispute_id: str):
    """
    Executes Phase 5 evidence verification comparing AI investigation claims against authoritative Phase 3 relational records and Phase 2 ML outputs.
    Returns VerifiedInvestigationResponse containing InvestigationReport, VerificationSummary, and itemized VerificationResults with citations.
    """
    try:
        report = investigation_agent.investigate_case(dispute_id)
        res = evidence_verifier.verify_investigation(dispute_id, report)
        return res
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Evidence verification failed: {str(e)}"
        )

@router.get("/{dispute_id}/simulate", summary="Run Decision Simulator Scenarios")
async def simulate_case_decision(dispute_id: str):
    """
    Simulates financial and risk outcomes for CONTEST vs DO NOT CONTEST vs ESCALATE decisions.
    Distinguishes Model Estimates from Recorded Actual Outcomes.
    """
    try:
        from backend.services.simulation_service import simulation_service
        detail = case_service.get_case_detail(dispute_id)
        if not detail:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Chargeback dispute case '{dispute_id}' not found."
            )
        amt = detail["dispute"]["disputed_amount"]
        win_prob = detail["prediction"]["win_probability"]
        res = simulation_service.simulate_decision_scenarios(dispute_id, amt, win_prob)
        return res
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Decision simulation failed: {str(e)}"
        )


@router.get("/{dispute_id}/timeline", summary="Get Case Investigation Chronological Timeline")
async def get_case_timeline(dispute_id: str):
    """
    Returns chronological investigation timeline tracking events from transaction creation
    through dispute filing, model prediction, evidence verification, priority assignment, and human review.
    """
    try:
        timeline = case_service.get_case_timeline(dispute_id)
        if not timeline:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Chargeback dispute case '{dispute_id}' not found."
            )
        return timeline
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate case investigation timeline: {str(e)}"
        )



