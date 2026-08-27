"""
Human Review & Decision Workflow Service for ChargeShield Phase 6 & Phase 8.
Manages persistent review queue, case package assembly, decision recording, state transitions,
duplicate protection, and paginated audit logs backed by SQLite (chargeshield.db).
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from sqlalchemy import func

from backend.db.database import get_db_session, init_db
from backend.db.models import ReviewStateModel, ReviewDecisionModel
from backend.review.schemas import (
    DecisionEnum, ReviewStateEnum, ReviewQueueItem, ReviewQueueResponse,
    DecisionRequest, DecisionRecord, ReviewCasePackage, AuditLogResponse
)
from backend.schemas.cases import CaseDetailResponse
from backend.schemas.predictions import PredictionResponse
from backend.services.case_service import case_service
from backend.services.prediction_service import prediction_service
from backend.agent.investigator import investigation_agent
from backend.evidence.verifier import evidence_verifier
from backend.core.logging import logger

class DuplicateDecisionError(Exception):
    """Raised when attempting to submit a decision on an already decided case."""
    pass


class ReviewService:
    """Service managing persistent human review workflow, review queue, and decision audit log."""

    def __init__(self):
        # Ensure database tables are ready on service initialization
        try:
            init_db()
        except Exception as e:
            logger.warning(f"Database initialization warning in ReviewService: {str(e)}")

    def get_review_status(self, dispute_id: str) -> ReviewStateEnum:
        """Queries persistent review state for a dispute case."""
        with get_db_session() as session:
            state_rec = session.query(ReviewStateModel).filter(ReviewStateModel.dispute_id == dispute_id).first()
            if state_rec:
                return ReviewStateEnum(state_rec.review_status)
            return ReviewStateEnum.PENDING_REVIEW

    def get_queue(
        self,
        status: Optional[str] = None,
        recommendation: Optional[str] = None,
        min_prob: Optional[float] = None,
        max_prob: Optional[float] = None,
        page: int = 1,
        page_size: int = 20
    ) -> ReviewQueueResponse:
        """
        Retrieves paginated and ordered review queue for human risk analysts.
        Orders cases by transparent priority score (verification risk, threshold proximity, amount).
        """
        cases_page = case_service.list_cases(page=1, page_size=100)
        items: List[ReviewQueueItem] = []

        # Batch load states from database
        with get_db_session() as session:
            states_db = {s.dispute_id: s.review_status for s in session.query(ReviewStateModel).all()}

        for case_sum in cases_page["items"]:
            disp_id = case_sum["dispute_id"]
            rev_status_str = states_db.get(disp_id, ReviewStateEnum.PENDING_REVIEW.value)
            rev_status = ReviewStateEnum(rev_status_str)
            
            # Predict win probability
            pred = prediction_service.predict_dispute(disp_id)
            win_prob = pred["win_probability"]
            rec_action = pred["recommendation"]
            amt = case_sum["disputed_amount"]

            # Calculate priority score
            thresh_proximity = max(0.0, 1.0 - abs(win_prob - 0.29))
            priority_score = round(
                (thresh_proximity * 40.0) + (amt / 100.0) + (win_prob * 10.0),
                2
            )

            item = ReviewQueueItem(
                dispute_id=disp_id,
                disputed_amount=amt,
                currency=case_sum.get("currency", "INR"),
                dispute_reason=case_sum["dispute_reason_code"],
                win_probability=win_prob,
                ai_recommendation=rec_action,
                verification_rate=1.0,
                review_status=rev_status,
                priority_score=priority_score,
                created_at=case_sum["dispute_creation_timestamp"]
            )
            items.append(item)

        # Apply optional filters
        if status:
            items = [i for i in items if i.review_status.value.upper() == status.upper()]
        if recommendation:
            items = [i for i in items if i.ai_recommendation.upper() == recommendation.upper()]
        if min_prob is not None:
            items = [i for i in items if i.win_probability >= min_prob]
        if max_prob is not None:
            items = [i for i in items if i.win_probability <= max_prob]

        # Priority ordering: highest priority score first
        items.sort(key=lambda x: x.priority_score, reverse=True)

        total = len(items)
        pending_count = sum(1 for i in items if i.review_status in (ReviewStateEnum.PENDING_REVIEW, ReviewStateEnum.IN_REVIEW))
        decided_count = sum(1 for i in items if i.review_status == ReviewStateEnum.DECIDED)
        escalated_count = sum(1 for i in items if i.review_status == ReviewStateEnum.ESCALATED)

        # Pagination calculations
        page_size = max(1, min(page_size, 100))
        total_pages = (total + page_size - 1) // page_size if total > 0 else 1
        page = max(1, min(page, total_pages)) if total > 0 else 1

        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paged_items = items[start_idx:end_idx]

        return ReviewQueueResponse(
            items=paged_items,
            total=total,
            pending_count=pending_count,
            decided_count=decided_count,
            escalated_count=escalated_count,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )

    def get_review_package(self, dispute_id: str) -> ReviewCasePackage:
        """
        Assembles complete reviewer package combining Case Detail, ML Prediction,
        Investigation Report, Evidence Verification, and Persistent Decision History.
        """
        case_dict = case_service.get_case_detail(dispute_id)
        if not case_dict:
            raise ValueError(f"Dispute case '{dispute_id}' not found.")

        # Update state to IN_REVIEW in database if currently PENDING_REVIEW
        now_iso = datetime.now(timezone.utc).isoformat()
        current_state = ReviewStateEnum.PENDING_REVIEW

        with get_db_session() as session:
            state_rec = session.query(ReviewStateModel).filter(ReviewStateModel.dispute_id == dispute_id).first()
            if state_rec:
                current_state = ReviewStateEnum(state_rec.review_status)
                if current_state == ReviewStateEnum.PENDING_REVIEW:
                    state_rec.review_status = ReviewStateEnum.IN_REVIEW.value
                    state_rec.updated_at = now_iso
                    current_state = ReviewStateEnum.IN_REVIEW
            else:
                new_state = ReviewStateModel(
                    dispute_id=dispute_id,
                    review_status=ReviewStateEnum.IN_REVIEW.value,
                    updated_at=now_iso
                )
                session.add(new_state)
                current_state = ReviewStateEnum.IN_REVIEW

            # Fetch existing decisions for this dispute
            dec_recs = session.query(ReviewDecisionModel).filter(
                ReviewDecisionModel.dispute_id == dispute_id
            ).order_by(ReviewDecisionModel.created_at.asc()).all()

            decisions = [
                DecisionRecord(
                    decision_id=d.decision_id,
                    dispute_id=d.dispute_id,
                    reviewer_id=d.reviewer_id,
                    decision=DecisionEnum(d.decision),
                    reason=d.reason,
                    ai_recommendation=d.ai_recommendation,
                    ai_win_probability=d.ai_win_probability,
                    verification_rate=d.verification_rate,
                    created_at=d.created_at
                )
                for d in dec_recs
            ]

        # Fetch predictions, investigation, and verification
        pred_dict = prediction_service.predict_dispute(dispute_id)
        report = investigation_agent.investigate_case(dispute_id)
        verification_resp = evidence_verifier.verify_investigation(dispute_id, report)

        return ReviewCasePackage(
            dispute_id=dispute_id,
            case=CaseDetailResponse(**case_dict),
            prediction=PredictionResponse(**pred_dict),
            investigation=report,
            verification=verification_resp,
            review_status=current_state,
            decisions=decisions,
            is_synthetic_data=True,
            disclaimer="HUMAN AUTHORIZATION REQUIRED. AI output is advisory only."
        )

    def submit_decision(self, dispute_id: str, request: DecisionRequest) -> DecisionRecord:
        """
        Records human reviewer decision into persistent database store.
        Enforces duplicate decision protection (HTTP 409) and updates review state.
        """
        case_dict = case_service.get_case_detail(dispute_id)
        if not case_dict:
            raise ValueError(f"Dispute case '{dispute_id}' not found.")

        now_iso = datetime.now(timezone.utc).isoformat()

        with get_db_session() as session:
            state_rec = session.query(ReviewStateModel).filter(ReviewStateModel.dispute_id == dispute_id).first()
            if state_rec and state_rec.review_status == ReviewStateEnum.DECIDED.value:
                raise DuplicateDecisionError(f"Case '{dispute_id}' has already been DECIDED. Duplicate decisions are rejected.")

            # Fetch prediction & verification status for decision audit record
            pred_dict = prediction_service.predict_dispute(dispute_id)
            report = investigation_agent.investigate_case(dispute_id)
            verification_resp = evidence_verifier.verify_investigation(dispute_id, report)

            # Generate unique decision ID
            count = session.query(ReviewDecisionModel).filter(ReviewDecisionModel.dispute_id == dispute_id).count()
            decision_id = f"DEC_{dispute_id}_{count + 1:03d}"

            dec_db = ReviewDecisionModel(
                decision_id=decision_id,
                dispute_id=dispute_id,
                reviewer_id=request.reviewer_id,
                decision=request.decision.value,
                reason=request.reason,
                ai_recommendation=pred_dict["recommendation"],
                ai_win_probability=pred_dict["win_probability"],
                verification_rate=verification_resp.verification_summary.verification_rate,
                created_at=now_iso
            )
            session.add(dec_db)

            # Update or create review state record
            target_status = ReviewStateEnum.ESCALATED.value if request.decision == DecisionEnum.ESCALATE else ReviewStateEnum.DECIDED.value
            if state_rec:
                state_rec.review_status = target_status
                state_rec.updated_at = now_iso
            else:
                new_state = ReviewStateModel(
                    dispute_id=dispute_id,
                    review_status=target_status,
                    updated_at=now_iso
                )
                session.add(new_state)

            rec = DecisionRecord(
                decision_id=decision_id,
                dispute_id=dispute_id,
                reviewer_id=request.reviewer_id,
                decision=request.decision,
                reason=request.reason,
                ai_recommendation=pred_dict["recommendation"],
                ai_win_probability=pred_dict["win_probability"],
                verification_rate=verification_resp.verification_summary.verification_rate,
                created_at=now_iso
            )

        logger.info(f"Persisted human decision '{request.decision.value}' for dispute {dispute_id} by reviewer '{request.reviewer_id}'.")
        return rec

    def get_audit_log(
        self,
        dispute_id: Optional[str] = None,
        reviewer_id: Optional[str] = None,
        decision: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> AuditLogResponse:
        """
        Queries persistent append-only decision audit log with optional search/filter parameters and pagination.
        """
        with get_db_session() as session:
            query = session.query(ReviewDecisionModel)

            if dispute_id and dispute_id.strip():
                query = query.filter(ReviewDecisionModel.dispute_id.ilike(f"%{dispute_id.strip()}%"))
            if reviewer_id and reviewer_id.strip():
                query = query.filter(ReviewDecisionModel.reviewer_id.ilike(f"%{reviewer_id.strip()}%"))
            if decision and decision.strip() and decision.upper() != "ALL":
                query = query.filter(ReviewDecisionModel.decision == decision.strip().upper())

            total = query.count()

            # Ordering by created_at descending (newest decisions first)
            query = query.order_by(ReviewDecisionModel.created_at.desc())

            page_size = max(1, min(page_size, 100))
            total_pages = (total + page_size - 1) // page_size if total > 0 else 1
            page = max(1, min(page, total_pages)) if total > 0 else 1

            offset = (page - 1) * page_size
            db_records = query.offset(offset).limit(page_size).all()

            items = [
                DecisionRecord(
                    decision_id=d.decision_id,
                    dispute_id=d.dispute_id,
                    reviewer_id=d.reviewer_id,
                    decision=DecisionEnum(d.decision),
                    reason=d.reason,
                    ai_recommendation=d.ai_recommendation,
                    ai_win_probability=d.ai_win_probability,
                    verification_rate=d.verification_rate,
                    created_at=d.created_at
                )
                for d in db_records
            ]

        return AuditLogResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            is_synthetic_data=True,
            disclaimer="HUMAN AUTHORIZATION REQUIRED. AI output is advisory only."
        )

review_service = ReviewService()
