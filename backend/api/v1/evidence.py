"""
Evidence Management API Router for ChargeShield Phase 14 Milestone 3.
Provides secure endpoints for document upload, metadata listing, streaming download,
and admin revocation with server-side RBAC and data-state governance.
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Header, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from backend.db.database import get_db
from backend.db.models import UserModel
from backend.api.dependencies import get_current_user, require_role
from backend.services.evidence_storage_service import evidence_storage_service
from backend.core.api_response import success_response, error_response

router = APIRouter(prefix="/api/v1", tags=["Evidence Management"])


@router.post(
    "/cases/{dispute_id}/evidence-upload",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Upload dispute evidence document"
)
async def upload_evidence(
    dispute_id: str,
    file: UploadFile = File(...),
    current_user: UserModel = Depends(require_role(["ADMIN", "REVIEWER"])),
    db: Session = Depends(get_db),
    x_correlation_id: Optional[str] = Header(None, alias="X-Correlation-ID")
):
    """
    Uploads an evidence document (PDF, PNG, JPG, CSV, TXT) for a dispute case.
    RBAC: ADMIN or REVIEWER required.
    Validates file size, file type, SHA-256 integrity, path traversal safety,
    and handles duplicate detection idempotently.
    """
    corr_id = x_correlation_id or f"corr-upload-{current_user.username}"

    if not file or not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file provided in upload request payload."
        )

    try:
        file_bytes = await file.read()
        if not file_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty (0 bytes)."
            )

        result = evidence_storage_service.store_evidence_document(
            db=db,
            dispute_id=dispute_id,
            file_bytes=file_bytes,
            original_filename=file.filename,
            content_type=file.content_type or "application/octet-stream",
            uploaded_by=current_user.username,
            correlation_id=corr_id
        )

        return success_response(
            data=result["evidence"],
            message=result["message"],
            request_id=corr_id,
            meta={"upload_status": result["status"]}
        )

    except ValueError as ve:
        err_msg = str(ve)
        if "does not exist" in err_msg:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=err_msg)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err_msg)
    except HTTPException:
        raise
    except Exception as ex:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error processing evidence upload: {str(ex)}"
        )


@router.get(
    "/cases/{dispute_id}/evidence",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="List evidence documents for dispute"
)
def list_evidence(
    dispute_id: str,
    current_user: UserModel = Depends(require_role(["ADMIN", "REVIEWER", "ANALYST", "AUDITOR"])),
    db: Session = Depends(get_db),
    x_correlation_id: Optional[str] = Header(None, alias="X-Correlation-ID")
):
    """
    Lists active evidence metadata records for a dispute.
    RBAC: ADMIN, REVIEWER, ANALYST, or AUDITOR.
    """
    corr_id = x_correlation_id or f"corr-list-{current_user.username}"

    docs = evidence_storage_service.list_evidence_documents(
        db=db,
        dispute_id=dispute_id
    )

    return success_response(
        data={"dispute_id": dispute_id, "evidence_documents": docs, "total_count": len(docs)},
        message=f"Retrieved {len(docs)} evidence document(s) for case '{dispute_id}'.",
        request_id=corr_id
    )


@router.get(
    "/cases/{dispute_id}/evidence/{evidence_id}",
    summary="Download / view evidence document binary stream"
)
def download_evidence(
    dispute_id: str,
    evidence_id: str,
    current_user: UserModel = Depends(require_role(["ADMIN", "REVIEWER", "ANALYST", "AUDITOR"])),
    db: Session = Depends(get_db),
    x_correlation_id: Optional[str] = Header(None, alias="X-Correlation-ID")
):
    """
    Safely streams physical evidence file to authorized callers.
    RBAC: ADMIN, REVIEWER, ANALYST, or AUDITOR.
    Prevents path traversal, raw path disclosure, and cross-dispute document access.
    """
    corr_id = x_correlation_id or f"corr-download-{current_user.username}"

    try:
        full_path, content_type, original_filename, data_state = evidence_storage_service.get_evidence_file_info(
            db=db,
            dispute_id=dispute_id,
            evidence_id=evidence_id,
            actor_id=current_user.username,
            correlation_id=corr_id
        )

        return FileResponse(
            path=full_path,
            media_type=content_type,
            filename=original_filename,
            headers={
                "X-ChargeShield-Evidence-ID": evidence_id,
                "X-ChargeShield-Data-State": data_state,
                "Content-Disposition": f'inline; filename="{original_filename}"'
            }
        )

    except KeyError as ke:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ke))
    except FileNotFoundError as fe:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(fe))
    except Exception as ex:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error retrieving evidence file: {str(ex)}"
        )


@router.delete(
    "/cases/{dispute_id}/evidence/{evidence_id}",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Revoke evidence document"
)
def revoke_evidence(
    dispute_id: str,
    evidence_id: str,
    current_user: UserModel = Depends(require_role(["ADMIN"])),
    db: Session = Depends(get_db),
    x_correlation_id: Optional[str] = Header(None, alias="X-Correlation-ID")
):
    """
    Revokes an evidence document.
    RBAC: ADMIN role strictly required (REVIEWER/ANALYST/AUDITOR forbidden -> 403).
    """
    corr_id = x_correlation_id or f"corr-revoke-{current_user.username}"

    try:
        result = evidence_storage_service.revoke_evidence_document(
            db=db,
            dispute_id=dispute_id,
            evidence_id=evidence_id,
            actor_id=current_user.username,
            correlation_id=corr_id
        )

        return success_response(
            data=result["evidence"],
            message=result["message"],
            request_id=corr_id
        )

    except KeyError as ke:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ke))
    except Exception as ex:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error revoking evidence document: {str(ex)}"
        )
