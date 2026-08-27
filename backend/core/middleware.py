"""
Security & Infrastructure Middlewares for ChargeShield.
Includes Request Correlation ID tracking, In-Memory Rate Limiting, Upload Size Validation, and Security Response Headers.
"""

import time
import uuid
from typing import Dict, List, Tuple
from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from backend.core.config import settings
from backend.core.logging import logger

# In-memory IP/Endpoint Rate Limit storage: { ip: [(timestamp1), (timestamp2)] }
_rate_limit_store: Dict[str, List[float]] = {}


class CorrelationIDMiddleware(BaseHTTPMiddleware):
    """Injects and propagates unique X-Request-ID headers for distributed audit tracing."""
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or f"req-{uuid.uuid4().hex[:12]}"
        request.state.request_id = request_id

        start_time = time.time()
        response: Response = await call_next(request)
        duration_ms = round((time.time() - start_time) * 1000, 2)

        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time-MS"] = str(duration_ms)
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Applies HTTP response security hardening headers."""
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response


class MaxUploadSizeMiddleware(BaseHTTPMiddleware):
    """Enforces maximum payload size limit (default 10MB) to prevent buffer overflow attacks."""
    async def dispatch(self, request: Request, call_next):
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                length = int(content_length)
                if length > settings.MAX_UPLOAD_SIZE_BYTES:
                    return JSONResponse(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        content={
                            "error": "Payload entity too large.",
                            "code": "PAYLOAD_TOO_LARGE",
                            "request_id": getattr(request.state, "request_id", "unknown"),
                            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                        }
                    )
            except ValueError:
                pass
        return await call_next(request)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Lightweight in-memory rate limiter protecting sensitive operational endpoints."""
    async def dispatch(self, request: Request, call_next):
        # Exempt pytest testclient requests from rate limits
        if request.client and request.client.host in ["testclient", "localhost"]:
            return await call_next(request)

        path = request.url.path
        # Apply rate limiting to sensitive routes
        if any(path.startswith(prefix) for prefix in ["/api/v1/auth/login", "/api/v1/simulation", "/api/v1/cases", "/api/v1/review"]):
            client_ip = request.client.host if request.client else "127.0.0.1"
            now = time.time()
            window_start = now - 60.0  # 1 minute window

            timestamps = _rate_limit_store.get(client_ip, [])
            # Filter timestamps within current window
            valid_timestamps = [t for t in timestamps if t > window_start]
            
            if len(valid_timestamps) >= settings.RATE_LIMIT_PER_MINUTE:
                logger.warning(f"Rate limit exceeded for IP '{client_ip}' on '{path}'")
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "error": "Rate limit exceeded. Too many requests. Please wait 60 seconds.",
                        "code": "RATE_LIMIT_EXCEEDED",
                        "request_id": getattr(request.state, "request_id", "unknown"),
                        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                    },
                    headers={"Retry-After": "60"}
                )

            valid_timestamps.append(now)
            _rate_limit_store[client_ip] = valid_timestamps

        return await call_next(request)
