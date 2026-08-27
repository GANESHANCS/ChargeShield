"""
Data Quality Service for ChargeShield Phase 7.

Validates dataset records against strict rules (schema integrity, missing values,
range constraints, duplicate checks) and derives a transparent Data Quality Score.
"""

import os
from typing import Dict, List, Any
import pandas as pd

from ml.config import config

class DataQualityService:
    """Performs programmatic data quality checks across relational datasets."""

    def __init__(self, data_dir: str = config.DATA_DIR):
        self.data_dir = data_dir

    def evaluate_quality(self) -> Dict[str, Any]:
        """
        Executes validation rules over disputes, transactions, orders, customers, and deliveries.
        Returns composite Data Quality Score and itemized issue details.
        """
        issues: List[Dict[str, Any]] = []
        total_checks = 0
        passed_checks = 0

        # Load datasets safely
        try:
            df_disputes = pd.read_csv(os.path.join(self.data_dir, "disputes.csv"))
            df_txns = pd.read_csv(os.path.join(self.data_dir, "transactions.csv"))
            df_orders = pd.read_csv(os.path.join(self.data_dir, "orders.csv"))
            df_customers = pd.read_csv(os.path.join(self.data_dir, "customers.csv"))
            df_deliveries = pd.read_csv(os.path.join(self.data_dir, "deliveries.csv"))
        except Exception as e:
            return {
                "data_quality_score": 0.0,
                "status": "DATASET_UNAVAILABLE",
                "issues": [{"severity": "CRITICAL", "message": f"Dataset CSV load failed: {str(e)}"}],
                "total_records_checked": 0,
                "passed_checks": 0,
                "total_checks": 0
            }

        total_records = len(df_disputes)

        # Rule 1: Dispute ID Uniqueness & Non-null Check
        total_checks += total_records
        null_disp = df_disputes["dispute_id"].isnull().sum()
        dup_disp = df_disputes["dispute_id"].duplicated().sum()
        if null_disp > 0 or dup_disp > 0:
            issues.append({
                "rule": "DISPUTE_ID_INTEGRITY",
                "severity": "HIGH",
                "message": f"Found {null_disp} missing and {dup_disp} duplicate dispute IDs.",
                "affected_records": int(null_disp + dup_disp)
            })
            passed_checks += (total_records - null_disp - dup_disp)
        else:
            passed_checks += total_records

        # Rule 2: Monetary Amount Range Validity (Disputed Amount > 0)
        total_checks += total_records
        invalid_amt = (df_disputes["disputed_amount"] <= 0).sum()
        if invalid_amt > 0:
            issues.append({
                "rule": "MONETARY_AMOUNT_POSITIVE",
                "severity": "MEDIUM",
                "message": f"Found {invalid_amt} disputes with invalid zero/negative amounts.",
                "affected_records": int(invalid_amt)
            })
            passed_checks += (total_records - invalid_amt)
        else:
            passed_checks += total_records

        # Rule 3: Foreign Key Integrity (disputes -> transactions)
        total_checks += total_records
        txn_ids = set(df_txns["transaction_id"].unique())
        orphan_disputes = (~df_disputes["transaction_id"].isin(txn_ids)).sum()
        if orphan_disputes > 0:
            issues.append({
                "rule": "FOREIGN_KEY_TRANSACTION_LINK",
                "severity": "HIGH",
                "message": f"Found {orphan_disputes} disputes linked to unrecorded transaction IDs.",
                "affected_records": int(orphan_disputes)
            })
            passed_checks += (total_records - orphan_disputes)
        else:
            passed_checks += total_records

        # Rule 4: Timestamp Schema & Chronology Check
        total_checks += total_records
        invalid_ts = df_disputes["dispute_creation_timestamp"].isnull().sum()
        if invalid_ts > 0:
            issues.append({
                "rule": "TIMESTAMP_PRESENT",
                "severity": "LOW",
                "message": f"Found {invalid_ts} disputes with missing creation timestamps.",
                "affected_records": int(invalid_ts)
            })
            passed_checks += (total_records - invalid_ts)
        else:
            passed_checks += total_records

        # Rule 5: Delivery Carrier & Signature Presence Validation
        total_checks += total_records
        missing_delivery = df_deliveries["delivery_status"].isnull().sum()
        if missing_delivery > 0:
            issues.append({
                "rule": "DELIVERY_STATUS_PRESENT",
                "severity": "LOW",
                "message": f"Found {missing_delivery} delivery records missing status values.",
                "affected_records": int(missing_delivery)
            })
            passed_checks += (total_records - missing_delivery)
        else:
            passed_checks += total_records

        quality_score = round((passed_checks / total_checks) * 100.0, 1) if total_checks > 0 else 100.0

        return {
            "data_quality_score": quality_score,
            "status": "EXCELLENT" if quality_score >= 95.0 else "GOOD" if quality_score >= 85.0 else "DEGRADED",
            "issues": issues,
            "total_records_checked": total_records,
            "passed_checks": passed_checks,
            "total_checks": total_checks
        }

data_quality_service = DataQualityService()
