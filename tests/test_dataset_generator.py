"""
Phase 1 Unit & Integration Test Suite.

Verifies:
1. Generator reproducibility across identical seeds
2. Schema & column completeness
3. Valid data types & ranges
4. Valid target value distribution
5. Relational & Foreign-Key consistency
6. Timestamp chronology logic
7. Strict target leakage prevention in pre-triage feature engineering
8. Configurable dataset size behavior
"""

import pytest
import pandas as pd
import numpy as np
from data.generator import SyntheticDataGenerator
from data.validator import DatasetValidator, get_pre_triage_features
from data.schemas import DATA_DICTIONARY, FieldCategory

@pytest.fixture
def generator():
    return SyntheticDataGenerator(seed=42)

@pytest.fixture
def sample_dataset(generator):
    return generator.generate_dataset(num_customers=100, dispute_rate=0.10, output_dir=None)

# 1. Generator Reproducibility Test
def test_generator_reproducibility():
    gen1 = SyntheticDataGenerator(seed=1234)
    ds1 = gen1.generate_dataset(num_customers=50, dispute_rate=0.10, output_dir=None)
    
    gen2 = SyntheticDataGenerator(seed=1234)
    ds2 = gen2.generate_dataset(num_customers=50, dispute_rate=0.10, output_dir=None)
    
    for key in ds1:
        pd.testing.assert_frame_equal(ds1[key], ds2[key])

def test_generator_seed_variation():
    gen1 = SyntheticDataGenerator(seed=42)
    ds1 = gen1.generate_dataset(num_customers=50, dispute_rate=0.10, output_dir=None)
    
    gen2 = SyntheticDataGenerator(seed=999)
    ds2 = gen2.generate_dataset(num_customers=50, dispute_rate=0.10, output_dir=None)
    
    # Verify different seed produces different generated feature values (e.g. tenure_days, order amounts)
    assert not ds1["customers"]["tenure_days"].equals(ds2["customers"]["tenure_days"])
    assert not ds1["orders"]["order_amount"].equals(ds2["orders"]["order_amount"])

# 2 & 3. Schema & Required Columns Test
def test_schema_required_columns(sample_dataset):
    validator = DatasetValidator()
    report = validator.validate_dataset(sample_dataset)
    assert report["is_valid"] is True
    assert len(report["errors"]) == 0

# 4. Valid Target Values Test
def test_valid_target_values(sample_dataset):
    df_disp = sample_dataset["disputes"]
    assert "contest_success" in df_disp.columns
    unique_targets = set(df_disp["contest_success"].unique())
    assert unique_targets.issubset({0, 1})

# 5 & 7. Entity Relationships & Foreign Key Consistency Test
def test_foreign_key_consistency(sample_dataset):
    df_cust = sample_dataset["customers"]
    df_ord = sample_dataset["orders"]
    df_txn = sample_dataset["transactions"]
    df_del = sample_dataset["deliveries"]
    df_disp = sample_dataset["disputes"]
    
    # orders -> customers
    assert set(df_ord["customer_id"]).issubset(set(df_cust["customer_id"]))
    # transactions -> orders
    assert set(df_txn["order_id"]).issubset(set(df_ord["order_id"]))
    # deliveries -> orders
    assert set(df_del["order_id"]).issubset(set(df_ord["order_id"]))
    # disputes -> transactions
    assert set(df_disp["transaction_id"]).issubset(set(df_txn["transaction_id"]))

# 8. Missing-Value Behavior Test
def test_missing_value_behavior(sample_dataset):
    df_del = sample_dataset["deliveries"]
    # Digital goods or in-transit items must allow null delivery_timestamp
    in_transit_or_na = df_del[df_del["delivery_status"].isin(["IN_TRANSIT", "NOT_APPLICABLE"])]
    assert in_transit_or_na["delivery_timestamp"].isnull().all()

# 9. Dataset Size Configuration Test
def test_dataset_size_configuration(generator):
    ds_small = generator.generate_dataset(num_customers=20, output_dir=None)
    ds_large = generator.generate_dataset(num_customers=200, output_dir=None)
    
    assert len(ds_small["customers"]) == 20
    assert len(ds_large["customers"]) == 200
    assert len(ds_large["orders"]) > len(ds_small["orders"])

# 10. Class Imbalance & Variation Test
def test_dispute_reason_distribution(sample_dataset):
    df_disp = sample_dataset["disputes"]
    assert len(df_disp) > 0
    reasons = df_disp["dispute_reason_code"].nunique()
    assert reasons >= 3  # Multiple reason codes present

# 11. Timestamp Consistency Test
def test_timestamp_chronology(sample_dataset):
    df_disp = sample_dataset["disputes"]
    df_txn = sample_dataset["transactions"]
    df_ord = sample_dataset["orders"]
    
    merged = df_disp.merge(df_txn[['transaction_id', 'transaction_timestamp']], on='transaction_id')
    merged = merged.merge(df_ord[['order_id', 'order_timestamp']], on='order_id')
    
    assert (merged['dispute_creation_timestamp'] >= merged['transaction_timestamp']).all()
    assert (merged['transaction_timestamp'] >= merged['order_timestamp']).all()

# 12. Amount Validity Test
def test_monetary_amount_validity(sample_dataset):
    df_txn = sample_dataset["transactions"]
    df_disp = sample_dataset["disputes"]
    
    assert (df_txn["amount"] > 0).all()
    assert (df_disp["disputed_amount"] > 0).all()

# 13. Target Leakage Prevention Test
def test_target_leakage_prevention(sample_dataset):
    df_disp = sample_dataset["disputes"]
    df_txn = sample_dataset["transactions"]
    df_del = sample_dataset["deliveries"]
    df_cust = sample_dataset["customers"]
    
    pre_triage_features = get_pre_triage_features(df_disp, df_txn, df_del, df_cust)
    
    # Must NOT contain post-outcome fields
    forbidden = {"final_outcome", "settlement_date", "contest_success"}
    for col in forbidden:
        assert col not in pre_triage_features.columns, f"Leaked column '{col}' found in pre-triage features!"
