"""
ChargeShield Dataset Manager.
Loads relational data, constructs feature table, and performs strict time-based splits.
"""

import os
from typing import Dict, Tuple, Any
import pandas as pd
from ml.config import config
from ml.features import construct_features, ALL_FEATURE_COLUMNS

def load_and_split_dataset(
    data_dir: str = config.DATA_DIR
) -> Dict[str, Any]:
    """
    Loads generated CSV datasets, constructs feature matrices, and splits into
    Train (60%), Validation (20%), and Test (20%) using chronological ordering.
    """
    df_customers = pd.read_csv(os.path.join(data_dir, "customers.csv"))
    df_orders = pd.read_csv(os.path.join(data_dir, "orders.csv"))
    df_transactions = pd.read_csv(os.path.join(data_dir, "transactions.csv"))
    df_deliveries = pd.read_csv(os.path.join(data_dir, "deliveries.csv"))
    df_disputes = pd.read_csv(os.path.join(data_dir, "disputes.csv"))
    df_communications = pd.read_csv(os.path.join(data_dir, "communications.csv"))

    # Construct features table
    df_features = construct_features(
        df_disputes, df_transactions, df_orders, df_deliveries, df_customers, df_communications
    )

    # Sort disputes chronologically to simulate operational time-split
    df_features = df_features.sort_values(by="dispute_creation_dt").reset_index(drop=True)

    total_n = len(df_features)
    train_end = int(total_n * config.TRAIN_RATIO)
    val_end = train_end + int(total_n * config.VAL_RATIO)

    df_train = df_features.iloc[:train_end].copy()
    df_val = df_features.iloc[train_end:val_end].copy()
    df_test = df_features.iloc[val_end:].copy()

    X_train = df_train[ALL_FEATURE_COLUMNS]
    y_train = df_train["contest_success"].values

    X_val = df_val[ALL_FEATURE_COLUMNS]
    y_val = df_val["contest_success"].values

    X_test = df_test[ALL_FEATURE_COLUMNS]
    y_test = df_test["contest_success"].values

    # Metadata for evaluation & cost estimation
    meta_cols = ["dispute_id", "disputed_amount", "dispute_creation_timestamp", "dispute_reason_code"]
    meta_train = df_train[meta_cols]
    meta_val = df_val[meta_cols]
    meta_test = df_test[meta_cols]

    return {
        "X_train": X_train, "y_train": y_train, "meta_train": meta_train,
        "X_val": X_val, "y_val": y_val, "meta_val": meta_val,
        "X_test": X_test, "y_test": y_test, "meta_test": meta_test,
        "total_disputes": total_n,
        "train_size": len(df_train),
        "val_size": len(df_val),
        "test_size": len(df_test)
    }
