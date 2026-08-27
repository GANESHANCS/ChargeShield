"""
Report Export API Endpoints for ChargeShield.
Exposes JSON and CSV operational data export endpoints with explicit data provenance metadata.
"""

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session
from backend.db.database import get_db
from backend.services.export_service import export_service
from backend.api.dependencies import get_current_user
from backend.db.models import UserModel

router = APIRouter(prefix="/api/v1/export", tags=["Report & Audit Export"])

@router.get("/cases", summary="Export Dispute Cases Report")
async def export_cases(
    format: str = Query("json", pattern="^(json|csv)$", description="Export format: json or csv"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Exports full dispute cases dataset in JSON or CSV format.
    Embeds explicit data provenance headers (DATA STATE: PRODUCTION vs SIMULATION).
    """
    if format.lower() == "csv":
        csv_content = export_service.export_cases_csv(db)
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=chargeshield_cases_export.csv"}
        )
    
    return export_service.export_cases_json(db)


@router.get("/audit", summary="Export Review Decision Audit Log")
async def export_audit_log(
    format: str = Query("json", pattern="^(json|csv)$", description="Export format: json or csv"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Exports append-only human review audit decisions in JSON or CSV format.
    Includes reviewer ID, decision, AI recommendation, timestamp, and justification reason.
    """
    if format.lower() == "csv":
        csv_content = export_service.export_audit_log_csv(db)
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=chargeshield_audit_log_export.csv"}
        )

    return export_service.export_audit_log_json(db)
