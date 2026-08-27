import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.core.config import settings
from backend.core.logging_config import setup_structured_logging
from backend.core.logging import logger
from backend.db.database import init_db
from backend.api.health import router as health_router
from backend.api.v1 import api_v1_router
from backend.core.middleware import (
    CorrelationIDMiddleware,
    SecurityHeadersMiddleware,
    MaxUploadSizeMiddleware,
    RateLimitMiddleware
)

# Initialize structured application logger
setup_structured_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize persistent database tables on application startup
    try:
        init_db()
        logger.info(f"{settings.PROJECT_NAME} database initialized at {settings.DATABASE_URL}.")
    except Exception as e:
        logger.error(f"Failed to initialize database on startup: {str(e)}")

    # Check if explicit SEED_DEV_USER is enabled
    if settings.SEED_DEV_USER and settings.DEV_ADMIN_PASSWORD:
        try:
            from backend.db.database import get_db_session
            from backend.services.user_service import seed_dev_users
            with get_db_session() as db:
                seed_dev_users(
                    db=db,
                    admin_username=settings.DEV_ADMIN_USERNAME or "admin",
                    admin_password=settings.DEV_ADMIN_PASSWORD
                )
                logger.info("Explicit development user seeding completed successfully.")
        except Exception as seed_err:
            logger.error(f"Failed to perform explicit development user seeding: {str(seed_err)}")

    logger.info(f"{settings.PROJECT_NAME} backend started in {settings.ENVIRONMENT} mode.")
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="AI-Powered Chargeback Defense & Recovery Platform (Production Hardened)",
    version="1.0.0",
    lifespan=lifespan
)

# Attach Security & Operational Middlewares
app.add_middleware(CorrelationIDMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(MaxUploadSizeMiddleware)
app.add_middleware(RateLimitMiddleware)

# CORS middleware for React frontend access
cors_origins = settings.ALLOWED_ORIGINS if settings.ENVIRONMENT == "production" else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global HTTP Exception Handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    request_id = getattr(request.state, "request_id", "req-unknown")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail if isinstance(exc.detail, str) else "HTTP Exception",
            "detail": exc.detail,
            "code": f"HTTP_{exc.status_code}",
            "request_id": request_id,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        },
        headers=getattr(exc, "headers", None)
    )

# Request Validation Error Handler
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    request_id = getattr(request.state, "request_id", "req-unknown")
    try:
        errors = [
            {"loc": [str(l) for l in err.get("loc", [])], "msg": str(err.get("msg", "")), "type": str(err.get("type", ""))}
            for err in exc.errors()
        ]
    except Exception:
        errors = str(exc)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation Error. Invalid request parameters or payload body.",
            "detail": errors,
            "code": "VALIDATION_ERROR",
            "request_id": request_id,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }
    )

# Sanitized Global Exception Handler (prevents stack trace leakage in production)
@app.exception_handler(Exception)
async def sanitized_global_exception_handler(request: Request, exc: Exception):
    request_id = getattr(request.state, "request_id", "req-unknown")
    logger.error(f"Unhandled Exception on {request.method} {request.url.path} (Request ID: {request_id}): {str(exc)}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "An internal system error occurred while processing the request.",
            "code": "INTERNAL_SERVER_ERROR",
            "request_id": request_id,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }
    )

# Include Routers
app.include_router(health_router)
app.include_router(api_v1_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host=settings.API_HOST, port=settings.API_PORT, reload=True)
