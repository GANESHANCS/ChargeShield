"""
Evidence Storage Service for ChargeShield Phase 14 Milestone 3.
Provides extensible file storage abstraction, secure filename sanitization,
path traversal prevention, SHA-256 checksum calculation, duplicate detection,
atomic filesystem-SQL rollback, and data-state governance.
"""

import os
import re
import hmac
import hashlib
import pathlib
import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session

from backend.core.config import settings
from backend.core.constants import DataState
from backend.db.models import DisputeModel, EvidenceDocumentModel
from backend.services.event_service import event_service
import logging

logger = logging.getLogger("chargeshield.evidence")

# Allowed extensions and content types
ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".csv", ".txt"}
ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "image/png",
    "image/jpeg",
    "image/jpg",
    "text/csv",
    "text/plain",
    "application/csv",
    "application/octet-stream",  # Evaluated alongside extension
}

DANGEROUS_EXTENSIONS = {
    ".exe", ".sh", ".py", ".php", ".js", ".bat", ".cmd", ".dll", ".so",
    ".bin", ".vbs", ".ps1", ".jar", ".app", ".msi", ".scr", ".pif", ".cpl"
}


class EvidenceStorageService:
    """
    Extensible evidence storage manager supporting local filesystem storage
    and abstracting operations for future object/S3 storage providers.
    """

    def __init__(self, base_storage_path: Optional[str] = None, max_file_size_mb: Optional[int] = None):
        self.base_storage_path = base_storage_path or settings.EVIDENCE_STORAGE_PATH
        self.max_file_size_bytes = (max_file_size_mb or settings.EVIDENCE_MAX_FILE_SIZE_MB) * 1024 * 1024
        self._ensure_storage_directory()

    def _ensure_storage_directory(self):
        """Ensures storage directory exists."""
        os.makedirs(self.base_storage_path, exist_ok=True)

    def sanitize_filename(self, filename: str) -> str:
        """
        Sanitizes raw user filename to prevent path traversal and shell injection.
        Strips directory paths, drive letters, and dangerous characters.
        """
        if not filename:
            return "unnamed_document.bin"

        # Strip directory components (handles Windows and Unix separators)
        clean = os.path.basename(filename)
        clean = pathlib.Path(clean).name

        # Remove null bytes or non-printable ASCII
        clean = clean.replace("\x00", "").strip()

        # Replace non-alphanumeric (except dot, underscore, hyphen) with underscore
        clean = re.sub(r"[^a-zA-Z0-9_\.-]", "_", clean)

        # Prevent hidden files or leading dots
        clean = clean.lstrip(".")

        if not clean:
            clean = "sanitized_document"

        # Truncate safe filename to 200 characters max
        if len(clean) > 200:
            ext = pathlib.Path(clean).suffix
            clean = clean[: 200 - len(ext)] + ext

        return clean

    def validate_file(self, filename: str, content_type: str, file_size: int) -> Tuple[bool, Optional[str]]:
        """
        Validates file size, extension, content type, and dangerous file flags.
        Returns (is_valid, error_message).
        """
        if file_size > self.max_file_size_bytes:
            max_mb = self.max_file_size_bytes / (1024 * 1024)
            return False, f"File size ({file_size / (1024 * 1024):.2f} MB) exceeds maximum allowed limit of {max_mb:.1f} MB."

        ext = pathlib.Path(filename).suffix.lower()

        if ext in DANGEROUS_EXTENSIONS:
            return False, f"Forbidden file extension '{ext}'. Executable and script files are strictly prohibited."

        if ext not in ALLOWED_EXTENSIONS:
            return False, f"Unsupported file type extension '{ext}'. Supported formats: PDF, PNG, JPG, JPEG, CSV, TXT."

        # Check content type if provided
        ct_clean = content_type.split(";")[0].strip().lower() if content_type else ""
        if ct_clean and ct_clean not in ALLOWED_CONTENT_TYPES:
            # Allow fallback if extension matches allowed list
            if ext not in ALLOWED_EXTENSIONS:
                return False, f"Unsupported Content-Type '{content_type}' for evidence document."

        return True, None

    def store_evidence_document(
        self,
        db: Session,
        dispute_id: str,
        file_bytes: bytes,
        original_filename: str,
        content_type: str,
        uploaded_by: str,
        correlation_id: str = "corr-evidence-upload"
    ) -> Dict[str, Any]:
        """
        Atomically persists physical file and database metadata record for evidence.
        Enforces dispute existence, data-state inheritance, SHA-256 deduplication,
        and transactional rollback cleanup on failure.
        """
        # 1. Verify dispute existence and retrieve data state
        dispute = db.query(DisputeModel).filter(DisputeModel.dispute_id == dispute_id).first()
        if not dispute:
            self._audit_event(
                action="EVIDENCE_REJECTED",
                actor=uploaded_by,
                dispute_id=dispute_id,
                evidence_id=None,
                data_state="UNKNOWN",
                correlation_id=correlation_id,
                details={"reason": "Dispute not found"}
            )
            raise ValueError(f"Dispute case '{dispute_id}' does not exist.")

        data_state = dispute.data_state

        # 2. Validate file size & type
        file_size = len(file_bytes)
        safe_filename = self.sanitize_filename(original_filename)
        is_valid, err_msg = self.validate_file(safe_filename, content_type, file_size)

        if not is_valid:
            self._audit_event(
                action="EVIDENCE_REJECTED",
                actor=uploaded_by,
                dispute_id=dispute_id,
                evidence_id=None,
                data_state=data_state,
                correlation_id=correlation_id,
                details={"reason": err_msg, "filename": safe_filename}
            )
            raise ValueError(err_msg)

        # 3. Calculate SHA-256 hash
        sha256_hash = hashlib.sha256(file_bytes).hexdigest()

        # 4. Idempotency / Duplicate Detection
        existing_doc = db.query(EvidenceDocumentModel).filter(
            EvidenceDocumentModel.dispute_id == dispute_id,
            EvidenceDocumentModel.sha256_hash == sha256_hash,
            EvidenceDocumentModel.status == "ACTIVE"
        ).first()

        if existing_doc:
            self._audit_event(
                action="EVIDENCE_DUPLICATE_ATTEMPT",
                actor=uploaded_by,
                dispute_id=dispute_id,
                evidence_id=existing_doc.evidence_id,
                data_state=data_state,
                correlation_id=correlation_id,
                details={"sha256_hash": sha256_hash, "original_filename": original_filename}
            )
            return {
                "status": "DUPLICATE_IDEMPOTENT",
                "message": f"Identical evidence document already exists for dispute '{dispute_id}'.",
                "evidence": self._model_to_dict(existing_doc)
            }

        # 5. Generate internal IDs and storage path
        evidence_id = f"EVD_{uuid.uuid4().hex[:12].upper()}"
        now_iso = datetime.now(timezone.utc).isoformat()
        
        # Subfolder per dispute to prevent single directory overcrowding
        dispute_dir = os.path.join(self.base_storage_path, dispute_id)
        os.makedirs(dispute_dir, exist_ok=True)

        physical_filename = f"{evidence_id}_{safe_filename}"
        full_physical_path = os.path.abspath(os.path.join(dispute_dir, physical_filename))
        relative_storage_key = f"{dispute_id}/{physical_filename}"

        # Prevent path traversal outside base storage path
        base_abs = os.path.abspath(self.base_storage_path)
        if not full_physical_path.startswith(base_abs):
            raise ValueError("Path traversal attempt detected in physical storage resolution.")

        # 6. Physical File Write
        file_created = False
        try:
            with open(full_physical_path, "wb") as f:
                f.write(file_bytes)
            file_created = True

            # 7. Database Entity Creation
            doc_model = EvidenceDocumentModel(
                evidence_id=evidence_id,
                dispute_id=dispute_id,
                original_filename=original_filename,
                safe_filename=safe_filename,
                content_type=content_type or "application/octet-stream",
                file_size=file_size,
                sha256_hash=sha256_hash,
                storage_key=relative_storage_key,
                uploaded_by=uploaded_by,
                uploaded_at=now_iso,
                data_state=data_state,
                status="ACTIVE",
                created_at=now_iso,
                updated_at=now_iso
            )
            db.add(doc_model)
            db.commit()
            db.refresh(doc_model)

            self._audit_event(
                action="EVIDENCE_UPLOAD",
                actor=uploaded_by,
                dispute_id=dispute_id,
                evidence_id=evidence_id,
                data_state=data_state,
                correlation_id=correlation_id,
                details={"filename": safe_filename, "file_size": file_size, "sha256_hash": sha256_hash}
            )

            return {
                "status": "SUCCESS",
                "message": f"Evidence document '{safe_filename}' uploaded successfully.",
                "evidence": self._model_to_dict(doc_model)
            }

        except Exception as ex:
            db.rollback()
            # Rollback compensating action: delete physical file if created
            if file_created and os.path.exists(full_physical_path):
                try:
                    os.remove(full_physical_path)
                except Exception as cleanup_ex:
                    logger.error(f"Failed to clean up physical file '{full_physical_path}' after DB failure: {cleanup_ex}")
            
            logger.error(f"Error persisting evidence document for dispute '{dispute_id}': {str(ex)}")
            raise ex

    def list_evidence_documents(
        self,
        db: Session,
        dispute_id: str,
        data_state_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieves all active evidence documents associated with a dispute case,
        filtered by data_state isolation bounds.
        """
        query = db.query(EvidenceDocumentModel).filter(
            EvidenceDocumentModel.dispute_id == dispute_id,
            EvidenceDocumentModel.status == "ACTIVE"
        )

        if data_state_filter:
            query = query.filter(EvidenceDocumentModel.data_state == data_state_filter)

        documents = query.order_by(EvidenceDocumentModel.created_at.desc()).all()
        return [self._model_to_dict(doc) for doc in documents]

    def get_evidence_file_info(
        self,
        db: Session,
        dispute_id: str,
        evidence_id: str,
        actor_id: str = "system",
        correlation_id: str = "corr-evidence-download"
    ) -> Tuple[str, str, str, str]:
        """
        Retrieves physical file path, content type, original filename, and data_state for streaming.
        Validates dispute ownership, evidence status, and path traversal safety.
        Returns (full_physical_path, content_type, original_filename, data_state).
        """
        doc = db.query(EvidenceDocumentModel).filter(
            EvidenceDocumentModel.evidence_id == evidence_id,
            EvidenceDocumentModel.dispute_id == dispute_id,
            EvidenceDocumentModel.status == "ACTIVE"
        ).first()

        if not doc:
            raise KeyError(f"Evidence document '{evidence_id}' not found for dispute '{dispute_id}'.")

        base_abs = os.path.abspath(self.base_storage_path)
        full_physical_path = os.path.abspath(os.path.join(self.base_storage_path, doc.storage_key))

        # Strict Path Traversal Check
        if not full_physical_path.startswith(base_abs) or not os.path.exists(full_physical_path):
            logger.error(f"Physical file missing or path traversal attempt for key '{doc.storage_key}'")
            raise FileNotFoundError(f"Physical evidence file for '{evidence_id}' could not be located.")

        self._audit_event(
            action="EVIDENCE_VIEW",
            actor=actor_id,
            dispute_id=dispute_id,
            evidence_id=evidence_id,
            data_state=doc.data_state,
            correlation_id=correlation_id,
            details={"filename": doc.safe_filename}
        )

        return full_physical_path, doc.content_type, doc.original_filename, doc.data_state

    def revoke_evidence_document(
        self,
        db: Session,
        dispute_id: str,
        evidence_id: str,
        actor_id: str,
        correlation_id: str = "corr-evidence-revoke"
    ) -> Dict[str, Any]:
        """
        Soft-deletes/revokes an evidence document record. ADMIN role required.
        """
        doc = db.query(EvidenceDocumentModel).filter(
            EvidenceDocumentModel.evidence_id == evidence_id,
            EvidenceDocumentModel.dispute_id == dispute_id,
            EvidenceDocumentModel.status == "ACTIVE"
        ).first()

        if not doc:
            raise KeyError(f"Evidence document '{evidence_id}' not found or already revoked.")

        now_iso = datetime.now(timezone.utc).isoformat()
        doc.status = "REVOKED"
        doc.updated_at = now_iso
        db.commit()
        db.refresh(doc)

        self._audit_event(
            action="EVIDENCE_REVOKE",
            actor=actor_id,
            dispute_id=dispute_id,
            evidence_id=evidence_id,
            data_state=doc.data_state,
            correlation_id=correlation_id,
            details={"revoked_by": actor_id}
        )

        return {
            "status": "SUCCESS",
            "message": f"Evidence document '{evidence_id}' has been revoked successfully.",
            "evidence": self._model_to_dict(doc)
        }

    def _model_to_dict(self, model: EvidenceDocumentModel) -> Dict[str, Any]:
        """Converts EvidenceDocumentModel to dictionary without exposing storage paths."""
        return {
            "evidence_id": model.evidence_id,
            "dispute_id": model.dispute_id,
            "original_filename": model.original_filename,
            "safe_filename": model.safe_filename,
            "content_type": model.content_type,
            "file_size": model.file_size,
            "sha256_hash": model.sha256_hash,
            "uploaded_by": model.uploaded_by,
            "uploaded_at": model.uploaded_at,
            "data_state": model.data_state,
            "status": model.status,
            "created_at": model.created_at,
            "updated_at": model.updated_at,
        }

    def _audit_event(
        self,
        action: str,
        actor: str,
        dispute_id: str,
        evidence_id: Optional[str],
        data_state: str,
        correlation_id: str,
        details: Optional[Dict[str, Any]] = None
    ):
        """Publishes audit log event via event_service."""
        try:
            event_service.publish_event(
                event_type=action,
                message=f"Evidence event '{action}' performed by actor '{actor}' on dispute '{dispute_id}'.",
                source="EVIDENCE_STORAGE_SERVICE",
                dispute_id=dispute_id,
                data_state=data_state,
                metadata={
                    "actor": actor,
                    "evidence_id": evidence_id,
                    "correlation_id": correlation_id,
                    "action": action,
                    "details": details or {}
                }
            )
        except Exception as ex:
            logger.warning(f"Failed to publish evidence audit event '{action}': {ex}")


# Singleton instance
evidence_storage_service = EvidenceStorageService()
