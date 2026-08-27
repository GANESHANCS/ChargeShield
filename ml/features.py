"""
ChargeShield Feature Engineering & Preprocessing Pipeline.

Extracts prediction-time features from relational entities and builds scikit-learn
ColumnTransformer pipelines fitted ONLY on training data.
"""

from typing import List, Tuple, Dict, Any
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline

from data.schemas import DATA_DICTIONARY, FieldCategory

# Categorization of Feature Types
NUMERICAL_FEATURES = [
    "disputed_amount",
    "tenure_days",
    "total_order_count",
    "successful_order_count",
    "customer_success_ratio",
    "previous_dispute_count",
    "previous_chargeback_count",
    "refund_count",
    "auth_risk_score",
    "velocity_24h",
    "order_age_days",
    "days_to_deadline"
]

CATEGORICAL_FEATURES = [
    "dispute_reason_code",
    "dispute_category",
    "payment_method",
    "product_category",
    "delivery_status",
    "carrier",
    "customer_segment"
]

BOOLEAN_FEATURES = [
    "is_digital_item",
    "tracking_available",
    "pod_signature_present",
    "delivery_location_match",
    "fulfillment_anomaly",
    "device_fingerprint_match",
    "ip_country_match",
    "customer_contacted_support",
    "support_ticket_resolved"
]

ALL_FEATURE_COLUMNS = NUMERICAL_FEATURES + CATEGORICAL_FEATURES + BOOLEAN_FEATURES
FORBIDDEN_FIELDS = {"final_outcome", "settlement_date", "contest_success"}

def construct_features(
    df_disputes: pd.DataFrame,
    df_transactions: pd.DataFrame,
    df_orders: pd.DataFrame,
    df_deliveries: pd.DataFrame,
    df_customers: pd.DataFrame,
    df_communications: pd.DataFrame
) -> pd.DataFrame:
    """
    Joins relational datasets and constructs pre-triage feature table.
    Guarantees strict exclusion of post-outcome fields.
    """
    # 1. Base Disputes
    df = df_disputes[['dispute_id', 'transaction_id', 'order_id', 'customer_id',
                      'dispute_creation_timestamp', 'dispute_reason_code', 'dispute_category',
                      'disputed_amount', 'response_deadline', 'contest_success']].copy()
                      
    # 2. Merge Transactions
    df = df.merge(
        df_transactions[['transaction_id', 'payment_method', 'auth_risk_score', 'velocity_24h',
                         'device_fingerprint_match', 'ip_country_match']],
        on='transaction_id', how='left'
    )
    
    # 3. Merge Orders & Deliveries
    df = df.merge(
        df_orders[['order_id', 'order_timestamp', 'product_category', 'is_digital_item']],
        on='order_id', how='left'
    )
    
    df = df.merge(
        df_deliveries[['order_id', 'delivery_status', 'carrier', 'tracking_available',
                         'pod_signature_present', 'delivery_location_match', 'fulfillment_anomaly']],
        on='order_id', how='left'
    )
    
    # 4. Merge Customers
    df = df.merge(
        df_customers[['customer_id', 'tenure_days', 'total_order_count', 'successful_order_count',
                         'previous_dispute_count', 'previous_chargeback_count', 'refund_count',
                         'customer_segment']],
        on='customer_id', how='left'
    )
    
    # 5. Support Communications Aggregation
    if not df_communications.empty:
        com_summary = df_communications.groupby('order_id').agg(
            customer_contacted_support=('communication_id', 'count'),
            support_ticket_resolved=('resolution_status', lambda s: (s == 'RESOLVED').any())
        ).reset_index()
        com_summary['customer_contacted_support'] = com_summary['customer_contacted_support'] > 0
        df = df.merge(com_summary, on='order_id', how='left')
        df['customer_contacted_support'] = df['customer_contacted_support'].fillna(False)
        df['support_ticket_resolved'] = df['support_ticket_resolved'].fillna(False)
    else:
        df['customer_contacted_support'] = False
        df['support_ticket_resolved'] = False

    # 6. Temporal Features
    df['dispute_creation_dt'] = pd.to_datetime(df['dispute_creation_timestamp'])
    df['order_dt'] = pd.to_datetime(df['order_timestamp'])
    df['response_deadline_dt'] = pd.to_datetime(df['response_deadline'])
    
    df['order_age_days'] = (df['dispute_creation_dt'] - df['order_dt']).dt.total_seconds() / 86400.0
    df['days_to_deadline'] = (df['response_deadline_dt'] - df['dispute_creation_dt']).dt.total_seconds() / 86400.0
    
    # 7. Customer Ratio Features
    df['customer_success_ratio'] = np.where(
        df['total_order_count'] > 0,
        df['successful_order_count'] / df['total_order_count'],
        1.0
    )

    # Convert Booleans to integer (0 or 1)
    for col in BOOLEAN_FEATURES:
        df[col] = df[col].astype(bool).astype(int)

    # 8. Strict Leakage Audit Gate
    leaked = FORBIDDEN_FIELDS.intersection(set(df.columns) - {'contest_success'})
    if leaked:
        raise ValueError(f"CRITICAL LEAKAGE DETECTED in feature builder: Leaked fields: {leaked}")
        
    return df

def build_preprocessing_pipeline() -> ColumnTransformer:
    """
    Constructs a ColumnTransformer for preprocessing numerical, categorical, and boolean features.
    """
    num_transformer = Pipeline([
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', StandardScaler())
    ])
    
    cat_transformer = Pipeline([
        ('imputer', SimpleImputer(strategy='constant', fill_value='MISSING')),
        ('encoder', OneHotEncoder(handle_unknown='ignore', sparse_output=False))
    ])
    
    bool_transformer = Pipeline([
        ('imputer', SimpleImputer(strategy='most_frequent'))
    ])
    
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', num_transformer, NUMERICAL_FEATURES),
            ('cat', cat_transformer, CATEGORICAL_FEATURES),
            ('bool', bool_transformer, BOOLEAN_FEATURES)
        ],
        remainder='drop'
    )
    
    return preprocessor
