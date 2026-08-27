"""
Standardized API Response Envelopes and Pagination Utilities for ChargeShield.
Enforces consistent success/error payloads, correlation IDs, metadata, and server-side pagination boundaries.
"""

import time
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone


def success_response(
    data: Any,
    message: str = "Request processed successfully",
    request_id: str = "req-unknown",
    meta: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Wraps API data payloads in a standardized success envelope."""
    payload = {
        "status": "SUCCESS",
        "message": message,
        "data": data,
        "request_id": request_id,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    if meta:
        payload["meta"] = meta
    return payload


def error_response(
    error_message: str,
    code: str = "GENERIC_ERROR",
    request_id: str = "req-unknown",
    detail: Optional[Any] = None
) -> Dict[str, Any]:
    """Wraps operational error payloads in a standardized error envelope."""
    return {
        "status": "ERROR",
        "error": error_message,
        "code": code,
        "detail": detail,
        "request_id": request_id,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


def paginate_list(
    items: List[Any],
    page: int = 1,
    page_size: int = 20,
    max_page_size: int = 100
) -> Dict[str, Any]:
    """
    Applies safe server-side pagination to an in-memory list of items.
    Enforces page bounds and maximum page size limits.
    """
    safe_page = max(1, page)
    safe_page_size = max(1, min(page_size, max_page_size))
    
    total_items = len(items)
    total_pages = max(1, (total_items + safe_page_size - 1) // safe_page_size)
    
    start_idx = (safe_page - 1) * safe_page_size
    end_idx = start_idx + safe_page_size
    
    paginated_items = items[start_idx:end_idx]
    
    return {
        "items": paginated_items,
        "pagination": {
            "page": safe_page,
            "page_size": safe_page_size,
            "total_items": total_items,
            "total_pages": total_pages,
            "has_next": safe_page < total_pages,
            "has_prev": safe_page > 1
        }
    }
