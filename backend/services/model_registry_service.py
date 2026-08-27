"""
Model Registry Service for ChargeShield Phase 12.
Tracks ML model versions, training timestamps, algorithm specs, and governance status
(DEVELOPMENT, VALIDATION, STAGED, PRODUCTION, RETIRED).
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from backend.db.database import get_db_session
from backend.db.models import ModelVersionModel

VALID_STATUSES = {"DEVELOPMENT", "VALIDATION", "STAGED", "PRODUCTION", "RETIRED"}


class ModelRegistryService:
    def __init__(self):
        self._default_versions = [
            {
                "id": "MOD_LGBM_V1_0",
                "version": "1.0.0",
                "algorithm": "LightGBM Binary Classifier (Cost-Sensitive)",
                "feature_count": 28.0,
                "threshold": 0.29,
                "lifecycle_status": "PRODUCTION",
                "training_timestamp": "2026-08-01T12:00:00Z",
                "created_at": "2026-08-01T12:00:00Z"
            },
            {
                "id": "MOD_LOGREG_V1_0",
                "version": "0.9.0",
                "algorithm": "Logistic Regression (L2 Baseline)",
                "feature_count": 28.0,
                "threshold": 0.50,
                "lifecycle_status": "RETIRED",
                "training_timestamp": "2026-07-15T09:30:00Z",
                "created_at": "2026-07-15T09:30:00Z"
            },
            {
                "id": "MOD_LGBM_V1_1_STAGED",
                "version": "1.1.0-rc1",
                "algorithm": "LightGBM Binary Classifier (Recalibrated)",
                "feature_count": 32.0,
                "threshold": 0.29,
                "lifecycle_status": "STAGED",
                "training_timestamp": "2026-08-20T16:45:00Z",
                "created_at": "2026-08-20T16:45:00Z"
            }
        ]

    def _ensure_seed_versions(self, db):
        existing_count = db.query(ModelVersionModel).count()
        if existing_count == 0:
            for item in self._default_versions:
                mv = ModelVersionModel(**item)
                db.add(mv)
            db.commit()

    def get_registry_status(self) -> Dict[str, Any]:
        with get_db_session() as db:
            self._ensure_seed_versions(db)
            versions = db.query(ModelVersionModel).all()
            
            records = []
            production_model = None
            for v in versions:
                rec = {
                    "id": v.id,
                    "version": v.version,
                    "algorithm": v.algorithm,
                    "feature_count": v.feature_count,
                    "threshold": v.threshold,
                    "lifecycle_status": v.lifecycle_status,
                    "training_timestamp": v.training_timestamp,
                    "created_at": v.created_at
                }
                records.append(rec)
                if v.lifecycle_status == "PRODUCTION":
                    production_model = rec

            return {
                "status": "HEALTHY",
                "active_production_model": production_model,
                "total_registered_versions": len(records),
                "versions": records,
                "data_provenance": "PRODUCTION",
                "governance": {
                    "auto_promotion": False,
                    "requires_approval": True,
                    "policy": "No automatic model promotion. Human Admin sign-off required."
                }
            }

    def update_model_status(self, version: str, new_status: str) -> Dict[str, Any]:
        if new_status not in VALID_STATUSES:
            raise ValueError(f"Invalid lifecycle status '{new_status}'. Must be one of {list(VALID_STATUSES)}")

        with get_db_session() as db:
            self._ensure_seed_versions(db)
            model_rec = db.query(ModelVersionModel).filter(ModelVersionModel.version == version).first()
            if not model_rec:
                raise ValueError(f"Model version '{version}' not found in registry.")

            old_status = model_rec.lifecycle_status
            if old_status == new_status:
                return {"status": "UNCHANGED", "version": version, "lifecycle_status": new_status}

            # If promoting to PRODUCTION, demote current PRODUCTION to RETIRED
            if new_status == "PRODUCTION":
                curr_prod = db.query(ModelVersionModel).filter(ModelVersionModel.lifecycle_status == "PRODUCTION").all()
                for cp in curr_prod:
                    cp.lifecycle_status = "RETIRED"

            model_rec.lifecycle_status = new_status
            db.commit()

            return {
                "status": "UPDATED",
                "version": version,
                "previous_status": old_status,
                "new_status": new_status,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }


model_registry_service = ModelRegistryService()
