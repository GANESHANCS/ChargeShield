"""
Value Comparator and Normalization Engine for Evidence Verification.
Provides field-level safe matching for strings, booleans, numbers/currency, and timestamps.
"""

from typing import Any, Tuple, Optional
from decimal import Decimal

def compare_values(claimed_val: Any, actual_val: Any) -> Tuple[str, str, str]:
    """
    Compares a claimed value against an actual source record value.
    Returns (verification_status, match_type, verification_reason).
    """
    if actual_val is None:
        if claimed_val is None or str(claimed_val).upper() in ["NONE", "NULL", "UNAVAILABLE"]:
            return (
                "VERIFIED",
                "NORMALIZED_MATCH",
                "Both claimed value and source record confirm that information is absent/unavailable."
            )
        return (
            "UNVERIFIABLE",
            "NOT_APPLICABLE",
            "Actual source record field is null or unpopulated."
        )

    if claimed_val is None:
        return (
            "UNSUPPORTED",
            "MISMATCH",
            f"Claim value is missing while source record contains value '{actual_val}'."
        )

    str_claimed = str(claimed_val).strip()
    str_actual = str(actual_val).strip()

    # 1. Exact String Match
    if str_claimed == str_actual:
        return (
            "VERIFIED",
            "EXACT",
            f"Claimed value '{str_claimed}' exactly matches authoritative source value '{str_actual}'."
        )

    # 2. Boolean Normalization Comparison
    bool_claimed = _parse_boolean(str_claimed)
    bool_actual = _parse_boolean(str_actual)
    if bool_claimed is not None and bool_actual is not None:
        if bool_claimed == bool_actual:
            return (
                "VERIFIED",
                "NORMALIZED_MATCH",
                f"Claimed boolean value '{str_claimed}' matches normalized source boolean '{bool_actual}'."
            )
        else:
            return (
                "MISMATCH",
                "MISMATCH",
                f"Boolean conflict: claimed '{str_claimed}' ({bool_claimed}) does not match source '{str_actual}' ({bool_actual})."
            )

    # 3. Numeric / Monetary Precision Comparison
    num_claimed = _parse_numeric(str_claimed)
    num_actual = _parse_numeric(str_actual)
    if num_claimed is not None and num_actual is not None:
        if num_claimed == num_actual:
            return (
                "VERIFIED",
                "EXACT",
                f"Claimed numeric value {num_claimed} exactly matches source value {num_actual}."
            )
        else:
            return (
                "MISMATCH",
                "MISMATCH",
                f"Numeric discrepancy: claimed value {num_claimed} conflicts with source value {num_actual}."
            )

    # 4. Normalized Case-Insensitive String Match
    if str_claimed.upper() == str_actual.upper():
        return (
            "VERIFIED",
            "NORMALIZED_MATCH",
            f"Claimed value '{str_claimed}' matches source value '{str_actual}' under case normalization."
        )

    # 5. Partial String Inclusion
    if str_claimed.upper() in str_actual.upper() or str_actual.upper() in str_claimed.upper():
        return (
            "VERIFIED",
            "PARTIAL_MATCH",
            f"Claimed value '{str_claimed}' partially matches source value '{str_actual}'."
        )

    # 6. Fallback Mismatch
    return (
        "MISMATCH",
        "MISMATCH",
        f"Claimed value '{str_claimed}' conflicts with authoritative source value '{str_actual}'."
    )

def _parse_boolean(val: str) -> Optional[bool]:
    clean = val.lower()
    if clean in ["true", "1", "yes", "t", "present"]:
        return True
    if clean in ["false", "0", "no", "f", "absent", "none"]:
        return False
    return None

def _parse_numeric(val: str) -> Optional[Decimal]:
    try:
        # Strip common currency prefixes
        clean = val.replace("INR", "").replace("USD", "").replace("Score:", "").replace(",", "").strip()
        return Decimal(clean).quantize(Decimal("0.01"))
    except Exception:
        return None
