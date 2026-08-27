"""
ChargeShield Synthetic Data Foundation Package.
Contains relational generator, schemas, and leakage validator for chargeback defense.
"""

from data.generator import SyntheticDataGenerator
from data.validator import DatasetValidator, get_pre_triage_features
from data.schemas import DATA_DICTIONARY, FieldCategory

__all__ = [
    "SyntheticDataGenerator",
    "DatasetValidator",
    "get_pre_triage_features",
    "DATA_DICTIONARY",
    "FieldCategory"
]
