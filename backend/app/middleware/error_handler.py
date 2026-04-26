"""Consistent error response handler."""
import logging
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError

logger = logging.getLogger(__name__)


class ErrorResponse:
    """Consistent error response format."""
    
    def __init__(self, error: str, detail: str = "", code: str = "", 
                 field: str = "", path: str = ""):
        self.error = error
        self.detail = detail
        self.code = code
        self.field = field
        self.path = path
    
    def to_dict(self):
        result = {
            "error": self.error,
            "detail": self.detail,
        }
        if self.code:
            result["code"] = self.code
        if self.field:
            result["field"] = self.field
        if self.path:
            result["path"] = self.path
        return result


async def custom_http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with consistent format."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status": exc.status_code,
        },
        headers={"X-Request-ID": request.headers.get("X-Request-ID", "")},
    )


async def validation_exception_handler(request: Request, exc: ValidationError):
    """Handle Pydantic validation errors."""
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(loc) for loc in error.get("loc", [])),
            "message": error.get("msg", ""),
        })
    
    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation Error",
            "detail": "Request validation failed",
            "validation_errors": errors,
        },
        headers={"X-Request-ID": request.headers.get("X-Request-ID", "")},
    )


async def general_exception_handler(request: Request, exc: Exception):
    """Catch-all for unhandled exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "detail": "An unexpected error occurred",
        },
        headers={"X-Request-ID": request.headers.get("X-Request-ID", "")},
    )