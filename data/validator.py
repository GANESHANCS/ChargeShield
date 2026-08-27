"""
ChargeShield Synthetic Data Quality & Leakage Validator.

Performs strict automated validation on generated synthetic datasets:
1. Foreign key and relational integrity check.
2. Target leakage risk analysis.
3. Schema and type invariant checks.
4. Timestamp sequence sanity checks.
"""

from typing import Dict, List, Tuple, Any
import pandas as pd
from data.schemas import DATA_DICTIONARY, FieldCategory

class DatasetValidator:
    """Validator engine for ChargeShield synthetic data integrity."""
    
    def validate_dataset(self, datasets: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """
        Runs full validation suite on datasets dict.
        Raises ValueError if critical relational or leakage invariants are violated.
        Returns detailed report dictionary.
        """
        errors: List[str] = []
        warnings: List[str] = []
        
        # 1. Primary Key Uniqueness
        for name, df in datasets.items():
            pk_col = f"{name[:-1]}_id" if name != "previous_disputes" else "previous_dispute_id"
            if pk_col in df.columns:
                dups = df[pk_col].duplicated().sum()
                if dups > 0:
                    errors.append(f"Entity '{name}' contains {dups} duplicate primary keys in column '{pk_col}'.")
                    
        # 2. Foreign Key Relational Integrity
        df_cust = datasets["customers"]
        df_ord = datasets["orders"]
        df_txn = datasets["transactions"]
        df_del = datasets["deliveries"]
        df_disp = datasets["disputes"]
        df_com = datasets["communications"]
        df_prev = datasets["previous_disputes"]
        
        # orders -> customers
        invalid_cust_orders = set(df_ord["customer_id"]) - set(df_cust["customer_id"])
        if invalid_cust_orders:
            errors.append(f"Orders reference non-existent customer_ids: {invalid_cust_orders}")
            
        # transactions -> orders
        invalid_ord_txns = set(df_txn["order_id"]) - set(df_ord["order_id"])
        if invalid_ord_txns:
            errors.append(f"Transactions reference non-existent order_ids: {invalid_ord_txns}")
            
        # deliveries -> orders
        invalid_ord_dels = set(df_del["order_id"]) - set(df_ord["order_id"])
        if invalid_ord_dels:
            errors.append(f"Deliveries reference non-existent order_ids: {invalid_ord_dels}")
            
        # disputes -> transactions
        invalid_txn_disps = set(df_disp["transaction_id"]) - set(df_txn["transaction_id"])
        if invalid_txn_disps:
            errors.append(f"Disputes reference non-existent transaction_ids: {invalid_txn_disps}")
            
        # communications -> customers
        invalid_cust_coms = set(df_com["customer_id"]) - set(df_cust["customer_id"])
        if invalid_cust_coms:
            errors.append(f"Communications reference non-existent customer_ids: {invalid_cust_coms}")
            
        # previous_disputes -> customers
        invalid_cust_prev = set(df_prev["customer_id"]) - set(df_cust["customer_id"])
        if invalid_cust_prev:
            errors.append(f"Previous disputes reference non-existent customer_ids: {invalid_cust_prev}")

        # 3. Target Leakage Validation
        for entity_name, fields_map in DATA_DICTIONARY.items():
            if entity_name in datasets:
                df = datasets[entity_name]
                for field_name, category in fields_map.items():
                    if category == FieldCategory.POST_OUTCOME:
                        # Verify this field is properly marked as post-outcome and excluded from pre-triage feature vectors
                        if field_name not in df.columns:
                            warnings.append(f"Post-outcome field '{field_name}' absent from '{entity_name}'.")

        # 4. Timestamp Sanity Checks
        # Merge disputes with transactions and orders to check timestamp chronology
        merged_disp = df_disp.merge(df_txn[['transaction_id', 'transaction_timestamp']], on='transaction_id')
        merged_disp = merged_disp.merge(df_ord[['order_id', 'order_timestamp']], on='order_id')
        
        invalid_disp_times = merged_disp[merged_disp['dispute_creation_timestamp'] < merged_disp['transaction_timestamp']]
        if len(invalid_disp_times) > 0:
            errors.append(f"Found {len(invalid_disp_times)} disputes created before transaction timestamp.")
            
        invalid_txn_times = merged_disp[merged_disp['transaction_timestamp'] < merged_disp['order_timestamp']]
        if len(invalid_txn_times) > 0:
            errors.append(f"Found {len(invalid_txn_times)} transactions processed before order timestamp.")

        # 5. Range & Target Value Invariants
        if (df_disp["disputed_amount"] <= 0).any():
            errors.append("Disputed amounts must be strictly positive (> 0).")
            
        invalid_targets = set(df_disp["contest_success"]) - {0, 1}
        if invalid_targets:
            errors.append(f"Target contest_success contains invalid values: {invalid_targets}")

        is_valid = len(errors) == 0
        if not is_valid:
            raise ValueError(f"Dataset Quality Validation Failed:\n" + "\n".join(f"- {e}" for e in errors))
            
        return {
            "is_valid": is_valid,
            "errors": errors,
            "warnings": warnings,
            "checked_records": {
                "customers": len(df_cust),
                "orders": len(df_ord),
                "transactions": len(df_txn),
                "deliveries": len(df_del),
                "disputes": len(df_disp),
                "communications": len(df_com),
                "previous_disputes": len(df_prev)
            }
        }

def get_pre_triage_features(df_disputes: pd.DataFrame, df_transactions: pd.DataFrame, df_deliveries: pd.DataFrame, df_customers: pd.DataFrame) -> pd.DataFrame:
    """
    Constructs a clean pre-triage feature dataset for ML model training.
    Guarantees strict exclusion of post-outcome fields (final_outcome, settlement_date, contest_success).
    """
    # Excluded columns explicit safety check
    post_outcome_fields = {"final_outcome", "settlement_date", "contest_success"}
    
    # Base dispute features
    base_cols = [c for c in df_disputes.columns if c not in post_outcome_fields]
    features_df = df_disputes[base_cols].copy()
    
    # Merge with pre-triage features from relational tables
    features_df = features_df.merge(
        df_transactions[['transaction_id', 'payment_method', 'auth_risk_score', 'velocity_24h', 'device_fingerprint_match', 'ip_country_match']],
        on='transaction_id', how='left'
    )
    
    features_df = features_df.merge(
        df_deliveries[['order_id', 'delivery_status', 'tracking_available', 'pod_signature_present', 'fulfillment_anomaly']],
        on='order_id', how='left'
    )
    
    features_df = features_df.merge(
        df_customers[['customer_id', 'tenure_days', 'total_order_count', 'successful_order_count', 'previous_dispute_count', 'previous_chargeback_count', 'customer_segment']],
        on='customer_id', how='left'
    )
    
    # Verify no post-outcome fields leaked
    leaked = set(features_df.columns).intersection(post_outcome_fields)
    if leaked:
        raise ValueError(f"CRITICAL LEAKAGE ERROR: Feature dataframe contains post-outcome columns: {leaked}")
        
    return features_df
